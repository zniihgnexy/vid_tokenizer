# Main Experiment Plan

## 1. Objective

- idea id: `idea-2835dace`
- selected idea in `1-2` sentences:
  the relation repair is now the second measured negative teacher-side result on
  the same frozen widened packet bridge. The next evidence-producing step should
  keep the export and evaluation surface fixed, but inject one minimal
  predicted-side anti-collapse repair directly into the current teacher-loss
  path, with `pred_feat` as the first intervention surface.
- user's core requirements:
  - keep the full pipeline runnable from upstream compression to downstream machine use
  - produce an inspectable result batch that shows whether this direction is worth doing
  - focus the novelty on pipeline/interface usefulness rather than reopening codec ranking
  - leave behind code and scripts that can be rerun locally
- non-negotiable constraints:
  - keep the accepted `nvrc-local-source` baseline contract visible
  - do not reopen upstream codec-line ranking
  - keep reconstructed video as a bounded control, not the main winner claim
  - do not widen scope to a larger-model demo before the local packet bridge is trustworthy
- current pass objective:
  implement and validate one bounded predicted-side variance-floor repair package
  on the same frozen widened surface, then use that smoke result to decide
  whether the line deserves a dedicated `run/*` main experiment branch.
- research question:
  can one explicit predicted-feature variance floor recover more predicted-to-target
  packet alignment than the downgraded blueprint repair and the negative relation
  repair without changing the current export/eval contract?

## 2. Baseline And Comparability

- baseline id: `nvrc-local-source`
- baseline variant: `tiny-local-teacher-pilot-r3`
- locked failure boundary from localization:
  - `target_feat_to_target_feat_seq_concat_top1_accuracy=1.0`
  - `target_delta_to_target_delta_seq_concat_top1_accuracy=1.0`
  - `pred_feat_to_pred_feat_seq_concat_top1_accuracy=0.25`
  - `pred_delta_to_pred_delta_seq_concat_top1_accuracy=0.25`
  - `pred_feat` and `pred_delta` cross-chunk cosine matrices are all `1.0`
  - earliest accessible collapse surface: `exported_predicted_packets_or_earlier`
- nearby failed repair evidence:
  - blueprint repair improved self-discrimination but did not restore usable predicted-to-target alignment
  - relation repair ended at primary-metric delta `0` vs baseline and did not rescue the packet bridge
- fixed control surfaces for this pass:
  - same frozen widened dataset family
  - same shared-gating initialization / resume path
  - same teacher packet export scripts
  - same packet retrieval evaluator
- explicit change boundary:
  - change one repair family only
  - keep `pred_feat` as the primary intervention surface
  - keep `pred_delta` variance regularization optional and off by default in the first config

## 3. Code Touchpoints

| Path | Planned change | Why this is needed |
|---|---|---|
| `experiments/main/upstream_shared_gating_snapshot/third_party/NVRC/tasks.py` | add a minimal variance-floor penalty on predicted teacher features, with optional delta-side extension | this is the narrowest loss-side intervention that matches the measured collapse evidence |
| `experiments/main/upstream_shared_gating_snapshot/third_party/NVRC/main_utils.py` | expose the new task-config fields and CLI plumbing | needed so the new repair can be driven by config like the existing teacher repairs |
| `experiments/main/upstream_shared_gating_snapshot/tools/smoke_teacher_loss.py` | add CLI switches and summary output for variance-floor smoke validation | fastest bounded proof that the new path is wired correctly |
| `experiments/main/upstream_shared_gating_snapshot/third_party/NVRC/scripts/configs/tasks/overfit/*.yaml` | add one task config for the variance-floor repair | keeps the first bounded run reproducible and comparable |
| `experiments/main/scripts/run_shared_gating_variance_repair_smoke.sh` | add one bounded launcher for the new repair | provides the same rerunnable entrypoint shape as the relation run |

## 4. Execution Design

- smoke path:
  - wire the new predicted-side variance-floor penalty into `OverfitTask`
  - expose config fields in `main_utils.py`
  - extend `smoke_teacher_loss.py` so the summary proves the penalty is active
  - run the smoke utility with a variance-floor-on configuration
- if smoke passes:
  - update `status.md` with the validated implementation state
  - decide whether to open a dedicated `run/*` branch and launch the bounded main run
  - keep packet export/eval unchanged so the post-run comparison stays interpretable
- if smoke fails:
  - stop before main-run launch
  - record the exact failure mode
  - fix only the smallest blocking issue instead of widening scope

## 5. Success And Abandonment Criteria

- smoke success criteria:
  - the new loss path runs without shape or config errors
  - the smoke summary shows the variance-floor settings and penalty value explicitly
  - no unrelated export/eval changes are required just to activate the repair
- main-pass success criteria:
  - the line is ready for one dedicated bounded run with the same external comparison surface
  - the run can later be judged against both the blueprint and relation repair evidence
- abandonment criteria:
  - the repair cannot be wired cleanly without wider architecture drift
  - the smoke result exposes an earlier inaccessible bottleneck that makes this intervention no longer defensible

## 6. Runtime Strategy

- safe efficiency levers:
  - reuse the frozen widened dataset family and current resume root
  - validate the repair path with the lightweight smoke utility before any real run
  - keep delta-side variance regularization off in the first config to reduce confounds
- main-run branch rule:
  - do not record a main experiment from this idea branch
  - if smoke passes, create or confirm a dedicated `run/*` branch/worktree before the bounded main run

## 7. Checklist Link

- checklist path: `CHECKLIST.md`
- next unchecked item:
  implement the variance-floor repair package and run the first smoke validation
