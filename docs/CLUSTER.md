# Running on the shared GPU server

## Assumptions baked into the scripts

The experiment, baseline and ops scripts were written for one specific shared host and still
hard-code its paths. To run elsewhere, replace these (a global search is enough):

| Path / value | Meaning |
|---|---|
| `/home/xinyizheng/vid_tokenizer` | repo checkout on the server (`cd` target of every job) |
| `/mnt/nas/xinyizheng/vidtok_out` (`R=` in scripts) | results root |
| `/mnt/nas/xinyizheng/InternVL2_5-8B`, `.../InternVL3_5-8B` | receiver weights (`INTERNVL_MODEL_PATH`) |
| `/mnt/nas/xinyizheng/.hfcache` | `HF_HOME` (jobs run with `HF_HUB_OFFLINE=1`) |
| `/mnt/nas/xinyizheng/vcm_baselines/` | third-party baseline repos and checkpoints |
| `/mnt/nas/xinyizheng/envs/vidtok_qwen` | second Python env (transformers 4.57) for InternVL3.5 |
| conda env `nvrc` | main env for codec training and InternVL2.5 evaluation |

The units in `scripts/units/` are path-agnostic: they read `OUT_ROOT`, `RESULTS_CSV`, `DATASET*`
and `INTERNVL_MODEL_PATH` from the environment.

## Job queue

```bash
bash scripts/experiments/e11_main_results.sh <adapter.pt> train    # writes queue/pending/040_*.sh ...
bash scripts/start_queue.sh                                        # start the runner once (idempotent)
bash scripts/ops/health.sh                                         # read-only status report
touch STOP_QUEUE                                                   # stop launching new jobs
bash scripts/ops/requeue_failed.sh                                 # retry failed jobs (bounded)
```

- A job is a bash file `queue/pending/<NNN>_<name>.sh`; lexicographic order is priority.
  States move through `pending/ → running/ → done/ | failed/`; logs in `logs/queue/<name>.log`.
- Header lines: `#Q minmb=24000` (free MiB required), `#Q share=2` (jobs per card),
  `#Q cards=0 1` (restrict cards).
- `GPU_ALLOW` limits which cards the runner may use (default `0 1 4 5 6 7`).
- Jobs receive `GPU=<GPU-UUID>`, not an index: a card that drops out of CUDA enumeration shifts all
  numeric indices, UUIDs do not. Everything passes `$GPU` into `CUDA_VISIBLE_DEVICES`.
- Jobs that consume other jobs' outputs wait with
  `while ls queue/pending queue/running | grep -q '^<prefix>'; do sleep 120; done`
  (do not use a multi-glob `ls` under `pipefail`: it passes silently when one glob is empty).
- `scripts/start_queue.sh` was reconstructed for this release from its behaviour on the server
  (pidfile `queue/runner.pid`); verify it against the server copy.

## Older direct launcher

`scripts/run.sh` → `scripts/control.sh` → `scripts/launch/launch_local.sh` runs a matrix of units
round-robin over `GPUS` without the queue. It produced the seed pools
(`scripts/baselines/seed_*_ours_hevc_oracle.sh`) and is still the simplest way to try a few videos.
