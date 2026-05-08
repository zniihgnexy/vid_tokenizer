# Project Structure

This repository now separates three layers clearly:

1. active engineering code and docs
2. canonical project outputs
3. archived notes and historical materials

## Top-Level Layout

```text
.
├── README.md
├── pyproject.toml
├── src/machine_codec_pipeline/      # packaged CLI and orchestration code
├── tests/                           # lightweight regression tests
├── docs/                            # user-facing docs
├── outputs/                         # canonical output area
├── patches/                         # NVRC patch files
├── third_party/NVRC/                # codec submodule
├── experiments/                     # experiment-side scripts kept in repo
├── paper/                           # paper and review materials
├── baselines/                       # baseline records
├── artifacts/                       # DeepScientist durable artifacts
├── memory/                          # quest memory and requirement snapshots
├── DeepScientist/                   # quest runtime root
└── arxiv/                           # archived notes and historical material
```

## What Lives In `outputs/`

```text
outputs/
├── README.md
├── demo/            # small synthetic demo outputs
├── examples/        # lightweight tracked reference outputs
├── runs/            # default location for new real runs
└── video_windows/   # extracted PNG windows and chunk indices
```

Recommended rule:

- keep `outputs/examples/` in Git only when the bundle is lightweight and
  directly useful for humans, such as a report, contact sheets, and a compact
  public summary
- treat `outputs/runs/` and `outputs/video_windows/` as local working outputs
- if one example generates large checkpoints, decoded frames, or rank logs,
  keep those under the ignored `outputs/runs/` area instead of the tracked
  `outputs/examples/` area

## What Lives In `docs/`

- `docs/PROJECT_STRUCTURE.md`
  This file; explains the repo layout.
- `docs/machine_codec_pipeline.md`
  Command-level pipeline reference.
- `docs/LONG_VIDEO_CUSTOM_DATA_GUIDE.md`
  Practical guide for swapping videos, datasets, and run scales.
- `docs/setup/`
  Environment and remote-machine setup notes.

## What Was Moved To `arxiv/`

Historical Markdown and handoff material no longer stays at the root. It is
kept under `arxiv/legacy_notes/` instead.

Current archive buckets:

- `arxiv/legacy_notes/root_docs/`
  Old root-level Markdown such as quest/process notes.
- `arxiv/legacy_notes/claude_notes/`
  Archived `.claude` note files that are not part of the main project entry.
- `arxiv/legacy_notes/DeepScientist_export/`
- `arxiv/legacy_notes/handoff_resnet18_teacher/`
- `arxiv/legacy_notes/tokenizer_vid/`

## Root Markdown Policy

The root should stay minimal:

- keep `README.md` as the main GitHub entry
- keep user-facing docs under `docs/`
- move historical Markdown into `arxiv/legacy_notes/`

That means the old quest/process Markdown files such as `brief.md`, `plan.md`,
`status.md`, `summary.md`, `PLAN.md`, `SUMMARY.md`, `CHECKLIST.md`, and
`CLAUDE.md` should not remain loose at the repo root.

## Where To Start Reading

1. `README.md`
2. `docs/machine_codec_pipeline.md`
3. `docs/LONG_VIDEO_CUSTOM_DATA_GUIDE.md`
4. `outputs/examples/`
5. `arxiv/legacy_notes/` only when historical context is needed
