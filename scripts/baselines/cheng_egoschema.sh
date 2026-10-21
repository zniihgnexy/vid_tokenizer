#!/usr/bin/env bash
# cheng2020-anchor (CompressAI, per-frame intra) EgoSchema common-100 recon batch (E-C / P2).
# Usage: GPU=2 SHARD=0 NSHARD=1 bash scripts/baselines/cheng_egoschema.sh
set -eo pipefail
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc   # cheng2020 = CompressAI; needs nvrc's python/numpy (bare base python has a broken numpy)
export DATASET=egoschema DATASET_CONFIG=configs/datasets/egoschema.yaml DATASET_MANIFEST_DIR=outputs/datasets/egoschema
export OUT_ROOT=outputs/gate1_egos RESULTS_CSV=outputs/gate1_egos/results.csv
export NUM_FRAMES=128 SAMPLING=uniform RES=256
GPU="${GPU:-2}"; SHARD="${SHARD:-0}"; NSHARD="${NSHARD:-1}"
mapfile -t ALL < outputs/gate1_egos/common100_uuids.txt
UUIDS=(); for ((i=SHARD;i<${#ALL[@]};i+=NSHARD)); do UUIDS+=("${ALL[$i]}"); done
echo "######## cheng2020 EgoSchema shard $SHARD/$NSHARD: ${#UUIDS[@]} videos x q{${QS:-1 2 3 4}} on gpu $GPU @ $(date) ########"
n=0
for u in "${UUIDS[@]}"; do
  for q in ${QS:-1 2 3 4}; do
    grep -q "learned_q${q},NA,learned,${u}," "$RESULTS_CSV" 2>/dev/null && continue
    bash scripts/units/baseline_learned.sh --uuid "$u" --q "$q" --gpu "$GPU" --recon-only || echo "[WARN] cheng $u q$q failed @ $(date +%T)"
    n=$((n+1)); [[ $((n % 20)) -eq 0 ]] && echo "  ...shard$SHARD: $n recon done @ $(date +%T)"
  done
done
echo "CHENG EGOS BATCH SHARD $SHARD: DONE @ $(date)"
