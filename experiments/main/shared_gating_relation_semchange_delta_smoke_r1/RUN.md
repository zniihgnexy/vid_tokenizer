# Shared-gating relation repair on frozen widened bridge surface

- Run id: `shared_gating_relation_semchange_delta_smoke_r1`
- Branch: `run/shared_gating_relation_semchange_delta_smoke_r1`
- Parent branch: `run/shared_gating_relation_semchange_delta_smoke_r1`
- Worktree: `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/shared-gating-relation-semchange-delta-smoke-r1`
- Idea: `idea-253b77bd`
- Baseline: `nvrc-local-source`
- Baseline variant: `tiny-local-teacher-pilot-r3`
- Dataset scope: `ego4d_small_bridge_16f bounded local bridge surface, 16 frames, 32x32 resolution, shared-gating resumed local repair run`
- Verdict: `negative`
- Status: `completed`

## Hypothesis

Adding teacher_relation_consistency on top of the frozen widened shared-gating surface will improve predicted-to-target packet alignment beyond the downgraded blueprint repair while preserving the same downstream export and evaluation interface.

## Setup

Frozen widened bounded bridge surface using ego4d_small_bridge_16f (16 frames at 32x32), shared-gating initialization resumed from shared_gating_interface_export_ego4d16f_chunk00_smoke_r1, relation+semantic-change+temporal-delta task config l1_teacher-resnet18-relation-semchange-delta.yaml, dedicated run wrapper experiments/main/scripts/run_shared_gating_relation_repair_smoke.sh.

## Execution

1. Validated the relation path with smoke_teacher_loss.py and saved experiments/main/evals/shared_gating_relation_teacher_loss_smoke_r1/summary.json. 2. Launched the bounded relation repair run via run_shared_gating_relation_repair_smoke.sh. 3. Exported the resulting teacher packet bundle with export_teacher_feature_interface.py. 4. Evaluated the bundle with run_teacher_packet_eval.py on the same teacher-packet surface used for the downgraded blueprint repair.

## Results

The bounded relation repair run completed successfully and produced a full checkpoint, bitstream, decoded outputs, and downstream packet bundle. Upstream aggregate metrics improved teacher consistency relative to blueprint (teacher-mse_avg 0.4888 vs 0.5481) while keeping similar bitrate (bpp_avg 23.9043 vs 23.8984). However, the downstream interface claim did not improve: pred_feat_to_target_feat top1 stayed at 0.0625, pred_delta_to_target_delta top1 regressed from 0.1875 to 0.0625, and the concat feature+delta comparison fell to 0.0 top1. Mean feature cosine improved (0.5972 vs 0.5387) but mean matching margins remained negative across all predicted-to-target comparisons.

## Conclusion

The built-in relation repair family does not rescue the current packet bridge on the frozen widened surface. The correct next move is to downgrade this repair line and route back to an interface-level or packet-structure redesign rather than stacking more nearby teacher-loss regularizers.

## Metrics Summary

- `uvg_bd_rate_reduction_pct_vs_vtm_ra_psnr` = 24
- `local_resnet18_teacher_smoke_loss_value` = 0.4067
- `tiny_local_teacher_pilot_bpp_avg` = 88.2109
- `tiny_local_teacher_pilot_psnr_avg` = 10.8996
- `tiny_local_teacher_pilot_teacher_mse_avg` = 0.5145
- `beauty_teacher_smoke_bpp_avg` = 2.091
- `beauty_teacher_smoke_psnr_avg` = 14.9552
- `beauty_teacher_smoke_teacher_mse_avg` = 0.0363
- `beauty_no_teacher_partial_teacher_mse` = 0.0472
- `bpp_avg` = 23.9043
- `psnr_avg` = 10.4351
- `teacher_mse_avg` = 0.4888
- `target_feat_to_target_feat_top1_accuracy` = 1
- `pred_feat_to_target_feat_top1_accuracy` = 0.0625
- `pred_feat_to_target_feat_mean_margin_vs_best_nonmatch` = -0.0219
- `pred_delta_to_target_delta_top1_accuracy` = 0.0625
- `pred_delta_to_target_delta_mean_margin_vs_best_nonmatch` = -0.137
- `pred_feat_plus_delta_concat_to_target_top1_accuracy` = 0

