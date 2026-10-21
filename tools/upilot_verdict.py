#!/usr/bin/env python3
"""upilot_verdict.py -- decision gate G1 for the universal (receiver-side) adapter.

On the 20 paired pilot videos (R/exp_shared_adapter_u/pilot_targets.txt) and two rungs
(lamb025, cap_r1), compares three adapter regimes:
  per-video   trainable adapter, bits as reported in the AAAI paper (gate1_vmme)
  R2 chain    frozen 8-video chain donor (exp_shared_adapter_r2 @cap_r1, exp_adapter_lowrate @lamb025)
  universal   frozen 32-donor round-robin adapter (exp_shared_adapter_u/pilot)
Reports per rung: mean bpp ratio vs per-video (and how many videos got costlier), and the
paired accuracy difference vs per-video over all matched questions (phase 0 grid).
"""
from __future__ import annotations

import collections
import random
import statistics as st

from cells_lib import R, bpp_map, graded, load, ok

U = f"{R}/exp_shared_adapter_u"
TARGETS = [l.strip() for l in open(f"{U}/pilot_targets.txt") if l.strip()]
RUNGS = ["cap_r1_lamb025", "cap_r1"]


def per_q(rows, rate):
    d = collections.defaultdict(list)
    for r in rows:
        if r.get("interface") == "ours" and r.get("rate") == rate and r.get("uuid") in TARGETS and graded(r):
            d[r["uuid"]].append(ok(r))
    return d


def paired(arm, base):
    deltas, by = [], collections.defaultdict(list)
    for u in sorted(set(arm) & set(base)):
        for x, y in zip(arm[u], base[u]):
            deltas.append(float(x) - float(y)); by[u].append(float(x) - float(y))
    if not deltas:
        return None
    units = list(by.values()); rng = random.Random(0); boots = []
    for _ in range(5000):
        flat = [d for g in rng.choices(units, k=len(units)) for d in g]
        boots.append(sum(flat) / len(flat))
    boots.sort()
    return sum(deltas) / len(deltas), boots[124], boots[4874], len(deltas), len(by)


def ratio(bm_arm, bm_base, rate):
    rs = []
    for u in TARGETS:
        a, b = bm_arm.get(("ours", rate, u)), bm_base.get(("ours", rate, u))
        if a and b:
            rs.append(a / b)
    return rs


base_rows = load(f"{R}/gate1_vmme/stratified_n179.csv") + load(f"{R}/gate1_vmme/stratified_lowbpp.csv")
base_bpp = bpp_map(f"{R}/gate1_vmme/results.csv")
uni_rows = load(f"{U}/pilot/stratified_upilot.csv")
uni_bpp = bpp_map(f"{U}/pilot/results.csv")
r2_rows = load(f"{R}/exp_shared_adapter_r2/stratified_sharedadapter_r2.csv")
r2_bpp = {**bpp_map(f"{R}/exp_adapter_lowrate/results.csv"), **bpp_map(f"{R}/exp_shared_adapter_r2/results.csv")}

print(f"G1 pilot verdict: {len(TARGETS)} target videos")
for rate in RUNGS:
    print(f"\n== rung {rate}")
    base = per_q(base_rows, rate)
    for name, rows, bm in (("R2 chain ", r2_rows, r2_bpp), ("universal", uni_rows, uni_bpp)):
        rs = ratio(bm, base_bpp, rate)
        if rs:
            print(f"  {name}: bpp ratio vs per-video mean={st.mean(rs):.3f} median={st.median(rs):.3f} "
                  f"costlier in {sum(1 for x in rs if x > 1)}/{len(rs)} videos")
        else:
            print(f"  {name}: no bpp rows yet")
        p = paired(per_q(rows, rate), base)
        if p:
            m, lo, hi, n, nv = p
            print(f"  {name}: paired dAcc vs per-video = {m:+.3f} 95% CI [{lo:+.3f},{hi:+.3f}] (n={n} questions, {nv} videos)")
        else:
            print(f"  {name}: no accuracy rows yet")
print("\nDecision rule: pick the adapter with the lower premium at both rungs; either way the frozen"
      " adapter becomes the main configuration (bit accounting), premiums are reported per rung.")
