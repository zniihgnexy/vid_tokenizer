#!/usr/bin/env python3
"""Query-time OOM-boundary sweep (the deployment advantage, as an explicit comparison).

Standard codecs (HEVC/VVC/DCVC) at query time must decode pixels and run the FULL vision
tower at 256 tokens/frame -> the LLM then holds nf*256 tokens; this OOMs at a modest frame
budget = the long-video feasibility ceiling. OUR cached, pixel-free representation skips the
vision tower and (crucially) can be spatially POOLED to 64 or 16 tokens/frame, pushing the
OOM ceiling ~4x / ~16x higher. We report, per method, the MAX FEASIBLE frame budget before
OOM on a single fixed GPU, plus peak memory at each budget.

MUST run on a CLEAN GPU (empty card) -- OOM boundary is meaningless if other jobs share the
card. Usage:
  CUDA_VISIBLE_DEVICES=<free> PYTHONPATH=src python tools/oom_boundary_sweep.py \
      --frames 8 16 24 32 48 64 96 128 192 256 384 512 768 1024
Writes /mnt/nas/xinyizheng/vidtok_out/oom_boundary/oom_boundary.csv
"""
import argparse, csv, os, time
import torch
from machine_codec_pipeline.vlm.internvl_backend import (
    load_internvl, extract_internvit_tokens, load_image, chat_embeds, DEFAULT_MODEL_PATH,
)
OUT = '/mnt/nas/xinyizheng/vidtok_out/oom_boundary'; os.makedirs(OUT, exist_ok=True)
Q = "What happens in the video?\nOptions:\nA. x\nB. y\nC. z\nD. w\nAnswer with the option letter only."

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model-path", default=DEFAULT_MODEL_PATH)
    ap.add_argument("--frames", type=int, nargs="+",
                    default=[8,16,24,32,48,64,96,128,192,256,384,512,768,1024])
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()
    model, tok = load_internvl(args.model_path, device=args.device)
    dev = next(model.parameters()).device; dt = next(model.parameters()).dtype
    hid = model.language_model.config.hidden_size
    total_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
    one = load_image(f"{args.model_path}/examples/image1.jpg", input_size=448, max_num=1).to(dev, dt)
    print(f"[oom] GPU total={total_gb:.0f}GB llm_hidden={hid}")

    # (label, tokens/frame, runs_vision) -- pixel path forced to 256 tok & must run ViT;
    # ours paths skip ViT and can pool.
    METHODS = [("pixel (decode+ViT, 256 tok/f)", 256, True),
               ("ours cached (256 tok/f)",       256, False),
               ("ours pooled (64 tok/f)",         64, False),
               ("ours pooled (16 tok/f)",         16, False)]
    rows = []; summary = {}
    for label, P, run_vis in METHODS:
        model.num_image_token = P
        maxfeasible = 0
        print(f"\n=== {label} ===")
        for nf in args.frames:
            if torch.cuda.is_available(): torch.cuda.reset_peak_memory_stats(); torch.cuda.empty_cache()
            q = "".join("<image>\n" for _ in range(nf)) + Q
            try:
                if run_vis:  # account for the vision tower the pixel path cannot avoid
                    CH = 16
                    for i in range(0, nf, CH):
                        extract_internvit_tokens(model, one.repeat(min(CH, nf - i), 1, 1, 1))
                embeds = torch.randn(nf, P, hid, device=dev, dtype=dt)
                chat_embeds(model, tok, embeds, [1] * nf, q, 16)
                if torch.cuda.is_available(): torch.cuda.synchronize()
                peak = torch.cuda.max_memory_allocated() / 1e9 if torch.cuda.is_available() else 0
                print(f"  {nf:>5}f  tokens={nf*P:>7}  peak={peak:6.1f}GB  OK")
                rows.append(dict(method=label, tokens_per_frame=P, frames=nf, total_tokens=nf*P,
                                 peak_gb=round(peak, 2), status="ok"))
                maxfeasible = nf
                del embeds
            except RuntimeError as e:
                if "out of memory" in str(e).lower():
                    print(f"  {nf:>5}f  tokens={nf*P:>7}  >>> OOM <<<")
                    rows.append(dict(method=label, tokens_per_frame=P, frames=nf, total_tokens=nf*P,
                                     peak_gb=None, status="OOM"))
                    torch.cuda.empty_cache(); break
                raise
        summary[label] = maxfeasible
        print(f"  -> max feasible frames: {maxfeasible}")
    with open(f"{OUT}/oom_boundary.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["method","tokens_per_frame","frames","total_tokens","peak_gb","status"])
        w.writeheader(); w.writerows(rows)
    print(f"\n===== MAX FEASIBLE FRAME BUDGET (before OOM), {total_gb:.0f}GB GPU =====")
    for k, v in summary.items():
        print(f"  {k:32} {v:>5} frames")
    print(f"\nwritten -> {OUT}/oom_boundary.csv")

if __name__ == "__main__":
    main()
