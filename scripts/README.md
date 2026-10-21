# scripts/

| Folder / file | Role |
|---|---|
| `units/` | **Atomic GPU jobs.** One video × one setting per call, idempotent, appends one CSV row. See [units/README.md](units/README.md). |
| `experiments/` | **One script per paper experiment.** Expands the experiment into unit jobs and writes them to `queue/pending/`. |
| `baselines/` | Producers for the comparison codecs (reconstructions + bpp) and the seed pools. |
| `queue_runner.py`, `start_queue.sh` | GPU job queue for a shared server ([docs/CLUSTER.md](../docs/CLUSTER.md)). |
| `run.sh`, `control.sh`, `launch/` | Older direct launcher: runs a matrix of units round-robin over GPUs without the queue. |
| `ops/` | Read-only cluster helpers (health report, status bundle, failed-job requeue, weight download). |
| `setup_nvrc.sh` | Initialise the NVRC submodule and apply `patches/`. |

## experiments/

| Script | Experiment |
|---|---|
| `adapter_universal_chain.sh` | fit the universal receiver-side adapter for InternVL2.5 (32 donors) |
| `adapter_universal_chain_internvl35.sh` | the same for InternVL3.5 (E-10) |
| `adapter_ego_chain.sh` | diagnostic: an EgoSchema-only adapter |
| `e11_main_results.sh` | **E-11 main results** (`train`, `harvest`, `egorung`) |
| `e01_e02_delta_warmstart.sh` | E-01 per-video adapter delta, E-02 warm start |
| `e03_pool_expansion.sh` | E-03 LongVideoBench pool |
| `e04_featcache_baselines.sh` | E-04 feature-cache baselines (`fit`, `grid0`, `grid1`, `pareto`, `ae`) |
| `c1_c2_alignment_depth_train.sh`, `e05_alignment_depth_harvest.sh` | E-05 alignment-depth ablation |
| `e10_internvl35.sh` | E-10 second receiver |
| `e12_e13_e14_controls.sh` | E-12 2×2 ablation, E-13 mechanism controls, E-14 timing |
| `b1_b2_controls_pervideo.sh` | B1/B2 controls on per-video-adapter caches |
| `d0_internvl35_screen.sh` | D0 InternVL3.5 screening |

Experiment IDs match [docs/REPRODUCE.md](../docs/REPRODUCE.md), which maps each one to its result
files and paper table.

## baselines/

| Script | Codec |
|---|---|
| `seed_vmme_ours_hevc_oracle.sh`, `seed_egoschema_ours_hevc_oracle.sh` | first pools: ours (per-video adapter), HEVC ladder, uncompressed oracle |
| `vvc_vmme.sh`, `vvc_egoschema.sh` | VVC (vvenc/vvdec), the MPEG-VCM anchor |
| `dcvc_vmme_recon.sh`, `dcvc_egoschema.sh` | DCVC-RT learned video codec (the EgoSchema script also runs the memory-ceiling sweep) |
| `lvb_baselines.sh` | rate-matched baselines on LongVideoBench |
| `cheng_egoschema.sh` | cheng2020-anchor (CompressAI), per-frame intra |
| `ugicm_vmme.sh`, `ugicm_egoschema.sh` | UG-ICM image coding for machines |
| `vcmrs_vmme.sh`, `vcmrs_egoschema.sh` | VCM-RS reference software |
| `smcpp_vmme.sh`, `smcpp_egoschema.sh` | SMC++ semantic video compression |

Reconstruction-only scripts write frames + bpp; `tools/harvest_stratified.py` then evaluates them on
the same questions as ours.
