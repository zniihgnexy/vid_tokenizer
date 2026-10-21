"""Uniform scalar quantisation with donor-fitted per-dimension ranges, plus closed-loop DPCM."""

from __future__ import annotations

import torch

RANGE_LO_Q = 0.005
RANGE_HI_Q = 0.995
RANGE_FIT_MAX_ROWS = 100_000
EPS = 1e-8


def fit_ranges(x: torch.Tensor, lo_q: float = RANGE_LO_Q, hi_q: float = RANGE_HI_Q,
               seed: int = 0) -> tuple[torch.Tensor, torch.Tensor]:
    """Per-dimension clipping range from quantiles of ``x`` [N, d] (subsampled rows)."""
    if x.dim() != 2:
        raise ValueError(f"fit_ranges expects [N, d], got {tuple(x.shape)}")
    if x.shape[0] > RANGE_FIT_MAX_ROWS:
        g = torch.Generator(device="cpu").manual_seed(seed)
        sel = torch.randperm(x.shape[0], generator=g)[:RANGE_FIT_MAX_ROWS]
        x = x[sel]
    xs = x.float().sort(dim=0).values
    n = xs.shape[0]
    # .clone() so the returned vectors do not alias the whole sorted array (torch.save would ship it)
    lo = xs[min(n - 1, int(lo_q * (n - 1)))].clone()
    hi = xs[min(n - 1, int(hi_q * (n - 1)))].clone()
    hi = torch.maximum(hi, lo + EPS)
    return lo, hi


def sq_step(lo: torch.Tensor, hi: torch.Tensor, bits: int) -> torch.Tensor:
    return (hi - lo) / float(2 ** bits - 1)


def sq_encode(x: torch.Tensor, lo: torch.Tensor, hi: torch.Tensor, bits: int) -> torch.Tensor:
    """x [..., d] -> integer codes [..., d] in [0, 2**bits - 1] (int64)."""
    step = sq_step(lo, hi, bits)
    q = torch.round((x.float() - lo) / step)
    return q.clamp_(0, 2 ** bits - 1).to(torch.int64)


def sq_decode(codes: torch.Tensor, lo: torch.Tensor, hi: torch.Tensor, bits: int) -> torch.Tensor:
    return lo + codes.float() * sq_step(lo, hi, bits)


def dpcm_encode(x: torch.Tensor, lo: torch.Tensor, hi: torch.Tensor, bits: int
                ) -> tuple[torch.Tensor, torch.Tensor]:
    """Closed-loop temporal DPCM over the first axis of x [T, K, d].

    Frame 0 is coded as a residual from zero. Returns (codes [T, K, d], recon [T, K, d]);
    the decoder reproduces ``recon`` exactly from ``codes``.
    """
    if x.dim() != 3:
        raise ValueError(f"dpcm_encode expects [T, K, d], got {tuple(x.shape)}")
    prev = torch.zeros_like(x[0], dtype=torch.float32)
    codes, recon = [], []
    for t in range(x.shape[0]):
        r = x[t].float() - prev
        c = sq_encode(r, lo, hi, bits)
        prev = prev + sq_decode(c, lo, hi, bits)
        codes.append(c)
        recon.append(prev.clone())
    return torch.stack(codes), torch.stack(recon)


def dpcm_decode(codes: torch.Tensor, lo: torch.Tensor, hi: torch.Tensor, bits: int) -> torch.Tensor:
    prev = torch.zeros(codes.shape[1:], dtype=torch.float32)
    out = []
    for t in range(codes.shape[0]):
        prev = prev + sq_decode(codes[t], lo, hi, bits)
        out.append(prev.clone())
    return torch.stack(out)


def open_loop_residuals(x: torch.Tensor) -> torch.Tensor:
    """x [T, K, d] -> [T, K, d] with r_0 = x_0 and r_t = x_t - x_{t-1} (for range fitting)."""
    r = x.float().clone()
    r[1:] = x[1:].float() - x[:-1].float()
    return r
