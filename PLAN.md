# Main Experiment Plan

## 1. Objective

- run id: `teacher_feature_packet_interface_bootstrap_r1`
- selected idea in `1-2` sentences: Keep the frozen shared-gating upstream module and the validated paired bundle from the parent line, but replace reconstructed-video consumption with a teacher/tokenizer feature-packet interface. The goal of this child line is to preserve more machine-usable structure than decoded frames while keeping the pipeline rerunnable and machine-facing.
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
- current pass objective: identify the cleanest teacher/tokenizer hook point, define the first packet export schema, and prepare a bounded feature-packet experiment that mirrors the parent line's comparison shape
- research question: Can a teacher/tokenizer feature-packet interface preserve identity-level retrieval structure better than reconstructed video on the same frozen upstream bundle and frozen downstream comparison surface?
- null hypothesis: Feature export adds complexity without improving downstream structure preservation over the reconstructed-video control.
- alternative hypothesis: Feature packets preserve the machine-facing signal better than decoded frames and therefore become the correct handoff layer for later larger-model integration.

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
| `experiments/main/scripts/export_teacher_feature_interface.py` | new | export teacher/tokenizer feature packets with stable sample ids and metadata | this is the core new interface layer under test | medium |
| `experiments/main/scripts/run_frozen_consumer_eval.py` | parent-line consumer evaluator | reuse or minimally extend it so the downstream comparison shape stays aligned between reconstructed-video and packet-side routes | preserves clean comparability between handoff layers | low |
| `experiments/main/interface_bundles/teacher_feature_packet_smoke_r1/` | new output root | store packet tensors, metadata manifest, and packet-side control summaries | keeps the child line self-contained and inspectable | low |

## 4. Execution Design

- minimal experiment:
  - export one bounded teacher/tokenizer packet bundle on the same 4-frame surface
  - reuse the frozen downstream comparison shape from the parent line
  - compare packet-side retrieval preservation against the reconstructed-video control
- smoke / pilot plan:
  - inspect hook points for teacher/tokenizer-side activations or packet tensors
  - export one minimal packet bundle with exact sample-id alignment
  - verify bundle structure, tensor shapes, and metadata integrity
  - run the frozen consumer or the smallest justified packet adapter on the packet bundle
- expected outputs:
  - packet export script
  - packet bundle manifest and tensor payloads
  - first packet-side downstream comparison table
  - one concise route recommendation versus the reconstructed-video control
- stop condition: the child line produces one bounded packet bundle plus one interpretable downstream comparison against the parent-line reconstructed-video control
- abandonment condition:
  - no clean teacher/tokenizer hook can be exported without destabilizing the frozen upstream contract
  - packet-side alignment becomes ambiguous enough that the comparison would no longer be trustworthy
  - the required adapter grows beyond a minimal bounded extension

## 5. Runtime Strategy

- immediate next actions:
  - inspect the frozen upstream code for teacher/tokenizer export hooks
  - define the packet manifest schema and expected tensor layout
  - prepare the first packet-side smoke command
- artifact locations:
  - parent-line evidence:
    `../idea-idea-3ed587d5/experiments/main/shared_gating_downstream_interface_bootstrap_r1/downstream_eval/`
  - parent-line bundle:
    `../idea-idea-3ed587d5/experiments/main/interface_bundles/shared_gating_interface_export_smoke_r1/`
  - child-line packet bundle root:
    `experiments/main/interface_bundles/teacher_feature_packet_smoke_r1/`
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

## 7. Checklist Link

- checklist path: `CHECKLIST.md`
- next unchecked item: inspect the frozen upstream code for the first clean teacher/tokenizer packet export hook
