# Query Collapse Localization

- mode: `smoke`
- chunk_count: `4`
- frame_count_per_chunk: `4`
- chance_top1: `0.2500`
- bundle_dirs:
  - `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-e0d17d22/experiments/main/interface_bundles/shared_gating_ego4d16f_teacher_packet_ego4d_small_bridge_16f_chunk00_smoke_r1`
  - `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-e0d17d22/experiments/main/interface_bundles/shared_gating_ego4d16f_teacher_packet_ego4d_small_bridge_16f_chunk01_smoke_r1`
  - `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-e0d17d22/experiments/main/interface_bundles/shared_gating_ego4d16f_teacher_packet_ego4d_small_bridge_16f_chunk02_smoke_r1`
  - `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-e0d17d22/experiments/main/interface_bundles/shared_gating_ego4d16f_teacher_packet_ego4d_small_bridge_16f_chunk03_smoke_r1`

## Accessible Surfaces

- accessible:
  - `target_feat`
  - `target_delta`
  - `pred_feat`
  - `pred_delta`
- missing:
  - `query_projection`
  - `query_packet_head`

## Self-Surface Discrimination

| Surface | Top-1 | Mean Rank | Offdiag Mean Cosine | Raw Mean Dim Var | Collapsed |
|---|---:|---:|---:|---:|---|
| target_feat_to_target_feat_seq_concat | 1.0000 | 1.0000 | 0.9432 | 0.032772 | False |
| target_feat_to_target_feat_frame_mean | 1.0000 | 1.0000 | 0.9618 | 0.021935 | False |
| target_delta_to_target_delta_seq_concat | 1.0000 | 1.0000 | -0.0218 | 0.020314 | False |
| target_delta_to_target_delta_frame_mean | 1.0000 | 1.0000 | -0.1100 | 0.006541 | False |
| pred_feat_to_pred_feat_seq_concat | 0.2500 | 2.5000 | 1.0000 | 0.000000 | True |
| pred_feat_to_pred_feat_frame_mean | 0.2500 | 2.5000 | 1.0000 | 0.000000 | True |
| pred_delta_to_pred_delta_seq_concat | 0.2500 | 2.5000 | 1.0000 | 0.000000 | True |
| pred_delta_to_pred_delta_frame_mean | 0.2500 | 2.5000 | 1.0000 | 0.000000 | True |

## Cross-Surface Comparisons

| Comparison | Top-1 | Mean Rank | Offdiag Mean Cosine | Mean Margin |
|---|---:|---:|---:|---:|
| pred_feat_to_target_feat_seq_concat | 0.2500 | 2.5000 | 0.5805 | -0.0052 |
| pred_feat_to_target_feat_frame_mean | 0.2500 | 2.5000 | 0.5947 | -0.0033 |
| pred_delta_to_target_delta_seq_concat | 0.2500 | 2.5000 | 0.0018 | -0.0522 |
| pred_delta_to_target_delta_frame_mean | 0.2500 | 2.5000 | -0.0343 | -0.0334 |
| pred_delta_to_target_feat_seq_concat | 0.2500 | 2.5000 | -0.0481 | -0.0061 |
| pred_delta_to_target_feat_frame_mean | 0.2500 | 2.5000 | -0.1471 | -0.0074 |

## Localization Judgment

- earliest_accessible_collapse_surface: `exported_predicted_packets_or_earlier`
- predicted_packet_surface_collapsed: `True`
- target_surface_discriminative: `True`
- recommendation: Exported predicted packets are already collapsed while target packets remain discriminative. If deeper query-side projections are inaccessible, treat exported predicted packets as the earliest accessible collapse surface and test at most one minimal repair that acts on the query head or predictor.
