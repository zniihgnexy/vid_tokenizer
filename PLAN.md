# Main Experiment Plan

## 1. Objective

- run id: `shared_gating_relation_semchange_delta_smoke_r1`
- selected idea in `1-2` sentences: The first bounded `blueprint + semantic-change + temporal-delta` repair no longer looks like a total constant-vector collapse, but it still fails the core target-alignment test. On the repaired 16-frame bundle, `target_feat` remains perfectly discriminative while `pred_feat -> target_feat` stays at `0.0625` top-1 and `pred_delta -> target_delta` reaches only `0.1875` with negative mean margin. The next move is exactly one more nearby repair that targets cross-view alignment more directly: `teacher_relation_consistency` on the same frozen surface.
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
- current pass objective: downgrade the insufficient blueprint repair cleanly, then validate and prepare one bounded relation-based repair on the same frozen widened surface
- research question: Can relation-consistency supervision recover predicted-to-target packet alignment after blueprint already showed that self-discrimination alone is not enough?
- null hypothesis: relation consistency also fails to lift packet alignment beyond near-chance retrieval, leaving the packet-bridge line unsupported on this frozen surface
- alternative hypothesis: relation consistency improves at least one predicted-to-target packet comparison beyond the current blueprint result while preserving the same bounded pipeline and export surfaces

## 2. Baseline And Comparability

- baseline id: `nvrc-local-source`
- baseline variant: `tiny-local-teacher-pilot-r3`
- locked failure boundary from the completed localization smoke:
  - `target_feat_to_target_feat_seq_concat_top1_accuracy=1.0`
  - `target_delta_to_target_delta_seq_concat_top1_accuracy=1.0`
  - `pred_feat_to_pred_feat_seq_concat_top1_accuracy=0.25`
  - `pred_delta_to_pred_delta_seq_concat_top1_accuracy=0.25`
  - `pred_feat` cross-chunk cosine matrix is all `1.0`
  - `pred_delta` cross-chunk cosine matrix is all `1.0`
  - `pred_feat` and `pred_delta` raw mean dimension variance are both `0.0`
  - the earliest accessible collapse surface remains `exported_predicted_packets_or_earlier`
- first repair result that triggered the downgrade:
  - bounded repair run aggregate metrics:
    - `bpp_avg=23.8984`
    - `psnr_avg=10.6733`
    - `teacher-mse_avg=0.5481`
  - repaired single-bundle teacher-packet evaluation:
    - `target_feat_to_target_feat_top1_accuracy=1.0`
    - `pred_feat_to_target_feat_top1_accuracy=0.0625`
    - `pred_delta_to_target_delta_top1_accuracy=0.1875`
    - `pred_delta_to_target_delta_mean_margin_vs_best_nonmatch=-0.0784`
  - within-bundle self checks on the repaired 16-frame packet bundle:
    - `pred_feat_self_top1=1.0`, `offdiag_mean=0.9947`, `raw_mean_dim_var=0.274643`
    - `pred_delta_self_top1=0.9375`, `offdiag_mean=-0.0543`, `raw_mean_dim_var=0.000028`
- interpretation of the downgrade:
  - the blueprint repair no longer looks like the earlier all-ones cross-chunk constant collapse
  - but the exported predicted packets still do not align cleanly enough to target packets for a credible machine-facing interface claim
  - this means the remaining bottleneck is target alignment, not merely injecting more self-variance
- chosen next repair family:
  - `teacher_relation_consistency=true`
  - keep the same frozen bounded dataset family and packet export/eval surface
  - keep semantic-change weighting and temporal-delta consistency unless the existing relation path requires a simpler first validation
- why relation now wins over staying on blueprint:
  - blueprint already showed that extra self-discrimination does not automatically recover predicted-to-target alignment
  - relation consistency is the nearest existing repair family that directly regularizes cross-view relational structure between predicted and target features
  - inventing a new custom contrastive packet loss would add unnecessary code risk before exhausting the built-in nearby repair
- comparison rule:
  - keep the same frozen bounded dataset family, shared-gating initialization, and packet-evaluation scripts
  - change exactly one repair family at a time
  - do not reopen aggregator tuning, broader bridge redesign, or larger multimodal integration in this pass
