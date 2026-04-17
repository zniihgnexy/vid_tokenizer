# Querybank-Normalized Teacher-Anchor Hubness Smoke Checklist

Update this while preparing, implementing, and validating the bounded
`16`-frame hubness smoke.

## Identity

- idea id: `idea-e313b721`
- planned run id: `querybank_teacher_anchor_smoke_r1`
- stage: `experiment`

## Preconditions

- [x] confirm the accepted baseline contract is still `nvrc-local-source`
- [x] confirm the active route is the querybank-normalized teacher-anchor line
- [x] confirm the widened failure is currently diagnosed as retrieval-time hub
  collapse
- [x] confirm the four frozen `16`-frame packet bundle chunks already exist in
  the prior collapse-diagnosis outputs
- [x] confirm the current evaluator entrypoint is
  `experiments/main/scripts/run_teacher_anchor_packet_eval.py`

## Run Contract

- [x] rewrite the quest `plan.md` around the querybank-normalized line
- [x] rewrite the quest `status.md` and `SUMMARY.md` around the same line
- [x] rewrite the workspace `PLAN.md` and `CHECKLIST.md`
- [x] lock the bounded comparison table to raw global-bank, QB-Norm, DIS, and
  CSLS
- [x] lock the first success threshold to beating raw top-1 `0.125` while
  reducing hub concentration on `0009/0010/0011`
- [ ] prepare the dedicated run branch/worktree for
  `querybank_teacher_anchor_smoke_r1`

## Implementation

- [ ] decide whether to extend `run_teacher_anchor_packet_eval.py` directly or
  wrap it with a multi-chunk driver
- [ ] add raw global-bank, QB-Norm, DIS, and CSLS scoring modes
- [ ] export per-mode anchor concentration diagnostics and hub-cluster share
- [ ] add the bounded launcher
  `experiments/main/scripts/run_querybank_teacher_anchor_smoke.sh`

## Smoke Gate

- [ ] run the bounded smoke on the four frozen `16`-frame bundle chunks
- [ ] verify the raw mode reproduces the current weak global-bank behavior
- [ ] verify at least one corrected mode beats raw global-bank top-1
- [ ] inspect whether QB-Norm or DIS actually lowers the
  `0009/0010/0011` hub-cluster share
- [ ] decide whether hard shortlist pruning is still unnecessary after the first
  four-mode comparison

## Durable Recording

- [ ] record the measured result with `artifact.record_main_experiment(...)`
- [ ] write the next route decision from the smoke result
- [ ] update the quest status surfaces with the measured outcome

## Notes

- current raw widened reference:
  - `raw_global_bank_to_target_feat.top1_accuracy = 0.125`
  - main hub cluster: `0009/0010/0011`
- current preferred route:
  - `QB-Norm` is the headline correction
  - `DIS` is the closest sibling fallback
  - `CSLS` is the classical control
  - hard shortlist pruning is optional secondary control only
