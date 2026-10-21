#!/usr/bin/env bash
# Track C ②: EgoSchema boundary cell (high-entropy egocentric × GIST questions).
# Prediction: no-room — HEVC robust at low bpp, ours ≈ parity/below (task-axis control).
# Small n=20, mainline protocol (r1@128f uniform 256). Elastic, full pool 0-7 (user restored gpu5).
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
echo "######## C-track EgoSchema (n=20, r1+HEVC+oracle) @ $(date) ########"
OUT_ROOT=outputs/gate1_egos RESULTS_CSV=outputs/gate1_egos/results.csv \
DATASETS=egoschema N_VIDEOS=20 BACKBONES=internvl LAYERS=mid \
INTERFACES="ours pixel oracle" CAPACITIES="r1" PIXEL_CRFS="40 45 51" \
SAMPLING=uniform NUM_FRAMES=128 RES=256 EPOCHS=30 \
GPUS="auto" GPU_ALLOW="0 1 2 3 4 5 6 7" GPU_MIN_FREE_MB=22000 GPU_MAX_PAR=8 \
bash scripts/launch/launch_local.sh
echo "######## C-track DONE @ $(date) ########"
