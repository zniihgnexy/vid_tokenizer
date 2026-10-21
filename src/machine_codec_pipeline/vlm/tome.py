"""ToMe token merging on InternViT output (QA-side baseline, Part I / tab:qa).

ToMe (Bolya et al., ICLR'23) reduces vision tokens by *merging* similar token
pairs (bipartite soft matching) instead of selecting (VisionZip) or pruning
(FastV) -- the third training-free token-reduction family.

Faithful-port note (disclosed): the original ToMe merges progressively inside
the ViT blocks using attention keys. InternVL2.5's ``extract_feature`` needs the
intact 32x32 patch grid for its pixel-shuffle, so -- exactly like our VisionZip
realisation -- we apply the merging at the shared token-injection point, i.e. on
the 256 post-shuffle tokens, iterating ToMe's bipartite soft matching (<=50%
merged per round, size-weighted averaging) until the matched budget ``K`` is
reached. Matching metric is token-feature cosine similarity (the standard
post-hoc port when attention keys are folded away). Same injection point, same
prompt, same frames as ours-pooled / VisionZip / FastV -> directly comparable.

Usage::

    with tome_merge(model, k=64):
        ans = qa_from_raw_frames(model, tok, frame_dir, question, options)
"""

from __future__ import annotations

import contextlib

import torch


def _bipartite_merge_to_k(x: torch.Tensor, k: int) -> torch.Tensor:
    """Iterated ToMe bipartite soft matching: [tiles, T, H] -> [tiles, k, H].

    Alternate tokens form sets A/B; each A token proposes its most-similar B
    partner; the r highest-similarity proposals are merged (size-weighted mean,
    sizes tracked across rounds); r <= 50% of tokens per round, as in ToMe.
    """
    tiles, T, H = x.shape
    if k >= T:
        return x
    s = torch.ones(tiles, T, 1, device=x.device, dtype=x.dtype)  # token sizes
    while x.shape[1] > k:
        T = x.shape[1]
        r = min(T - k, T // 2)
        xa, xb = x[:, ::2], x[:, 1::2]
        sa, sb = s[:, ::2], s[:, 1::2]
        na = xa / xa.norm(dim=-1, keepdim=True).clamp_min(1e-6)
        nb = xb / xb.norm(dim=-1, keepdim=True).clamp_min(1e-6)
        sim = na @ nb.transpose(1, 2)                      # [tiles, A, B]
        best_val, best_b = sim.max(dim=-1)                 # each A's best partner
        order = best_val.argsort(dim=1, descending=True)
        merge_a, keep_a = order[:, :r], order[:, r:]
        # weighted accumulate merged A rows into their B partners
        wa, wb = xa * sa, xb * sb
        idx_h = merge_a.unsqueeze(-1).expand(-1, -1, H)
        src_w = torch.gather(wa, 1, idx_h)                 # [tiles, r, H]
        src_s = torch.gather(sa, 1, merge_a.unsqueeze(-1)) # [tiles, r, 1]
        tgt = torch.gather(best_b, 1, merge_a)             # [tiles, r]
        wb = wb.scatter_add(1, tgt.unsqueeze(-1).expand(-1, -1, H), src_w)
        sb = sb.scatter_add(1, tgt.unsqueeze(-1), src_s)
        xb_new = wb / sb
        keep_h = keep_a.unsqueeze(-1).expand(-1, -1, H)
        x = torch.cat([torch.gather(xa, 1, keep_h), xb_new], dim=1)
        s = torch.cat([torch.gather(sa, 1, keep_a.unsqueeze(-1)), sb], dim=1)
    return x


@contextlib.contextmanager
def tome_merge(model, k: int):
    """Patch ``model.extract_feature`` to return ToMe-merged tokens (budget k).

    Mirrors ``visionzip_reduce``: also sets ``model.num_image_token`` so the
    IMG_CONTEXT prompt expansion matches the reduced token count. Restores on
    exit.
    """
    orig_extract = model.extract_feature
    orig_num_tok = model.num_image_token

    def patched_extract(pixel_values):
        vit_embeds = orig_extract(pixel_values)            # [tiles, 256, H]
        return _bipartite_merge_to_k(vit_embeds, k)

    model.extract_feature = patched_extract
    model.num_image_token = k
    try:
        yield model
    finally:
        model.extract_feature = orig_extract
        model.num_image_token = orig_num_tok
