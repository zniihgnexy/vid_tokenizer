# Reproducing the paper

Every experiment is a script in `scripts/experiments/` (or `scripts/baselines/`) that **writes jobs
into `queue/pending/`**; the queue runner executes them on free GPUs (see [CLUSTER.md](CLUSTER.md)).
Result CSVs land under the results root `R` (on our cluster `R=/mnt/nas/xinyizheng/vidtok_out`).
Tables and figures are then produced on CPU by `tools/paper_tables.py`.

## 0. Inputs you need first

| Input | How it is produced | Used by |
|---|---|---|
| `outputs/datasets/egoschema/manifest.jsonl` (+ per-video `qa.json`) | `python tools/egoschema_prep.py` | all EgoSchema jobs |
| `outputs/datasets/vmme_long_motion/{manifest,questions}.jsonl` | `python tools/vmme_prep.py` | all Video-MME jobs |
| `outputs/datasets/longvideobench/manifest.jsonl` | `python tools/longvideobench_prep.py` | E-03 |
| `outputs/gate1_egos/common100_uuids.txt` | the 100 EgoSchema videos every codec finished; the set is defined in `tools/egos_common100.py` | E-10..E-14, baselines, tables |
| `outputs/datasets/vmme_long_motion/{motion115,nonmotion48}_uuids.txt` | Video-MME long videos split by domain: motion = Sports Competition, Artistic Performance, Film & Television | VMME tables |
| `outputs/featcache/donors.txt` | the 32 donor videos of the universal adapter, one `<dataset> <uuid>` per line | E-04 |
| InternVL2.5-8B / InternVL3.5-8B weights | Hugging Face; `scripts/ops/fetch_internvl35.sh` | everything |

> The evaluation-pool ID lists used in the paper are kept on the cluster and are **not yet in git**
> (to be added under `outputs/` exceptions once the server is back).

## 1. Pipeline order

```text
seed pools (per-video adapter, HEVC, oracle)   scripts/baselines/seed_*_ours_hevc_oracle.sh
   └─> universal adapter                       scripts/experiments/adapter_universal_chain.sh
        └─> main results (E-11)                scripts/experiments/e11_main_results.sh  train -> harvest
             ├─> baselines on the same videos  scripts/baselines/{vvc,dcvc,...}_*.sh + harvests
             ├─> feature-cache baselines E-04  scripts/experiments/e04_featcache_baselines.sh
             ├─> controls E-12/13/14           scripts/experiments/e12_e13_e14_controls.sh
             └─> second receiver E-10          adapter_universal_chain_internvl35.sh -> e10_internvl35.sh
   tables/figures                              python tools/paper_tables.py --out <dir>
```

## 2. Experiment → script → results → paper artefact

| ID | What it answers | Script (mode) | Results under `R/` | Paper artefact |
|---|---|---|---|---|
| Adapter | one frozen receiver-side adapter per backbone | `experiments/adapter_universal_chain.sh` | `exp_shared_adapter_u/` | method |
| **E-11** | main RD results, main configuration | `DELTA_MODE=film TLAYER=1224 experiments/e11_main_results.sh <adapter.pt> train`, then `harvest`; extra rung: `RUNG=lamb050 ... egorung` | `u_egos/`, `u_vmme/` (`stratified_u_n1224_dfilm_off{0..3}.csv`) | T1, T7, F1, F2 |
| E-01/E-02 | per-video FiLM/LoRA delta; warm start | `experiments/e01_e02_delta_warmstart.sh e01\|e02` | `exp_delta/`, `exp_warm/` | design choice (FiLM) |
| E-03 | detail-sensitive pool (LongVideoBench) | `experiments/e03_pool_expansion.sh train\|harvest` | `u_lvb/` | T1 (LVB) |
| E-04 | compressed feature-cache baselines (PCA/PQ/AE) | `experiments/e04_featcache_baselines.sh fit\|grid0\|grid1\|pareto\|ae` | `exp_featcache/` | T2, T1 multipliers |
| E-05 / C1-C2 | alignment depth: mid / final / multi-layer | `experiments/c1_c2_alignment_depth_train.sh`, `experiments/e05_alignment_depth_harvest.sh` | `gate1_vmme/stratified_{final,ours}_*` | T4 |
| E-10 | second receiver InternVL3.5-8B | `experiments/adapter_universal_chain_internvl35.sh`, `experiments/e10_internvl35.sh train\|harvest` | `exp_shared_adapter_u35/`, `ivl35_egos/` | T5 |
| E-12 | adapter × alignment 2×2 ablation | `experiments/e12_e13_e14_controls.sh e12` | `u_egos/` (`cap_r1_dfilm`, `cap_r1_n1224`) | T6 (**partial**) |
| E-13 | mechanism controls: shuffle, mismatch, pooling | `experiments/e12_e13_e14_controls.sh e13` | `u_egos/`, `u_vmme/` (`stratified_e13_*`) | T3 |
| E-14 | isolated encode-time benchmark | `experiments/e12_e13_e14_controls.sh e14` (`tools/timing_bench.sh`) | `exp_timing/` | not run |
| B1/B2 | controls on per-video-adapter caches | `experiments/b1_b2_controls_pervideo.sh` | `gate1_*/stratified_ctrl_*` | appendix |
| D0 | InternVL3.5 screening | `experiments/d0_internvl35_screen.sh` | `ivl35_*` | appendix |
| Baselines | HEVC/VVC/DCVC-RT/cheng2020/UG-ICM/VCM-RS/SMC++ | `baselines/*.sh` (recon) + `tools/harvest_stratified.py` | `gate1_egos/`, `gate1_vmme/`, `u_lvb/` | T1, F1 |

## 3. Evaluation protocol (what the tables mean)

- **4-phase harvest.** `tools/harvest_stratified.py` re-evaluates each finished codec on every
  question of its video; `QA_SAMPLE_OFFSET=0..3` rotates the question/frame sample. Cell accuracy is
  the plain mean over all rows of the four phases.
- **Uncertainty.** 95% CIs are video-cluster bootstraps. Method comparisons are **paired** (same
  videos and questions): T7/F2 report ours − nearest-rate baseline with a paired bootstrap CI; T1
  reports the rate multiplier a baseline needs to match ours (log-bpp interpolation on its
  accuracy-monotone front) with a paired bootstrap CI, and a TOST equivalence test at δ = 0.05.
- **Bits.** Ours includes the 2 KB FiLM delta; shared adapter and feature-cache codebooks are free
  on both sides. Only measured `bpp` / `correct` columns from the result CSVs are used.

## 4. Regenerating tables

```bash
python tools/paper_tables.py --out outputs/paper_tables            # all tables + figures
python tools/paper_tables.py --only controls                       # one block: controls|ablation|backbone|depth
python tools/phase_summary.py "$R/u_egos/stratified_u_n1224_dfilm_off*.csv"   # quick look at any pool
```

## 5. Known gaps (frozen 2026-10-21)

- E-12: cell A (`cap_r1_dfilm`) trained on 100/100 videos, cell B (`cap_r1_n1224`) on about 56/100;
  the 4-phase harvest has not run, so T6 has 3 of 6 cells.
- E-14: not run. Resume with `bash scripts/start_queue.sh` on the server (pending jobs are kept).
