"""Unit tests for the E-04 feature-cache codec (CPU, synthetic data)."""

import math

import pytest
import torch

from machine_codec_pipeline.featcache import FeatCodec, bpp_of, parse_spec, pool_tokens, book_key
from machine_codec_pipeline.featcache.entropy import entropy_bits, lzma_bits, pack_codes, raw_bits
from machine_codec_pipeline.featcache.fit import fit_book
from machine_codec_pipeline.featcache.pca import fit_pca, pca_project, pca_unproject
from machine_codec_pipeline.featcache.pq import fit_pq, pq_decode, pq_encode
from machine_codec_pipeline.featcache.quant import dpcm_decode, dpcm_encode, fit_ranges, sq_decode, sq_encode, sq_step

C = 32  # token width in tests (real: 4096)


# ---- spec ----------------------------------------------------------------
def test_parse_spec_full():
    s = parse_spec("p16_pca64_q4_t")
    assert (s.pool, s.pca, s.quant, s.dpcm) == (16, 64, ("sq", 4), True)
    assert s.name == "p16_pca64_q4_t"


def test_parse_spec_variants():
    assert parse_spec("p64_pq8").quant == ("pq", 8)
    assert parse_spec("p256_fp16").quant is None
    assert parse_spec("p4").name == "p4_fp16"


@pytest.mark.parametrize("bad", ["pca64_q4", "p5_q4", "p16_q9", "p16_pq8_t", "p16_q4_pq8", "p16_x1"])
def test_parse_spec_rejects(bad):
    with pytest.raises(ValueError):
        parse_spec(bad)


# ---- pooling -------------------------------------------------------------
def test_pool_tokens_matches_grid_average():
    x = torch.arange(2 * 16 * 3, dtype=torch.float32).reshape(2, 16, 3)
    y = pool_tokens(x, 4)
    assert y.shape == (2, 4, 3)
    # top-left 2x2 block of the 4x4 grid: tokens 0,1,4,5
    assert torch.allclose(y[0, 0], x[0, [0, 1, 4, 5]].mean(0))
    assert pool_tokens(x, 16) is x


# ---- scalar quantiser ----------------------------------------------------
def test_sq_roundtrip_error_bounded():
    torch.manual_seed(0)
    x = torch.randn(1000, 8)
    lo, hi = fit_ranges(x)
    for v in (lo, hi):   # must not alias the sorted [N, d] array (book size)
        assert v.untyped_storage().nbytes() == v.numel() * v.element_size()
    for bits in (2, 4, 8):
        c = sq_encode(x, lo, hi, bits)
        assert c.min() >= 0 and c.max() <= 2 ** bits - 1
        xh = sq_decode(c, lo, hi, bits)
        inside = (x >= lo) & (x <= hi)
        err = (xh - x).abs()
        tol = (sq_step(lo, hi, bits) / 2 + 1e-5).expand_as(err)
        assert (err[inside] <= tol[inside]).all()


def test_dpcm_closed_loop_no_drift():
    torch.manual_seed(0)
    base = torch.randn(1, 4, 8)
    x = base + 0.01 * torch.randn(64, 4, 8).cumsum(0)      # slowly drifting sequence
    lo, hi = fit_ranges((x[1:] - x[:-1]).reshape(-1, 8))
    lo, hi = torch.minimum(lo, x[0].min(0).values), torch.maximum(hi, x[0].max(0).values)
    codes, recon = dpcm_encode(x, lo, hi, 6)
    assert torch.allclose(dpcm_decode(codes, lo, hi, 6), recon)
    err = (recon - x).abs()
    assert err[-1].max() <= sq_step(lo, hi, 6).max() / 2 + 1e-4   # last frame as good as first


# ---- entropy / packing ---------------------------------------------------
def test_pack_codes_and_bits():
    codes = torch.randint(0, 16, (10, 7))
    assert len(pack_codes(codes, 4)) == math.ceil(70 * 4 / 8)
    assert raw_bits(codes, 4) == 280
    assert lzma_bits(codes, 4) > 0
    const = torch.zeros(1000, 4, dtype=torch.int64)
    assert entropy_bits(const, 16) == pytest.approx(4 * 16 * 8)   # only the tables
    uni = torch.arange(16).repeat(100).reshape(100, 16)             # each dim constant -> 0 entropy
    assert entropy_bits(uni, 16) == pytest.approx(16 * 16 * 8)
    assert entropy_bits(uni, 16, per_dim=False) == pytest.approx(1600 * 4 + 16 * 8)


# ---- pca / pq -------------------------------------------------------------
def test_pca_recovers_low_rank():
    torch.manual_seed(0)
    basis = torch.randn(4, C)
    x = torch.randn(500, 4) @ basis + 3.0
    p = fit_pca(x, 4)
    assert p["basis"].shape == (4, C)
    xh = pca_unproject(pca_project(x, p), p)
    assert torch.allclose(xh, x, atol=1e-3)
    assert p["explained"].item() > 0.999


def test_pq_roundtrip_on_clusters():
    torch.manual_seed(0)
    centers = torch.randn(200, 8) * 5
    x = centers[torch.randint(0, 200, (4000,))] + 0.01 * torch.randn(4000, 8)
    books = fit_pq(x, m=2, k=256, iters=20)
    assert books.shape == (2, 256, 4)
    codes = pq_encode(x, books)
    assert codes.shape == (4000, 2) and codes.max() < 256
    mse = ((pq_decode(codes, books) - x) ** 2).mean()
    assert mse < 0.05 * x.var()          # far below the raw variance (~25)


# ---- end-to-end codec ------------------------------------------------------
def _toy_book():
    torch.manual_seed(0)
    donors = [torch.randn(40, 16, C) * 2 + 1 for _ in range(3)]   # 3 donors x 40 frames x 16 tokens
    from machine_codec_pipeline.featcache.fit import collect_pooled
    pooled = collect_pooled(donors, pools=(16, 4))
    return fit_book(pooled, pcas=(None, 8), pq={8: (2,), None: (4,)}, log=lambda *a: None)


@pytest.mark.parametrize("spec", ["p4_fp16", "p16_pca8_q4", "p16_pca8_q4_t", "p4_pca8_pq2", "p16_q8", "p4_pq4"])
def test_codec_roundtrip_shapes_and_bits(spec):
    book = _toy_book()
    codec = FeatCodec(book, parse_spec(spec))
    x = torch.randn(6, 16, C)
    pay = codec.encode(x)
    y = codec.decode(pay, [1, 4])
    assert y.shape == (2, codec.spec.pool, C)
    assert torch.allclose(y, codec.decode(pay)[[1, 4]])
    assert 0 < pay.bits <= min(pay.bits_entropy, pay.bits_lzma, pay.bits_raw)
    assert pay.bpp == pytest.approx(bpp_of(pay.bits, 6))


def test_codec_fp16_bits_exact():
    codec = FeatCodec({}, parse_spec("p4_fp16"))
    pay = codec.encode(torch.randn(3, 16, C))
    assert pay.bits == 3 * 4 * C * 16
    assert bpp_of(pay.bits, 3) == pytest.approx(3 * 4 * C * 16 / (3 * 256 * 256))


def test_codec_requires_book_entry():
    with pytest.raises(KeyError):
        FeatCodec({}, parse_spec("p16_pca8_q4"))
    assert book_key(16, None) == "K16_draw"
