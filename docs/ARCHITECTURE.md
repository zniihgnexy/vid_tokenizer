# Architecture

## Data flow

```text
 video (mp4)
   │  tools/*_prep.py            -> outputs/datasets/<ds>/manifest.jsonl  (+ per-video qa.json)
   ▼
 sampled frames (128 x 256px, uniform)          scripts/units/_common.sh: ensure_frames
   │
   ├── ours ──────────────────────────────────────────────────────────────────────────┐
   │   scripts/units/train_codec.sh                                                   │
   │     tools/run_machine_codec_pipeline.py run-chunked  -> third_party/NVRC (patched)
   │     loss = rate + λ · ‖adapter(decoded) − frozen-ViT(original)‖ at layers 12 and 24
   │     universal adapter frozen; 2 KB FiLM delta trained per video and entropy-coded
   │   -> codec bitstream + codec_tokens.pt                                            │
   │   scripts/units/eval_downstream.sh                                               │
   │     codec tokens -> frozen projector + LLM -> answer letter                      │
   │                                                                                  │
   ├── baselines: baseline_pixel (HEVC) / _vvc / _dcvc / _learned / _ugicm / _vcmrs / _smcpp
   │     encode -> decode -> frozen VLM (standard pixel path) -> answer letter, real bpp
   │                                                                                  │
   ├── feature cache: src/machine_codec_pipeline/featcache + tools/featcache_*.py      │
   │     frozen ViT tokens -> PCA/PQ/AE + quantisation + entropy coding -> LLM         │
   │                                                                                  │
   └── oracle: eval_oracle.sh  (uncompressed frames, accuracy ceiling)                │
                                                                                      ▼
 one CSV row per (video, interface, rate): dataset,backbone,rate,layer,interface,uuid,bpp,correct,...
   │
   ▼
 tools/harvest_stratified.py   re-evaluate every finished codec on ALL questions of its video,
                               4 phases (QA_SAMPLE_OFFSET 0..3) -> stratified_*_off{0..3}.csv
   ▼
 tools/paper_tables.py         4-phase mean, video-cluster bootstrap CIs, paired deltas, TOST,
                               rate multipliers -> T1..T7 tables, F1 RD curves, F2 forest plots
```

## Layers of the code base

| Layer | Location | Responsibility | Depends on |
|---|---|---|---|
| Codec core | `third_party/NVRC` + `patches/` | INR model, entropy coding, training loop, feature-space losses, adapter + FiLM delta | PyTorch |
| Library | `src/machine_codec_pipeline/` | dataset IO, NVRC launch profiles, VLM backends, QA evaluation, feature-cache codecs | NVRC (via subprocess) |
| Units | `scripts/units/*.sh` | one idempotent GPU job each; append one CSV row | library, tools |
| Experiments | `scripts/experiments/*.sh` | expand an experiment into unit jobs and drop them into `queue/pending/` | units |
| Scheduling | `scripts/queue_runner.py`, `scripts/start_queue.sh` | launch queued jobs on free GPUs of a shared server | `nvidia-smi` |
| Analysis | `tools/*.py` | harvests, statistics, tables, figures (no GPU except harvests) | result CSVs |

## Package `src/machine_codec_pipeline`

| Module | Purpose |
|---|---|
| `cli.py`, `commands.py`, `__main__.py` | `machine-codec` CLI: prepare frames, split chunks, launch NVRC runs (`run`, `run-chunked`), QA eval |
| `profiles.py` | named NVRC launch profiles -> NVRC task configs (rate rungs, alignment depth, capacity) |
| `paths.py`, `io.py`, `results.py` | repo paths, frame IO, run-summary parsing |
| `data/video_data.py` | frame extraction and sampling |
| `vlm/` | backends: InternVL 2.5/3.5 (`internvl_backend.py` = token-injection eval used by the units), InstructBLIP, Qwen2.5-VL, LLaVA-Video; token-pruning baselines (FastV, ToMe, VisionZip) |
| `evaluation/video_qa.py` | multiple-choice prompt, answer parsing, grading |
| `featcache/` | feature-cache baselines: `extract` (ViT tokens), `pca`, `pq`, `quant`, `entropy`, `ae` (learned AE), `codec` (bitstream + bpp), `fit` (shared codebook) |
| `experiment_config.py` | YAML bundle loader with `resolved_config.yaml` snapshotting |

## Key conventions

- **Rate tag.** `train_codec.sh` and `eval_downstream.sh` build the same run-directory tag from
  `--capacity`, `--loss-variant`, `--seed` and `$RATE_SUFFIX`, e.g. `cap_r1_lamb025_n1224_dfilm`.
  Harvests and `tools/paper_tables.py` select cells by this tag.
- **Run directory.** `$OUT_ROOT/<dataset>/<backbone>/<layer>/<interface>/<rate_tag>/<uuid>/`.
- **Idempotency.** Training skips a video whose `codec_tokens.pt` exists; evaluation appends a row.
  Any job can be re-queued safely.
- **Bits.** Ours bpp = codec stream + FiLM delta. The universal adapter and feature-cache codebooks
  are shared receiver-side state and are not charged on either side.
- **Environment switches.** The patched NVRC reads `NVRC_FROZEN_ADAPTER`, `NVRC_ADAPTER_DELTA` (`film`)
  and `NVRC_ADAPTER_LR`. `train_codec.sh` reads `NVRC_INIT_CODEC` (warm start from a donor run) and
  `RATE_SUFFIX`. `INTERNVL_MODEL_PATH` selects the receiver weights.
