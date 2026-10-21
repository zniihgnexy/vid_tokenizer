#!/usr/bin/env bash
# VCM-RS EgoSchema common-100 recon batch (E-C / P2). Mirrors _vcmrs_batch.sh but
# on EgoSchema + restricted to the common-100 pool (outputs/gate1_egos/common100_uuids.txt).
# Usage: GPU=4 SHARD=0 NSHARD=2 PORT=42010 bash scripts/baselines/vcmrs_egoschema.sh
set -eo pipefail
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
export DATASET=egoschema DATASET_CONFIG=configs/datasets/egoschema.yaml DATASET_MANIFEST_DIR=outputs/datasets/egoschema
export OUT_ROOT=outputs/gate1_egos RESULTS_CSV=outputs/gate1_egos/results.csv
export NUM_FRAMES=128 SAMPLING=uniform RES=256
export VCMRS_PORT="${PORT:-42010}"
GPU="${GPU:?}"; SHARD="${SHARD:?}"; NSHARD="${NSHARD:-2}"
mapfile -t ALL < outputs/gate1_egos/common100_uuids.txt
UUIDS=(); for ((i=SHARD;i<${#ALL[@]};i+=NSHARD)); do UUIDS+=("${ALL[$i]}"); done
echo "######## VCM-RS EgoSchema shard $SHARD/$NSHARD: ${#UUIDS[@]} videos x {${QPS:-22 32 42 52}} QP, gpu $GPU port $VCMRS_PORT @ $(date) ########"
n=0
for u in "${UUIDS[@]}"; do
  for qp in ${QPS:-22 32 42 52}; do
    grep -q "vcmrs_qp${qp},NA,vcmrs,${u}," "$RESULTS_CSV" 2>/dev/null && continue
    bash scripts/units/baseline_vcmrs.sh --uuid "$u" --qp "$qp" --gpu "$GPU" --recon-only || echo "[WARN] vcmrs $u qp$qp failed @ $(date +%T)"
    n=$((n+1)); [[ $((n % 5)) -eq 0 ]] && echo "  ...shard$SHARD: $n recon done @ $(date +%T)"
  done
done
echo "VCMRS EGOS BATCH SHARD $SHARD: DONE @ $(date)"
