"""InternVL2.5-8B backbone.

Vision tower: InternViT (direct patch tokens) -> pixel_shuffle -> mlp1 -> 256
tokens in InternLM2's embedding space. Alignment target = InternViT layer-N
hidden state. Token injection uses the checkpoint's
``generate(visual_features=...)`` hook.

This file is the single home of all InternVL-specific logic (both the
training-align side and the eval side). It implements ``VLMBackbone``.
"""

from __future__ import annotations

import os
import contextlib
import importlib
import sys

import torch
import torch.nn.functional as F
import torchvision.transforms as T
from PIL import Image
from torchvision.transforms.functional import InterpolationMode

from .base import VLMBackbone

DEFAULT_MODEL_PATH = os.environ.get("INTERNVL_MODEL_PATH", "/mnt/nas/xinyizheng/InternVL2_5-8B")  # align side honours the env too (E-10)
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)
IMG_START_TOKEN, IMG_END_TOKEN, IMG_CONTEXT_TOKEN = "<img>", "</img>", "<IMG_CONTEXT>"


# --------------------------------------------------------------------- #
# dynamic-tiling image preprocessing (eval/oracle pixel path)
# --------------------------------------------------------------------- #
def _build_transform(input_size):
    return T.Compose([
        T.Lambda(lambda im: im.convert("RGB") if im.mode != "RGB" else im),
        T.Resize((input_size, input_size), interpolation=InterpolationMode.BICUBIC),
        T.ToTensor(),
        T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])


def _load_image(path, input_size=448):
    """One frame -> [1, 3, 448, 448] (single tile; videos use 1 tile/frame)."""
    image = Image.open(path).convert("RGB")
    return _build_transform(input_size)(image).unsqueeze(0)


