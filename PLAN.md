# Main Experiment Plan

## 1. Objective

- run id: `shared_gating_downstream_interface_bootstrap_r1`
- selected idea in `1-2` sentences: Freeze the inherited `shared_semantic_gated_dual_path_tiny_local_r1` upstream module from quest 001 instead of reopening upstream route selection. Build a quest-local machine-facing interface around reconstructed video plus aligned metadata, then run one minimal downstream consumer comparison on original vs reconstructed clips.
- user's core requirements:
  - link the current compression layer to larger-model layers through a runnable pipeline
  - produce a first result batch that shows what the output looks like and whether the direction is worth pursuing
  - keep the main innovation centered on pipeline building, even if algorithm novelty is only moderate in this round
  - end with code that can be rerun locally and later shared as a GitHub-ready repo
- non-negotiable user constraints:
  - do not reopen the old upstream ranking unless new evidence forces it
  - inherit the prior quest's paper-facing upstream line rather than plain baseline-only NVRC
  - keep the accepted baseline contract visible and do not misstate downstream results as new compression-benchmark wins
  - start with one minimal downstream task before any broader VLM or LLM demo
- research question: Can the frozen shared semantic-gated dual-path upstream line be exported as reconstructed clips plus aligned metadata in a way that supports a minimal downstream machine-consumer comparison on original vs reconstructed inputs?
- null hypothesis: After the inherited module is frozen, either the interface cannot be packaged reproducibly in the new quest, or the downstream original-vs-reconstructed gap is too large or too unstable to justify further pipeline expansion.
- alternative hypothesis: The inherited module can be packaged reproducibly, a minimal downstream consumer can run end to end on original and reconstructed clips, and the resulting gap is bounded enough to justify a second-stage feature-packet or larger-model interface.

## 2. Baseline And Comparability

- baseline id: `nvrc-local-source`
- baseline variant: `tiny-local-teacher-pilot-r3`
- dataset / split:
  - inherited upstream anchor: tiny-local synthetic, 4 frames, 32x32, 1 epoch, repaired resnet18 teacher path
  - downstream bootstrap surface: the same fixed clip identities exported from the inherited shared-gating line, with exact original/reconstructed pairing
- primary metric: `tiny_local_teacher_pilot_teacher_mse_avg` stays the inherited upstream guardrail metric; new downstream metrics will be additive rather than replacing the accepted contract
- required metric keys:
  - `uvg_bd_rate_reduction_pct_vs_vtm_ra_psnr`
  - `local_resnet18_teacher_smoke_loss_value`
  - `tiny_local_teacher_pilot_bpp_avg`
  - `tiny_local_teacher_pilot_psnr_avg`
  - `tiny_local_teacher_pilot_teacher_mse_avg`
  - `beauty_teacher_smoke_bpp_avg`
  - `beauty_teacher_smoke_psnr_avg`
  - `beauty_teacher_smoke_teacher_mse_avg`
  - `beauty_no_teacher_partial_teacher_mse`
- comparability risks:
  - the imported baseline package in quest 002 contains metrics and verification only, not executable code
  - the inherited upstream line comes from quest 001 and must be vendored or mirrored into quest 002 without silently changing behavior
  - downstream task metrics are new and should be reported as downstream utility signals, not as replacements for the accepted compression comparison surface
  - if vendored code or configs drift from the inherited shared-gating run, the round becomes an implementation-change run rather than a pure frozen-upstream bootstrap

## 3. Code Translation Plan

Map the idea into concrete code changes.

| Path | Current role | Planned change | Why this is needed | Risk |
|---|---|---|---|---|
| `experiments/main/upstream_shared_gating_snapshot/third_party/NVRC/` | empty in quest 002 | vendor a frozen source snapshot from the verified local NVRC tree and pin provenance to the quest 001 shared-gating run | the current quest has no executable upstream code, so the pipeline cannot be rerun or shared without a quest-local source copy | medium |
| `experiments/main/upstream_shared_gating_snapshot/tools/smoke_teacher_loss.py` | empty in quest 002 | bring over the verified teacher smoke entrypoint used to validate the repaired teacher path | preserves the smallest smoke needed to confirm the vendored upstream path still works | low |
| `experiments/main/configs/shared_gating_downstream_interface_bootstrap_r1.yaml` | new | pin the inherited shared-gating settings plus export/output parameters for the downstream bootstrap | makes the frozen-upstream contract explicit inside quest 002 instead of relying on quest 001 paths | medium |
| `experiments/main/scripts/export_reconstructed_interface.py` | new | export original ids, reconstructed clips or frames, and aligned teacher-side metadata from the frozen upstream module | this is the new machine-facing interface layer the user actually asked for | medium |
| `experiments/main/scripts/run_frozen_consumer_eval.py` | new | run one minimal frozen downstream consumer on original and reconstructed inputs and emit comparable outputs | needed for the first output batch and first original-vs-reconstructed downstream comparison | medium |
| `experiments/main/shared_gating_downstream_interface_bootstrap_r1/` | new output root | store args, logs, exported interface objects, downstream results, and summary tables | keeps the new quest self-contained and GitHub-shareable | low |

## 4. Execution Design

