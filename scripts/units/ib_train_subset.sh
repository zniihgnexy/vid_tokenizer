#!/usr/bin/env bash
# EXP-027 P1-C: train `ours` per-video codecs against the InstructBLIP teacher on a
# subset of motion-regime videos, round-robin across GPUs. Bypasses train_codec.sh's
# internvl-only guard by calling the pipeline directly with --no-smoke-first (the
# preflight smoke tests the deprecated internvit feature-loss path; real training uses
# the teacher-agnostic hidden-consistency path with teacher_loss_weight=0).
#
#   bash scripts/units/ib_train_subset.sh <N_VIDEOS> "<GPU LIST>" [EPOCHS]
set -uo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$REPO_ROOT"

N="${1:-30}"; GPUS="${2:-4 5 6 7}"; EPOCHS="${3:-60}"
OUT_ROOT=outputs/gate1_vmme; DATASET=vmme_long_motion
MANIFEST=outputs/datasets/$DATASET/questions.jsonl
MODELCFG=scripts/configs/nvrc/models/teacher_cap_r1.yaml
LOGDIR=/tmp/claude-1019/-home-xinyizheng-vid-tokenizer/58f9bf9b-7718-45ce-a8f0-1ccc3520baf4/scratchpad/ib_train
mkdir -p "$LOGDIR"

# first N motion-regime uuids (sorted, deterministic)
mapfile -t UUIDS < <(python - "$MANIFEST" "$N" <<'PY'
import json,sys
MOTION={'Sports Competition','Artistic Performance','Film & Television'}
seen={}
for l in open(sys.argv[1]):
    d=json.loads(l)
    if d.get('domain') in MOTION: seen[d['video_idx']]=1
for u in sorted(seen)[:int(sys.argv[2])]: print(u)
PY
)
echo "[ib_train] ${#UUIDS[@]} videos, GPUs=[$GPUS], epochs=$EPOCHS"
read -r -a GPUARR <<< "$GPUS"; NG=${#GPUARR[@]}

pids=()
i=0
for UUID in "${UUIDS[@]}"; do
  GPU=${GPUARR[$((i % NG))]}
  CIDX="$OUT_ROOT/_videos/$DATASET/${UUID}_256_uniform/chunks/eg_${UUID}_256_uniform_chunk_chunk_index.json"
  RUNDIR="$OUT_ROOT/$DATASET/instructblip/mid/ours/cap_r1/$UUID"
  if [[ -n "$(find "$RUNDIR" -name codec_tokens.pt 2>/dev/null | head -1)" ]]; then
    echo "[skip] $UUID already trained"; i=$((i+1)); continue
  fi
  if [[ ! -f "$CIDX" ]]; then echo "[warn] $UUID no chunk index, skip"; i=$((i+1)); continue; fi
  mkdir -p "$RUNDIR"
  echo "[launch] $UUID on GPU $GPU"
  CUDA_VISIBLE_DEVICES="$GPU" nohup python tools/run_machine_codec_pipeline.py run-chunked \
    --profile pathway_b_mid_instructblip --chunk-index "$CIDX" --no-smoke-first \
    --model-config "$MODELCFG" \
    --exp-name-prefix pbmid_ib_ours_cap_r1 --output-root "$RUNDIR" --limit-chunks 1 \
    --epochs "$EPOCHS" --warmup-epochs 0 --eval-epochs "$EPOCHS" \
    --rate-steps 1 --workers 0 --eval-enable-log > "$LOGDIR/$UUID.log" 2>&1 &
  pids+=($!)
  i=$((i+1))
  # throttle: keep at most NG jobs in flight (one per GPU)
  while [[ $(jobs -rp | wc -l) -ge $NG ]]; do sleep 10; done
done
echo "[ib_train] all dispatched; waiting on ${#pids[@]} jobs..."
wait
echo "[ib_train] DONE. trained dirs:"
find "$OUT_ROOT/$DATASET/instructblip/mid/ours/cap_r1" -name codec_tokens.pt 2>/dev/null | wc -l
