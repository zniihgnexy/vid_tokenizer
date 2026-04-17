# Shared-gating predicted variance-floor repair on frozen widened bridge surface

- Run id: `shared_gating_pred_variance_repair_ego4d16f_smoke_r1`
- Branch: `run/shared_gating_pred_variance_repair_ego4d16f_smoke_r1`
- Parent branch: `idea/002-idea-2835dace`
- Worktree: `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/shared-gating-pred-variance-repair-ego4d16f-smoke-r1`
- Idea: `idea-2835dace`
- Baseline: `nvrc-local-source`
- Baseline variant: `tiny-local-teacher-pilot-r3`
- Dataset scope: `bounded local bridge subset ego4d_small_bridge_16f with 16 frames at 32x32 resolution; same frozen widened bridge surface used for the relation-repair comparison.`
- Verdict: `mixed`
- Status: `completed`

## Hypothesis

A minimal predicted-feature variance-floor regularizer on the same frozen widened bridge surface can improve bounded teacher-consistency without changing the external packet export/evaluation surface.

## Setup

Dedicated run branch/worktree on the active idea line. Resume root: shared_gating_interface_export_ego4d16f_chunk00_smoke_r1. Task config keeps semantic-change weighting and temporal-delta consistency enabled, turns on predicted-feature variance floor with weight=1.0 and margin=0.1, and keeps predicted-delta variance floor off. The external packet export/eval surface stays fixed to the same bounded ego4d_small_bridge_16f bridge subset.

## Execution

First bounded run on this branch exposed a real plumbing bug: the new variance-floor fields were present in args.yaml but were not forwarded through create_overfit_task(...), so the effective pred_variance_weight stayed at 0.0 in both train and eval logs. That invalid first output was archived, the missing passthrough was fixed in tasks.py, syntax was rechecked, and the corrected bounded run was relaunched and completed successfully under bash session bash-9cf7c4a3.

## Results

{"output_dir":"/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/shared-gating-pred-variance-repair-ego4d16f-smoke-r1/experiments/main/shared_gating_pred_variance_repair_ego4d16f_smoke_r1","archived_invalid_attempt_reason":"missing create_overfit_task passthrough kept pred_variance_weight at 0.0","corrected_run_session":"bash-9cf7c4a3","archived_invalid_run_session":"bash-4cf72434"}

## Conclusion

The minimal predicted-side variance-floor repair is now validated as an effective live regularizer in the real bounded main-run path, but its first measured trade-off is mixed rather than clearly positive. It is good enough to support route judgment, but not good enough to claim that this repair family already improves the bridge end to end.

## Metrics Summary

- `uvg_bd_rate_reduction_pct_vs_vtm_ra_psnr` = 24
- `local_resnet18_teacher_smoke_loss_value` = 0.3541
- `tiny_local_teacher_pilot_bpp_avg` = 88.2109
- `tiny_local_teacher_pilot_psnr_avg` = 10.8996
- `tiny_local_teacher_pilot_teacher_mse_avg` = 0.5145
- `beauty_teacher_smoke_bpp_avg` = 2.091
- `beauty_teacher_smoke_psnr_avg` = 14.9552
- `beauty_teacher_smoke_teacher_mse_avg` = 0.0363
- `beauty_no_teacher_partial_teacher_mse` = 0.0472
- `bpp_avg` = 23.9277
- `psnr_avg` = 10.4509
- `teacher_mse_avg` = 0.4821
- `bounded_bridge_bpp_avg` = 23.9277
- `bounded_bridge_psnr_avg` = 10.4509
- `bounded_bridge_teacher_mse_avg` = 0.4821

## Baseline Comparison

- `uvg_bd_rate_reduction_pct_vs_vtm_ra_psnr`: run=24 baseline=24 delta=0 (worse)
- `local_resnet18_teacher_smoke_loss_value`: run=0.3541 baseline=0.3541 delta=0 (worse)
- `tiny_local_teacher_pilot_bpp_avg`: run=88.2109 baseline=88.2109 delta=0 (worse)
- `tiny_local_teacher_pilot_psnr_avg`: run=10.8996 baseline=10.8996 delta=0 (worse)
- `tiny_local_teacher_pilot_teacher_mse_avg`: run=0.5145 baseline=0.5145 delta=0 (worse)
- `beauty_teacher_smoke_bpp_avg`: run=2.091 baseline=2.091 delta=0 (worse)
- `beauty_teacher_smoke_psnr_avg`: run=14.9552 baseline=14.9552 delta=0 (worse)
- `beauty_teacher_smoke_teacher_mse_avg`: run=0.0363 baseline=0.0363 delta=0 (worse)
- `beauty_no_teacher_partial_teacher_mse`: run=0.0472 baseline=0.0472 delta=0 (worse)
- `bpp_avg`: run=23.9277 baseline=None delta=n/a (not comparable)
- `psnr_avg`: run=10.4509 baseline=None delta=n/a (not comparable)
- `teacher_mse_avg`: run=0.4821 baseline=None delta=n/a (not comparable)
- `bounded_bridge_bpp_avg`: run=23.9277 baseline=None delta=n/a (not comparable)
- `bounded_bridge_psnr_avg`: run=10.4509 baseline=None delta=n/a (not comparable)
- `bounded_bridge_teacher_mse_avg`: run=0.4821 baseline=None delta=n/a (not comparable)

## Changed Files

- `experiments/main/upstream_shared_gating_snapshot/third_party/NVRC/tasks.py`
- `experiments/main/upstream_shared_gating_snapshot/third_party/NVRC/main_utils.py`
- `experiments/main/upstream_shared_gating_snapshot/tools/smoke_teacher_loss.py`
- `experiments/main/upstream_shared_gating_snapshot/third_party/NVRC/scripts/configs/tasks/overfit/l1_teacher-resnet18-variance-semchange-delta.yaml`
- `experiments/main/scripts/run_shared_gating_variance_repair_smoke.sh`
- `PLAN.md`
- `CHECKLIST.md`
- `status.md`

## Evidence Paths

- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/shared-gating-pred-variance-repair-ego4d16f-smoke-r1/experiments/main/shared_gating_pred_variance_repair_ego4d16f_smoke_r1`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/shared-gating-pred-variance-repair-ego4d16f-smoke-r1/experiments/main/shared_gating_pred_variance_repair_ego4d16f_smoke_r1/results/all.txt`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/shared-gating-pred-variance-repair-ego4d16f-smoke-r1/experiments/main/shared_gating_pred_variance_repair_ego4d16f_smoke_r1/args.yaml`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/bash_exec/bash-9cf7c4a3/terminal.log`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/bash_exec/bash-4cf72434/terminal.log`

## Config Paths

- `experiments/main/scripts/run_shared_gating_variance_repair_smoke.sh`
- `experiments/main/upstream_shared_gating_snapshot/third_party/NVRC/scripts/configs/tasks/overfit/l1_teacher-resnet18-variance-semchange-delta.yaml`

## Notes

- Treat this as the first valid bounded evidence point for the predicted-side variance-floor line, not as a paper-facing win.
- The archived first attempt remains useful only as debugging evidence because the configured regularizer never became active there.
- Canonical baseline metrics are carried through in the record to preserve the accepted comparison contract; the run-specific bounded-bridge metrics are the newly measured evidence for this branch.

## Evaluation Summary

- Not recorded.

## Delivery Policy

- Research paper required: `True`
- Recommended next route: `revise_idea`
- Reason: Research paper mode is enabled, but the current run does not beat the baseline clearly enough. Revise the direction or strengthen the method before writing.
