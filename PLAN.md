# Idea Round Plan

## 1. Objective

- idea id: `idea-2835dace`
- selected idea in `1-2` sentences:
  the bounded relation repair became the second negative teacher-side result on
  the same frozen widened packet bridge. The next round should stay on the same
  comparison surface but shift the bottleneck story back to the predicted side:
  localize what is still accessible around the query-side packet path, then test
  one minimal anti-collapse repair that acts on predicted packet features instead
  of adding another teacher-side auxiliary loss.
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
- current pass objective:
  close the current idea round with a literature-grounded and code-grounded
  route choice for one bounded predicted-side anti-collapse experiment package.
- research question:
  on the same frozen widened packet bridge surface, can one minimal
  predicted-side anti-collapse control recover more predicted-to-target packet
  alignment than the downgraded blueprint repair and the negative relation repair?
- null hypothesis:
  the accessible predicted packet surfaces are already too late or too collapsed,
  so even a direct anti-collapse control will not improve packet alignment
  meaningfully.
- alternative hypothesis:
  a bounded predicted-side anti-collapse control, especially explicit variance
  regularization on the accessible packet features or deltas, improves at least
  one predicted-to-target comparison while preserving the same export and eval
  surface.

## 2. Evidence And Comparability

- baseline id: `nvrc-local-source`
- baseline variant: `tiny-local-teacher-pilot-r3`
- locked failure boundary from the localization package:
  - `target_feat_to_target_feat_seq_concat_top1_accuracy=1.0`
  - `target_delta_to_target_delta_seq_concat_top1_accuracy=1.0`
  - `pred_feat_to_pred_feat_seq_concat_top1_accuracy=0.25`
  - `pred_delta_to_pred_delta_seq_concat_top1_accuracy=0.25`
  - `pred_feat` and `pred_delta` cross-chunk cosine matrices are all `1.0`
  - `pred_feat` and `pred_delta` raw mean dimension variance are both `0.0`
  - earliest accessible collapse surface:
    `exported_predicted_packets_or_earlier`
- first repair that was downgraded:
  - blueprint repair single-bundle eval:
    - `target_feat_to_target_feat_top1_accuracy=1.0`
    - `pred_feat_to_target_feat_top1_accuracy=0.0625`
    - `pred_delta_to_target_delta_top1_accuracy=0.1875`
    - `pred_delta_to_target_delta_mean_margin_vs_best_nonmatch=-0.0784`
  - interpretation:
    self-discrimination improved, but usable predicted-to-target alignment did
    not.
- second repair that was rejected:
  - relation main result:
    `uvg_bd_rate_reduction_pct_vs_vtm_ra_psnr=24` vs baseline `24` (`delta=0`)
  - route implication:
    another teacher-side repair family did not move the active packet-bridge
    line forward.
- accessible code surfaces today:
  - `pred_feat`, `target_feat`, `pred_delta`, `target_delta`
  - relation matrices and current packet export/eval scripts
- inaccessible deeper surfaces today:
  - `query_projection`
  - `query_packet_head`
- comparability rule:
  - keep the same frozen widened dataset family, shared-gating initialization,
    packet exporter, and packet evaluator
  - change exactly one predicted-side repair family at a time
  - do not reopen codec ranking, broader interface redesign, or larger-model
    integration in this pass

## 3. Candidate Frontier

### Candidate A: localization-first plus variance-floor repair

- recommended: yes
- mechanism:
  keep the current active idea family, expose deeper query-side surfaces only if
  cheap, and otherwise add one explicit variance-floor control on accessible
  `pred_feat` / `pred_delta`, with a tiny covariance term only if needed.
- why it wins:
  it matches the measured failure mode directly, keeps the next result
  interpretable, and is the smallest code-path change supported by the current
  literature sweep.

### Candidate B: redundancy-reduction or covariance-heavy repair

- recommended: second best
- mechanism:
  use a Barlow/VICReg-style decorrelation-heavy repair on predicted packet
  features.
- why not first:
  it is broader than the variance-first route and would make another negative
  result harder to interpret.

### Candidate C: return to interface redesign

- recommended: fallback only
- mechanism:
  stop local repair and go back to chunk-aware or packet-structure redesign.
- why not first:
  the direct predicted-side collapse evidence is still too strong to skip one
  bounded predicted-side repair.

## 4. Code Translation Plan

| Path | Current role | Planned change | Why this is needed | Risk |
|---|---|---|---|---|
| `experiments/main/scripts/run_query_collapse_localization.py` | locked failure-boundary diagnostic | keep as the reference package and reuse its missing-surface report | preserves the decisive pre-repair boundary | low |
| `experiments/main/upstream_shared_gating_snapshot/third_party/NVRC/teacher_utils.py` | exposes `pred_feat`, `target_feat`, `pred_delta`, `target_delta` | inspect whether a minimal predicted-side variance control can be inserted without changing the baseline contract | this is the nearest accessible intervention surface | medium |
| `experiments/main/upstream_shared_gating_snapshot/third_party/NVRC/tasks.py` | teacher-consistency loss assembly | identify the smallest hook point for a bounded predicted-side anti-collapse regularizer | keeps the intervention in the current loss path rather than inventing a new exporter-centric hack | medium |
| `experiments/main/scripts/export_teacher_feature_interface.py` | packet bundle export | keep unchanged as the post-repair export surface unless deeper query-side tensors become cheaply exposable | preserves packet-surface comparability | low |
| `experiments/main/scripts/run_teacher_packet_eval.py` | bounded packet retrieval evaluator | keep unchanged as the main predicted-to-target comparison surface | ensures direct comparison to blueprint and relation results | low |

## 5. Execution Design

- first bounded package:
  - re-read the localization package and current hook points
  - confirm whether `query_projection` or `query_packet_head` can be exposed
    cheaply; if not, treat accessible predicted packet tensors as the intervention
    surface
  - implement exactly one explicit predicted-side anti-collapse control
    (variance-floor first)
  - rerun the same packet export and teacher-packet evaluation
- success criteria:
  - the current idea round leaves one explicit next experiment package instead of
    another vague anti-collapse bucket
  - the chosen repair improves at least one predicted-to-target packet metric
    beyond the downgraded blueprint and negative relation results, or produces a
    clearer negative result that justifies reopening interface redesign
- abandonment criteria:
  - deeper query-side surfaces remain inaccessible and the accessible control
    cannot be added cleanly without wider architecture drift
  - the chosen repair is implemented cleanly but still leaves alignment near
    chance, in which case the next move should be interface redesign instead of
    another nearby regularizer

## 6. Runtime Strategy

- immediate next actions:
  - create the missing literature survey for the active branch
  - sync `PLAN.md`, `CHECKLIST.md`, and `status.md` to the active anti-collapse route
  - revise the active idea package with the literature-grounded candidate ranking
  - hand off to `experiment` for one bounded predicted-side localization-plus-repair package
- safe efficiency levers:
  - reuse the frozen widened dataset family and the same export/eval scripts
  - prefer a hook-point audit before broader code edits
  - keep the first repair minimal and local to accessible predicted-side tensors

## 7. Checklist Link

- checklist path: `CHECKLIST.md`
- next unchecked item: revise the active idea durably, then hand off to
  experiment for the bounded predicted-side repair package
