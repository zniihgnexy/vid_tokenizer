#!/usr/bin/env python
"""UG-ICM (AAAI 2025) per-frame image-ICM recon: frames-dir -> recon PNGs + measured bpp.

All-intra baseline: each sampled frame is compressed independently with REAL entropy
coding (compressai compress/decompress), bits = encoded string bytes * 8 — no estimated
bpp_loss. Mirrors the tools/dcvc_codec_recon.py contract: last stdout line is "bpp=<v>".
Run inside the 'ugicm' conda env:
  /home/xinyizheng/anaconda3/envs/ugicm/bin/python tools/ugicm_codec_recon.py \
      --frames-dir <dir> --out-dir <dir> --ckpt <N.pth.tar>
"""
import argparse, glob, math, os, sys

import torch
import torchvision.transforms.functional as TF
from PIL import Image

REPO = '/mnt/nas/xinyizheng/vcm_baselines/repos/UG-ICM'
sys.path.insert(0, REPO)
from models import UG_MLICPlusPlus            # noqa: E402
from config.config import model_config        # noqa: E402


def flat_bytes(ss):
    if isinstance(ss, (bytes, bytearray)):
        return len(ss)
    return sum(flat_bytes(s) for s in ss)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--frames-dir', required=True)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--ckpt', required=True)
    a = ap.parse_args()

    dev = 'cuda' if torch.cuda.is_available() else 'cpu'
    net = UG_MLICPlusPlus(config=model_config()).to(dev).eval()
    ck = torch.load(a.ckpt, map_location='cpu')
    net.load_state_dict(ck['state_dict'] if 'state_dict' in ck else ck)
    net.update(force=True)

    frames = sorted(glob.glob(os.path.join(a.frames_dir, '*.png')))
    assert frames, f'no input frames in {a.frames_dir}'
    os.makedirs(a.out_dir, exist_ok=True)
    total_bits, total_px = 0, 0
    with torch.no_grad():
        for i, f in enumerate(frames):
            x = TF.to_tensor(Image.open(f).convert('RGB')).unsqueeze(0).to(dev)
            h, w = x.shape[-2:]
            H, W = math.ceil(h / 64) * 64, math.ceil(w / 64) * 64
            xp = torch.nn.functional.pad(x, (0, W - w, 0, H - h), mode='replicate')
            out = net.compress(xp)
            rec = net.decompress(out['strings'], out['shape'], net.beta)
            xh = rec['x_hat'][..., :h, :w].clamp(0, 1)
            TF.to_pil_image(xh.squeeze(0).cpu()).save(
                os.path.join(a.out_dir, f'recon_{i:04d}.png'))
            total_bits += flat_bytes(out['strings']) * 8
            total_px += h * w
    print(f'bpp={total_bits / total_px:.6f}')


if __name__ == '__main__':
    main()
