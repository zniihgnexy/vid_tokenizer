#!/usr/bin/env bash
# Generate DCVC-RT (SOTA learned video codec) recon frames + bpp for every gate1_vmme
# video across a qp curve, so the stratified harvest can re-eval them per question.
# Recon-only (harvest does the VLM eval). Single card (default 7) so it never contends
# with the EgoSchema scale on 0-5. Idempotent: skips (uuid,qp) already in results.csv.
#   GPU=7 QPS="22 33 40 45 52" bash scripts/baselines/dcvc_vmme_recon.sh
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export DATASET=vmme_long_motion DATASET_CONFIG=configs/datasets/vmme_long_motion.yaml DATASET_MANIFEST_DIR=outputs/datasets/vmme_long_motion
export OUT_ROOT=outputs/gate1_vmme RESULTS_CSV=outputs/gate1_vmme/results.csv
export NUM_FRAMES=128 SAMPLING=uniform RES=256
GPU="${GPU:-7}"; QPS="${QPS:-22 33 40 45 52}"
CSV="$RESULTS_CSV"
mapfile -t UUIDS < <(python -c "import json;print('\n'.join(sorted({json.loads(l)['video_idx'] for l in open('$DATASET_MANIFEST_DIR/questions.jsonl')})))")
echo "######## DCVC recon-gen: ${#UUIDS[@]} videos x [$QPS] on gpu $GPU @ $(date) ########"
n=0; done=0; skip=0
for u in "${UUIDS[@]}"; do
  for qp in $QPS; do
    n=$((n+1))
    if grep -q "dcvc_q${qp},mid,dcvc,${u}," "$CSV" 2>/dev/null; then skip=$((skip+1)); continue; fi
    bash scripts/units/baseline_dcvc.sh --uuid "$u" --qp "$qp" --gpu "$GPU" --recon-only \
      || echo "[WARN] dcvc failed $u qp$qp"
    done=$((done+1))
    [[ $((done % 25)) -eq 0 ]] && echo "  ...progress: $done generated, $skip skipped, $n/$(( ${#UUIDS[@]} * $(echo $QPS|wc -w) )) seen @ $(date)"
  done
done
echo "######## DCVC recon-gen DONE: generated=$done skipped=$skip @ $(date) ########"