- minimal experiment: freeze the inherited shared-gating upstream line, export a tiny paired batch of original and reconstructed clips with aligned metadata, and run one frozen downstream consumer on both sides to produce an interpretable first comparison table
- smoke / pilot plan:
  - vendor the upstream source snapshot into quest 002
  - confirm the vendored tree exposes the repaired teacher path and the shared-gating config entrypoint
  - export one paired clip or clip-batch from the inherited shared-gating configuration
  - run the downstream consumer on a 1-2 clip smoke batch and verify outputs are structurally valid
- full run plan:
  - export a fixed bounded set of paired original/reconstructed samples from the frozen shared-gating line
  - run the same frozen downstream consumer on both input modes
  - compute at least one paired downstream utility metric and produce a sample output batch for inspection
  - if the first reconstructed-video interface is stable, optionally include aligned metadata in the exported bundle without changing the consumer route mid-run
- expected outputs:
  - quest-local frozen upstream source snapshot
  - quest-local shared-gating export config
  - paired original/reconstructed interface bundle with metadata manifest
  - first downstream comparison table in JSON or Markdown
  - sample outputs that the user can inspect directly
- stop condition: one end-to-end bounded batch runs cleanly from frozen upstream export through downstream comparison, and the result table is interpretable enough to support a route decision
- abandonment condition:
  - vendored upstream code cannot be made runnable without reopening broad upstream debugging
  - the inherited shared-gating settings cannot be reproduced closely enough to trust the frozen-upstream contract
  - the intended downstream consumer is unavailable locally and even the lighter fallback cannot produce a bounded first batch
- strongest alternative hypothesis: the reconstructed-video interface may be too lossy or awkward, and the next serious route may need a feature-packet or teacher-feature consumer instead

## 5. Runtime Strategy

- command for smoke:
  - `python experiments/main/scripts/export_reconstructed_interface.py --config experiments/main/configs/shared_gating_downstream_interface_bootstrap_r1.yaml --limit 1 --mode smoke`
  - `python experiments/main/scripts/run_frozen_consumer_eval.py --config experiments/main/configs/shared_gating_downstream_interface_bootstrap_r1.yaml --limit 2 --mode smoke`
- command for main run:
  - `python experiments/main/scripts/export_reconstructed_interface.py --config experiments/main/configs/shared_gating_downstream_interface_bootstrap_r1.yaml --mode full`
  - `python experiments/main/scripts/run_frozen_consumer_eval.py --config experiments/main/configs/shared_gating_downstream_interface_bootstrap_r1.yaml --mode full`
- expected runtime / budget:
  - vendoring and smoke: under 10 minutes if the inherited tree is intact
  - first bounded downstream batch: 30-90 minutes depending on consumer size and caching
- log / artifact locations:
  - `experiments/main/shared_gating_downstream_interface_bootstrap_r1/`
  - `experiments/main/shared_gating_downstream_interface_bootstrap_r1/logs/`
  - `experiments/main/shared_gating_downstream_interface_bootstrap_r1/exports/`
  - `experiments/main/shared_gating_downstream_interface_bootstrap_r1/results/`
- safe efficiency levers to use first:
  - freeze all inherited upstream weights and reuse the accepted quest 001 upstream metrics as context
  - start with the same bounded tiny-local surface before any broader data expansion
  - cache exported reconstructions and metadata instead of regenerating them across retries
  - keep the downstream consumer frozen and batch inference where possible
  - prefer a smaller bounded consumer batch over a large first run
- how existing tooling will be used efficiently:
  - use the already verified local NVRC source tree as provenance for vendoring
  - reuse the quest 001 shared-gating run record and config paths to avoid guessing settings
  - carry forward the accepted teacher smoke only when the vendored code path is unchanged; otherwise rerun the smoke explicitly

Monitoring and sleep plan:

- wait cadence:
  - `60s`
  - `120s`
  - `300s`
  - `600s`
  - `1800s`
- health signals that justify continuing to monitor:
  - export directory grows with paired artifacts
  - downstream logs show batch completion and metric accumulation
  - no new traceback or import failure appears after the initial steps
- conditions that trigger kill / relaunch:
  - vendored path cannot import or reproduce the inherited shared-gating config
  - outputs are empty, malformed, or mispaired after the smoke
  - downstream consumer crashes consistently on the same bounded batch without producing usable outputs

## 6. Fallbacks And Recovery

- if the intended model / endpoint / download path fails:
  - fall back from a heavier video-language consumer to a lighter frozen local encoder or teacher-feature consumer, but keep the same original-vs-reconstructed comparison shape
- if hardware or memory is tighter than expected:
  - reduce clip count first, then frame count, while keeping exact pairing and a fixed evaluation recipe
- if the code path is wrong after smoke:
  - stop before the full run, repair the vendored upstream snapshot, and do not record downstream metrics from a drifted upstream implementation
- if the first full run becomes non-comparable:
  - downgrade the round to an interface-bootstrap report, record the break in comparability explicitly, and relaunch only after the frozen-upstream contract is restored

## 7. Checklist Link

- checklist path: `CHECKLIST.md`
- next unchecked item: vendor the frozen shared-gating upstream source snapshot into quest 002 and pin its provenance to the inherited run record

## 8. Revision Log

| Time | What changed | Why it changed | Impact on comparability or runtime |
|---|---|---|---|
| 2026-04-14 | Created the first experiment contract for the downstream pipeline bootstrap. | The active idea line is selected and the inherited upstream anchor is now explicit enough to begin experiment work. | No runtime yet; comparability improves because the inherited shared-gating anchor replaces the earlier vague baseline-only assumption. |
