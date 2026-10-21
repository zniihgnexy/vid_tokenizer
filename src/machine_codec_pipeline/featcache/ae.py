"""B4: learned feature autoencoder baseline (D-017) for the frozen-VLM token cache.

Per-token MLP analysis/synthesis transform with a CompressAI entropy model:
  * hyper=True  -> scale hyperprior (Ballé et al. 2018): z = h_a(y), scales = h_s(z_hat),
                   y coded with a Gaussian conditional, z with a factorised bottleneck
  * hyper=False -> fully factorised bottleneck on y (Ballé et al. 2017)
Trained on the 32 universal-adapter donors (rate-distortion loss on standardised tokens);
bits at evaluation are the ACTUAL entropy-coded byte counts, so this baseline is charged
exactly like a real codec. Tokens are pooled to K per frame first, like every other cell.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F
from compressai.entropy_models import EntropyBottleneck, GaussianConditional
from compressai.models import CompressionModel

from .codec import Payload, bpp_of, pool_tokens

SCALE_MIN, SCALE_MAX, SCALE_LEVELS = 0.11, 256.0, 64
EPS = 1e-6


def _mlp(dims: list[int]) -> nn.Sequential:
    layers: list[nn.Module] = []
    for i in range(len(dims) - 1):
        layers.append(nn.Linear(dims[i], dims[i + 1]))
        if i < len(dims) - 2:
            layers.append(nn.GELU())
    return nn.Sequential(*layers)


def _scale_table() -> torch.Tensor:
    return torch.exp(torch.linspace(math.log(SCALE_MIN), math.log(SCALE_MAX), SCALE_LEVELS))


@dataclass(frozen=True)
class AEConfig:
    dim: int = 4096
    hidden: int = 1024
    latent: int = 128
    hyper_dim: int = 64
    hyper: bool = True
    pool: int = 64


class TokenAE(CompressionModel):
    """x [N, dim] (raw tokens) <-> y [N, latent] with an entropy model; standardisation is part of the model."""

    def __init__(self, cfg: AEConfig):
        super().__init__()
        self.cfg = cfg
        self.register_buffer("mean", torch.zeros(cfg.dim))
        self.register_buffer("std", torch.ones(cfg.dim))
        self.enc = _mlp([cfg.dim, cfg.hidden, cfg.hidden, cfg.latent])
        self.dec = _mlp([cfg.latent, cfg.hidden, cfg.hidden, cfg.dim])
        if cfg.hyper:
            self.h_a = _mlp([cfg.latent, cfg.hidden // 4, cfg.hyper_dim])
            self.h_s = _mlp([cfg.hyper_dim, cfg.hidden // 4, cfg.latent])
            self.entropy_bottleneck = EntropyBottleneck(cfg.hyper_dim)
            self.gaussian_conditional = GaussianConditional(None)
        else:
            self.entropy_bottleneck = EntropyBottleneck(cfg.latent)

    def set_standardisation(self, mean: torch.Tensor, std: torch.Tensor) -> None:
        self.mean.copy_(mean); self.std.copy_(std.clamp_min(EPS))

    # [N, C] <-> [1, C, N, 1] (CompressAI wants the channel axis at 1)
    @staticmethod
    def _to4d(t: torch.Tensor) -> torch.Tensor:
        return t.T.unsqueeze(0).unsqueeze(-1)

    @staticmethod
    def _from4d(t: torch.Tensor) -> torch.Tensor:
        return t.squeeze(-1).squeeze(0).T

    def _scales(self, z_hat4: torch.Tensor) -> torch.Tensor:
        return F.softplus(self.h_s(self._from4d(z_hat4))) + SCALE_MIN

    def forward(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        xs = (x - self.mean) / self.std
        y = self.enc(xs)
        if self.cfg.hyper:
            z = self.h_a(y)
            z_hat4, z_lik = self.entropy_bottleneck(self._to4d(z))
            y_hat4, y_lik = self.gaussian_conditional(self._to4d(y), self._to4d(self._scales(z_hat4)))
            bits = -(torch.log2(y_lik).sum() + torch.log2(z_lik).sum())
        else:
            y_hat4, y_lik = self.entropy_bottleneck(self._to4d(y))
            bits = -torch.log2(y_lik).sum()
        x_hat = self.dec(self._from4d(y_hat4))
        n = x.shape[0]
        return {"x_hat_std": x_hat, "mse": F.mse_loss(x_hat, xs), "bits_per_token": bits / n}

    @torch.no_grad()
    def compress(self, x: torch.Tensor) -> dict[str, Any]:
        """x [N, dim] -> {'strings': [...], 'n': N}; call update() once after training."""
        y = self.enc((x - self.mean) / self.std)
        if self.cfg.hyper:
            z4 = self._to4d(self.h_a(y))
            z_str = self.entropy_bottleneck.compress(z4)
            z_hat4 = self.entropy_bottleneck.decompress(z_str, z4.shape[2:])
            idx = self.gaussian_conditional.build_indexes(self._to4d(self._scales(z_hat4)))
            y_str = self.gaussian_conditional.compress(self._to4d(y), idx)
            return {"strings": [y_str, z_str], "n": x.shape[0]}
        return {"strings": [self.entropy_bottleneck.compress(self._to4d(y))], "n": x.shape[0]}

    @torch.no_grad()
    def decompress(self, payload: dict[str, Any]) -> torch.Tensor:
        n = payload["n"]
        if self.cfg.hyper:
            y_str, z_str = payload["strings"]
            z_hat4 = self.entropy_bottleneck.decompress(z_str, (n, 1))
            idx = self.gaussian_conditional.build_indexes(self._to4d(self._scales(z_hat4)))
            y_hat = self._from4d(self.gaussian_conditional.decompress(y_str, idx))
        else:
            y_hat = self._from4d(self.entropy_bottleneck.decompress(payload["strings"][0], (n, 1)))
        return self.dec(y_hat) * self.std + self.mean

    def update(self, force: bool = True) -> bool:  # type: ignore[override]
        if self.cfg.hyper:
            self.gaussian_conditional.update_scale_table(_scale_table(), force=force)
        return super().update(force=force)


def payload_bits(payload: dict[str, Any]) -> int:
    return 8 * sum(len(s) for group in payload["strings"] for s in group)


def save_ae(model: TokenAE, path: str, meta: dict | None = None) -> None:
    torch.save({"cfg": model.cfg.__dict__, "state": model.state_dict(), "meta": meta or {}}, path)


def load_ae(path: str, device: str | torch.device = "cpu") -> tuple[TokenAE, dict]:
    ck = torch.load(path, map_location="cpu")
    model = TokenAE(AEConfig(**ck["cfg"]))
    model.load_state_dict(ck["state"], strict=False)   # entropy-model CDF buffers may differ in size
    model.update(force=True)
    return model.to(device).eval(), ck.get("meta", {})


@dataclass(frozen=True)
class AESpec:
    name: str
    pool: int


class AECodec:
    """Same encode/decode contract as FeatCodec, backed by a trained TokenAE."""

    def __init__(self, path: str, device: str | torch.device | None = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model, self.meta = load_ae(path, self.device)
        self.spec = AESpec(name=self.meta.get("name", "ae"), pool=self.model.cfg.pool)

    def encode(self, tokens: torch.Tensor) -> Payload:
        t = tokens.shape[0]
        pooled = pool_tokens(tokens, self.spec.pool).float()
        flat = pooled.reshape(-1, pooled.shape[-1]).to(self.device)
        pay = self.model.compress(flat)
        bits = float(payload_bits(pay))
        x_hat = self.model.decompress(pay).reshape(pooled.shape).to(torch.float16).cpu()
        return Payload(self.spec, t, None, x_hat, bits, bits, bits)   # type: ignore[arg-type]

    def decode(self, payload: Payload, frames: list[int] | None = None) -> torch.Tensor:
        out = payload.raw.float()
        return out if frames is None else out[frames]
