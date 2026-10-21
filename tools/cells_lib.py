"""cells_lib.py -- shared loaders for the paper's result pools (CVPR-27 cycle).

Mirrors the file sets and filters of tools/table_cells_phasemean.py (the canonical
tab:main cell computation) so every analysis tool reads exactly the same rows:

  * Video-MME long+motion: phase-0 harvests + the 4-phase offset harvests, motion
    domains only, pooled by plain row mean (lamb050 full-pool harvest replaces the
    partial one).
  * EgoSchema common pool: phase 0 from results.csv (first row per uuid), phases 1..3
    from stratified_off{1,2,3}.csv, restricted to the ours/HEVC/VVC/DCVC common set.

Pairing: within one phase file, rows of (interface, rate, uuid) appear in manifest
question order, so the k-th row of arm A pairs with the k-th row of arm B.
"""
from __future__ import annotations

import collections
import csv
import glob
import json
import os
from dataclasses import dataclass

R = os.environ.get("VIDTOK_OUT", "/mnt/nas/xinyizheng/vidtok_out")
REPO = os.environ.get("VIDTOK_REPO", "/home/xinyizheng/vid_tokenizer")
MOTION = {"Sports Competition", "Artistic Performance", "Film & Television"}


def load(p: str) -> list[dict]:
    try:
        with open(p) as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def merge(*pats: str) -> list[dict]:
    """Concatenate CSVs matching the globs, deduped by real path (NAS symlinks)."""
    out: list[dict] = []
    seen: set[str] = set()
    for pat in pats:
        for p in sorted(glob.glob(pat)):
            rp = os.path.realpath(p)
            if rp in seen:
                continue
            seen.add(rp)
            out += load(p)
    return out


def ok(r: dict) -> bool:
    return str(r.get("correct", "")).lower() in ("true", "1")


def graded(r: dict) -> bool:
    return str(r.get("correct", "")).lower() in ("true", "false", "1", "0")


def rate_aliases(iface: str, rate: str) -> list[str]:
    """results.csv says 'vvc_qp46'/'dcvc_q22'; the harvest CSVs say 'qp46'/'q22'."""
    pre = iface + "_"
    return [rate, rate[len(pre):]] if rate.startswith(pre) else [rate, pre + rate]


def vmme_domains() -> dict[str, str]:
    p = os.path.join(REPO, "outputs/datasets/vmme_long_motion/questions.jsonl")
    return {json.loads(l)["video_idx"]: json.loads(l).get("domain") for l in open(p)}


@dataclass(frozen=True)
class Pool:
    """One dataset's row sources: a list of 'phases', each a list of CSV rows."""
    name: str
    phases: list[list[dict]]
    videos: set[str]           # videos that count (motion pool / common-100)
    first_row_only: bool       # EgoSchema results.csv holds re-run repeats


def vmme_pool() -> Pool:
    g = f"{R}/gate1_vmme"
    v0 = merge(f"{g}/stratified_n179.csv", f"{g}/stratified_lowbpp.csv", f"{g}/stratified_lamb*.csv",
               f"{g}/stratified_dcvc.csv", f"{g}/stratified_smcpp_ugicm.csv", f"{g}/stratified_vcmrs.csv",
               f"{g}/stratified_vcmrs_qp17_ph0.csv")
    v0 += [r for r in merge(f"{g}/stratified_learned.csv") if r.get("interface") == "learned"]
    vp = merge(f"{g}/stratified_off*_s*.csv", f"{g}/stratified_off*_cheng.csv")
    l050 = merge(f"{g}/stratified_l050_off*_s*.csv")
    if l050:
        v0 = [r for r in v0 if r.get("rate") != "cap_r1_lamb050"]
        vp = [r for r in vp if r.get("rate") != "cap_r1_lamb050"] + l050
    u2d = vmme_domains()
    motion = {u for u, d in u2d.items() if d in MOTION}
    # phases are not labelled in the VMME offset files; keep phase 0 separate from the rest
    return Pool("vmme", [v0, vp], motion, first_row_only=False)


def ego_pool() -> Pool:
    g = f"{R}/gate1_egos"
    res = load(f"{g}/results.csv")
    ecvcm = merge(f"{g}/stratified_ecvcm.csv")
    cheng = merge(f"{g}/stratified_cheng.csv")
    if cheng:
        ecvcm = [r for r in ecvcm if r.get("interface") != "learned"]

    def uu(i, rt):
        return {r["uuid"] for r in res if r.get("interface") == i and r.get("rate") == rt}

    common = (uu("ours", "cap_r1")
              & set().union(*[uu("pixel", f"crf{c}") for c in (28, 33, 40, 45, 51)])
              & set().union(*[uu("vvc", f"vvc_qp{q}") for q in (28, 32, 36, 40, 46)])
              & set().union(*[uu("dcvc", f"dcvc_q{q}") for q in (22, 33, 40, 45, 52)]))
    phases = [res + ecvcm + cheng] + [load(f"{g}/stratified_off{o}.csv") for o in (1, 2, 3)]
    return Pool("ego", phases, common, first_row_only=True)


def get_pool(name: str) -> Pool:
    return {"vmme": vmme_pool, "ego": ego_pool}[name]()


def arm_rows(pool: Pool, iface: str, rate: str, bucket: str | None = None
             ) -> list[dict[str, list[bool]]]:
    """Per phase: {uuid: [correct, ...]} in manifest order, filtered to the pool's videos."""
    out = []
    aliases = set(rate_aliases(iface, rate))
    for rows in pool.phases:
        per: dict[str, list[bool]] = collections.defaultdict(list)
        for r in rows:
            if r.get("interface") != iface or r.get("rate") not in aliases or not graded(r):
                continue
            u = r.get("uuid")
            if u not in pool.videos:
                continue
            if bucket and r.get("bucket", "all") != bucket:
                continue
            if pool.first_row_only and per[u]:
                continue
            per[u].append(ok(r))
        out.append(dict(per))
    return out


def paired_deltas(pool: Pool, a: tuple[str, str], b: tuple[str, str], bucket: str | None = None
                  ) -> list[tuple[str, float, float]]:
    """(uuid, correct_a, correct_b) per matched question across all phases (A minus B
    is computed by the caller). Phases without both arms contribute nothing."""
    out = []
    for pa, pb in zip(arm_rows(pool, *a, bucket=bucket), arm_rows(pool, *b, bucket=bucket)):
        for u in sorted(set(pa) & set(pb)):
            for x, y in zip(pa[u], pb[u]):
                out.append((u, float(x), float(y)))
    return out


def bpp_map(results_csv: str) -> dict[tuple[str, str, str], float]:
    """(interface, rate, uuid) -> measured bpp from a results.csv (first graded row)."""
    m: dict[tuple[str, str, str], float] = {}
    for r in load(results_csv):
        k = (r.get("interface"), r.get("rate"), r.get("uuid"))
        if k in m:
            continue
        try:
            m[k] = float(r.get("bpp"))
        except (TypeError, ValueError):
            pass
    return m
