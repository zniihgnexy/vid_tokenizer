#!/usr/bin/env bash
# SMC++ EgoSchema common-100 recon batch (E-C / P2). Mirrors _smcpp_batch.sh, egos + common-100.
# Usage: GPU=3 SHARD=0 NSHARD=1 bash scripts/baselines/smcpp_egoschema.sh
set -eo pipefail
cd /home/xinyizheng/vid_tokenizer
source scripts/units/_common.sh 2>/dev/null || true
export DATASET=egoschema DATASET_CONFIG=configs/datasets/egoschema.yaml DATASET_MANIFEST_DIR=outputs/datasets/egoschema
export OUT_ROOT=outputs/gate1_egos RESULTS_CSV=outputs/gate1_egos/results.csv
export NUM_FRAMES=128 SAMPLING=uniform RES=256
GPU="${GPU:-3}"; SHARD="${SHARD:-0}"; NSHARD="${NSHARD:-1}"
mapfile -t ALL < outputs/gate1_egos/common100_uuids.txt
UUIDS=(); for ((i=SHARD;i<${#ALL[@]};i+=NSHARD)); do UUIDS+=("${ALL[$i]}"); done
echo "######## SMC++ EgoSchema shard $SHARD/$NSHARD: ${#UUIDS[@]} videos x {${CRFS:-51 47 43 39 35}} crf on gpu $GPU @ $(date) ########"
n=0
for u in "${UUIDS[@]}"; do
  for c in ${CRFS:-51 47 43 39 35}; do
    grep -q "smcpp_crf${c},NA,smcpp,${u}," "$RESULTS_CSV" 2>/dev/null && continue
    bash scripts/units/baseline_smcpp.sh --uuid "$u" --crf "$c" --gpu "$GPU" --recon-only || echo "[WARN] smcpp $u crf$c failed @ $(date +%T)"
    n=$((n+1)); [[ $((n % 10)) -eq 0 ]] && echo "  ...shard$SHARD: $n recon done @ $(date +%T)"
  done
done
echo "SMCPP EGOS BATCH SHARD $SHARD: DONE @ $(date)"
