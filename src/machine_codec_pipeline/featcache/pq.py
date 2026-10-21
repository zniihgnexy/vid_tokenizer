"""Product quantiser with donor-fitted codebooks (k-means in torch, no faiss dependency)."""

from __future__ import annotations

import torch

from .spec import PQ_CENTROIDS

KMEANS_ITERS = 25
ASSIGN_CHUNK = 65_536


def _kmeans(x: torch.Tensor, k: int, iters: int, gen: torch.Generator) -> torch.Tensor:
    """Lloyd k-means on x [N, s] -> centroids [k, s]. Empty clusters are re-seeded."""
    n = x.shape[0]
    cent = x[torch.randperm(n, generator=gen, device="cpu")[:k].to(x.device)].clone()
    for _ in range(iters):
        assign = torch.empty(n, dtype=torch.int64, device=x.device)
        for i in range(0, n, ASSIGN_CHUNK):
            assign[i:i + ASSIGN_CHUNK] = torch.cdist(x[i:i + ASSIGN_CHUNK], cent).argmin(dim=1)
        counts = torch.bincount(assign, minlength=k).float()
        sums = torch.zeros_like(cent).index_add_(0, assign, x)
        nonempty = counts > 0
        cent[nonempty] = sums[nonempty] / counts[nonempty].unsqueeze(1)
        if (~nonempty).any():
            reseed = x[torch.randperm(n, generator=gen, device="cpu")[: int((~nonempty).sum())].to(x.device)]
            cent[~nonempty] = reseed
    return cent


def fit_pq(x: torch.Tensor, m: int, k: int = PQ_CENTROIDS, iters: int = KMEANS_ITERS,
           seed: int = 0, device: str | torch.device = "cpu") -> torch.Tensor:
    """Fit M sub-quantisers on x [N, d] (d % M == 0). Returns codebooks [M, k, d//M] (float32, cpu)."""
    if x.dim() != 2:
        raise ValueError(f"fit_pq expects [N, d], got {tuple(x.shape)}")
    n, d = x.shape
    if d % m != 0:
        raise ValueError(f"d={d} not divisible by M={m}")
    if n < k:
        raise ValueError(f"need at least {k} rows to fit {k} centroids, got {n}")
    gen = torch.Generator(device="cpu").manual_seed(seed)
    s = d // m
    xd = x.to(device).float()
    books = [_kmeans(xd[:, j * s:(j + 1) * s].contiguous(), k, iters, gen) for j in range(m)]
    return torch.stack(books).cpu()


def pq_encode(x: torch.Tensor, books: torch.Tensor) -> torch.Tensor:
    """x [..., d] -> codes [..., M] (int64 in [0, k))."""
    m, k, s = books.shape
    flat = x.reshape(-1, m * s).float()
    out = torch.empty(flat.shape[0], m, dtype=torch.int64)
    for j in range(m):
        sub = flat[:, j * s:(j + 1) * s]
        for i in range(0, sub.shape[0], ASSIGN_CHUNK):
            out[i:i + ASSIGN_CHUNK, j] = torch.cdist(sub[i:i + ASSIGN_CHUNK], books[j]).argmin(dim=1)
    return out.reshape(*x.shape[:-1], m)


def pq_decode(codes: torch.Tensor, books: torch.Tensor) -> torch.Tensor:
    """codes [..., M] -> reconstruction [..., d]."""
    m, k, s = books.shape
    flat = codes.reshape(-1, m)
    parts = [books[j][flat[:, j]] for j in range(m)]
    return torch.cat(parts, dim=1).reshape(*codes.shape[:-1], m * s)
