# Main Experiment Plan

## 1. Objective

- run id: `shared_gating_downstream_interface_bootstrap_r1`
- selected idea in `1-2` sentences: Freeze the inherited `shared_semantic_gated_dual_path_tiny_local_r1` upstream module from quest 001 instead of reopening upstream route selection. Reuse the validated original/reconstructed interface bundle inside quest 002, then run one minimal downstream consumer comparison on original vs reconstructed frames.
- user's core requirements:
  - link the current compression layer to a larger downstream model stack through a runnable pipeline
  - produce a first result batch that shows what the output looks like and whether the direction is worth pursuing
  - keep the main innovation centered on pipeline building, even if algorithm novelty is only moderate in this round
  - end with code that can be rerun locally and later shared as a GitHub-ready repo
- non-negotiable user constraints:
  - do not reopen the old upstream ranking unless new evidence forces it
  - inherit the prior quest's paper-facing upstream line rather than plain baseline-only NVRC
  - keep the accepted baseline contract visible and do not misstate downstream results as new compression-benchmark wins
  - start with one minimal downstream task before any broader VLM or LLM demo
- current pass objective: keep the upstream module frozen, treat the validated interface bundle as the input contract, and add the first frozen downstream consumer evaluation
- research question: Can the frozen shared semantic-gated dual-path upstream line support a minimal downstream retrieval or matching task when the consumer only sees original or reconstructed frames?
- null hypothesis: The frozen upstream interface cannot be packaged reproducibly in the new quest, or a frozen downstream consumer cannot preserve identity-level retrieval well enough to justify further pipeline expansion.
- alternative hypothesis: The inherited module can be packaged reproducibly, a minimal downstream consumer can run end to end on original and reconstructed frames, and the resulting gap is bounded enough to justify a second-stage feature-packet or larger-model interface.

## 2. Baseline And Comparability

- baseline id: `nvrc-local-source`
- baseline variant: `tiny-local-teacher-pilot-r3`
- dataset / split:
  - inherited upstream anchor: tiny-local synthetic, 4 frames, 32x32, 1 epoch, repaired resnet18 teacher path
  - downstream bootstrap surface: the same fixed clip identities exported from the inherited shared-gating line, with exact original/reconstructed pairing
- primary metric: `tiny_local_teacher_pilot_teacher_mse_avg` stays the inherited upstream guardrail metric; new downstream metrics are additive rather than replacing the accepted contract
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
- reproduced quest-002 frozen-upstream bootstrap metrics:
  - `bpp_avg=88.2266`
  - `psnr_avg=10.9012`
  - `teacher-mse_avg=0.5126`
- comparability risks:
  - the imported baseline package in quest 002 contains metrics and verification only, not executable code
  - downstream task metrics are new and should be reported as downstream utility signals, not as replacements for the accepted compression comparison surface
  - if the frozen upstream tree drifts from the inherited shared-gating run, the round becomes an implementation-change run rather than a pure frozen-upstream bootstrap
  - if the downstream consumer cannot separate the original-frame control set, the round is not informative enough to justify a broader claim

## 3. Code Translation Plan

| Path | Current role | Planned change | Why this is needed | Risk |
|---|---|---|---|---|
| `experiments/main/upstream_shared_gating_snapshot/third_party/NVRC/` | quest-local frozen upstream source snapshot | keep the vendored tree frozen during downstream bootstrap and reuse it only for export and smoke | quest 002 now has a rerunnable upstream anchor without reopening codec-line ranking | low |
| `experiments/main/upstream_shared_gating_snapshot/tools/smoke_teacher_loss.py` | quest-local teacher smoke entrypoint | keep as the minimal repaired-teacher validation surface when needed | preserves the smallest sanity check around the inherited teacher path | low |
| `experiments/main/upstream_shared_gating_snapshot/PROVENANCE.md` | provenance note | pin quest-001 origin, inherited checkpoint, and the allowed eval-only reuse path | makes the frozen-upstream contract auditable and shareable | low |
| `experiments/main/scripts/export_reconstructed_interface.py` | implemented export helper | keep the manifest schema stable and reuse it for downstream consumption | this is the new machine-facing interface layer the user actually asked for | low |
| `experiments/main/interface_bundles/shared_gating_interface_export_smoke_r1/manifest.json` | validated interface bundle | treat the bundle as the frozen input contract for the first downstream smoke | avoids rerunning upstream export for every downstream retry | low |
| `experiments/main/scripts/run_frozen_consumer_eval.py` | new | run a frozen `torchvision` retrieval or matching consumer on original and reconstructed inputs and emit comparison tables | needed for the first output batch and first original-vs-reconstructed downstream comparison | medium |
| `experiments/main/shared_gating_downstream_interface_bootstrap_r1/downstream_eval/` | planned output root | store similarity matrices, retrieval metrics, and sample matches | keeps the downstream result batch self-contained and GitHub-shareable | low |

