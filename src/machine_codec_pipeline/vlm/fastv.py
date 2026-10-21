"""FastV token pruning inside the language model (QA-side baseline, tab:qa).

FastV (Chen et al., ECCV'24) observes that most visual tokens receive little
attention after the first few LLM layers, so it keeps only the top-scoring
visual tokens past a pruning layer K and drops the rest, cutting LLM FLOPs.

For the accuracy comparison in tab:qa we implement the *selection* faithfully
and realise the drop by ATTENTION MASKING (no query attends to a pruned visual
token from layer K on). Masking is accuracy-equivalent to physically dropping
the tokens -- the surviving tokens' and the answer token's representations are
identical either way -- while being far simpler and robust to the KV cache. We
therefore measure FastV's task accuracy, not its FLOPs (FLOPs/latency live in
the amortization study).

Faithful realisation on InternVL2.5 (InternLM2 LLM, eager attention):
  * Visual token positions are ``input_ids == img_context_token_id``.
  * At the pruning layer K we take that layer's real attention weights (obtained
    by forcing ``output_attentions=True`` on that one attention module, so RoPE
    and grouped-query attention are already applied by the model itself), read
    the last prefill query's attention to the visual columns, average over heads,
    and keep the top ``budget = k * n_frames`` visual tokens.
  * For every layer after K we add ``-inf`` to the pruned visual columns of the
    additive attention mask, for the prefill and every cached decode step.

Usage::

    with fastv_prune(model, k=64, layer_k=2):
        ans = qa_from_raw_frames(model, tok, frame_dir, q, opts, sample_count)
"""

from __future__ import annotations

import contextlib
import os

import torch

_DBG = os.environ.get("FASTV_DEBUG")
def _dbg(*a):
    if _DBG:
        print("[fastv-dbg]", *a, flush=True)


@contextlib.contextmanager
def fastv_prune(model, k: int, layer_k: int = 2, img_token_id: int | None = None):
    """Keep only the top ``k`` visual tokens/frame past decoder layer ``layer_k``.

    ``k``: retained visual tokens per frame (matched budget vs. ours/VisionZip).
    ``layer_k``: prune after this many decoder layers (FastV default 2).
    """
    img_token_id = img_token_id if img_token_id is not None else model.img_context_token_id
    inner = model.language_model.model if hasattr(model.language_model, "model") else model.language_model
    layers = inner.layers
    num_img_tok = model.num_image_token
    st: dict = {}
    handles = []

    # (1) capture visual-token positions from input_ids at the InternVL generate
    #     level. The language model itself only sees inputs_embeds (image features
    #     already substituted, input_ids=None), so we must grab input_ids here --
    #     this was the bug that made the whole pass a no-op.
    orig_generate = model.generate

    def patched_generate(*a, **kw):
        ids = kw.get("input_ids", None)
        if ids is None:
            for x in a:
                if torch.is_tensor(x) and x.dim() == 2 and x.dtype in (torch.long, torch.int):
                    ids = x; break
        st.pop("img_pos", None); st.pop("prune", None)
        if ids is not None:
            pos = (ids[0] == img_token_id).nonzero(as_tuple=True)[0]
            if pos.numel() > 0:
                st["img_pos"] = pos
                n_frames = max(1, pos.numel() // max(1, num_img_tok))
                st["budget"] = min(pos.numel(), k * n_frames)
        _dbg(f"generate: ids={'yes' if ids is not None else 'NONE'} img_pos={st.get('img_pos').numel() if 'img_pos' in st else 0} budget={st.get('budget')}")
        return orig_generate(*a, **kw)
    model.generate = patched_generate

    # (2) force the pruning layer's attention to expose weights; select keep/prune
    attn_mod = layers[layer_k].attention
    orig_attn_forward = attn_mod.forward

    def attn_forward(*args, **kwargs):
        kwargs["output_attentions"] = True
        out = orig_attn_forward(*args, **kwargs)
        if "img_pos" in st and "prune" not in st:
            aw = out[1]  # [bsz, heads, q_len, kv_len]
            if aw is not None and aw.dim() == 4 and aw.shape[2] > 1:
                pos = st["img_pos"].to(aw.device)
                last = aw[0, :, -1, :].mean(0)          # last query -> all keys
                scores = last.index_select(0, pos)      # over visual columns
                b = st["budget"]
                keep_local = torch.topk(scores, b).indices
                keep = pos.index_select(0, keep_local)
                mask = torch.ones(pos.numel(), dtype=torch.bool, device=pos.device)
                mask[keep_local] = False
                st["prune"] = pos[mask]                 # absolute cols to drop
                _dbg(f"select@layer{layer_k}: aw={tuple(aw.shape)} kept={keep.numel()} prune={st['prune'].numel()}")
        elif "img_pos" in st:
            _dbg(f"select: skipped (aw={None if out[1] is None else tuple(out[1].shape)} 'prune' already={'prune' in st})")
        return out
    attn_mod.forward = attn_forward

    # (3) mask pruned visual columns for every layer after K
    def make_mask_hook():
        def mask_hook(module, args, kwargs):
            prune = st.get("prune")
            if prune is None:
                return args, kwargs
            am = kwargs.get("attention_mask", None)
            idx = None
            if am is None and len(args) >= 2:
                am = args[1]; idx = 1
            if not torch.is_tensor(am) or am.dim() != 4:
                _dbg(f"mask_hook: am not-4D (type={type(am).__name__}) -> cannot mask"); return args, kwargs
            p = prune.to(am.device)
            p = p[p < am.shape[-1]]
            if p.numel():
                neg = torch.finfo(am.dtype).min
                am = am.clone()
                am[..., p] = neg
                if idx is None:
                    kwargs["attention_mask"] = am
                else:
                    args = list(args); args[idx] = am; args = tuple(args)
                _dbg(f"mask_hook APPLIED: masked {p.numel()} cols in am{tuple(am.shape)}")
            return args, kwargs
        return mask_hook
    for i in range(layer_k + 1, len(layers)):
        handles.append(layers[i].register_forward_pre_hook(make_mask_hook(), with_kwargs=True))

    try:
        yield model
    finally:
        for h in handles:
            h.remove()
        attn_mod.forward = orig_attn_forward
        model.generate = orig_generate
