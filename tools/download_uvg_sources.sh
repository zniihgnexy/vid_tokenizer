#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

DEFAULT_ARCHIVE_ROOT="${REPO_ROOT}/Datasets/UVG/source_archives"
DEFAULT_SOURCE_ROOT="${REPO_ROOT}/Datasets/UVG/source_yuv"
DEFAULT_VIDEOS="Beauty,Bosphorus,HoneyBee,Jockey,ReadySetGo,ShakeNDry,YachtRide"

ARCHIVE_ROOT="${DEFAULT_ARCHIVE_ROOT}"
SOURCE_ROOT="${DEFAULT_SOURCE_ROOT}"
VIDEOS_CSV="${DEFAULT_VIDEOS}"
PREPARE_AFTER_DOWNLOAD=0
PROBE_ONLY=0
OVERWRITE=0

CURL_BIN="${CURL_BIN:-curl}"
BSDTAR_BIN="${BSDTAR_BIN:-bsdtar}"
PREPARE_SCRIPT="${REPO_ROOT}/tools/prepare_uvg_dataset.sh"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-NVRC}"
FFMPEG_BIN="${FFMPEG_BIN:-}"

usage() {
  cat <<EOF
Download and extract the official 1920x1080 8-bit UVG YUV sources used by the
vendored NVRC setup.

Usage:
  $(basename "$0") [--probe-only] [--videos CSV] [--archive-root PATH] [--source-root PATH]
  $(basename "$0") [--videos CSV] [--archive-root PATH] [--source-root PATH] [--prepare] [--overwrite]

Options:
  --videos CSV         Comma-separated subset of:
                       Beauty,Bosphorus,HoneyBee,Jockey,ReadySetGo,ShakeNDry,YachtRide
                       Default: ${DEFAULT_VIDEOS}
  --archive-root PATH  Download location for .7z archives.
                       Default: ${DEFAULT_ARCHIVE_ROOT}
  --source-root PATH   Extraction location for raw .yuv files.
                       Default: ${DEFAULT_SOURCE_ROOT}
  --prepare            After extracting the raw .yuv files, run prepare_uvg_dataset.sh.
  --overwrite          Re-download archives and replace extracted .yuv files if they already exist.
  --probe-only         Print the planned URLs and paths without downloading.
  --help               Show this message.

Notes:
  - Source checked on 2026-04-04: https://ultravideo.fi/dataset.html
  - The seven standard 1080p archives total roughly 4.9 GiB compressed.
  - The prepare step needs ffmpeg. The recommended local fix is:
      conda install -n ${CONDA_ENV_NAME} -c conda-forge ffmpeg -y
EOF
}

video_url() {
  case "$1" in
    Beauty)
      printf '%s\n' 'https://ultravideo.fi/video/Beauty_1920x1080_120fps_420_8bit_YUV_RAW.7z'
      ;;
    Bosphorus)
      printf '%s\n' 'https://ultravideo.fi/video/Bosphorus_1920x1080_120fps_420_8bit_YUV_RAW.7z'
      ;;
    HoneyBee)
      printf '%s\n' 'https://ultravideo.fi/video/HoneyBee_1920x1080_120fps_420_8bit_YUV_RAW.7z'
      ;;
    Jockey)
      printf '%s\n' 'https://ultravideo.fi/video/Jockey_1920x1080_120fps_420_8bit_YUV_RAW.7z'
      ;;
    ReadySetGo)
      printf '%s\n' 'https://ultravideo.fi/video/ReadySetGo_1920x1080_120fps_420_8bit_YUV_RAW.7z'
      ;;
    ShakeNDry)
      printf '%s\n' 'https://ultravideo.fi/video/ShakeNDry_1920x1080_120fps_420_8bit_YUV_RAW.7z'
      ;;
    YachtRide)
      printf '%s\n' 'https://ultravideo.fi/video/YachtRide_1920x1080_120fps_420_8bit_YUV_RAW.7z'
      ;;
    *)
      printf 'unknown UVG video id: %s\n' "$1" >&2
      return 1
      ;;
  esac
}

require_command() {
  local command_name="$1"
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    printf 'required command not found: %s\n' "${command_name}" >&2
    return 1
  fi
}

download_archive() {
  local video_id="$1"
  local url archive_path

  url="$(video_url "${video_id}")"
  archive_path="${ARCHIVE_ROOT}/$(basename "${url}")"

  mkdir -p "${ARCHIVE_ROOT}"

  if [ -f "${archive_path}" ] && [ "${OVERWRITE}" -ne 1 ]; then
    printf 'skip_existing_archive=%s\n' "${archive_path}"
    return 0
  fi

  if [ "${OVERWRITE}" -eq 1 ]; then
    rm -f "${archive_path}"
  fi

  printf 'download_video=%s url=%s archive=%s\n' "${video_id}" "${url}" "${archive_path}"
  "${CURL_BIN}" -L --fail --continue-at - --output "${archive_path}" "${url}"
}

