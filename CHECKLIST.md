# Main Experiment Checklist

Update this while interpreting the blueprint result, downgrading it honestly, and validating the next relation-based repair.

## Identity

- run id: `shared_gating_relation_semchange_delta_smoke_r1`
- idea id: `idea-c5e88710`
- stage: `experiment_prep`

## Planning

- [x] localization evidence interpreted
- [x] earliest accessible collapse surface made explicit
- [x] exactly one first repair family selected
- [x] first repair family executed and interpreted
- [x] first repair family downgraded explicitly when the evidence weakened it
- [x] baseline and comparison contract kept stable
- [x] next nearby repair family selected

## Implementation

- [x] localization entrypoint written
- [x] localization result package generated
- [x] blueprint repair config added
- [x] blueprint teacher-loss smoke executed
- [x] bounded blueprint repair run executed
- [x] repaired teacher-packet bundle exported
- [x] repaired single-bundle teacher-packet evaluation generated
- [ ] relation repair config added
- [ ] relation teacher-loss smoke executed

## Validation

- [x] target packet discrimination remains explicit after the blueprint repair
- [x] blueprint repair result shows target-alignment is still unresolved
- [x] blueprint downgrade is explicit
- [ ] relation repair path validates cleanly
- [ ] at least one relation-based predicted-to-target packet comparison beats the current blueprint result
- [ ] downgrade the packet-bridge line again if relation still leaves target alignment near chance

## Notes

- locked localization result:
  - `target_feat_to_target_feat_seq_concat_top1_accuracy=1.0`
  - `target_delta_to_target_delta_seq_concat_top1_accuracy=1.0`
  - `pred_feat_to_pred_feat_seq_concat_top1_accuracy=0.25`
  - `pred_delta_to_pred_delta_seq_concat_top1_accuracy=0.25`
  - `pred_feat` and `pred_delta` cross-chunk cosine matrices are all `1.0`
  - `pred_feat` and `pred_delta` raw mean dimension variance are both `0.0`
- bounded blueprint repair aggregate metrics:
  - `bpp_avg=23.8984`
  - `psnr_avg=10.6733`
  - `teacher-mse_avg=0.5481`
- bounded blueprint single-bundle packet evaluation:
  - `target_feat_to_target_feat_top1_accuracy=1.0`
  - `pred_feat_to_target_feat_top1_accuracy=0.0625`
  - `pred_delta_to_target_delta_top1_accuracy=0.1875`
  - `pred_delta_to_target_delta_mean_margin_vs_best_nonmatch=-0.0784`
- bounded blueprint self checks:
  - `pred_feat_self_top1=1.0`, `offdiag_mean=0.9947`, `raw_mean_dim_var=0.274643`
  - `pred_delta_self_top1=0.9375`, `offdiag_mean=-0.0543`, `raw_mean_dim_var=0.000028`
- downgrade interpretation:
  - blueprint recovered some self-discrimination but not usable predicted-to-target alignment
- chosen next repair:
  - `teacher_relation_consistency`
- next unchecked item:
  - add the relation repair config and validate it with the lightweight smoke
