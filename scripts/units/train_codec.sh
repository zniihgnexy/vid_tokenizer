#!/usr/bin/env bash
# train_codec.sh -- ATOMIC UNIT: train ONE per-video codec.
# LIGHT (the codec drops the LLM during training). Idempotent (skip if tokens exist).
#
#   bash scripts/units/train_codec.sh --uuid <video_idx> --rate mid \
#        --backbone internvl --layer mid --interface ours --gpu 0 --epochs 30
#
# --interface ours  -> mid-layer alignment (layer 12)   profile pathway_b_mid_rate_<r>
# --interface final -> final-layer alignment (layer 24) profile pathway_b_mid_final_rate_<r>
#   (Latent-INR-style baseline; same codec/rate/loss, only the alignment depth differs.)
#
# Produces codec_tokens.pt under
#   $OUT_ROOT/<dataset>/<backbone>/<layer>/<interface>/<rate>/<uuid>/
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$REPO_ROOT"
source scripts/units/_common.sh

UUID=""; RATE="mid"; BACKBONE="internvl"; LAYER="mid"; INTERFACE="ours"; CAPACITY=""; GPU="0"; EPOCHS="30"; SEED=""; TLAYER=""
while [[ $# -gt 0 ]]; do case "$1" in
  --uuid) UUID="$2"; shift 2;; --rate) RATE="$2"; shift 2;;
  --backbone) BACKBONE="$2"; shift 2;; --layer) LAYER="$2"; shift 2;;
  --interface) INTERFACE="$2"; shift 2;;
  --capacity) CAPACITY="$2"; shift 2;;
  --gpu) GPU="$2"; shift 2;; --epochs) EPOCHS="$2"; shift 2;;
  --seed) SEED="$2"; shift 2;;
  --teacher-layer) TLAYER="$2"; shift 2;;
  --loss-variant) LOSSVAR="$2"; shift 2;;
  *) echo "train_codec: unknown arg $1" >&2; exit 2;; esac; done
[[ -n "$UUID" ]] || { echo "train_codec: --uuid required" >&2; exit 2; }
export GPU

if [[ "$BACKBONE" != "internvl" ]]; then
  echo "[train_codec] backbone=$BACKBONE needs the generalized adapter (Stage 3) -- skipping."
  exit 0
fi

# Two rate mechanisms:
#  (a) lambda axis (legacy): --rate vlo|lo|mid|hi|vhi selects the loss profile.
#  (b) CAPACITY axis (Stage-1 rate knob): --capacity <name> fixes the loss profile
#      (lamb=1.0) and varies the INR size via --model-config teacher_cap_<name>.yaml.
#      The lambda floor saturates ~0.5 bpp; capacity is the real rate lever.
EXTRA=()
if [[ -n "$CAPACITY" ]]; then
  LSUFFIX=""
  case "$INTERFACE" in
    ours)
      # layer sweep: --teacher-layer {6,18} selects an N-variant profile; 12 = default mid.
      # loss ablation: --loss-variant {w0,w1,eta0} selects a loss-variant profile (at N=12).
      if [[ -n "${LOSSVAR:-}" && -n "$TLAYER" && "$TLAYER" != "12" ]]; then
        # lambda rung x alignment-layer variant (E-11 main config: lambXXX + N1224)
        PROFILE="pathway_b_mid_${LOSSVAR}_n${TLAYER}"
        [[ -f "third_party/NVRC/scripts/configs/tasks/overfit/l1_teacher-pathway-b-mid-${LOSSVAR}-N${TLAYER}.yaml" ]] \
          || { echo "[train_codec] no combined config ${LOSSVAR}-N${TLAYER}" >&2; exit 2; }
        LSUFFIX="_${LOSSVAR}_n${TLAYER}"
      elif [[ -n "${LOSSVAR:-}" ]]; then
        PROFILE="pathway_b_mid_${LOSSVAR}"
        [[ -f "third_party/NVRC/scripts/configs/tasks/overfit/l1_teacher-pathway-b-mid-${LOSSVAR}.yaml" ]] \
          || { echo "[train_codec] no loss-variant config ${LOSSVAR}" >&2; exit 2; }
        LSUFFIX="_${LOSSVAR}"
      elif [[ -n "$TLAYER" && "$TLAYER" != "12" ]]; then
        PROFILE="pathway_b_mid_n${TLAYER}"
        [[ -f "third_party/NVRC/scripts/configs/tasks/overfit/l1_teacher-pathway-b-mid-N${TLAYER}.yaml" ]] \
          || { echo "[train_codec] no layer-N${TLAYER} config" >&2; exit 2; }
        LSUFFIX="_n${TLAYER}"
      else PROFILE="pathway_b_mid"; fi
      ;;                                              # base loss, lamb=1.0, layer 12 (or N/loss-variant)
    final)                                            # lamb=1.0, layer 24 (Latent-INR-style baseline)
      # C1 lambda ablation: --loss-variant lamb025 selects pathway_b_mid_final_lamb025 (rate tag cap_r1_lamb025).
      if [[ -n "${LOSSVAR:-}" ]]; then
        PROFILE="pathway_b_mid_final_${LOSSVAR}"
        [[ -f "third_party/NVRC/scripts/configs/tasks/overfit/l1_teacher-pathway-b-mid-final-${LOSSVAR}.yaml" ]] \
          || { echo "[train_codec] no final-layer loss-variant config ${LOSSVAR}" >&2; exit 2; }
        LSUFFIX="_${LOSSVAR}"
      else PROFILE="pathway_b_mid_final_rate_mid"; fi
      ;;
    *) echo "[train_codec] interface=$INTERFACE not trainable (use ours|final)." >&2; exit 2;;
  esac
  MODELCFG="scripts/configs/nvrc/models/teacher_cap_${CAPACITY}.yaml"
  [[ -f "third_party/NVRC/$MODELCFG" ]] || { echo "[train_codec] no capacity config $MODELCFG" >&2; exit 2; }
  EXTRA+=(--model-config "$MODELCFG")
  RATE_TAG="cap_${CAPACITY}${LSUFFIX}"
