# vid_tokenizer: Machine-Oriented Video Compression Toolkit

This repository collects the current machine-oriented video compression work in
two reviewable layers:

1. An existing paper/evidence line for machine-facing packet evaluation.
2. This PR's project-style NVRC pipeline wrapper for teacher/tokenizer-aware
   compression experiments.

The shared idea is not ordinary human-viewing compression. The goal is to keep
compressed egocentric video useful for downstream machine understanding.

## Current Repository Context

The existing `main` line already contains a bounded paper-ready package around a
query-adaptive teacher-anchor retrieval surface:

- Upstream machine-oriented compression / packet interfaces can be exported.
- With a frozen packet surface, query-adaptive arbitration reaches headline
  `top1_accuracy = 0.15625` on the bounded teacher-anchor retrieval surface.
- This supports the claim that frozen packet outputs still contain
  downstream-recoverable structure.
- It does not yet prove a universal machine-facing adapter for long videos,
  larger consumers, or arbitrary custom datasets.

The new pipeline package in this PR adds a cleaner project entrypoint for the
NVRC-style codec side:

- `x -> NVRC-style compression -> x_hat`
- `x -> teacher/tokenizer -> y`
- `x_hat -> teacher/tokenizer -> y_hat`
- training signal: keep `y_hat` close to `y` while preserving the codec/rate
  contract.

## Quick Start: Small Demo

The small demo requires no GPU and does not train NVRC. It creates two synthetic
result folders and compares them with the same parser and ranking rule used for
real runs.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"

python -m machine_codec_pipeline list-profiles
python -m machine_codec_pipeline demo --output-root runs/readme_demo
python -m machine_codec_pipeline compare \
  runs/readme_demo/bootstrap_demo \
  runs/readme_demo/shared_semchange_delta_demo
```

Expected demo files:

```text
runs/readme_demo/bootstrap_demo/results/all.txt
runs/readme_demo/bootstrap_demo/pipeline_summary.json
runs/readme_demo/shared_semchange_delta_demo/results/all.txt
runs/readme_demo/shared_semchange_delta_demo/pipeline_summary.json
runs/readme_demo/demo_compare.json
```

The comparison sorts by lower `teacher-mse_avg`, then higher `psnr_avg`, then
lower `bpp_avg`.

## Project Layout

```text
.
├── src/machine_codec_pipeline/            # Packaged CLI and orchestration code
├── tools/run_machine_codec_pipeline.py    # Backward-compatible wrapper script
├── docs/machine_codec_pipeline.md         # Full NVRC pipeline link graph
├── patches/nvrc_machine_oriented_pipeline.patch
│                                           # NVRC-side teacher-aware codec patch
├── third_party/NVRC/                      # NVRC codec submodule
├── tests/                                 # Lightweight package tests
├── paper/                                 # Existing paper bundle and evidence
├── experiments/main/                      # Existing experiment scripts/results
├── baselines/                             # Confirmed baseline records
└── PR_LOCAL_REVIEW.md                     # Existing paper-line PR notes
```

## Pipeline Modules

1. Codec backbone
   `third_party/NVRC/main_nvrc.py` runs the train, encode, decode, and evaluate
   loop for the INR/NVRC codec.

2. Teacher/tokenizer supervision
   The NVRC patch adds `teacher_utils.py` plus teacher-aware task and loss
   wiring so reconstructed video can be supervised through frozen teacher
   features.

3. Profile registry
   `src/machine_codec_pipeline/profiles.py` maps experiment names such as
   `bootstrap`, `semchange_delta`, and `shared_semchange_delta` to concrete
   NVRC task configs and smoke-test arguments.

4. Launcher and bookkeeping
   `src/machine_codec_pipeline/cli.py` provides one command surface for smoke
   checks, bounded runs, comparisons, and the small local demo.

5. Output contract
   Full runs write native NVRC outputs plus `pipeline_summary.json`, which
   records the selected profile, command, experiment directory, and parsed
   aggregate metrics.

## NVRC Patch Note

The outer Python package and small demo work without modifying NVRC. For full
teacher-aware codec training, apply the included NVRC patch first:

```bash
cd third_party/NVRC
git am ../../patches/nvrc_machine_oriented_pipeline.patch
```

The patch adds the frozen-teacher adapter, teacher-aware losses/tasks, tiny
local configs, and the `shared_semchange_delta` profile used by the bounded
research run. It is included as a patch because the upstream NVRC submodule
remote requires separate push credentials. Once an accessible NVRC branch exists,
the patch can be replaced by a normal submodule pointer update.

## Smoke Check A Real Profile

Use this before a full experiment to verify the teacher/tokenizer command path:

```bash
python -m machine_codec_pipeline smoke \
  --profile shared_semchange_delta \
  --dry-run
```

Remove `--dry-run` when the NVRC environment is installed and the teacher smoke
script can run locally.

The old script path remains valid:

```bash
python tools/run_machine_codec_pipeline.py smoke \
  --profile shared_semchange_delta \
  --dry-run
```

## Run A Bounded NVRC Pilot

Start with `--dry-run` to inspect the exact NVRC command before spending
compute:

```bash
python -m machine_codec_pipeline run \
  --profile shared_semchange_delta \
  --exp-name shared_semchange_delta_tiny_local_r1 \
  --dataset-dir /abs/path/to/data \
  --dataset tiny_video \
  --video-size 4 32 32 \
  --patch-size 1 32 32 \
  --epochs 1 \
  --warmup-epochs 0 \
  --eval-epochs 1 \
  --rate-steps 1 \
  --workers 0 \
  --dry-run
```

When `--dry-run` is removed, the launcher delegates to:

```text
third_party/NVRC/main_nvrc.py
```

and expects NVRC to write:

```text
runs/<exp-name>/results/all.txt
```

After that, the launcher writes:

```text
runs/<exp-name>/pipeline_summary.json
```

## Compare Real Runs

```bash
python -m machine_codec_pipeline compare \
  runs/bootstrap_tiny_local \
  runs/shared_semchange_delta_tiny_local
```

Each argument can be either an experiment directory containing
`results/all.txt` or a direct path to a result file.

## Existing Paper-Line Reading Order

For the existing paper/evidence package on `main`, use this order:

1. `PR_LOCAL_REVIEW.md`
   Explains what the current local PR/evidence line is meant to deliver.
2. `paper/draft.md`
   Manuscript body with method, results, and scoped limitations.
3. `paper/review/review.md`
   Skeptical review of the current claims and boundaries.
4. `docs/LEARNING_PATH.md`
   Walkthrough of the existing code and data assets.
5. `docs/LONG_VIDEO_CUSTOM_DATA_GUIDE.md`
   Operational guide for longer videos and custom data.

The most direct bounded smoke entry for that existing line is:

```bash
./experiments/main/scripts/run_querybank_teacher_anchor_smoke.sh
```

## Current Research Boundary

The new NVRC pipeline package validates orchestration, demo execution, result
parsing, and command construction. The current bounded research evidence
supports the local/proxy teacher-MSE trend for `shared_semchange_delta`, but it
should not yet be described as a fully validated real-egocentric codec or a
universal one-shot compression model. Full egocentric, UVG, or MCL validation
remains the next research step.
