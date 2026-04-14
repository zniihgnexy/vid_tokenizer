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

- [ ] packet export hook identified
- [ ] packet manifest schema written
- [ ] intended files modified
- [ ] risky logic guarded or sanity-checked

## Pilot / Smoke

- [ ] packet smoke command executed
- [ ] packet outputs look valid
- [ ] packet metadata aligns with sample ids
- [ ] downstream comparison is interpretable

## Validation

- [ ] packet-side metrics are complete
- [ ] packet-side comparison against reconstructed-video control is comparable
- [ ] main claim is classified as supported / refuted / inconclusive
- [ ] next action is explicit

## Notes

- parent-line downstream control:
  - `reconstructed_to_original_top1_accuracy=0.25`
  - `reconstructed_to_original_mean_match_rank=2.5`
- next unchecked item: inspect the frozen upstream code for the first clean teacher/tokenizer packet export hook
