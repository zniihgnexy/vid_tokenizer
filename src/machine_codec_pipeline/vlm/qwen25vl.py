"""Qwen2.5-VL-7B-Instruct backbone (third VLM backbone, distinct architecture).

Vision tower: Qwen2.5-VL native-resolution ViT -- 32 blocks, hidden 1280, patch 14,
temporal_patch_size=2, spatial_merge_size=2, WINDOW attention on all blocks except
fullatt_block_indexes {7,15,23,31}. After the 32 blocks a PatchMerger (RMSNorm +
2-layer MLP over each 2x2 spatial group) projects 4*1280 -> out_hidden_size=3584,
which the Qwen2.5 LLM consumes directly (there is NO `mm_vision_select_layer=-2`
scheme like SigLIP -- the merger output IS the projected token stream).

Empirically (256px frame): grid_thw=[1,18,18] -> 324 pre-merger patches [324,1280]
-> 81 merged LLM tokens [81,3584].

Alignment layer choice (documented for EXP notes):
  Analogous to InternVL (mid, N=12 of 24) we align at the MID vision block N=16 of 32
  for the hidden-consistency loss (the "pathway_b_mid" philosophy). The codec adapter's
  patch embeddings are routed through the frozen ViT blocks 1..N (reusing the tower's OWN
  rotary-pos-emb / window-index / cu_seqlens machinery) and aligned to the oracle's
  block-N hidden state; at eval, codec features are routed 1..32 + merger to produce the
  3584-dim tokens the LLM consumes.

CRITICAL (per EXP-028): we take the model's OWN fine-tuned vision tower (loaded from the
full Qwen2.5-VL checkpoint), never a vanilla HF vision model.

CAVEATS vs LLaVA/SigLIP (flagged for validation):
  * temporal_patch_size=2: Qwen pairs consecutive frames into one temporal patch. We
    duplicate each frame (t-pair = [frame, frame]) so every VLM "frame" == one temporal
    patch, matching the per-frame codec token layout used elsewhere.
  * variable resolution: we FIX the frame size (default 252px -> grid 18x18) so grid_thw
    is deterministic and the codec produces a fixed patch count, matching CodecAdapter.
  * window attention: routing arbitrary patch embeddings through the blocks requires the
    tower's window_index/rotary machinery -- reused verbatim from the frozen tower.
"""

from __future__ import annotations

import glob
import os

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

from .base import VLMBackbone

DEFAULT_MODEL_PATH = os.environ.get(
    "QWEN25VL_PATH",
    glob.glob(os.path.expanduser(
        "~/.cache/huggingface/hub/models--Qwen--Qwen2.5-VL-7B-Instruct/snapshots/*"))[0]
    if glob.glob(os.path.expanduser(
        "~/.cache/huggingface/hub/models--Qwen--Qwen2.5-VL-7B-Instruct/snapshots/*"))
    else "Qwen/Qwen2.5-VL-7B-Instruct",
)
# Qwen2.5-VL image mean/std (OPENAI_CLIP defaults used by Qwen2VLImageProcessor).
QWEN_MEAN = (0.48145466, 0.4578275, 0.40821073)
QWEN_STD = (0.26862954, 0.26130258, 0.27577711)
QWEN_MID_N = 16          # of 32 vision blocks (mid, analog to InternVL N=12/24)
FIX_SIZE = 252           # 18*14; deterministic 18x18 patch grid -> 81 merged tokens/frame


