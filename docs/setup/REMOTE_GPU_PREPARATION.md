# Remote GPU Preparation

This note is the cleaned-up checklist for moving the current project to a
remote GPU machine without carrying over local clutter.

## What Should Be In Git

Keep these in the main repository:

- `README.md`
- `docs/`
- `src/machine_codec_pipeline/`
- `tests/`
- `tools/`
- `patches/`
- `outputs/examples/`
- `arxiv/legacy_notes/`

Do not treat local run artifacts as source code.

## What Should Stay Local

Do not push these local-only areas:

- `.env`
- `.venv/`
- `outputs/runs/`
- `outputs/video_windows/`
- `Datasets/`
- `DeepScientist/`
- temporary caches, logs, and scratch files

## NVRC Submodule Reminder

`third_party/NVRC` is a Git submodule. If you made local NVRC changes, the
parent repository alone will not preserve them.

Recommended path:

1. commit or preserve the NVRC changes in a reachable remote you control
2. update the parent repo to point at that submodule commit
3. only then clone on the GPU machine

## Clean Clone On The Remote Machine

```bash
git clone --recursive <your-repo-url>
cd vid_tokenizer
```

If the repo is already cloned:

```bash
git submodule update --init --recursive
```

## Environment Bootstrap

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Also make sure `ffmpeg` is available on the remote machine.

## Apply The NVRC Patch

```bash
cd third_party/NVRC
git am ../../patches/nvrc_machine_oriented_pipeline.patch
cd ../..
```

## Restore The OpenAI Key

Create a fresh `.env` on the remote machine:

```bash
cp .env.example .env
```

Then set:

```bash
OPENAI_API_KEY=your_key_here
```

Do not commit the real key.

## Suggested First Validation On The Remote Machine

1. `machine-codec list-profiles`
2. `machine-codec demo --output-root outputs/demo/remote_smoke`
3. `machine-codec prepare-video ...`
4. one bounded `machine-codec run --dry-run`
5. one real run after the dry run looks correct

## Historical Notes

Old process documents and archived Markdown now live under:

```text
arxiv/legacy_notes/
```

Use those for reference only. The main operational surface should be:

1. `README.md`
2. `docs/machine_codec_pipeline.md`
3. `docs/LONG_VIDEO_CUSTOM_DATA_GUIDE.md`
