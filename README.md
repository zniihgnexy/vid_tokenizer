# vid_tokenizer

`vid_tokenizer` is a machine-oriented video compression project built around an
NVRC-style codec pipeline. The repository is organized as a GitHub-style
engineering repo: active code and user-facing docs stay at the top level,
historical notes and process material are archived under `arxiv/`.

The current packaged pipeline covers four things:

1. turn one raw video into a PNG-frame dataset
2. run one bounded or chunked NVRC experiment profile
3. collect structured run summaries under a consistent output contract
4. compare original vs reconstructed video with an OpenAI vision model

## Repository Guide

- `src/machine_codec_pipeline/`
  Main Python package and CLI.
- `docs/`
  User-facing setup, structure, and pipeline docs.
- `outputs/`
  Canonical output area for demos, run artifacts, and tracked examples.
- `patches/nvrc_machine_oriented_pipeline.patch`
  NVRC-side teacher-aware patch.
- `third_party/NVRC/`
  NVRC submodule.
- `arxiv/legacy_notes/`
  Archived Markdown notes, handoffs, and old process material.

The fastest follow-up docs are:

1. `docs/PROJECT_STRUCTURE.md`
2. `docs/machine_codec_pipeline.md`
3. `docs/LONG_VIDEO_CUSTOM_DATA_GUIDE.md`

## Environment Setup

### 1. Clone with submodules

```bash
git clone --recursive <your-repo-url>
cd vid_tokenizer
```

If you already cloned the repo without submodules:

```bash
git submodule update --init --recursive
```

### 2. Create a Python environment

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

The packaged CLI depends on `pillow`. Real NVRC runs also need the NVRC-side
runtime stack such as `torch`, `torchvision`, `pyyaml`, and `accelerate`.

### 3. Install `ffmpeg`

`prepare-video` and the OpenAI report helpers rely on `ffmpeg`.

Quick check:

```bash
ffmpeg -version
```

### 4. Apply the NVRC patch before real codec runs

The outer Python package works without modifying NVRC, but teacher-aware codec
training and the current experiment profiles expect the bundled NVRC patch:

```bash
cd third_party/NVRC
git am ../../patches/nvrc_machine_oriented_pipeline.patch
cd ../..
```

### 5. Configure the OpenAI key

Create a local `.env` file from the example:

```bash
cp .env.example .env
```

Then set:

```bash
OPENAI_API_KEY=your_key_here
```

The OpenAI comparison commands first read `OPENAI_API_KEY` from the process
environment, then fall back to the repo-local `.env`.

## Quick Command Index

After `pip install -e .`, you can use either form:

```bash
machine-codec --help
python -m machine_codec_pipeline --help
```

Main commands:

- `machine-codec list-profiles`
- `machine-codec demo`
- `machine-codec prepare-video`
- `machine-codec run`
- `machine-codec run-chunked`
- `machine-codec compare`
- `machine-codec video-qa-report`
- `machine-codec video-qa-chunked-report`

## Canonical Output Layout

The repository now treats `outputs/` as the main project output surface.

```text
outputs/
├── demo/            # tiny local demo outputs
├── examples/        # lightweight tracked example artifacts
├── runs/            # full local run artifacts (ignored by Git)
└── video_windows/   # extracted PNG windows and chunk indices
```

Tracked examples live under `outputs/examples/` and should stay lightweight:
contact sheets, compact summaries, and human-readable reports. Full chunk-level
run artifacts belong under `outputs/runs/` and extracted frame windows under
`outputs/video_windows/`; both are ignored by Git.

The current curated real-video example is:

- `outputs/examples/ego4d_real_full_video_openai/`

It keeps the OpenAI QA report, both contact sheets, compact public metrics, and
raw model answers, while the much heavier chunk-level codec artifacts stay in
the local-only run area.

## Quick Smoke Demo

This path does not train NVRC. It creates two tiny synthetic result folders and
checks that the comparison layer is working.

```bash
machine-codec list-profiles
machine-codec demo --output-root outputs/demo/readme_demo
machine-codec compare \
  outputs/demo/readme_demo/bootstrap_demo \
  outputs/demo/readme_demo/shared_semchange_delta_demo
```

Expected files:

```text
outputs/demo/readme_demo/bootstrap_demo/results/all.txt
outputs/demo/readme_demo/bootstrap_demo/pipeline_summary.json
outputs/demo/readme_demo/shared_semchange_delta_demo/results/all.txt
outputs/demo/readme_demo/shared_semchange_delta_demo/pipeline_summary.json
outputs/demo/readme_demo/demo_compare.json
```

## End-to-End Pipeline For One Real Video

### Step 1. Extract a bounded or full-video window

Example: extract a 64-frame window from one video and also create chunked frame
datasets.

```bash
machine-codec prepare-video \
  --video-path /abs/path/to/ego4d_video.mp4 \
  --output-dir outputs/video_windows/ego4d_64f \
  --start-frame 0 \
  --num-frames 64 \
  --width 32 \
  --height 32 \
  --chunk-size 16 \
  --chunk-output-root outputs/video_windows/ego4d_64f_chunks \
  --overwrite
```

Expected artifacts:

