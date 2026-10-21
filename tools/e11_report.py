#!/usr/bin/env python3
"""E-11 report: main configuration (frozen universal adapter + FiLM delta + 12/24 alignment, bits
include the delta) vs the per-video-adapter runs of the AAAI version, paired per question across
the 4-phase harvests, with video-cluster bootstrap CIs; plus the gap to the oracle with a TOST
non-inferiority read-out (delta = 0.05).

  python tools/e11_report.py --pool ego|vmme [--bucket temporal] [--reps 2000]

Per-video rows come from tools/cells_lib.py (the paper's canonical pools); main-config rows from
R/u_egos|u_vmme/stratified_u_n1224_dfilm_off{0..3}.csv. Within a phase file, rows of one
(interface, rate, uuid) are in manifest question order, so the k-th rows pair.
"""
import argparse, collections, random, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from cells_lib import R, get_pool, arm_rows, merge, bpp_map, ok, graded, Pool

RUNGS = {"ego": ["cap_r1_lamb006", "cap_r1_lamb025", "cap_r1", "cap_r1_lamb150"],
         "vmme": ["cap_r1_lamb006", "cap_r1_lamb025", "cap_r1"]}
MAIN_SFX = "_n1224_dfilm"
DELTA = 0.05


def main_pool(name: str, base: Pool) -> Pool:
    """Main-config harvests shaped like the per-video pool's phase list (ego: 4 phases; vmme: [off0, off1-3])."""
    root = f"{R}/u_egos" if name == "ego" else f"{R}/u_vmme"
    files = [f"{root}/stratified_u{MAIN_SFX}_off{o}.csv" for o in range(4)]
    if name == "ego":
        phases = [merge(f) for f in files]
    else:
        phases = [merge(files[0]), merge(*files[1:])]
    return Pool(name + "_main", phases, base.videos, first_row_only=False)


def paired(pa, pb):
    """[(uuid, a, b)] over matched questions in all phases."""
    out = []
    for xa, xb in zip(pa, pb):
        for u in sorted(set(xa) & set(xb)):
            for x, y in zip(xa[u], xb[u]):
                out.append((u, float(x), float(y)))
    return out


def cluster_ci(pairs, reps, seed=0):
    by = collections.defaultdict(list)
    for u, a, b in pairs:
        by[u].append(a - b)
    vids = sorted(by)
    if not vids:
        return float("nan"), (float("nan"), float("nan")), 0
    rng = random.Random(seed)
    def mean_of(sel):
        vals = [d for u in sel for d in by[u]]
        return sum(vals) / len(vals)
    point = mean_of(vids)
    boots = sorted(mean_of([vids[rng.randrange(len(vids))] for _ in vids]) for _ in range(reps))
    return point, (boots[int(0.025 * reps)], boots[int(0.975 * reps) - 1]), len(vids)


def acc_of(rows_per_phase):
    vals = [v for ph in rows_per_phase for lst in ph.values() for v in lst]
    return (sum(vals) / len(vals), len(vals)) if vals else (float("nan"), 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", choices=["ego", "vmme"], required=True)
    ap.add_argument("--bucket", default=None)
    ap.add_argument("--reps", type=int, default=2000)
    args = ap.parse_args()
    base = get_pool(args.pool)
    mainp = main_pool(args.pool, base)
    root = f"{R}/u_egos" if args.pool == "ego" else f"{R}/u_vmme"
    bm_main = bpp_map(f"{root}/results.csv")
    bm_pv = bpp_map(f"{R}/gate1_egos/results.csv" if args.pool == "ego" else f"{R}/gate1_vmme/results.csv")

    def mean_bpp(bm, iface, rate):
        v = [b for (i, r, u), b in bm.items() if i == iface and r == rate and u in base.videos]
        return sum(v) / len(v) if v else float("nan")

    orc_pv = arm_rows(base, "oracle", "NA", bucket=args.bucket)
    orc_main = arm_rows(mainp, "oracle", "NA", bucket=args.bucket)
    print(f"## E-11 {args.pool}{' bucket=' + args.bucket if args.bucket else ''}: main config vs per-video adapter "
          f"(videos in pool: {len(base.videos)}; oracle acc per-video-harvest {acc_of(orc_pv)[0]:.3f}, main-harvest {acc_of(orc_main)[0]:.3f})\n")
    print("| rung | main acc@bpp (n) | per-video acc@bpp (n) | Δ main−pv [95% cluster CI] (videos) | Δ main−oracle [CI] | TOST δ=0.05 |")
    print("|---|---|---|---|---|---|")
    for rung in RUNGS[args.pool]:
        m = arm_rows(mainp, "ours", rung + MAIN_SFX, bucket=args.bucket)
        p = arm_rows(base, "ours", rung, bucket=args.bucket)
        am, nm = acc_of(m); apv, npv = acc_of(p)
        d, (lo, hi), nv = cluster_ci(paired(m, p), args.reps)
        do, (olo, ohi), _ = cluster_ci(paired(m, orc_main), args.reps, seed=1)
        tost = "non-inferior" if olo > -DELTA and ohi < DELTA else ("inferior" if ohi < 0 else "inconclusive")
        print(f"| {rung} | {am:.3f}@{mean_bpp(bm_main, 'ours', rung + MAIN_SFX):.4f} ({nm}) | "
              f"{apv:.3f}@{mean_bpp(bm_pv, 'ours', rung):.4f} ({npv}) | {d:+.3f} [{lo:+.3f},{hi:+.3f}] ({nv}) | "
              f"{do:+.3f} [{olo:+.3f},{ohi:+.3f}] | {tost} |")


if __name__ == "__main__":
    main()
