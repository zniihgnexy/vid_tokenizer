#!/usr/bin/env bash
# Learned-codec (CompressAI cheng2020-anchor, per-frame) pixel-path baseline:
# encode sampled frames at quality q -> recon -> frozen-VLM QA. Mirrors baseline_pixel.sh.
#   bash scripts/units/baseline_learned.sh --uuid <video_idx> --q 1 --gpu 0
set -eo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$REPO_ROOT"
source scripts/units/_common.sh
UUID=""; GPU="0"; Q="1"; BACKBONE="internvl"; RECON_ONLY=0
while [[ $# -gt 0 ]]; do case "$1" in
  --uuid) UUID="$2"; shift 2;; --gpu) GPU="$2"; shift 2;;
  --q) Q="$2"; shift 2;; --backbone) BACKBONE="$2"; shift 2;;
  --recon-only) RECON_ONLY=1; shift;;
  *) echo "baseline_learned: unknown arg $1" >&2; exit 2;; esac; done
[[ -n "$UUID" ]] || { echo "baseline_learned: --uuid required" >&2; exit 2; }
MP4="$(qa_field "$UUID" mp4)"
ensure_frames "$UUID" "$MP4"
RES="$(ds frames.width)"
RECON="$VIDEO_CACHE/learned_q${Q}_recon"
if [[ -z "$(find "$RECON" -name 'recon_*.png' 2>/dev/null | head -1)" ]]; then
  mkdir -p "$RECON"
  BPP_LINE=$(CUDA_VISIBLE_DEVICES="$GPU" python tools/learned_codec_recon.py \
    --frames-dir "$RAW_CHUNK_DIR" --out-dir "$RECON" --quality "$Q" 2>"$VIDEO_CACHE/learned_q${Q}.log" | tail -1)
  echo "$BPP_LINE" > "$VIDEO_CACHE/learned_q${Q}.bpp"
fi
BPP="$(grep -oE '[0-9.]+' "$VIDEO_CACHE/learned_q${Q}.bpp" | head -1)"
if [[ "$RECON_ONLY" == "1" ]]; then
  csv_append "$DATASET" "$BACKBONE" "learned_q${Q}" "NA" "learned" "$UUID" "$BPP" "NA" "NA" "NA" "0" learned_recononly
  echo "[baseline_learned] $UUID q$Q bpp=$BPP recon-only"
  exit 0
fi
QUESTION="$(qa_field "$UUID" question)"; LETTER="$(qa_field "$UUID" expected_letter)"
SC="$(ds frames.sample_count)"; build_opt_flags "$UUID"
QA_OUT="$VIDEO_CACHE/qa_learned_q${Q}.json"
t0=$(date +%s)
CUDA_VISIBLE_DEVICES="$GPU" python src/machine_codec_pipeline/vlm/internvl_backend.py \
  --qa-raw-frames "$RECON" --question "$QUESTION" --expected-letter "$LETTER" \
  --sample-count "$SC" --output-json "$QA_OUT" "${OPT_FLAGS[@]}" \
  >"$VIDEO_CACHE/qa_learned_q${Q}.eval.log" 2>&1
t1=$(date +%s)
CORRECT="$(field_from_json "$QA_OUT" correct)"; PARSED="$(field_from_json "$QA_OUT" parsed_letter)"
csv_append "$DATASET" "$BACKBONE" "learned_q${Q}" "mid" "learned" "$UUID" "$BPP" "$CORRECT" "$PARSED" "$LETTER" "$((t1-t0))" learned
echo "[baseline_learned] $UUID q$Q bpp=$BPP correct=$CORRECT in $((t1-t0))s"
