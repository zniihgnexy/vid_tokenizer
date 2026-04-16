# Main Experiment Checklist

Update this while interpreting the localization result, selecting the first repair, and validating the chosen repair path.

## Identity

- run id: `shared_gating_blueprint_semchange_delta_smoke_r1`
- idea id: `idea-c5e88710`
- stage: `experiment_prep`

## Planning

- [x] localization evidence interpreted
- [x] earliest accessible collapse surface made explicit
- [x] exactly one first repair family selected
- [x] main alternative repair family explicitly deferred
- [x] baseline and comparison contract kept stable

## Implementation

- [x] localization entrypoint written
- [x] localization result package generated
- [x] control docs synced to the localization outcome
- [x] blueprint repair config added
- [x] lightweight repair-smoke command executed

## Pilot / Smoke

- [x] localization smoke command executed
- [x] diagnostic output root contains report, summary, cosine matrices, and per-surface statistics
- [x] predicted packet collapse is explicit
- [x] target packet discrimination is explicit
- [x] blueprint teacher-loss path validates cleanly
- [ ] bounded blueprint repair run is ready to launch on the same frozen surface

## Validation

- [x] next action is explicit: test the blueprint repair family first
- [x] no second repair family is added before the first repair is interpreted
- [ ] predicted packet self-surface variance rises above zero after repair
- [ ] at least one predicted-to-target packet comparison exceeds `0.25` top-1 after repair
- [ ] downgrade the packet-bridge line if the blueprint repair still leaves packets collapsed

## Notes

- localization result:
  - `target_feat_to_target_feat_seq_concat_top1_accuracy=1.0`
  - `target_delta_to_target_delta_seq_concat_top1_accuracy=1.0`
  - `pred_feat_to_pred_feat_seq_concat_top1_accuracy=0.25`
  - `pred_delta_to_pred_delta_seq_concat_top1_accuracy=0.25`
  - `pred_feat` and `pred_delta` cross-chunk cosine matrices are all `1.0`
  - `pred_feat` and `pred_delta` raw mean dimension variance are both `0.0`
- chosen first repair:
  - enable `teacher_semantic_blueprint`
  - keep semantic-change weighting
  - keep temporal-delta consistency
- repair-smoke validation:
  - `semantic_blueprint=true`
  - `temporal_delta_consistency=true`
  - `semantic_change_weighting=true`
  - `feature_shape=[2, 4, 512]`
  - `semantic_blueprint_target_shape=[2, 4, 4]`
  - `temporal_delta_shape=[2, 4, 512]`
- deferred alternative:
  - `teacher_relation_consistency`
- next unchecked item:
  - prepare the bounded blueprint repair run
