# Teacher Packet Evaluation

- teacher_type: `resnet18_imagenet`
- feature_dim: `512`

| Comparison | Top-1 Accuracy | Mean Match Rank | Mean Matching Similarity | Mean Margin vs Best Nonmatch |
|---|---:|---:|---:|---:|
| target_feat_to_target_feat | 1.0000 | 1.0000 | 1.0000 | 0.0662 |
| pred_feat_to_target_feat | 0.2500 | 2.5000 | 0.6805 | -0.0685 |
| pred_delta_to_target_delta | 0.7500 | 1.2500 | 0.0782 | 0.0614 |
| pred_feat_plus_delta_to_target_feat_plus_delta | 0.2500 | 2.0000 | 0.6079 | -0.0243 |
