"""Emit tab:main's cells under the 4-phase-mean protocol, row by row, next to the
values currently in the paper, so the edit list is mechanical.

VMME and MLVU aggregate by plain row mean, so their phases can be pooled.
EgoSchema keeps only the first row per uuid (results.csv holds re-run repeats),
so each phase is reduced to its own point first and the points are averaged.
"""
import collections
import csv
import glob
import json
import os

import numpy as np

R = "/mnt/nas/xinyizheng/vidtok_out"
MOTION = {"Sports Competition", "Artistic Performance", "Film & Television"}


def load(p):
    try:
        return list(csv.DictReader(open(p)))
    except Exception:
        return []


def merge(*pats):
    """Dedupe by real path: outputs/gate1_* are symlinks to the same NAS files, and
    loading a phase-0 CSV twice silently reweights it from 1/4 to 2/5 of the phase
    mean -- which tilts every temporally-subsampling arm in its own favour."""
    out = []
    seen = set()
    for pat in pats:
        for p in sorted(glob.glob(pat)):
            rp = os.path.realpath(p)
            if rp in seen:
                continue
            seen.add(rp)
            out += load(p)
    return out


def ok(r):
    return str(r.get("correct", "")).lower() in ("true", "1")


def graded(r):
    return str(r.get("correct", "")).lower() in ("true", "false", "1", "0")


u2d = {json.loads(l)["video_idx"]: json.loads(l).get("domain")
       for l in open("outputs/datasets/vmme_long_motion/questions.jsonl")}

# ---------------- Video-MME long+motion ----------------
V0 = merge(f"{R}/gate1_vmme/stratified_n179.csv", f"{R}/gate1_vmme/stratified_lowbpp.csv",
           f"{R}/gate1_vmme/stratified_lamb*.csv", f"{R}/gate1_vmme/stratified_dcvc.csv",
           f"{R}/gate1_vmme/stratified_smcpp_ugicm.csv", f"{R}/gate1_vmme/stratified_vcmrs.csv",
           f"{R}/gate1_vmme/stratified_vcmrs_qp17_ph0.csv",
           "outputs/gate1_vmme/stratified_smcpp_ugicm.csv",
           "outputs/gate1_vmme/stratified_vcmrs.csv")
# cheng2020 on VMME is interface 'learned' and its phase-0 rows live in
# stratified_learned.csv (the stratified_cheng.csv name is EgoSchema-only). That
# harvest ran on its own ~70-video subset and carries its own oracle rows, so only
# the learned rows are taken: pooling its oracle rows would shift the shared oracle
# cell from 0.471 to 0.461 by silently reweighting the video pool.
V0 += [r for r in merge(f"{R}/gate1_vmme/stratified_learned.csv")
       if r.get("interface") == "learned"]
VP = merge(f"{R}/gate1_vmme/stratified_off*_s*.csv", f"{R}/gate1_vmme/stratified_off*_cheng.csv")
# lamb050's completed 4-phase harvest over the full 94-video pool REPLACES both the
# old partial-pool CSV and the lamb050 rows inside the stage-1 offset harvest; the
# partial-pool value read 0.485, which was subset bias, not a rate response.
_L050 = merge(f"{R}/gate1_vmme/stratified_l050_off*_s*.csv")
if _L050:
    V0 = [r for r in V0 if r.get("rate") != "cap_r1_lamb050"]
    VP = [r for r in VP if r.get("rate") != "cap_r1_lamb050"] + _L050


def vmme_cell(rows, iface, rate):
    per = collections.defaultdict(list)
    bl = []
    for r in rows:
        if r.get("interface") != iface or r.get("rate") != rate or not graded(r):
            continue
        if u2d.get(r.get("uuid")) not in MOTION:
            continue
        per[r.get("bucket", "all")].append(ok(r))
        per["ALL"].append(ok(r))
        raw = r.get("bpp")
        if raw not in ("NA", "", "None", None):
            try:
                bl.append(float(raw))
            except ValueError:
                pass
    if not per["ALL"]:
        return None
    return dict(bpp=float(np.mean(bl)) if bl else None, n=len(per["ALL"]),
                **{k: float(np.mean(per[k])) for k in ("temporal", "detail", "gist", "ALL")
                   if per.get(k)})


# ---------------- EgoSchema common pool ----------------
G = load(f"{R}/gate1_egos/results.csv")
_ecvcm = merge(f"{R}/gate1_egos/stratified_ecvcm.csv",
               "outputs/gate1_egos/stratified_ecvcm.csv")
_cheng = merge(f"{R}/gate1_egos/stratified_cheng.csv",
               "outputs/gate1_egos/stratified_cheng.csv")
# the ecvcm harvest's learned (cheng2020) rows came from incomplete recons and read
# near chance; the fixed re-harvest is stratified_cheng.csv. Same drop the figure does.
if _cheng:
    _ecvcm = [r for r in _ecvcm if r.get("interface") != "learned"]
