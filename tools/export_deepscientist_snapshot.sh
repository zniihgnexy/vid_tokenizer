#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

QUEST_ROOT="${QUEST_ROOT:-/Users/wf24018/DeepScientist/quests/001}"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-${QUEST_ROOT}/.ds/worktrees/idea-idea-3f64faf1}"
EXPORT_ROOT="${EXPORT_ROOT:-${REPO_ROOT}/DeepScientist_export/quest_001}"

DOCS_DIR="${EXPORT_ROOT}/docs"
EXPERIMENT_DIR="${EXPORT_ROOT}/experiment"
RUN_SNAPSHOT_DIR="${EXPORT_ROOT}/run_snapshots"
MANIFEST_PATH="${EXPORT_ROOT}/SYNC_MANIFEST.txt"

if [ ! -d "${QUEST_ROOT}" ]; then
  printf 'quest root not found: %s\n' "${QUEST_ROOT}" >&2
  exit 1
fi

mkdir -p "${DOCS_DIR}" "${EXPERIMENT_DIR}" "${RUN_SNAPSHOT_DIR}"

copy_if_exists() {
  local src="$1"
  local dst="$2"
  if [ -f "${src}" ]; then
    mkdir -p "$(dirname "${dst}")"
    cp "${src}" "${dst}"
  fi
}

copy_if_exists "${QUEST_ROOT}/brief.md" "${DOCS_DIR}/brief.md"
copy_if_exists "${QUEST_ROOT}/plan.md" "${DOCS_DIR}/plan.md"
copy_if_exists "${QUEST_ROOT}/status.md" "${DOCS_DIR}/status.md"
copy_if_exists "${QUEST_ROOT}/SUMMARY.md" "${DOCS_DIR}/SUMMARY.md"
copy_if_exists "${QUEST_ROOT}/quest.yaml" "${DOCS_DIR}/quest.yaml"
copy_if_exists \
  "${QUEST_ROOT}/memory/knowledge/active-user-requirements.md" \
  "${DOCS_DIR}/active_user_requirements.md"

copy_if_exists "${WORKSPACE_ROOT}/PLAN.md" "${EXPERIMENT_DIR}/PLAN.md"
copy_if_exists "${WORKSPACE_ROOT}/CHECKLIST.md" "${EXPERIMENT_DIR}/CHECKLIST.md"

for run_dir in "${QUEST_ROOT}/experiments/main"/*; do
  [ -d "${run_dir}" ] || continue
  run_name="$(basename "${run_dir}")"
  dst_dir="${RUN_SNAPSHOT_DIR}/${run_name}"
  mkdir -p "${dst_dir}"
  copy_if_exists "${run_dir}/args.yaml" "${dst_dir}/args.yaml"
  if [ -f "${run_dir}/rank_0/logs.txt" ]; then
    tail -n 400 "${run_dir}/rank_0/logs.txt" > "${dst_dir}/logs.tail.txt"
  fi
done

{
  printf 'Export refreshed at: %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  printf 'Quest root: %s\n' "${QUEST_ROOT}"
  printf 'Workspace root: %s\n' "${WORKSPACE_ROOT}"
  printf 'Export root: %s\n' "${EXPORT_ROOT}"
} > "${MANIFEST_PATH}"

printf 'DeepScientist export refreshed under %s\n' "${EXPORT_ROOT}"
