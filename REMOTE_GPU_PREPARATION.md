# Remote GPU Preparation

This note captures what needs to be ready before moving the project onto an SSH-only GPU machine.
It is based on the current repo state as of 2026-04-08.

## 1. Current repository split

- Main code repo: `/Users/wf24018/home/vid_tokenizer`
- Main repo remote: `https://github.com/zniihgnexy/vid_tokenizer.git`
- NVRC submodule path: `third_party/NVRC`
- NVRC submodule remote: `https://github.com/hmkx/NVRC.git`
- DeepScientist quest history is separate from the code repo and currently lives under `/Users/wf24018/DeepScientist/quests/001`

## 2. What should be preserved in GitHub

Recommended to keep in the main `vid_tokenizer` repo:

- `CLAUDE.md`
- `CLAUDE_readme.md`
- `CONDA_SETUP.md`
- `DeepScientist_export/`
- `tools/download_uvg_sources.sh`
- `tools/export_deepscientist_snapshot.sh`
- `tools/prepare_uvg_dataset.sh`
- `tools/smoke_teacher_loss.py`
- `.gitignore`
- `REMOTE_GPU_PREPARATION.md`

Recommended to preserve in an NVRC fork or other user-controlled GitHub remote before the move:

- `main_utils.py`
- `tasks.py`
- `utils.py`
- `teacher_utils.py`
- `scripts/configs/data/video/png/tiny_local.yaml`
- `scripts/configs/nvrc/compress_models/nvrc_tiny_s1.yaml`
- `scripts/configs/nvrc/models/teacher_tiny_32.yaml`
- `scripts/configs/nvrc/overfit/tiny-1e.yaml`
- `scripts/configs/tasks/overfit/l1_teacher-bootstrap.yaml`

Do not push these local-only paths to GitHub:

- `Datasets/`
- `Outputs/`
- `DeepScientist/`
- `.clawy/`
- `third_party/NVRC/tmp/`
- runtime caches, sqlite files, terminal logs, and transient experiment scratch state

## 3. Why the NVRC submodule needs special handling

`third_party/NVRC` is a Git submodule, not an ordinary folder in the parent repo.
That means the parent repo alone cannot preserve local NVRC code edits.

Before the remote move, the clean preservation path is:

1. Commit the local NVRC changes inside `third_party/NVRC`.
2. Push those commits to a reachable remote you control, ideally a fork of `hmkx/NVRC`.
3. Update the parent repo to point to that new submodule commit.
4. Commit the parent repo change only after the submodule commit exists remotely.

If step 3 is skipped, a fresh clone on the GPU machine will pull the old upstream NVRC state and the current local teacher-consistency changes will be missing.

## 4. Main recommended sequence before moving machines

1. Review the current main-repo changes and decide the GitHub-ready parent-repo commit.
2. Refresh the tracked DeepScientist export with `bash tools/export_deepscientist_snapshot.sh`.
3. Preserve the NVRC local changes in a user-controlled remote and update the submodule pointer.
4. Push only after explicit user approval.
5. Clone the main repo recursively on the GPU machine.
6. Rebuild the environment there.
7. Restore or download the dataset there.
8. Read the exported quest state under `DeepScientist_export/` before continuing the research line on the GPU machine.

## 5. Clone and bootstrap on the GPU machine

Use a recursive clone so the NVRC submodule is present:

```bash
git clone --recursive https://github.com/zniihgnexy/vid_tokenizer.git
cd vid_tokenizer
git submodule update --init --recursive
```

If the NVRC preservation step later changes the submodule remote, run:

```bash
git submodule sync --recursive
git submodule update --init --recursive
```

## 5A. Direct download checklist

These are the external downloads that the remote machine needs in order to start cleanly:

1. Download the main code repo from GitHub.
2. Download the NVRC submodule through the recursive clone or submodule update.
3. Download Python packages and Conda packages for the `NVRC` environment.
4. Download the UVG source videos or sync an already-prepared UVG dataset from the current machine.

## 6. Environment preparation

Conda or Anaconda remains the recommended default.
Start from `CONDA_SETUP.md`, but do not blindly reuse the Apple-Silicon PyTorch line on the GPU machine.

