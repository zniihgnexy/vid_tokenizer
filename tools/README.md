# tools/

Stand-alone Python entry points. Run from the repo root with `PYTHONPATH=src`.
Everything except the harvest, reconstruction and feature-cache extraction tools runs on CPU.

## Data preparation

| Tool | Purpose |
|---|---|
| `egoschema_prep.py` | EgoSchema multiple-choice manifest from the subset parquet |
| `vmme_prep.py` | Video-MME long/motion manifest, all questions per video, bucketed detail / temporal / gist |
| `longvideobench_prep.py` | LongVideoBench manifest (long, visual questions) |

## Running and evaluating codecs

| Tool | Purpose |
|---|---|
| `run_machine_codec_pipeline.py` | wrapper around the `machine-codec` CLI; `train_codec.sh` calls its `run-chunked` command |
| `harvest_stratified.py` | re-evaluate finished codecs (+ oracle + HEVC recon) on all questions of each video; 4 phases via `QA_SAMPLE_OFFSET` |
| `dcvc_codec_recon.py`, `learned_codec_recon.py`, `ugicm_codec_recon.py` | baseline reconstructions + measured bpp (DCVC-RT, cheng2020, UG-ICM) |
| `featcache_fit.py`, `featcache_ae_train.py`, `featcache_harvest.py`, `featcache_pareto.py` | E-04 feature-cache baselines: fit codebook / train AE / evaluate / Pareto front + rate multipliers |
| `timing_bench.sh`, `timing_featcache.py` | E-14 encode wall time |
| `oom_boundary_sweep.py` | memory-ceiling sweep used by the DCVC EgoSchema script |

## Statistics and paper outputs

| Tool | Purpose |
|---|---|
| `paper_tables.py` | **all paper tables and figures** (T1–T7, F1, F2) from the 4-phase harvests |
| `cells_lib.py` | shared loaders for result pools (imported by the reporting tools) |
| `phase_summary.py` | quick (interface, rate) → n / accuracy / bpp summary of any harvest glob |
| `noninferiority.py` | paired accuracy difference with a pre-specified margin |
| `e11_report.py`, `ctrl_report.py`, `upilot_verdict.py`, `egos_common100.py`, `table_cells_phasemean.py` | per-experiment reports and decision gates |
| `proxy_vs_error.py` | does the feature-space distortion predict downstream errors? |
