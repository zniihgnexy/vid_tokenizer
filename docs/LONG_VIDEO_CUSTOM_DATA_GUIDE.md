# Long Video And Custom Data Guide

This guide answers three practical follow-up questions:

1. how to move from a tiny bounded example to a longer or full video
2. how to swap in a different raw video or extracted dataset
3. how to keep the same code surface while changing scale

## Recommended Progression

Do not jump from a tiny smoke example straight to a very large end-to-end run.
The more stable path is:

1. bounded window
2. longer bounded window
3. chunked longer video
4. full-video chunked QA comparison

That keeps failures interpretable.

## A. Start From One Raw Video

Use `prepare-video` as the main project entrypoint.

### Small window

```bash
machine-codec prepare-video \
  --video-path /abs/path/to/video.mp4 \
  --output-dir outputs/video_windows/my_video_16f \
  --start-frame 0 \
  --num-frames 16 \
  --width 32 \
  --height 32 \
  --overwrite
```

### Longer window with chunking

```bash
machine-codec prepare-video \
  --video-path /abs/path/to/video.mp4 \
  --output-dir outputs/video_windows/my_video_128f \
  --start-frame 0 \
  --num-frames 128 \
  --width 32 \
  --height 32 \
  --chunk-size 16 \
  --chunk-output-root outputs/video_windows/my_video_128f_chunks \
  --overwrite
```

What you get:

- extracted PNG frames
- `extraction_manifest.json`
- `prepare_video_summary.json`
- a chunk index if `--chunk-size` is provided

## B. Run On A Different Dataset

For a bounded dataset, the two main knobs are:

- `--dataset-dir`
- `--dataset`

Example:

```bash
machine-codec run \
  --profile shared_semchange_delta \
  --exp-name custom_dataset_run \
  --dataset-dir /abs/path/to/png_datasets \
  --dataset custom_dataset_name \
  --video-size 4 32 32 \
  --patch-size 1 32 32 \
  --output-root outputs/runs
```

Use this mode when you already have a directory that looks like:

```text
/abs/path/to/png_datasets/
└── custom_dataset_name/
    ├── 0001.png
    ├── 0002.png
    └── ...
```

## C. Run On A Longer Or Full Video

Once you have a chunk index, switch to `run-chunked`:

```bash
machine-codec run-chunked \
  --profile shared_semchange_delta \
  --chunk-index outputs/video_windows/my_video_128f_chunks/my_video_128f_chunk_index.json \
  --exp-name-prefix my_video_shared_semchange_delta \
  --output-root outputs/runs \
  --epochs 1 \
  --warmup-epochs 0 \
  --eval-epochs 1 \
  --rate-steps 1 \
  --workers 0 \
  --eval-enable-log
```

Important points:

- keep `--eval-enable-log` on if you want downstream QA later
- let the chunk manifest drive shape inference when possible
- change one scale variable at a time before changing everything else

## D. How To Swap The Video Path Cleanly

If you want to try another raw video, you usually only need to change:

- `prepare-video --video-path`
- `prepare-video --output-dir`
- `prepare-video --chunk-output-root`

Everything downstream can stay on the same CLI surface.

Example:

```bash
machine-codec prepare-video \
  --video-path /data/ego4d/clip_002.mp4 \
  --output-dir outputs/video_windows/clip_002_64f \
  --num-frames 64 \
  --chunk-size 16 \
  --chunk-output-root outputs/video_windows/clip_002_64f_chunks \
  --overwrite
```

Then:

```bash
machine-codec run-chunked \
  --profile shared_semchange_delta \
  --chunk-index outputs/video_windows/clip_002_64f_chunks/clip_002_64f_chunk_index.json \
  --exp-name-prefix clip_002_shared_semchange_delta \
  --output-root outputs/runs \
  --eval-enable-log
```

## E. How To Change The LLM Model Later

The OpenAI QA steps expose model selection directly:

```bash
machine-codec video-qa-chunked-report \
  --chunked-summary outputs/runs/your_summary.json \
  --model gpt-4.1 \
  --question "..." \
  --option "A" \
  --option "B" \
  --answer-index 0
```

Current limitation:

- the packaged provider surface only supports OpenAI
- `--provider` is intentionally fixed to `openai`

If you want Gemini or another downstream model, extend:

- `src/machine_codec_pipeline/video_qa.py`
- `src/machine_codec_pipeline/cli.py`

## F. How To Keep Results Organized

Recommended convention:

```text
outputs/
├── video_windows/
│   ├── <video_name>_64f/
│   └── <video_name>_64f_chunks/
├── runs/
│   ├── <exp-name>/
│   ├── <exp-name-prefix>_chunked_summary.json
│   └── <qa-report-dir>/
└── examples/
```

That makes it obvious which files belong to:

- extracted input frames
- codec runs
- downstream QA reports
- tracked example artifacts

## G. Minimal Debug Checklist

If a new video or dataset does not run, check these in order:

1. `ffmpeg` is installed and `prepare-video` succeeded.
2. The output dataset really contains sequential PNGs.
3. The NVRC patch has been applied in `third_party/NVRC`.
4. `run --dry-run` or `run-chunked --dry-run` produces the command you expect.
5. `OPENAI_API_KEY` is available before running the QA report.

## H. Practical Rule

When you scale up, change only one of these at a time:

1. video length
2. chunk size
3. resolution
4. experiment profile
5. downstream model

That keeps comparisons meaningful and makes failures much easier to debug.
