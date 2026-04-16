# Status

Baseline reuse is already resolved: `nvrc-local-source` remains the accepted upstream asset.

Current stage: `experiment_prep`

Current judgment:
- The localization smoke is complete and decisive.
- The failure is not in chunk aggregation.
- The earliest accessible collapse surface is `exported_predicted_packets_or_earlier`.
- Target packets still separate all four chunks:
  - `target_feat_to_target_feat_seq_concat_top1_accuracy=1.0`
  - `target_delta_to_target_delta_seq_concat_top1_accuracy=1.0`
- Exported predicted packets are fully collapsed:
  - `pred_feat_to_pred_feat_seq_concat_top1_accuracy=0.25`
  - `pred_delta_to_pred_delta_seq_concat_top1_accuracy=0.25`
  - `pred_feat` cross-chunk cosine is `1.0` everywhere
  - `pred_delta` cross-chunk cosine is `1.0` everywhere
  - `pred_feat` and `pred_delta` raw mean dimension variance are both `0.0`
- The frozen bundle does not expose deeper `query_projection` or `query_packet_head` tensors, so exported predicted packets are the current comparison boundary.
- The chosen first repair is `teacher_semantic_blueprint` on top of the existing semantic-change and temporal-delta path.
- The lightweight blueprint smoke already validated that this repair path is executable in the current NVRC task stack:
  - `semantic_blueprint=true`
  - `temporal_delta_consistency=true`
  - `semantic_change_weighting=true`
  - `feature_shape=[2, 4, 512]`
  - `semantic_blueprint_target_shape=[2, 4, 4]`
  - `temporal_delta_shape=[2, 4, 512]`
- Why blueprint wins:
  - this failure is cross-chunk identity collapse, not only weak within-clip temporal structure
  - blueprint aligns each clip to its own target-conditioned low-rank semantic subspace
  - relation consistency is kept as a fallback because it is less directly targeted at cross-chunk separation
- The route is now intentionally narrow:
  - no second repair family yet
  - no wider bridge redesign yet
  - no larger VLM/LLM integration yet
  - no reopened codec ranking

Current frontier:
1. Recommended: prepare one bounded blueprint repair run on the same frozen widened surface.
2. Fallback: if blueprint is invalid or unsupported, fall back to the existing relation-consistency path as the only alternate minimal repair.
3. Stop condition: if a bounded blueprint repair still leaves predicted packets collapsed, downgrade the packet-bridge line instead of stacking more controls.
4. Deferred: heavier bridge redesign before the first repair result exists.
5. Deferred: larger multimodal or VLM/LLM integration until a non-collapsed packet bridge exists.

Next durable action:
- keep the localization result as the locked failure boundary
- keep the validated blueprint repair config as the single active repair family
- prepare the smallest bounded repair smoke before any broader change
