# Packet Adapter Experiment Plan

## 1. Objective

- idea id: `idea-76fee64d`
- selected idea in `1-2` sentences:
  the next bounded step should stop tuning local loss terms and instead test
  whether the already exported teacher-feature packet bundle can be mapped into
  a more usable machine-facing space with one lightweight, teacher-anchored
  adapter.
- user's core requirements:
  - keep the full pipeline runnable from upstream compression to downstream machine use
  - produce an inspectable result batch that shows whether this direction is worth doing
  - focus novelty on pipeline/interface usefulness rather than reopening codec ranking
  - leave behind code and scripts that can be rerun locally
- non-negotiable constraints:
  - keep the accepted `nvrc-local-source` baseline contract visible
  - do not reopen upstream codec-line ranking
  - do not widen scope to a larger-model or VLM/LLM demo before the packet bridge is trustworthy
  - keep the packet bundle schema aligned with the existing manifest surface unless a concrete breakage forces a change
- current pass objective:
  finish the new idea-stage convergence pass by rewriting the route around one
  minimal experiment package: reuse the existing teacher-feature packet bundle,
  preserve the same tiny-local comparison surface, and add one teacher-anchored
  adapter comparison that can be smoke-tested before any larger run.
- research question:
  can a teacher-anchored adapter over the current packet bundle improve
  predicted-to-target retrieval alignment beyond the direct packet controls and
  the previously tried naive ridge bridge, without changing the bundle schema or
  leaking per-query target information at inference time?

## 2. Strongest Existing Evidence

- frozen downstream control from the parent line:
  - `original_to_original_top1_accuracy = 1.0`
  - `reconstructed_to_original_top1_accuracy = 0.25`
  - `reconstructed_to_original_mean_match_rank = 2.5`
- packet-side baseline from the blueprint teacher-packet smoke:
  - `target_feat_to_target_feat top1 = 1.0`
  - `pred_feat_to_target_feat top1 = 0.0625`
  - `pred_delta_to_target_delta top1 = 0.1875`
- packet-side bounded bridge evidence from the delta packet smoke:
  - `pred_feat_to_target_feat_direct top1 = 0.25`
  - `pred_delta_to_target_feat_direct top1 = 0.5`
  - `delta_ridge_to_target_feat_loo top1 = 0.0`
  - `feat_plus_8p0x_delta_ridge_to_target_feat_loo top1 = 0.0`
- exporter feasibility evidence:
  - the current packet bundle manifest already records `packet_relpath`,
    decoded/eval metrics, aggregate metrics, and a `teacher_packet_summary`
  - packet payloads already expose `pred_feat`, `target_feat`, `pred_delta`,
    and `target_delta`
- route judgment evidence from the last bounded main run:
  the corrected predicted-side variance-floor repair is now a valid measured
  result, but its mixed trade-off means the next highest-leverage move is
  interface-level rather than another immediate low-level repair sweep

## 3. Fixed Constraints And Comparability

- same confirmed baseline: `nvrc-local-source` with variant `tiny-local-teacher-pilot-r3`
- same frozen upstream family and parent result interpretation
- same packet bundle schema unless the current manifest proves insufficient
- same tiny-local `4`-frame bounded surface for the first adapter smoke
- same downstream evaluation style: retrieval-style matching against frozen target-side teacher space
- no new dataset
- no new external model API
- no broader end-to-end demo before this packet-side bridge becomes trustworthy

## 4. Candidate Routes

### Candidate A: reuse the current bundle and add one teacher-anchored adapter comparison

- what changes:
  extend the packet-side evaluator with a lightweight adapter that maps query
  packets into the frozen target/consumer space through a teacher-anchored basis
  or coefficient path
- why it is serious:
  all required inputs are already present in the current bundle and the missing
  comparison is exactly at the evaluator/adapter layer rather than the bundle
  layer

### Candidate B: redesign the packet bundle schema first

- what changes:
  add new exported fields or a new manifest contract before touching the evaluator
- why it is serious:
  would allow richer metadata or more explicit teacher anchors
- why it is not preferred now:
  the current manifest already carries the packet path, metrics, aggregate
  metrics, and teacher packet summary, so another schema round would add churn
  before the current interface surface is actually exhausted

