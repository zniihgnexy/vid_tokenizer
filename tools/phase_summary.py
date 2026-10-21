#!/usr/bin/env python3
"""Summarise harvest CSVs (one or more phases) by (interface, rate): n, accuracy, mean bpp.

  python tools/phase_summary.py "<glob>" [--bucket temporal] [--label TEXT]

Rows are pooled across all matching files (plain row mean = the 4-phase protocol);
bpp is the mean of graded rows that carry a numeric bpp.
"""
import argparse, collections, csv, glob, math


def summarise(pattern: str, bucket: str | None = None, uuids: set | None = None) -> tuple[int, dict]:
    agg = collections.defaultdict(lambda: [0, 0, 0.0, 0])
    files = sorted(glob.glob(pattern))
    for f in files:
        for r in csv.DictReader(open(f)):
            if bucket and r.get("bucket") != bucket:
                continue
            if uuids is not None and r.get("uuid") not in uuids:
                continue
            a = agg[(r["interface"], r["rate"])]
            a[0] += 1
            a[1] += r["correct"] == "True"
            try:
                a[2] += float(r["bpp"]); a[3] += 1
            except (TypeError, ValueError):
                pass
    out = {k: {"n": n, "acc": c / n, "bpp": (b / nb) if nb else math.nan} for k, (n, c, b, nb) in agg.items()}
    return len(files), out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pattern")
    ap.add_argument("--bucket", default=None)
    ap.add_argument("--label", default="")
    ap.add_argument("--uuids", default=None, help="file with one video id per line: keep only these")
    args = ap.parse_args()
    uu = {l.strip() for l in open(args.uuids) if l.strip()} if args.uuids else None
    nfiles, cells = summarise(args.pattern, args.bucket, uu)
    tag = f" bucket={args.bucket}" if args.bucket else ""
    print(f"--- {args.label or args.pattern} ({nfiles} files{tag})")
    for (iface, rate), v in sorted(cells.items(), key=lambda kv: (kv[0][0], kv[1]["bpp"] if not math.isnan(kv[1]["bpp"]) else 1e9)):
        print(f"  {iface:9s} {rate:30s} n={v['n']:4d} acc={v['acc']:.3f} bpp={v['bpp']:.4f}")


if __name__ == "__main__":
    main()