EX = _ecvcm + _cheng
EP = [load(f"{R}/gate1_egos/stratified_off{o}.csv") for o in (1, 2, 3)]


def uu(i, rt):
    return {r["uuid"] for r in G if r.get("interface") == i and r.get("rate") == rt}


common = (uu("ours", "cap_r1")
          & set().union(*[uu("pixel", f"crf{c}") for c in (28, 33, 40, 45, 51)])
          & set().union(*[uu("vvc", f"vvc_qp{q}") for q in (28, 32, 36, 40, 46)])
          & set().union(*[uu("dcvc", f"dcvc_q{q}") for q in (22, 33, 40, 45, 52)]))


def ego_one(rows, iface, rate):
    seen = {}
    bl = {}
    for r in rows:
        if r.get("interface") != iface or r.get("rate") != rate or r.get("uuid") not in common:
            continue
        if not graded(r):
            continue
        if r["uuid"] in seen:
            continue
        seen[r["uuid"]] = ok(r)
        raw = r.get("bpp")
        if raw not in ("NA", "", "None", None):
            try:
                bl[r["uuid"]] = float(raw)
            except ValueError:
                pass
    if not seen:
        return None
    return (float(np.mean(list(bl.values()))) if bl else None,
            float(np.mean(list(seen.values()))), len(seen))


def rate_aliases(iface, rate):
    """results.csv says 'vvc_qp46'/'dcvc_q22'; the harvest CSVs say 'qp46'/'q22'."""
    pre = iface + "_"
    return [rate, rate[len(pre):]] if rate.startswith(pre) else [rate, pre + rate]


def ego_cell(iface, rate, phase0_extra=False):
    base = (G + EX) if phase0_extra else G
    pts = []
    for rs in [base] + EP:
        for rt in rate_aliases(iface, rate):
            if (p := ego_one(rs, iface, rt)):
                pts.append(p)
                break
    if not pts:
        return None
    bs = [p[0] for p in pts if p[0] is not None]
    return dict(bpp=float(np.mean(bs)) if bs else None,
                acc=float(np.mean([p[1] for p in pts])), phases=len(pts), n=pts[0][2])


# ---------------- MLVU-100 (tab:main's third column group) ----------------
M = f"{R}/gate1_mlvu"
ML = (merge(f"{M}/stratified_mcodec_s*.csv", f"{M}/stratified_ourslam_s*.csv",
            f"{M}/stratified_qa_s*.csv", f"{M}/results.csv")
      + merge(f"{M}/stratified_off*_s*.csv"))


def mlvu_cell(iface, rate):
    alias = set(rate_aliases(iface, rate))
    hits, bl = [], []
    for r in ML:
        if r.get("interface") != iface or r.get("rate") not in alias or not graded(r):
            continue
        hits.append(ok(r))
        raw = r.get("bpp")
        if raw not in ("NA", "", "None", None):
            try:
                bl.append(float(raw))
            except ValueError:
                pass
    if not hits:
        return None
    return dict(bpp=float(np.mean(bl)) if bl else None, acc=float(np.mean(hits)), n=len(hits))


MLVU_ROWS = [  # (label, iface, rate, paper bpp, paper acc)
    ("Oracle", "oracle", "NA", None, 0.55),
    ("HEVC low", "pixel", "crf51", 0.034, 0.47),
    ("HEVC mat", "pixel", "crf33", 0.148, 0.54),
    ("DCVC low", "dcvc", "dcvc_q22", 0.043, 0.56),
    ("DCVC mat", "dcvc", "dcvc_q37", 0.112, 0.57),
    ("SMC++ low", "smcpp", "crf47", 0.030, 0.53),
    ("SMC++ mat", "smcpp", "crf39", 0.067, 0.57),
    ("UG-ICM floor", "ugicm", "q1", 0.152, 0.56),
    ("VCM-RS u.low", "vcmrs", "vcmrs_qp52", 0.004, 0.45),
    ("VCM-RS low", "vcmrs", "vcmrs_qp32", 0.021, 0.54),
    ("VCM-RS mat", "vcmrs", "vcmrs_qp22", 0.065, 0.53),
    ("Ours floor", "ours", "cap_r1_lamb006", 0.020, 0.47),
    ("Ours low", "ours", "cap_r1_lamb025", 0.046, 0.51),
    ("Ours low+", "ours", "cap_r1_lamb050", 0.079, 0.51),
    ("Ours mat", "ours", "cap_r1", 0.115, 0.52),
    ("Ours high", "ours", "cap_r1_lamb150", 0.138, 0.53),
]

