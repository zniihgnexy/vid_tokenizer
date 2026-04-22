# Querybank-Normalized Teacher-Anchor Hubness Smoke Plan

## 1. Run Contract

- run id: `querybank_teacher_anchor_smoke_r1`
- parent idea id: `idea-e313b721`
- selected idea in `1-2` sentences:
  the next bounded experiment should keep the frozen `16`-frame teacher-anchor
  packet bundles and evaluation surface unchanged, then test whether
  querybank-normalized teacher-anchor scoring can rescue retrieval stability
  better than raw global-bank scoring without reopening training.
- user-facing objective:
  produce one rerunnable result batch that shows whether inference-time hubness
  correction is enough to stabilize the packet interface before we spend more
  effort on a heavier downstream bridge or a new training-side repair.
- baseline and comparability contract:
  - confirmed baseline remains `nvrc-local-source` / `tiny-local-teacher-pilot-r3`
  - the UVG paper-facing coding metrics stay read-only reference metrics
  - this pass is a local `16`-frame packet-interface smoke, not a UVG-comparable
    coding run
  - reuse the four frozen bundle chunks already recorded in
    `experiments/main/evals/shared_gating_query_collapse_localization_smoke_r1/summary.json`
  - no upstream retraining, exporter schema change, dataset change, or split
    change is allowed
- research question:
  can querybank-normalized teacher-anchor scoring recover better retrieval on the
  existing `16`-frame packet bundles than raw global-bank scoring while reducing
  the collapse onto anchors `0009/0010/0011`?
- null hypothesis:
  post-hoc hubness correction only reshuffles the same mistakes; the best
  corrected mode does not materially improve over raw global-bank retrieval and
  does not reduce hub concentration.
- alternative hypothesis:
  a querybank-normalized or Dynamic Inverted Softmax style score can improve
  retrieval on the same frozen bundles and spread anchor usage away from the
  `0009/0010/0011` hub cluster without retraining.
- primary metric:
  `consumer_metrics.qb_norm_teacher_anchor_to_target_feat.top1_accuracy`
- required metric keys for acceptance:
  - `consumer_metrics.raw_global_bank_to_target_feat.top1_accuracy`
  - `consumer_metrics.qb_norm_teacher_anchor_to_target_feat.top1_accuracy`
  - `consumer_metrics.dis_teacher_anchor_to_target_feat.top1_accuracy`
  - `consumer_metrics.csls_teacher_anchor_to_target_feat.top1_accuracy`
  - `diagnostics.raw_global_bank.hub_cluster_share_0009_0010_0011`
  - `diagnostics.qb_norm_teacher_anchor.hub_cluster_share_0009_0010_0011`
  - `diagnostics.raw_global_bank.unique_top1_anchor_count`
  - `diagnostics.qb_norm_teacher_anchor.unique_top1_anchor_count`
- stop condition for this bounded pass:
  one runnable smoke command, one durable result directory, one report that
  compares the four scoring modes, and one explicit route decision from the
  measured result.

## 2. Strongest Existing Evidence

- the widened packet-interface line already showed that packet-side signal still
  exists; the main failure is retrieval geometry, not missing packet content
- the current raw global-bank `16`-frame result is `top1_accuracy = 0.125`
  together with strong concentration on anchors `0009/0010/0011`
- the earlier `4`-frame packet-adapter line proved that teacher-anchor style
  retrieval can work in a bounded setting, but it does not answer the widened
  hubness failure
- the selected idea package and literature sweep both converge on lightweight
  post-hoc cross-modal normalization as the most defensible next correction

## 3. Chosen Comparison Surface

- `raw_global_bank_to_target_feat`
  - current control and failure reference
- `qb_norm_teacher_anchor_to_target_feat`
  - main route and headline comparison
- `dis_teacher_anchor_to_target_feat`
  - close sibling of QB-Norm; keep as fallback within the same smoke
- `csls_teacher_anchor_to_target_feat`
  - classical control that tests whether local scaling alone explains the gain
- `hard_shortlist_teacher_anchor_to_target_feat`
  - optional secondary control only if the first four modes leave ambiguity