## 4. Execution Design

- minimal experiment: the frozen shared-gating upstream line is already exported as a validated paired bundle; the next step is to run one frozen `torchvision` retrieval or matching consumer on original and reconstructed inputs to produce an interpretable first comparison table
- smoke / pilot plan:
  - completed: vendor the upstream source snapshot into quest 002
  - completed: confirm the vendored tree can reuse the inherited checkpoint without retraining
  - completed: export one paired bundle from the inherited shared-gating configuration
  - next: run the downstream consumer on the validated 4-frame bundle and verify the retrieval outputs are structurally valid
- full run plan:
  - reuse the validated paired original/reconstructed bundle from the frozen shared-gating line
  - embed original frames with a frozen pretrained `torchvision` encoder to form the gallery and control queries
  - embed reconstructed frames with the same frozen encoder and compare them against the original-frame gallery
  - compute cosine similarity matrices, top-1 retrieval accuracy, and diagonal similarity gaps, then produce a sample output batch for inspection
- expected outputs:
  - quest-local frozen upstream source snapshot
  - provenance note for the frozen upstream source
  - paired original/reconstructed interface bundle with metadata manifest
  - first downstream comparison table in JSON or Markdown
  - similarity matrix and sample matches that the user can inspect directly
- stop condition: one end-to-end bounded batch runs cleanly from the validated interface bundle through downstream comparison, and the result table is interpretable enough to support a route decision
- abandonment condition:
  - the inherited shared-gating settings cannot be reproduced closely enough to trust the frozen-upstream contract
  - the frozen `torchvision` consumer cannot load pretrained weights or cannot separate even the original-frame control set
  - the intended downstream consumer path produces malformed or unpaired outputs
- strongest alternative hypothesis: the reconstructed-video interface may be too lossy or awkward, and the next serious route may need a feature-packet or teacher-feature consumer instead

## 5. Runtime Strategy

- completed commands:
  - upstream replay:
    `conda run -n NVRC python main_nvrc.py --cfg scripts/configs/nvrc/overfit/tiny-1e.yaml scripts/configs/data/video/png/tiny_local.yaml scripts/configs/nvrc/compress_models/nvrc_tiny_s1.yaml scripts/configs/nvrc/models/teacher_tiny_32.yaml scripts/configs/tasks/overfit/l1_teacher-resnet18-shared-semchange-delta.yaml --resume /home/xinyizheng/vid_tokenizer/DeepScientist/quests/001/.ds/worktrees/shared-semantic-gated-dual-path-tiny-local-r1/experiments/main/shared_semantic_gated_dual_path_tiny_local_r1 --resume-model-only true --eval-only true --eval-enable-log true --output experiments/main/shared_gating_interface_export_smoke_r1`
  - bundle export:
    `conda run -n NVRC python experiments/main/scripts/export_reconstructed_interface.py --source-run-dir experiments/main/shared_gating_interface_export_smoke_r1 --dataset-dir /home/xinyizheng/vid_tokenizer/DeepScientist/quests/001/tmp/teacher-tiny-run-v1/data/tiny_video --output-dir experiments/main/interface_bundles/shared_gating_interface_export_smoke_r1`
