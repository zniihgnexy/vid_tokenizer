#!/usr/bin/env bash
set -euo pipefail

# Launch one bounded shared-gating repair run that swaps the main teacher
# feature target to relation-preserving consistency while preserving
# semantic-change weighting and temporal-delta consistency.

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
WORKTREE_ROOT=$(cd -- "${SCRIPT_DIR}/../../.." && pwd)
QUEST_ROOT=$(cd -- "${WORKTREE_ROOT}/../../.." && pwd)
NVRC_ROOT="${WORKTREE_ROOT}/experiments/main/upstream_shared_gating_snapshot/third_party/NVRC"

DATASET_NAME="${DATASET_NAME:-ego4d_small_bridge_16f}"
DEFAULT_DATASET_DIR="${WORKTREE_ROOT}/tmp/ego4d_bounded_bridge_r1/data"
if [[ -z "${DATASET_DIR:-}" ]]; then
  if [[ -d "${DEFAULT_DATASET_DIR}/${DATASET_NAME}" ]]; then
    DATASET_DIR="${DEFAULT_DATASET_DIR}"
  else
    FOUND_DATASET_PATH=$(find "${QUEST_ROOT}" -type d -path "*/tmp/ego4d_bounded_bridge_r1/data/${DATASET_NAME}" | head -n 1 || true)
    if [[ -n "${FOUND_DATASET_PATH}" ]]; then
      DATASET_DIR="${FOUND_DATASET_PATH%/${DATASET_NAME}}"
    else
      DATASET_DIR="${DEFAULT_DATASET_DIR}"
    fi
  fi
fi
NUM_FRAMES="${NUM_FRAMES:-16}"
FRAME_HEIGHT="${FRAME_HEIGHT:-32}"
FRAME_WIDTH="${FRAME_WIDTH:-32}"
OUTPUT_ROOT="${OUTPUT_ROOT:-${WORKTREE_ROOT}/experiments/main}"
EXP_NAME="${EXP_NAME:-shared_gating_relation_repair_ego4d16f_smoke_r1}"
DEFAULT_RESUME_ROOT="${WORKTREE_ROOT}/experiments/main/shared_gating_interface_export_ego4d16f_chunk00_smoke_r1"
if [[ -z "${RESUME_ROOT:-}" ]]; then
  if [[ -f "${DEFAULT_RESUME_ROOT}/checkpoints/0000/pytorch_model.bin" ]]; then
    RESUME_ROOT="${DEFAULT_RESUME_ROOT}"
  else
    FOUND_RESUME_PATH=$(find "${QUEST_ROOT}" -type f -path "*/shared_gating_interface_export_ego4d16f_chunk00_smoke_r1/checkpoints/0000/pytorch_model.bin" | head -n 1 || true)
    if [[ -n "${FOUND_RESUME_PATH}" ]]; then
      RESUME_ROOT="${FOUND_RESUME_PATH%/checkpoints/0000/pytorch_model.bin}"
    else
      RESUME_ROOT="/home/xinyizheng/vid_tokenizer/DeepScientist/quests/001/.ds/worktrees/shared-semantic-gated-dual-path-tiny-local-r1/experiments/main/shared_semantic_gated_dual_path_tiny_local_r1"
    fi
  fi
fi

DATASET_PATH="${DATASET_DIR}/${DATASET_NAME}"
if [[ ! -d "${DATASET_PATH}" ]]; then
  echo "Missing bounded dataset at ${DATASET_PATH}" >&2
  exit 1
fi

mkdir -p "${OUTPUT_ROOT}"

echo "Launching bounded shared-gating relation repair smoke"
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
  --train-task-config "${NVRC_ROOT}/scripts/configs/tasks/overfit/l1_teacher-resnet18-relation-semchange-delta.yaml" \
  --eval-task-config "${NVRC_ROOT}/scripts/configs/tasks/overfit/l1_teacher-resnet18-relation-semchange-delta.yaml" \
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
