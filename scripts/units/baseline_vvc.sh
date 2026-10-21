#!/usr/bin/env bash
# VVC (vvenc/vvdec) pixel-path baseline — the MPEG-VCM anchor codec. Mirrors baseline_pixel.sh.
#   bash scripts/units/baseline_vvc.sh --uuid <video_idx> --qp 36 --gpu 0
set -eo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$REPO_ROOT"
source scripts/units/_common.sh
VVENC=third_party/baselines/vvenc/install/bin/vvencapp
VVDEC=third_party/baselines/vvdec/bin/release-static/vvdecapp
UUID=""; GPU="0"; QP="36"; BACKBONE="internvl"; RECON_ONLY=0
while [[ $# -gt 0 ]]; do case "$1" in
  --uuid) UUID="$2"; shift 2;; --gpu) GPU="$2"; shift 2;;
  --qp) QP="$2"; shift 2;; --backbone) BACKBONE="$2"; shift 2;;
  --recon-only) RECON_ONLY=1; shift;;
  *) echo "baseline_vvc: unknown arg $1" >&2; exit 2;; esac; done
[[ -n "$UUID" ]] || { echo "baseline_vvc: --uuid required" >&2; exit 2; }
MP4="$(qa_field "$UUID" mp4)"
ensure_frames "$UUID" "$MP4"
RES="$(ds frames.width)"
RECON="$VIDEO_CACHE/vvc_qp${QP}_recon"
ENC="$VIDEO_CACHE/vvc_qp${QP}.266"
if [[ -z "$(find "$RECON" -name 'recon_*.png' 2>/dev/null | head -1)" ]]; then
  mkdir -p "$RECON"
  Y4M="$VIDEO_CACHE/vvc_src.y4m"
  [[ -s "$Y4M" ]] || ffmpeg -y -framerate 30 -pattern_type glob -i "$RAW_CHUNK_DIR/*.png" -pix_fmt yuv420p "$Y4M" >"$VIDEO_CACHE/vvc_qp${QP}.log" 2>&1
  "$VVENC" --preset faster -i "$Y4M" -q "$QP" -o "$ENC" >>"$VIDEO_CACHE/vvc_qp${QP}.log" 2>&1
  "$VVDEC" -b "$ENC" -o "$VIDEO_CACHE/vvc_qp${QP}_rec.y4m" >>"$VIDEO_CACHE/vvc_qp${QP}.log" 2>&1
  ffmpeg -y -i "$VIDEO_CACHE/vvc_qp${QP}_rec.y4m" "$RECON/recon_%04d.png" >>"$VIDEO_CACHE/vvc_qp${QP}.log" 2>&1
  rm -f "$VIDEO_CACHE/vvc_qp${QP}_rec.y4m"
fi
NF="$(find "$RAW_CHUNK_DIR" -maxdepth 1 -name '*.png' | wc -l)"
BPP="$(python3 -c "import os;print(round(os.path.getsize('$ENC')*8/($NF*$RES*$RES),4))")"
if [[ "$RECON_ONLY" == "1" ]]; then echo "[baseline_vvc:recon-only] $UUID qp$QP bpp=$BPP recon=$RECON"; exit 0; fi
QUESTION="$(qa_field "$UUID" question)"; LETTER="$(qa_field "$UUID" expected_letter)"
SC="$(ds frames.sample_count)"; build_opt_flags "$UUID"
QA_OUT="$VIDEO_CACHE/qa_vvc_qp${QP}.json"
t0=$(date +%s)
CUDA_VISIBLE_DEVICES="$GPU" python src/machine_codec_pipeline/vlm/internvl_backend.py \
  --qa-raw-frames "$RECON" --question "$QUESTION" --expected-letter "$LETTER" \
  --sample-count "$SC" --output-json "$QA_OUT" "${OPT_FLAGS[@]}" \
  >"$VIDEO_CACHE/qa_vvc_qp${QP}.eval.log" 2>&1
t1=$(date +%s)
CORRECT="$(field_from_json "$QA_OUT" correct)"; PARSED="$(field_from_json "$QA_OUT" parsed_letter)"
csv_append "$DATASET" "$BACKBONE" "vvc_qp${QP}" "mid" "vvc" "$UUID" "$BPP" "$CORRECT" "$PARSED" "$LETTER" "$((t1-t0))" vvc
echo "[baseline_vvc] $UUID qp$QP bpp=$BPP correct=$CORRECT in $((t1-t0))s"