extract_archive() {
  local video_id="$1"
  local url archive_path target_path temp_dir yuv_count
  local yuv_file
  local yuv_files=()

  url="$(video_url "${video_id}")"
  archive_path="${ARCHIVE_ROOT}/$(basename "${url}")"
  target_path="${SOURCE_ROOT}/${video_id}_1920x1080_yuv420p.yuv"

  mkdir -p "${SOURCE_ROOT}"

  if [ -f "${target_path}" ] && [ "${OVERWRITE}" -ne 1 ]; then
    printf 'skip_existing_source=%s\n' "${target_path}"
    return 0
  fi

  if [ ! -f "${archive_path}" ]; then
    printf 'archive missing for %s: %s\n' "${video_id}" "${archive_path}" >&2
    return 1
  fi

  temp_dir="$(mktemp -d)"
  trap 'rm -rf "${temp_dir}"' RETURN

  printf 'extract_video=%s archive=%s\n' "${video_id}" "${archive_path}"
  "${BSDTAR_BIN}" -xf "${archive_path}" -C "${temp_dir}"

  while IFS= read -r yuv_file; do
    yuv_files+=("${yuv_file}")
  done < <(find "${temp_dir}" -type f -iname '*.yuv' | sort)
  yuv_count="${#yuv_files[@]}"
  if [ "${yuv_count}" -ne 1 ]; then
    printf 'expected exactly one .yuv file in %s but found %s\n' "${archive_path}" "${yuv_count}" >&2
    return 1
  fi

  if [ "${OVERWRITE}" -eq 1 ]; then
    rm -f "${target_path}"
  fi
  mv "${yuv_files[0]}" "${target_path}"
  printf 'extracted_source=%s\n' "${target_path}"

  rm -rf "${temp_dir}"
  trap - RETURN
}

run_prepare() {
  local prepare_args=("--source-root" "${SOURCE_ROOT}")

  if [ "${OVERWRITE}" -eq 1 ]; then
    prepare_args+=("--overwrite")
  fi

  if [ -n "${FFMPEG_BIN}" ]; then
    FFMPEG_BIN="${FFMPEG_BIN}" bash "${PREPARE_SCRIPT}" "${prepare_args[@]}"
    return 0
  fi

  if command -v ffmpeg >/dev/null 2>&1; then
    bash "${PREPARE_SCRIPT}" "${prepare_args[@]}"
    return 0
  fi

  if command -v conda >/dev/null 2>&1 && conda run -n "${CONDA_ENV_NAME}" ffmpeg -version >/dev/null 2>&1; then
    conda run -n "${CONDA_ENV_NAME}" env FFMPEG_BIN=ffmpeg /bin/bash "${PREPARE_SCRIPT}" "${prepare_args[@]}"
    return 0
  fi

  cat >&2 <<EOF
Downloaded and extracted UVG YUV sources successfully, but ffmpeg is still missing.
Recommended fix:
  conda install -n ${CONDA_ENV_NAME} -c conda-forge ffmpeg -y

Then rerun:
  $(basename "$0") --videos "${VIDEOS_CSV}" --prepare
EOF
  return 1
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --videos)
      VIDEOS_CSV="$2"
      shift 2
      ;;
    --archive-root)
      ARCHIVE_ROOT="$2"
      shift 2
      ;;
    --source-root)
      SOURCE_ROOT="$2"
      shift 2
      ;;
    --prepare)
      PREPARE_AFTER_DOWNLOAD=1
      shift
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

require_command "${CURL_BIN}"
require_command "${BSDTAR_BIN}"

IFS=',' read -r -a videos <<< "${VIDEOS_CSV}"

if [ "${PROBE_ONLY}" -eq 1 ]; then
  printf 'archive_root=%s\n' "${ARCHIVE_ROOT}"
  printf 'source_root=%s\n' "${SOURCE_ROOT}"
  printf 'prepare_after_download=%s\n' "${PREPARE_AFTER_DOWNLOAD}"
  for video_id in "${videos[@]}"; do
    printf 'video=%s url=%s archive=%s source=%s/%s_1920x1080_yuv420p.yuv\n' \
      "${video_id}" \
      "$(video_url "${video_id}")" \
      "${ARCHIVE_ROOT}/$(basename "$(video_url "${video_id}")")" \
      "${SOURCE_ROOT}" \
      "${video_id}"
  done
  exit 0
fi

for video_id in "${videos[@]}"; do
  download_archive "${video_id}"
  extract_archive "${video_id}"
done

if [ "${PREPARE_AFTER_DOWNLOAD}" -eq 1 ]; then
  run_prepare
fi
