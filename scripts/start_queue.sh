#!/usr/bin/env bash
# start_queue.sh -- start scripts/queue_runner.py exactly once (idempotent; pidfile queue/runner.pid).
# Safe to call from cron as a watchdog. Stop launching new jobs with `touch STOP_QUEUE`.
set -u
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 1
REPO="$(pwd)"; PIDF=queue/runner.pid
mkdir -p queue/pending queue/running queue/done queue/failed logs/queue
if [ -f "$PIDF" ] && kill -0 "$(cat "$PIDF")" 2>/dev/null; then
  echo "runner alive (pid $(cat "$PIDF"))"; exit 0
fi
REPO="$REPO" setsid nohup python3 scripts/queue_runner.py >> logs/queue_runner.nohup 2>&1 < /dev/null &
echo $! > "$PIDF"; echo "runner started (pid $!)"