## Baseline Comparison

- `uvg_bd_rate_reduction_pct_vs_vtm_ra_psnr`: run=24 baseline=24 delta=0 (worse)
- `local_resnet18_teacher_smoke_loss_value`: run=0.4067 baseline=0.3541 delta=0.0525 (worse)
- `tiny_local_teacher_pilot_bpp_avg`: run=88.2109 baseline=88.2109 delta=0 (worse)
- `tiny_local_teacher_pilot_psnr_avg`: run=10.8996 baseline=10.8996 delta=0 (worse)
- `tiny_local_teacher_pilot_teacher_mse_avg`: run=0.5145 baseline=0.5145 delta=0 (worse)
- `beauty_teacher_smoke_bpp_avg`: run=2.091 baseline=2.091 delta=0 (worse)
- `beauty_teacher_smoke_psnr_avg`: run=14.9552 baseline=14.9552 delta=0 (worse)
- `beauty_teacher_smoke_teacher_mse_avg`: run=0.0363 baseline=0.0363 delta=0 (worse)
- `beauty_no_teacher_partial_teacher_mse`: run=0.0472 baseline=0.0472 delta=0 (worse)
- `bpp_avg`: run=23.9043 baseline=None delta=n/a (not comparable)
- `psnr_avg`: run=10.4351 baseline=None delta=n/a (not comparable)
- `teacher_mse_avg`: run=0.4888 baseline=None delta=n/a (not comparable)
- `target_feat_to_target_feat_top1_accuracy`: run=1 baseline=None delta=n/a (not comparable)
- `pred_feat_to_target_feat_top1_accuracy`: run=0.0625 baseline=None delta=n/a (not comparable)
- `pred_delta_to_target_delta_top1_accuracy`: run=0.0625 baseline=None delta=n/a (not comparable)
- `pred_feat_plus_delta_concat_to_target_top1_accuracy`: run=0 baseline=None delta=n/a (not comparable)
- `pred_feat_to_target_feat_mean_margin_vs_best_nonmatch`: run=-0.0219 baseline=None delta=n/a (not comparable)
- `pred_delta_to_target_delta_mean_margin_vs_best_nonmatch`: run=-0.137 baseline=None delta=n/a (not comparable)

## Changed Files

- `CHECKLIST.md`
- `PLAN.md`
- `status.md`
- `experiments/main/scripts/run_shared_gating_relation_repair_smoke.sh`

## Evidence Paths

- `experiments/main/evals/shared_gating_relation_teacher_loss_smoke_r1/summary.json`
- `experiments/main/shared_gating_relation_repair_ego4d16f_smoke_r1/results/all.txt`
- `experiments/main/shared_gating_relation_repair_ego4d16f_smoke_r1/args.yaml`
- `experiments/main/interface_bundles/shared_gating_relation_repair_teacher_packet_smoke_r1`
- `experiments/main/evals/shared_gating_relation_repair_teacher_packet_smoke_r1/summary.json`

## Config Paths

- `experiments/main/upstream_shared_gating_snapshot/third_party/NVRC/scripts/configs/tasks/overfit/l1_teacher-resnet18-relation-semchange-delta.yaml`
- `experiments/main/scripts/run_shared_gating_relation_repair_smoke.sh`

## Notes

- Important comparability caveat: this result lives on the local bounded bridge surface and should be interpreted against the prior blueprint repair on the same surface, not against the UVG paper-facing coding-gain metric in the accepted baseline contract.
- Required baseline metric ids that were not remeasured on this run are carried forward unchanged from the confirmed baseline contract as reference-only placeholders. The actual route judgment for this run should use the relation smoke, bounded bridge aggregate metrics, and teacher-packet evaluation metrics in the extra fields.

## Evaluation Summary

- Not recorded.

## Delivery Policy

- Research paper required: `True`
- Recommended next route: `revise_idea`
- Reason: Research paper mode is enabled, but the current run does not beat the baseline clearly enough. Revise the direction or strengthen the method before writing.
