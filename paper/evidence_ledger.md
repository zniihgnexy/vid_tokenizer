# Paper Evidence Ledger

- Selected outline: `outline-002`
- Item count: `4`
- Updated at: `2026-04-17T20:57:25+00:00`

| Item | Kind | Section | Role | Status | Metrics | Source |
|---|---|---|---|---|---|---|
| `shared_gating_pred_variance_repair_ego4d16f_smoke_r1` | main_experiment | main-results | main_text | completed | uvg_bd_rate_reduction_pct_vs_vtm_ra_psnr=24; local_resnet18_teacher_smoke_loss_value=0.3541; tiny_local_teacher_pilot_bpp_avg=88.2109; tiny_local_teacher_pilot_psnr_avg=10.8996; tiny_local_teacher_pilot_teacher_mse_avg=0.5145; beauty_teacher_smoke_bpp_avg=2.091 | `.ds/worktrees/shared-gating-pred-variance-repair-ego4d16f-smoke-r1/experiments/main/shared_gating_pred_variance_repair_ego4d16f_smoke_r1/RUN.md`, `.ds/worktrees/shared-gating-pred-variance-repair-ego4d16f-smoke-r1/experiments/main/shared_gating_pred_variance_repair_ego4d16f_smoke_r1/RESULT.json` |
| `shared_gating_relation_semchange_delta_smoke_r1` | main_experiment | main-results | main_text | completed | uvg_bd_rate_reduction_pct_vs_vtm_ra_psnr=24; local_resnet18_teacher_smoke_loss_value=0.4067; tiny_local_teacher_pilot_bpp_avg=88.2109; tiny_local_teacher_pilot_psnr_avg=10.8996; tiny_local_teacher_pilot_teacher_mse_avg=0.5145; beauty_teacher_smoke_bpp_avg=2.091 | `.ds/worktrees/shared-gating-relation-semchange-delta-smoke-r1/experiments/main/shared_gating_relation_semchange_delta_smoke_r1/RUN.md`, `.ds/worktrees/shared-gating-relation-semchange-delta-smoke-r1/experiments/main/shared_gating_relation_semchange_delta_smoke_r1/RESULT.json` |
| `teacher_anchored_packet_adapter_smoke_r1` | main_experiment | main-results | main_text | completed | uvg_bd_rate_reduction_pct_vs_vtm_ra_psnr=24; local_resnet18_teacher_smoke_loss_value=0.3541; tiny_local_teacher_pilot_bpp_avg=88.2266; tiny_local_teacher_pilot_psnr_avg=10.9012; tiny_local_teacher_pilot_teacher_mse_avg=0.5126; beauty_teacher_smoke_bpp_avg=2.091 | `.ds/worktrees/teacher-anchored-packet-adapter-smoke-r1/experiments/main/teacher_anchored_packet_adapter_smoke_r1/RUN.md`, `.ds/worktrees/teacher-anchored-packet-adapter-smoke-r1/experiments/main/teacher_anchored_packet_adapter_smoke_r1/RESULT.json` |
| `AC-01` | analysis_slice | sec_teacher_anchor_adapter | appendix | completed | raw_global_bank_to_target_feat.top1_accuracy=0.0625; qb_norm_teacher_anchor_to_target_feat.top1_accuracy=0.0625; dis_teacher_anchor_to_target_feat.top1_accuracy=0.0625; csls_teacher_anchor_to_target_feat.top1_accuracy=0; raw_global_bank_to_target_feat.max_top1_anchor_share=0.5; qb_norm_teacher_anchor_to_target_feat.max_top1_anchor_share=0.25 | `.ds/worktrees/analysis-analysis-8e2b0428-chunked-16f-qbnorm-revalidation/experiments/analysis/analysis-8e2b0428/chunked_16f_qbnorm_revalidation/RESULT.md`, `.ds/worktrees/analysis-analysis-8e2b0428-chunked-16f-qbnorm-revalidation/experiments/analysis/analysis-8e2b0428/chunked_16f_qbnorm_revalidation/RESULT.json` |

## shared_gating_pred_variance_repair_ego4d16f_smoke_r1

- Title: Shared-gating predicted variance-floor repair on frozen widened bridge surface
- Kind: `main_experiment`
- Section: `main-results`
- Role: `main_text`
- Status: `completed`
- Claims: none

