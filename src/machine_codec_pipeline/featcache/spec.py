"""Feature-cache codec spec strings.

Grammar (parts joined by ``_``, order fixed):
  p{K}            tokens per frame after average pooling; K must be a square in {1,4,16,64,256}
  pca{d}          optional PCA to d dims (donor-fitted basis)
  q{b} | pq{M}    optional quantiser: uniform scalar with b bits, or product quantiser
                  with M sub-vectors of 256 centroids (8 bits each); omitted = fp16 raw
  t               optional closed-loop temporal DPCM (scalar quantiser only)

Examples: ``p16_pca64_q4``, ``p64_pca64_pq8``, ``p256_pca16_q2_t``, ``p16_fp16``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

VALID_POOLS = (1, 4, 16, 64, 256)
MAX_SQ_BITS = 8
PQ_CENTROIDS = 256


@dataclass(frozen=True)
class FeatSpec:
    pool: int
    pca: int | None
    quant: tuple[str, int] | None  # ("sq", bits) | ("pq", M) | None
    dpcm: bool

    @property
    def name(self) -> str:
        parts = [f"p{self.pool}"]
        if self.pca is not None:
            parts.append(f"pca{self.pca}")
        if self.quant is None:
            parts.append("fp16")
        elif self.quant[0] == "sq":
            parts.append(f"q{self.quant[1]}")
        else:
            parts.append(f"pq{self.quant[1]}")
        if self.dpcm:
            parts.append("t")
        return "_".join(parts)

    @property
    def dims(self) -> int | None:
        """Coefficient dimensionality after PCA (None = raw token width)."""
        return self.pca


_PART = re.compile(r"^(p|pca|q|pq)(\d+)$")


def parse_spec(text: str) -> FeatSpec:
    parts = text.strip().split("_")
    if not parts or not parts[0].startswith("p") or parts[0].startswith("pca"):
        raise ValueError(f"spec must start with p<K>: {text!r}")
    pool = int(parts[0][1:])
    if pool not in VALID_POOLS:
        raise ValueError(f"pool {pool} not in {VALID_POOLS}: {text!r}")
    pca: int | None = None
    quant: tuple[str, int] | None = None
    dpcm = False
    seen_fp16 = False
    for p in parts[1:]:
        if p == "t":
            dpcm = True
            continue
        if p == "fp16":
            seen_fp16 = True
            continue
        m = _PART.match(p)
        if not m:
            raise ValueError(f"bad spec part {p!r} in {text!r}")
        kind, val = m.group(1), int(m.group(2))
        if kind == "pca":
            if val <= 0:
                raise ValueError(f"pca dims must be positive: {text!r}")
            pca = val
        elif kind == "q":
            if not 1 <= val <= MAX_SQ_BITS:
                raise ValueError(f"q bits must be in 1..{MAX_SQ_BITS}: {text!r}")
            if quant is not None:
                raise ValueError(f"only one quantiser allowed: {text!r}")
            quant = ("sq", val)
        elif kind == "pq":
            if val <= 0:
                raise ValueError(f"pq M must be positive: {text!r}")
            if quant is not None:
                raise ValueError(f"only one quantiser allowed: {text!r}")
            quant = ("pq", val)
        else:
            raise ValueError(f"unexpected part {p!r} in {text!r}")
    if seen_fp16 and quant is not None:
        raise ValueError(f"fp16 and a quantiser are exclusive: {text!r}")
    if dpcm and (quant is None or quant[0] != "sq"):
        raise ValueError(f"dpcm (t) requires a scalar quantiser q<b>: {text!r}")
    return FeatSpec(pool=pool, pca=pca, quant=quant, dpcm=dpcm)
