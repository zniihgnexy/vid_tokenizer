#!/usr/bin/env bash
# health.sh -- ONE-SHOT, READ-ONLY health report for the CVPR-27 queue (run on estar).
# Prints a compact status the 30-min check loop can act on. Never launches or kills anything.
cd /home/xinyizheng/vid_tokenizer || exit 1
R=/mnt/nas/xinyizheng/vidtok_out
hf=$(df -BG /home | awk 'NR==2{gsub("G","",$4); print $4}')
echo "== $(date '+%m-%d %H:%M CST')  home_free=${hf}G  nas_free=$(df -h /mnt/nas | awk 'NR==2{print $4}')$( [ "$hf" -lt 15 ] && echo '  !! /home below 15G (someone else is filling it); job logs live on /home')"
# runner
pid=$(cat queue/runner.pid 2>/dev/null)
if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then echo "runner: ALIVE pid $pid$( [ -f STOP_QUEUE ] && echo ' (STOP_QUEUE present!)')"; else echo "runner: DEAD"; fi
echo "queue: pending=$(ls queue/pending 2>/dev/null | wc -l) running=$(ls queue/running 2>/dev/null | grep -c "\.sh$") done=$(ls queue/done 2>/dev/null | wc -l) failed=$(ls queue/failed 2>/dev/null | wc -l)"
echo "running: $(ls queue/running 2>/dev/null | grep "\.sh$" | tr "\n" " ")"
if ls queue/failed/*.sh >/dev/null 2>&1; then echo "FAILED jobs:"; for f in queue/failed/*.sh; do n=$(basename $f .sh); echo "  - $n :: $(grep -m1 -E 'Traceback|Error|OOM|out of memory|FileExistsError|FATAL' logs/queue/$n.log 2>/dev/null | cut -c1-140)"; done; fi
# error scan of running job logs (last 40 lines)
for f in queue/running/*.sh; do [ -f "$f" ] || continue; n=$(basename $f .sh)
  e=$(tail -40 logs/queue/$n.log 2>/dev/null | grep -E 'Traceback|Error|OOM|out of memory|FileExistsError|FATAL|RUN SUSPECT' | tail -1 | cut -c1-140)
  [ -n "$e" ] && echo "  ! $n: $e"
  # stall: log not modified for >45 min
  age=$(( $(date +%s) - $(stat -c %Y logs/queue/$n.log 2>/dev/null || date +%s) ))
  # a job that was (re)launched recently reuses an old log name: measure from its pidfile instead
  pf="$f.pid"; [ -f "$pf" ] && { pa=$(( $(date +%s) - $(stat -c %Y "$pf") )); [ $pa -lt $age ] && age=$pa; }
  if [ $age -gt 3900 ]; then
    # training jobs only write the queue log at unit boundaries; look at the run's own codec.log
    u=$(echo "$n" | sed -E 's/^0[0-9]+_(c1_final_(cap_r1|lamb025)|c2_nmulti_cap_r1|a1_(ego|vmme)_[a-z0-9]+|upilot_[a-z0-9]+)_//')
    active=""
    if [ "$u" != "$n" ]; then
      for cl in $R/gate1_vmme/vmme_long_motion/internvl/mid/*/*/$u/codec.log $R/u_vmme/vmme_long_motion/internvl/mid/*/*/$u/codec.log \
                $R/u_egos/egoschema/internvl/mid/*/*/$u/codec.log $R/exp_shared_adapter_u/pilot/vmme_long_motion/internvl/mid/*/*/$u/codec.log; do
        [ -f "$cl" ] && [ $(( $(date +%s) - $(stat -c %Y "$cl") )) -lt 1800 ] && { active=1; break; }
      done
    fi
    if [ -n "$active" ]; then
      echo "  . $n: queue log silent $((age/60)) min but codec.log active (training)"
    else
      echo "  ? $n: log silent for $((age/60)) min"
    fi
  fi
done
# key progress
echo "chain: steps=$(grep -c 'step ' logs/queue/010_adapter_u_chain.log 2>/dev/null)/96 | $(tail -1 logs/queue/010_adapter_u_chain.log 2>/dev/null | cut -c1-110)"
[ -f $R/exp_shared_adapter_u/universal_adapter_internvl_v1.pt ] && echo "ADAPTER READY: $R/exp_shared_adapter_u/universal_adapter_internvl_v1.pt"
for j in 030_ctrl_shuffle_vmme 031_ctrl_mismatch_vmme 032_ctrl_shuffle_egos 033_ctrl_mismatch_egos 034_ctrl_pixcache_vmme 035_ctrl_pixcache_egos; do
  if [ -f queue/done/$j.sh ]; then s=done; elif [ -f queue/failed/$j.sh ]; then s=FAILED; elif [ -f queue/running/$j.sh ]; then s="running $(tail -1 logs/queue/$j.log 2>/dev/null | grep -o '^\[[0-9]*/[0-9]*\]')"; else s=pending; fi; echo "ctrl $j: $s"; done
echo "C1/C2: done 060=$(ls queue/done | grep -c '^060_') 061=$(ls queue/done | grep -c '^061_') 062=$(ls queue/done | grep -c '^062_')  pilot 020 done=$(ls queue/done | grep -c '^020_') pending=$(ls queue/pending | grep -c '^020_')  A1 040/041 done=$(ls queue/done | grep -cE '^04[01]_')"
echo "fetch_ivl35: $(grep -E '^attempt|DONE|GAVE UP' logs/fetch_ivl35.log 2>/dev/null | tail -1 | cut -c1-60) | have $(du -sh /mnt/nas/xinyizheng/InternVL3_5-8B 2>/dev/null | cut -f1) | safetensors=$(ls /mnt/nas/xinyizheng/InternVL3_5-8B/model-*.safetensors 2>/dev/null | wc -l)/4"
echo "gpu: $(nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader,nounits | awk -F', ' '{printf "g%s:%dG/%s%% ", $1, $2/1024, $3}')"
echo "others: $(nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader,nounits | while IFS=', ' read p m; do u=$(ps -o user= -p $p 2>/dev/null); [ "$u" != xinyizheng ] && [ -n "$u" ] && echo -n "$u:$((m/1024))G "; done)"
# E-11 progress (main config n1224_dfilm): done-dir counts are stale because re-queued jobs overwrite same-named done files
R=/mnt/nas/xinyizheng/vidtok_out
echo "E-11 main-config rows: ego=$(grep -c "_n1224_dfilm," $R/u_egos/results.csv 2>/dev/null) vmme=$(grep -c "_n1224_dfilm," $R/u_vmme/results.csv 2>/dev/null)  runner DONE events=$(grep -c "\[DONE\]" logs/queue_runner.log)"
