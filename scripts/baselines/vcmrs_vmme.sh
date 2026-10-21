#!/usr/bin/env bash
# VCM-RS full-pool recon batch worker. Usage: GPU=4 SHARD=0 NSHARD=8 PORT=42010 bash ...
set -eo pipefail
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
export DATASET=vmme_long_motion DATASET_CONFIG=configs/datasets/vmme_long_motion.yaml DATASET_MANIFEST_DIR=outputs/datasets/vmme_long_motion
export OUT_ROOT=outputs/gate1_vmme RESULTS_CSV=outputs/gate1_vmme/results.csv
export NUM_FRAMES=128 SAMPLING=uniform RES=256
export VCMRS_PORT="$PORT"
GPU="${GPU:?}"; SHARD="${SHARD:?}"; NSHARD="${NSHARD:-8}"
mapfile -t UUIDS < <(python -c "import json;us=sorted({json.loads(l)['video_idx'] for l in open('outputs/datasets/vmme_long_motion/questions.jsonl')});print('\n'.join(us[$SHARD::$NSHARD]))")
echo "######## VCM-RS batch shard $SHARD/$NSHARD: ${#UUIDS[@]} videos x 6 QP, gpu $GPU port $PORT ########"
n=0
for u in "${UUIDS[@]}"; do
  for qp in ${QPS:-22 27 32 37 42 52}; do
    grep -q "vcmrs_qp${qp},NA,vcmrs,${u}," "$RESULTS_CSV" 2>/dev/null && continue
    bash scripts/units/baseline_vcmrs.sh --uuid "$u" --qp "$qp" --gpu "$GPU" --recon-only || echo "[WARN] vcmrs $u qp$qp failed"
    n=$((n+1)); [[ $((n % 10)) -eq 0 ]] && echo "  ...shard$SHARD: $n done @ $(date +%T)"
  done
done
echo "VCMRS BATCH SHARD $SHARD: DONE"
