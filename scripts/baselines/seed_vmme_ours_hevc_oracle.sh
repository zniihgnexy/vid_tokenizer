#!/usr/bin/env bash
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
echo "######## GATE 1 Video-MME (ours 3 caps + HEVC + oracle, n=25, 128f) @ $(date) ########"
OUT_ROOT=outputs/gate1_vmme RESULTS_CSV=outputs/gate1_vmme/results.csv \
DATASETS=vmme_long_motion N_VIDEOS=25 BACKBONES=internvl LAYERS=mid \
INTERFACES="ours pixel oracle" CAPACITIES="r1 g_mlo xs" PIXEL_CRFS="28 33 40 45 51" \
SAMPLING=uniform NUM_FRAMES=128 RES=256 EPOCHS=30 GPUS="4 5 6 7" \
bash scripts/launch/launch_local.sh
echo "######## GATE 1 VMME DONE @ $(date) ########"
