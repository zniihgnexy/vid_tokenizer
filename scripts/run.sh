#!/usr/bin/env bash
# =============================================================================
#  run.sh -- one-command entry point. Clone the repo, edit scripts/control.sh,
#  then:   bash scripts/run.sh
#
#  It (1) activates the conda env named in control.sh, (2) prints the experiment
#  banner, (3) launches the gate over the GPUs you set. Override anything inline:
#       DATASET=egoschema N_VIDEOS=10 GPUS="0 1" bash scripts/run.sh
#
#  Inspect without running:   bash scripts/run.sh --dry   (prints the job list)
# =============================================================================
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

# Load the experiment definition (sets CONDA_ENV, paths, matrix).
# shellcheck disable=SC1091
source scripts/control.sh

# Activate conda env (portable across anaconda/miniconda installs).
if command -v conda >/dev/null 2>&1; then
  source "$(conda info --base)/etc/profile.d/conda.sh"
else
  for base in "$HOME/anaconda3" "$HOME/miniconda3" /opt/conda; do
    [[ -f "$base/etc/profile.d/conda.sh" ]] && source "$base/etc/profile.d/conda.sh" && break
  done
fi
conda activate "$CONDA_ENV" 2>/dev/null || {
  echo "[run] WARNING: could not 'conda activate $CONDA_ENV'; assuming the right python is already active." >&2
}

if [[ "${1:-}" == "--dry" ]]; then
  echo "[run] DRY RUN -- job manifest only (nothing executes):" >&2
  exec bash scripts/launch/launch_manifest.sh
fi

exec bash scripts/launch/launch_local.sh
