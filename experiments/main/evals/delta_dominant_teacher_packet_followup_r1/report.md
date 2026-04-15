# Teacher Packet Evaluation

- teacher_type: `resnet18_imagenet`
- feature_dim: `512`
- comparison_preset: `delta_first`
- delta_weight: `8.0`

| Comparison | Top-1 Accuracy | Mean Match Rank | Mean Matching Similarity | Mean Margin vs Best Nonmatch |
|---|---:|---:|---:|---:|
| target_feat_to_target_feat | 1.0000 | 1.0000 | 1.0000 | 0.0662 |
| pred_delta_to_target_delta | 0.7500 | 1.2500 | 0.0782 | 0.0614 |
| pred_feat_plus_8p0x_delta_concat_to_target_feat_plus_8p0x_delta_concat | 0.7500 | 1.2500 | 0.1585 | 0.0644 |
| pred_feat_plus_8p0x_delta_sum_to_target_feat_plus_8p0x_delta_sum | 0.5000 | 1.5000 | 0.1604 | 0.0638 |
