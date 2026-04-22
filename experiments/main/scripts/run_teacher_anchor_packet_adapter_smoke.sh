#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPERIMENT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

BUNDLE_DIR="${1:-${EXPERIMENT_ROOT}/interface_bundles/shared_gating_teacher_packet_smoke_r1}"
OUTPUT_DIR="${2:-${EXPERIMENT_ROOT}/evals/teacher_anchor_packet_adapter_smoke_r1}"
DELTA_WEIGHT="${DELTA_WEIGHT:-8.0}"
ANCHOR_LOGIT_SCALE="${ANCHOR_LOGIT_SCALE:-16.0}"

python "${SCRIPT_DIR}/run_teacher_anchor_packet_eval.py" \
  --bundle-dir "${BUNDLE_DIR}" \
  --output-dir "${OUTPUT_DIR}" \
  --mode smoke \
  --delta-weight "${DELTA_WEIGHT}" \
  --anchor-logit-scale "${ANCHOR_LOGIT_SCALE}"
