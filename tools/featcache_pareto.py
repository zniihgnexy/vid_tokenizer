#!/usr/bin/env python3
"""E-04 Pareto report: feature-cache baseline cells vs ours (main config) on the same harvest protocol.

  python tools/featcache_pareto.py --fc R/exp_featcache/stratified_fc_egos_off0.csv \
      --ours R/u_egos/stratified_u_n1224_dfilm_off0.csv [--bucket temporal] [--top 5]

Prints (markdown): every featcache cell (n, acc, bpp), the Pareto front, ours rungs + oracle, and for
each ours rung the cheapest featcache bpp that reaches its accuracy (linear interpolation on the front)
-> the G-C multiplier. Also prints a space-separated PARETO_SPECS line for `e04_featcache_baselines.sh pareto`.
"""
import argparse, csv, collections, math


def load(path, bucket=None, uuids=None):
    rows = list(csv.DictReader(open(path)))
    if bucket:
        rows = [r for r in rows if r["bucket"] == bucket]
    if uuids is not None:
        rows = [r for r in rows if r["uuid"] in uuids]
    return rows


def cells(rows, iface):
    agg = collections.defaultdict(lambda: [0, 0, 0.0, 0])
    for r in rows:
        if r["interface"] != iface:
            continue
        a = agg[r["rate"]]
        a[0] += 1; a[1] += (r["correct"] == "True")
        try:
            a[2] += float(r["bpp"]); a[3] += 1
        except ValueError:
            pass
    out = {}
    for k, (n, c, b, nb) in agg.items():
        out[k] = {"n": n, "acc": c / n, "bpp": (b / nb) if nb else float("nan")}
    return out


def pareto(cl):
    pts = sorted(((v["bpp"], v["acc"], k) for k, v in cl.items() if not math.isnan(v["bpp"])))
    front, best = [], -1.0
    for bpp, acc, k in pts:
        if acc > best:
            front.append((bpp, acc, k)); best = acc
    return front


def reach(front, target):
    """Cheapest bpp on the (monotone) front reaching accuracy >= target; log-bpp interpolation between points."""
    prev = None
    for bpp, acc, _ in front:
        if acc >= target:
            if prev is None or prev[1] == acc:
                return bpp
            pb, pa = prev
            return math.exp(math.log(pb) + (math.log(bpp) - math.log(pb)) * (target - pa) / (acc - pa))
        prev = (bpp, acc)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fc", required=True)
    ap.add_argument("--ours", required=True)
    ap.add_argument("--ours-iface", default="ours")
    ap.add_argument("--bucket", default=None)
    ap.add_argument("--top", type=int, default=5, help="Pareto cells to suggest for the 4-phase run")
    ap.add_argument("--uuids", default=None, help="file with one video id per line: keep only these")
    args = ap.parse_args()
    uu = {l.strip() for l in open(args.uuids) if l.strip()} if args.uuids else None

    fc = cells(load(args.fc, args.bucket, uu), "featcache")
    ours_rows = load(args.ours, args.bucket, uu)
    ours = cells(ours_rows, args.ours_iface)
    orc = cells(ours_rows, "oracle")
    oracle_acc = next(iter(orc.values()))["acc"] if orc else float("nan")

    print(f"### featcache cells ({len(fc)}; bucket={args.bucket or 'all'})\n")
    print("| cell | n | acc | bpp |\n|---|---|---|---|")
    for k, v in sorted(fc.items(), key=lambda kv: kv[1]["bpp"]):
        print(f"| {k} | {v['n']} | {v['acc']:.3f} | {v['bpp']:.4f} |")
    front = pareto(fc)
    print(f"\n### Pareto front ({len(front)})\n")
    print("| cell | acc | bpp |\n|---|---|---|")
    for bpp, acc, k in front:
        print(f"| {k} | {acc:.3f} | {bpp:.4f} |")
    print(f"\n### ours ({args.ours_iface}) and reach-to-match (oracle acc {oracle_acc:.3f})\n")
    print("| ours rung | n | acc | bpp | featcache bpp to reach | multiplier |\n|---|---|---|---|---|---|")
    for k, v in sorted(ours.items(), key=lambda kv: kv[1]["bpp"]):
        rb = reach(front, v["acc"])
        rs = f"{rb:.4f}" if rb is not None else "never"
        mult = f"x{rb / v['bpp']:.1f}" if rb is not None and v["bpp"] > 0 else "-"
        print(f"| {k} | {v['n']} | {v['acc']:.3f} | {v['bpp']:.4f} | {rs} | {mult} |")
    # suggestion: front cells closest (in log bpp) to the ours rungs, up to --top, plus the best-acc front cell
    want = sorted({math.log(v["bpp"]) for v in ours.values() if v["bpp"] > 0})
    chosen = []
    for lw in want:
        best = min(front, key=lambda p: abs(math.log(p[0]) - lw)) if front else None
        if best and best[2] not in chosen:
            chosen.append(best[2])
    if front and front[-1][2] not in chosen:
        chosen.append(front[-1][2])
    print("\nPARETO_SPECS=\"" + " ".join(chosen[: args.top]) + "\"")


if __name__ == "__main__":
    main()
