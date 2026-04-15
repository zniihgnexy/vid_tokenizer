# Main Experiment Plan

## 1. Objective

- run id: `shared_gating_interface_export_ego4d16f_smoke_r1`
- selected idea in `1-2` sentences: Keep the same frozen shared-gating upstream module and the validated packet/consumer route, but widen the bounded surface before claiming anything stronger about the delta bridge. This child line exists because the 4-frame surface kept the signal alive but was too small to defend a stronger consumer-facing claim.
- user's core requirements:
  - keep the pipeline runnable from upstream compression to downstream machine use
  - produce an inspectable result batch that shows whether this direction is worth doing
  - focus the innovation on pipeline/interface construction rather than reopening codec novelty
  - leave behind code that can be rerun locally and later shared cleanly
- non-negotiable user constraints:
  - do not reopen the upstream codec-line ranking
  - keep the accepted `nvrc-local-source` baseline contract visible
  - treat reconstructed video as a bounded control, not as the default winner
  - avoid a confounded direct VLM/LLM demo before the local bridge is proven
- current pass objective: rerun the frozen shared-gating export on the new 16-frame bounded Ego4D surface and produce a widened interface bundle for the next bridge comparison
- research question: Does the same frozen shared-gating export contract remain runnable and interpretable on a wider 16-frame bounded surface?
- null hypothesis: the widened export fails to run cleanly or yields an incompatible bundle, so the bridge line cannot yet progress beyond the old 4-frame surface
- alternative hypothesis: the same frozen contract exports a valid widened bundle with interpretable metrics, enabling a fair next bridge evaluation

## 2. Baseline And Comparability

- baseline id: `nvrc-local-source`
- baseline variant: `tiny-local-teacher-pilot-r3`
- inherited 4-frame export metrics:
  - `bpp_avg=88.2266`
  - `psnr_avg=10.9012`
  - `teacher-mse_avg=0.5126`
- parent-line downstream control:
  - `original_to_original_top1_accuracy=1.0`
  - `reconstructed_to_original_top1_accuracy=0.25`
  - `reconstructed_to_original_mean_match_rank=2.5`
- current bridge evidence on the old 4-frame surface:
  - `pred_delta_to_target_feat_direct_top1_accuracy=0.5`
  - `delta_ridge_to_target_feat_loo_top1_accuracy=0.0`
- widened bounded surface:
  - dataset root: `tmp/ego4d_bounded_bridge_r1/data/ego4d_small_bridge_16f`
  - sample shape: `16 x 32 x 32`
  - manifest: `tmp/ego4d_bounded_bridge_r1/data/ego4d_small_bridge_16f/extraction_manifest.json`
- comparison rule:
  - keep the same frozen upstream checkpoint, task config, model config, and NVRC config
  - change only the bounded PNG surface and frame-count override
  - require the widened run to emit the same output structure and metric keys as the old 4-frame export
  - do not reopen codec or teacher-path selection inside this pass
- comparability risks:
  - the widened dataset root could violate the old PNG loader expectations if the directory layout drifted
  - config drift could silently change the old contract if the rerun does not use the recovered tiny config family
  - downstream exporters will stay blocked if the widened run does not reproduce the old output tree shape

## 3. Code Translation Plan

| Path | Current role | Planned change | Why this is needed | Risk |
|---|---|---|---|---|
| `experiments/main/scripts/extract_bounded_video_frames.py` | bounded PNG regeneration helper | keep as the source-of-truth extractor for the widened local sample surface | preserves the frozen-upstream contract while widening only the sample surface | low |
| `experiments/main/scripts/run_shared_gating_export_ego4d16f_smoke.sh` | widened upstream launch script | add one explicit rerun entrypoint with absolute config paths and bounded-surface overrides | leaves behind a rerunnable local command instead of a chat-only command recipe | low |
| `experiments/main/upstream_shared_gating_snapshot/third_party/NVRC/scripts/configs/*` | recovered frozen config family | reuse directly without editing | keeps the widened run tied to the same tiny contract as the old 4-frame export | low |
| `experiments/main/shared_gating_interface_export_ego4d16f_smoke_r1/` | widened upstream smoke output root | create a new export run directory under the active worktree | makes the next bridge step depend on durable widened outputs | low |
| `experiments/main/scripts/export_reconstructed_interface.py` | reconstructed-video exporter | reuse only after the widened upstream smoke succeeds | keeps the widened bundle comparable to the parent downstream control | low |
| `experiments/main/scripts/export_teacher_feature_interface.py` | teacher-packet exporter | reuse only after the widened upstream smoke succeeds | keeps the bridge step parallel to the validated packet route | low |

## 4. Execution Design

- minimal experiment:
  - run one `eval_only + resume_model_only` frozen export smoke on the widened 16-frame bounded PNG surface
  - keep the same tiny config family, checkpoint, and teacher supervision settings
  - validate that the widened run emits the expected bitstream, decoded outputs, and results summaries
- smoke / pilot plan:
  - verify the widened launch script resolves the recovered config family correctly
  - run the frozen upstream smoke on the 16-frame surface
  - confirm that `args.yaml`, `bitstreams/`, `outputs/0000/{decoded,eval}`, and `results/all.txt` all exist
  - confirm that the metric keys stay legible against the old 4-frame export control
- expected outputs:
  - one rerunnable widened-export launch script
  - one 16-frame widened export smoke directory with args, logs, decoded outputs, and metric summaries
  - one explicit judgment on whether the widened bundle is ready for reconstructed/teacher bridge export
- stop condition:
  - the widened export smoke runs end to end and produces a bundle compatible with the downstream exporters
- abandonment condition:
  - the widened dataset root cannot satisfy the old PNG loader assumptions
  - the recovered tiny config family cannot reproduce the old contract without ad hoc edits
  - the widened output tree is incompatible with the downstream exporter expectations

## 5. Runtime Strategy

- immediate next actions:
  - write the widened export launch script inside the active worktree
  - sync the control docs to the widened rerun route
  - run the 16-frame frozen export smoke and inspect the output tree before any new bridge comparison
- artifact locations:
  - old 4-frame export root:
    `../idea-idea-301dcd71/experiments/main/shared_gating_interface_export_smoke_r1/`
  - widened bounded surface:
    `tmp/ego4d_bounded_bridge_r1/data/ego4d_small_bridge_16f/`
  - new widened export root:
    `experiments/main/shared_gating_interface_export_ego4d16f_smoke_r1/`
- safe efficiency levers:
  - keep the run `eval_only`
  - keep `resume_model_only=true`
  - keep `workers=0` and the tiny config family
  - widen only the bounded local sample surface, not the codec contract

## 6. Fallbacks And Recovery

- if the direct config launch still drifts:
  - fall back to a very thin parameter-replay wrapper seeded from the old resolved `args.yaml`
- if the widened dataset root still fails loader assumptions:
  - regenerate the bounded surface again under the exact old tiny dataset layout
- if the widened export succeeds but metrics degrade sharply:
  - still accept the widened bundle for bridge comparison, but record the export-quality downgrade explicitly
- if the widened export does not produce downstream-compatible outputs:
  - stop before a new bridge run and classify the blocker as an upstream interface issue, not a bridge result

## 7. Checklist Link

- checklist path: `CHECKLIST.md`
- next unchecked item: write and run the widened frozen export smoke entrypoint
