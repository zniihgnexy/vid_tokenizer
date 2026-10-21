#!/usr/bin/env bash
# requeue_failed.sh -- move failed queue jobs back to pending, at most MAXRETRY times each
# (count kept in queue/retries.txt). Jobs are idempotent (train skips finished codecs), so a
# transient failure (OOM when two evals collide, NAS hiccup) just needs another go. A job that
# failed MAXRETRY+1 times stays in failed/ and is listed for a human decision.
cd /home/xinyizheng/vid_tokenizer || exit 1
MAXRETRY="${MAXRETRY:-2}"; touch queue/retries.txt
for f in queue/failed/*.sh; do
  [ -f "$f" ] || continue
  n=$(basename "$f")
  c=$(grep -c "^$n$" queue/retries.txt)
  if [ "$c" -lt "$MAXRETRY" ]; then
    echo "$n" >> queue/retries.txt
    { echo; echo "===== requeued $(date '+%m-%d %H:%M') (retry $((c+1))/$MAXRETRY) ====="; } >> "logs/queue/${n%.sh}.log"
    mv "$f" queue/pending/ && echo "requeued $n (retry $((c+1))/$MAXRETRY)"
  else
    echo "GIVE-UP $n (failed $((c+1)) times) :: $(grep -m1 -E 'Traceback|Error|OOM|FATAL' logs/queue/${n%.sh}.log | cut -c1-120)"
  fi
done
