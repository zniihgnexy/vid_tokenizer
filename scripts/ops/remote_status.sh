#!/usr/bin/env bash
# remote_status.sh — READ-ONLY remote inspection + results bundler.
# Run this ON THE REMOTE GPU HOST (/home/xinyizheng/vid_tokenizer). It never
# launches GPU jobs and never deletes anything. It:
#   1) reports which experiment/daemon processes are still alive,
#   2) prints GPU occupancy,
#   3) counts rows + (interface,rate) breakdown of every results.csv / stratified_*.csv,
#   4) tails the important driver logs,
#   5) bundles all small result files (CSVs, AUTO_RESULTS, paper_cells.json, key logs)
#      into ONE tarball you can scp back to the Mac.
#
# Usage (on remote):   bash scripts/ops/remote_status.sh
# Then from the Mac:   scp <remote>:/home/xinyizheng/vid_tokenizer/_status_bundle_*.tgz .
set -uo pipefail
cd /home/xinyizheng/vid_tokenizer 2>/dev/null || { echo "not on remote host"; exit 1; }
R=/mnt/nas/xinyizheng/vidtok_out
STAMP=$(date +%Y%m%d_%H%M)
OUT=_status_bundle_${STAMP}
mkdir -p "$OUT"

sec(){ printf '\n============================================================\n%s\n============================================================\n' "$*"; }

sec "0. WHERE / WHEN"
echo "host: $(hostname)   date: $(date)   London: $(TZ=Europe/London date '+%F %H:%M')"
echo "repo: $(pwd)"
echo "NAS : $R  ($( [ -d "$R" ] && echo mounted || echo 'NOT mounted!'))"

sec "1. ALIVE EXPERIMENT / DAEMON PROCESSES"
ps -eo pid,etime,cmd | grep -Ev 'grep|remote_status' | grep -E \
 'train_codec|eval_downstream|main_nvrc|baseline_(vcmrs|smcpp|ugicm|learned|pixel|vvc|dcvc)|harvest_stratified|_egos_lambda|_lamb_densify|_densify_finish|_b_sensitivity|_mlvu|_lvb|_davis|_auto_harvest|gpu_grab_daemon|gpu_keep_busy|fig_bdrate_full' \
 | tee "$OUT/alive_processes.txt"
[ -s "$OUT/alive_processes.txt" ] || echo "(nothing running — all nohup jobs have exited)"

sec "2. GPU OCCUPANCY"
nvidia-smi --query-gpu=index,memory.used,memory.free,utilization.gpu --format=csv 2>/dev/null | tee "$OUT/gpu.txt"

sec "3. RESULT FILES — row counts + (interface,rate) breakdown"
# scan both NAS gate dirs and the local outputs/ mirror
CSVS=$( { ls "$R"/gate1_*/results.csv "$R"/gate1_*/stratified_*.csv \
             outputs/gate1_*/results.csv outputs/gate1_*/stratified_*.csv \
             outputs/*.csv 2>/dev/null; } | sort -u )
for f in $CSVS; do
  [ -f "$f" ] || continue
  printf '\n--- %s  (rows=%s, mtime=%s) ---\n' "$f" "$(( $(wc -l < "$f") - 1 ))" "$(date -r "$f" '+%m-%d %H:%M' 2>/dev/null)"
  # breakdown by interface,rate (columns vary, so do it defensively in python)
  python3 - "$f" 2>/dev/null <<'PY' || echo "(non-standard columns; header printed below)"
import csv,sys,collections
f=sys.argv[1]
rows=list(csv.DictReader(open(f)))
if not rows: print("  (empty)"); sys.exit()
key=[k for k in ('interface','rate') if k in rows[0]]
if not key:
    print("  header:", ",".join(rows[0].keys())); sys.exit()
c=collections.Counter(tuple(r.get(k,'') for k in key) for r in rows)
for k,n in sorted(c.items()): print(f"   {'/'.join(k):40s} {n:4d} rows")
PY
done | tee "$OUT/result_rowcounts.txt"

sec "4. TAIL OF KEY DRIVER LOGS (last 8 lines each)"
for lg in egos_lambda_sweep egos_lambda egos_lambda_clean.nohup lamb_densify densify_finish \
          auto_harvest bd_after_harvest exp036_resume gpu_grab_daemon \
          ec_vcmrs_egos_s0 ec_vcmrs_egos_s1 ec_smcpp ec_ugicm ec_cheng cheng_reharvest \
          fastv_waiter cheng_waiter mlvu_ours_train lvb_ours_train \
          mlvu_qa_harvest lvb_qa_harvest e_g_certify; do
  for cand in "logs/${lg}.log" "logs/${lg}"; do
    [ -f "$cand" ] || continue
    printf '\n----- %s (mtime %s) -----\n' "$cand" "$(date -r "$cand" '+%m-%d %H:%M' 2>/dev/null)"
    tail -n 8 "$cand"
    break
  done
done | tee "$OUT/log_tails.txt"

sec "5. FIGURE FILES (mtime = last regen)"
ls -la figures/bdrate_full.* conference/Figures/bdrate_full.* figures/candidates/*.png 2>/dev/null | tee "$OUT/figures.txt"

sec "6. BUNDLING RESULTS FOR DOWNLOAD"
# copy all the small, valuable result artifacts into the bundle
for f in $CSVS; do [ -f "$f" ] && cp -p "$f" "$OUT/" 2>/dev/null; done
cp -p outputs/AUTO_RESULTS.txt outputs/paper_cells.json outputs/ALL_RESULTS_consolidated.csv "$OUT/" 2>/dev/null
mkdir -p "$OUT/logs"
cp -p logs/{egos_lambda*,lamb_densify*,densify_finish*,auto_harvest*,ec_*,exp036_resume*,mlvu_*,lvb_*,e_g_*,cheng_reharvest*}.log "$OUT/logs/" 2>/dev/null
tar czf "${OUT}.tgz" "$OUT" 2>/dev/null
echo "bundle: $(pwd)/${OUT}.tgz   ($(du -h "${OUT}.tgz" 2>/dev/null | cut -f1))"
echo
echo ">>> On the Mac, pull it with:"
echo "    scp <user>@<remote>:$(pwd)/${OUT}.tgz  /Users/wf24018/home/vid_tokenizer/"
echo ">>> then: tar xzf ${OUT}.tgz  and I'll read the CSVs directly."
