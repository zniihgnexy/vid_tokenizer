#!/usr/bin/env bash
# SMC++ (IEEE TPAMI 2025, unsupervised video semantic compression) pixel-path baseline:
# transcode the SAME sampled frames (VVC base layer + semantic enhancement stream,
# GOP10 LDP, official transcode settings) -> semantics-enhanced recon -> frozen-VLM QA.
# Mirrors baseline_dcvc.sh. Runs the official driver (patched copy
# transcode_frames_vidtok.py: env-var seq_root/valid_list/image_tmpl, nothing else changed)
# in the 'video_semantic_coding' conda env.
# Rate lever = --test_crf (paper ladder: 51 47 43 39 35).
# ⚠️ bit accounting: sum_br = measured VVC bits + entropy-model ESTIMATE for the semantic
# stream (their protocol); recorded as-is, disclosed in the paper.
#   bash scripts/units/baseline_smcpp.sh --uuid <video_idx> --crf 43 --gpu 0 [--recon-only]
set -eo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$REPO_ROOT"
source scripts/units/_common.sh
SMCPP_DIR="${SMCPP_DIR:-/mnt/nas/xinyizheng/vcm_baselines/repos/VideoSemanticCompression-Pytorch}"
SMCPP_PY="${SMCPP_PY:-/home/xinyizheng/anaconda3/envs/video_semantic_coding/bin/python}"

UUID=""; GPU="0"; CRF="43"; BACKBONE="internvl"; RECON_ONLY=0
while [[ $# -gt 0 ]]; do case "$1" in
  --uuid) UUID="$2"; shift 2;; --gpu) GPU="$2"; shift 2;;
  --crf) CRF="$2"; shift 2;; --backbone) BACKBONE="$2"; shift 2;;
  --recon-only) RECON_ONLY=1; shift;;
  *) echo "baseline_smcpp: unknown arg $1" >&2; exit 2;; esac; done
[[ -n "$UUID" ]] || { echo "baseline_smcpp: --uuid required" >&2; exit 2; }

MP4="$(qa_field "$UUID" mp4)"
ensure_frames "$UUID" "$MP4"
RES="$(ds frames.width)"
NF="$(find "$RAW_CHUNK_DIR" -maxdepth 1 -name '*.png' | wc -l)"

# absolute paths: the driver runs with cwd inside the SMC++ repo
VC_ABS="$(readlink -f "$VIDEO_CACHE")"
STAGE="$VC_ABS/smcpp_stage"; DEST="$VC_ABS/smcpp_crf${CRF}_dest"
RECON="$VC_ABS/smcpp_crf${CRF}_recon"
LOG="$VC_ABS/smcpp_crf${CRF}.log"
if [[ -z "$(find "$RECON/" -name '*.png' 2>/dev/null | head -1)" ]]; then
  mkdir -p "$STAGE" "$DEST"
  ln -sfn "$(readlink -f "$RAW_CHUNK_DIR")" "$STAGE/$UUID"
  VALID="$VC_ABS/smcpp_valid.txt"; echo "$UUID $NF 0" > "$VALID"
  PORT=$((20000 + GPU * 137 + RANDOM % 100))
  te0=$(date +%s)
  ( cd "$SMCPP_DIR" && \
    env -u PYTORCH_CUDA_ALLOC_CONF \
      VIDTOK_SEQ_ROOT="$STAGE" VIDTOK_VALID_LIST="$VALID" VIDTOK_IMAGE_TMPL='{:04d}.png' \
      CUDA_VISIBLE_DEVICES="$GPU" "$SMCPP_PY" -m torch.distributed.launch \
      --master_port="$PORT" --nproc_per_node 1 \
      VideoDatasetList/Davis2017/transcode_frames_vidtok.py \
      --fp 32 --lr 0.0001 -b 1 -j 3 --root_path ./ --dataset k60k_brrand --dataset_eval k400_video \
      --type action_backbone.TSM --aug_crop_scale 1 --no_video_scale --agg_type agg \
      --input_size 224 --arch resnet50 --num_segments 10 --beta 2 --alpha 4 \
      --checkpoint_dir "./checkpoints/temp_${PORT}" --temporal_compression \
      --encoder_net_type smc_plus --encoder_1st vanilla --enc_dim 32 --last_Tlayer_causual --lambda_bpp 4 \
      --test_crf "$CRF" --codec_type h266 --evaluate --test_codec_gop 10 \
      --resume_main pretrain_models/coding/SMC_plus.pth.tar \
      --trancode_src_dir "$STAGE" --trancode_dest_dir "$DEST" ) >"$LOG" 2>&1
  te1=$(date +%s)
  echo "[baseline_smcpp] $UUID crf$CRF transcode took $((te1-te0))s" | tee -a "$LOG"
  [[ -n "$(find "$DEST/$UUID/" -name '*.png' 2>/dev/null | head -1)" ]] \
    || { echo "baseline_smcpp: no recon PNGs in $DEST/$UUID (see $LOG)" >&2; exit 3; }
  ln -sfn "$(readlink -f "$DEST/$UUID")" "$RECON"
  grep "average" "$LOG" | tail -1 > "$VIDEO_CACHE/smcpp_crf${CRF}.bpp"
fi
# sum_br = H265_br + meta_br (bpp); last float on the "average ..." line
BPP="$(grep -oE '[0-9]+\.[0-9]+' "$VIDEO_CACHE/smcpp_crf${CRF}.bpp" | tail -1)"
[[ -n "$BPP" ]] || { echo "baseline_smcpp: could not parse bpp (see $LOG)" >&2; exit 3; }

if [[ "$RECON_ONLY" == "1" ]]; then
  csv_append "$DATASET" "$BACKBONE" "smcpp_crf${CRF}" "NA" "smcpp" "$UUID" "$BPP" "NA" "NA" "NA" "0" smcpp_recononly
  echo "[baseline_smcpp] $UUID crf$CRF bpp=$BPP recon-only"
  exit 0
fi

QUESTION="$(qa_field "$UUID" question)"; LETTER="$(qa_field "$UUID" expected_letter)"
SC="$(ds frames.sample_count)"; build_opt_flags "$UUID"
QA_OUT="$VIDEO_CACHE/qa_smcpp_crf${CRF}.json"
t0=$(date +%s)
CUDA_VISIBLE_DEVICES="$GPU" python src/machine_codec_pipeline/vlm/internvl_backend.py \
  --qa-raw-frames "$RECON" --question "$QUESTION" --expected-letter "$LETTER" \
  --sample-count "$SC" --output-json "$QA_OUT" "${OPT_FLAGS[@]}" \
  >"$VIDEO_CACHE/qa_smcpp_crf${CRF}.eval.log" 2>&1
t1=$(date +%s)
CORRECT="$(field_from_json "$QA_OUT" correct)"; PARSED="$(field_from_json "$QA_OUT" parsed_letter)"
csv_append "$DATASET" "$BACKBONE" "smcpp_crf${CRF}" "NA" "smcpp" "$UUID" "$BPP" "$CORRECT" "$PARSED" "$LETTER" "$((t1-t0))" smcpp
echo "[baseline_smcpp] $UUID crf$CRF bpp=$BPP correct=$CORRECT in $((t1-t0))s"
