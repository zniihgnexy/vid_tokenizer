#!/usr/bin/env python3
"""proxy_vs_error.py -- does the mid-layer proxy distortion predict downstream errors?

AI-review suggestion 1: relate the training proxy (smooth-L1 and cosine at layer N,
read from the LAST '[hidden] step=... smooth_l1=... cos=...' line of each run's
codec.log) to question-level outcomes (ours vs the lossless oracle on the same
questions), per bucket and per rate.

Outputs
  <out>.csv   one row per (rate, uuid): bpp, smooth_l1, cos, n_q, acc_ours, acc_oracle,
              flips (oracle right -> ours wrong), gains (oracle wrong -> ours right)
  stdout      per rate x bucket: Spearman rho between cos and (acc_ours - acc_oracle)
              across videos, AUC of cos for predicting a question-level flip, and a
              cos-tertile table of flip rates. Numpy-free on purpose (runs anywhere).
"""
from __future__ import annotations

import argparse
import collections
import csv
import glob
import os
import re

from cells_lib import R, arm_rows, bpp_map, get_pool

HID = re.compile(r"\[hidden\] step=(\d+) smooth_l1=([0-9.eE+-]+) cos=([0-9.eE+-]+)")


def last_hidden(run_root: str, rate: str, uuid: str):
    cands = glob.glob(f"{run_root}/{rate}/{uuid}/codec.log") + \
        glob.glob(f"{run_root}/{rate}/{uuid}/**/codec.log", recursive=True)
    for p in cands:
        last = None
        try:
            with open(p, errors="ignore") as f:
                for line in f:
                    m = HID.search(line)
                    if m:
                        last = (float(m.group(2)), float(m.group(3)))
        except OSError:
            continue
        if last:
            return last
    return None


def ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(x, y):
    if len(x) < 3:
        return float("nan")
    rx, ry = ranks(x), ranks(y)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else float("nan")


def auc(scores_pos, scores_neg):
    """P(score_pos > score_neg) with ties at 0.5 (Mann-Whitney)."""
    if not scores_pos or not scores_neg:
        return float("nan")
    s = 0.0
    for p in scores_pos:
        for n in scores_neg:
            s += 1.0 if p > n else 0.5 if p == n else 0.0
    return s / (len(scores_pos) * len(scores_neg))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=["vmme", "ego"], default="vmme")
    ap.add_argument("--rates", nargs="+", default=["cap_r1_lamb006", "cap_r1_lamb025", "cap_r1", "cap_r1_lamb150"])
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    pool = get_pool(args.dataset)
    gate = {"vmme": "gate1_vmme", "ego": "gate1_egos"}[args.dataset]
    dsname = {"vmme": "vmme_long_motion", "ego": "egoschema"}[args.dataset]
    run_root = f"{R}/{gate}/{dsname}/internvl/mid/ours"
    bm = bpp_map(f"{R}/{gate}/results.csv")
    out = args.out or f"{R}/{gate}/proxy_vs_error.csv"
    buckets = ["temporal", "detail", "gist"] if args.dataset == "vmme" else [None]

    rows_out = []
    print(f"dataset={args.dataset}  run_root={run_root}")
    for rate in args.rates:
        ours_ph = arm_rows(pool, "ours", rate)
        orc_ph = arm_rows(pool, "oracle", "NA")
        per_video = {}
        qlevel = collections.defaultdict(list)   # bucket -> [(cos, flip)]
        for bucket in buckets:
            ours_b = arm_rows(pool, "ours", rate, bucket=bucket)
            orc_b = arm_rows(pool, "oracle", "NA", bucket=bucket)
            for pa, pb in zip(ours_b, orc_b):
                for u in set(pa) & set(pb):
                    h = last_hidden(run_root, rate, u)
                    if h is None:
                        continue
                    for x, y in zip(pa[u], pb[u]):
                        qlevel[bucket or "all"].append((h[1], x, y))
        for pa, pb in zip(ours_ph, orc_ph):
            for u in set(pa) & set(pb):
                h = last_hidden(run_root, rate, u)
                if h is None:
                    continue
                v = per_video.setdefault(u, dict(rate=rate, uuid=u, bpp=bm.get(("ours", rate, u)),
                                                 smooth_l1=h[0], cos=h[1], n_q=0, ours=0, oracle=0, flips=0, gains=0))
                for x, y in zip(pa[u], pb[u]):
                    v["n_q"] += 1; v["ours"] += x; v["oracle"] += y
                    v["flips"] += int(y and not x); v["gains"] += int(x and not y)
        if not per_video:
            print(f"\n[{rate}] no matched videos with a codec.log -- skipped")
            continue
        for v in per_video.values():
            v["acc_ours"] = v["ours"] / v["n_q"]; v["acc_oracle"] = v["oracle"] / v["n_q"]
            rows_out.append(v)
        cos = [v["cos"] for v in per_video.values()]
        dacc = [v["acc_ours"] - v["acc_oracle"] for v in per_video.values()]
        print(f"\n[{rate}] videos={len(per_video)}  mean cos={sum(cos)/len(cos):.3f}  "
              f"Spearman(cos, acc_ours-acc_oracle)={spearman(cos, dacc):+.3f}")
        for bucket, trip in qlevel.items():
            pos = [c for c, x, y in trip if y and not x]        # flips
            neg = [c for c, x, y in trip if y and x]            # oracle right, ours right
            srt = sorted(trip, key=lambda t: t[0])
            n3 = max(1, len(srt) // 3)
            tert = []
            for k in range(3):
                seg = srt[k * n3:(k + 1) * n3] if k < 2 else srt[2 * n3:]
                orc_right = [t for t in seg if t[2]]
                fr = sum(1 for t in orc_right if not t[1]) / len(orc_right) if orc_right else float("nan")
                tert.append(f"{fr:.2f}(n={len(orc_right)})")
            print(f"   {bucket:9s} questions={len(trip)}  AUC(low cos -> flip)={1 - auc(pos, neg):.3f}  "
                  f"flip rate by cos tertile low/mid/high: {' '.join(tert)}")
    if rows_out:
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
            w.writeheader(); w.writerows(rows_out)
        print(f"\n{len(rows_out)} (rate, video) rows -> {out}")


if __name__ == "__main__":
    main()
