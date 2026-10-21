#!/usr/bin/env bash
# DCVC-RT (CVPR2025, learned VIDEO codec) pixel-path baseline: sequential I+P encode
# the sampled frames at rate index qp -> recon -> frozen-VLM QA. Mirrors baseline_learned.sh.
#   bash scripts/units/baseline_dcvc.sh --uuid <video_idx> --qp 27 --gpu 0
set -eo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$REPO_ROOT"
source scripts/units/_common.sh
UUID=""; GPU="0"; QP="27"; BACKBONE="internvl"; RECON_ONLY=0
while [[ $# -gt 0 ]]; do case "$1" in
  --uuid) UUID="$2"; shift 2;; --gpu) GPU="$2"; shift 2;;
  --qp) QP="$2"; shift 2;; --backbone) BACKBONE="$2"; shift 2;;
  --recon-only) RECON_ONLY=1; shift;;
  *) echo "baseline_dcvc: unknown arg $1" >&2; exit 2;; esac; done
[[ -n "$UUID" ]] || { echo "baseline_dcvc: --uuid required" >&2; exit 2; }
MP4="$(qa_field "$UUID" mp4)"
ensure_frames "$UUID" "$MP4"
RECON="$VIDEO_CACHE/dcvc_q${QP}_recon"
if [[ -z "$(find "$RECON" -name 'recon_*.png' 2>/dev/null | head -1)" ]]; then
  mkdir -p "$RECON"
  BPP_LINE=$(CUDA_VISIBLE_DEVICES="$GPU" python tools/dcvc_codec_recon.py \
    --frames-dir "$RAW_CHUNK_DIR" --out-dir "$RECON" --qp "$QP" 2>"$VIDEO_CACHE/dcvc_q${QP}.log" | tail -1)
  echo "$BPP_LINE" > "$VIDEO_CACHE/dcvc_q${QP}.bpp"
fi
BPP="$(grep -oE '[0-9.]+' "$VIDEO_CACHE/dcvc_q${QP}.bpp" | head -1)"
if [[ "$RECON_ONLY" == "1" ]]; then
  # recon dir + bpp only; the stratified harvest does the multi-question VLM eval once.
  csv_append "$DATASET" "$BACKBONE" "dcvc_q${QP}" "mid" "dcvc" "$UUID" "$BPP" "NA" "NA" "NA" "0" dcvc_recononly
  echo "[baseline_dcvc] $UUID qp$QP bpp=$BPP recon-only"
  exit 0
fi
QUESTION="$(qa_field "$UUID" question)"; LETTER="$(qa_field "$UUID" expected_letter)"
SC="$(ds frames.sample_count)"; build_opt_flags "$UUID"
QA_OUT="$VIDEO_CACHE/qa_dcvc_q${QP}.json"
t0=$(date +%s)
CUDA_VISIBLE_DEVICES="$GPU" python src/machine_codec_pipeline/vlm/internvl_backend.py \
  --qa-raw-frames "$RECON" --question "$QUESTION" --expected-letter "$LETTER" \
  --sample-count "$SC" --output-json "$QA_OUT" "${OPT_FLAGS[@]}" \
  >"$VIDEO_CACHE/qa_dcvc_q${QP}.eval.log" 2>&1
t1=$(date +%s)
CORRECT="$(field_from_json "$QA_OUT" correct)"; PARSED="$(field_from_json "$QA_OUT" parsed_letter)"
csv_append "$DATASET" "$BACKBONE" "dcvc_q${QP}" "mid" "dcvc" "$UUID" "$BPP" "$CORRECT" "$PARSED" "$LETTER" "$((t1-t0))" dcvc
echo "[baseline_dcvc] $UUID qp$QP bpp=$BPP correct=$CORRECT in $((t1-t0))s"
