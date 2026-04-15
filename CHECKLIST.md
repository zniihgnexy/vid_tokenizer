# Main Experiment Checklist

Update this while planning, modifying code, running pilots, monitoring the full run, and validating the result.

## Identity

- run id: `teacher_feature_packet_interface_bootstrap_r1`
- idea id: `idea-301dcd71`
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
- [x] intended files modified
- [x] risky logic guarded or sanity-checked

## Pilot / Smoke

- [x] packet smoke command executed
- [x] packet outputs look valid
- [x] packet metadata aligns with sample ids
- [x] downstream comparison is interpretable

## Validation

- [x] packet-side metrics are complete
- [x] packet-side comparison against reconstructed-video control is comparable
- [x] main claim is classified as supported / refuted / inconclusive
- [x] next action is explicit

## Notes

- parent-line downstream control:
  - `reconstructed_to_original_top1_accuracy=0.25`
  - `reconstructed_to_original_mean_match_rank=2.5`
- first smoke result:
  - `pred_feat_to_target_feat_top1_accuracy=0.25`
  - `pred_delta_to_target_delta_top1_accuracy=0.75`
  - heavy delta concat (`weight=8.0`) also reaches `top1_accuracy=0.75`
- next unchecked item: record the delta-dominant packet decision and prepare the first delta-first follow-up package