Recommended flow:

1. Install Conda on the remote machine.
2. Create the `NVRC` environment.
3. Install non-PyTorch dependencies from `CONDA_SETUP.md`.
4. Install the CUDA-enabled `torch`, `torchvision`, and `torchaudio` builds that match the remote machine's driver and CUDA stack.
5. Validate the repo entrypoint with a bounded smoke command before launching a real run.

Base skeleton:

```bash
conda create -n NVRC python=3.13.2 -y
conda activate NVRC
# Replace the torch install line below with the correct CUDA-enabled build for the remote GPU machine.
pip install torch torchvision torchaudio
pip install compressai==1.2.6 accelerate==1.3.0 pytorch-msssim==1.0.0 timm==0.9.16
conda install -c conda-forge ffmpeg -y
```

On the current local Apple-Silicon machine, the working bootstrap used:

```bash
conda create -n NVRC python=3.13.2 -y
conda run -n NVRC pip install torch==2.6.0 torchvision torchaudio
conda run -n NVRC pip install compressai==1.2.6 accelerate==1.3.0 pytorch-msssim==1.0.0 timm==0.9.16
conda install -n NVRC -c conda-forge ffmpeg -y
```

For the GPU machine, keep the same non-PyTorch dependency list but swap the `torch` line to the CUDA-enabled build that matches the remote machine.

Smoke-test the repo entrypoint before launching a real run:

```bash
conda run -n NVRC python third_party/NVRC/main_nvrc.py --help
```

## 7. Dataset preparation

The dataset is not in GitHub.
You have two clean options on the GPU machine.

Option A: sync the prepared dataset over SSH from the current machine.

Option B: download and prepare it again from the repo helpers:

```bash
mkdir -p Datasets
bash tools/download_uvg_sources.sh --prepare
conda run -n NVRC bash tools/prepare_uvg_dataset.sh --source-root /path/to/uvg_yuv_files
```

If you want a smaller first download before pulling the full dataset, start with one video:

```bash
bash tools/download_uvg_sources.sh --videos ShakeNDry --prepare
```

If you only want to inspect what is missing before downloading, use the probe mode:

```bash
bash tools/download_uvg_sources.sh --probe-only
bash tools/prepare_uvg_dataset.sh --probe-only
```

The current local prepared path is:

- `/Users/wf24018/home/vid_tokenizer/Datasets/UVG/1920x1080`

The current compatibility path expected by the vendored PNG config is:

- `~/Datasets/PNG/UVG/1920x1080`

If the dataset is already prepared on the current machine and you want the fastest remote bootstrap, copy it over SSH instead of redownloading it:

```bash
rsync -avP /Users/wf24018/home/vid_tokenizer/Datasets/UVG/1920x1080/ user@remote-host:/path/to/vid_tokenizer/Datasets/UVG/1920x1080/
```

## 8. DeepScientist history and run-state handoff

If the goal is only to continue code development, the GitHub clone plus the preserved NVRC submodule state is enough.

If the goal is to continue the research quest with all durable history, also sync the quest root:

- `/Users/wf24018/DeepScientist/quests/001`

At minimum, keep these durable areas:

- `brief.md`
- `status.md`
- `SUMMARY.md`
- `plan.md`
- `artifacts/`
- `baselines/`
- `experiments/`
- `literature/`
- `memory/`

Do not assume a live local process can be resumed remotely.
Treat the current running local experiment as history to be recorded or relaunched, not as a process that can be transplanted across machines.

If exact quest history is needed on the remote machine, sync it over SSH separately from the GitHub clone, for example:

```bash
rsync -avP /Users/wf24018/DeepScientist/quests/001/ user@remote-host:/path/to/DeepScientist/quests/001/
```

## 9. Current open follow-up tasks

1. Review the parent repo changes that are candidates for GitHub.
2. Decide the preservation route for the NVRC submodule changes.
3. Push only after the user reviews and explicitly approves.
4. Lock the exact CUDA-enabled PyTorch install command once the target GPU specs are known.
5. Decide whether the current no-teacher comparator should be relaunched from scratch on the GPU machine after the environment is ready.