### Setup

Dedicated run branch/worktree on the active idea line. Resume root: shared_gating_interface_export_ego4d16f_chunk00_smoke_r1. Task config keeps semantic-change weighting and temporal-delta consistency enabled, turns on predicted-feature variance floor with weight=1.0 and margin=0.1, and keeps predicted-delta variance floor off. The external packet export/eval surface stays fixed to the same bounded ego4d_small_bridge_16f bridge subset.

### Result Summary

{"output_dir":"/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/shared-gating-pred-variance-repair-ego4d16f-smoke-r1/experiments/main/shared_gating_pred_variance_repair_ego4d16f_smoke_r1","archived_invalid_attempt_reason":"missing create_overfit_task passthrough kept pred_variance_weight at 0.0","corrected_run_session":"bash-9cf7c4a3","archived_invalid_run_session":"bash-4cf72434"}

### Source Paths

- `.ds/worktrees/shared-gating-pred-variance-repair-ego4d16f-smoke-r1/experiments/main/shared_gating_pred_variance_repair_ego4d16f_smoke_r1/RUN.md`
- `.ds/worktrees/shared-gating-pred-variance-repair-ego4d16f-smoke-r1/experiments/main/shared_gating_pred_variance_repair_ego4d16f_smoke_r1/RESULT.json`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/shared-gating-pred-variance-repair-ego4d16f-smoke-r1/experiments/main/shared_gating_pred_variance_repair_ego4d16f_smoke_r1`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/shared-gating-pred-variance-repair-ego4d16f-smoke-r1/experiments/main/shared_gating_pred_variance_repair_ego4d16f_smoke_r1/results/all.txt`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/shared-gating-pred-variance-repair-ego4d16f-smoke-r1/experiments/main/shared_gating_pred_variance_repair_ego4d16f_smoke_r1/args.yaml`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/bash_exec/bash-9cf7c4a3/terminal.log`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/bash_exec/bash-4cf72434/terminal.log`

## shared_gating_relation_semchange_delta_smoke_r1

- Title: Shared-gating relation repair on frozen widened bridge surface
- Kind: `main_experiment`
- Section: `main-results`
- Role: `main_text`
- Status: `completed`
- Claims: none

### Setup

Frozen widened bounded bridge surface using ego4d_small_bridge_16f (16 frames at 32x32), shared-gating initialization resumed from shared_gating_interface_export_ego4d16f_chunk00_smoke_r1, relation+semantic-change+temporal-delta task config l1_teacher-resnet18-relation-semchange-delta.yaml, dedicated run wrapper experiments/main/scripts/run_shared_gating_relation_repair_smoke.sh.

### Result Summary

The bounded relation repair run completed successfully and produced a full checkpoint, bitstream, decoded outputs, and downstream packet bundle. Upstream aggregate metrics improved teacher consistency relative to blueprint (teacher-mse_avg 0.4888 vs 0.5481) while keeping similar bitrate (bpp_avg 23.9043 vs 23.8984). However, the downstream interface claim did not improve: pred_feat_to_target_feat top1 stayed at 0.0625, pred_delta_to_target_delta top1 regressed from 0.1875 to 0.0625, and the concat feature+delta comparison fell to 0.0 top1. Mean feature cosine improved (0.5972 vs 0.5387) but mean matching margins remained negative across all predicted-to-target comparisons.

### Source Paths

- `.ds/worktrees/shared-gating-relation-semchange-delta-smoke-r1/experiments/main/shared_gating_relation_semchange_delta_smoke_r1/RUN.md`
- `.ds/worktrees/shared-gating-relation-semchange-delta-smoke-r1/experiments/main/shared_gating_relation_semchange_delta_smoke_r1/RESULT.json`
- `experiments/main/evals/shared_gating_relation_teacher_loss_smoke_r1/summary.json`
- `experiments/main/shared_gating_relation_repair_ego4d16f_smoke_r1/results/all.txt`
- `experiments/main/shared_gating_relation_repair_ego4d16f_smoke_r1/args.yaml`
- `experiments/main/interface_bundles/shared_gating_relation_repair_teacher_packet_smoke_r1`
- `experiments/main/evals/shared_gating_relation_repair_teacher_packet_smoke_r1/summary.json`

## teacher_anchored_packet_adapter_smoke_r1

- Title: Teacher gallery-anchor packet adapter smoke on the local 4-frame bundle
- Kind: `main_experiment`
- Section: `main-results`
- Role: `main_text`
- Status: `completed`
- Claims: none

### Setup

Dedicated run branch/worktree: run/teacher_anchored_packet_adapter_smoke_r1. Reused experiments/main/interface_bundles/shared_gating_teacher_packet_smoke_r1 with 4 bounded frames, teacher_type resnet18_imagenet, packet fields pred_feat/target_feat/pred_delta/target_delta, delta_weight=8.0, and anchor_logit_scale=16.0. No upstream retraining or exporter schema change was introduced in this pass.

### Result Summary

Headline packet-interface result: teacher_gallery_anchor_joint_to_target_feat achieved top-1 accuracy 0.75 and mean match rank 1.5 in target_feat space, versus only 0.25 and 2.5 for the direct pred_feat -> target_feat control. The remaining failure case is query 0000 collapsing toward 0001; queries 0001, 0002, and 0003 are correct.

### Source Paths

- `.ds/worktrees/teacher-anchored-packet-adapter-smoke-r1/experiments/main/teacher_anchored_packet_adapter_smoke_r1/RUN.md`
- `.ds/worktrees/teacher-anchored-packet-adapter-smoke-r1/experiments/main/teacher_anchored_packet_adapter_smoke_r1/RESULT.json`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/teacher-anchored-packet-adapter-smoke-r1/experiments/main/evals/teacher_anchor_packet_adapter_smoke_r1/summary.json`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/teacher-anchored-packet-adapter-smoke-r1/experiments/main/evals/teacher_anchor_packet_adapter_smoke_r1/report.md`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/teacher-anchored-packet-adapter-smoke-r1/experiments/main/evals/teacher_anchor_packet_adapter_smoke_r1/teacher_gallery_anchor_weights.csv`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/teacher-anchored-packet-adapter-smoke-r1/experiments/main/scripts/run_teacher_anchor_packet_eval.py`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/teacher-anchored-packet-adapter-smoke-r1/experiments/main/scripts/run_teacher_anchor_packet_adapter_smoke.sh`

