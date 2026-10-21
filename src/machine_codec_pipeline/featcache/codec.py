"""FeatCodec: pool -> (pca) -> (sq | pq | fp16) [-> dpcm] with bit accounting."""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn.functional as F

from .entropy import entropy_bits, lzma_bits, raw_bits
from .pca import pca_project, pca_unproject
from .pq import pq_decode, pq_encode
from .quant import dpcm_decode, dpcm_encode, sq_decode, sq_encode
from .spec import PQ_CENTROIDS, FeatSpec

FRAME_H = 256
FRAME_W = 256
FP16_BITS = 16
PQ_BITS = 8


def bpp_of(bits: float, frames: int, h: int = FRAME_H, w: int = FRAME_W) -> float:
    """Same denominator as the NVRC codec: bits / (T * H * W) at the 256-res frame cache."""
    return bits / float(frames * h * w)


def pool_tokens(tokens: torch.Tensor, k: int) -> torch.Tensor:
    """[N, T, C] -> [N, k, C] by spatial average pooling on the sqrt(T) grid (256 = identity)."""
    n, t, c = tokens.shape
    if k == t:
        return tokens
    g = int(round(t ** 0.5))
    o = int(round(k ** 0.5))
    if g * g != t or o * o != k:
        raise ValueError(f"pool needs square token counts, got T={t} k={k}")
    x = tokens.float().view(n, g, g, c).permute(0, 3, 1, 2)
    return F.adaptive_avg_pool2d(x, (o, o)).permute(0, 2, 3, 1).reshape(n, k, c)


def book_key(pool: int, pca: int | None) -> str:
    return f"K{pool}_d{pca if pca is not None else 'raw'}"


@dataclass(frozen=True)
class Payload:
    spec: FeatSpec
    frames: int
    codes: torch.Tensor | None      # int codes [T, K, d'] (sq/dpcm) or [T, K, M] (pq); None for fp16
    raw: torch.Tensor | None        # fp16 tokens [T, K, C] when spec.quant is None
    bits_entropy: float
    bits_lzma: float
    bits_raw: float

    @property
    def bits(self) -> float:
        """Bits charged to the baseline: the best of ideal adaptive coding, lzma and raw packing."""
        return min(self.bits_entropy, self.bits_lzma, self.bits_raw)

    @property
    def bpp(self) -> float:
        return bpp_of(self.bits, self.frames)


class FeatCodec:
    """Encode a video's token cache under one spec using a fitted book (see featcache.fit)."""

    def __init__(self, book: dict, spec: FeatSpec):
        self.spec = spec
        self.key = book_key(spec.pool, spec.pca)
        entry = book.get(self.key)
        if spec.pca is not None or spec.quant is not None:
            if entry is None:
                raise KeyError(f"book has no entry {self.key} for spec {spec.name}")
        self.entry = entry or {}
        if spec.quant is not None and spec.quant[0] == "sq":
            mode = "dpcm" if spec.dpcm else "abs"
            if mode not in self.entry.get("range", {}):
                raise KeyError(f"book {self.key} lacks {mode} ranges for {spec.name}")
        if spec.quant is not None and spec.quant[0] == "pq":
            if spec.quant[1] not in self.entry.get("pq", {}):
                raise KeyError(f"book {self.key} lacks pq{spec.quant[1]} codebooks for {spec.name}")

    # -- coefficient space ----------------------------------------------------
    def _to_coeff(self, pooled: torch.Tensor) -> torch.Tensor:
        return pca_project(pooled, self.entry["pca"]) if self.spec.pca is not None else pooled.float()

    def _from_coeff(self, coeff: torch.Tensor) -> torch.Tensor:
        return pca_unproject(coeff, self.entry["pca"]) if self.spec.pca is not None else coeff

    # -- encode ---------------------------------------------------------------
    def encode(self, tokens: torch.Tensor) -> Payload:
        """tokens [T, 256, C] (any float dtype) -> Payload."""
        if tokens.dim() != 3:
            raise ValueError(f"encode expects [T, 256, C], got {tuple(tokens.shape)}")
        t = tokens.shape[0]
        pooled = pool_tokens(tokens, self.spec.pool)
        if self.spec.quant is None:
            raw = pooled.to(torch.float16)
            bits = float(raw.numel() * FP16_BITS)
            return Payload(self.spec, t, None, raw, bits, bits, bits)
        coeff = self._to_coeff(pooled)
        kind, val = self.spec.quant
        if kind == "sq":
            lo, hi = self._ranges()
            if self.spec.dpcm:
                codes, _ = dpcm_encode(coeff, lo, hi, val)
            else:
                codes = sq_encode(coeff, lo, hi, val)
            nlevels, bits_per = 2 ** val, val
        else:
            codes = pq_encode(coeff, self.entry["pq"][val])
            nlevels, bits_per = PQ_CENTROIDS, PQ_BITS
        return Payload(self.spec, t, codes, None,
                       entropy_bits(codes, nlevels), float(lzma_bits(codes, bits_per)),
                       float(raw_bits(codes, bits_per)))

    # -- decode ---------------------------------------------------------------
    def decode(self, payload: Payload, frames: list[int] | None = None) -> torch.Tensor:
        """Payload -> tokens [N, K, C] for the requested frame indices (all frames when None)."""
        if payload.raw is not None:
            out = payload.raw.float()
            return out if frames is None else out[frames]
        kind, val = self.spec.quant
        if kind == "sq":
            lo, hi = self._ranges()
            if self.spec.dpcm:
                coeff = dpcm_decode(payload.codes, lo, hi, val)          # must run from frame 0
                if frames is not None:
                    coeff = coeff[frames]
            else:
                codes = payload.codes if frames is None else payload.codes[frames]
                coeff = sq_decode(codes, lo, hi, val)
        else:
            codes = payload.codes if frames is None else payload.codes[frames]
            coeff = pq_decode(codes, self.entry["pq"][val])
        return self._from_coeff(coeff)

    def _ranges(self) -> tuple[torch.Tensor, torch.Tensor]:
        r = self.entry["range"]["dpcm" if self.spec.dpcm else "abs"]
        return r["lo"], r["hi"]
