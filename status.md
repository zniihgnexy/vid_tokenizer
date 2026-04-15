# Status

Baseline reuse is already resolved: `nvrc-local-source` is the accepted upstream asset.

Current stage: `experiment_prep`

Current judgment:
- The next line should not reopen old compression-variant ranking.
- The imported baseline package behaves like a verified upstream asset bundle, not a full downstream-ready system.
- The parent downstream line already proved the pipeline skeleton: frozen upstream export plus frozen downstream consumer is runnable end to end.
- The reconstructed-video handoff is now a bounded control result, not the preferred interface winner.
- The key parent-line comparison is `original_to_original_top1_accuracy=1.0`, `reconstructed_to_original_top1_accuracy=0.25`, and `reconstructed_to_original_mean_match_rank=2.5`.
- The active child line is `Teacher-Feature Packet Interface After Reconstructed-Video Bottleneck`.
- The correct next move is to preserve the same upstream checkpoint, sample ids, and 4-frame tiny-local surface while changing only the machine-facing handoff layer.
- The next stage should not reopen codec ranking or jump straight to a larger VLM/LLM interface before packet-side evidence exists.

Current frontier:
1. Recommended: teacher/tokenizer feature packet export with the same frozen downstream comparison shape.
2. Fallback: the smallest stable intermediate feature above decoded frames if direct teacher/tokenizer hooks are too entangled.
3. Deferred: larger multimodal or VLM/LLM integration after packet-side preservation is measured.
4. Rejected for now: further scaling of reconstructed-video as the primary machine-facing interface.

Next durable action:
- inspect the frozen upstream snapshot for packet hook points
- define the packet manifest and tensor layout
- implement and smoke the first packet export path
- run the first packet-side downstream comparison against the reconstructed-video control
