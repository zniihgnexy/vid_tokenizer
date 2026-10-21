"""LLaVA-Video-7B-Qwen2 backbone (second VLM backbone, video-capable).

Vision tower: SigLIP so400m-patch14-384 (1152-dim, 384px, 27x27=729 patches, NO
CLS token). LLM: Qwen2-7B (3584-dim). Projector: mlp2x_gelu (1152->3584). The LLM
consumes SigLIP `hidden_states[-2]` == output after the first 26 of 27 encoder
layers, so alignment layer N=26.

Two sides (run in the same env as InternVL/InstructBLIP once compressai is present):
  * align side  -- standalone transformers.SiglipVisionModel (no llava dep). Used
    inside NVRC training for the hidden-consistency loss. SigLIP has no class token,
    so codec_hidden just adds the position embedding (simpler than internvl/blip).
  * eval side   -- full llava model via llava.model.builder.load_pretrained_model.
    The codec path saves SigLIP layer-26 features [T,729,1152]; answer_codec_tokens
    runs mm_projector -> get_2dPool -> add_token_per_grid (the llava video pipeline)
    by overriding encode_images and reusing prepare_inputs_labels_for_multimodal.

Method order mirrors instructblip.py / internvl.py for a side-by-side diff.
"""

from __future__ import annotations

import glob
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

from .base import VLMBackbone

DEFAULT_MODEL_PATH = "/mnt/nas/xinyizheng/llava_video/LLaVA-Video-7B-Qwen2"
SIGLIP_ID = "google/siglip-so400m-patch14-384"
SIGLIP_MEAN = (0.5, 0.5, 0.5)
SIGLIP_STD = (0.5, 0.5, 0.5)
SIGLIP_SELECT_N = 26  # first-26 of 27 layers == mm_vision_select_layer=-2 (EVAL routing to projector -- FIXED)
SIGLIP_MID_N = 13     # ALIGNMENT layer: mid of the 26 used layers (mirrors InternVL's mid 12/24).
# Rationale (EXP-021/022 + user 2026-07-06 controlled-variable fix): InternVL aligns at MID (best;
# final/near-final is worse). The old LLaVA align at near-final N=26 was NOT a controlled replicate
# of pathway_b_mid; aligning at mid N=13 + routing codec through frozen 14..26 + projector (codec_to_llm
# keeps SELECT_N=26) makes backbone the only variable vs InternVL.


