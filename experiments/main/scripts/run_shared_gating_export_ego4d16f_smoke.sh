#!/usr/bin/env bash
set -euo pipefail

# Re-run the frozen shared-gating export smoke on the widened 16-frame bounded
# PNG surface without changing the accepted upstream contract.

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
WORKTREE_ROOT=$(cd -- "${SCRIPT_DIR}/../../.." && pwd)
NVRC_ROOT="${WORKTREE_ROOT}/experiments/main/upstream_shared_gating_snapshot/third_party/NVRC"

DATASET_DIR="${DATASET_DIR:-${WORKTREE_ROOT}/tmp/ego4d_bounded_bridge_r1/data}"
DATASET_NAME="${DATASET_NAME:-ego4d_small_bridge_16f}"
NUM_FRAMES="${NUM_FRAMES:-16}"
FRAME_HEIGHT="${FRAME_HEIGHT:-32}"
FRAME_WIDTH="${FRAME_WIDTH:-32}"
OUTPUT_ROOT="${OUTPUT_ROOT:-${WORKTREE_ROOT}/experiments/main}"
EXP_NAME="${EXP_NAME:-shared_gating_interface_export_ego4d16f_smoke_r1}"
RESUME_ROOT="${RESUME_ROOT:-/home/xinyizheng/vid_tokenizer/DeepScientist/quests/001/.ds/worktrees/shared-semantic-gated-dual-path-tiny-local-r1/experiments/main/shared_semantic_gated_dual_path_tiny_local_r1}"

DATASET_PATH="${DATASET_DIR}/${DATASET_NAME}"
if [[ ! -d "${DATASET_PATH}" ]]; then
  echo "Missing bounded dataset at ${DATASET_PATH}" >&2
  exit 1
fi

mkdir -p "${OUTPUT_ROOT}"

echo "Launching frozen shared-gating export smoke"
echo "  dataset_path: ${DATASET_PATH}"
echo "  num_frames: ${NUM_FRAMES}"
echo "  frame_size: ${FRAME_HEIGHT}x${FRAME_WIDTH}"
echo "  output_root: ${OUTPUT_ROOT}"
echo "  exp_name: ${EXP_NAME}"
echo "  resume_root: ${RESUME_ROOT}"

python "${NVRC_ROOT}/main_nvrc.py" \
  --exp-config "${NVRC_ROOT}/scripts/configs/nvrc/overfit/tiny-1e.yaml" \
  --train-data-config "${NVRC_ROOT}/scripts/configs/data/video/png/tiny_local.yaml" \
  --eval-data-config "${NVRC_ROOT}/scripts/configs/data/video/png/tiny_local.yaml" \
  --train-task-config "${NVRC_ROOT}/scripts/configs/tasks/overfit/l1_teacher-resnet18-shared-semchange-delta.yaml" \
  --eval-task-config "${NVRC_ROOT}/scripts/configs/tasks/overfit/l1_teacher-resnet18-shared-semchange-delta.yaml" \
  --compress-model-config "${NVRC_ROOT}/scripts/configs/nvrc/compress_models/nvrc_tiny_s1.yaml" \
  --model-config "${NVRC_ROOT}/scripts/configs/nvrc/models/teacher_tiny_32.yaml" \
  --train-dataset-dir "${DATASET_DIR}" \
  --train-dataset "${DATASET_NAME}" \
  --train-video-size "${NUM_FRAMES}" "${FRAME_HEIGHT}" "${FRAME_WIDTH}" \
  --train-patch-size 1 "${FRAME_HEIGHT}" "${FRAME_WIDTH}" \
  --train-fmt png \
  --eval-dataset-dir "${DATASET_DIR}" \
  --eval-dataset "${DATASET_NAME}" \
  --eval-video-size "${NUM_FRAMES}" "${FRAME_HEIGHT}" "${FRAME_WIDTH}" \
  --eval-patch-size 1 "${FRAME_HEIGHT}" "${FRAME_WIDTH}" \
  --eval-fmt png \
  --eval-enable-log true \
  --eval-only true \
  --resume "${RESUME_ROOT}" \
  --resume-model-only true \
  --workers 0 \
  --prefetch-factor 4 \
  --pin-mem true \
  --seed 0 \
  --start-frame 0 \
  --num-frames "${NUM_FRAMES}" \
  --output "${OUTPUT_ROOT}" \
  --exp-name "${EXP_NAME}" \
  "$@"
