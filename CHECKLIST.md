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
- [ ] update `status.md` once the first smoke result exists

## Implementation

- [ ] add predicted-feature variance-floor loss plumbing in `tasks.py`
- [ ] expose variance-floor config fields in `main_utils.py`
- [ ] extend `smoke_teacher_loss.py` with variance-floor arguments and summary output
- [ ] add one reproducible task config for the variance-floor repair
- [ ] add one bounded launcher script for the variance-floor repair

## Smoke Validation

- [ ] run the teacher-loss smoke with variance-floor enabled
- [ ] confirm the smoke summary shows the new variance-floor settings explicitly
- [ ] confirm the smoke summary reports a non-null variance-floor penalty value
- [ ] confirm no unrelated export/eval code changes are required

## Main-Run Gate

- [ ] decide whether the smoke result is clean enough to justify a dedicated `run/*` branch
- [ ] if justified, prepare the bounded main-run package on a dedicated run branch/worktree
- [ ] if not justified, record the blocking issue before retrying anything

## Notes

- locked failure boundary:
  - target packets remain discriminative
  - exported predicted packets remain collapsed
  - earliest accessible collapse surface: `exported_predicted_packets_or_earlier`
- first repair scope:
  - on: predicted-feature variance floor
  - off by default: predicted-delta variance floor
  - unchanged: packet export and packet evaluation contract
