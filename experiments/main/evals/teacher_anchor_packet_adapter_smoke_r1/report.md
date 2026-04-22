# Teacher Gallery-Anchor Packet Evaluation

- teacher_type: `resnet18_imagenet`
- feature_dim: `512`
- delta_weight: `8.0`
- anchor_logit_scale: `16.0`

| Comparison | Top-1 Accuracy | Mean Match Rank | Mean Matching Similarity | Mean Margin vs Best Nonmatch |
|---|---:|---:|---:|---:|
| target_feat_to_target_feat | 1.0000 | 1.0000 | 1.0000 | 0.0662 |
| pred_feat_to_target_feat | 0.2500 | 2.5000 | 0.6805 | -0.0685 |
| pred_delta_to_target_delta | 0.7500 | 1.2500 | 0.0782 | 0.0614 |
| pred_feat_plus_8p0x_delta_concat_to_target_feat_plus_8p0x_delta_concat | 0.7500 | 1.2500 | 0.1585 | 0.0644 |
| teacher_gallery_anchor_joint_to_target_feat | 0.7500 | 1.5000 | 0.9751 | 0.0084 |

## Notes

- `teacher_gallery_anchor_joint_to_target_feat` uses the teacher packet gallery as a retrieval-time memory bank.
- Query keys are built from `pred_feat + delta_weight * pred_delta`.
- Anchor keys are built from `target_feat + delta_weight * target_delta`.
- Anchor values are normalized `target_feat` vectors, so the adapter explicitly projects into target feature space.