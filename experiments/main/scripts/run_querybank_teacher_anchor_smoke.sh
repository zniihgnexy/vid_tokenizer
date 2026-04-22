#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPERIMENT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

DEFAULT_COLLAPSE_SUMMARY="${EXPERIMENT_ROOT}/evals/shared_gating_query_collapse_localization_smoke_r1/summary.json"
OUTPUT_DIR="${OUTPUT_DIR:-${EXPERIMENT_ROOT}/evals/querybank_teacher_anchor_smoke_r1}"
DELTA_WEIGHT="${DELTA_WEIGHT:-8.0}"
ANCHOR_LOGIT_SCALE="${ANCHOR_LOGIT_SCALE:-16.0}"
CSLS_K="${CSLS_K:-3}"

declare -a BUNDLE_DIRS
if [[ "$#" -gt 0 ]]; then
  BUNDLE_DIRS=("$@")
else
  mapfile -t BUNDLE_DIRS < <(
    python - "${DEFAULT_COLLAPSE_SUMMARY}" <<'PY'
import json
import pathlib
import sys

summary_path = pathlib.Path(sys.argv[1])
summary = json.loads(summary_path.read_text(encoding="utf-8"))
for bundle_dir in summary["bundle_dirs"]:
    print(bundle_dir)
PY
  )
fi

python "${SCRIPT_DIR}/run_teacher_anchor_packet_eval.py" \
  --bundle-dir "${BUNDLE_DIRS[@]}" \
  --output-dir "${OUTPUT_DIR}" \
  --mode smoke \
  --delta-weight "${DELTA_WEIGHT}" \
  --anchor-logit-scale "${ANCHOR_LOGIT_SCALE}" \
  --csls-k "${CSLS_K}"
