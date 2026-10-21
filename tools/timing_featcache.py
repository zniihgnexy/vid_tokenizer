#!/usr/bin/env python3
"""E-14: wall time of the feature-cache baselines per video: frozen ViT over all cached frames + encode."""
import argparse, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import torch
from machine_codec_pipeline.vlm.internvl_backend import load_internvl, DEFAULT_MODEL_PATH
from machine_codec_pipeline.featcache import FeatCodec, parse_spec
from machine_codec_pipeline.featcache.ae import AECodec
from machine_codec_pipeline.featcache.extract import video_tokens

R = "/mnt/nas/xinyizheng/vidtok_out"
ap = argparse.ArgumentParser()
ap.add_argument("--frames-root", required=True); ap.add_argument("--uuids", nargs="+", required=True)
ap.add_argument("--gpu-name", default=""); ap.add_argument("--out", required=True)
a = ap.parse_args()
model, _ = load_internvl(os.environ.get("INTERNVL_MODEL_PATH", DEFAULT_MODEL_PATH))
book = torch.load(f"{R}/exp_featcache/featcodec_internvl_v1.pt", map_location="cpu")
sq = FeatCodec(book, parse_spec("p64_pca64_q2")); ae = AECodec(f"{R}/exp_featcache/ae/p64_ae_z128_l1.pt")
video_tokens(model, f"{a.frames_root}/{a.uuids[0]}_256_uniform")   # warm-up
with open(a.out, "a") as f:
    for u in a.uuids:
        torch.cuda.synchronize(); t0 = time.time()
        tok = video_tokens(model, f"{a.frames_root}/{u}_256_uniform"); torch.cuda.synchronize(); t1 = time.time()
        sq.encode(tok); t2 = time.time()
        ae.encode(tok); torch.cuda.synchronize(); t3 = time.time()
        f.write(f"{u},featcache_vit_tokens,{t1-t0:.3f},{a.gpu_name}\n{u},featcache_pca64_q2_encode,{t2-t1:.3f},{a.gpu_name}\n"
                f"{u},featcache_ae_encode,{t3-t2:.3f},{a.gpu_name}\n")
