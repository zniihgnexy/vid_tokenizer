# Machine-oriented video coding for frozen VLMs

Code for a per-video implicit neural representation (INR) video codec whose decoded output is
consumed by a **frozen** vision-language model (VLM) instead of a human viewer. The codec
(HiNeRV / NVRC) is trained per video with a rate–distortion loss whose distortion term is measured
in the VLM's own feature space, so the bits are spent on what the downstream model actually uses.

The main configuration evaluated in the paper:

| Component | Setting |
|---|---|
| Receiver | InternVL2.5-8B, frozen (InternVL3.5-8B as a second receiver) |
| Codec | NVRC / HiNeRV, one model per video, 30 epochs |
| Receiver-side adapter | one *universal* adapter per backbone, frozen, not charged to the bitstream |
| Per-video side information | 2 KB FiLM delta on the adapter, **counted in the bitstream** |
| Alignment target | joint layer-12 + layer-24 features of the frozen vision encoder |
| Rate tag in result files | `cap_r1_<rung>_n1224_dfilm` |

Evaluation is multiple-choice video QA (EgoSchema, Video-MME long/motion subset, LongVideoBench)
compared at equal bits per pixel against HEVC, VVC, DCVC-RT, image ICM codecs and compressed
feature caches.

## Repository layout

```text
src/machine_codec_pipeline/   Python package: data, VLM backends, QA evaluation, feature-cache codecs
configs/                      dataset definitions (frames, sampling, QA fields) and VLM specs
third_party/NVRC/             upstream NVRC, pinned submodule (unmodified)
patches/                      our changes to NVRC as one patch (alignment losses, adapter, FiLM delta)
scripts/units/                atomic GPU jobs: train one codec, evaluate one video, one baseline point
scripts/experiments/          one script per paper experiment; writes jobs into the queue
scripts/queue_runner.py       GPU job queue for a shared multi-GPU server
scripts/ops/                  read-only health/status helpers for the cluster
tools/                        harvest, statistics and paper-table generation (CPU only)
tests/                        unit tests (pytest)
docs/                         architecture, reproduction guide, cluster notes
```

Run artifacts (`outputs/`, `logs/`, `queue/`), datasets and model weights are not tracked.

## Setup

```bash
git clone --recurse-submodules <this repo> && cd vid_tokenizer
bash scripts/setup_nvrc.sh              # init the NVRC submodule and apply patches/
conda create -n nvrc python=3.13 && conda activate nvrc   # >=3.10 works; tests run on 3.13
pip install torch torchvision           # match your CUDA version
pip install -e ".[nvrc,dev]"
# upstream codec dependencies: see third_party/NVRC/install_env.sh
cp .env.example .env                    # only needed for the optional OpenAI QA path
pytest                                  # 40 tests, CPU only
```

External tools used by baselines: `ffmpeg` with libx265 (HEVC), vvenc/vvdec (VVC, built under
`third_party/baselines/`), and the DCVC-RT / CompressAI / UG-ICM checkpoints. See
[docs/CLUSTER.md](docs/CLUSTER.md).

## Where to start

| You want to | Read |
|---|---|
| Understand how the pieces fit together | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Re-run an experiment or regenerate a paper table | [docs/REPRODUCE.md](docs/REPRODUCE.md) |
| Run jobs on the shared GPU server | [docs/CLUSTER.md](docs/CLUSTER.md) |
| Know what each script / tool does | [scripts/README.md](scripts/README.md), [tools/README.md](tools/README.md) |
| See what we changed inside NVRC | [patches/README.md](patches/README.md) |

## Minimal example: one video, end to end

```bash
export PYTHONPATH=src DATASET=egoschema OUT_ROOT=outputs/demo RESULTS_CSV=outputs/demo/results.csv
export INTERNVL_MODEL_PATH=/path/to/InternVL2_5-8B NVRC_FROZEN_ADAPTER=/path/to/universal_adapter.pt
export NVRC_ADAPTER_DELTA=film RATE_SUFFIX=_dfilm
python tools/egoschema_prep.py --n 5                      # build a 5-video QA manifest
U=<video_idx from outputs/datasets/egoschema/manifest.jsonl>
bash scripts/units/train_codec.sh     --uuid $U --rate cap --capacity r1 --teacher-layer 1224 --gpu 0
bash scripts/units/eval_downstream.sh --uuid $U --rate cap --capacity r1 --loss-variant n1224 --gpu 0
bash scripts/units/eval_oracle.sh     --uuid $U --gpu 0   # uncompressed-frames reference
bash scripts/units/baseline_pixel.sh  --uuid $U --crf 33 --gpu 0
cat outputs/demo/results.csv
```
