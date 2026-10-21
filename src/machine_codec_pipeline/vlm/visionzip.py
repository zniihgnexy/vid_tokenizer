"""VisionZip token reduction on InternViT (QA-side baseline, Part I / tab:qa).

VisionZip (Yang et al., CVPR'25) keeps a small set of *dominant* visual tokens
(those that receive the most attention from the vision encoder's CLS token) and
merges the rest into a few *contextual* tokens. It is training-free and drops in
after the vision tower, which is exactly our token-injection point, so it is the
fair QA-side counterpart to our cached, pooled representation.

Faithful realisation on InternVL2.5:
  * InternViT (``model.vision_model``) uses eager attention (``use_flash_attn``
    is False), so the last block's CLS->patch attention is recoverable. We
    register a forward hook on the last ``InternAttention`` and recompute the
    CLS row from that block's own ``qkv`` weights (one extra matmul, last layer
    only), giving a per-patch importance over the 1024 patches.
  * ``extract_feature`` then pixel-shuffles the 32x32 patch grid to a 16x16 grid
    of 256 tokens (each output token = one 2x2 patch block). We 2x2 average-pool
    the 1024-patch importance to 256, matching that spatial folding.
  * We keep the top ``K - C`` tokens by importance (dominant) and mean-merge the
    remaining tokens into ``C`` contextual tokens, for a matched budget of ``K``
    tokens/frame. ``model.num_image_token`` is set to ``K`` so the prompt sizes
    the IMG_CONTEXT expansion correctly.

Usage::

    with visionzip_reduce(model, k=64):
        vit_embeds = extract_internvit_tokens(model, pixel_values)  # [tiles, K, H]
        ans = chat_embeds(model, tok, vit_embeds, num_patches_list, question)
"""

from __future__ import annotations

import contextlib
import math

import torch


def _cls_patch_importance(attn_module, hidden_states: torch.Tensor) -> torch.Tensor:
    """Recompute the CLS->patch attention of one InternAttention block.

    Returns per-patch importance ``[B, num_patches]`` (mean over heads), where
    ``num_patches = N - 1`` (token 0 is the CLS token).
    """
    B, N, C = hidden_states.shape
    h = attn_module.num_heads
    qkv = attn_module.qkv(hidden_states)
    qkv = qkv.reshape(B, N, 3, h, C // h).permute(2, 0, 3, 1, 4)
    q, k, _ = qkv.unbind(0)  # [B, h, N, d]
    if getattr(attn_module, "qk_normalization", False):
        B_, H_, N_, D_ = q.shape
        q = attn_module.q_norm(q.transpose(1, 2).flatten(-2, -1)).view(B_, N_, H_, D_).transpose(1, 2)
        k = attn_module.k_norm(k.transpose(1, 2).flatten(-2, -1)).view(B_, N_, H_, D_).transpose(1, 2)
    # CLS query (row 0) attends over all keys; keep patch columns (drop CLS col).
    q_cls = q[:, :, :1, :] * attn_module.scale          # [B, h, 1, d]
    attn = (q_cls @ k.transpose(-2, -1)).softmax(dim=-1)  # [B, h, 1, N]
    cls_to_patch = attn[:, :, 0, 1:]                      # [B, h, N-1]
    return cls_to_patch.mean(dim=1).float()              # [B, N-1]


def _patch_to_token_importance(patch_imp: torch.Tensor) -> torch.Tensor:
    """2x2 average-pool patch importance [B, P] onto the 256 shuffled tokens."""
    B, P = patch_imp.shape
    g = int(round(math.sqrt(P)))          # 32 for 1024 patches
    grid = patch_imp.reshape(B, 1, g, g)
    pooled = torch.nn.functional.avg_pool2d(grid, kernel_size=2, stride=2)  # [B,1,16,16]
    return pooled.reshape(B, -1)          # [B, 256], row-major (matches pixel_shuffle)


def _reduce(vit_embeds: torch.Tensor, importance: torch.Tensor, k: int, n_ctx: int) -> torch.Tensor:
    """Keep top ``k-n_ctx`` dominant tokens + ``n_ctx`` merged contextual tokens.

    ``vit_embeds``: [tiles, T, H]; ``importance``: [tiles, T]. Returns [tiles, k, H].
    """
    tiles, T, H = vit_embeds.shape
    if k >= T:
        return vit_embeds
    n_dom = max(1, k - n_ctx)
    n_ctx = k - n_dom
    order = importance.argsort(dim=1, descending=True)          # [tiles, T]
    dom_idx = order[:, :n_dom]                                  # [tiles, n_dom]
    dom = torch.gather(vit_embeds, 1, dom_idx.unsqueeze(-1).expand(-1, -1, H))
    if n_ctx <= 0:
        return dom
    rest_idx = order[:, n_dom:]                                 # [tiles, T-n_dom]
    rest = torch.gather(vit_embeds, 1, rest_idx.unsqueeze(-1).expand(-1, -1, H))
    # Split the (importance-ordered) remainder into n_ctx contiguous groups and
    # mean-pool each -> contextual tokens (VisionZip's merge step, simplified).
    groups = torch.tensor_split(rest, n_ctx, dim=1)
    ctx = torch.stack([g.mean(dim=1) for g in groups], dim=1)   # [tiles, n_ctx, H]
    return torch.cat([dom, ctx], dim=1)                        # [tiles, k, H]


@contextlib.contextmanager
def visionzip_reduce(model, k: int, ctx_ratio: float = 0.15):
    """Patch ``model.extract_feature`` to return VisionZip-reduced tokens.

    ``k``: total tokens/frame budget. ``ctx_ratio``: fraction of ``k`` used as
    contextual (merged) tokens; the rest are dominant. Restores on exit.
    """
    n_ctx = max(1, int(round(k * ctx_ratio))) if k > 4 else 0
    last_attn = model.vision_model.encoder.layers[-1].attn
    orig_extract = model.extract_feature
    orig_num_tok = model.num_image_token
    holder: dict = {}

    def _hook(module, inputs, output):
        holder["imp"] = _cls_patch_importance(module, inputs[0])

    handle = last_attn.register_forward_hook(_hook)

    def patched_extract(pixel_values):
        holder.clear()
        vit_embeds = orig_extract(pixel_values)            # [tiles, 256, H]
        patch_imp = holder.get("imp")
        if patch_imp is None:                              # hook did not fire; fall back
            return vit_embeds
        tok_imp = _patch_to_token_importance(patch_imp).to(vit_embeds.device)
        if tok_imp.shape[1] != vit_embeds.shape[1]:        # shape guard
            return vit_embeds
        return _reduce(vit_embeds, tok_imp, k, n_ctx)

    model.extract_feature = patched_extract
    model.num_image_token = k
    try:
        yield model
    finally:
        handle.remove()
        model.extract_feature = orig_extract
        model.num_image_token = orig_num_tok
