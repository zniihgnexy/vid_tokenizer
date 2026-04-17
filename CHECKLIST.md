# Main Experiment Checklist

Update this while implementing, smoke-testing, and deciding whether to launch
the bounded main run for the variance-floor repair.

## Identity

- idea id: `idea-2835dace`
- stage: `experiment`

## Preconditions

- [x] confirm the accepted baseline contract is still `nvrc-local-source`
- [x] confirm the active anti-collapse idea remains the selected route
- [x] confirm this pass keeps the current frozen export/eval surface unchanged
- [x] confirm `pred_feat` is the primary intervention surface for the first repair

## Control Files

- [x] convert `PLAN.md` from idea framing to main-experiment framing
- [x] convert `CHECKLIST.md` to experiment execution tracking
- [x] update `status.md` once the corrected bounded main-run result exists

## Implementation

- [x] add predicted-feature variance-floor loss plumbing in `tasks.py`
- [x] expose variance-floor config fields in `main_utils.py`
- [x] extend `smoke_teacher_loss.py` with variance-floor arguments and summary output
- [x] add one reproducible task config for the variance-floor repair
- [x] add one bounded launcher script for the variance-floor repair

## Smoke Validation

- [x] run the teacher-loss smoke with variance-floor enabled
- [x] confirm the smoke summary shows the new variance-floor settings explicitly
- [x] confirm the smoke summary reports a non-null variance-floor penalty value
- [x] confirm no unrelated export/eval code changes are required

## Main-Run Gate

- [x] decide whether the smoke result is clean enough to justify a dedicated `run/*` branch
- [x] if justified, prepare the bounded main-run package on a dedicated run branch/worktree
- [x] archive the first invalid bounded run after the missing task-construction passthrough was exposed
- [x] rerun the bounded main experiment after fixing the missing passthrough
- [ ] record the corrected bounded run durably with the real metric trade-off
- [ ] route the next step through an explicit post-result decision

## Notes

- locked failure boundary:
  - target packets remain discriminative
  - exported predicted packets remain collapsed
  - earliest accessible collapse surface: `exported_predicted_packets_or_earlier`
- first repair scope:
  - on: predicted-feature variance floor
  - off by default: predicted-delta variance floor
  - unchanged: packet export and packet evaluation contract
- corrected bounded main-run headline:
  - active regularizer in logs: `pred_variance_weight=1.0`
  - `teacher-mse_avg=0.4821` vs invalid first run `0.4888`
  - `bpp_avg=23.9277` vs invalid first run `23.8555`
  - `psnr_avg=10.4509` vs invalid first run `10.4642`
