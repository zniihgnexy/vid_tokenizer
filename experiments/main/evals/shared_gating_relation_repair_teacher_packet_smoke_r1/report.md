# Teacher Packet Evaluation

- teacher_type: `resnet18_imagenet`
- feature_dim: `512`
- comparison_preset: `all`
- delta_weight: `1.0`

| Comparison | Top-1 Accuracy | Mean Match Rank | Mean Matching Similarity | Mean Margin vs Best Nonmatch |
|---|---:|---:|---:|---:|
| target_feat_to_target_feat | 1.0000 | 1.0000 | 1.0000 | 0.0139 |
| pred_feat_to_target_feat | 0.0625 | 8.0625 | 0.5972 | -0.0219 |
| pred_delta_to_target_delta | 0.0625 | 7.3125 | 0.0270 | -0.1370 |
| pred_feat_plus_1p0x_delta_concat_to_target_feat_plus_1p0x_delta_concat | 0.0000 | 7.8750 | 0.5778 | -0.0219 |
| pred_feat_plus_1p0x_delta_sum_to_target_feat_plus_1p0x_delta_sum | 0.0625 | 8.1250 | 0.5682 | -0.0390 |
