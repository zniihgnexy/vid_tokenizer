# Status

Baseline reuse is already resolved: `nvrc-local-source` is the accepted upstream asset.

Current stage: `experiment_prep`

Current judgment:
- The next line should not reopen old compression-variant ranking.
- The parent downstream line already proved the pipeline skeleton: frozen upstream export plus frozen downstream consumer is runnable end to end.
- The reconstructed-video handoff is now a bounded control result, not the preferred interface winner.
- The active child line is `Query-Distinct Packet Bridge After Collapse Evidence`.
- The chunk-aware parent line is now preserved as a failed but informative control:
  - `chunk_target_feat_to_chunk_target_feat_seq_concat_top1_accuracy=1.0`
  - `chunk_pred_feat_to_chunk_target_feat_seq_concat_top1_accuracy=0.25`
  - `chunk_pred_delta_to_chunk_target_feat_seq_concat_top1_accuracy=0.25`
- The decisive bottleneck is no longer “can chunk-aware aggregation help?” That question is already answered.
- The decisive new evidence is that the predicted packet side collapses while the target side does not:
  - `pred_feat` cross-chunk cosine is `1.0` everywhere
  - `pred_delta` cross-chunk cosine is `1.0` everywhere
  - `target_feat` and `target_delta` remain non-constant across chunks
- The correct next move is to localize where chunk discrimination disappears on the same frozen widened surface before trying any repair.
- The literature now supports four plausible repair families after localization:
  - target/query asymmetry
  - explicit variance floors
  - redundancy reduction
  - chunk-local temporal contrastive calibration
- The next experiment should still stay narrow:
  - no upstream rerun
  - no new dataset
  - no larger VLM/LLM integration
  - no direct regularizer-first jump before localization

Current frontier:
1. Recommended: run a collapse-localization package on the same frozen widened four-chunk surface.
2. Next if the collapse localizes to the query-side head: test exactly one minimal diversity-preserving control on the same surface.
3. Fallback: if collapse already exists before packet export, downgrade the packet-bridge story instead of adding more bridge variants.
4. Deferred: heavier fusion or broader bridge redesign before localization.
5. Deferred: larger multimodal or VLM/LLM integration until a non-collapsed packet bridge exists.
6. Rejected for now: more chunk-aware aggregator tuning as the primary route.
7. Rejected for now: direct regularizer-first repair without localization.
8. Rejected for now: another flat widened retrieval claim.

Next durable action:
- sync this child branch's control docs to the localization-first route
- implement the first collapse-localization smoke package
- if the failing layer is localized to the query-side head, choose one minimal repair family and test it on the same frozen widened surface
