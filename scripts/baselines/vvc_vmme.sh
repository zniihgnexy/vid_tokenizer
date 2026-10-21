#!/usr/bin/env bash
# Track E: VVC anchor (the MPEG-VCM anchor codec) on the 84-video main set. Elastic 0-7.
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
source scripts/units/_gpus.sh
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export DATASET=vmme_long_motion DATASET_CONFIG=configs/datasets/vmme_long_motion.yaml DATASET_MANIFEST_DIR=outputs/datasets/vmme_long_motion
export OUT_ROOT=outputs/gate1_vmme RESULTS_CSV=outputs/gate1_vmme/results.csv NUM_FRAMES=128 SAMPLING=uniform RES=256
MAX_PAR=6
mapfile -t UUIDS < <(python3 -c "import json;[print(json.loads(l)['video_idx']) for l in open('outputs/datasets/vmme_long_motion/manifest.jsonl')]")
declare -A GPU_PID
reap(){ [[ ${#GPU_PID[@]} -gt 0 ]] || return 0; local g; for g in "${!GPU_PID[@]}"; do kill -0 "${GPU_PID[$g]}" 2>/dev/null || unset 'GPU_PID[$g]'; done; }
echo "######## E-track VVC (${#UUIDS[@]} videos x QP{28,32,36,40,46}) @ $(date) ########"
for qp in 28 32 36 40 46; do for u in "${UUIDS[@]}"; do
  grep -q "vvc_qp${qp},mid,vvc,${u}," "$RESULTS_CSV" 2>/dev/null && continue
  while true; do
    reap; placed=0
    if (( ${#GPU_PID[@]} < MAX_PAR )); then
      for g in $(GPU_ALLOW="0 1 2 3 4 5 6 7" free_gpus 22000); do
        [[ -n "${GPU_PID[$g]:-}" ]] && continue
        ( bash scripts/units/baseline_vvc.sh --uuid "$u" --qp "$qp" --gpu "$g" || echo "[VVC] FAIL $u qp$qp" ) &
        GPU_PID[$g]=$!; placed=1; break
      done
    fi
    (( placed )) && break
    if (( ${#GPU_PID[@]} > 0 )); then wait -n || true; else sleep 60; fi
  done
done; done
wait
echo "######## E-track VVC DONE @ $(date) ########"
