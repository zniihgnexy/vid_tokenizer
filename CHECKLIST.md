# Main Experiment Checklist

Update this while planning, modifying code, running pilots, monitoring the full run, and validating the result.

## Identity

- run id: `delta_dominant_teacher_packet_followup_r1`
- idea id: `idea-44a0e404`
- stage: `experiment_prep`

## Planning

- [x] selected idea summarized in `1-2` sentences
- [x] parent-line evidence and baseline contract confirmed
- [x] code touchpoints listed
- [x] smoke plan written
- [x] fallback options written

## Implementation

- [x] packet export hook identified
- [x] packet manifest schema written
- [x] intended files modified for delta-first follow-up
- [x] risky logic guarded or sanity-checked for delta-first weighting or gating

## Pilot / Smoke

- [x] delta-first follow-up command executed
- [x] delta-first outputs look valid
- [x] delta-first metadata aligns with sample ids
- [x] delta-first comparison is interpretable

## Validation

- [x] delta-first metrics are complete
- [x] delta-first comparison against reconstructed-video and plain-feature controls is comparable
- [x] delta-first claim is classified as supported / refuted / inconclusive
- [x] next action after the follow-up is explicit

## Notes

- parent-line downstream control:
  - `reconstructed_to_original_top1_accuracy=0.25`
  - `reconstructed_to_original_mean_match_rank=2.5`
- first smoke result:
  - `pred_feat_to_target_feat_top1_accuracy=0.25`
  - `pred_delta_to_target_delta_top1_accuracy=0.75`
  - heavy delta concat (`weight=8.0`) also reaches `top1_accuracy=0.75`
- branch meaning:
  - plain feature packet is downgraded to a rejected sibling control
  - delta-dominant packet is the active continuation line
- formal follow-up result:
  - `pred_delta_to_target_delta_top1_accuracy=0.75`
  - `pred_feat_plus_8p0x_delta_concat_to_target_feat_plus_8p0x_delta_concat_top1_accuracy=0.75`
  - `pred_feat_plus_8p0x_delta_sum_to_target_feat_plus_8p0x_delta_sum_top1_accuracy=0.5`
- next unchecked item: prepare the smallest wider bounded validation package beyond the current 4-frame surface