class LlavaVideoBackbone(VLMBackbone):
    name = "llava_video"

    def __init__(self, model_path=DEFAULT_MODEL_PATH, device="cuda",
                 dtype=torch.bfloat16, align_layer=SIGLIP_MID_N, input_size=384, **kw):
        super().__init__(model_path, device, dtype, align_layer, input_size, **kw)
        self._dims = None
        self.image_processor = None
        self._tower = None  # standalone SigLIP (align mode)

    # ============================ align side ============================ #
    def load_align(self):
        """Use the LLaVA model's OWN (fine-tuned) SigLip tower as the alignment target.
        LLaVA-Video fine-tunes its vision tower, so vanilla google/siglip mismatches what
        the projector consumes (cos~0.64). We load the full model, take its fine-tuned
        tower, and drop the LLM blocks to save memory. Runs in the cloned env (has llava)."""
        import gc
        from llava.model.builder import load_pretrained_model
        _, model, ip, _ = load_pretrained_model(
            self.model_path, None, "llava_qwen", torch_dtype="bfloat16",
            device_map="cuda", attn_implementation="sdpa")
        tower = model.get_model().get_vision_tower()  # fine-tuned SigLipVisionTower
        try:  # free the Qwen2 decoder blocks (unused for align) to reclaim ~14GB
            model.get_model().layers = torch.nn.ModuleList()
            gc.collect(); torch.cuda.empty_cache()
        except Exception:
            pass
        self.image_processor = ip
        self._full = model  # keep alive: tower is its submodule
        tower = tower.to(self.device).float().eval()
        for p in tower.parameters():
            p.requires_grad = False
        self._tower = tower
        self.model = tower  # base.py uses self.model generically
        self._mode = "align"
        return self

    def _vm(self):
        return self._tower.vision_tower.vision_model

    def vit_dims(self):
        if self._dims is None:
            emb = self._vm().embeddings
            img = int(emb.image_size); patch = int(emb.patch_size)
            grid = img // patch
            self._dims = {
                "num_patches": grid * grid,        # 729
                "hidden_dim": int(emb.embed_dim),  # 1152
                "num_layers": len(self._vm().encoder.layers),  # 27
                "image_size": img, "patch_size": patch, "grid": grid,
            }
        return self._dims

    def preprocess_for_vit(self, x_5d):
        n, c, t, h, w = x_5d.shape
        frames = x_5d.permute(0, 2, 1, 3, 4).reshape(n * t, c, h, w).float()
        # match llava SigLipImageProcessor: BICUBIC resize to 384 + (0.5,0.5,0.5) norm.
        frames = F.interpolate(frames, size=(self.input_size, self.input_size),
                               mode="bicubic", align_corners=False, antialias=True)
        mean = torch.tensor(SIGLIP_MEAN, device=frames.device).view(1, 3, 1, 1)
        std = torch.tensor(SIGLIP_STD, device=frames.device).view(1, 3, 1, 1)
        return (frames - mean) / std, n, t

    def _add_pos(self, patch_embeds):
        # SigLIP has NO class token; just add the (interpolation-free) position emb.
        emb = self._vm().embeddings
        pos = emb.position_embedding(emb.position_ids)  # [1, 729, 1152]
        return patch_embeds + pos.to(patch_embeds.dtype)

    def _run_first_n(self, hidden, num_layers):
        out = hidden
        for layer in self._vm().encoder.layers[:num_layers]:
            # SiglipEncoderLayer.forward(hidden_states, attention_mask, ...) ->
            # attention_mask is a REQUIRED positional arg; returns a tuple.
            out = layer(out, attention_mask=None, output_attentions=False)
            if isinstance(out, tuple):
                out = out[0]
        return out

    @torch.no_grad()
    def oracle_hidden(self, x_5d, layer_idx):
        # llava tower output = vision_tower(px).hidden_states[-1] (raw encoder output of the
        # last-layer-deleted 26-layer model; NO post_layernorm). Replicate via the SAME
        # llava vision_model so the target == what the projector consumes.
        frames, n, t = self.preprocess_for_vit(x_5d)
        frames = frames.to(self._vm().embeddings.patch_embedding.weight.dtype)
        h = self._vm().embeddings(frames)         # [N*T, 729, 1152]
        h = self._run_first_n(h, layer_idx)       # all 26 layers; no post_layernorm
        return h.view(n, t, h.shape[-2], h.shape[-1]).contiguous()

    def codec_hidden(self, patch_embeds, layer_idx):
        return self._run_first_n(self._add_pos(patch_embeds), layer_idx)

    @torch.no_grad()
    def codec_to_llm_tokens(self, patch_embeds):
        # Save the tower-matching layer-26 features [T,729,1152]; eval applies projector+pool+newline.
        return self._run_first_n(self._add_pos(patch_embeds), SIGLIP_SELECT_N)

    # ============================ eval side ============================ #
    def load_full(self):
        from llava.model.builder import load_pretrained_model
        tok, model, image_processor, _ = load_pretrained_model(
            self.model_path, None, "llava_qwen", torch_dtype="bfloat16",
            device_map="cuda", attn_implementation="sdpa")
        model.eval()
        self.model = model
        self.tokenizer = tok
        self.image_processor = image_processor
        self._mode = "full"
        return self

    def _frames_to_video(self, frame_paths):
        arr = np.stack([np.array(Image.open(p).convert("RGB")) for p in frame_paths])
        return self.image_processor.preprocess(arr, return_tensors="pt")["pixel_values"].to(
            self.model.device, torch.bfloat16)

    def _gen(self, input_ids, images, max_new_tokens):
        out = self.model.generate(input_ids, images=images, modalities=["video"],
                                  do_sample=False, temperature=0, max_new_tokens=max_new_tokens)
        return self.tokenizer.batch_decode(out, skip_special_tokens=True)[0].strip()

    def _build_ids(self, prompt):
        import copy
        from llava.mm_utils import tokenizer_image_token
        from llava.constants import IMAGE_TOKEN_INDEX, DEFAULT_IMAGE_TOKEN
        from llava.conversation import conv_templates
        text = DEFAULT_IMAGE_TOKEN + "\n" + prompt
        conv = copy.deepcopy(conv_templates["qwen_1_5"])
        conv.append_message(conv.roles[0], text)
        conv.append_message(conv.roles[1], None)
        return tokenizer_image_token(conv.get_prompt(), self.tokenizer, IMAGE_TOKEN_INDEX,
                                     return_tensors="pt").unsqueeze(0).to(self.model.device)

    @torch.no_grad()
    def answer_pixels(self, frame_paths, prompt, max_new_tokens=64):
        video = self._frames_to_video(frame_paths)
        return self._gen(self._build_ids(prompt), [video], max_new_tokens)

    @torch.no_grad()
    def answer_codec_tokens(self, token_rows, prompt, max_new_tokens=64):
        # token_rows = codec SigLIP layer-26 feats [T, 729, 1152]. Override
        # encode_images to return projected codec feats so the unmodified
        # prepare_inputs_labels_for_multimodal does pool+newline+splice (video path).
        feats = token_rows.to(self.model.device, torch.bfloat16)  # [T,729,1152]
        T = feats.shape[0]
        proj = self.model.get_model().mm_projector(feats)  # [T,729,3584]
        orig = self.model.encode_images
        self.model.encode_images = lambda images: proj  # ignore dummy images
        try:
            dummy = torch.zeros(T, 3, self.input_size, self.input_size,
                                device=self.model.device, dtype=torch.bfloat16)
            ans = self._gen(self._build_ids(prompt), [dummy], max_new_tokens)
        finally:
            self.model.encode_images = orig
        return ans

    @torch.no_grad()
    def judge(self, prompt, max_new_tokens=8):
        ids = self.tokenizer(f"{prompt}", return_tensors="pt").input_ids.to(self.model.device)
        out = self.model.generate(ids, do_sample=False, max_new_tokens=max_new_tokens)
        return self.tokenizer.batch_decode(out[:, ids.shape[1]:], skip_special_tokens=True)[0].strip()