ROWS = [  # (label, vmme_iface, vmme_rate, ego_iface, ego_rate, paper_vmme_temporal, paper_ego_acc)
    ("Oracle",        "oracle", "NA",     "oracle", "NA",          0.47, 0.76),
    ("HEVC low",      "pixel", "crf45",   "pixel", "crf45",        0.39, 0.42),
    ("HEVC mat",      "pixel", "crf33",   "pixel", "crf33",        0.44, 0.67),
    ("VVC low",       "vvc", "qp46",      "vvc", "vvc_qp46",       0.36, 0.45),
    ("VVC mat",       "vvc", "qp32",      "vvc", "vvc_qp32",       0.45, 0.66),
    ("cheng floor",   "learned", "q1",    "learned", "q1",         0.43, 0.65),
    ("DCVC low",      "dcvc", "q18",      "dcvc", "dcvc_q22",      0.40, 0.55),
    ("DCVC mat",      "dcvc", "q34",      "dcvc", "dcvc_q40",      0.45, 0.63),
    ("SMC++ low",     "smcpp", "crf51",   "smcpp", "crf51",        0.40, 0.51),
    ("SMC++ mat",     "smcpp", "crf35",   "smcpp", "crf35",        0.45, 0.68),
    ("UG-ICM floor",  "ugicm", "q1",      "ugicm", "q1",           0.42, 0.70),
    ("VCM-RS u.low",  "vcmrs", "qp52",    "vcmrs", "qp52",         0.41, 0.43),
    ("VCM-RS low",    "vcmrs", "qp32",    "vcmrs", "qp32",         0.45, 0.69),
    ("VCM-RS mat",    "vcmrs", "qp22",    "vcmrs", "qp22",         0.46, 0.72),
    ("Ours floor",    "ours", "cap_r1_lamb006", "ours", "cap_r1_lamb006", 0.38, 0.48),
    ("Ours low",      "ours", "cap_r1_lamb025", "ours", "cap_r1_lamb025", 0.47, 0.62),
    ("Ours low+",     "ours", "cap_r1_lamb050", "ours", "cap_r1_lamb050", 0.44, 0.65),
    ("Ours mat",      "ours", "cap_r1",         "ours", "cap_r1",         0.46, 0.71),
    ("Ours high",     "ours", "cap_r1_lamb150", "ours", "cap_r1_lamb150", 0.42, 0.76),
]

print("tab:main under the 4-phase mean. paper = value now in tables_latest.tex.")
print("VMME temporal/detail/gist/all, then EgoSchema acc. * marks a shift >= 0.02.\n")
hdr = (f"{'row':14s} {'bpp':>6s} {'temp':>13s} {'detail':>7s} {'gist':>6s} "
       f"{'all':>6s} | {'Ego bpp':>7s} {'Ego acc':>14s} {'ph':>3s}")
print(hdr)
print("-" * len(hdr))
for label, vi, vr, ei, er, pap_v, pap_e in ROWS:
    v = vmme_cell(V0 + VP, vi, vr)
    e = ego_cell(ei, er, phase0_extra=(ei not in ("pixel", "vvc", "dcvc", "ours", "oracle")))
    if v:
        mark = "*" if abs(v["temporal"] - pap_v) >= 0.02 else " "
        bstr = f"{v['bpp']:6.3f}" if v["bpp"] is not None else f"{'--':>6s}"
        vs = (f"{bstr} {v['temporal']:.3f}({pap_v:.2f}){mark} "
              f"{v.get('detail', float('nan')):7.3f} {v.get('gist', float('nan')):6.3f} "
              f"{v['ALL']:6.3f}")
    else:
        vs = f"{'--':>6s} {'--':>13s} {'--':>7s} {'--':>6s} {'--':>6s}"
    if e:
        mk = "*" if abs(e["acc"] - pap_e) >= 0.02 else " "
        b = f"{e['bpp']:7.3f}" if e["bpp"] is not None else f"{'--':>7s}"
        es = f"{b} {e['acc']:.3f}({pap_e:.2f}){mk} {e['phases']:>3d}"
    else:
        es = f"{'--':>7s} {'--':>14s} {'--':>3s}"
    print(f"{label:14s} {vs} | {es}")
print(f"\nEgoSchema common pool n={len(common)}; blind floors 0.401 (VMME temporal) / 0.330 (Ego)")

print("\n=== MLVU-100 column of tab:main (4-phase mean) ===")
h2 = f"{'row':14s} {'bpp':>6s}({'paper':>5s}) {'acc':>13s} {'n':>5s}"
print(h2)
print("-" * len(h2))
for label, iface, rate, pb, pa in MLVU_ROWS:
    c = mlvu_cell(iface, rate)
    if not c:
        print(f"{label:14s} {'-- no data --':>32s}")
        continue
    mk = "*" if abs(c["acc"] - pa) >= 0.02 else " "
    b = f"{c['bpp']:6.3f}" if c["bpp"] is not None else f"{'--':>6s}"
    pbs = f"{pb:5.3f}" if pb is not None else f"{'--':>5s}"
    print(f"{label:14s} {b}({pbs}) {c['acc']:.3f}({pa:.2f}){mk} {c['n']:>5d}")
