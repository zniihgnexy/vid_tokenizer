"""Bit accounting for integer code tensors.

``entropy_bits`` is the order-0 per-dimension entropy (what an ideal adaptive
arithmetic coder with one frequency table per dimension achieves) plus the cost
of transmitting those tables. ``lzma_bits`` is the size of the bit-packed codes
after lzma, i.e. what a lazy implementation actually ships. The baseline's bpp
uses the smaller-is-friendlier entropy figure; both are logged.
"""

from __future__ import annotations

import lzma
import math

import numpy as np
import torch

TABLE_PRECISION_BITS = 8


def table_bits(dims: int, nlevels: int, precision: int = TABLE_PRECISION_BITS) -> int:
    """Side information for per-dimension frequency tables."""
    return dims * nlevels * precision


def entropy_bits(codes: torch.Tensor, nlevels: int, per_dim: bool = True) -> float:
    """Order-0 entropy of codes [..., d] in bits (per-dimension tables when per_dim)."""
    flat = codes.reshape(-1, codes.shape[-1]).to(torch.int64)
    n, d = flat.shape
    if n == 0:
        return 0.0
    if per_dim:
        offs = torch.arange(d, dtype=torch.int64) * nlevels
        hist = torch.bincount((flat + offs).reshape(-1), minlength=d * nlevels).reshape(d, nlevels).double()
        p = hist / n
        h = -(p[p > 0] * p[p > 0].log2()).sum().item()   # sum over dims of per-dim entropies
        return h * n + table_bits(d, nlevels)
    hist = torch.bincount(flat.reshape(-1), minlength=nlevels).double()
    p = hist / (n * d)
    h = -(p[p > 0] * p[p > 0].log2()).sum().item()
    return h * n * d + table_bits(1, nlevels)


def pack_codes(codes: torch.Tensor, bits: int) -> bytes:
    """Bit-pack integer codes (values < 2**bits, bits <= 8) into bytes."""
    if bits > 8:
        raise ValueError("pack_codes supports bits <= 8")
    arr = codes.reshape(-1).to(torch.int64).numpy().astype(np.uint8)
    if bits == 8:
        return arr.tobytes()
    bitarr = np.unpackbits(arr.reshape(-1, 1), axis=1)[:, 8 - bits:]
    return np.packbits(bitarr.reshape(-1)).tobytes()


def lzma_bits(codes: torch.Tensor, bits: int) -> int:
    packed = pack_codes(codes, bits)
    return 8 * len(lzma.compress(packed, preset=9 | lzma.PRESET_EXTREME))


def raw_bits(codes: torch.Tensor, bits: int) -> int:
    return int(math.prod(codes.shape)) * bits
