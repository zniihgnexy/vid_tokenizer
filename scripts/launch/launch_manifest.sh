#!/usr/bin/env bash
# launch_manifest.sh -- expand scripts/control.sh into a FLAT JOB MANIFEST:
# one self-contained command per line, each independent, with a `--gpu __GPU__`
# placeholder the launcher substitutes. Loops over the DATASETS axis (§14).
#
#   bash scripts/launch/launch_manifest.sh                 # print manifest to stdout
#   bash scripts/launch/launch_manifest.sh > jobs.txt      # save it
#   sed 's/__GPU__/0/' jobs.txt | head | bash              # run a slice on GPU 0
#
# Per-dataset manifests must already exist (build once with the dataset's prep
# script, e.g. tools/egoschema_prep.py). egoschema is auto-built if missing.
# All logging goes to stderr so stdout is ONLY job lines.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$REPO_ROOT"

# shellcheck disable=SC1091
source scripts/control.sh 1>&2

contains() { [[ " $INTERFACES " == *" $1 "* ]]; }
U="scripts/units"

for DS in $DATASETS; do
  DS_CONFIG="configs/datasets/$DS.yaml"
  DS_MANIFEST="outputs/datasets/$DS"
  if [[ ! -f "$DS_CONFIG" ]]; then
    echo "[manifest] SKIP dataset '$DS' -- no $DS_CONFIG" 1>&2; continue
  fi
  # Ensure the manifest (only egoschema has a built-in prep; others must be prebuilt).
  HAVE=0
  [[ -f "$DS_MANIFEST/manifest.jsonl" ]] && HAVE="$(grep -c . "$DS_MANIFEST/manifest.jsonl" || true)"
  if [[ ! -f "$DS_MANIFEST/manifest.jsonl" || "$HAVE" -lt "$N_VIDEOS" ]]; then
    if [[ "$DS" == "egoschema" ]]; then
      echo "[manifest] building egoschema manifest (have=$HAVE need=$N_VIDEOS) ..." 1>&2
      python tools/egoschema_prep.py --dataset-config "$DS_CONFIG" --n "$N_VIDEOS" --out-dir "$DS_MANIFEST" 1>&2
    else
      echo "[manifest] SKIP dataset '$DS' -- manifest missing/short ($HAVE<$N_VIDEOS). Run its prep script first." 1>&2
      continue
    fi
  fi

  UUIDS="$(python - "$DS_MANIFEST/manifest.jsonl" "$N_VIDEOS" <<'PY'
import json, sys
ids = [json.loads(l)['video_idx'] for l in open(sys.argv[1]) if l.strip()]
n = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] else len(ids)
print(' '.join(ids[:n]))
PY
)"
  # Env prefix that pins every unit on this line to this dataset.
  E="DATASET=$DS DATASET_CONFIG=$DS_CONFIG DATASET_MANIFEST_DIR=$DS_MANIFEST"

  # Trainable interfaces (codec is trained, then evaluated). ours = mid-layer
  # alignment, final = final-layer alignment (Latent-INR-style baseline).
  # Rate axis = CAPACITIES (INR size) when set, else RATES (lambda).
  for itf in ours final; do
    contains "$itf" || continue
    for b in $BACKBONES; do for l in $LAYERS; do for u in $UUIDS; do
      if [[ -n "$CAPACITIES" ]]; then
        for c in $CAPACITIES; do
          echo "$E bash $U/train_codec.sh --uuid $u --rate cap --capacity $c --backbone $b --layer $l --interface $itf --gpu __GPU__ --epochs $EPOCHS && $E bash $U/eval_downstream.sh --uuid $u --rate cap --capacity $c --backbone $b --layer $l --interface $itf --gpu __GPU__"
        done
      else
        for r in $RATES; do
          echo "$E bash $U/train_codec.sh --uuid $u --rate $r --backbone $b --layer $l --interface $itf --gpu __GPU__ --epochs $EPOCHS && $E bash $U/eval_downstream.sh --uuid $u --rate $r --backbone $b --layer $l --interface $itf --gpu __GPU__"
        done
      fi
    done; done; done
  done
  if contains oracle; then
    for u in $UUIDS; do echo "$E bash $U/eval_oracle.sh --uuid $u --gpu __GPU__"; done
  fi
  if contains pixel; then
    for crf in $PIXEL_CRFS; do for u in $UUIDS; do
      echo "$E bash $U/baseline_pixel.sh --uuid $u --crf $crf --gpu __GPU__"
    done; done
  fi
  for missing in feature vvc dcvc; do
    contains "$missing" && echo "# TODO interface=$missing not implemented yet (§14 method column; Stage 3/4)" 1>&2 || true
  done
done
