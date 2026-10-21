#!/usr/bin/env python3
"""DCVC-RT (CVPR2025) learned-VIDEO-codec baseline: sequential I+P coding of the
sampled PNG frames at a given qp index -> recon PNGs + true bpp from the entropy
coded bit_stream. SOTA learned video codec, the answer to "you only beat old HEVC?".

Faithful single-process adaptation of third_party/baselines/DCVC/test_video.py:
ENCODE pass (compress -> bit_stream, bits) then DECODE pass (decompress -> x_hat),
since DMC.compress() emits only the bitstream and regenerates x_hat in decompress().
Skips the SPS/NAL stream writer + multiprocessing worker pool; the bit_stream is
handed straight to decompress() and bits are summed from len(bit_stream).

Usage: CUDA_VISIBLE_DEVICES=0 python tools/dcvc_codec_recon.py \
         --frames-dir <raw_chunk_dir> --out-dir <recon_dir> --qp 27 [--intra-period -1]
Prints: BPP=<value> on the last line. qp is a rate INDEX in [0, get_qp_num()-1=63];
higher qp -> higher quality/rate (verify empirically)."""
import argparse, glob, os, sys

DCVC_ROOT = os.path.join(os.path.dirname(__file__), "..",
                         "third_party", "baselines", "DCVC")
sys.path.insert(0, os.path.abspath(DCVC_ROOT))

import numpy as np
import torch
from PIL import Image
from src.models.video_model import DMC
from src.models.image_model import DMCI
from src.utils.common import get_state_dict
from src.utils.transforms import rgb2ycbcr, ycbcr2rgb
from src.layers.cuda_inference import replicate_pad

ap = argparse.ArgumentParser()
ap.add_argument("--frames-dir", required=True)
ap.add_argument("--out-dir", required=True)
ap.add_argument("--qp", type=int, default=27)            # rate index in [0, 63]
ap.add_argument("--intra-period", type=int, default=-1)  # -1 = only frame 0 is I
ap.add_argument("--reset-interval", type=int, default=32)
ap.add_argument("--force-zero-thres", type=float, default=None)
ap.add_argument("--model-i", default=os.path.join(DCVC_ROOT, "checkpoints", "cvpr2025_image.pth.tar"))
ap.add_argument("--model-p", default=os.path.join(DCVC_ROOT, "checkpoints", "cvpr2025_video.pth.tar"))
args = ap.parse_args()

dev = "cuda" if torch.cuda.is_available() else "cpu"

i_net = DMCI()
i_net.load_state_dict(get_state_dict(args.model_i))
i_net = i_net.to(dev).eval(); i_net.update(args.force_zero_thres); i_net.half()

p_net = DMC()
p_net.load_state_dict(get_state_dict(args.model_p))
p_net = p_net.to(dev).eval(); p_net.update(args.force_zero_thres); p_net.half()

os.makedirs(args.out_dir, exist_ok=True)
pngs = sorted(glob.glob(os.path.join(args.frames_dir, "*.png")))
assert pngs, f"no PNGs in {args.frames_dir}"

h0, w0 = np.asarray(Image.open(pngs[0]).convert("RGB")).shape[:2]
pad_r, pad_b = DMCI.get_padding_size(h0, w0, 16)
use_two_ec = h0 * w0 > 1280 * 720
i_net.set_use_two_entropy_coders(use_two_ec)
p_net.set_use_two_entropy_coders(use_two_ec)


def load_frame(path):
    rgb = np.asarray(Image.open(path).convert("RGB")).astype(np.uint8).transpose(2, 0, 1)
    x = torch.from_numpy(rgb).to(dev).float().div(255.0).unsqueeze(0)
    x = rgb2ycbcr(x).to(torch.float16)
    return replicate_pad(x, pad_b, pad_r)


index_map = [0, 1, 0, 2, 0, 2, 0, 2]
ec_part = 1 if use_two_ec else 0

# ---- ENCODE pass: bits + per-frame (bit_stream, sps, qp, is_i) ----
frames = []
total_bits = total_px = 0
p_net.set_curr_poc(0)
with torch.no_grad():
    last_qp = 0
    for idx, p in enumerate(pngs):
        x_padded = load_frame(p)
        is_i = (idx == 0) or (args.intra_period > 0 and idx % args.intra_period == 0)
        if is_i:
            curr_qp = args.qp
            sps = {"sps_id": 0, "height": h0, "width": w0, "ec_part": ec_part, "use_ada_i": 0}
            enc = i_net.compress(x_padded, curr_qp)
            p_net.clear_dpb()
            p_net.add_ref_frame(None, enc["x_hat"])
        else:
            fa_idx = index_map[idx % 8]
            use_ada_i = 1 if (args.reset_interval > 0 and idx % args.reset_interval == 1) else 0
            if use_ada_i:
                p_net.prepare_feature_adaptor_i(last_qp)
            curr_qp = p_net.shift_qp(args.qp, fa_idx)
            sps = {"sps_id": 0, "height": h0, "width": w0, "ec_part": ec_part, "use_ada_i": use_ada_i}
            enc = p_net.compress(x_padded, curr_qp)
            last_qp = curr_qp
        frames.append({"bit_stream": enc["bit_stream"], "sps": sps, "qp": curr_qp, "is_i": is_i})
        total_bits += len(enc["bit_stream"]) * 8
        total_px += h0 * w0

# ---- DECODE pass: regenerate x_hat per frame, mirroring the encode DPB ----
p_net.set_curr_poc(0)
with torch.no_grad():
    for idx, f in enumerate(frames):
        if f["is_i"]:
            dec = i_net.decompress(f["bit_stream"], f["sps"], f["qp"])
            p_net.clear_dpb()
            p_net.add_ref_frame(None, dec["x_hat"])
        else:
            if f["sps"]["use_ada_i"]:
                p_net.reset_ref_feature()
            dec = p_net.decompress(f["bit_stream"], f["sps"], f["qp"])
        x_hat = dec["x_hat"][..., :h0, :w0].float()
        rec = ycbcr2rgb(x_hat).clamp(0, 1)
        rec = (rec.squeeze(0).cpu().numpy() * 255).round().astype(np.uint8).transpose(1, 2, 0)
        Image.fromarray(rec).save(os.path.join(args.out_dir, f"recon_{idx:04d}.png"))

print(f"BPP={total_bits/total_px:.4f}")
