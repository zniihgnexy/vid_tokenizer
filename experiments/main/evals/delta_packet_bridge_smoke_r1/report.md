# Delta Packet Bridge Evaluation

- teacher_type: `resnet18_imagenet`
- feature_dim: `512`
- delta_weight: `8.0`
- ridge_lambda: `1.0`

| Comparison | Top-1 Accuracy | Mean Match Rank | Mean Matching Similarity | Mean Margin vs Best Nonmatch |
|---|---:|---:|---:|---:|
| pred_feat_to_target_feat_direct | 0.2500 | 2.5000 | 0.6805 | -0.0685 |
| pred_delta_to_target_feat_direct | 0.5000 | 2.0000 | -0.1356 | -0.0052 |
| delta_ridge_to_target_feat_loo | 0.0000 | 3.2500 | 0.8249 | -0.1509 |
| feat_plus_8p0x_delta_ridge_to_target_feat_loo | 0.0000 | 3.2500 | 0.8249 | -0.1424 |
| target_feat_to_target_feat | 1.0000 | 1.0000 | 1.0000 | 0.0662 |

## Notes

- `pred_feat_to_target_feat_direct` is the bridge-free control in the frozen consumer feature space.
- `pred_delta_to_target_feat_direct` measures whether delta is already aligned without any learned bridge.
- `delta_ridge_to_target_feat_loo` uses a leave-one-out ridge adapter from `pred_delta` into the consumer feature space.
- `feat_plus_delta_ridge_to_target_feat_loo` uses the same leave-one-out ridge bridge but with concatenated static plus weighted delta input.