- next smoke command:
  - `conda run -n NVRC python experiments/main/scripts/run_frozen_consumer_eval.py --bundle-dir experiments/main/interface_bundles/shared_gating_interface_export_smoke_r1 --model resnet18 --mode smoke --output-dir experiments/main/shared_gating_downstream_interface_bootstrap_r1/downstream_eval`
- command for main run:
  - `conda run -n NVRC python experiments/main/scripts/run_frozen_consumer_eval.py --bundle-dir experiments/main/interface_bundles/shared_gating_interface_export_smoke_r1 --model resnet18 --mode full --output-dir experiments/main/shared_gating_downstream_interface_bootstrap_r1/downstream_eval`
- expected runtime / budget:
  - vendoring and upstream replay are already complete
  - first bounded downstream batch should stay under 10 minutes if pretrained `torchvision` weights are already cached; otherwise runtime is dominated by one model download
- log / artifact locations:
  - `experiments/main/shared_gating_downstream_interface_bootstrap_r1/`
  - `experiments/main/interface_bundles/shared_gating_interface_export_smoke_r1/`
  - `experiments/main/shared_gating_downstream_interface_bootstrap_r1/downstream_eval/`
- safe efficiency levers to use first:
  - freeze all inherited upstream weights and reuse the accepted quest-001 upstream metrics as context
  - reuse the already validated paired bundle instead of regenerating it across retries
  - keep the downstream consumer frozen and batch inference where possible
  - stay on the bounded 4-frame surface before any broader data expansion
- how existing tooling will be used efficiently:
  - use the already verified local NVRC source tree as provenance for vendoring
  - reuse the quest-001 shared-gating run record and config paths to avoid guessing settings
  - use pretrained `torchvision` weights already supported by the environment instead of adding a heavier new model stack in this round

## 6. Fallbacks And Recovery

- if the intended model or download path fails:
  - fall back from the pretrained `torchvision` encoder to a lighter local encoder or teacher-feature consumer, but keep the same original-vs-reconstructed comparison shape
- if hardware or memory is tighter than expected:
  - reduce clip count first, then frame count, while keeping exact pairing and a fixed evaluation recipe
- if the code path is wrong after smoke:
  - stop before the full run, repair the vendored upstream snapshot, and do not record downstream metrics from a drifted upstream implementation
- if the first full run becomes non-comparable:
  - downgrade the round to an interface-bootstrap report, record the break in comparability explicitly, and relaunch only after the frozen-upstream contract is restored

## 7. Checklist Link

- checklist path: `CHECKLIST.md`
- next unchecked item: implement and smoke `experiments/main/scripts/run_frozen_consumer_eval.py` on the validated interface bundle

## 8. Revision Log

| Time | What changed | Why it changed | Impact on comparability or runtime |
|---|---|---|---|
| 2026-04-14 | Created the first experiment contract for the downstream pipeline bootstrap. | The active idea line is selected and the inherited upstream anchor is now explicit enough to begin experiment work. | No runtime yet; comparability improves because the inherited shared-gating anchor replaces the earlier vague baseline-only assumption. |
| 2026-04-14 | Vendored the frozen upstream source, replayed the inherited checkpoint without retraining, and reproduced `bpp_avg=88.2266`, `psnr_avg=10.9012`, `teacher-mse_avg=0.5126` inside quest 002. | The downstream pipeline needs a quest-local, reproducible upstream anchor before any consumer-side comparison can be trusted. | Comparability stayed aligned with the inherited shared-gating line while runtime cost stayed low because the round reused the checkpoint instead of retraining. |
| 2026-04-14 | Exported and validated the first paired interface bundle with 4 original frames, 4 reconstructed frames, per-frame metrics, and aggregate metrics. | The user asked for a runnable machine-facing interface and an inspectable first result batch rather than only upstream logs. | The next downstream run can now reuse a fixed bundle, which lowers runtime variance and avoids accidental upstream drift. |
| 2026-04-14 | Narrowed the first downstream consumer to frozen `torchvision` retrieval or matching. | The environment already supports `torch` and `torchvision`, while heavier multimodal stacks are not installed. | This reduces integration risk for round one and keeps the first downstream signal focused on pipeline feasibility. |
