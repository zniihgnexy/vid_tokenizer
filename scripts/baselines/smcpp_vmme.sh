#!/usr/bin/env bash
# SMC++ full-pool recon batch: all manifest videos x crf{51,47,43,39,35}, recon-only.
# Usage: GPU=5 SHARD=0 NSHARD=2 bash scripts/baselines/smcpp_vmme.sh
set -eo pipefail
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
export DATASET=vmme_long_motion DATASET_CONFIG=configs/datasets/vmme_long_motion.yaml DATASET_MANIFEST_DIR=outputs/datasets/vmme_long_motion
export OUT_ROOT=outputs/gate1_vmme RESULTS_CSV=outputs/gate1_vmme/results.csv
export NUM_FRAMES=128 SAMPLING=uniform RES=256
GPU="${GPU:-5}"; SHARD="${SHARD:-0}"; NSHARD="${NSHARD:-2}"
mapfile -t UUIDS < <(python -c "import json;us=sorted({json.loads(l)['video_idx'] for l in open('outputs/datasets/vmme_long_motion/questions.jsonl')});print('\n'.join(us[$SHARD::$NSHARD]))")
echo "######## SMC++ recon batch shard $SHARD/$NSHARD: ${#UUIDS[@]} videos x 5 crf on gpu $GPU ########"
n=0
for u in "${UUIDS[@]}"; do
  for c in 51 47 43 39 35; do
    grep -q "smcpp_crf${c},NA,smcpp,${u}," "$RESULTS_CSV" 2>/dev/null && continue
    bash scripts/units/baseline_smcpp.sh --uuid "$u" --crf "$c" --gpu "$GPU" --recon-only || echo "[WARN] smcpp $u crf$c failed"
    n=$((n+1)); [[ $((n % 25)) -eq 0 ]] && echo "  ...progress shard$SHARD: $n done @ $(date +%T)"
  done
done
echo "SMCPP BATCH SHARD $SHARD: DONE"
