# Teacher Gallery-Anchor Packet Adapter Checklist

Update this while implementing and validating the bounded packet-adapter smoke.

## Identity

- idea id: `idea-76fee64d`
- run id: `teacher_anchored_packet_adapter_smoke_r1`
- stage: `experiment`

## Preconditions

- [x] confirm the accepted baseline contract is still `nvrc-local-source`
- [x] confirm the active route is the teacher-anchored packet-adapter line
- [x] confirm the first package stays on the same bounded `4`-frame packet bundle
- [x] confirm the current packet bundle schema already exposes packet paths, metrics, and teacher packet summary
- [x] confirm the local reusable bundle exists at `experiments/main/interface_bundles/shared_gating_teacher_packet_smoke_r1`

## Run Contract

- [x] rewrite `PLAN.md` around the dedicated run contract
- [x] rewrite `CHECKLIST.md` for the run branch
- [x] rewrite `status.md` for the run branch
- [x] choose the first adapter formula:
  teacher gallery-anchor softmax projection from
  `pred_feat + 8.0 * pred_delta` into `target_feat`
- [x] choose a bounded default scale:
  `anchor_logit_scale = 16.0`
- [x] define the smoke command and output directory contract
- [x] define the comparison table for the smoke report

## Implementation

- [x] add the dedicated `run_teacher_anchor_packet_eval.py` helper
- [x] add the bounded launcher `run_teacher_anchor_packet_adapter_smoke.sh`
- [x] write report fields for the teacher gallery-anchor comparison
- [x] write anchor-weight export for the new comparison

## Smoke Gate

- [x] run the bounded packet-adapter smoke on the local `4`-frame bundle
- [x] verify `teacher_gallery_anchor_joint_to_target_feat.top1_accuracy > 0.25`
- [x] verify the new comparison beats the old ridge bridge baseline (`0.0`)
- [x] inspect whether the result is close enough to the `0.75` joint-space direct control to justify a fuller packet-interface run

## Durable Recording

- [ ] record the measured result with `artifact.record_main_experiment(...)`
- [ ] write the route decision for whether to keep pushing this packet-memory interface or widen scope

## Notes

- current bounded packet evidence:
  - `pred_feat_to_target_feat top1 = 0.25`
  - `pred_delta_to_target_delta top1 = 0.75`
  - `pred_feat_plus_8p0x_delta_concat_to_target_feat_plus_8p0x_delta_concat top1 = 0.75`
  - old ridge bridge top-1 stayed at `0.0`
- quick prototype evidence on this run branch:
  - teacher gallery-anchor projection reaches `0.75` top-1 at
    `anchor_logit_scale = 16.0`
  - strict leave-one-out gallery exclusion collapses to `0.0`, so the honest
    first smoke is the retrieval-time gallery-memory setting
- measured smoke result:
  - `teacher_gallery_anchor_joint_to_target_feat top1 = 0.75`
  - `teacher_gallery_anchor_joint_to_target_feat mean_match_rank = 1.5`
  - `pred_feat_to_target_feat top1 = 0.25`
  - only query `0000` still collapses toward `0001`; the other three queries are correct
