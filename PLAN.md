# Main Experiment Plan

## 1. Objective

- run id: `shared_gating_blueprint_semchange_delta_smoke_r1`
- selected idea in `1-2` sentences: The localization smoke showed that the widened chunk line does not fail in the chunk aggregator. Target packets still separate all four chunks, while exported `pred_feat` and `pred_delta` are already collapsed to constant vectors. The chosen next move is exactly one minimal repair that keeps the same pipeline but replaces the main teacher feature target with a target-conditioned semantic blueprint while retaining semantic-change weighting and temporal-delta consistency.
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
- current pass objective: validate and prepare one bounded blueprint-based repair on the same frozen widened surface before spending compute on a full repair run
- research question: Can target-conditioned semantic-blueprint supervision restore chunk-level discrimination in the exported predicted packets without changing the upstream pipeline skeleton?
- null hypothesis: even with blueprint supervision, exported predicted packets remain collapsed, self-surface variance stays at zero, and packet retrieval remains at the `0.25` chance level
- alternative hypothesis: blueprint supervision restores non-zero predicted-packet variance and lifts at least one predicted-to-target packet comparison above `0.25` top-1 on the same frozen bounded surface

## 2. Baseline And Comparability

- baseline id: `nvrc-local-source`
- baseline variant: `tiny-local-teacher-pilot-r3`
- decisive localization evidence from the completed smoke:
  - `target_feat_to_target_feat_seq_concat_top1_accuracy=1.0`
  - `target_delta_to_target_delta_seq_concat_top1_accuracy=1.0`
  - `pred_feat_to_pred_feat_seq_concat_top1_accuracy=0.25`
  - `pred_delta_to_pred_delta_seq_concat_top1_accuracy=0.25`
  - `pred_feat` cross-chunk cosine matrix is all `1.0`
  - `pred_delta` cross-chunk cosine matrix is all `1.0`
  - `pred_feat` and `pred_delta` raw mean dimension variance are both `0.0`
  - `query_projection` and `query_packet_head` are not exported in the frozen bundle, so the earliest accessible collapse surface is `exported_predicted_packets_or_earlier`
- chosen repair family:
  - `teacher_semantic_blueprint=true`
  - keep `teacher_temporal_delta_consistency=true`
  - keep `teacher_temporal_delta_semantic_gating=true`
  - keep `teacher_semantic_change_weighting=true`
- why blueprint wins over relation for the first repair:
  - the observed failure is cross-chunk identity collapse, not merely weak intra-clip temporal structure
  - `blueprint` aligns each clip to its own target-conditioned low-rank semantic subspace, which directly pressures clip-specific separation
  - `relation` preserves within-clip pairwise structure but can still allow different clips to share the same absolute packet location
- comparison rule:
  - keep the same frozen bounded dataset family, shared-gating initialization, and packet-evaluation surfaces
  - add exactly one repair family before interpreting results
  - do not reopen aggregator tuning, broader bridge redesign, or larger multimodal integration in this pass
- comparability risks:
  - blueprint supervision changes the main teacher feature target, so any gain must still be checked against the same packet export and retrieval surfaces
  - current exports still do not expose deeper query-side head tensors
  - a tiny bounded gain without restored packet variance would not count as a real repair

## 3. Code Translation Plan

| Path | Current role | Planned change | Why this is needed | Risk |
|---|---|---|---|---|
| `experiments/main/scripts/run_query_collapse_localization.py` | completed localization entrypoint | keep as the locked diagnostic for pre/post repair comparison | preserves the decisive failure boundary | low |
| `experiments/main/upstream_shared_gating_snapshot/third_party/NVRC/scripts/configs/tasks/overfit/l1_teacher-resnet18-blueprint-semchange-delta.yaml` | new repair config | add one target-conditioned blueprint variant that retains delta and semantic-change weighting | creates a bounded first repair without inventing new model code | low |
| `experiments/main/upstream_shared_gating_snapshot/tools/smoke_teacher_loss.py` | lightweight teacher-path validator | reuse to confirm the chosen blueprint repair path is executable before a real run | catches config or loss-path issues cheaply | low |
| `experiments/main/scripts/run_shared_gating_export_ego4d16f_smoke.sh` | existing frozen export/eval entrypoint | reuse later as the export/eval scaffold after a repaired checkpoint exists | keeps packet comparison surfaces stable | medium |

## 4. Execution Design

- minimal experiment:
  - add the blueprint repair config
  - validate the chosen teacher-loss path with the lightweight smoke utility
  - then prepare one bounded repair run on the same frozen widened surface
  - after a repaired checkpoint exists, export packet bundles and rerun the localization plus packet retrieval package
- smoke / pilot plan:
  - confirm `teacher_semantic_blueprint + semantic_change + temporal_delta` is executable in the frozen NVRC task path
  - do not launch a second repair family before the first blueprint path is validated
- expected outputs:
  - one rerunnable blueprint repair config
  - one smoke validation result for the chosen teacher-loss path
  - one explicit go/no-go judgment on whether a bounded blueprint repair run should launch
- stop condition:
  - the blueprint repair path is validated and the next bounded repair run is specified cleanly
- abandonment condition:
  - the blueprint repair path is invalid or unsupported in the current code path
  - a blueprint-path smoke reveals no meaningful way to evaluate the repair against the existing packet surfaces
  - a later bounded blueprint run leaves predicted packets fully collapsed, in which case the packet-bridge line should be downgraded instead of widened

## 5. Runtime Strategy

- immediate next actions:
  - sync the current branch docs to the completed localization result and the chosen blueprint route
  - add the blueprint repair config
  - run the lightweight teacher-loss smoke for the chosen config
  - if that smoke passes, prepare one bounded repair run on the same frozen widened surface
- artifact locations:
  - completed localization root:
    `experiments/main/evals/shared_gating_query_collapse_localization_smoke_r1/`
  - chosen repair config:
    `experiments/main/upstream_shared_gating_snapshot/third_party/NVRC/scripts/configs/tasks/overfit/l1_teacher-resnet18-blueprint-semchange-delta.yaml`
- safe efficiency levers:
  - reuse the frozen bounded dataset and shared-gating initialization
  - validate the repair path with the cheap teacher-loss smoke before any real run
  - keep the post-repair comparison on the same packet export and localization scripts

## 6. Fallbacks And Recovery

- if the blueprint loss path fails to validate:
  - fall back to the existing `relation` path as the only alternate minimal repair family
- if the blueprint path validates but a later bounded repair run stays collapsed:
  - downgrade the packet-bridge line instead of stacking more repair families
- if deeper query-head tensors remain inaccessible:
  - continue treating exported predicted packets as the primary evaluation surface

## 7. Checklist Link

- checklist path: `CHECKLIST.md`
- next unchecked item: validate the chosen blueprint repair path with the lightweight teacher-loss smoke
