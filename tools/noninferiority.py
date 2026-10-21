#!/usr/bin/env python3
"""noninferiority.py -- paired accuracy difference with a pre-specified margin.

Replaces "n.s." statements (AI review, weakness 4): reports the paired difference
A - B over matched questions, a two-sided 95% bootstrap CI, and a non-inferiority
verdict at margin delta (A is non-inferior to B if the one-sided 95% lower bound of
A - B is above -delta), plus the exact McNemar p-value for the two-sided difference.

Bootstrap resamples whole videos by default (--cluster video), i.e. questions of one
video move together, which is the conservative choice for multi-question Video-MME
videos; --cluster question reproduces the per-question bootstrap used in the AAAI
submission.

Examples
  python tools/noninferiority.py --dataset vmme --a ours:cap_r1 --b oracle:NA --bucket temporal
  python tools/noninferiority.py --dataset ego  --a ours:cap_r1_lamb150 --b oracle:NA --delta 0.05
"""
from __future__ import annotations

import argparse
import collections
import math
import random

from cells_lib import get_pool, paired_deltas


def mcnemar_p(b: int, c: int) -> float:
    """Exact two-sided McNemar on the discordant counts (A right/B wrong = b, A wrong/B right = c)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def bootstrap(deltas: list[tuple[str, float]], cluster: str, nboot: int, seed: int):
    rng = random.Random(seed)
    if cluster == "video":
        by = collections.defaultdict(list)
        for u, d in deltas:
            by[u].append(d)
        units = list(by.values())
    else:
        units = [[d] for _, d in deltas]
    means = []
    for _ in range(nboot):
        picked = rng.choices(units, k=len(units))
        flat = [d for grp in picked for d in grp]
        means.append(sum(flat) / len(flat))
    means.sort()
    q = lambda p: means[min(len(means) - 1, max(0, int(p * len(means))))]
    return q(0.025), q(0.975), q(0.05), q(0.95)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=["vmme", "ego"], required=True)
    ap.add_argument("--a", required=True, help="interface:rate, e.g. ours:cap_r1")
    ap.add_argument("--b", required=True, help="interface:rate, e.g. oracle:NA")
    ap.add_argument("--bucket", default=None, help="vmme bucket: temporal|detail|gist (default all)")
    ap.add_argument("--delta", type=float, default=0.05, help="non-inferiority margin on accuracy")
    ap.add_argument("--cluster", choices=["video", "question"], default="video")
    ap.add_argument("--nboot", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    pool = get_pool(args.dataset)
    a = tuple(args.a.split(":", 1))
    b = tuple(args.b.split(":", 1))
    trip = paired_deltas(pool, a, b, bucket=args.bucket)
    if not trip:
        raise SystemExit("no matched questions; check interface/rate names")
    deltas = [(u, x - y) for u, x, y in trip]
    n = len(deltas)
    nvid = len({u for u, _ in deltas})
    acc_a = sum(x for _, x, _ in trip) / n
    acc_b = sum(y for _, _, y in trip) / n
    diff = acc_a - acc_b
    lo2, hi2, lo1, hi1 = bootstrap(deltas, args.cluster, args.nboot, args.seed)
    disc_b = sum(1 for _, x, y in trip if x > y)
    disc_c = sum(1 for _, x, y in trip if x < y)
    p = mcnemar_p(disc_b, disc_c)
    noninf = lo1 > -args.delta
    equiv = noninf and hi1 < args.delta

    print(f"dataset={args.dataset} bucket={args.bucket or 'all'}  A={args.a}  B={args.b}")
    print(f"matched questions n={n} over {nvid} videos (phases pooled); cluster bootstrap by {args.cluster}, {args.nboot} resamples")
    print(f"acc A={acc_a:.3f}  acc B={acc_b:.3f}  A-B={diff:+.3f}  95% CI [{lo2:+.3f}, {hi2:+.3f}]")
    print(f"discordant: A right/B wrong={disc_b}  A wrong/B right={disc_c}  exact McNemar p={p:.3f}")
    print(f"one-sided 95% lower bound of A-B = {lo1:+.3f}  (margin -delta = {-args.delta:+.3f})")
    print(f"NON-INFERIOR at delta={args.delta}: {'YES' if noninf else 'NO'}"
          f"   | EQUIVALENT (TOST, both bounds within +/-delta): {'YES' if equiv else 'NO'}")
    print("paper phrasing: " + (
        f"A is non-inferior to B within {args.delta:.2f} (paired difference {diff:+.3f}, 95% CI [{lo2:+.2f}, {hi2:+.2f}], n={n})."
        if noninf else
        f"non-inferiority within {args.delta:.2f} is NOT established (paired difference {diff:+.3f}, 95% CI [{lo2:+.2f}, {hi2:+.2f}], n={n})."))


if __name__ == "__main__":
    main()
