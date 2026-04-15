# Main Experiment Checklist

Update this while planning, modifying code, running pilots, monitoring the full run, and validating the result.

## Identity

- run id: `delta_packet_bridge_smoke_r1`
- idea id: `idea-e0d17d22`
- stage: `experiment_prep`

## Planning

- [x] selected idea summarized in `1-2` sentences
- [x] parent-line evidence and baseline contract confirmed
- [x] bridge-specific risks listed
- [ ] widened bounded sample surface chosen
- [ ] exact bridge implementation path chosen
- [ ] smoke command written

## Implementation

- [x] packet exporter scaffold identified
- [x] packet evaluator scaffold identified
- [ ] minimal bridge script or extension implemented
- [ ] widened-surface manifest or sample list written
- [ ] risky logic sanity-checked for packet/sample alignment

## Pilot / Smoke

- [ ] widened bridge smoke command executed
- [ ] outputs look valid
- [ ] bridge embeddings or scores align with sample ids
- [ ] comparison against reconstructed-video control is interpretable

## Validation

- [ ] bridge metrics are complete
- [ ] comparison against reconstructed-video control is comparable
- [ ] `delta-only` vs `delta-dominant concat` bridge result is classified as supported / refuted / mixed
- [ ] next action after the smoke is explicit

## Notes

- parent-line downstream control:
  - `reconstructed_to_original_top1_accuracy=0.25`
  - `reconstructed_to_original_mean_match_rank=2.5`
- current packet evidence:
  - `pred_delta_to_target_delta_top1_accuracy=0.75`
  - `pred_feat_plus_8p0x_delta_concat_to_target_feat_plus_8p0x_delta_concat_top1_accuracy=0.75`
  - `pred_feat_plus_8p0x_delta_sum_to_target_feat_plus_8p0x_delta_sum_top1_accuracy=0.5`
- branch meaning:
  - plain static packet is downgraded as a default winner
  - temporal-change packet is the active continuation signal
  - the new experiment must test a consumer-facing bridge, not just another packet-similarity loop
- next unchecked item:
  - choose the widened bounded surface and lock the bridge script path
