#!/usr/bin/env bash
# Use the reserved cards 6,7 for two unfinished high-value experiments:
#  (1) EgoSchema DCVC-RT baseline (completes hero panel-a 4th codec curve) -> gate1_egos/results.csv
#  (2) OOM feasibility-ceiling sweep (Tab3c deployment advantage) on a CLEAN card, after DCVC frees it.
# campaign_tail runs the heavy tail on 0,1,4,5; this script owns 6,7 -> no cross-dispatch race.
set -eo pipefail
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
source scripts/units/_gpus.sh
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export DATASET=egoschema DATASET_CONFIG=configs/datasets/egoschema.yaml DATASET_MANIFEST_DIR=outputs/datasets/egoschema
export OUT_ROOT=outputs/gate1_egos RESULTS_CSV=outputs/gate1_egos/results.csv NUM_FRAMES=128 SAMPLING=uniform RES=256
ALLOW="6 7"; MAXPAR=2
mapfile -t UU < <(python -c "import json;print('\n'.join(sorted({json.loads(l)['video_idx'] for l in open('outputs/datasets/egoschema/manifest.jsonl')})))" | head -100)
echo "######## EgoSchema DCVC: ${#UU[@]} videos x q{22,33,40,45,52} @ $(date) ########"
declare -A GP
for qp in 22 33 40 45 52; do for u in "${UU[@]}"; do
  grep -q "dcvc_q${qp},mid,dcvc,${u}," "$RESULTS_CSV" 2>/dev/null && continue
  while true; do
    for g in "${!GP[@]}"; do kill -0 "${GP[$g]}" 2>/dev/null || unset 'GP[$g]'; done
    if (( ${#GP[@]} < MAXPAR )); then
      for g in $(GPU_ALLOW="$ALLOW" free_gpus 24000); do [[ -n "${GP[$g]:-}" ]] && continue
        ( bash scripts/units/baseline_dcvc.sh --uuid "$u" --qp "$qp" --gpu "$g" || echo "[WARN] dcvc $u q$qp" ) & GP[$g]=$!; break 2; done
    fi
    if (( ${#GP[@]} > 0 )); then wait -n || true; else sleep 20; fi
  done
done; done
wait
echo "######## EgoSchema DCVC DONE @ $(date) :: $(grep -c ',dcvc,' "$RESULTS_CSV") dcvc rows ########"
# --- (2) OOM sweep on a now-free clean card (7) ---
echo "######## OOM boundary sweep on card 7 @ $(date) ########"
CUDA_VISIBLE_DEVICES=7 PYTHONPATH=src python tools/oom_boundary_sweep.py \
  --frames 8 16 24 32 48 64 96 128 192 256 384 512 768 1024 2>&1 | tail -20
echo "######## DCVC + OOM ALL DONE @ $(date) ########"