else
  case "$INTERFACE" in
    ours)  PROFILE="pathway_b_mid_rate_${RATE}";;
    final) PROFILE="pathway_b_mid_final_rate_${RATE}";;
    *) echo "[train_codec] interface=$INTERFACE not trainable (use ours|final)." >&2; exit 2;;
  esac
  RATE_TAG="$RATE"
fi

# Seed passthrough (Phase 0c monotonicity diagnosis): tag the run dir so different
# seeds don't collide / get skip-if-trained, and forward --seed to the NVRC run.
if [[ -n "$SEED" ]]; then EXTRA+=(--seed "$SEED"); RATE_TAG="${RATE_TAG}_seed${SEED}"; fi
# E-01/E-02 (2026-10-04): RATE_SUFFIX tags a variant run (e.g. _dfilm, _ws10) so it never
# collides with the default run; NVRC_INIT_CODEC=<donor run dir> warm-starts the codec
# weights (--resume <dir> --resume-model-only true; dir must hold checkpoints/0000/pytorch_model.bin).
[[ -n "${RATE_SUFFIX:-}" ]] && RATE_TAG="${RATE_TAG}${RATE_SUFFIX}"
if [[ -n "${NVRC_INIT_CODEC:-}" ]]; then
  [[ -f "$NVRC_INIT_CODEC/checkpoints/0000/pytorch_model.bin" ]] || { echo "[train_codec] NVRC_INIT_CODEC has no checkpoints/0000/pytorch_model.bin: $NVRC_INIT_CODEC" >&2; exit 2; }
  # values starting with "--" must use the = form, otherwise argparse eats them as options
  EXTRA+=("--nvrc-arg=--resume" "--nvrc-arg=$NVRC_INIT_CODEC" "--nvrc-arg=--resume-model-only" "--nvrc-arg=true")
fi

MP4="$(qa_field "$UUID" mp4)"
ensure_frames "$UUID" "$MP4"

RUNDIR="$OUT_ROOT/$DATASET/$BACKBONE/$LAYER/$INTERFACE/$RATE_TAG/$UUID"
if [[ -n "$(find "$RUNDIR" -name codec_tokens.pt 2>/dev/null | head -1)" ]]; then
  echo "[train_codec] $UUID/$INTERFACE/$RATE_TAG already trained -- skip"; exit 0
fi
mkdir -p "$RUNDIR"

t0=$(date +%s)
CUDA_VISIBLE_DEVICES="$GPU" python tools/run_machine_codec_pipeline.py run-chunked \
  --profile "$PROFILE" --chunk-index "$CIDX" "${EXTRA[@]}" \
  --exp-name-prefix "pbmid_${INTERFACE}_${RATE_TAG}" --output-root "$RUNDIR" --limit-chunks 1 \
  --epochs "$EPOCHS" --warmup-epochs 0 --eval-epochs "$EPOCHS" \
  --rate-steps 1 --workers 0 --eval-enable-log >"$RUNDIR/codec.log" 2>&1
t1=$(date +%s)

echo "{\"unit\":\"train_codec\",\"uuid\":\"$UUID\",\"rate\":\"$RATE_TAG\",\"interface\":\"$INTERFACE\",\"capacity\":\"$CAPACITY\",\"backbone\":\"$BACKBONE\",\"layer\":\"$LAYER\",\"profile\":\"$PROFILE\",\"epochs\":$EPOCHS,\"secs\":$((t1-t0))}" > "$RUNDIR/unit_cost.json"
echo "[train_codec] $UUID/$INTERFACE/$RATE_TAG done in $((t1-t0))s -> $RUNDIR"
