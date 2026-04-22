# Teacher Packet Evaluation

- teacher_type: `resnet18_imagenet`
- feature_dim: `512`
- comparison_preset: `all`
- delta_weight: `1.0`

| Comparison | Top-1 Accuracy | Mean Match Rank | Mean Matching Similarity | Mean Margin vs Best Nonmatch |
|---|---:|---:|---:|---:|
| target_feat_to_target_feat | 1.0000 | 1.0000 | 1.0000 | 0.0139 |
| pred_feat_to_target_feat | 0.0625 | 8.2500 | 0.5387 | -0.0205 |
| pred_delta_to_target_delta | 0.1875 | 6.6875 | 0.0339 | -0.0784 |
| pred_feat_plus_1p0x_delta_concat_to_target_feat_plus_1p0x_delta_concat | 0.0625 | 8.1875 | 0.5273 | -0.0215 |
| pred_feat_plus_1p0x_delta_sum_to_target_feat_plus_1p0x_delta_sum | 0.0625 | 7.7500 | 0.5195 | -0.0428 |
