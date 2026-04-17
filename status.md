# Status

Baseline reuse is already resolved: `nvrc-local-source` remains the accepted
upstream asset.

Current stage: `experiment_prep`

Current judgment:
- The active child line is now `Teacher-Anchored Packet Adapter After Mixed Variance-Floor Repair`.
- The corrected variance-floor run is useful only as route evidence; it does not justify another immediate low-level repair sweep.
- The current teacher-feature packet exporter is already sufficient for the next bounded step:
  - packet payloads include `pred_feat`, `target_feat`, `pred_delta`, and `target_delta`
  - the manifest already stores packet paths, frame-level decoded/eval metrics,
    aggregate metrics, and a teacher packet summary
- The current packet-side bottleneck is no longer “we have no bridge at all”.
  The stronger reading is:
  - direct packet controls are weak but non-zero
  - the naive ridge bridge is even worse
  - the missing evidence is whether a teacher-anchored adapter can improve the handoff on the same bundle
- The current comparison anchor stays fixed:
  - same frozen upstream surface
  - same tiny-local `4`-frame smoke surface for the next bounded package
  - same retrieval-style packet evaluation contract
- The best-supported next route is to reuse the existing bundle and add one
  teacher-anchored adapter comparison before any bundle redesign or larger-model integration.

Deferred:
- another immediate low-level anti-collapse or variance-floor sweep
- packet bundle schema redesign without concrete missing-field evidence
- direct VLM/LLM integration
- reopening codec-line ranking

Next durable action:
- finish the idea-stage convergence pass with the rewritten survey and control files
- define one non-leaking teacher-anchored adapter comparison
- hand off to `experiment` for a bounded packet-adapter smoke on the existing bundle surface
