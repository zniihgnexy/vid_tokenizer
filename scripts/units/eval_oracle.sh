#!/usr/bin/env bash
# eval_oracle.sh -- ATOMIC UNIT: raw-frames MC accuracy = the ACCURACY CEILING.
# Feeds the original (lossless) frames through the same frozen VLM with the same
# MC prompt as the codec path. bpp is recorded as NA (infinite-rate reference).
# HEAVY. Appends one row to $RESULTS_CSV (interface=oracle).
#
#   bash scripts/units/eval_oracle.sh --uuid <video_idx> --gpu 0
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$REPO_ROOT"
source scripts/units/_common.sh

UUID=""; GPU="0"; BACKBONE="internvl"
while [[ $# -gt 0 ]]; do case "$1" in
  --uuid) UUID="$2"; shift 2;; --gpu) GPU="$2"; shift 2;;
  --backbone) BACKBONE="$2"; shift 2;;
  *) echo "eval_oracle: unknown arg $1" >&2; exit 2;; esac; done
[[ -n "$UUID" ]] || { echo "eval_oracle: --uuid required" >&2; exit 2; }
export GPU

MP4="$(qa_field "$UUID" mp4)"
ensure_frames "$UUID" "$MP4"   # reuses the SAME frames the codec trains on (fair)

QUESTION="$(qa_field "$UUID" question)"
LETTER="$(qa_field "$UUID" expected_letter)"
SC="$(ds frames.sample_count)"
build_opt_flags "$UUID"
QA_OUT="$OUT_ROOT/$DATASET/oracle/$UUID/qa_oracle.json"
mkdir -p "$(dirname "$QA_OUT")"

t0=$(date +%s)
CUDA_VISIBLE_DEVICES="$GPU" python src/machine_codec_pipeline/vlm/internvl_backend.py \
  --qa-raw-frames "$RAW_CHUNK_DIR" --question "$QUESTION" --expected-letter "$LETTER" \
  --sample-count "$SC" --output-json "$QA_OUT" "${OPT_FLAGS[@]}" \
  >"$OUT_ROOT/$DATASET/oracle/$UUID/qa_oracle.log" 2>&1
t1=$(date +%s)

CORRECT="$(field_from_json "$QA_OUT" correct)"
PARSED="$(field_from_json "$QA_OUT" parsed_letter)"
csv_append "$DATASET" "$BACKBONE" NA NA oracle "$UUID" NA "$CORRECT" "$PARSED" "$LETTER" "$((t1-t0))" oracle
echo "[eval_oracle] $UUID correct=$CORRECT in $((t1-t0))s (ceiling)"
