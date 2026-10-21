#!/usr/bin/env bash
# EgoSchema VVC baseline (MPEG-VCM anchor) -> gate1_egos/results.csv (interface=vvc), n=100.
# FIX vs the failed campaign_prio vvc_egos: read manifest.jsonl (video_idx), NOT questions.jsonl.
# Light (vvenc encode + 1 VLM eval ~14s/point); interleaves on free cards. Idempotent (skip done).
set -eo pipefail
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
source scripts/units/_gpus.sh
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export DATASET=egoschema DATASET_CONFIG=configs/datasets/egoschema.yaml DATASET_MANIFEST_DIR=outputs/datasets/egoschema
export OUT_ROOT=outputs/gate1_egos RESULTS_CSV=outputs/gate1_egos/results.csv NUM_FRAMES=128 SAMPLING=uniform RES=256
ALLOW="0 1 4 5 6 7"; MAXPAR=2
mapfile -t UU < <(python -c "import json;print('\n'.join(sorted({json.loads(l)['video_idx'] for l in open('outputs/datasets/egoschema/manifest.jsonl')})))" | head -100)
echo "######## EgoSchema VVC: ${#UU[@]} videos x QP{28,32,36,40,46} @ $(date) ########"
declare -A GP
for qp in 28 32 36 40 46; do for u in "${UU[@]}"; do
  grep -q "vvc_qp${qp},mid,vvc,${u}," "$RESULTS_CSV" 2>/dev/null && continue
  while true; do
    for g in "${!GP[@]}"; do kill -0 "${GP[$g]}" 2>/dev/null || unset 'GP[$g]'; done
    if (( ${#GP[@]} < MAXPAR )); then
      for g in $(GPU_ALLOW="$ALLOW" free_gpus 24000); do [[ -n "${GP[$g]:-}" ]] && continue
        ( bash scripts/units/baseline_vvc.sh --uuid "$u" --qp "$qp" --gpu "$g" || echo "[WARN] vvc $u qp$qp" ) & GP[$g]=$!; break 2; done
    fi
    if (( ${#GP[@]} > 0 )); then wait -n || true; else sleep 20; fi
  done
done; done
wait
echo "######## EgoSchema VVC DONE @ $(date) :: $(grep -c ',vvc,' "$RESULTS_CSV") vvc rows ########"
