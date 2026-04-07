#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEFAULT_REPO_DATASET_ROOT="${REPO_ROOT}/Datasets/UVG/1920x1080"

SOURCE_ROOT=""
OUTPUT_ROOT="${DEFAULT_REPO_DATASET_ROOT}"
REPO_LINK_ROOT="${DEFAULT_REPO_DATASET_ROOT}"
HOME_LINK_ROOT="${HOME}/Datasets/PNG/UVG/1920x1080"
FFMPEG_BIN="${FFMPEG_BIN:-ffmpeg}"
PROBE_ONLY=0
OVERWRITE=0

usage() {
  cat <<EOF
Prepare the UVG dataset layout expected by the local NVRC configs.

The PNG conversion step requires \`ffmpeg\`. For the repo-local conda workflow on
this machine, install it with:
  conda install -n NVRC -c conda-forge ffmpeg -y

Usage:
  $(basename "$0") --probe-only [--source-root PATH] [--output-root PATH]
  $(basename "$0") --source-root PATH [--output-root PATH] [--overwrite]

Options:
  --source-root PATH     Directory containing raw .yuv files.
  --output-root PATH     PNG dataset root. Default: ${DEFAULT_REPO_DATASET_ROOT}
  --repo-link-root PATH  Repo-side dataset root. Default: ${DEFAULT_REPO_DATASET_ROOT}
  --home-link-root PATH  Home-side compatibility link. Default: ${HOME}/Datasets/PNG/UVG/1920x1080
  --overwrite            Rebuild PNG directories that already exist.
  --probe-only           Report the current path state without converting data.
  --help                 Show this message.

Expected input file names:
  Beauty_1920x1080_yuv420p.yuv
  Beauty.yuv

Output layout:
  <output-root>/Beauty/0001.png
  <output-root>/Bosphorus/0001.png

The helper keeps the prepared dataset under the local repo by default and creates a
compatibility link at ~/Datasets/PNG/UVG/1920x1080 for the vendored NVRC configs.
EOF
}

derive_video_id() {
  local file_name="$1"
  local base_name
  base_name="$(basename "${file_name}")"
  base_name="${base_name%_1920x1080_yuv420p.yuv}"
  base_name="${base_name%.yuv}"
  printf '%s\n' "${base_name}"
}

link_path() {
  local link_root="$1"
  local target_root="$2"

  if [ "${link_root}" = "${target_root}" ]; then
    return 0
  fi

  mkdir -p "$(dirname "${link_root}")"

  if [ -L "${link_root}" ]; then
    ln -sfn "${target_root}" "${link_root}"
    return 0
  fi

  if [ -e "${link_root}" ]; then
    printf 'refusing to replace existing non-symlink path: %s\n' "${link_root}" >&2
    return 1
  fi

  ln -s "${target_root}" "${link_root}"
}

print_probe() {
  local yuv_file
  local yuv_files=()

  printf 'source_root=%s\n' "${SOURCE_ROOT:-<unset>}"
  printf 'output_root=%s\n' "${OUTPUT_ROOT}"
  printf 'repo_link_root=%s\n' "${REPO_LINK_ROOT}"
  printf 'home_link_root=%s\n' "${HOME_LINK_ROOT}"

  if [ -e "${OUTPUT_ROOT}" ]; then
    printf 'output_root_exists=yes\n'
  else
    printf 'output_root_exists=no\n'
  fi

  if [ -e "${REPO_LINK_ROOT}" ] || [ -L "${REPO_LINK_ROOT}" ]; then
    printf 'repo_link_exists=yes\n'
  else
    printf 'repo_link_exists=no\n'
  fi

  if [ -e "${HOME_LINK_ROOT}" ] || [ -L "${HOME_LINK_ROOT}" ]; then
    printf 'home_link_exists=yes\n'
  else
    printf 'home_link_exists=no\n'
  fi

  if [ -z "${SOURCE_ROOT}" ]; then
    printf 'source_root_status=unset\n'
    return 0
  fi

  if [ ! -d "${SOURCE_ROOT}" ]; then
    printf 'source_root_status=missing\n'
    return 0
  fi

  printf 'source_root_status=present\n'

  while IFS= read -r yuv_file; do
    yuv_files+=("${yuv_file}")
  done < <(find "${SOURCE_ROOT}" -maxdepth 1 -type f -iname '*.yuv' | sort)
  printf 'candidate_yuv_count=%s\n' "${#yuv_files[@]}"

  for yuv_file in "${yuv_files[@]}"; do
    printf 'candidate=%s video_id=%s\n' "$(basename "${yuv_file}")" "$(derive_video_id "${yuv_file}")"
  done
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --source-root)
      SOURCE_ROOT="$2"
      shift 2
      ;;
    --output-root)
      OUTPUT_ROOT="$2"
      shift 2
      ;;
    --repo-link-root)
      REPO_LINK_ROOT="$2"
      shift 2
      ;;
    --home-link-root)
      HOME_LINK_ROOT="$2"
      shift 2
      ;;
    --probe-only)
      PROBE_ONLY=1
      shift
      ;;
    --overwrite)
      OVERWRITE=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      printf 'unknown argument: %s\n\n' "$1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [ "${PROBE_ONLY}" -eq 1 ]; then
  print_probe
  exit 0
fi

if [ -z "${SOURCE_ROOT}" ]; then
  printf 'missing required --source-root argument\n\n' >&2
  usage >&2
  exit 1
fi

if [ ! -d "${SOURCE_ROOT}" ]; then
  printf 'source root does not exist: %s\n' "${SOURCE_ROOT}" >&2
  exit 1
fi

if ! command -v "${FFMPEG_BIN}" >/dev/null 2>&1; then
  cat >&2 <<EOF
ffmpeg is required but not available at ${FFMPEG_BIN}
Recommended fix for this repo:
  conda install -n NVRC -c conda-forge ffmpeg -y

Then rerun:
  conda run -n NVRC bash ${REPO_ROOT}/tools/prepare_uvg_dataset.sh --source-root /path/to/uvg_yuv_files
EOF
  exit 1
fi

yuv_files=()
while IFS= read -r yuv_file; do
  yuv_files+=("${yuv_file}")
done < <(find "${SOURCE_ROOT}" -maxdepth 1 -type f -iname '*.yuv' | sort)

if [ "${#yuv_files[@]}" -eq 0 ]; then
  printf 'no .yuv files found under %s\n' "${SOURCE_ROOT}" >&2
  exit 1
fi

mkdir -p "${OUTPUT_ROOT}"

for yuv_file in "${yuv_files[@]}"; do
  video_id="$(derive_video_id "${yuv_file}")"
  output_dir="${OUTPUT_ROOT}/${video_id}"

  if [ -d "${output_dir}" ] && [ "${OVERWRITE}" -ne 1 ]; then
    printf 'skip_existing_output=%s\n' "${output_dir}"
    continue
  fi

  rm -rf "${output_dir}"
  mkdir -p "${output_dir}"

  "${FFMPEG_BIN}" -y \
    -video_size 1920x1080 \
    -pixel_format yuv420p \
    -i "${yuv_file}" \
    "${output_dir}/%04d.png"

  printf 'prepared_video=%s output_dir=%s\n' "${video_id}" "${output_dir}"
done

link_path "${REPO_LINK_ROOT}" "${OUTPUT_ROOT}"
link_path "${HOME_LINK_ROOT}" "${OUTPUT_ROOT}"

printf 'repo_link_target=%s -> %s\n' "${REPO_LINK_ROOT}" "${OUTPUT_ROOT}"
printf 'home_link_target=%s -> %s\n' "${HOME_LINK_ROOT}" "${OUTPUT_ROOT}"