class InternVLBackbone(VLMBackbone):
    name = "internvl"

    def __init__(self, model_path=DEFAULT_MODEL_PATH, device="cuda",
                 dtype=torch.bfloat16, align_layer=12, input_size=448, **kw):
        super().__init__(model_path, device, dtype, align_layer, input_size, **kw)
        self._dims = None

    # ============================ align side ============================ #
    def load_align(self):
        """Vision tower + mlp1 in fp32, LLM dropped (matches codec training).

        Falls back to a vision-only build (InternViT + mlp1 read straight from the safetensors
        shards) when the checkpoint's chat config needs a newer transformers than this env has
        (InternVL3.5: Qwen3). The align side never touches the LLM, so the fallback is exact.
        """
        from transformers import AutoModel
        try:
            with contextlib.redirect_stdout(sys.stderr):
                model = AutoModel.from_pretrained(
                    self.model_path, torch_dtype=torch.bfloat16,
                    trust_remote_code=True, low_cpu_mem_usage=True)
        except ImportError as e:
            print(f"[internvl] AutoModel failed ({e}); building vision-only teacher", file=sys.stderr)
            with contextlib.redirect_stdout(sys.stderr):   # remote modeling code prints notices; stdout must stay pure JSON
                model = _VisionOnlyInternVL.from_checkpoint(self.model_path)
        if hasattr(model, "language_model"):
            del model.language_model
        model = model.float().eval()
        for p in model.parameters():
            p.requires_grad = False
        self.model = model.to(self.device)
        self._mode = "align"
        return self

    def vit_dims(self):
        if self._dims is None:
            emb = self.model.vision_model.embeddings
            img, patch = int(emb.image_size), int(emb.patch_size)
            self._dims = {
                "num_patches": int(emb.num_patches),
                "hidden_dim": int(emb.embed_dim),
                "num_layers": len(self.model.vision_model.encoder.layers),
                "image_size": img, "patch_size": patch, "grid": img // patch,
            }
        return self._dims

    def preprocess_for_vit(self, x_5d):
        n, c, t, h, w = x_5d.shape
        frames = x_5d.permute(0, 2, 1, 3, 4).reshape(n * t, c, h, w).float()
        frames = F.interpolate(frames, size=(self.input_size, self.input_size),
                               mode="bilinear", align_corners=False)
        mean = torch.tensor(IMAGENET_MEAN, device=frames.device).view(1, 3, 1, 1)
        std = torch.tensor(IMAGENET_STD, device=frames.device).view(1, 3, 1, 1)
        return (frames - mean) / std, n, t

    def _add_cls_and_pos(self, patch_embeds):
        emb = self.model.vision_model.embeddings
        grid = self.vit_dims()["grid"]
        b = patch_embeds.shape[0]
        cls = emb.class_embedding.expand(b, 1, -1).to(patch_embeds.dtype)
        x = torch.cat([cls, patch_embeds], dim=1)
        pos = emb.position_embedding
        if pos.shape[1] == x.shape[1]:
            pos_eff = pos
        else:
            pos_eff = torch.cat([pos[:, :1, :],
                                 emb._get_pos_embed(pos[:, 1:, :], grid, grid)], dim=1)
        return x + pos_eff.to(patch_embeds.dtype)

    def _run_first_n(self, hidden, num_layers):
        """num_layers: int -> layer-N hidden state; list of ints -> {N: hidden state} from ONE
        pass up to max(N) (multi-layer alignment, CVPR-27 ablation C2)."""
        taps = sorted({int(n) for n in num_layers}) if isinstance(num_layers, (list, tuple)) else None
        stop = taps[-1] if taps else int(num_layers)
        out, tapped = hidden, {}
        for i, layer in enumerate(self.model.vision_model.encoder.layers[:stop], start=1):
            out = layer(out)
            if isinstance(out, tuple):
                out = out[0]
            if taps and i in taps:
                tapped[i] = out
        return tapped if taps else out

    @torch.no_grad()
    def oracle_hidden(self, x_5d, layer_idx):
        frames, n, t = self.preprocess_for_vit(x_5d)
        frames = frames.to(self.model.vision_model.embeddings.patch_embedding.weight.dtype)
        h = self.model.vision_model.embeddings(pixel_values=frames)
        h = self._run_first_n(h, layer_idx)
        if isinstance(h, dict):
            return {k: v.view(n, t, v.shape[-2], v.shape[-1]).contiguous() for k, v in h.items()}
        return h.view(n, t, h.shape[-2], h.shape[-1]).contiguous()

    def codec_hidden(self, patch_embeds, layer_idx):
        return self._run_first_n(self._add_cls_and_pos(patch_embeds), layer_idx)

    @torch.no_grad()
    def codec_to_llm_tokens(self, patch_embeds):
        grid = self.vit_dims()["grid"]
        h = self._run_first_n(self._add_cls_and_pos(patch_embeds),
                              self.vit_dims()["num_layers"])
        h = h[:, 1:, :].contiguous()
        b = h.shape[0]
        h = h.reshape(b, grid, grid, -1)
        h = self.model.pixel_shuffle(h, scale_factor=self.model.downsample_ratio)
        h = h.reshape(b, -1, h.shape[-1])
        return self.model.mlp1(h)  # [B, 256, llm_hidden]

    # ============================ eval side ============================ #
    def load_full(self):
        from transformers import AutoModel, AutoTokenizer, GenerationConfig, GenerationMixin
        model = AutoModel.from_pretrained(
            self.model_path, torch_dtype=self.dtype,
            trust_remote_code=True, low_cpu_mem_usage=True).eval().to(self.device)
        for p in model.parameters():
            p.requires_grad = False
        tok = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=True,
                                            use_fast=False)
        model.img_context_token_id = tok.convert_tokens_to_ids(IMG_CONTEXT_TOKEN)
        lm = model.language_model
        if not isinstance(lm, GenerationMixin):
            lm.__class__ = type(lm.__class__.__name__, (lm.__class__, GenerationMixin), {})
        if getattr(lm, "generation_config", None) is None:
            try:
                lm.generation_config = GenerationConfig.from_model_config(lm.config)
            except Exception:
                lm.generation_config = GenerationConfig()
        self.model, self.tokenizer, self._mode = model, tok, "full"
        return self

    def _build_query(self, question, num_patches_list):
        get_conv = importlib.import_module(self.model.__class__.__module__).get_conv_template
        if "<image>" not in question:
            question = "<image>\n" + question
        tmpl = get_conv(self.model.template)
        tmpl.system_message = self.model.system_message
        eos = self.tokenizer.convert_tokens_to_ids(tmpl.sep.strip())
        tmpl.append_message(tmpl.roles[0], question)
        tmpl.append_message(tmpl.roles[1], None)
        query = tmpl.get_prompt()
        for npatch in num_patches_list:
            tags = IMG_START_TOKEN + IMG_CONTEXT_TOKEN * self.model.num_image_token * npatch + IMG_END_TOKEN
            query = query.replace("<image>", tags, 1)
        mi = self.tokenizer(query, return_tensors="pt")
        return mi["input_ids"], mi["attention_mask"], eos

    @torch.no_grad()
    def answer_pixels(self, frame_paths, prompt, max_new_tokens=128):
        param = next(self.model.parameters())
        tiles = [_load_image(p, self.input_size) for p in frame_paths]
        pixel_values = torch.cat(tiles, dim=0).to(device=param.device, dtype=param.dtype)
        num_patches_list = [1] * len(frame_paths)
        tags = "".join("<image>\n" for _ in frame_paths)
        return self.model.chat(
            self.tokenizer, pixel_values, f"{tags}{prompt}",
            {"max_new_tokens": max_new_tokens, "do_sample": False},
            num_patches_list=num_patches_list)

    @torch.no_grad()
    def answer_codec_tokens(self, token_rows, prompt, max_new_tokens=128):
        param = next(self.model.parameters())
        n = token_rows.shape[0]
        vit_embeds = token_rows.to(device=param.device, dtype=param.dtype)
        tags = "".join("<image>\n" for _ in range(n))
        input_ids, attn, eos = self._build_query(f"{tags}{prompt}", [1] * n)
        dummy = torch.zeros(n, 3, self.input_size, self.input_size,
                            device=param.device, dtype=param.dtype)
        out = self.model.generate(
            pixel_values=dummy, visual_features=vit_embeds,
            input_ids=input_ids.to(param.device), attention_mask=attn.to(param.device),
            max_new_tokens=max_new_tokens, do_sample=False, eos_token_id=eos)
        return self.tokenizer.batch_decode(out, skip_special_tokens=True)[0].strip()

    @torch.no_grad()
    def judge(self, prompt, max_new_tokens=8):
        param = next(self.model.parameters())
        dummy = torch.zeros(1, 3, self.input_size, self.input_size,
                            device=param.device, dtype=param.dtype)
        return self.model.chat(
            self.tokenizer, dummy, f"<image>\n{prompt}",
            {"max_new_tokens": max_new_tokens, "do_sample": False})


