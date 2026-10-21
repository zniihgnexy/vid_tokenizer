#!/usr/bin/env bash
# UG-ICM full-pool recon batch: all manifest videos x q1..q4, recon-only (harvest evals later).
# Usage: GPU=7 SHARD=0 NSHARD=2 bash scripts/baselines/ugicm_vmme.sh
set -eo pipefail
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
export DATASET=vmme_long_motion DATASET_CONFIG=configs/datasets/vmme_long_motion.yaml DATASET_MANIFEST_DIR=outputs/datasets/vmme_long_motion
export OUT_ROOT=outputs/gate1_vmme RESULTS_CSV=outputs/gate1_vmme/results.csv
export NUM_FRAMES=128 SAMPLING=uniform RES=256
GPU="${GPU:-7}"; SHARD="${SHARD:-0}"; NSHARD="${NSHARD:-2}"
mapfile -t UUIDS < <(python -c "import json;us=sorted({json.loads(l)['video_idx'] for l in open('outputs/datasets/vmme_long_motion/questions.jsonl')});print('\n'.join(us[$SHARD::$NSHARD]))")
echo "######## UG-ICM recon batch shard $SHARD/$NSHARD: ${#UUIDS[@]} videos x q1-4 on gpu $GPU ########"
n=0
for u in "${UUIDS[@]}"; do
  for q in 1 2 3 4; do
    grep -q "ugicm_q${q},NA,ugicm,${u}," "$RESULTS_CSV" 2>/dev/null && continue
    bash scripts/units/baseline_ugicm.sh --uuid "$u" --q "$q" --gpu "$GPU" --recon-only || echo "[WARN] ugicm $u q$q failed"
    n=$((n+1)); [[ $((n % 40)) -eq 0 ]] && echo "  ...progress shard$SHARD: $n done @ $(date +%T)"
  done
done
echo "UGICM BATCH SHARD $SHARD: DONE"
