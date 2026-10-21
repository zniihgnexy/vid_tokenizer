#!/usr/bin/env python3
"""Learned-codec baseline (CompressAI cheng2020-anchor, per-frame intra): encode the
sampled PNG frames at quality q, write recon PNGs + true bpp from the entropy-coded
strings. Modern learned anchor for the 'only beats old HEVC?' critique.

Usage: CUDA_VISIBLE_DEVICES=0 python tools/learned_codec_recon.py \
         --frames-dir <raw_chunk_dir> --out-dir <recon_dir> --quality 1
Prints: BPP=<value> on the last line."""
import argparse, glob, os
import torch
from PIL import Image
import torchvision.transforms.functional as TF
from compressai.zoo import cheng2020_anchor

ap = argparse.ArgumentParser()
ap.add_argument("--frames-dir", required=True)
ap.add_argument("--out-dir", required=True)
ap.add_argument("--quality", type=int, default=1)  # 1..6, 1 = lowest rate
args = ap.parse_args()

dev = "cuda" if torch.cuda.is_available() else "cpu"
model = cheng2020_anchor(quality=args.quality, metric="mse", pretrained=True).eval().to(dev)
os.makedirs(args.out_dir, exist_ok=True)
pngs = sorted(glob.glob(os.path.join(args.frames_dir, "*.png")))
total_bits = total_px = 0
with torch.no_grad():
    for i, p in enumerate(pngs):
        img = Image.open(p).convert("RGB")
        x = TF.to_tensor(img).unsqueeze(0).to(dev)
        h, w = x.shape[-2:]
        ph, pw = (64 - h % 64) % 64, (64 - w % 64) % 64
        xp = torch.nn.functional.pad(x, (0, pw, 0, ph), mode="replicate")
        enc = model.compress(xp)
        total_bits += sum(len(s) * 8 for ss in enc["strings"] for s in ss)
        total_px += h * w
        dec = model.decompress(enc["strings"], enc["shape"])
        rec = dec["x_hat"][..., :h, :w].clamp(0, 1)
        TF.to_pil_image(rec.squeeze(0).cpu()).save(os.path.join(args.out_dir, f"recon_{i:04d}.png"))
print(f"BPP={total_bits/total_px:.4f}")
