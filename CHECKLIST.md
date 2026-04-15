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
- [ ] intended files modified for delta-first follow-up
- [ ] risky logic guarded or sanity-checked for delta-first weighting or gating

## Pilot / Smoke

- [ ] delta-first follow-up command executed
- [ ] delta-first outputs look valid
- [ ] delta-first metadata aligns with sample ids
- [ ] delta-first comparison is interpretable

## Validation

- [ ] delta-first metrics are complete
- [ ] delta-first comparison against reconstructed-video and plain-feature controls is comparable
- [ ] delta-first claim is classified as supported / refuted / inconclusive
- [ ] next action after the follow-up is explicit

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
- next unchecked item: prepare and run the first delta-first follow-up package
