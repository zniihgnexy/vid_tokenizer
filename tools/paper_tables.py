#!/usr/bin/env python3
"""D-021: final paper numbers from the 4-phase harvests (zero GPU). Writes CSV/Markdown tables and
RD-curve data (+ PNG when matplotlib is available) to --out (default R/paper_tables). Never touches
the paper source.

Protocol: 4-phase row mean per cell; 95% CI = video-cluster bootstrap of the cell mean; ours bits include
the 2 KB FiLM delta. Comparisons are PAIRED (same videos and questions): T7/F2 give ours - baseline at the
nearest-rate baseline cell with a paired cluster-bootstrap CI; T1 gives the rate multiplier (bpp a baseline
family needs to match ours' accuracy / ours bpp, log-bpp interpolation on the family's accuracy-monotone
front) with a paired bootstrap CI. RD figures carry no error bars (codec convention); CIs are in the tables.

  python tools/paper_tables.py [--out DIR] [--reps 2000]
"""
import argparse, collections, csv, glob, json, math, os, random, sys
sys.path.insert(0, os.path.dirname(__file__))
from cells_lib import R, REPO, get_pool, arm_rows, merge, bpp_map, rate_aliases, ok, graded

DELTA = 0.05
HEVC = ["crf28", "crf33", "crf40", "crf45", "crf51"]
VVC = ["qp28", "qp32", "qp36", "qp40", "qp46"]
DCVC_EGO = ["q22", "q33", "q40", "q45", "q52"]
DCVC_VMME = ["q14", "q18", "q22", "q28", "q34", "q42"]
MAIN = "_n1224_dfilm"
RUNGS_EGO = ["cap_r1_lamb006", "cap_r1_lamb025", "cap_r1_lamb050", "cap_r1", "cap_r1_lamb150"]
RUNGS_VMME = ["cap_r1_lamb006", "cap_r1_lamb025", "cap_r1"]


# ----------------------------------------------------------------------------- helpers
def uuids_file(p):
    return {l.strip() for l in open(os.path.join(REPO, p)) if l.strip()}


def rows_of(globs, uuids=None, bucket=None):
    rows = merge(*globs)
    if uuids is not None:
        rows = [r for r in rows if r.get("uuid") in uuids]
    if bucket:
        rows = [r for r in rows if r.get("bucket") == bucket]
    return rows


def per_video(rows, iface, rate):
    """{uuid: [bool,...]} over all rows of (iface, rate) in file order."""
    al = set(rate_aliases(iface, rate))
    out = collections.defaultdict(list)
    for r in rows:
        if r.get("interface") == iface and r.get("rate") in al and graded(r):
            out[r["uuid"]].append(ok(r))
    return dict(out)


def flatten_phases(phase_dicts):
    out = collections.defaultdict(list)
    for d in phase_dicts:
        for u, v in d.items():
            out[u].extend(v)
    return dict(out)


def cell_stats(pv, reps, seed=0):
    vids = sorted(pv)
    if not vids:
        return None
    vals = [x for u in vids for x in pv[u]]
    acc = sum(vals) / len(vals)
    rng = random.Random(seed)
    boots = []
    for _ in range(reps):
        sel = [vids[rng.randrange(len(vids))] for _ in vids]
        v = [x for u in sel for x in pv[u]]
        boots.append(sum(v) / len(v))
    boots.sort()
    return {"acc": acc, "lo": boots[int(0.025 * reps)], "hi": boots[int(0.975 * reps) - 1], "n": len(vals), "videos": len(vids)}


def paired(pa, pb, reps, seed=1):
    """Mean(a-b) over matched questions with cluster CI; TOST verdict at ±DELTA."""
    by = {}
    for u in sorted(set(pa) & set(pb)):
        d = [float(x) - float(y) for x, y in zip(pa[u], pb[u])]
        if d:
            by[u] = d
    vids = sorted(by)
    if not vids:
        return None
    rng = random.Random(seed)
    mean = lambda sel: sum(x for u in sel for x in by[u]) / sum(len(by[u]) for u in sel)
    point = mean(vids)
    boots = sorted(mean([vids[rng.randrange(len(vids))] for _ in vids]) for _ in range(reps))
    lo, hi = boots[int(0.025 * reps)], boots[int(0.975 * reps) - 1]
    verdict = "non-inferior" if lo > -DELTA and hi < DELTA else ("inferior" if hi < 0 else "inconclusive")
    return {"delta": point, "lo": lo, "hi": hi, "videos": len(vids), "tost": verdict}