## AC-01

- Title: Chunked 16-frame QB-Norm Revalidation
- Kind: `analysis_slice`
- Section: `sec_teacher_anchor_adapter`
- Role: `appendix`
- Status: `completed`
- Claims: teacher_anchor_adapter_stability, querybank_route_validation

### Setup

Used the existing chunked 16-frame teacher-packet bundle that had already been exported earlier. No retraining, dataset change, teacher change, or new bundle export was introduced for this slice; the goal was a pure wider-surface robustness check of the current teacher-anchor packet evaluator.

### Result Summary

The wider-surface slice weakened the earlier narrow-smoke retrieval claim. Raw, QB-Norm, and DIS all reached top-1 accuracy 0.0625 on the chunked 16-frame bundle, while CSLS was 0.0. QB-Norm still materially regularized anchor geometry: it reduced max top-1 anchor share from 0.50 to 0.25, increased unique top-1 anchors from 3 to 4, and reduced mean hub weight mass from 0.2109 to 0.1547 versus raw. However, QB-Norm also showed a non-zero 0009/0010/0011 hub-cluster share of 0.25, so the previous interpretation must be downgraded from stable retrieval rescue to partial geometric repair.

### Source Paths

- `.ds/worktrees/analysis-analysis-8e2b0428-chunked-16f-qbnorm-revalidation/experiments/analysis/analysis-8e2b0428/chunked_16f_qbnorm_revalidation/RESULT.md`
- `.ds/worktrees/analysis-analysis-8e2b0428-chunked-16f-qbnorm-revalidation/experiments/analysis/analysis-8e2b0428/chunked_16f_qbnorm_revalidation/RESULT.json`
- `.ds/worktrees/querybank-teacher-anchor-smoke-r1/experiments/analysis-results/analysis-8e2b0428/chunked_16f_qbnorm_revalidation.md`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/querybank-teacher-anchor-smoke-r1/experiments/analysis/chunked_16f_qbnorm_revalidation/summary.json`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/querybank-teacher-anchor-smoke-r1/experiments/analysis/chunked_16f_qbnorm_revalidation/report.md`
