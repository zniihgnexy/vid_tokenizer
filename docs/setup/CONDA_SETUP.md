# Conda Setup

## Recommended Workflow

- Use Anaconda or conda as the default environment manager for this repo.
- Keep local edits under `/Users/wf24018/home/vid_tokenizer`.
- Do not push to GitHub until the user has reviewed the changes and explicitly approved the push.

## Current Situation

- `conda` is installed on this machine.
- The vendored NVRC baseline already ships a conda-oriented install hint in `third_party/NVRC/install_env.sh`.
- The older project guidance example used `python=3.10`, but the vendored NVRC install hint uses `python=3.13.2`.

Because those version hints do not match yet, this file is a provisional bootstrap note rather than a fully locked `environment.yml`.

## Recommended Bootstrap For Local NVRC Smoke Work

On this Apple Silicon macOS machine, the working local bootstrap path is:

```bash
conda create -n NVRC python=3.13.2
conda run -n NVRC pip install torch==2.6.0 torchvision torchaudio
conda run -n NVRC pip install compressai==1.2.6 accelerate==1.3.0 pytorch-msssim==1.0.0 timm==0.9.16
conda install -n NVRC -c conda-forge ffmpeg -y
```

The vendored NVRC install hint uses a CUDA wheel index, but that did not work on this macOS arm64 machine. Plain PyPI did expose `torch==2.6.0`, and the commands above succeeded locally.

`deepspeed` is still not installed in this environment. For local smoke work on this machine, the following repo-local guards were needed so `main_nvrc.py --help` can run without `deepspeed`:

- `third_party/NVRC/utils.py`
- `third_party/NVRC/main_utils.py`

## Next Validation Step

The bounded smoke that now succeeds locally is:

```bash
conda run -n NVRC python /Users/wf24018/home/vid_tokenizer/third_party/NVRC/main_nvrc.py --help
```

Next step:

1. reconnect the selected teacher-consistency path to a real local smoke beyond `--help`
2. keep the missing UVG dataset path explicit as the blocker to honest baseline comparability

## UVG Dataset Recovery

The broader local search across `/Users/wf24018` and `/Volumes` did not find any existing UVG assets on this machine, so the dataset blocker is now explicit rather than assumed.

The local recovery helpers are:

```bash
bash /Users/wf24018/home/vid_tokenizer/tools/prepare_uvg_dataset.sh --probe-only
bash /Users/wf24018/home/vid_tokenizer/tools/download_uvg_sources.sh --probe-only
```

The second helper downloads and extracts the official 1920x1080 8-bit UVG archives into a repo-local YUV folder. Source checked on 2026-04-04: https://ultravideo.fi/dataset.html

For a bounded one-video bootstrap smoke:

```bash
bash /Users/wf24018/home/vid_tokenizer/tools/download_uvg_sources.sh \
  --videos ShakeNDry \
  --prepare
```

For the full seven-video repo-local bootstrap:

```bash
bash /Users/wf24018/home/vid_tokenizer/tools/download_uvg_sources.sh --prepare
```

If you already have the raw UVG `.yuv` files in one folder, prepare the repo-local dataset surface with:

```bash
conda run -n NVRC bash /Users/wf24018/home/vid_tokenizer/tools/prepare_uvg_dataset.sh \
  --source-root /path/to/uvg_yuv_files
```

By default this keeps the prepared dataset under `/Users/wf24018/home/vid_tokenizer/Datasets/UVG/1920x1080` and also creates the compatibility path expected by the vendored PNG config at `~/Datasets/PNG/UVG/1920x1080`.