def mean_bpp(bm, iface, rate, videos):
    al = rate_aliases(iface, rate)
    v = [b for (i, r, u), b in bm.items() if i == iface and r in al and u in videos]
    return sum(v) / len(v) if v else float("nan")


def front(cells):
    """cells: list of (bpp, acc, label) -> accuracy-monotone Pareto front sorted by bpp."""
    pts = sorted((b, a, l) for b, a, l in cells if b == b and b > 0)
    out, best = [], -1.0
    for b, a, l in pts:
        if a > best:
            out.append((b, a, l)); best = a
    return out


def reach(fr, target):
    prev = None
    for b, a, _ in fr:
        if a >= target:
            if prev is None or prev[1] == a:
                return b
            pb, pa = prev
            return math.exp(math.log(pb) + (math.log(b) - math.log(pb)) * (target - pa) / (a - pa))
        prev = (b, a)
    return None


def fmt(x, d=3):
    return "—" if x is None or (isinstance(x, float) and x != x) else f"{x:.{d}f}"


def write_table(path, header, rows):
    with open(path + ".csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)
    with open(path + ".md", "w") as f:
        f.write("| " + " | ".join(header) + " |\n|" + "---|" * len(header) + "\n")
        for r in rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")


# ----------------------------------------------------------------------------- pools
def pool_spec(name):
    """Returns dict with: main rows (ours main-config + oracle [+ hevc]), baseline phases, bpp maps, videos."""
    if name == "ego":
        uu = uuids_file("outputs/gate1_egos/common100_uuids.txt")
        main = rows_of([f"{R}/u_egos/stratified_u{MAIN}_off[0-3].csv", f"{R}/u_egos/stratified_u{MAIN}_lamb050_off[0-3].csv"], uu)
        base = get_pool("ego"); bucket = None
        fc = rows_of([f"{R}/exp_featcache/_merged4_fcall_ego.csv"], uu)
        return dict(uu=uu, main=main, base=base, bucket=bucket, fc=fc, rungs=RUNGS_EGO,
                    bm_main=bpp_map(f"{R}/u_egos/results.csv"), bm_base=bpp_map(f"{R}/gate1_egos/results.csv"),
                    dcvc=DCVC_EGO, hevc_rows=None)
    if name in ("vmme", "vmme_temporal"):
        base = get_pool("vmme"); uu = base.videos
        bucket = "temporal" if name == "vmme_temporal" else None
        main = rows_of([f"{R}/u_vmme/stratified_u{MAIN}_off[0-3].csv"], uu, bucket)
        fc = rows_of([f"{R}/exp_featcache/_merged4_fcall_vmme.csv"], uu, bucket)
        return dict(uu=uu, main=main, base=base, bucket=bucket, fc=fc, rungs=RUNGS_VMME,
                    bm_main=bpp_map(f"{R}/u_vmme/results.csv"), bm_base=bpp_map(f"{R}/gate1_vmme/results.csv"),
                    dcvc=DCVC_VMME, hevc_rows=None)
    if name == "vmme_nonmotion":
        uu = uuids_file("outputs/datasets/vmme_long_motion/nonmotion48_uuids.txt")
        main = rows_of([f"{R}/u_vmme/stratified_u{MAIN}_nonmotion_off[0-3].csv"], uu)
        fc = rows_of([f"{R}/exp_featcache/_merged4_fc_vmme_nm.csv"], uu)
        return dict(uu=uu, main=main, base=None, bucket=None, fc=fc, rungs=["cap_r1"],
                    bm_main=bpp_map(f"{R}/u_vmme/results.csv"), bm_base=bpp_map(f"{R}/u_vmme/results.csv"),
                    dcvc=[], hevc_rows=main)
    if name == "lvb":
        main = rows_of([f"{R}/u_lvb/stratified_u{MAIN}_off[0-3].csv"])
        uu = {r["uuid"] for r in main}
        fc = rows_of([f"{R}/exp_featcache/_merged4_fc_lvb.csv"], uu)
        return dict(uu=uu, main=main, base=None, bucket=None, fc=fc, rungs=["cap_r1_lamb025", "cap_r1"],
                    bm_main=bpp_map(f"{R}/u_lvb/results.csv"), bm_base=bpp_map(f"{R}/u_lvb/results.csv"),
                    dcvc=[], hevc_rows=main)
    raise ValueError(name)


def baseline_pv(spec, iface, rate):
    """per-video dict for a baseline family: from cells_lib pool phases (gate1) or from the main harvest rows."""
    if spec["base"] is not None:
        return flatten_phases(arm_rows(spec["base"], iface, rate, bucket=spec["bucket"]))
    return per_video(spec["hevc_rows"], iface, rate)


FAM_LABEL = {"hevc": "HEVC", "vvc": "VVC", "dcvc": "DCVC-RT", "featcache": "feature cache"}


def boot_multiplier(ours_pv, b_ours, cells, reps, seed=7):
    """Paired video-cluster bootstrap of the rate multiplier reach(family front, ours acc) / ours bpp.

    cells: [(bpp, label, per_video_dict)] of one baseline family. Each resample draws videos with replacement,
    recomputes ours' accuracy and every cell's accuracy on the SAME draw, rebuilds the accuracy-monotone front
    and re-interpolates. Cell bpp stays at its full-sample mean. Returns (point, lo, hi, never_frac)."""
    import numpy as np
    vids = sorted(ours_pv)
    V = len(vids)
    os_ = np.array([sum(ours_pv[u]) for u in vids], float); on = np.array([len(ours_pv[u]) for u in vids], float)
    S = np.array([[sum(pv.get(u, [])) for u in vids] for _, _, pv in cells], float)
    N = np.array([[len(pv.get(u, [])) for u in vids] for _, _, pv in cells], float)
    bpps = [c[0] for c in cells]; labels = [c[1] for c in cells]

    def mult(w):
        oa = (w @ os_) / (w @ on)
        ca = (S @ w) / np.maximum(N @ w, 1)
        fr = front([(bpps[i], ca[i], labels[i]) for i in range(len(cells)) if (N[i] @ w) > 0])
        r = reach(fr, oa)
        return float("inf") if r is None else r / b_ours

    point = mult(np.ones(V))
    C = np.random.default_rng(seed).multinomial(V, [1.0 / V] * V, size=reps).astype(float)
    ms = sorted(mult(C[k]) for k in range(reps))
    lo, hi = ms[int(0.025 * reps)], ms[int(0.975 * reps) - 1]
    never = sum(1 for m in ms if m == float("inf")) / reps
    return point, lo, hi, never


def fmt_mult(m):
    if m is None:
        return "—"
    point, lo, hi, never = m
    p = "never" if point == float("inf") else f"x{point:.1f}"
    l = "never" if lo == float("inf") else f"{lo:.1f}"
    h = ">max" if hi == float("inf") else f"{hi:.1f}"
    return f"{p} [{l}, {h}]"


def build_pool(name, reps, out):
    sp = pool_spec(name)
    uu = sp["uu"]
    rows_t1, rd, forest = [], [], []
    orc = per_video(sp["main"], "oracle", "NA")
    o = cell_stats(orc, reps)
    oracle_acc = o["acc"]
    # ours main configuration
    ours_cells = []
    for rung in sp["rungs"]:
        pv = per_video(sp["main"], "ours", rung + MAIN)
        st = cell_stats(pv, reps)
        if not st:
            continue
        b = mean_bpp(sp["bm_main"], "ours", rung + MAIN, uu)
        ours_cells.append((rung, st, b, paired(pv, orc, reps), pv))
        rd.append(["ours_main", rung, b, st["acc"], st["lo"], st["hi"]])
    if sp["base"] is not None:
        for rung in sp["rungs"]:
            pv = flatten_phases(arm_rows(sp["base"], "ours", rung, bucket=sp["bucket"]))
            st = cell_stats(pv, reps)
            if st:
                rd.append(["ours_pervideo", rung, mean_bpp(sp["bm_base"], "ours", rung, uu), st["acc"], st["lo"], st["hi"]])
    # baseline families: cells = [(bpp, label, per_video)]
    fams = [("pixel", HEVC, "hevc")] + ([("vvc", VVC, "vvc"), ("dcvc", sp["dcvc"], "dcvc")] if sp["base"] is not None else [])
    fam_cells, base_rows = collections.OrderedDict(), []
    for iface, rates, tag in fams:
        cells = []
        for rt in rates:
            pv = baseline_pv(sp, iface, rt)
            st = cell_stats(pv, reps)
            if not st:
                continue
            b = mean_bpp(sp["bm_base"], iface, rt, uu)
            if b != b and tag == "hevc":
                b = mean_bpp(bpp_map(f"{R}/gate1_egos/results.csv"), iface, rt, uu)
            if b != b:
                continue
            cells.append((b, rt, pv)); rd.append([tag, rt, b, st["acc"], st["lo"], st["hi"]])
            base_rows.append([tag, rt, fmt(st["acc"]), f"[{fmt(st['lo'])},{fmt(st['hi'])}]", st["videos"], st["n"], fmt(b, 4), "—", "—", "—"])
        fam_cells[tag] = cells
    fc_cells = []
    for rate in sorted({r["rate"] for r in sp["fc"] if r.get("interface") == "featcache"}):
        pv = per_video(sp["fc"], "featcache", rate)
        st = cell_stats(pv, reps)
        bs = [float(r["bpp"]) for r in sp["fc"] if r.get("interface") == "featcache" and r["rate"] == rate]
        b = sum(bs) / len(bs)
        fc_cells.append((b, rate, pv)); rd.append(["featcache", rate, b, st["acc"], st["lo"], st["hi"]])
    fam_cells["featcache"] = fc_cells
    fc_front = front([(b, cell_stats(pv, 1)["acc"], l) for b, l, pv in fc_cells])
    # ours rows: vs oracle (paired), rate multipliers with paired bootstrap CI, and the paired forest
    ours_rows = []
    for rung, st, b, pd, pv in ours_cells:
        mh = boot_multiplier(pv, b, fam_cells["hevc"], reps) if fam_cells.get("hevc") else None
        mf = boot_multiplier(pv, b, fc_cells, reps) if fc_cells else None
        ours_rows.append(["ours", rung, fmt(st["acc"]), f"[{fmt(st['lo'])},{fmt(st['hi'])}]", st["videos"], st["n"], fmt(b, 4),
                          f"{pd['delta']:+.3f} [{pd['lo']:+.3f},{pd['hi']:+.3f}] {pd['tost']}" if pd else "—",
                          fmt_mult(mh), fmt_mult(mf)])
        for tag, cells in fam_cells.items():
            pool_cells = cells if tag != "featcache" else [c for c in cells if any(c[1] == f[2] for f in fc_front)]
            if not pool_cells:
                continue
            cb, cl, cpv = min(pool_cells, key=lambda c: abs(math.log(c[0]) - math.log(b)))   # nearest-rate cell
            d = paired(pv, cpv, reps)
            if d:
                forest.append([name, rung, round(b, 4), FAM_LABEL[tag], cl, round(cb, 4), round(d["delta"], 4), round(d["lo"], 4), round(d["hi"], 4), d["videos"]])
    rows_t1 = [["oracle", "—", fmt(o["acc"]), f"[{fmt(o['lo'])},{fmt(o['hi'])}]", o["videos"], o["n"], "—", "—", "—", "—"]] + ours_rows + base_rows
    write_table(f"{out}/T1_main_{name}", ["family", "rung", "acc", "ci95", "videos", "questions", "bpp", "delta_vs_oracle_paired",
                                         "HEVC_rate_multiplier_[95%CI]", "featcache_rate_multiplier_[95%CI]"], rows_t1)
    write_table(f"{out}/T2_featcache_{name}", ["cell", "acc", "bpp", "on_front"],
                [[l, fmt(cell_stats(pv, 1)["acc"]), fmt(b, 4), "yes" if any(l == f[2] for f in fc_front) else ""] for b, l, pv in sorted(fc_cells)])
    write_table(f"{out}/T7_paired_{name}", ["pool", "ours_rung", "ours_bpp", "baseline", "baseline_cell", "baseline_bpp",
                                           "delta_acc", "lo95", "hi95", "videos"], forest)
    with open(f"{out}/F1_rd_{name}.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["family", "rung", "bpp", "acc", "lo", "hi"]); w.writerows(rd)
    plot_rd(name, rd, oracle_acc, out)
    plot_forest(name, forest, out)
    return rows_t1


def _plt():
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        return plt
    except Exception:
        return None


def plot_rd(name, rd, oracle_acc, out):
    """RD curves without error bars (codec convention); a light 95% band on ours only. CIs live in T1/T7."""
    plt = _plt()
    if plt is None:
        return
    fams = collections.OrderedDict()
    for fam, rung, b, a, lo, hi in rd:
        if b == b:
            fams.setdefault(fam, []).append((b, a, lo, hi))
    plt.figure(figsize=(5.2, 3.6))
    style = {"ours_main": ("o-", "C3", "ours"), "ours_pervideo": ("o--", "C1", "ours, per-video adapter (uncounted)"),
             "hevc": ("s-", "C0", "HEVC"), "vvc": ("^-", "C2", "VVC"), "dcvc": ("v-", "C4", "DCVC-RT")}
    for fam, pts in fams.items():
        pts.sort(); xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        if fam == "featcache":
            plt.plot(xs, ys, "x", color="C7", alpha=.35, ms=4, label="feature cache (all cells)")
            fr = front([(b, a, "") for b, a, _, _ in pts])
            plt.plot([f[0] for f in fr], [f[1] for f in fr], "-", color="C7", lw=1.5, label="feature cache (front)")
            continue
        mk, c, lab = style.get(fam, ("d-", "C5", fam))
        if fam == "ours_main":
            plt.fill_between(xs, [p[2] for p in pts], [p[3] for p in pts], color=c, alpha=.10, lw=0)
        plt.plot(xs, ys, mk, color=c, lw=1.8 if fam == "ours_main" else 1.2, ms=4, label=lab)
    plt.axhline(oracle_acc, color="k", ls=":", lw=1, label=f"uncompressed ({oracle_acc:.3f})")
    plt.xscale("log"); plt.xlabel("bpp"); plt.ylabel("accuracy (4-phase mean)")
    plt.title(name); plt.legend(fontsize=6, loc="lower right"); plt.grid(alpha=.3); plt.tight_layout()
    plt.savefig(f"{out}/F1_rd_{name}.png", dpi=200); plt.close()


def plot_forest(name, forest, out):
    """Paired differences ours - baseline at the nearest-rate baseline cell, 95% video-cluster bootstrap CI."""
    plt = _plt()
    if plt is None or not forest:
        return
    rows = list(reversed(forest))
    fig, ax = plt.subplots(figsize=(5.2, 0.28 * len(rows) + 0.9))
    for i, r in enumerate(rows):
        d, lo, hi = r[6], r[7], r[8]
        c = "C3" if lo > 0 else ("C0" if hi < 0 else "0.45")
        ax.plot([lo, hi], [i, i], "-", color=c, lw=1.6); ax.plot([d], [i], "o", color=c, ms=4)
    ax.axvline(0, color="k", lw=.8)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([f"{r[1].replace('cap_r1_', '').replace('cap_r1', 'r1')} @{r[2]:.3f}  vs {r[3]} {r[4]} @{r[5]:.3f}" for r in rows], fontsize=6)
    ax.set_xlabel("accuracy difference, ours - baseline (paired, 95% CI)", fontsize=7)
    ax.set_title(name, fontsize=8); ax.grid(axis="x", alpha=.3); fig.tight_layout()
    fig.savefig(f"{out}/F2_paired_{name}.png", dpi=200); plt.close(fig)


def backbone_table(reps, out):
    uu = uuids_file("outputs/gate1_egos/common100_uuids.txt")
    rows = []
    for tag, globs, bm in (("InternVL2.5-8B", [f"{R}/u_egos/stratified_u{MAIN}_off[0-3].csv"], bpp_map(f"{R}/u_egos/results.csv")),
                           ("InternVL3.5-8B", [f"{R}/ivl35_egos/stratified_u35{MAIN}_off[0-3].csv"], bpp_map(f"{R}/ivl35_egos/results.csv"))):
        rr = rows_of(globs, uu)
        orc = per_video(rr, "oracle", "NA"); o = cell_stats(orc, reps)
        pv = per_video(rr, "ours", "cap_r1" + MAIN); st = cell_stats(pv, reps); pd = paired(pv, orc, reps)
        rows.append([tag, "oracle", fmt(o["acc"]), f"[{fmt(o['lo'])},{fmt(o['hi'])}]", "—", "—"])
        rows.append([tag, "ours cap_r1", fmt(st["acc"]), f"[{fmt(st['lo'])},{fmt(st['hi'])}]", fmt(mean_bpp(bm, "ours", "cap_r1" + MAIN, uu), 4),
                     f"{fmt(pd['delta'])} [{fmt(pd['lo'])},{fmt(pd['hi'])}] {pd['tost']}"])
        hev = rr if tag.startswith("InternVL3.5") else None
        for crf in HEVC:
            pv = per_video(rr, "pixel", crf) if hev is not None else flatten_phases(arm_rows(get_pool("ego"), "pixel", crf))
            st = cell_stats(pv, reps)
            if st:
                rows.append([tag, f"HEVC {crf}", fmt(st["acc"]), f"[{fmt(st['lo'])},{fmt(st['hi'])}]", fmt(mean_bpp(bpp_map(f"{R}/gate1_egos/results.csv"), "pixel", crf, uu), 4), "—"])
    write_table(f"{out}/T5_backbone_ego", ["backbone", "arm", "acc", "ci95", "bpp", "delta_vs_oracle"], rows)


def adapter_ablation(reps, out):
    uu = uuids_file("outputs/gate1_egos/common100_uuids.txt")
    main = rows_of([f"{R}/u_egos/stratified_u{MAIN}_off[0-3].csv", f"{R}/u_egos/stratified_u{MAIN}_lamb050_off[0-3].csv"], uu)
    v1 = rows_of([f"{R}/u_egos/stratified_u_off[0-3].csv"], uu)
    base = get_pool("ego")
    bm_u = bpp_map(f"{R}/u_egos/results.csv"); bm_g = bpp_map(f"{R}/gate1_egos/results.csv")
    rows = []
    for rung in RUNGS_EGO:
        for label, pv, b in (("per-video adapter (1.73 MB uncounted)", flatten_phases(arm_rows(base, "ours", rung)), mean_bpp(bm_g, "ours", rung, uu)),
                             ("frozen universal, no delta, layer 12", per_video(v1, "ours", rung), mean_bpp(bm_u, "ours", rung, uu)),
                             ("frozen universal + FiLM 2 KB + 12/24 (main)", per_video(main, "ours", rung + MAIN), mean_bpp(bm_u, "ours", rung + MAIN, uu))):
            st = cell_stats(pv, reps)
            if st:
                rows.append([rung, label, fmt(st["acc"]), f"[{fmt(st['lo'])},{fmt(st['hi'])}]", st["videos"], fmt(b, 4)])
    write_table(f"{out}/T6_adapter_ablation_ego", ["rung", "configuration", "acc", "ci95", "videos", "bpp"], rows)


def alignment_depth(reps, out):
    base = get_pool("vmme"); uu = base.videos
    g = f"{R}/gate1_vmme"; bm = bpp_map(f"{g}/results.csv")
    rows = []
    for bucket in (None, "temporal"):
        for label, globs, iface, rate in (("mid-layer N=12 (per-video, cap_r1)", None, "ours", "cap_r1"),
                                          ("final-layer N=24 cap_r1", [f"{g}/stratified_final_cap_r1_off[0-3].csv"], "final", "cap_r1"),
                                          ("final-layer N=24 lamb025", [f"{g}/stratified_final_cap_r1_lamb025_off[0-3].csv"], "final", "cap_r1_lamb025"),
                                          ("multi-layer (per-video, cap_r1)", [f"{g}/stratified_ours_cap_r1_nmulti_off[0-3].csv"], "ours", "cap_r1_nmulti")):
            pv = flatten_phases(arm_rows(base, iface, rate, bucket=bucket)) if globs is None else per_video(rows_of(globs, uu, bucket), iface, rate)
            st = cell_stats(pv, reps)
            if st:
                rows.append([bucket or "all", label, fmt(st["acc"]), f"[{fmt(st['lo'])},{fmt(st['hi'])}]", st["videos"], fmt(mean_bpp(bm, iface, rate, uu), 4)])
    write_table(f"{out}/T4_alignment_depth_vmme", ["bucket", "configuration", "acc", "ci95", "videos", "bpp"], rows)


def controls_table(reps, out):
    """T3 (E-13): controls on the MAIN configuration, 4 phases, paired against the unmodified counterpart."""
    rows = []
    for pool, root, gate in (("ego", f"{R}/u_egos", f"{R}/gate1_egos"), ("vmme", f"{R}/u_vmme", f"{R}/gate1_vmme"),
                             ("vmme_temporal", f"{R}/u_vmme", f"{R}/gate1_vmme")):
        sp = pool_spec(pool); uu = sp["uu"]; bucket = sp["bucket"]
        main = sp["main"]
        ctl = lambda k: rows_of([f"{root}/stratified_e13_{k}_off[0-3].csv"], uu, bucket)
        ours = per_video(main, "ours", "cap_r1" + MAIN); orc = per_video(main, "oracle", "NA")
        bm_p = bpp_map(f"{gate}/results.csv"); b_ours = mean_bpp(sp["bm_main"], "ours", "cap_r1" + MAIN, uu)
        sh, mm, p64, p16, pc = ctl("shuffle"), ctl("mismatch"), ctl("pool64"), ctl("pool16"), ctl("pixcache")
        arms = [("ours (256 tok/frame)", ours, None, b_ours),
                ("ours, frames shuffled", per_video(sh, "ours_shuffle", "cap_r1" + MAIN), ours, b_ours),
                ("ours, other video's cache", per_video(mm, "ours_mismatch", "cap_r1" + MAIN), ours, b_ours),
                ("ours pooled to 64 tok/frame", per_video(p64, "ours", "cap_r1" + MAIN), ours, b_ours),
                ("ours pooled to 16 tok/frame", per_video(p16, "ours", "cap_r1" + MAIN), ours, b_ours),
                ("uncompressed (256 tok/frame)", orc, None, float("nan")),
                ("uncompressed, frames shuffled", per_video(sh, "oracle_shuffle", "NA"), orc, float("nan")),
                ("uncompressed, other video", per_video(mm, "oracle_mismatch", "NA"), orc, float("nan")),
                ("uncompressed cache pooled 64", per_video(pc, "oraclecache", "oracle_p64"), orc, float("nan")),
                ("uncompressed cache pooled 16", per_video(pc, "oraclecache", "oracle_p16"), orc, float("nan"))]
        for crf in ("crf33", "crf40", "crf45"):
            full = per_video(pc, "pixel", crf); b = mean_bpp(bm_p, "pixel", crf, uu)
            arms += [(f"HEVC {crf} (256 tok/frame)", full, None, b),
                     (f"HEVC {crf} cache pooled 64", per_video(pc, "pixelcache", crf + "_p64"), full, b),
                     (f"HEVC {crf} cache pooled 16", per_video(pc, "pixelcache", crf + "_p16"), full, b)]
        for label, pv, ref, b in arms:
            st = cell_stats(pv, reps)
            if not st:
                continue
            d = paired(pv, ref, reps) if ref is not None else None
            rows.append([pool, label, fmt(st["acc"]), f"[{fmt(st['lo'])},{fmt(st['hi'])}]", st["videos"], fmt(b, 4),
                         f"{d['delta']:+.3f} [{d['lo']:+.3f},{d['hi']:+.3f}]" if d else "—"])
    write_table(f"{out}/T3_controls", ["pool", "arm", "acc", "ci95", "videos", "bpp", "delta_vs_unmodified_paired"], rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=f"{R}/paper_tables")
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--pools", nargs="+", default=["ego", "vmme", "vmme_temporal", "vmme_nonmotion", "lvb"])
    ap.add_argument("--only", default=None, help="run just one extra table: controls|ablation|backbone|depth")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    if args.only:
        {"controls": controls_table, "ablation": adapter_ablation, "backbone": backbone_table, "depth": alignment_depth}[args.only](args.reps, args.out)
        print("written", args.only); return
    for p in args.pools:
        rows = build_pool(p, args.reps, args.out)
        print(f"== {p}"); [print("  ", r) for r in rows if r[0] in ("oracle", "ours")]
    backbone_table(args.reps, args.out); adapter_ablation(args.reps, args.out); alignment_depth(args.reps, args.out)
    controls_table(args.reps, args.out)
    print("written to", args.out)


if __name__ == "__main__":
    main()
