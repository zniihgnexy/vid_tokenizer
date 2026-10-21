#!/usr/bin/env bash
# EXP-028 P1-C': train `ours` per-video codecs against the LLaVA-Video (SigLIP)
# teacher on motion-regime videos, round-robin across GPUs. Runs in the CLONED env
# (vidtok_llava: has compressai + llava + the dynamo env-guard). Bypasses the
# internvl-only shell guard via run-chunked --no-smoke-first.
#
#   bash scripts/units/llava_train_subset.sh <N_VIDEOS> "<GPU LIST>" [EPOCHS] [NUM_FRAMES]
set -uo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$REPO_ROOT"

N="${1:-30}"; GPUS="${2:-0 1 4}"; EPOCHS="${3:-30}"; NF="${4:-128}"
PY=/mnt/nas/xinyizheng/envs/vidtok_llava/bin/python
OUT_ROOT=outputs/gate1_vmme; DATASET=vmme_long_motion
MANIFEST=outputs/datasets/$DATASET/questions.jsonl
MODELCFG=scripts/configs/nvrc/models/teacher_cap_r1.yaml
LOGDIR=/tmp/claude-1019/-home-xinyizheng-vid-tokenizer/58f9bf9b-7718-45ce-a8f0-1ccc3520baf4/scratchpad/llava_train
mkdir -p "$LOGDIR"
export HF_HOME=/mnt/nas/xinyizheng/.hfcache PYTHONPATH=src TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1

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
echo "[llava_train] ${#UUIDS[@]} videos, GPUs=[$GPUS], epochs=$EPOCHS, frames=$NF"
read -r -a GPUARR <<< "$GPUS"; NG=${#GPUARR[@]}
i=0
for UUID in "${UUIDS[@]}"; do
  GPU=${GPUARR[$((i % NG))]}
  CIDX="$OUT_ROOT/_videos/$DATASET/${UUID}_256_uniform/chunks/eg_${UUID}_256_uniform_chunk_chunk_index.json"
  RUNDIR="$OUT_ROOT/$DATASET/llava_video/mid/ours/cap_r1/$UUID"
  if [[ -n "$(find "$RUNDIR" -name codec_tokens.pt 2>/dev/null | head -1)" ]]; then
    echo "[skip] $UUID trained"; i=$((i+1)); continue; fi
  if [[ ! -f "$CIDX" ]]; then echo "[warn] $UUID no chunk index"; i=$((i+1)); continue; fi
  mkdir -p "$RUNDIR"
  echo "[launch] $UUID on GPU $GPU"
  CUDA_VISIBLE_DEVICES="$GPU" nohup "$PY" tools/run_machine_codec_pipeline.py run-chunked \
    --profile pathway_b_mid_llavavideo --chunk-index "$CIDX" --no-smoke-first \
    --model-config "$MODELCFG" --exp-name-prefix pbmid_llava_cap_r1 --output-root "$RUNDIR" \
    --limit-chunks 1 --epochs "$EPOCHS" --warmup-epochs 0 --eval-epochs "$EPOCHS" \
    --rate-steps 1 --workers 0 --eval-enable-log > "$LOGDIR/$UUID.log" 2>&1 &
  i=$((i+1))
  while [[ $(jobs -rp | wc -l) -ge $NG ]]; do sleep 10; done
done
wait
echo "[llava_train] DONE. trained: $(find "$OUT_ROOT/$DATASET/llava_video/mid/ours/cap_r1" -name codec_tokens.pt 2>/dev/null | wc -l)"
