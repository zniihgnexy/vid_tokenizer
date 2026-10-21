#!/usr/bin/env bash
# UG-ICM EgoSchema common-100 recon batch (E-C / P2). Mirrors _ugicm_batch.sh, egos + common-100.
# Usage: GPU=2 SHARD=0 NSHARD=1 bash scripts/baselines/ugicm_egoschema.sh
set -eo pipefail
cd /home/xinyizheng/vid_tokenizer
source scripts/units/_common.sh 2>/dev/null || true
export DATASET=egoschema DATASET_CONFIG=configs/datasets/egoschema.yaml DATASET_MANIFEST_DIR=outputs/datasets/egoschema
export OUT_ROOT=outputs/gate1_egos RESULTS_CSV=outputs/gate1_egos/results.csv
export NUM_FRAMES=128 SAMPLING=uniform RES=256
GPU="${GPU:-2}"; SHARD="${SHARD:-0}"; NSHARD="${NSHARD:-1}"
mapfile -t ALL < outputs/gate1_egos/common100_uuids.txt
UUIDS=(); for ((i=SHARD;i<${#ALL[@]};i+=NSHARD)); do UUIDS+=("${ALL[$i]}"); done
echo "######## UG-ICM EgoSchema shard $SHARD/$NSHARD: ${#UUIDS[@]} videos x q{${QS:-1 2 3 4}} on gpu $GPU @ $(date) ########"
n=0
for u in "${UUIDS[@]}"; do
  for q in ${QS:-1 2 3 4}; do
    grep -q "ugicm_q${q},NA,ugicm,${u}," "$RESULTS_CSV" 2>/dev/null && continue
    bash scripts/units/baseline_ugicm.sh --uuid "$u" --q "$q" --gpu "$GPU" --recon-only || echo "[WARN] ugicm $u q$q failed @ $(date +%T)"
    n=$((n+1)); [[ $((n % 20)) -eq 0 ]] && echo "  ...shard$SHARD: $n recon done @ $(date +%T)"
  done
done
echo "UGICM EGOS BATCH SHARD $SHARD: DONE @ $(date)"
