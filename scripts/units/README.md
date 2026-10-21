# scripts/units/ + scripts/launch/ — the executable-unit model

Every experiment is decomposed into **atomic units**: one unit = one self-contained
GPU job that runs to completion, writes a self-describing output dir + one CSV row,
and **skips if its output already exists**. Units are independent, so any subset can
run on any GPU / any server in parallel. (Run everything in the `nvrc` conda env.)

## The one file you edit

`scripts/control.sh` — declares the campaign: dataset, `BACKBONES`, `RATES`, `LAYERS`,
`INTERFACES`, `N_VIDEOS`, `GPUS`, `EPOCHS`, `PIXEL_CRF`. Nothing else needs editing for
a normal run. Manual data choices live in `configs/datasets/*.yaml`.

## Units (`scripts/units/`)

| Unit | Cost | What it does | CSV `interface` |
|---|---|---|---|
| `train_codec.sh`     | LIGHT (no LLM) | train one per-video codec → `codec_tokens.pt` | (produces tokens) |
| `eval_downstream.sh` | HEAVY (LLM)    | codec tokens → frozen VLM MC answer vs EgoSchema GT | `ours` |
| `eval_oracle.sh`     | HEAVY (LLM)    | lossless frames → VLM MC answer (accuracy ceiling) | `oracle` |
| `baseline_pixel.sh`  | HEAVY (LLM)    | HEVC-encode→decode→VLM MC answer + real bpp | `pixel` |

`_common.sh` holds shared helpers (`ds`, `qa_field`, `ensure_frames`, `bpp_from_run`,
`csv_append`). Results accumulate in `$OUT_ROOT/results.csv`
(`dataset,backbone,rate,layer,interface,uuid,bpp,correct,parsed_letter,expected_letter,secs,note`).

## Launchers (`scripts/launch/`)

- `launch_manifest.sh` → prints a **flat job manifest** (one independent command per
  line, with a `--gpu __GPU__` placeholder). This is the multi-GPU / multi-server primitive.
- `launch_local.sh` → runs the manifest round-robin over `GPUS`, one job per GPU at a time.

```bash
# Stage 0 — calibration on local GPU(s): real EgoSchema accuracy + per-unit cost
python tools/egoschema_prep.py --n 5                 # build the GT manifest
INTERFACES="ours oracle pixel" RATES="mid" N_VIDEOS=2 GPUS="0" \
  bash scripts/launch/launch_local.sh
# -> outputs/campaign/results.csv  +  per-unit secs in unit_cost.json

# multi-server: split the manifest and run a slice per box
bash scripts/launch/launch_manifest.sh > jobs.txt
split -n l/4 jobs.txt part_          # 4 shards; copy each to a server, then:
GPUS="0 1 2 3 4 5 6 7" bash scripts/launch/launch_local.sh   # (reads control.sh matrix)
```

## Scaling notes

- **More videos:** unzip `videos_chunked_*.zip` from `benchmarks/egoschema` into the
  dataset `videos_dir`, raise `n_videos`, rerun `egoschema_prep.py`.
- **More backbones (Stage 3):** needs the generalized adapter shim + `configs/vlm/*.yaml`;
  `train_codec.sh` currently no-ops for non-`internvl` backbones on purpose.
- **Frame sampling:** Stage 0 takes the first N frames (fine for cost). Switch to uniform
  sampling across the clip before the real pilot (EgoSchema clips are ~3 min).
