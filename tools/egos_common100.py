#!/usr/bin/env python3
"""EgoSchema common-100 aligned comparison.

Computes, from gate1_egos/results.csv (1 question per video, so video-level
== question-level):
  1. the common uuid set across ours(cap_r1) / oracle / pixel(all CRFs) /
     vvc(all QPs) / dcvc(all Qs);
  2. per interface x rate mean bpp + accuracy on the common set;
  3. paired accuracy differences (ours-oracle, ours-HEVC@lowest-bpp CRF,
     ours-VVC@nearest-matched-bpp, ours-DCVC@nearest-matched-bpp) with
     paired video-level bootstrap 95% CIs (B=5000, seed=7);
  4. the same ours-vs-oracle / ours-vs-HEVC stats on the full 129-video set;
  5. writes the common-100 aggregate table to
     gate1_egos/egos_common100_agg.csv.

Duplicate (interface, rate, uuid) rows in results.csv are exact repeats and
are deduplicated (first kept).
"""

import numpy as np
import pandas as pd

RESULTS = "/mnt/nas/xinyizheng/vidtok_out/gate1_egos/results.csv"
OUT_AGG = "/mnt/nas/xinyizheng/vidtok_out/gate1_egos/egos_common100_agg.csv"
B = 5000
SEED = 7


def load():
    df = pd.read_csv(RESULTS)
    df["correct"] = df["correct"].astype(str).str.lower().isin(("true", "1"))
    df["rate"] = df["rate"].fillna("oracle")
    # duplicates are exact repeats (verified): keep first
    df = df.drop_duplicates(["interface", "rate", "uuid"]).copy()
    return df


def cond(df, interface, rate):
    """Per-uuid Series of accuracy (0/1) for one interface x rate."""
    sub = df[(df.interface == interface) & (df.rate == rate)]
    return sub.set_index("uuid")


def boot_mean(acc, rng):
    """Bootstrap CI of the mean of a per-video accuracy vector."""
    n = len(acc)
    idx = rng.integers(0, n, size=(B, n))
    means = acc[idx].mean(axis=1)
    return means.mean(), np.percentile(means, 2.5), np.percentile(means, 97.5)


def paired(df, a_if, a_rate, b_if, b_rate, uuids=None):
    """Paired diff (a-b) on common uuids with paired bootstrap CI."""
    a = cond(df, a_if, a_rate)
    b = cond(df, b_if, b_rate)
    common = a.index.intersection(b.index)
    if uuids is not None:
        common = common.intersection(pd.Index(uuids))
    common = sorted(common)
    d = (a.loc[common, "correct"].astype(float)
         - b.loc[common, "correct"].astype(float)).values
    rng = np.random.default_rng(SEED)
    np.random.seed(SEED)
    mean, lo, hi = boot_mean(d, np.random.default_rng(SEED))
    return dict(
        n=len(common),
        acc_a=a.loc[common, "correct"].mean(),
        acc_b=b.loc[common, "correct"].mean(),
        diff=d.mean(),
        boot_mean=mean, ci_lo=lo, ci_hi=hi,
    )


def main():
    df = load()

    conds = sorted(df.groupby(["interface", "rate"]).groups.keys())
    uuid_sets = {c: set(df[(df.interface == c[0]) & (df.rate == c[1])].uuid)
                 for c in conds}
    common = set.intersection(*uuid_sets.values())
    print(f"conditions: {len(conds)}; common uuid set size: {len(common)}")
    for c in conds:
        assert common <= uuid_sets[c]

    # (2) per-condition aggregate on common set
    rows = []
    for iface, rate in conds:
        sub = df[(df.interface == iface) & (df.rate == rate)
                 & df.uuid.isin(common)]
        acc = sub.correct.astype(float).values
        m, lo, hi = boot_mean(acc, np.random.default_rng(SEED))
        rows.append(dict(interface=iface, rate=rate, n_videos=len(sub),
                         mean_bpp=sub.bpp.mean(), accuracy=acc.mean(),
                         acc_boot_mean=m, acc_ci_lo=lo, acc_ci_hi=hi))
    agg = pd.DataFrame(rows).sort_values(["interface", "mean_bpp"])
    agg.to_csv(OUT_AGG, index=False)
    print("\n=== common-100 aggregate (written to", OUT_AGG, ") ===")
    print(agg.to_string(index=False, float_format=lambda x: f"{x:.4f}"))

    ours_bpp = agg[(agg.interface == "ours")].mean_bpp.iloc[0]

    # HEVC lowest-bpp crf; VVC/DCVC nearest-matched bpp to ours
    pix = agg[agg.interface == "pixel"]
    hevc_rate = pix.loc[pix.mean_bpp.idxmin(), "rate"]
    vvc = agg[agg.interface == "vvc"]
    vvc_rate = vvc.loc[(vvc.mean_bpp - ours_bpp).abs().idxmin(), "rate"]
    dcvc = agg[agg.interface == "dcvc"]
    dcvc_rate = dcvc.loc[(dcvc.mean_bpp - ours_bpp).abs().idxmin(), "rate"]
    print(f"\nours mean bpp={ours_bpp:.4f}; HEVC lowest-bpp={hevc_rate}; "
          f"VVC nearest={vvc_rate}; DCVC nearest={dcvc_rate}")

    # (3) paired stats on common-100
    print("\n=== paired diffs on common set ===")
    pairs = [("ours-oracle", "oracle", "oracle"),
             (f"ours-HEVC({hevc_rate})", "pixel", hevc_rate),
             (f"ours-VVC({vvc_rate})", "vvc", vvc_rate),
             (f"ours-DCVC({dcvc_rate})", "dcvc", dcvc_rate)]
    for name, b_if, b_rate in pairs:
        r = paired(df, "ours", "cap_r1", b_if, b_rate, uuids=common)
        print(f"{name}: n={r['n']} acc_ours={r['acc_a']:.4f} "
              f"acc_base={r['acc_b']:.4f} diff={r['diff']:+.4f} "
              f"CI95=[{r['ci_lo']:+.4f},{r['ci_hi']:+.4f}]")

    # (4) full-129 where both sides exist
    print("\n=== paired diffs on full overlap (129) ===")
    for name, b_if, b_rate in [("ours-oracle", "oracle", "oracle"),
                               (f"ours-HEVC({hevc_rate})", "pixel", hevc_rate)]:
        r = paired(df, "ours", "cap_r1", b_if, b_rate)
        print(f"{name}: n={r['n']} acc_ours={r['acc_a']:.4f} "
              f"acc_base={r['acc_b']:.4f} diff={r['diff']:+.4f} "
              f"CI95=[{r['ci_lo']:+.4f},{r['ci_hi']:+.4f}]")


if __name__ == "__main__":
    main()
