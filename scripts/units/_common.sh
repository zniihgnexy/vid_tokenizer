#!/usr/bin/env bash
# _common.sh -- shared helpers sourced by every scripts/units/*.sh unit.
# Assumes the `nvrc` conda env is active (python has torch, pyyaml, pandas,
# pyarrow) and that the working dir is the repo root.

# Defaults (overridden by control.sh env when launched via scripts/launch/*).
OUT_ROOT="${OUT_ROOT:-outputs/campaign}"
DATASET="${DATASET:-egoschema}"                                   # dataset axis (§14)
DATASET_CONFIG="${DATASET_CONFIG:-configs/datasets/$DATASET.yaml}"
DATASET_MANIFEST_DIR="${DATASET_MANIFEST_DIR:-outputs/datasets/$DATASET}"
RESULTS_CSV="${RESULTS_CSV:-$OUT_ROOT/results.csv}"

# ds KEY.PATH -> value from the dataset yaml (e.g. ds frames.num_frames)
ds() {
  python - "$DATASET_CONFIG" "$1" <<'PY'
import yaml, sys, functools
c = yaml.safe_load(open(sys.argv[1]))
print(functools.reduce(lambda d, k: d[k], sys.argv[2].split('.'), c))
PY
}

# qa_field UUID FIELD -> value from the per-video sidecar qa.json
qa_field() {
  python - "$DATASET_MANIFEST_DIR/$1/qa.json" "$2" <<'PY'
import json, sys
print(json.load(open(sys.argv[1]))[sys.argv[2]])
PY
}

# field_from_json FILE KEY -> top-level value (or "None")
field_from_json() {
  python - "$1" "$2" <<'PY'
import json, sys
print(json.load(open(sys.argv[1])).get(sys.argv[2]))
PY
}

# build_opt_flags UUID -> fills global array OPT_FLAGS=(--option .. --option ..)
build_opt_flags() {
  mapfile -t _OPTS < <(python - "$DATASET_MANIFEST_DIR/$1/qa.json" <<'PY'
import json, sys
for o in json.load(open(sys.argv[1]))['options']:
    print(o)
PY
)
  OPT_FLAGS=()
  local o
  for o in "${_OPTS[@]}"; do OPT_FLAGS+=(--option "$o"); done
}

# bpp_from_run RUNDIR -> aggregate_metrics_mean.bpp_avg from the chunked summary
bpp_from_run() {
  local s
  s="$(find "$1" -name '*chunked_summary.json' 2>/dev/null | head -1)"
  [[ -n "$s" ]] || { echo "NA"; return; }
  python - "$s" <<'PY'
import json, sys
j = json.load(open(sys.argv[1]))
print(j.get('aggregate_metrics_mean', {}).get('bpp_avg', 'NA'))
PY
}

# ensure_frames UUID MP4 -> sets VIDEO_CACHE, CHUNKDIR, CIDX, RAW_CHUNK_DIR;
# extracts+chunks frames once (shared across rates/interfaces). Needs GPU set.
ensure_frames() {
  local uuid="$1" mp4="$2"
  local res nframes prefix sampling
  # Env RES / NUM_FRAMES override the dataset yaml (so control.sh owns resolution
  # and frame count without editing per-dataset yaml).
  res="${RES:-$(ds frames.width)}"
  nframes="${NUM_FRAMES:-$(ds frames.num_frames)}"
  # frames.sampling: contiguous (first N) | uniform (N spread across whole clip).
  # Env SAMPLING overrides the config (so a campaign can flip it without editing yaml).
  sampling="${SAMPLING:-$(ds frames.sampling 2>/dev/null || echo contiguous)}"
  [[ -z "$sampling" || "$sampling" == "None" ]] && sampling="contiguous"
  # Sampling is part of the cache key so uniform/contiguous never reuse each other's frames.
  VIDEO_CACHE="$OUT_ROOT/_videos/$DATASET/${uuid}_${res}_${sampling}"
  CHUNKDIR="$VIDEO_CACHE/chunks"
  prefix="eg_${uuid}_${res}_${sampling}_chunk"
  CIDX="$CHUNKDIR/${prefix}_chunk_index.json"
  # Per-video lock: when the same uuid is dispatched to two GPUs at once (different
  # rates/interfaces), serialize extraction so they don't race on the same cache dir.
  mkdir -p "$(dirname "$VIDEO_CACHE")"
  (
    flock 200
    if [[ ! -f "$CIDX" ]]; then
      mkdir -p "$VIDEO_CACHE"
      CUDA_VISIBLE_DEVICES="${GPU:-0}" python tools/run_machine_codec_pipeline.py prepare-video \
        --video-path "$mp4" --output-dir "$VIDEO_CACHE" \
        --num-frames "$nframes" --width "$res" --height "$res" --chunk-size "$nframes" \
        --sampling "$sampling" \
        --chunk-output-root "$CHUNKDIR" --chunk-prefix "$prefix" \
        >"$VIDEO_CACHE/prep.log" 2>&1
    fi
  ) 200>"${VIDEO_CACHE}.lock"
  [[ -f "$CIDX" ]] || { echo "FATAL: prepare-video failed for $uuid (see $VIDEO_CACHE/prep.log)" >&2; return 1; }
  RAW_CHUNK_DIR="$(python - "$CIDX" <<'PY'
import json, sys
print(json.load(open(sys.argv[1]))['chunks'][0]['chunk_dir'])
PY
)"
}

# csv_append <12 comma-free fields> -> one locked row into RESULTS_CSV
csv_append() {
  local row hdr
  row="$(IFS=,; echo "$*")"
  hdr="dataset,backbone,rate,layer,interface,uuid,bpp,correct,parsed_letter,expected_letter,secs,note"
  mkdir -p "$(dirname "$RESULTS_CSV")"
  (
    flock 9
    [[ -s "$RESULTS_CSV" ]] || echo "$hdr" > "$RESULTS_CSV"
    echo "$row" >> "$RESULTS_CSV"
  ) 9>"$RESULTS_CSV.lock"
}