### Candidate C: jump directly to a larger-model interface

- what changes:
  connect the current packet surface or reconstructed output to a larger VLM/LLM
  consumer
- why it is serious:
  closer to the user's long-horizon goal
- why it is not preferred now:
  too many variables would change at once before the local packet bridge is
  trustworthy

### Candidate D: continue local anti-collapse loss tuning

- what changes:
  spend another round inside the variance-floor or related regularizer family
- why it is serious:
  the last corrected run was at least a valid measured step
- why it is not preferred now:
  the measured trade-off was mixed and existing packet-side evidence now points
  to a higher-leverage interface bottleneck

## 5. Selected Route

- winner: Candidate A
- why it wins:
  it is the smallest credible move that tests the actual missing claim. The old
  packet evidence already includes direct controls and a weak ridge bridge, so
  the next discriminating experiment is not a new bundle or a larger model; it
  is one better-scoped adapter comparison on the same bundle.
- main residual risk:
  a teacher-anchored adapter can still fail if the predicted packet geometry is
  too damaged even after anchoring, which would strengthen the case for a deeper
  interface redesign rather than a local evaluator patch

## 6. Minimal Experiment Package

- reuse the existing teacher-feature packet exporter and manifest schema
- keep the current smoke surface at `4` bounded frames
- preserve existing controls:
  - `pred_feat -> target_feat` direct
  - `pred_delta -> target_feat` direct when applicable
  - previous naive ridge bridge as the weak adapter baseline
- add one new comparison:
  - a teacher-anchored adapter that projects predicted packets through a basis or
    coefficient path derived from teacher-side target packets without using the
    held-out query target packet itself at inference time
- first implementation target:
  extend the packet-side evaluation entry rather than changing the exporter,
  unless an exact missing field is discovered during implementation

## 7. Code Touchpoints

| Path | Planned change | Why this is needed |
|---|---|---|
| `experiments/main/scripts/export_teacher_feature_interface.py` | likely no schema change in the first pass | the current manifest already carries packet paths, metrics, and teacher packet summary |
| `experiments/main/scripts/run_teacher_packet_eval.py` | add one teacher-anchored adapter comparison or route to a new adapter-specific helper | this is the narrowest place to add the missing comparison while preserving the same bundle |
| `experiments/main/scripts/run_delta_packet_bridge_eval.py` | reuse as a design reference only unless the new adapter can be cleanly merged there | it already shows that a naive bridge can be worse than the direct packet control |
| `PLAN.md`, `CHECKLIST.md`, `status.md` | rewrite around the new packet-adapter route | the active control files were still describing the old variance-floor run |
| `artifacts/idea/literature_survey.md` | refresh for retrieval / adapter / distillation papers | the old survey was still anti-collapse-centered rather than interface-centered |

## 8. Success And Abandonment Criteria

- success criteria for the next smoke package:
  - the new adapter comparison is defined without target leakage
  - it runs on the same bundle without schema churn
  - it beats the weakest current baselines, especially the naive ridge bridge
  - ideally it also beats the direct `pred_feat -> target_feat` control on top-1
    or mean match rank
- abandonment criteria:
  - the adapter definition requires the held-out query target packet at inference time
  - the current manifest is discovered to be insufficient in a way that forces a
    broad exporter redesign
  - the new comparison remains no better than the direct packet controls and the
    old naive bridge, in which case the line should downgrade toward a deeper
    interface redesign instead of further local evaluator tuning

## 9. Runtime Strategy

- safe efficiency levers:
  - reuse the existing packet bundle schema
  - reuse the same tiny-local `4`-frame surface for the first smoke
  - keep the upstream run frozen and untouched
  - add exactly one new comparison before considering any wider package
- branch rule:
  - finish this idea-stage control-file and survey rewrite first
  - then hand off into `experiment` for the bounded packet-adapter smoke rather
    than implementing a larger package directly from the idea stage

## 10. Checklist Link

- checklist path: `CHECKLIST.md`
- next unchecked item:
  specify the exact non-leaking teacher-anchored adapter formulation and choose
  whether it extends the current evaluator or lives in a small new helper
