#!/usr/bin/env bash
# UG-ICM (AAAI 2025, multimodal-supervised generalized image coding for machines)
# pixel-path baseline, applied ALL-INTRA (per-frame) to the SAME sampled frames ->
# recon -> frozen-VLM QA. Declared in the paper as a per-frame image-ICM baseline.
# Mirrors baseline_dcvc.sh. Rate lever = released quality checkpoints q1..q4.
#   bash scripts/units/baseline_ugicm.sh --uuid <video_idx> --q 4 --gpu 0 [--recon-only]
set -eo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$REPO_ROOT"
source scripts/units/_common.sh
UGICM_PY="${UGICM_PY:-/home/xinyizheng/anaconda3/envs/ugicm/bin/python}"
UGICM_CKPT_DIR="${UGICM_CKPT_DIR:-/mnt/nas/xinyizheng/vcm_baselines/weights/ugicm/UG-ICM}"

UUID=""; GPU="0"; Q="4"; BACKBONE="internvl"; RECON_ONLY=0
while [[ $# -gt 0 ]]; do case "$1" in
  --uuid) UUID="$2"; shift 2;; --gpu) GPU="$2"; shift 2;;
  --q) Q="$2"; shift 2;; --backbone) BACKBONE="$2"; shift 2;;
  --recon-only) RECON_ONLY=1; shift;;
  *) echo "baseline_ugicm: unknown arg $1" >&2; exit 2;; esac; done
[[ -n "$UUID" ]] || { echo "baseline_ugicm: --uuid required" >&2; exit 2; }
CKPT="$UGICM_CKPT_DIR/${Q}.pth.tar"
[[ -f "$CKPT" ]] || { echo "baseline_ugicm: missing checkpoint $CKPT" >&2; exit 2; }

MP4="$(qa_field "$UUID" mp4)"
ensure_frames "$UUID" "$MP4"
RECON="$VIDEO_CACHE/ugicm_q${Q}_recon"
if [[ -z "$(find "$RECON" -name 'recon_*.png' 2>/dev/null | head -1)" ]]; then
  mkdir -p "$RECON"
  BPP_LINE=$(env -u PYTORCH_CUDA_ALLOC_CONF CUDA_VISIBLE_DEVICES="$GPU" "$UGICM_PY" tools/ugicm_codec_recon.py \
    --frames-dir "$RAW_CHUNK_DIR" --out-dir "$RECON" --ckpt "$CKPT" 2>"$VIDEO_CACHE/ugicm_q${Q}.log" | tail -1)
  echo "$BPP_LINE" > "$VIDEO_CACHE/ugicm_q${Q}.bpp"
fi
BPP="$(grep -oE '[0-9.]+' "$VIDEO_CACHE/ugicm_q${Q}.bpp" | head -1)"

if [[ "$RECON_ONLY" == "1" ]]; then
  csv_append "$DATASET" "$BACKBONE" "ugicm_q${Q}" "NA" "ugicm" "$UUID" "$BPP" "NA" "NA" "NA" "0" ugicm_recononly
  echo "[baseline_ugicm] $UUID q$Q bpp=$BPP recon-only"
  exit 0
fi

QUESTION="$(qa_field "$UUID" question)"; LETTER="$(qa_field "$UUID" expected_letter)"
SC="$(ds frames.sample_count)"; build_opt_flags "$UUID"
QA_OUT="$VIDEO_CACHE/qa_ugicm_q${Q}.json"
t0=$(date +%s)
CUDA_VISIBLE_DEVICES="$GPU" python src/machine_codec_pipeline/vlm/internvl_backend.py \
  --qa-raw-frames "$RECON" --question "$QUESTION" --expected-letter "$LETTER" \
  --sample-count "$SC" --output-json "$QA_OUT" "${OPT_FLAGS[@]}" \
  >"$VIDEO_CACHE/qa_ugicm_q${Q}.eval.log" 2>&1
t1=$(date +%s)
CORRECT="$(field_from_json "$QA_OUT" correct)"; PARSED="$(field_from_json "$QA_OUT" parsed_letter)"
csv_append "$DATASET" "$BACKBONE" "ugicm_q${Q}" "NA" "ugicm" "$UUID" "$BPP" "$CORRECT" "$PARSED" "$LETTER" "$((t1-t0))" ugicm
echo "[baseline_ugicm] $UUID q$Q bpp=$BPP correct=$CORRECT in $((t1-t0))s"
