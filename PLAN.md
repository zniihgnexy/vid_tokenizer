# Main Experiment Plan

## 1. Objective

- run id: `shared_gating_query_collapse_localization_smoke_r1`
- selected idea in `1-2` sentences: Keep the same frozen widened chunk bundles and the failed chunk-aware evaluator, but stop treating aggregation as the main issue. This child line exists because the target route still separates chunks while the predicted packet routes collapse to constant vectors, so the next question is where discrimination disappears before any repair is attempted.
- user's core requirements:
  - keep the pipeline runnable from upstream compression to downstream machine use
  - produce an inspectable result batch that shows whether this direction is worth doing
  - focus the innovation on pipeline/interface construction rather than reopening codec novelty
  - leave behind code that can be rerun locally and later shared cleanly
- non-negotiable user constraints:
  - do not reopen the upstream codec-line ranking
  - keep the accepted `nvrc-local-source` baseline contract visible
  - treat reconstructed video as a bounded control, not as the default winner
  - avoid a confounded direct VLM/LLM demo before the local bridge is proven
- current pass objective: localize where chunk discrimination disappears across target fields, exported predicted packets, and any query-side projection/head on the same frozen widened four-chunk surface
- research question: Is the decisive bottleneck introduced before packet export, inside the query-side packet head, or only in a later bridge transform?
- null hypothesis: no query-side surface retains chunk discrimination, so the packet-bridge story should be downgraded instead of repaired locally
- alternative hypothesis: discrimination survives somewhere before the final query head, which justifies one minimal diversity-preserving control on the same frozen surface

## 2. Baseline And Comparability

- baseline id: `nvrc-local-source`
- baseline variant: `tiny-local-teacher-pilot-r3`
- inherited widened chunk-aware control:
  - `chunk_target_feat_to_chunk_target_feat_seq_concat_top1_accuracy=1.0`
  - `chunk_pred_feat_to_chunk_target_feat_seq_concat_top1_accuracy=0.25`
  - `chunk_pred_delta_to_chunk_target_feat_seq_concat_top1_accuracy=0.25`
- decisive collapse evidence:
  - `pred_feat` cross-chunk cosine matrix is all `1.0`
  - `pred_delta` cross-chunk cosine matrix is all `1.0`
  - `target_feat` cross-chunk cosine values remain in the `0.9359-0.9596` range
  - `target_delta` cross-chunk cosine values vary from about `-0.1110` to `0.0541`
- inherited bundle surface for this pass:
  - `../idea-idea-e0d17d22/experiments/main/interface_bundles/shared_gating_ego4d16f_teacher_packet_ego4d_small_bridge_16f_chunk00_smoke_r1`
  - `../idea-idea-e0d17d22/experiments/main/interface_bundles/shared_gating_ego4d16f_teacher_packet_ego4d_small_bridge_16f_chunk01_smoke_r1`
  - `../idea-idea-e0d17d22/experiments/main/interface_bundles/shared_gating_ego4d16f_teacher_packet_ego4d_small_bridge_16f_chunk02_smoke_r1`
  - `../idea-idea-e0d17d22/experiments/main/interface_bundles/shared_gating_ego4d16f_teacher_packet_ego4d_small_bridge_16f_chunk03_smoke_r1`
- comparison rule:
  - keep the same frozen chunk bundles, evaluator contract, and bounded four-chunk surface
  - change only the diagnostic surface: inspect target fields, exported predicted packets, and query-side projections
  - do not reopen upstream export, codec ranking, or downstream evaluator design in this pass
  - add a repair control only after localization points to one clear failing layer
- comparability risks:
  - some query-side projections may not be preserved in the exported packet files, which could force a narrower diagnostic than planned
  - a tiny-surface anti-collapse control could overfit and create a misleading gain
  - if the collapse is already upstream of packet export, this child line may terminate quickly

## 3. Code Translation Plan

| Path | Current role | Planned change | Why this is needed | Risk |
|---|---|---|---|---|
| `experiments/main/scripts/run_chunk_aware_packet_eval.py` | current failed control evaluator | reuse as the locked comparison surface for the new line | keeps the child line tied to the exact failed control rather than a moving target | low |
| `experiments/main/scripts/run_query_collapse_localization.py` | new localization script | add one diagnostic entrypoint that measures cosine, rank, and variance surfaces across target/pred/query tensors | turns the selected idea into a bounded, interpretable experiment | medium |
| `experiments/main/evals/shared_gating_query_collapse_localization_smoke_r1/` | new localization output root | create a durable report, summary, and per-surface diagnostic package | keeps the next route choice grounded in files instead of chat | low |
| `experiments/main/scripts/run_query_diversity_control.py` | optional minimal repair entrypoint | defer implementation until localization shows the query head is the failing layer | prevents mixing diagnosis and repair prematurely | medium |

## 4. Execution Design

- minimal experiment:
  - read the existing widened chunk bundles and current chunk-aware control outputs
  - measure cross-chunk discrimination at target fields, exported predicted packets, and any query-side projection/head tensors that can be accessed without changing the upstream contract
  - write one report with cosine matrices, per-surface rank summaries, and per-dimension variance summaries
- smoke / pilot plan:
  - confirm the required tensors are accessible from the frozen widened bundles or the closest non-confounding export surface
  - run one localization smoke on the four chunk objects
  - confirm that the diagnostic package clearly identifies the earliest surface where discrimination collapses, or honestly reports that the available surfaces are insufficient
- expected outputs:
  - one rerunnable localization entrypoint
  - one diagnostic output root with report, summary, cosine matrices, and per-surface statistics
  - one explicit judgment on whether a minimal repair is justified and where it should attach
- stop condition:
  - the localization package identifies the earliest surface where query-side discrimination disappears
- abandonment condition:
  - no additional query-side surface can be accessed without changing the frozen contract
  - every accessible query-side surface is already collapsed, leaving no clear local repair point
  - the localization result shows the packet-bridge line should be downgraded instead of repaired

## 5. Runtime Strategy

- immediate next actions:
  - sync this child branch's control docs to the localization-first route
  - write the localization entrypoint inside the child worktree
  - run the first localization smoke before choosing any repair family
- artifact locations:
  - failed chunk-aware control root:
    `../idea-idea-955ff951/experiments/main/evals/shared_gating_ego4d16f_chunk_aware_packet_smoke_r1/`
  - current child localization root:
    `experiments/main/evals/shared_gating_query_collapse_localization_smoke_r1/`
- safe efficiency levers:
  - reuse the same frozen widened bundles instead of rerunning upstream export
  - localize with lightweight tensor diagnostics before adding any repair control
  - if repair is justified, test exactly one minimal family before widening scope

## 6. Fallbacks And Recovery

- if the needed query-side projection is not preserved in the current packet files:
  - fall back to the closest accessible exported surface and classify the missing surface as a frozen-contract limitation
- if the collapse already exists before packet export:
  - downgrade the packet-bridge story and stop before inventing a local repair
- if the collapse localizes to the query-side head:
  - choose the smallest clean repair family from asymmetry, variance, redundancy reduction, or temporal contrastive calibration
- if the first repair family fails:
  - treat that as evidence against easy local salvage rather than immediately stacking more controls

## 7. Checklist Link

- checklist path: `CHECKLIST.md`
- next unchecked item: write and run the first localization smoke package
