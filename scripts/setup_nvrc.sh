#!/usr/bin/env bash
# setup_nvrc.sh -- fetch the pinned upstream NVRC submodule and apply our patch (idempotent).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
git submodule update --init third_party/NVRC
cd third_party/NVRC
if git apply -p1 --reverse --check ../../patches/nvrc_machine_oriented_pipeline.patch 2>/dev/null; then
  echo "[setup_nvrc] patch already applied"
else
  git apply -p1 ../../patches/nvrc_machine_oriented_pipeline.patch
  echo "[setup_nvrc] patch applied"
fi