## 4. Bundle And Output Contract

- input bundle surface:
  - reuse the four bundle chunks already referenced by
    `experiments/main/evals/shared_gating_query_collapse_localization_smoke_r1/summary.json`
  - chunk names:
    - `shared_gating_ego4d16f_teacher_packet_ego4d_small_bridge_16f_chunk00_smoke_r1`
    - `shared_gating_ego4d16f_teacher_packet_ego4d_small_bridge_16f_chunk01_smoke_r1`
    - `shared_gating_ego4d16f_teacher_packet_ego4d_small_bridge_16f_chunk02_smoke_r1`
    - `shared_gating_ego4d16f_teacher_packet_ego4d_small_bridge_16f_chunk03_smoke_r1`
- default output directory:
  `experiments/main/evals/querybank_teacher_anchor_smoke_r1`
- required outputs:
  - `summary.json`
  - `report.md`
  - per-mode row csv files
  - per-mode similarity matrices
  - anchor-weight csv or equivalent per-mode diagnostic export
  - concentration summary for hubs `0009/0010/0011`

## 5. Code Touchpoints

| Path | Planned change | Why this is needed |
|---|---|---|
| `experiments/main/scripts/run_teacher_anchor_packet_eval.py` | extend the existing evaluator so it can score raw, QB-Norm, DIS, and CSLS modes and emit per-mode concentration diagnostics | keep the hubness experiment close to the existing teacher-anchor code path |
| `experiments/main/scripts/run_query_collapse_localization.py` | reuse or factor helper logic for multi-chunk loading and concentration summaries if that is cleaner than duplicating it | the new smoke should stay comparable to the existing collapse diagnosis |
| `experiments/main/scripts/run_querybank_teacher_anchor_smoke.sh` | add a reproducible bounded launcher for the four-chunk smoke | make the result rerunnable from one command |
| `PLAN.md`, `CHECKLIST.md`, `plan.md`, `status.md`, `SUMMARY.md` | sync the control surface onto the active querybank-normalized line | avoid carrying stale packet-adapter assumptions into the new run |

## 6. Safe Efficiency Levers

- inference-only change on already exported packet bundles
- reuse existing bundle manifests and packet payloads instead of regenerating
  them
- keep all comparisons inside one bounded smoke so every mode sees the same
  inputs
- only widen to a heavier run if the first smoke produces a clean, interpretable
  delta

## 7. Smoke Command

- planned launcher:
  `./experiments/main/scripts/run_querybank_teacher_anchor_smoke.sh`
- launcher responsibilities:
  - pass the four `16`-frame bundle chunk directories
  - run raw, QB-Norm, DIS, and CSLS comparisons in one smoke
  - collect retrieval plus concentration diagnostics into the same output
    directory

## 8. Success And Abandonment Criteria

- success:
  - at least one corrected mode beats the raw global-bank `0.125` top-1 control
  - the winning corrected mode reduces hub-cluster share on
    `0009/0010/0011`
  - the smoke leaves a clear rerunnable report
- strong success:
  - `qb_norm_teacher_anchor_to_target_feat.top1_accuracy >= 0.25`
  - the winning mode also increases the number of unique top-1 anchors versus
    raw global-bank
- abandonment or downgrade:
  - all corrected modes tie or underperform the raw control
  - hub concentration stays essentially unchanged even when top-1 moves
  - only ad hoc shortlist pruning helps, which would point away from the current
    single-bank normalization claim

## 9. Why This Route Dominates The Alternatives

- it keeps the frozen packet-interface story intact and tests the lightest
  plausible correction first
- it is more directly aligned with the observed widened failure than reopening
  training-side anti-collapse repair
- it is cleaner and cheaper than dual-bank normalization as a first step
- it still includes CSLS as a serious control, so the next decision should be
  evidence-based rather than slogan-based

## 10. Checklist Link

- checklist path: `CHECKLIST.md`
- immediate next unchecked item:
  prepare the dedicated run branch/worktree, then extend the evaluator with the
  four scoring modes and concentration outputs
