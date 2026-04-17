# Teacher Gallery-Anchor Packet Adapter Plan

## 1. Run Contract

- run id: `teacher_anchored_packet_adapter_smoke_r1`
- parent idea id: `idea-76fee64d`
- selected idea in `1-2` sentences:
  the next bounded experiment should stop reopening upstream loss tuning and
  instead test whether the already exported teacher-feature packet bundle can be
  turned into a more usable machine-facing interface through one lightweight,
  teacher-anchored retrieval adapter.
- user-facing objective:
  keep the pipeline runnable, produce an inspectable first result batch, and
  decide whether the packet-side interface is worth pushing further before any
  larger-model integration.
- baseline and comparability contract:
  - confirmed baseline remains `nvrc-local-source` / `tiny-local-teacher-pilot-r3`
  - keep the upstream compression result frozen
  - keep the packet bundle schema unchanged
  - keep the first packet smoke on the same bounded `4`-frame bundle surface
  - keep the downstream evaluation as retrieval-style matching against
    target-side teacher space
- research question:
  can one teacher gallery-anchor projection map the current packet bundle into
  `target_feat` space better than the existing direct `pred_feat -> target_feat`
  control, while staying inside the same tiny-local packet bundle?
- null hypothesis:
  the teacher gallery-anchor projection does not improve `target_feat`-space
  retrieval over the direct `pred_feat -> target_feat` control.
- alternative hypothesis:
  a teacher gallery-anchor projection built from the joint
  `pred_feat + 8.0 * pred_delta` query can materially improve `target_feat`-space
  retrieval on the same bundle.
- primary metric:
  `consumer_metrics.teacher_gallery_anchor_joint_to_target_feat.top1_accuracy`
- secondary metrics:
  - `mean_match_rank`
  - `mean_margin_vs_best_nonmatch`
  - comparison against
    `consumer_metrics.pred_feat_to_target_feat.top1_accuracy`
- stop condition for this bounded pass:
  one runnable smoke command, one durable summary/report, and an explicit route
  decision from the measured result

## 2. Strongest Existing Evidence

- frozen downstream control from the reconstructed-video line:
  - `original_to_original_top1_accuracy = 1.0`
  - `reconstructed_to_original_top1_accuracy = 0.25`
- current packet-side control on the reusable `4`-frame bundle:
  - `pred_feat_to_target_feat top1 = 0.25`
  - `pred_delta_to_target_delta top1 = 0.75`
  - `pred_feat_plus_8p0x_delta_concat_to_target_feat_plus_8p0x_delta_concat top1 = 0.75`
- old weak bridge evidence:
  - `delta_ridge_to_target_feat_loo top1 = 0.0`
  - `feat_plus_8p0x_delta_ridge_to_target_feat_loo top1 = 0.0`
- local packet payload and manifest are already sufficient:
  - packet fields: `pred_feat`, `target_feat`, `pred_delta`, `target_delta`
  - no exporter change is required for the first adapter smoke
- quick prototype on the active run worktree:
  - teacher gallery-anchor softmax with `delta_weight = 8.0` and
    `anchor_logit_scale = 16.0` raises `target_feat`-space top-1 from `0.25` to
    `0.75`
  - strict leave-one-out gallery exclusion collapses to `0.0`, so the honest
    first bounded test is the retrieval-time gallery-memory setting, not a
    self-excluded adapter

## 3. Chosen Adapter Formulation

- query key:
  normalized `concat(pred_feat, 8.0 * pred_delta)`
- gallery anchor keys:
  normalized `concat(target_feat, 8.0 * target_delta)`
- gallery anchor values:
  normalized `target_feat`
- projection rule:
  `softmax(16.0 * cosine(query_key, gallery_anchor_keys)) @ gallery_anchor_values`
- interpretation:
  this is a fixed teacher gallery-memory adapter. It does not learn a new
  regression map; it uses the teacher packet bank as the retrieval-time memory
  that projects the predicted packet into `target_feat` space.
- caveat:
  this is a gallery-memory interface, not yet a standalone parametric bridge.
  That is acceptable for the first bounded packet-interface smoke because the
  user asked for a runnable first pipeline version and an inspectable result
  batch, not yet a final larger-model handoff.

## 4. Comparison Table For The Smoke

- `target_feat_to_target_feat`
- `pred_feat_to_target_feat`
- `pred_delta_to_target_delta`
- `pred_feat_plus_8p0x_delta_concat_to_target_feat_plus_8p0x_delta_concat`
- `teacher_gallery_anchor_joint_to_target_feat`

## 5. Code Touchpoints

| Path | Planned change | Why this is needed |
|---|---|---|
| `experiments/main/scripts/run_teacher_anchor_packet_eval.py` | add a dedicated teacher gallery-anchor evaluator | keep the new adapter logic isolated instead of overloading the direct evaluator |
| `experiments/main/scripts/run_teacher_anchor_packet_adapter_smoke.sh` | add a reproducible bounded smoke launcher | make the result rerunnable from one command |
| `PLAN.md`, `CHECKLIST.md`, `status.md` | rewrite around the run contract | make the run branch auditable as an experiment, not only as idea prep |

## 6. Smoke Command And Outputs

- default bundle:
  `experiments/main/interface_bundles/shared_gating_teacher_packet_smoke_r1`
- default output:
  `experiments/main/evals/teacher_anchor_packet_adapter_smoke_r1`
- smoke command:
  `./experiments/main/scripts/run_teacher_anchor_packet_adapter_smoke.sh`
- required outputs:
  - `summary.json`
  - `report.md`
  - per-comparison row csv files
  - anchor-weight csv for the new teacher gallery-anchor comparison

## 7. Success And Abandonment Criteria

- success:
  - the new script runs on the current local bundle without exporter changes
  - `teacher_gallery_anchor_joint_to_target_feat.top1_accuracy > 0.25`
  - the run leaves a durable report and summary that show what the packet-side
    output actually looks like
- strong success:
  - the new comparison reaches `0.75` top-1 or better and therefore matches the
    strongest existing joint-space direct control while improving the
    `target_feat`-space handoff
- abandonment or downgrade:
  - the runnable script fails on the current bundle
  - the new comparison stays at or below `0.25` top-1
  - the adapter only works after a schema change or a hidden extra dependency

## 8. Why This Route Dominates The Alternatives

- it reuses the exact packet bundle the repo already owns
- it gives the user a runnable first result batch immediately
- it focuses innovation on pipeline/interface usefulness rather than reopening
  codec ranking
- it is a cleaner first packet-interface test than another weak ridge map
- it is still bounded enough that failure would clearly justify a deeper
  interface redesign instead of another ambiguous tuning round

## 9. Checklist Link

- checklist path: `CHECKLIST.md`
- immediate next unchecked item:
  add the dedicated evaluator, launcher, and run the bounded smoke
