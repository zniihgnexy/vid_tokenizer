#!/usr/bin/env python3
"""ctrl_report.py -- summarise the CVPR-27 control harvests (B1 cached-pixel path, B2 shuffle /
mismatch) against the normal arms, on the paper's pools (motion domains / common-100).

Reads R/gate1_{vmme,egos}/stratified_ctrl_*.csv produced by harvest_stratified.py --ctrl /
--pixel-cache-pool, plus the phase-0 reference rows of ours@cap_r1 and the oracle.
Accuracy with video-cluster bootstrap CIs; VMME split by bucket.
"""
from __future__ import annotations

import collections
import glob
import random

from cells_lib import R, get_pool, graded, load, ok


def cell(rows, iface, rate, videos, bucket=None, first_only=False):
    per = collections.defaultdict(list)
    for r in rows:
        if r.get("interface") != iface or (rate and r.get("rate") != rate) or not graded(r):
            continue
        if r.get("uuid") not in videos:
            continue
        if bucket and r.get("bucket", "all") != bucket:
            continue
        if first_only and per[r["uuid"]]:
            continue  # EgoSchema results.csv holds re-run repeats: first row per video
        per[r["uuid"]].append(1.0 if ok(r) else 0.0)
    if not per:
        return None
    units = list(per.values()); n = sum(len(u) for u in units)
    acc = sum(sum(u) for u in units) / n
    rng = random.Random(0); boots = []
    for _ in range(2000):
        flat = [x for g in rng.choices(units, k=len(units)) for x in g]
        boots.append(sum(flat) / len(flat))
    boots.sort()
    return acc, boots[49], boots[1949], n, len(units)


def fmt(c):
    return "   --" if c is None else f"{c[0]:.3f} [{c[1]:.2f},{c[2]:.2f}] n={c[3]}/{c[4]}v"


for ds, gate, buckets in (("vmme", "gate1_vmme", ["temporal", "detail", "gist"]), ("ego", "gate1_egos", [None])):
    pool = get_pool(ds)
    ref = pool.phases[0]
    ctrl = []
    for p in glob.glob(f"{R}/{gate}/stratified_ctrl_*.csv"):
        ctrl += load(p)
    print(f"\n===== {ds}: videos in pool = {len(pool.videos)}; control rows = {len(ctrl)} =====")
    arms = [("oracle", ref, "oracle", "NA"), ("ours@cap_r1", ref, "ours", "cap_r1"),
            ("oracle shuffled", ctrl, "oracle_shuffle", "NA"), ("ours shuffled", ctrl, "ours_shuffle", "cap_r1"),
            ("oracle mismatched", ctrl, "oracle_mismatch", "NA"), ("ours mismatched", ctrl, "ours_mismatch", "cap_r1"),
            ("blind floor (paper)", None, None, None)]
    pooled = {K: (load(f"{R}/{gate}/stratified_pool{K}.csv") if ds == "vmme"
                  else load(f"{R}/{gate}/stratified_ourspool{K}.csv")) for K in (64, 16)}
    for K in (64, 16):
        arms += [(f"ours@cap_r1 pool{K}", pooled[K], "ours", "cap_r1")]
        arms += [(f"oracle cache pool{K}", ctrl, "oraclecache", f"oracle_p{K}")]
        arms += [(f"HEVC crf{c} cache pool{K}", ctrl, "pixelcache", f"crf{c}_p{K}") for c in (33, 40, 45)]
    for bucket in buckets:
        print(f"-- bucket: {bucket or 'all'}")
        for name, rows, iface, rate in arms:
            if rows is None:
                floor = {"temporal": 0.401, "detail": 0.366, "gist": 0.509, None: 0.330}[bucket]
                print(f"  {name:26s} {floor:.3f}")
                continue
            print(f"  {name:26s} {fmt(cell(rows, iface, rate, pool.videos, bucket, first_only=pool.first_row_only))}")
