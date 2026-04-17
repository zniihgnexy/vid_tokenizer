# Packet Adapter Checklist

Update this while converging the new idea line into the first bounded
teacher-anchored packet-adapter experiment package.

## Identity

- idea id: `idea-76fee64d`
- stage: `experiment_prep`

## Preconditions

- [x] confirm the accepted baseline contract is still `nvrc-local-source`
- [x] confirm the active route is the new teacher-anchored packet-adapter line
- [x] confirm the first package stays on the same tiny-local `4`-frame surface
- [x] confirm the current packet bundle schema already exposes packet paths, metrics, and teacher packet summary

## Control Files

- [x] rewrite `PLAN.md` around the packet-adapter route instead of the old variance-floor run
- [x] rewrite `CHECKLIST.md` for packet-adapter experiment prep
- [x] rewrite `status.md` so it reflects the new idea line rather than the completed variance-floor run
- [x] refresh the idea-stage literature survey for retrieval / adapter / distillation papers

## Evidence Review

- [x] confirm the reconstructed-video control remains a bounded baseline, not the preferred handoff winner
- [x] confirm prior packet-side direct controls are weak but non-trivial
- [x] confirm the naive ridge packet bridge is already measured and is worse than the direct controls
- [x] confirm the exporter manifest already preserves the existing comparison surface

## Package Design

- [ ] specify one non-leaking teacher-anchored adapter formulation
- [ ] decide whether to extend `run_teacher_packet_eval.py` or add one dedicated adapter-eval helper
- [ ] define the exact smoke command and output directory contract
- [ ] define the comparison table for the next smoke report

## Implementation Prep

- [ ] add the new teacher-anchored adapter comparison entry
- [ ] write summary/report fields for the new comparison
- [ ] add one reproducible launcher or documented command for the bounded smoke

## Smoke Gate

- [ ] run the bounded packet-adapter smoke on the same bundle surface
- [ ] verify the new comparison avoids target leakage
- [ ] verify the new comparison beats the naive ridge bridge
- [ ] decide whether the result is strong enough to justify a dedicated run branch

## Notes

- current bounded packet evidence:
  - `pred_feat_to_target_feat_direct top1 = 0.25` on the delta packet smoke
  - `pred_delta_to_target_feat_direct top1 = 0.5` on the delta packet smoke
  - `delta_ridge_to_target_feat_loo top1 = 0.0`
  - blueprint packet smoke remained near chance for direct packet retrieval on the widened surface
- selected route:
  - reuse the current bundle
  - keep upstream frozen
  - add exactly one better-scoped, teacher-anchored comparison before widening scope