```text
outputs/video_windows/ego4d_64f/extraction_manifest.json
outputs/video_windows/ego4d_64f/prepare_video_summary.json
outputs/video_windows/ego4d_64f_chunks/ego4d_64f_chunk00/
outputs/video_windows/ego4d_64f_chunks/ego4d_64f_chunk_index.json
```

### Step 2. Run the codec pipeline on the extracted data

For one bounded dataset:

```bash
machine-codec run \
  --profile shared_semchange_delta \
  --exp-name ego4d_64f_shared_semchange_delta \
  --dataset-dir outputs/video_windows \
  --dataset ego4d_64f \
  --video-size 4 32 32 \
  --patch-size 1 32 32 \
  --epochs 1 \
  --warmup-epochs 0 \
  --eval-epochs 1 \
  --rate-steps 1 \
  --workers 0 \
  --output-root outputs/runs
```

For a longer or full video that has already been chunked:

```bash
machine-codec run-chunked \
  --profile shared_semchange_delta \
  --chunk-index outputs/video_windows/ego4d_64f_chunks/ego4d_64f_chunk_index.json \
  --exp-name-prefix ego4d_64f_shared_semchange_delta \
  --output-root outputs/runs \
  --epochs 1 \
  --warmup-epochs 0 \
  --eval-epochs 1 \
  --rate-steps 1 \
  --workers 0 \
  --eval-enable-log
```

Notes:

- `--eval-enable-log` is important when you later want to build reconstructed
  contact sheets for downstream QA.
- `run-chunked` can infer `video-size` and `patch-size` from chunk manifests
  created by `prepare-video`.

### Step 3. Run the downstream OpenAI comparison

Once the chunked summary JSON exists, run the original-vs-reconstructed QA
comparison:

```bash
machine-codec video-qa-chunked-report \
  --chunked-summary outputs/runs/ego4d_64f_shared_semchange_delta_chunked_summary.json \
  --model gpt-4.1-mini \
  --question "Taking into account all the actions performed by c, what can you deduce about the primary objective and focus within the video content?" \
  --option "C is cooking." \
  --option "C is doing laundry." \
  --option "C is cleaning the kitchen." \
  --option "C is cleaning dishes." \
  --option "C is cleaning the bathroom." \
  --answer-index 3 \
  --sample-count 12 \
  --output-dir outputs/runs/ego4d_64f_openai_qa
```

Expected files:

```text
outputs/runs/ego4d_64f_openai_qa/original_contact_sheet.png
outputs/runs/ego4d_64f_openai_qa/reconstructed_contact_sheet.png
outputs/runs/ego4d_64f_openai_qa/original_response.json
outputs/runs/ego4d_64f_openai_qa/reconstructed_response.json
outputs/runs/ego4d_64f_openai_qa/summary.json
outputs/runs/ego4d_64f_openai_qa/report.md
```

If `--output-dir` is omitted, the command writes into a default
`downstream_llm/openai-<model>` folder next to the source report or chunked
summary parent directory.

## How To Change The LLM Model

The current implementation exposes OpenAI as the packaged downstream example.

### Change only the model name

Use `--model`:

```bash
machine-codec video-qa-chunked-report \
  --chunked-summary outputs/runs/your_summary.json \
  --model gpt-4.1 \
  --question "..." \
  --option "A" \
  --option "B" \
  --answer-index 0
```

The same applies to `video-qa-report`.

### Change the provider implementation

Right now `--provider` is intentionally restricted to `openai`. If you want to
plug in Gemini or another VLM/LLM provider, the main integration points are:

- `src/machine_codec_pipeline/video_qa.py`
- `src/machine_codec_pipeline/cli.py`

That is where provider selection, request formatting, and response parsing are
currently defined.

## How To Change The Dataset Or Video Path

The pipeline is now designed around a few explicit path knobs:

### Use a different raw video

Change `--video-path` on `prepare-video`:

```bash
machine-codec prepare-video \
  --video-path /abs/path/to/another_video.mp4 \
  --output-dir outputs/video_windows/another_video_64f \
  --num-frames 64
```

### Use a different extracted PNG dataset

For bounded runs, change:

- `--dataset-dir`
- `--dataset`

Example:

```bash
machine-codec run \
  --profile shared_semchange_delta \
  --exp-name custom_dataset_run \
  --dataset-dir /abs/path/to/png_datasets \
  --dataset my_dataset_name
```

### Use a different chunked dataset

For longer videos, change `--chunk-index`:

```bash
machine-codec run-chunked \
  --profile shared_semchange_delta \
  --chunk-index /abs/path/to/my_chunk_index.json \
  --exp-name-prefix my_video_profile \
  --output-root outputs/runs
```

### Move outputs somewhere else

Every major stage accepts an explicit output path:

- `prepare-video --output-dir`
- `prepare-video --chunk-output-root`
- `run --output-root`
- `run-chunked --output-root`
- `video-qa-report --output-dir`
- `video-qa-chunked-report --output-dir`

## Included Example Outputs

The repository keeps a tracked example bundle under `outputs/examples/` so the
current pipeline has a concrete reference artifact inside the code repo itself.

Use it as:

- a layout reference
- a sanity check for expected summary/report files
- a quick way to inspect what one OpenAI comparison bundle looks like

## Historical Material

Older root Markdown files, handoff notes, and process-heavy documentation are
preserved under:

```text
arxiv/legacy_notes/
```

That archive is for history and reference, not for the main day-to-day project
entry surface.
