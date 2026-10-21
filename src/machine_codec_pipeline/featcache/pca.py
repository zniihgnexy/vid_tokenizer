"""Donor-fitted PCA basis (shared across videos, amortised like the frozen adapter)."""

from __future__ import annotations

import torch

COV_CHUNK_ROWS = 65_536


def fit_pca(x: torch.Tensor, k: int, device: str | torch.device = "cpu") -> dict[str, torch.Tensor]:
    """Fit a k-dim PCA on rows of x [N, d]. Returns {'mean': [d], 'basis': [k, d]} (float32, cpu)."""
    if x.dim() != 2:
        raise ValueError(f"fit_pca expects [N, d], got {tuple(x.shape)}")
    n, d = x.shape
    if not 1 <= k <= d:
        raise ValueError(f"k must be in 1..{d}, got {k}")
    mean = x.float().mean(dim=0).to(device)
    cov = torch.zeros(d, d, dtype=torch.float64, device=device)
    for i in range(0, n, COV_CHUNK_ROWS):
        xc = x[i:i + COV_CHUNK_ROWS].to(device).float() - mean
        cov += (xc.T @ xc).double()
    cov /= max(n - 1, 1)
    evals, evecs = torch.linalg.eigh(cov)          # ascending
    order = torch.argsort(evals, descending=True)[:k]
    basis = evecs[:, order].T.float()              # [k, d]
    explained = (evals[order].sum() / evals.clamp_min(0).sum()).item()
    return {"mean": mean.cpu(), "basis": basis.cpu(), "explained": torch.tensor(explained)}


def pca_project(x: torch.Tensor, p: dict[str, torch.Tensor]) -> torch.Tensor:
    """x [..., d] -> coefficients [..., k]."""
    return (x.float() - p["mean"]) @ p["basis"].T


def pca_unproject(c: torch.Tensor, p: dict[str, torch.Tensor]) -> torch.Tensor:
    """coefficients [..., k] -> reconstruction [..., d]."""
    return c.float() @ p["basis"] + p["mean"]