class Qwen25VLBackbone(VLMBackbone):
    name = "qwen25vl"

    def __init__(self, model_path=DEFAULT_MODEL_PATH, device="cuda",
                 dtype=torch.bfloat16, align_layer=QWEN_MID_N, input_size=FIX_SIZE, **kw):
        super().__init__(model_path, device, dtype, align_layer, input_size, **kw)
        self._dims = None
        self.processor = None
        self._vt = None      # standalone fine-tuned vision tower (align mode)
        self._full = None

    # ============================ align side ============================ #
    def load_align(self):
        """Load the full Qwen2.5-VL, keep its OWN fine-tuned vision tower, drop the LLM
        decoder layers to reclaim memory. Needs transformers>=4.49 (vidtok_qwen env)."""
        import gc
        from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
        model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            self.model_path, dtype=self.dtype, device_map=self.device,
            attn_implementation="sdpa").eval()
        self.processor = AutoProcessor.from_pretrained(self.model_path)
        vt = getattr(model, "visual", None) or model.model.visual
        try:  # free the Qwen2.5 decoder blocks (unused for align) to reclaim ~14GB
            model.model.layers = torch.nn.ModuleList()
            gc.collect(); torch.cuda.empty_cache()
        except Exception:
            pass
        vt = vt.to(self.device).float().eval()
        for p in vt.parameters():
            p.requires_grad = False
        self._vt = vt
        self._full = model            # keep alive: vt is its submodule
        self.model = vt               # base.py uses self.model generically
        self._mode = "align"
        return self

    def vit_dims(self):
        if self._dims is None:
            vt = self._vt
            grid = self.input_size // vt.config.patch_size   # 18
            self._dims = {
                "num_patches": grid * grid,                  # 324 (pre-merger, per frame)
                "hidden_dim": vt.config.hidden_size,         # 1280
                "num_layers": len(vt.blocks),                # 32
                "image_size": self.input_size, "patch_size": vt.config.patch_size,
                "grid": grid, "merge": vt.config.spatial_merge_size,
                "llm_dim": vt.config.out_hidden_size,        # 3584
            }
        return self._dims

    def preprocess_for_vit(self, x_5d):
        """[N,C,T,H,W] in [0,1] -> [N*T,3,S,S] CLIP-normalised at the fixed grid size."""
        n, c, t, h, w = x_5d.shape
        frames = x_5d.permute(0, 2, 1, 3, 4).reshape(n * t, c, h, w).float()
        frames = F.interpolate(frames, size=(self.input_size, self.input_size),
                               mode="bicubic", align_corners=False, antialias=True)
        mean = torch.tensor(QWEN_MEAN, device=frames.device).view(1, 3, 1, 1)
        std = torch.tensor(QWEN_STD, device=frames.device).view(1, 3, 1, 1)
        return (frames - mean) / std, n, t

    def _grid_thw(self, n_frames):
        """Deterministic grid for fixed-size frames; temporal_patch_size handled by
        pairing each frame with itself so one frame == one temporal patch."""
        g = self.input_size // self._vt.config.patch_size
        # one row per frame: (t=1, h=g, w=g) -- temporal pairing done in _patchify.
        return torch.tensor([[1, g, g]] * n_frames, device=self.device, dtype=torch.long)

    def _patchify(self, frames_nt3ss):
        """[F,3,S,S] -> Qwen flat patch tensor [F*g*g, 3*tp*P*P] with each frame duplicated
        across temporal_patch_size, matching Qwen2VLImageProcessor's layout."""
        vt = self._vt
        P = vt.config.patch_size; tp = vt.config.temporal_patch_size
        ms = vt.config.spatial_merge_size
        Fr, C, S, _ = frames_nt3ss.shape
        g = S // P
        # temporal pair: duplicate each frame tp times along a new temporal axis
        x = frames_nt3ss.unsqueeze(1).repeat(1, tp, 1, 1, 1)   # [F,tp,3,S,S]
        x = x.reshape(Fr, tp, C, g, P, g, P)
        # Qwen patch order: (grid_t, grid_h//ms, grid_w//ms, ms, ms, C, tp, P, P)
        x = x.reshape(Fr, tp, C, g // ms, ms, P, g // ms, ms, P)
        x = x.permute(0, 3, 6, 4, 7, 2, 1, 5, 8)               # F, gh, gw, ms, ms, C, tp, P, P
        x = x.reshape(Fr * g * g, C * tp * P * P)
        return x.to(self._vt.patch_embed.proj.weight.dtype)

    def _prep(self, hidden, grid_thw):
        """Replicate Qwen2_5_VisionTransformer.forward window/rotary setup for a given
        post-patch_embed hidden [seq,1280]. Returns hidden(window-ordered), pos_emb,
        cu_seqlens, cu_window_seqlens, window_index."""
        vt = self._vt
        rot = vt.rot_pos_emb(grid_thw)
        window_index, cu_window_seqlens = vt.get_window_index(grid_thw)
        cu_window_seqlens = torch.tensor(cu_window_seqlens, device=hidden.device, dtype=torch.int32)
        cu_window_seqlens = torch.unique_consecutive(cu_window_seqlens)
        seq = hidden.shape[0]; smu = vt.spatial_merge_unit
        hidden = hidden.reshape(seq // smu, smu, -1)[window_index, :, :].reshape(seq, -1)
        rot = rot.reshape(seq // smu, smu, -1)[window_index, :, :].reshape(seq, -1)
        emb = torch.cat((rot, rot), dim=-1)
        pos = (emb.cos(), emb.sin())
        cu = torch.repeat_interleave(grid_thw[:, 1] * grid_thw[:, 2], grid_thw[:, 0]).cumsum(
            0, dtype=torch.int32)
        cu = F.pad(cu, (1, 0), value=0)
        return hidden, pos, cu, cu_window_seqlens, window_index

    def _run_blocks(self, hidden, pos, cu, cuw, start, stop):
        vt = self._vt
        for ln in range(start, stop):
            blk = vt.blocks[ln]
            cs = cu if ln in vt.fullatt_block_indexes else cuw
            hidden = blk(hidden, cu_seqlens=cs, position_embeddings=pos)
        return hidden

    @torch.no_grad()
    def oracle_hidden(self, x_5d, layer_idx):
        """Real frames -> patch_embed -> ViT blocks 1..layer_idx. [N,T,tok,dim] window-order."""
        frames, n, t = self.preprocess_for_vit(x_5d)
        grid = self._grid_thw(n * t)
        patches = self._patchify(frames)
        hidden = self._vt.patch_embed(patches)               # [seq,1280]
        hidden, pos, cu, cuw, _ = self._prep(hidden, grid)
        hidden = self._run_blocks(hidden, pos, cu, cuw, 0, layer_idx)
        tok = hidden.shape[0] // (n * t)
        return hidden.view(n, t, tok, hidden.shape[-1]).contiguous()

    def codec_hidden(self, patch_embeds, layer_idx):
        """CodecAdapter patch embeds [B,tok,1280] -> ViT blocks 1..layer_idx (grad flows)."""
        b, tok, d = patch_embeds.shape
        grid = self._grid_thw(b)
        hidden = patch_embeds.reshape(b * tok, d)
        hidden, pos, cu, cuw, _ = self._prep(hidden, grid)
        hidden = self._run_blocks(hidden, pos, cu, cuw, 0, layer_idx)
        return hidden

    @torch.no_grad()
    def codec_to_llm_tokens(self, patch_embeds):
        """CodecAdapter patch embeds -> full 32 blocks + merger -> [n_merged,3584] LLM tokens."""
        b, tok, d = patch_embeds.shape
        grid = self._grid_thw(b)
        hidden = patch_embeds.reshape(b * tok, d)
        hidden, pos, cu, cuw, widx = self._prep(hidden, grid)
        hidden = self._run_blocks(hidden, pos, cu, cuw, 0, len(self._vt.blocks))
        hidden = self._vt.merger(hidden)
        hidden = hidden[torch.argsort(widx), :]
        return hidden

    # ============================ eval side ============================ #
    def load_full(self):
        from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            self.model_path, dtype=self.dtype, device_map=self.device,
            attn_implementation="sdpa").eval()
        self.processor = AutoProcessor.from_pretrained(self.model_path)
        self.tokenizer = self.processor.tokenizer
        self._mode = "full"
        return self

    def _pil(self, frame_paths):
        return [Image.open(p).convert("RGB").resize((self.input_size, self.input_size))
                for p in frame_paths]

    @torch.no_grad()
    def answer_pixels(self, frame_paths, prompt, max_new_tokens=64):
        imgs = self._pil(frame_paths)
        msgs = [{"role": "user", "content": [{"type": "video", "video": imgs},
                                             {"type": "text", "text": prompt}]}]
        text = self.processor.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        inputs = self.processor(text=[text], videos=[imgs], return_tensors="pt").to(self.device)
        out = self.model.generate(**inputs, do_sample=False, max_new_tokens=max_new_tokens)
        gen = out[:, inputs["input_ids"].shape[1]:]
        return self.processor.batch_decode(gen, skip_special_tokens=True)[0].strip()

    @torch.no_grad()
    def answer_codec_tokens(self, token_rows, prompt, max_new_tokens=64):
        """token_rows = codec merger-space tokens [n_merged_total,3584] (from
        codec_to_llm_tokens). Inject them at the video placeholder positions by replacing
        the vision embeds after the LLM embeds the text+placeholder ids."""
        feats = token_rows.to(self.device, self.dtype)
        n_vis = feats.shape[0]
        # build ids with a video placeholder sized to n_vis tokens
        vid_tok = self.model.config.video_token_id
        msgs = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
        text = self.processor.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        ids = self.processor.tokenizer(text, return_tensors="pt").input_ids.to(self.device)
        # splice n_vis video tokens after the first token
        vis = torch.full((1, n_vis), vid_tok, device=self.device, dtype=ids.dtype)
        ids = torch.cat([ids[:, :1], vis, ids[:, 1:]], dim=1)
        emb = self.model.get_input_embeddings()(ids)
        mask = (ids == vid_tok)
        emb[mask] = feats.to(emb.dtype)
        out = self.model.generate(inputs_embeds=emb, do_sample=False, max_new_tokens=max_new_tokens)
        return self.processor.batch_decode(out, skip_special_tokens=True)[0].strip()

    @torch.no_grad()
    def judge(self, prompt, max_new_tokens=8):
        ids = self.processor.tokenizer(prompt, return_tensors="pt").input_ids.to(self.device)
        out = self.model.generate(ids, do_sample=False, max_new_tokens=max_new_tokens)
        return self.processor.tokenizer.batch_decode(
            out[:, ids.shape[1]:], skip_special_tokens=True)[0].strip()
