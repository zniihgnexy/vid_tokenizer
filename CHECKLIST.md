# Main Experiment Checklist

Update this while planning, modifying code, running pilots, and validating the localization result.

## Identity

- run id: `shared_gating_query_collapse_localization_smoke_r1`
- idea id: `idea-c5e88710`
- stage: `experiment_prep`

## Planning

- [x] selected idea summarized in `1-2` sentences
- [x] parent-line evidence and baseline contract confirmed
- [x] collapse-specific risks listed
- [x] localization surfaces defined
- [x] literature-backed repair families ranked after localization
- [x] exact localization output package chosen

## Implementation

- [ ] localization entrypoint written
- [ ] control docs synced to the localization-first route
- [ ] target/pred/query tensor access sanity-checked against real widened bundle files
- [ ] optional repair entrypoint left deferred until localization result exists

## Pilot / Smoke

- [ ] localization smoke command executed
- [ ] diagnostic output root contains report, summary, cosine matrices, and per-surface statistics
- [ ] earliest collapse surface is explicit
- [ ] result is interpretable against the existing chunk-aware control

## Validation

- [ ] next action is explicit: either choose one minimal repair family or downgrade the packet bridge line
- [ ] no second repair family is added before the first localization result is interpreted
- [ ] bridge-line continuation remains justified after the localization package

## Notes

- chunk-aware control:
  - `chunk_target_feat_to_chunk_target_feat_seq_concat_top1_accuracy=1.0`
  - `chunk_pred_feat_to_chunk_target_feat_seq_concat_top1_accuracy=0.25`
  - `chunk_pred_delta_to_chunk_target_feat_seq_concat_top1_accuracy=0.25`
- collapse probe:
  - `pred_feat` cross-chunk cosine matrix is all `1.0`
  - `pred_delta` cross-chunk cosine matrix is all `1.0`
  - `target_feat` and `target_delta` remain non-constant across chunks
- repair families now justified by literature:
  - target/query asymmetry
  - explicit variance floors
  - redundancy reduction
  - chunk-local temporal contrastive calibration
- branch meaning:
  - the chunk-aware branch is preserved as a failed but informative control
  - the immediate blocker is localization of query-side collapse, not another evaluator rewrite
  - the next repair, if any, depends on a successful localization package
- next unchecked item:
  - write and execute the localization smoke entrypoint
