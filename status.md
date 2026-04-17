# Status

Baseline reuse is already resolved: `nvrc-local-source` remains the accepted upstream asset.

Current stage: `experiment_prep`

Current judgment:
- The earlier localization smoke is still the locked failure boundary.
- The bounded `blueprint + semantic-change + temporal-delta` repair successfully ran end-to-end, exported a packet bundle, and produced a bounded teacher-packet evaluation.
- That first repair is now downgraded.
- Why it is downgraded:
  - `target_feat` remains fully discriminative on the repaired single bundle: `top1_accuracy=1.0`
  - `pred_feat -> target_feat` is still only `0.0625` top-1 on a `16`-frame bundle, which is effectively chance-level alignment
  - `pred_delta -> target_delta` rises to `0.1875` top-1, but its mean margin vs best non-match is still negative
  - within-bundle self checks show the repair is not a pure constant-vector failure anymore:
    - `pred_feat_self_top1=1.0`, `offdiag_mean=0.9947`
    - `pred_delta_self_top1=0.9375`, `offdiag_mean=-0.0543`
  - taken together, the evidence says blueprint recovers some self-discrimination but does not recover clean predicted-to-target packet alignment
- This means the remaining bottleneck is target alignment, not simply restoring packet variance.
- The lightweight relation smoke now validates the next repair path cleanly:
  - `feature_shape=[2, 4, 512]`
  - `relation_shape=[2, 4, 4]`
  - `temporal_delta_shape=[2, 4, 512]`
  - semantic-change weights stay well-formed with mean `~1.0`
- The current frontier is now intentionally narrow again:
  1. Recommended: launch one bounded `teacher_relation_consistency` repair on the same frozen surface.
  2. Fallback: if the bounded run fails early or is invalid, reopen route selection instead of stacking more built-in regularizers blindly.
  3. Stop condition: if the bounded relation run still leaves predicted-to-target alignment near chance, downgrade the packet-bridge line again instead of widening scope.
- Deferred:
  - broader bridge redesign before relation is tested
  - deeper multimodal / VLM integration before a reliable packet interface exists
  - reopening codec-line ranking

Next durable action:
- keep the localization package as the locked pre-repair failure boundary
- keep the blueprint result as a completed but insufficient first repair
- keep the relation repair smoke summary as the entry validation
- launch one bounded relation repair run via the dedicated wrapper
