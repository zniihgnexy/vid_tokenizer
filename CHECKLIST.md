# Main Experiment Checklist

Update this while planning, modifying code, running pilots, monitoring the full run, and validating the result.

## Identity

- run id: `shared_gating_downstream_interface_bootstrap_r1`
- idea id: `idea-3ed587d5`
- stage: `experiment_prep`

## Planning

- [x] selected idea summarized in `1-2` sentences
- [x] baseline and comparability contract confirmed
- [x] code touchpoints listed
- [x] smoke plan written
- [x] full run plan written
- [x] fallback options written

## Implementation

- [x] intended files modified
- [x] unrelated changes avoided or justified
- [x] risky logic guarded or sanity-checked
- [x] plan updated if the implementation route changed

## Pilot / Smoke

- [x] smoke command executed
- [x] outputs look valid
- [x] metrics / logs are interpretable
- [x] comparability still holds

## Main Run

- [ ] real downstream consumer run launched
- [ ] monitoring cadence started
- [ ] health signals confirmed
- [ ] major runtime deviations reflected in `PLAN.md`

## Validation

- [x] upstream interface outputs exist
- [x] upstream interface metrics are complete
- [x] frozen-upstream comparability holds
- [ ] downstream main claim is classified as supported / refuted / inconclusive
- [ ] result recorded durably

## Closeout

- [ ] main experiment summarized in `1-2` sentences
- [ ] next action is explicit

## Notes

- validated interface bundle: `experiments/main/interface_bundles/shared_gating_interface_export_smoke_r1/`
- next unchecked item: implement and smoke `experiments/main/scripts/run_frozen_consumer_eval.py`
