"""Unit tests for the B4 learned feature-cache baseline (tiny dims, CPU)."""

import os

import pytest
import torch

from machine_codec_pipeline.featcache.ae import AEConfig, AECodec, TokenAE, load_ae, payload_bits, save_ae

C = 32


def _tiny(hyper: bool) -> TokenAE:
    torch.manual_seed(0)
    m = TokenAE(AEConfig(dim=C, hidden=16, latent=8, hyper_dim=4, hyper=hyper, pool=4))
    m.set_standardisation(torch.zeros(C), torch.ones(C))
    return m


@pytest.mark.parametrize("hyper", [True, False])
def test_forward_rate_distortion_terms(hyper):
    m = _tiny(hyper)
    out = m(torch.randn(50, C))
    assert out["x_hat_std"].shape == (50, C)
    assert torch.isfinite(out["mse"]) and out["bits_per_token"].item() > 0
    (out["bits_per_token"] / C + out["mse"]).backward()      # trainable end to end
    assert m.aux_loss().item() >= 0


@pytest.mark.parametrize("hyper", [True, False])
def test_compress_decompress_roundtrip(hyper):
    m = _tiny(hyper).eval()
    m.update(force=True)
    x = torch.randn(40, C) * 3
    pay = m.compress(x)
    assert pay["n"] == 40 and payload_bits(pay) > 0
    x_hat = m.decompress(pay)
    assert x_hat.shape == (40, C)
    # decompress must reproduce the forward-pass reconstruction (same quantised latents)
    ref = m(x)["x_hat_std"] * m.std + m.mean
    assert torch.allclose(x_hat, ref, atol=1e-3, rtol=1e-3)


def test_save_load_and_codec(tmp_path):
    m = _tiny(True).eval(); m.update(force=True)
    p = str(tmp_path / "tiny.pt")
    save_ae(m, p, {"name": "p4_ae_test"})
    m2, meta = load_ae(p)
    assert meta["name"] == "p4_ae_test"
    codec = AECodec(p, device="cpu")
    tokens = torch.randn(6, 16, C)
    pay = codec.encode(tokens)
    assert pay.raw.shape == (6, 4, C) and pay.bits > 0 and pay.frames == 6
    y = codec.decode(pay, [0, 5])
    assert y.shape == (2, 4, C) and torch.allclose(y, codec.decode(pay)[[0, 5]])
    assert os.path.exists(p)
