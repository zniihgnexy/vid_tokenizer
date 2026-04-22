# Teacher gallery-anchor packet adapter smoke on the local 4-frame bundle

- Run id: `teacher_anchored_packet_adapter_smoke_r1`
- Branch: `run/teacher_anchored_packet_adapter_smoke_r1`
- Parent branch: `none`
- Worktree: `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/teacher-anchored-packet-adapter-smoke-r1`
- Idea: `none`
- Baseline: `nvrc-local-source`
- Baseline variant: `tiny-local-teacher-pilot-r3`
- Dataset scope: `tiny_local_synthetic bounded packet-bundle smoke; 4 frames; retrieval-style packet matching against target-side teacher space.`
- Verdict: `improved`
- Status: `completed`

## Hypothesis

A fixed teacher gallery-anchor softmax projection from the joint packet query space (pred_feat + 8.0 * pred_delta) into target_feat space can materially improve packet-side target_feat retrieval over the direct pred_feat -> target_feat control without changing the packet bundle schema.

## Setup

Dedicated run branch/worktree: run/teacher_anchored_packet_adapter_smoke_r1. Reused experiments/main/interface_bundles/shared_gating_teacher_packet_smoke_r1 with 4 bounded frames, teacher_type resnet18_imagenet, packet fields pred_feat/target_feat/pred_delta/target_delta, delta_weight=8.0, and anchor_logit_scale=16.0. No upstream retraining or exporter schema change was introduced in this pass.

## Execution

Validated the new evaluator with python -m py_compile, then ran ./experiments/main/scripts/run_teacher_anchor_packet_adapter_smoke.sh in the dedicated run worktree. The script completed successfully and wrote summary.json, report.md, per-comparison row csv files, similarity matrices, and teacher_gallery_anchor_weights.csv.

## Results

Headline packet-interface result: teacher_gallery_anchor_joint_to_target_feat achieved top-1 accuracy 0.75 and mean match rank 1.5 in target_feat space, versus only 0.25 and 2.5 for the direct pred_feat -> target_feat control. The remaining failure case is query 0000 collapsing toward 0001; queries 0001, 0002, and 0003 are correct.

## Conclusion

This bounded smoke supports continuing the packet-memory interface line. The route should not widen to a larger-model handoff yet, but it has now cleared the minimum bar for a real runnable packet-interface result batch and justifies either a wider packet-memory validation pass or a targeted redesign around the remaining 0000/0001 confusion.

## Metrics Summary

- `uvg_bd_rate_reduction_pct_vs_vtm_ra_psnr` = 24
- `local_resnet18_teacher_smoke_loss_value` = 0.3541
- `tiny_local_teacher_pilot_bpp_avg` = 88.2266
- `tiny_local_teacher_pilot_psnr_avg` = 10.9012
- `tiny_local_teacher_pilot_teacher_mse_avg` = 0.5126
- `beauty_teacher_smoke_bpp_avg` = 2.091
- `beauty_teacher_smoke_psnr_avg` = 14.9552
- `beauty_teacher_smoke_teacher_mse_avg` = 0.0363
- `beauty_no_teacher_partial_teacher_mse` = 0.0472
- `teacher_gallery_anchor_joint_to_target_feat_top1_accuracy` = 0.75
- `teacher_gallery_anchor_joint_to_target_feat_mean_match_rank` = 1.5
- `pred_feat_to_target_feat_top1_accuracy` = 0.25
- `pred_feat_plus_8p0x_delta_concat_to_target_feat_plus_8p0x_delta_concat_top1_accuracy` = 0.75
- `pred_delta_to_target_delta_top1_accuracy` = 0.75

## Baseline Comparison

- `uvg_bd_rate_reduction_pct_vs_vtm_ra_psnr`: run=24 baseline=24 delta=0 (worse)
- `local_resnet18_teacher_smoke_loss_value`: run=0.3541 baseline=0.3541 delta=0 (worse)
- `tiny_local_teacher_pilot_bpp_avg`: run=88.2266 baseline=88.2109 delta=0.0157 (worse)
- `tiny_local_teacher_pilot_psnr_avg`: run=10.9012 baseline=10.8996 delta=0.0016 (better)
- `tiny_local_teacher_pilot_teacher_mse_avg`: run=0.5126 baseline=0.5145 delta=-0.0019 (better)
- `beauty_teacher_smoke_bpp_avg`: run=2.091 baseline=2.091 delta=0 (worse)
- `beauty_teacher_smoke_psnr_avg`: run=14.9552 baseline=14.9552 delta=0 (worse)
- `beauty_teacher_smoke_teacher_mse_avg`: run=0.0363 baseline=0.0363 delta=0 (worse)
- `beauty_no_teacher_partial_teacher_mse`: run=0.0472 baseline=0.0472 delta=0 (worse)
- `teacher_gallery_anchor_joint_to_target_feat_top1_accuracy`: run=0.75 baseline=None delta=n/a (not comparable)
- `teacher_gallery_anchor_joint_to_target_feat_mean_match_rank`: run=1.5 baseline=None delta=n/a (not comparable)
- `pred_feat_to_target_feat_top1_accuracy`: run=0.25 baseline=None delta=n/a (not comparable)
- `pred_feat_plus_8p0x_delta_concat_to_target_feat_plus_8p0x_delta_concat_top1_accuracy`: run=0.75 baseline=None delta=n/a (not comparable)
- `pred_delta_to_target_delta_top1_accuracy`: run=0.75 baseline=None delta=n/a (not comparable)

## Changed Files

- `PLAN.md`
- `CHECKLIST.md`
- `status.md`
- `experiments/main/scripts/run_teacher_anchor_packet_eval.py`
- `experiments/main/scripts/run_teacher_anchor_packet_adapter_smoke.sh`
- `experiments/main/evals/teacher_anchor_packet_adapter_smoke_r1/summary.json`
- `experiments/main/evals/teacher_anchor_packet_adapter_smoke_r1/report.md`
- `experiments/main/evals/teacher_anchor_packet_adapter_smoke_r1/teacher_gallery_anchor_weights.csv`

## Evidence Paths

- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/teacher-anchored-packet-adapter-smoke-r1/experiments/main/evals/teacher_anchor_packet_adapter_smoke_r1/summary.json`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/teacher-anchored-packet-adapter-smoke-r1/experiments/main/evals/teacher_anchor_packet_adapter_smoke_r1/report.md`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/teacher-anchored-packet-adapter-smoke-r1/experiments/main/evals/teacher_anchor_packet_adapter_smoke_r1/teacher_gallery_anchor_weights.csv`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/teacher-anchored-packet-adapter-smoke-r1/experiments/main/scripts/run_teacher_anchor_packet_eval.py`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/teacher-anchored-packet-adapter-smoke-r1/experiments/main/scripts/run_teacher_anchor_packet_adapter_smoke.sh`

## Notes

- Main caveat: the new adapter is a gallery-memory interface that uses the teacher packet bank at retrieval time; it is not yet a parametric bridge that can run without that memory bank.
- Runtime note: branch/worktree preparation succeeded, but artifact branch activation was inconsistent, so record attachment should be checked against the intended run branch context.

## Evaluation Summary

- Not recorded.

## Delivery Policy

- Research paper required: `True`
- Recommended next route: `revise_idea`
- Reason: Research paper mode is enabled, but the current run does not beat the baseline clearly enough. Revise the direction or strengthen the method before writing.
