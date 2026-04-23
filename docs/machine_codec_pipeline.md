# Machine-Oriented NVRC Pipeline

This repository already contains the two verified building blocks needed for the
current machine-oriented compression line:

1. `third_party/NVRC/main_nvrc.py`
   This is the end-to-end codec loop: train -> encode -> decode -> re-evaluate.
2. `third_party/NVRC/teacher_utils.py` + `third_party/NVRC/tasks.py` +
   `tools/smoke_teacher_loss.py`
   This is the teacher/tokenizer supervision layer used to preserve
   machine-oriented signals after reconstruction.

The missing piece was an orchestration layer that makes the whole path feel like
one reproducible pipeline instead of a collection of manual commands. The new
launcher is `tools/run_machine_codec_pipeline.py`.

## NVRC Patch Delivery

The project-level CLI and demo live in the outer repository. The NVRC-side
teacher-aware codec changes are shipped as
`patches/nvrc_machine_oriented_pipeline.patch` because the upstream NVRC remote
requires separate push credentials. Apply it before running real teacher-aware
NVRC training:

```bash
cd third_party/NVRC
git am ../../patches/nvrc_machine_oriented_pipeline.patch
```

After applying the patch, the modules referenced below are present in the NVRC
submodule and match the profiles exposed by the outer CLI.

## Module Link Graph

```text
input video x
  -> main_nvrc.py
     -> create_overfit_dataset(...)
     -> create_overfit_task(...)
        -> OverfitTask in tasks.py
           -> pixel loss
           -> teacher-aware auxiliary losses
              -> FrozenTeacherAdapter in teacher_utils.py
                 -> y = teacher(x)
                 -> y_hat = teacher(x_hat)
     -> NVRC codec train / encode / decode
  -> results/all.txt
  -> pipeline_summary.json
```

## Supported Profiles

`tools/run_machine_codec_pipeline.py list-profiles` prints the current registry.

The built-in profiles directly mirror the existing task configs:

- `bootstrap`
- `blueprint`
- `readout`
- `relation`
- `semchange`
- `semchange_delta`
- `semchange_gamma2`
- `shared_semchange_delta`

Each profile maps to:

- one teacher-aware task config under
  `third_party/NVRC/scripts/configs/tasks/overfit/`
- one matching smoke-test argument bundle for
  `tools/smoke_teacher_loss.py`

## Typical Usage

Run the smoke test for one profile:

```bash
conda run -n NVRC python tools/run_machine_codec_pipeline.py smoke \
  --profile bootstrap
```

Run a bounded tiny-local pilot:

```bash
conda run -n NVRC python tools/run_machine_codec_pipeline.py run \
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
  --workers 0
```

Compare historical runs:

```bash
python tools/run_machine_codec_pipeline.py compare \
  /abs/path/to/run_a \
  /abs/path/to/run_b \
  /abs/path/to/run_c
```

The compare command sorts runs by:

1. lower `teacher-mse_avg`
2. higher `psnr_avg`
3. lower `bpp_avg`

## Output Contract

Every successful `run` command writes:

- the original NVRC artifacts under `<output-root>/<exp-name>/`
- the native aggregate metrics file at
  `<output-root>/<exp-name>/results/all.txt`
- a structured wrapper summary at
  `<output-root>/<exp-name>/pipeline_summary.json`

`pipeline_summary.json` records:

- selected profile
- smoke-test summary, when enabled
- resolved experiment directory
- parsed aggregate metrics
- exact NVRC command used by the wrapper

## Why This Structure

This keeps the research logic aligned with the project story:

- compression stays in `third_party/NVRC`
- machine-oriented supervision stays in the teacher-aware task layer
- orchestration, reproducibility, and result bookkeeping live in the outer repo

That separation makes the next steps cleaner:

- connect the previously tested modules through one entrypoint
- rerun bounded pilots consistently
- scale to full-dataset experiments without rewriting commands by hand
