#!/usr/bin/env bash
# launch_local.sh -- run the job manifest on local GPUs, round-robin, with at
# most one job per GPU at a time. For multi-server, split the manifest from
# launch_manifest.sh and run this (or a slice) on each box.
#
#   bash scripts/launch/launch_local.sh                       # uses scripts/control.sh
#   GPUS="0 1 2 3" RATES="mid" N_VIDEOS=2 bash scripts/launch/launch_local.sh
set -eo pipefail   # NOT nounset: elastic GPU_PID assoc-array expands empty under set -u on older bash
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"; cd "$REPO_ROOT"

# shellcheck disable=SC1091
source scripts/control.sh
source scripts/units/_gpus.sh

# GPUS="auto" -> ELASTIC: pick whatever GPU is free RIGHT NOW (shared server). Else
# use the fixed list. GPU_MIN_FREE_MB = how much free mem a job needs (default 22GB
# for the 8B eval); GPU_MAX_PAR caps concurrency.
AUTO=0; [[ "${GPUS:-}" == auto* ]] && AUTO=1
MIN_FREE="${GPU_MIN_FREE_MB:-22000}"
MAX_PAR="${GPU_MAX_PAR:-8}"
read -r -a GPU_ARR <<< "${GPUS:-}"
if [[ $AUTO -eq 0 ]]; then
  [[ ${#GPU_ARR[@]} -ge 1 ]] || { echo "launch_local: no GPUS set" >&2; exit 2; }
fi

mapfile -t JOBS < <(bash scripts/launch/launch_manifest.sh)
echo "[launch_local] ${#JOBS[@]} job lines; mode=$([[ $AUTO -eq 1 ]] && echo auto:min=${MIN_FREE}MB,max=${MAX_PAR} || echo "fixed:${GPU_ARR[*]}")"
echo "[launch_local] results -> $RESULTS_CSV"

declare -A GPU_PID  # GPU_PID[g] = pid of my job currently on card g

reap() { [[ ${#GPU_PID[@]} -gt 0 ]] || return 0; local g; for g in "${!GPU_PID[@]}"; do kill -0 "${GPU_PID[$g]}" 2>/dev/null || unset 'GPU_PID[$g]'; done; }
nlive() { reap; echo "${#GPU_PID[@]}"; }
launch_on() {
  local g="$1"; local cmd="$2"; local c="${cmd//__GPU__/$g}"
  echo "[launch_local] gpu=$g :: $c"
  { bash -c "$c" || echo "[launch_local] UNIT FAILED (continuing): $c" >&2; } &
  GPU_PID[$g]=$!
}

dispatch_fixed() {
  local cmd="$1" g pid
  while true; do
    for g in "${GPU_ARR[@]}"; do
      pid="${GPU_PID[$g]:-}"
      if [[ -z "$pid" ]] || ! kill -0 "$pid" 2>/dev/null; then launch_on "$g" "$cmd"; return; fi
    done
    wait -n || true
  done
}

dispatch_auto() {
  local cmd="$1" cand g
  while true; do
    reap
    if (( ${#GPU_PID[@]} < MAX_PAR )); then
      for cand in $(free_gpus "$MIN_FREE"); do
        [[ -n "${GPU_PID[$cand]:-}" ]] && continue   # already running my job
        launch_on "$cand" "$cmd"; return
      done
    fi
    # nothing usable right now: if I have live jobs, wait for one; else poll (others hold GPUs)
    if (( ${#GPU_PID[@]} > 0 )); then wait -n || true; else echo "[launch_local|auto] no free GPU (others busy); waiting 30s..."; sleep 30; fi
  done
}

for job in "${JOBS[@]}"; do
  [[ -z "$job" || "$job" == \#* ]] && continue
  if [[ $AUTO -eq 1 ]]; then dispatch_auto "$job"; else dispatch_fixed "$job"; fi
done
wait
echo "[launch_local] DONE. Inspect $RESULTS_CSV ; per-unit cost in */unit_cost.json"
