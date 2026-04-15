# Status

Baseline reuse is already resolved: `nvrc-local-source` is the accepted upstream asset.

Current stage: `experiment_prep`

Current judgment:
- The next line should not reopen old compression-variant ranking.
- The parent downstream line already proved the pipeline skeleton: frozen upstream export plus frozen downstream consumer is runnable end to end.
- The reconstructed-video handoff is now a bounded control result, not the preferred interface winner.
- The key parent-line comparison is `original_to_original_top1_accuracy=1.0`, `reconstructed_to_original_top1_accuracy=0.25`, and `reconstructed_to_original_mean_match_rank=2.5`.
- The delta-first packet follow-up stabilized on the same frozen 4-frame surface: `delta-only_top1_accuracy=0.75`, `8x_delta_concat_top1_accuracy=0.75`, and `8x_delta_sum_top1_accuracy=0.5`.
- The active child line is `Delta-Packet Bridge to Frozen Consumer Space`.
- The scientific bottleneck is now split into two steps:
  - first, widen the frozen upstream export surface without changing the contract
  - then, rerun the bridge comparison on that widened surface
- The repo currently has a new 16-frame bounded local Ego4D surface at `32x32`, plus a manifest that records its extraction provenance.
- The full frozen rerun config family has now been recovered inside the upstream snapshot: `tiny_local`, `tiny-1e`, `teacher_tiny_32`, `nvrc_tiny_s1`, and the shared semantic-change delta teacher task.
- The first bridge smoke still exists on the old 4-frame surface:
  - `pred_feat_to_target_feat_direct_top1_accuracy=0.25`
  - `pred_delta_to_target_feat_direct_top1_accuracy=0.5`
  - `delta_ridge_to_target_feat_loo_top1_accuracy=0.0`
  - `feat_plus_8p0x_delta_ridge_to_target_feat_loo_top1_accuracy=0.0`
- The current evidence supports direct delta alignment as a live bridge signal, but explicitly rejects a learned bridge claim on the 4-frame surface.
- The correct next move is therefore a frozen 16-frame upstream export smoke under the recovered tiny config family, not another 4-frame bridge tweak, not a direct VLM/LLM demo, and not a learned-adapter claim yet.

Current frontier:
1. Recommended: run the 16-frame frozen export smoke and validate bundle compatibility.
2. Next if the smoke succeeds: rebuild reconstructed and teacher-packet bundles on the widened surface, then rerun the bridge comparison.
3. Fallback if direct config launch still drifts: add a thin replay wrapper seeded from the old resolved `args.yaml`.
4. Deferred: static-context sidecar or other fusion-heavy packet variants.
5. Deferred: larger multimodal or VLM/LLM integration after the widened bridge line proves itself on local assets.
6. Rejected for now: learned ridge-style bridge claims on the 4-frame surface.
7. Rejected for now: plain static feature packet as the default machine-facing winner.
8. Rejected for now: simple weighted-sum fusion as the default composition rule.
9. Rejected for now: further scaling of reconstructed video as the primary handoff layer.

Next durable action:
- write the local widened-export rerun script
- execute `shared_gating_interface_export_ego4d16f_smoke_r1`
- inspect the output tree and metrics before any new bridge evaluation
