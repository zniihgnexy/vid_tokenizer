# Status

Baseline reuse is already resolved: `nvrc-local-source` is the accepted upstream asset.

Current stage: `decision`

Current judgment:
- The next line should not reopen old compression-variant ranking.
- The imported baseline package behaves like a verified upstream asset bundle, not a full downstream-ready system.
- The parent downstream line already proved the pipeline skeleton: frozen upstream export plus frozen downstream consumer is runnable end to end.
- The reconstructed-video handoff is now a bounded control result, not the preferred interface winner.
- The key parent-line comparison is `original_to_original_top1_accuracy=1.0`, `reconstructed_to_original_top1_accuracy=0.25`, and `reconstructed_to_original_mean_match_rank=2.5`.
- The active child line is `Teacher-Feature Packet Interface After Reconstructed-Video Bottleneck`.
- The parent smoke is complete on the same 4-frame surface and is now the foundation for this new child line.
- Plain feature packet did not beat the reconstructed-video control: `pred_feat_to_target_feat_top1_accuracy=0.25`, matching the reconstructed-video control's `0.25`.
- Temporal delta packet is materially stronger: `pred_delta_to_target_delta_top1_accuracy=0.75` with `mean_match_rank=1.25`.
- A heavy delta-dominant concat sweep (`weight=8.0`) also reaches `top1_accuracy=0.75`, which confirms that the promising signal is delta-led rather than static-feature-led.
- The active child line now exists to test whether that delta-dominant advantage remains stable in the next bounded follow-up.
- The next stage should not reopen codec ranking or jump straight to a larger VLM/LLM interface before delta-first packet evidence is sharpened.

Current frontier:
1. Recommended: delta-dominant packet interface with the same frozen comparison shape.
2. Fallback: heavy-delta feature+delta mix if a pure delta packet becomes too brittle.
3. Deferred: larger multimodal or VLM/LLM integration after delta-first packet evidence is measured.
4. Rejected for now: plain static feature packet as the default machine-facing winner.
5. Rejected for now: further scaling of reconstructed-video as the primary machine-facing interface.

Next durable action:
- keep the new exporter/evaluator as reusable scaffolding
- prepare the smallest delta-first follow-up comparison on the same bounded surface
- use this child line only for the next delta-first validation rather than mixing it with the rejected plain-feature route
