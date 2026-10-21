"""InstructBLIP-vicuna-7b backbone.

Vision tower: EVA-CLIP ViT-g (direct patch tokens). Unlike InternVL, the
visual tokens are NOT fed straight to the LLM -- they go through a Q-Former
(resampler, 32 learned query tokens) and a linear projection into Vicuna's
embedding space. Alignment target = EVA-CLIP layer-N hidden state.

Method order mirrors internvl.py so a side-by-side diff shows exactly where
the two paradigms differ:
  * preprocess: 224 + OpenAI-CLIP norm (vs InternVL 448 + ImageNet norm)
  * codec_to_llm_tokens: ViT -> Q-Former -> projection -> 32 tokens
    (vs InternVL ViT -> pixel_shuffle -> mlp1 -> 256 tokens)
  * answer_codec_tokens: inject via language_model.generate(inputs_embeds=...)
    (vs InternVL generate(visual_features=...))

NOTE: the eval-side Q-Former injection path is written against HuggingFace's
``InstructBlipForConditionalGeneration`` internals and is validated only once
the weights are present (acceptance stage 3). The align-side ViT forward is a
standard ViT and mirrors the InternVL implementation.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F
import torchvision.transforms as T
from PIL import Image
from torchvision.transforms.functional import InterpolationMode

from .base import VLMBackbone

DEFAULT_MODEL_PATH = "/mnt/nas/xinyizheng/instructblip-vicuna-7b"
# EVA-CLIP / BLIP image normalisation (OpenAI CLIP stats).
CLIP_MEAN = (0.48145466, 0.4578275, 0.40821073)
CLIP_STD = (0.26862954, 0.26130258, 0.27577711)


def _build_transform(input_size):
    return T.Compose([
        T.Lambda(lambda im: im.convert("RGB") if im.mode != "RGB" else im),
        T.Resize((input_size, input_size), interpolation=InterpolationMode.BICUBIC),
        T.ToTensor(),
        T.Normalize(mean=CLIP_MEAN, std=CLIP_STD),
    ])


def _load_image(path, input_size=224):
    image = Image.open(path).convert("RGB")
    return _build_transform(input_size)(image).unsqueeze(0)


class InstructBlipBackbone(VLMBackbone):
    name = "instructblip"

    def __init__(self, model_path=DEFAULT_MODEL_PATH, device="cuda",
                 dtype=torch.bfloat16, align_layer=20, input_size=224, **kw):
        super().__init__(model_path, device, dtype, align_layer, input_size, **kw)
        self._dims = None
        self.processor = None

    # ============================ align side ============================ #
    def load_align(self):
        """Vision tower + Q-Former + projection in fp32; LLM dropped."""
        from transformers import InstructBlipForConditionalGeneration
        model = InstructBlipForConditionalGeneration.from_pretrained(
            self.model_path, torch_dtype=torch.bfloat16, low_cpu_mem_usage=True)
        if hasattr(model, "language_model"):
            del model.language_model          # not needed for align / token capture
        model = model.float().eval()
        for p in model.parameters():
            p.requires_grad = False
        self.model = model.to(self.device)
        # The Q-Former is instruction-aware -> it needs instruction input_ids.
        # We encode one fixed neutral instruction so the captured codec tokens
        # are instruction-agnostic (parity with InternVL, where visual tokens
        # don't depend on the question).
        from transformers import AutoTokenizer
        self.qformer_tokenizer = AutoTokenizer.from_pretrained(
            self.model_path, subfolder="qformer_tokenizer", use_fast=False)
        self._mode = "align"
        return self

    def vit_dims(self):
        if self._dims is None:
            emb = self.model.vision_model.embeddings
            img = int(emb.image_size); patch = int(emb.patch_size)
            grid = img // patch
            self._dims = {
                "num_patches": grid * grid,
                "hidden_dim": int(emb.embed_dim) if hasattr(emb, "embed_dim")
                else int(self.model.vision_model.config.hidden_size),
                "num_layers": len(self.model.vision_model.encoder.layers),
                "image_size": img, "patch_size": patch, "grid": grid,
            }
        return self._dims

    def preprocess_for_vit(self, x_5d):
        n, c, t, h, w = x_5d.shape
        frames = x_5d.permute(0, 2, 1, 3, 4).reshape(n * t, c, h, w).float()
        frames = F.interpolate(frames, size=(self.input_size, self.input_size),
                               mode="bilinear", align_corners=False)
        mean = torch.tensor(CLIP_MEAN, device=frames.device).view(1, 3, 1, 1)
        std = torch.tensor(CLIP_STD, device=frames.device).view(1, 3, 1, 1)
        return (frames - mean) / std, n, t

    def _add_cls_and_pos(self, patch_embeds):
        # EVA-CLIP embeddings: class_embedding [1,1,H], position_embedding
        # [1, 1+num_patches, H]. Patch count is fixed (no interpolation needed
        # because the codec adapter already emits the native patch grid).
        emb = self.model.vision_model.embeddings
        b = patch_embeds.shape[0]
        cls = emb.class_embedding.expand(b, 1, -1).to(patch_embeds.dtype)
        x = torch.cat([cls, patch_embeds], dim=1)
        return x + emb.position_embedding[:, : x.shape[1], :].to(patch_embeds.dtype)

    def _run_first_n(self, hidden, num_layers):
        out = hidden
        for layer in self.model.vision_model.encoder.layers[:num_layers]:
            out = layer(out, attention_mask=None, output_attentions=False)
            if isinstance(out, tuple):
                out = out[0]
        return out

    @torch.no_grad()
    def oracle_hidden(self, x_5d, layer_idx):
        frames, n, t = self.preprocess_for_vit(x_5d)
        frames = frames.to(self.model.vision_model.embeddings.patch_embedding.weight.dtype)
        h = self.model.vision_model.embeddings(frames)
        h = self._run_first_n(h, layer_idx)
        return h.view(n, t, h.shape[-2], h.shape[-1]).contiguous()

    def codec_hidden(self, patch_embeds, layer_idx):
        return self._run_first_n(self._add_cls_and_pos(patch_embeds), layer_idx)

    @torch.no_grad()
    def codec_to_llm_tokens(self, patch_embeds):
        # codec -> full ViT -> post_layernorm -> Q-Former -> language_projection
        # -> [B, num_query_tokens, llm_hidden]
        h = self._run_first_n(self._add_cls_and_pos(patch_embeds),
                              self.vit_dims()["num_layers"])
        vm = self.model.vision_model
        if hasattr(vm, "post_layernorm"):
            h = vm.post_layernorm(h)
        b = h.shape[0]
        img_attn = torch.ones(h.shape[:-1], dtype=torch.long, device=h.device)
        query = self.model.query_tokens.expand(b, -1, -1).to(h.dtype)
        # neutral instruction, mirroring InstructBlipForConditionalGeneration.forward
        instr = self.extra.get("qformer_instruction", "")
        qt = self.qformer_tokenizer([instr] * b, return_tensors="pt",
                                    padding=True).to(h.device)
        q_attn = torch.ones(query.shape[:-1], dtype=torch.long, device=h.device)
        attn = torch.cat([q_attn, qt.attention_mask], dim=1)
        qout = self.model.qformer(
            input_ids=qt.input_ids, attention_mask=attn, query_embeds=query,
            encoder_hidden_states=h, encoder_attention_mask=img_attn,
            return_dict=True)
        query_output = qout.last_hidden_state[:, : query.shape[1], :]
        return self.model.language_projection(query_output)  # [B, 32, llm_hidden]

    # ============================ eval side ============================ #
    def load_full(self):
        from transformers import (InstructBlipForConditionalGeneration,
                                  InstructBlipProcessor)
        self.model = InstructBlipForConditionalGeneration.from_pretrained(
            self.model_path, torch_dtype=self.dtype,
            low_cpu_mem_usage=True).eval().to(self.device)
        for p in self.model.parameters():
            p.requires_grad = False
        # use_fast=False: the checkpoint's tokenizer.json is newer than the
        # tokenizers lib pinned in this env (transformers 4.37.2); the slow
        # SentencePiece tokenizer loads cleanly and is functionally identical.
        self.processor = InstructBlipProcessor.from_pretrained(
            self.model_path, use_fast=False)
        self.tokenizer = self.processor.tokenizer
        self._mode = "full"
        return self

    @torch.no_grad()
    def answer_pixels(self, frame_paths, prompt, max_new_tokens=128):
        # Multi-frame: InstructBLIP is single-image; we tile sampled frames into
        # one grid image so all frames share one forward (keeps parity with the
        # codec path, which also summarises all frames jointly).
        imgs = [Image.open(p).convert("RGB") for p in frame_paths]
        grid = _tile_grid(imgs, self.input_size)
        inputs = self.processor(images=grid, text=prompt, return_tensors="pt").to(
            self.device, self.dtype)
        out = self.model.generate(**inputs, do_sample=False, max_new_tokens=max_new_tokens)
        return self.processor.batch_decode(out, skip_special_tokens=True)[0].strip()

    @torch.no_grad()
    def answer_codec_tokens(self, token_rows, prompt, max_new_tokens=128):
        # token_rows: [N_frames, num_query_tokens, llm_hidden] (already in
        # Vicuna's embedding space, produced by codec_to_llm_tokens at capture).
        param = next(self.model.language_model.parameters())
        visual_embeds = token_rows.reshape(1, -1, token_rows.shape[-1]).to(
            device=param.device, dtype=param.dtype)
        text = self.processor(text=prompt, return_tensors="pt").to(self.device)
        input_ids = text["input_ids"]
        text_embeds = self.model.language_model.get_input_embeddings()(input_ids)
        inputs_embeds = torch.cat([visual_embeds, text_embeds], dim=1)
        vis_mask = torch.ones(visual_embeds.shape[:-1], dtype=torch.long,
                              device=self.device)
        attn = torch.cat([vis_mask, text["attention_mask"]], dim=1)
        out = self.model.language_model.generate(
            inputs_embeds=inputs_embeds, attention_mask=attn,
            do_sample=False, max_new_tokens=max_new_tokens)
        return self.processor.batch_decode(out, skip_special_tokens=True)[0].strip()

    @torch.no_grad()
    def judge(self, prompt, max_new_tokens=8):
        # Text-only: Vicuna chat format so it answers (not continues), and
        # decode ONLY the generated continuation (generate returns prompt+new).
        wrapped = f"USER: {prompt}\nASSISTANT:"
        text = self.processor(text=wrapped, return_tensors="pt").to(self.device)
        inp_len = text["input_ids"].shape[1]
        out = self.model.language_model.generate(
            input_ids=text["input_ids"], attention_mask=text["attention_mask"],
            do_sample=False, max_new_tokens=max_new_tokens)
        new = out[:, inp_len:]
        return self.processor.batch_decode(new, skip_special_tokens=True)[0].strip()


def _tile_grid(images, cell, cols=2):
    """Compose up to a few frames into one square-ish grid image."""
    import math
    n = len(images)
    cols = min(cols, n)
    rows = math.ceil(n / cols)
    canvas = Image.new("RGB", (cols * cell, rows * cell))
    for i, im in enumerate(images):
        canvas.paste(im.resize((cell, cell)), ((i % cols) * cell, (i // cols) * cell))
    return canvas
