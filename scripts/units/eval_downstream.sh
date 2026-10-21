#!/usr/bin/env bash
# eval_downstream.sh -- ATOMIC UNIT: evaluate ONE trained codec's downstream
# multiple-choice accuracy on the real EgoSchema GT. Works for both trainable
# interfaces (ours = mid-layer, final = final-layer); the eval path is identical
# (codec latent -> full frozen encoder -> projector -> LLM), only the run dir +
# CSV label differ. HEAVY (loads the full frozen LLM). Appends one row to $RESULTS_CSV.
#
#   bash scripts/units/eval_downstream.sh --uuid <video_idx> --rate mid \
#        --backbone internvl --layer mid --interface ours --gpu 0
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$REPO_ROOT"
source scripts/units/_common.sh

UUID=""; RATE="mid"; BACKBONE="internvl"; LAYER="mid"; INTERFACE="ours"; CAPACITY=""; GPU="0"; SEED=""; LOSSVAR=""
while [[ $# -gt 0 ]]; do case "$1" in
  --uuid) UUID="$2"; shift 2;; --rate) RATE="$2"; shift 2;;
  --backbone) BACKBONE="$2"; shift 2;; --layer) LAYER="$2"; shift 2;;
  --interface) INTERFACE="$2"; shift 2;;
  --capacity) CAPACITY="$2"; shift 2;;
  --gpu) GPU="$2"; shift 2;;
  --seed) SEED="$2"; shift 2;;
  --loss-variant) LOSSVAR="$2"; shift 2;;
  *) echo "eval_downstream: unknown arg $1" >&2; exit 2;; esac; done
[[ -n "$UUID" ]] || { echo "eval_downstream: --uuid required" >&2; exit 2; }

# RATE_TAG matches train_codec: cap_<name> on the capacity axis, else the rate label.
if [[ -n "$CAPACITY" ]]; then RATE_TAG="cap_${CAPACITY}"; else RATE_TAG="$RATE"; fi
[[ -n "$LOSSVAR" ]] && RATE_TAG="${RATE_TAG}_${LOSSVAR}"   # mirrors train_codec LSUFFIX
[[ -n "$SEED" ]] && RATE_TAG="${RATE_TAG}_seed${SEED}"
[[ -n "${RATE_SUFFIX:-}" ]] && RATE_TAG="${RATE_TAG}${RATE_SUFFIX}"   # mirrors train_codec (E-01/E-02 variants)
RUNDIR="$OUT_ROOT/$DATASET/$BACKBONE/$LAYER/$INTERFACE/$RATE_TAG/$UUID"
TOKENS="$(find "$RUNDIR" -name codec_tokens.pt 2>/dev/null | head -1)"
[[ -n "$TOKENS" ]] || { echo "eval_downstream: no codec_tokens.pt in $RUNDIR (train first)" >&2; exit 1; }

QUESTION="$(qa_field "$UUID" question)"
LETTER="$(qa_field "$UUID" expected_letter)"
build_opt_flags "$UUID"
QA_OUT="$RUNDIR/qa_egoschema.json"

t0=$(date +%s)
CUDA_VISIBLE_DEVICES="$GPU" python src/machine_codec_pipeline/vlm/internvl_backend.py \
  --qa-tokens "$TOKENS" --question "$QUESTION" --expected-letter "$LETTER" \
  --output-json "$QA_OUT" "${OPT_FLAGS[@]}" >"$RUNDIR/qa_eval.log" 2>&1
t1=$(date +%s)

BPP="$(bpp_from_run "$RUNDIR")"
CORRECT="$(field_from_json "$QA_OUT" correct)"
PARSED="$(field_from_json "$QA_OUT" parsed_letter)"
csv_append "$DATASET" "$BACKBONE" "$RATE_TAG" "$LAYER" "$INTERFACE" "$UUID" "$BPP" "$CORRECT" "$PARSED" "$LETTER" "$((t1-t0))" codec
echo "[eval_downstream] $UUID/$INTERFACE/$RATE_TAG bpp=$BPP correct=$CORRECT in $((t1-t0))s"
