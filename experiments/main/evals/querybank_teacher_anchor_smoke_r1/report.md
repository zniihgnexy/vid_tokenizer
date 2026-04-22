# Querybank Teacher-Anchor Packet Evaluation

- teacher_type: `resnet18_imagenet`
- feature_dim: `512`
- bundle_count: `4`
- delta_weight: `8.0`
- anchor_logit_scale: `16.0`
- csls_k: `3`
- bundle_dirs:
  - `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-e0d17d22/experiments/main/interface_bundles/shared_gating_ego4d16f_teacher_packet_ego4d_small_bridge_16f_chunk00_smoke_r1`
  - `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-e0d17d22/experiments/main/interface_bundles/shared_gating_ego4d16f_teacher_packet_ego4d_small_bridge_16f_chunk01_smoke_r1`
  - `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-e0d17d22/experiments/main/interface_bundles/shared_gating_ego4d16f_teacher_packet_ego4d_small_bridge_16f_chunk02_smoke_r1`
  - `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-e0d17d22/experiments/main/interface_bundles/shared_gating_ego4d16f_teacher_packet_ego4d_small_bridge_16f_chunk03_smoke_r1`

| Comparison | Top-1 Accuracy | Mean Match Rank | Mean Margin | Unique Top-1 Anchors | Max Anchor Share | Hub Cluster Share | Mean Hub Weight Mass |
|---|---:|---:|---:|---:|---:|---:|---:|
| csls_teacher_anchor_to_target_feat | 0.1875 | 2.5000 | -0.0052 | 4 | 0.5000 | 0.0000 | 0.0000 |
| dis_teacher_anchor_to_target_feat | 0.3125 | 2.2500 | -0.0035 | 4 | 0.3750 | 0.0000 | 0.0000 |
| pred_delta_to_target_delta | 0.1875 | 2.5000 | -0.0526 | - | - | - | - |
| pred_feat_plus_8p0x_delta_concat_to_target_feat_plus_8p0x_delta_concat | 0.1875 | 2.6250 | -0.0450 | - | - | - | - |
| pred_feat_to_target_feat | 0.2500 | 2.5000 | -0.0140 | - | - | - | - |
| qb_norm_teacher_anchor_to_target_feat | 0.3750 | 2.1250 | -0.0065 | 4 | 0.3125 | 0.0000 | 0.0000 |
| raw_global_bank_to_target_feat | 0.2500 | 2.5000 | -0.0053 | 4 | 0.5000 | 0.0000 | 0.0000 |
| target_feat_to_target_feat | 1.0000 | 1.0000 | 0.0154 | - | - | - | - |

## Notes

- `raw_global_bank_to_target_feat` is the current widened failure reference.
- `qb_norm_teacher_anchor_to_target_feat` is the headline route for this smoke.
- `dis_teacher_anchor_to_target_feat` keeps the Dynamic Inverted Softmax sibling visible inside the same bounded pass.
- `csls_teacher_anchor_to_target_feat` is the classical local-scaling control.
- Hub-cluster diagnostics use anchors `0009`, `0010`, and `0011`.