class _VisionOnlyInternVL(torch.nn.Module):
    """InternViT + pixel_shuffle + mlp1 of an InternVL checkpoint, without the LLM/chat wrapper.
    Exposes the attributes InternVLBackbone's align side uses: vision_model, mlp1, pixel_shuffle,
    downsample_ratio."""

    def __init__(self, vision_model, mlp1, downsample_ratio):
        super().__init__()
        self.vision_model = vision_model
        self.mlp1 = mlp1
        self.downsample_ratio = downsample_ratio

    @staticmethod
    def pixel_shuffle(x, scale_factor=0.5):
        n, w, h, c = x.size()
        x = x.view(n, w, int(h * scale_factor), int(c / scale_factor))
        x = x.permute(0, 2, 1, 3).contiguous()
        x = x.view(n, int(h * scale_factor), int(w * scale_factor), int(c / (scale_factor * scale_factor)))
        return x.permute(0, 2, 1, 3).contiguous()

    @classmethod
    def from_checkpoint(cls, path):
        import json, os, glob
        from safetensors.torch import load_file
        from transformers.dynamic_module_utils import get_class_from_dynamic_module
        cfg = json.load(open(os.path.join(path, "config.json")))
        VCfg = get_class_from_dynamic_module("configuration_intern_vit.InternVisionConfig", path)
        VModel = get_class_from_dynamic_module("modeling_intern_vit.InternVisionModel", path)
        vcfg = VCfg(**{k: v for k, v in cfg["vision_config"].items() if k not in ("architectures", "model_type")})
        vision = VModel(vcfg)
        ds = float(cfg.get("downsample_ratio", 0.5))
        vit_hidden = int(cfg["vision_config"]["hidden_size"])
        llm_hidden = int((cfg.get("llm_config") or cfg.get("text_config"))["hidden_size"])
        mlp1 = torch.nn.Sequential(
            torch.nn.LayerNorm(vit_hidden * int(1 / ds) ** 2),
            torch.nn.Linear(vit_hidden * int(1 / ds) ** 2, llm_hidden),
            torch.nn.GELU(),
            torch.nn.Linear(llm_hidden, llm_hidden))
        vstate, mstate = {}, {}
        for shard in sorted(glob.glob(os.path.join(path, "*.safetensors"))):
            for k, v in load_file(shard).items():
                if k.startswith("vision_model."):
                    vstate[k[len("vision_model."):]] = v
                elif k.startswith("mlp1."):
                    mstate[k[len("mlp1."):]] = v
        missing, unexpected = vision.load_state_dict(vstate, strict=False)
        missing = [m for m in missing if "position_ids" not in m]
        assert not missing and not unexpected, f"vision weights mismatch: missing={missing[:5]} unexpected={unexpected[:5]}"
        mlp1.load_state_dict(mstate, strict=True)
        return cls(vision.to(torch.bfloat16), mlp1.to(torch.bfloat16), ds)
