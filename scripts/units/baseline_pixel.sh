#!/usr/bin/env bash
# baseline_pixel.sh -- ATOMIC UNIT: pixel-codec baseline (PQ1).
# HEVC-encode the SAME frames the codec uses at a chosen quality, decode, feed the
# reconstructed frames through the frozen VLM (standard pixel path), and record the
# REAL bitrate (bpp from the encoded file size). Appends one row (interface=pixel).
#
#   bash scripts/units/baseline_pixel.sh --uuid <video_idx> --crf 28 --gpu 0
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$REPO_ROOT"
source scripts/units/_common.sh

UUID=""; GPU="0"; CRF="28"; BACKBONE="internvl"; FPS="30"; RECON_ONLY=0
while [[ $# -gt 0 ]]; do case "$1" in
  --uuid) UUID="$2"; shift 2;; --gpu) GPU="$2"; shift 2;;
  --crf) CRF="$2"; shift 2;; --backbone) BACKBONE="$2"; shift 2;;
  --recon-only) RECON_ONLY=1; shift;;
  *) echo "baseline_pixel: unknown arg $1" >&2; exit 2;; esac; done
[[ -n "$UUID" ]] || { echo "baseline_pixel: --uuid required" >&2; exit 2; }
export GPU

MP4="$(qa_field "$UUID" mp4)"
ensure_frames "$UUID" "$MP4"
RES="$(ds frames.width)"

ENC="$VIDEO_CACHE/hevc_crf${CRF}.mp4"
RECON="$VIDEO_CACHE/hevc_crf${CRF}_recon"
mkdir -p "$RECON"
# encode the raw PNG sequence -> HEVC, then decode back to PNGs
ffmpeg -y -framerate "$FPS" -pattern_type glob -i "$RAW_CHUNK_DIR/*.png" \
  -c:v libx265 -crf "$CRF" -pix_fmt yuv420p -x265-params log-level=error "$ENC" \
  >"$VIDEO_CACHE/hevc_crf${CRF}.log" 2>&1
ffmpeg -y -i "$ENC" "$RECON/recon_%04d.png" >>"$VIDEO_CACHE/hevc_crf${CRF}.log" 2>&1

NF="$(find "$RAW_CHUNK_DIR" -maxdepth 1 -name '*.png' | wc -l)"
BPP="$(python - "$ENC" "$NF" "$RES" <<'PY'
import os, sys
b = os.path.getsize(sys.argv[1]); nf = int(sys.argv[2]); r = int(sys.argv[3])
print(round(b * 8 / (nf * r * r), 4) if nf and r else 'NA')
PY
)"

if [[ "$RECON_ONLY" == "1" ]]; then
  echo "[baseline_pixel:recon-only] $UUID crf=$CRF bpp=$BPP recon=$RECON"
  exit 0
fi

QUESTION="$(qa_field "$UUID" question)"
LETTER="$(qa_field "$UUID" expected_letter)"
SC="$(ds frames.sample_count)"
build_opt_flags "$UUID"
QA_OUT="$VIDEO_CACHE/qa_pixel_crf${CRF}.json"

t0=$(date +%s)
CUDA_VISIBLE_DEVICES="$GPU" python src/machine_codec_pipeline/vlm/internvl_backend.py \
  --qa-raw-frames "$RECON" --question "$QUESTION" --expected-letter "$LETTER" \
  --sample-count "$SC" --output-json "$QA_OUT" "${OPT_FLAGS[@]}" \
  >"$VIDEO_CACHE/qa_pixel_crf${CRF}.eval.log" 2>&1
t1=$(date +%s)

CORRECT="$(field_from_json "$QA_OUT" correct)"
PARSED="$(field_from_json "$QA_OUT" parsed_letter)"
csv_append "$DATASET" "$BACKBONE" "crf${CRF}" NA pixel "$UUID" "$BPP" "$CORRECT" "$PARSED" "$LETTER" "$((t1-t0))" hevc
echo "[baseline_pixel] $UUID crf=$CRF bpp=$BPP correct=$CORRECT in $((t1-t0))s"