- comparability risks:
  - the repaired single-bundle result is not directly comparable to the earlier 4-chunk localization package
  - deeper `query_projection` and `query_packet_head` tensors are still not exported
  - a small delta-only gain without positive matching margin would still not count as a real repair

## 3. Code Translation Plan

| Path | Current role | Planned change | Why this is needed | Risk |
|---|---|---|---|---|
| `experiments/main/scripts/run_query_collapse_localization.py` | locked failure-boundary diagnostic | keep as the reference localization package for the earlier collapse claim | preserves the decisive pre-repair boundary | low |
| `experiments/main/scripts/export_teacher_feature_interface.py` | packet bundle export | keep as the same bundle export surface for repaired runs | preserves interface comparability | low |
| `experiments/main/scripts/run_teacher_packet_eval.py` | single-bundle packet retrieval evaluator | keep as the bounded alignment check for repaired runs | directly measures whether predicted packets align to target packets | low |
| `experiments/main/upstream_shared_gating_snapshot/third_party/NVRC/scripts/configs/tasks/overfit/l1_teacher-resnet18-relation-semchange-delta.yaml` | new relation repair config | add one relation-based repair variant on the frozen surface | enables the next nearby repair without architectural drift | low |
| `experiments/main/upstream_shared_gating_snapshot/tools/smoke_teacher_loss.py` | lightweight teacher-path validator | reuse to confirm the relation repair path before a real run | catches config or loss-path issues cheaply | low |

## 4. Execution Design

- minimal experiment:
  - write the relation repair config
  - validate the chosen relation path with the lightweight teacher-loss smoke utility
  - if that smoke passes, prepare one bounded relation repair run on the same frozen widened surface
  - after a repaired checkpoint exists, export a teacher packet bundle and rerun the bounded teacher-packet evaluation
- smoke / pilot plan:
  - confirm `teacher_relation_consistency` is executable in the frozen NVRC task path on top of the same bounded setup
  - do not widen to a custom new loss family before the relation path is interpreted
- expected outputs:
  - one rerunnable relation repair config
  - one smoke validation result for the chosen relation loss path
  - one explicit go/no-go judgment on whether a bounded relation repair run should launch
- stop condition:
  - the relation repair path is validated and the next bounded repair run is specified cleanly
- abandonment condition:
  - relation consistency is invalid or unsupported in the current code path
  - a relation-path smoke reveals no meaningful way to evaluate against the existing packet surfaces
  - a later bounded relation run still leaves predicted-to-target packet alignment near chance, in which case the packet-bridge line should be downgraded again instead of widened

## 5. Runtime Strategy

- immediate next actions:
  - sync the current branch docs to the completed blueprint downgrade
  - add the relation repair config
  - run the lightweight teacher-loss smoke for the chosen relation config
  - if that smoke passes, prepare one bounded relation repair run on the same frozen widened surface
- artifact locations:
  - locked localization root:
    `experiments/main/evals/shared_gating_query_collapse_localization_smoke_r1/`
  - downgraded blueprint single-bundle eval:
    `experiments/main/evals/shared_gating_blueprint_repair_teacher_packet_smoke_r1/`
  - downgraded blueprint bundle:
    `experiments/main/interface_bundles/shared_gating_blueprint_repair_teacher_packet_smoke_r1/`
- safe efficiency levers:
  - reuse the frozen bounded dataset and shared-gating initialization
  - validate the relation path with the cheap teacher-loss smoke before any real run
  - keep the post-repair comparison on the same packet export and teacher-packet evaluation scripts

## 6. Fallbacks And Recovery

- if the relation loss path fails to validate:
  - stop stacking built-in teacher repair families and reopen route selection explicitly
- if the relation path validates but a later bounded run still stays near chance:
  - downgrade the packet-bridge line again instead of adding more ad hoc regularizers
- if deeper query-head tensors remain inaccessible:
  - continue treating exported predicted packets and bounded teacher-packet evaluation as the primary evaluation surface

## 7. Checklist Link

- checklist path: `CHECKLIST.md`
- next unchecked item: add and validate the relation repair config with the lightweight teacher-loss smoke
