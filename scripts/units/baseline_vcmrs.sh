#!/usr/bin/env bash
# MPEG VCM-RS v2.0 (ISO/IEC 23888-2 reference software; standards-track VCM) pixel-path
# baseline: encode the SAME sampled frames at a chosen QP -> reconstructed frames ->
# frozen-VLM QA. Mirrors baseline_dcvc.sh. The encoder runs in the 'vcm' conda env
# (repo: /mnt/nas/xinyizheng/vcm_baselines/repos/vcm_rs_v2, mirror approved 2026-07-10);
# flags follow the repo's own video smoke test (PostFilter IMA, InterMachineAdapter 0).
#   bash scripts/units/baseline_vcmrs.sh --uuid <video_idx> --qp 42 --gpu 0 [--recon-only]
set -eo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$REPO_ROOT"
source scripts/units/_common.sh
VCMRS_PY="${VCMRS_PY:-/home/xinyizheng/anaconda3/envs/vcm/bin/python}"

UUID=""; GPU="0"; QP="42"; BACKBONE="internvl"; RECON_ONLY=0
while [[ $# -gt 0 ]]; do case "$1" in
  --uuid) UUID="$2"; shift 2;; --gpu) GPU="$2"; shift 2;;
  --qp) QP="$2"; shift 2;; --backbone) BACKBONE="$2"; shift 2;;
  --recon-only) RECON_ONLY=1; shift;;
  *) echo "baseline_vcmrs: unknown arg $1" >&2; exit 2;; esac; done
[[ -n "$UUID" ]] || { echo "baseline_vcmrs: --uuid required" >&2; exit 2; }

MP4="$(qa_field "$UUID" mp4)"
ensure_frames "$UUID" "$MP4"
RES="$(ds frames.width)"

OUT="$VIDEO_CACHE/vcmrs_qp${QP}"
RECON="$VIDEO_CACHE/vcmrs_qp${QP}_recon"
if [[ -z "$(find "$RECON/" -name '*.png' 2>/dev/null | head -1)" ]]; then
  mkdir -p "$OUT"
  te0=$(date +%s)
  # env -u: torch 1.12 in the vcm env rejects expandable_segments (nvrc-era alloc conf).
  # PATH prefix: the encoder spawns NNManager with bare `python` — it must resolve to the
  # vcm env, not the active nvrc env. VCMRS_PORT: set per-worker for parallel encodes.
  env -u PYTORCH_CUDA_ALLOC_CONF PATH="$(dirname "$VCMRS_PY"):$PATH" \
    CUDA_VISIBLE_DEVICES="$GPU" "$VCMRS_PY" -m vcmrs.encoder \
    ${VCMRS_PORT:+--port "$VCMRS_PORT"} \
    --directory_as_video --quality "$QP" \
    --PostFilter IMA --InterMachineAdapter 0 \
    --output_dir "$OUT" --working_dir "$OUT/work" \
    "$RAW_CHUNK_DIR" >"$VIDEO_CACHE/vcmrs_qp${QP}.log" 2>&1
  te1=$(date +%s)
  echo "[baseline_vcmrs] $UUID qp$QP encode took $((te1-te0))s" | tee -a "$VIDEO_CACHE/vcmrs_qp${QP}.log"
  # encoder emits output_dir/recon/<input_basename>/ (PNG frames) + output_dir/bitstream
  RDIR="$(find "$OUT/recon" -name '*.png' -printf '%h\n' 2>/dev/null | sort -u | head -1)"
  [[ -n "$RDIR" ]] || { echo "baseline_vcmrs: no recon PNGs under $OUT/recon (see .log)" >&2; exit 3; }
  ln -sfn "$(readlink -f "$RDIR")" "$RECON"
  "$VCMRS_PY" - "$RECON" <<'PY' >> "$VIDEO_CACHE/vcmrs_qp${QP}.log"
import sys, glob
from PIL import Image
f = sorted(glob.glob(sys.argv[1] + '/*.png'))
print(f"recon check: {len(f)} pngs, first mode={Image.open(f[0]).mode} size={Image.open(f[0]).size}")
PY
fi

# real bitrate from the bitstream bytes (all VCM NAL units included — CTC accounting)
BIN="$OUT/bitstream"
[[ -f "$BIN" ]] || BIN="$(find "$OUT/bitstream" -type f 2>/dev/null | head -1)"
[[ -n "$BIN" && -f "$BIN" ]] || { echo "baseline_vcmrs: bitstream not found under $OUT" >&2; exit 3; }
NF="$(find "$RAW_CHUNK_DIR" -maxdepth 1 -name '*.png' | wc -l)"
BPP="$(python - "$BIN" "$NF" "$RES" <<'PY'
import os, sys
b = os.path.getsize(sys.argv[1]); nf = int(sys.argv[2]); r = int(sys.argv[3])
print(round(b * 8 / (nf * r * r), 4) if nf and r else 'NA')
PY
)"

if [[ "$RECON_ONLY" == "1" ]]; then
  csv_append "$DATASET" "$BACKBONE" "vcmrs_qp${QP}" "NA" "vcmrs" "$UUID" "$BPP" "NA" "NA" "NA" "0" vcmrs_recononly
  echo "[baseline_vcmrs] $UUID qp$QP bpp=$BPP recon-only"
  exit 0
fi

QUESTION="$(qa_field "$UUID" question)"; LETTER="$(qa_field "$UUID" expected_letter)"
SC="$(ds frames.sample_count)"; build_opt_flags "$UUID"
QA_OUT="$VIDEO_CACHE/qa_vcmrs_qp${QP}.json"
t0=$(date +%s)
CUDA_VISIBLE_DEVICES="$GPU" python src/machine_codec_pipeline/vlm/internvl_backend.py \
  --qa-raw-frames "$RECON" --question "$QUESTION" --expected-letter "$LETTER" \
  --sample-count "$SC" --output-json "$QA_OUT" "${OPT_FLAGS[@]}" \
  >"$VIDEO_CACHE/qa_vcmrs_qp${QP}.eval.log" 2>&1
t1=$(date +%s)
CORRECT="$(field_from_json "$QA_OUT" correct)"; PARSED="$(field_from_json "$QA_OUT" parsed_letter)"
csv_append "$DATASET" "$BACKBONE" "vcmrs_qp${QP}" "NA" "vcmrs" "$UUID" "$BPP" "$CORRECT" "$PARSED" "$LETTER" "$((t1-t0))" vcmrs
echo "[baseline_vcmrs] $UUID qp$QP bpp=$BPP correct=$CORRECT in $((t1-t0))s"
