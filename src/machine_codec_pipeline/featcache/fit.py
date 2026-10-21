"""Fit the shared feature-cache book (PCA bases, quantiser ranges, PQ codebooks) on donor tokens.

The book is amortised across all videos exactly like the frozen universal adapter
(same 32 donors, disjoint from every evaluation pool), so its bytes are not charged
per video — stated explicitly in the paper's accounting.
"""

from __future__ import annotations

from collections.abc import Iterable

import torch

from .codec import book_key, pool_tokens
from .pca import fit_pca, pca_project
from .pq import fit_pq
from .quant import fit_ranges, open_loop_residuals

DEFAULT_POOLS = (256, 64, 16, 4)
DEFAULT_PCAS: tuple[int | None, ...] = (None, 256, 64, 16)
DEFAULT_PQ: dict[int | None, tuple[int, ...]] = {64: (8, 16), 256: (16, 32), None: (32,)}
FULL_RES_FRAMES_FOR_K256 = 32      # keep 32 consecutive frames per donor at K=256 (memory)
PCA_FIT_MAX_ROWS = 200_000
PQ_FIT_MAX_ROWS = 100_000


def collect_pooled(donor_tokens: Iterable[torch.Tensor], pools: tuple[int, ...]) -> dict[int, torch.Tensor]:
    """donor_tokens yields [T, 256, C] per donor -> {K: [D, T_K, K, C] fp16} stacked over donors."""
    acc: dict[int, list[torch.Tensor]] = {k: [] for k in pools}
    for tok in donor_tokens:
        for k in pools:
            x = tok if k < 256 else tok[:FULL_RES_FRAMES_FOR_K256]
            acc[k].append(pool_tokens(x, k).to(torch.float16))
    return {k: torch.stack(v) for k, v in acc.items()}


def _subsample(x: torch.Tensor, n: int, seed: int) -> torch.Tensor:
    if x.shape[0] <= n:
        return x
    g = torch.Generator(device="cpu").manual_seed(seed)
    return x[torch.randperm(x.shape[0], generator=g)[:n]]


def fit_book(pooled: dict[int, torch.Tensor], pcas: tuple[int | None, ...] = DEFAULT_PCAS,
             pq: dict[int | None, tuple[int, ...]] | None = None, device: str = "cpu",
             seed: int = 0, log=print) -> dict:
    """pooled: {K: [D, T, K, C]} -> book {key: {'pca', 'range': {'abs','dpcm'}, 'pq': {M: books}}}."""
    pq = DEFAULT_PQ if pq is None else pq
    book: dict = {"meta": {"pools": sorted(pooled), "pcas": list(pcas), "pq": {str(k): v for k, v in pq.items()}}}
    for k, x in pooled.items():
        d_, t_, k_, c = x.shape
        flat = x.reshape(-1, c)
        for p in pcas:
            key = book_key(k, p)
            entry: dict = {}
            if p is not None:
                entry["pca"] = fit_pca(_subsample(flat, PCA_FIT_MAX_ROWS, seed), p, device=device)
                log(f"[fit] {key}: pca explained={entry['pca']['explained'].item():.3f}")
                pca_dev = {n: v.to(device) for n, v in entry["pca"].items()}
                coeff_seq = torch.stack([pca_project(x[i].to(device), pca_dev).cpu() for i in range(d_)])  # [D, T, K, p]
            else:
                coeff_seq = x.float()
            cflat = coeff_seq.reshape(-1, coeff_seq.shape[-1])
            lo, hi = fit_ranges(cflat, seed=seed)
            res = torch.cat([open_loop_residuals(coeff_seq[i]) for i in range(d_)]).reshape(-1, coeff_seq.shape[-1])
            rlo, rhi = fit_ranges(res, seed=seed)
            entry["range"] = {"abs": {"lo": lo, "hi": hi}, "dpcm": {"lo": rlo, "hi": rhi}}
            entry["pq"] = {}
            for m in pq.get(p, ()):
                entry["pq"][m] = fit_pq(_subsample(cflat, PQ_FIT_MAX_ROWS, seed), m, seed=seed, device=device)
                log(f"[fit] {key}: pq M={m} done")
            book[key] = entry
            log(f"[fit] {key}: ranges abs[{lo.min():.3f},{hi.max():.3f}] dpcm[{rlo.min():.3f},{rhi.max():.3f}]")
    return book
