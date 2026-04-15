# Main Experiment Plan

## 1. Objective

- run id: `delta_dominant_teacher_packet_followup_r1`
- selected idea in `1-2` sentences: Keep the same frozen shared-gating upstream module and the validated paired bundle from the parent line, but make temporal delta the primary packet signal. This child line exists because the first packet smoke showed that static feature packet did not beat the reconstructed-video control, while delta-heavy views did.
- user's core requirements:
  - keep the pipeline runnable from upstream compression to downstream machine use
  - produce an inspectable first result batch that shows whether the direction is worth doing
  - focus the innovation on pipeline/interface construction rather than reopening codec novelty
  - leave behind code that can be rerun locally and later shared cleanly
- non-negotiable user constraints:
  - do not reopen the upstream codec-line ranking
  - keep the accepted `nvrc-local-source` baseline contract visible
  - treat the reconstructed-video result as evidence, not as the final interface winner
  - keep the first follow-up route minimal and comparable
- current pass objective: use the first formal delta-first follow-up result to lock in the best bounded packet view before widening validation
- research question: Can a delta-dominant packet preserve retrieval structure better than both reconstructed video and plain feature packet on the same frozen upstream surface?
- null hypothesis: Even when delta is treated as the primary signal, packet export still fails to improve meaningfully over the reconstructed-video control.
- alternative hypothesis: A delta-dominant packet captures the useful machine-facing structure more reliably than decoded frames or plain feature packet and therefore becomes the correct next handoff layer.

## 2. Baseline And Comparability

- baseline id: `nvrc-local-source`
- baseline variant: `tiny-local-teacher-pilot-r3`
- inherited upstream metrics:
  - `bpp_avg=88.2266`
  - `psnr_avg=10.9012`
  - `teacher-mse_avg=0.5126`
- parent-line downstream control:
  - `original_to_original_top1_accuracy=1.0`
  - `reconstructed_to_original_top1_accuracy=0.25`
  - `reconstructed_to_original_mean_match_rank=2.5`
- comparison rule:
  - keep the same frozen upstream checkpoint
  - keep the same 4-frame bounded tiny-local surface
  - keep the same downstream comparison shape whenever possible
  - report feature-packet results against the reconstructed-video control rather than pretending they replace the baseline contract
- comparability risks:
  - teacher/tokenizer hooks may drift too close to the upstream teacher objective if the downstream evaluation is not kept independent enough
  - packet export may introduce alignment bugs between sample ids, frame order, and packet tensors
  - the frozen downstream consumer may need a lightweight adapter, which must be recorded explicitly if used

## 3. Code Translation Plan

| Path | Current role | Planned change | Why this is needed | Risk |
|---|---|---|---|---|
| `experiments/main/upstream_shared_gating_snapshot/third_party/NVRC/` | frozen upstream source snapshot | inspect the cleanest hook points for teacher/tokenizer packet export without changing upstream learning logic | the child line depends on exporting machine-usable structure more directly than decoded frames | medium |
| `experiments/main/scripts/export_reconstructed_interface.py` | parent-line bundle exporter | keep as the reference schema for ids, metadata, and aggregate metrics | the packet bundle should stay structurally compatible with the validated parent route where possible | low |
| `experiments/main/scripts/export_teacher_feature_interface.py` | reusable packet exporter | keep exporting stable sample ids plus feature/delta packet payloads, with any delta-first metadata additions kept minimal | this is the scaffold the new delta-dominant line will build on | medium |
| `experiments/main/scripts/run_frozen_consumer_eval.py` | parent-line consumer evaluator | keep as the reconstructed-video control evaluator and metric template | preserves clean comparability between the old handoff layer and the new packet-side route | low |
| `experiments/main/scripts/run_teacher_packet_eval.py` | reusable packet evaluator | extend or parameterize packet-side retrieval so delta-first comparisons are first-class instead of only post-hoc | lets the child line validate the new route without rewriting the evaluation surface | low |
| `experiments/main/interface_bundles/shared_gating_teacher_packet_smoke_r1/` | new output root | store packet tensors, metadata manifest, and packet-side control summaries | keeps the child line self-contained and inspectable | low |

## 4. Execution Design

- minimal experiment:
  - reuse the existing bounded teacher/tokenizer packet bundle on the same 4-frame surface
  - elevate delta-only and heavy-delta-gated concat packet views into the primary comparison objects
  - compare those delta-dominant results against both the reconstructed-video control and the rejected plain-feature packet result
- smoke / pilot plan:
  - keep the current exporter/evaluator scaffold and sample-id alignment fixed
  - encode delta-first comparison settings explicitly
  - run one bounded delta-first follow-up comparison
  - verify that the improvement is still present when delta is promoted deliberately rather than discovered only by post-hoc slicing
- expected outputs:
  - delta-first comparison configuration or minimal evaluator extension
  - bounded follow-up comparison table
  - one concise judgment on whether delta-first is stable enough to justify broader validation
  - one concise judgment on whether delta-dominant concat is preferable to delta-weighted sum
- stop condition: the child line produces one bounded packet bundle plus one interpretable downstream comparison against the parent-line reconstructed-video control
- abandonment condition:
  - no clean teacher/tokenizer hook can be exported without destabilizing the frozen upstream contract
  - packet-side alignment becomes ambiguous enough that the comparison would no longer be trustworthy
  - the required adapter grows beyond a minimal bounded extension

## 5. Runtime Strategy

- immediate next actions:
  - keep delta-only and heavy-delta concat as the active bounded winners
  - treat delta-weighted sum as downgraded after the first formal follow-up
  - prepare the smallest wider validation package that keeps the same scaffold but tests whether the `0.75` signal survives beyond the current 4-frame surface
- artifact locations:
  - parent-line evidence:
    `../idea-idea-3ed587d5/experiments/main/shared_gating_downstream_interface_bootstrap_r1/downstream_eval/`
  - parent-line bundle:
    `../idea-idea-3ed587d5/experiments/main/interface_bundles/shared_gating_interface_export_smoke_r1/`
  - child-line packet bundle root:
    `experiments/main/interface_bundles/shared_gating_teacher_packet_smoke_r1/`
  - child-line packet eval root:
    `experiments/main/evals/shared_gating_teacher_packet_smoke_r1/`
- safe efficiency levers:
  - reuse the frozen upstream checkpoint and bounded sample surface
  - keep packet export detached from retraining
  - mirror the parent-line comparison surface before widening scope

## 6. Fallbacks And Recovery

- if direct teacher/tokenizer packet export is too entangled:
  - fall back to the smallest stable intermediate feature that still sits above decoded frames
- if the packet consumer requires too much new modeling:
  - keep the adapter minimal and explicitly record the added layer
- if packet-side evidence is still weak:
  - treat the result as a bounded negative finding and revisit which interface layer is genuinely worth scaling
  - after the first smoke, treat plain feature packet as downgraded if it does not outperform the reconstructed-video control

## 7. Checklist Link

- checklist path: `CHECKLIST.md`
- next unchecked item: define the exact delta-first follow-up comparison package and run the next bounded validation
