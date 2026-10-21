#!/usr/bin/env python3
"""queue_runner.py -- opportunistic GPU job queue for a SHARED server (CVPR-27 cycle).

The moment a card has enough free memory, the highest-priority pending job is
launched on it. Jobs are plain bash files dropped into queue/pending/; each is
launched with GPU=<idx> and CUDA_VISIBLE_DEVICES=<idx> in its environment.

Layout (all under the repo root):
  queue/pending/<NNN>_<name>.sh   waiting, lexicographic order = priority
  queue/running/<...>.sh          launched (moved back to pending/ if the runner dies)
  queue/done/<...>.sh             exit code 0
  queue/failed/<...>.sh           non-zero exit (log kept)
  queue/status.tsv                name  card  start  end  rc
  logs/queue/<name>.log           job stdout+stderr
  logs/queue_runner.log           runner heartbeat / launches

Job header (optional, first 10 lines):
  #Q minmb=24000      free memory (MiB) the card must have      [default 24000]
  #Q share=1          how many runner jobs may share one card   [default 1]
  #Q cards=0 1 7      restrict this job to these cards           [default GPU_ALLOW]

Jobs receive GPU=<GPU-uuid> (not the index): a card that 'requires reset' drops out of
CUDA's enumeration and shifts every numeric index, while UUIDs stay stable. All units
pass $GPU straight into CUDA_VISIBLE_DEVICES, which accepts UUIDs. GPU_INDEX=<idx> is
also exported for logging.

Rules: only cards in GPU_ALLOW (default "0 1 4 5 6 7"; 2/3 are never ours);
a card in a bad state (memory unreadable) is skipped; a freshly launched job
reserves its minmb on that card for GRACE seconds so we do not double-book
before the model has actually been loaded.

Run:   setsid nohup python scripts/queue_runner.py > logs/queue_runner.nohup 2>&1 < /dev/null &
Stop:  touch STOP_QUEUE   (running jobs keep going; remove the file to resume)
"""
import datetime
import os
import re
import shutil
import subprocess
import sys
import time

REPO = os.environ.get("REPO", "/home/xinyizheng/vid_tokenizer")
os.chdir(REPO)
Q = os.path.join(REPO, "queue")
PEND, RUN, DONE, FAIL = (os.path.join(Q, d) for d in ("pending", "running", "done", "failed"))
LOGDIR = os.path.join(REPO, "logs", "queue")
for d in (PEND, RUN, DONE, FAIL, LOGDIR):
    os.makedirs(d, exist_ok=True)
STATUS = os.path.join(Q, "status.tsv")
RLOG = os.path.join(REPO, "logs", "queue_runner.log")
STOP = os.path.join(REPO, "STOP_QUEUE")
GPU_ALLOW = os.environ.get("GPU_ALLOW", "0 1 4 5 6 7").split()
POLL = int(os.environ.get("POLL", "15"))
HB_EVERY = int(os.environ.get("HB", "20"))          # heartbeat every HB polls (~5 min)
GRACE = int(os.environ.get("GRACE", "240"))         # seconds a launch reserves its minmb


def log(msg):
    t = datetime.datetime.now().strftime("%m-%d %H:%M:%S")
    line = f"[{t}] {msg}"
    print(line, flush=True)
    with open(RLOG, "a") as f:
        f.write(line + "\n")


UUID = {}   # nvidia-smi index -> GPU-uuid, refreshed by gpu_free()


def deny_cards():
    """Cards listed in queue/deny_cards.txt (space/newline separated) are never used.
    Re-read every poll so a card can be blacklisted/whitelisted without a restart."""
    try:
        return set(open(os.path.join(Q, "deny_cards.txt")).read().split())
    except FileNotFoundError:
        return set()


def gpu_free():
    """{card: free MiB} for HEALTHY cards only: memory, utilization and pstate must all be
    readable (a card that 'requires reset' reports [N/A]/ERR there) and the card must not
    be in queue/deny_cards.txt."""
    out = subprocess.run(
        ["nvidia-smi", "--query-gpu=index,memory.free,utilization.gpu,pstate,gpu_uuid",
         "--format=csv,noheader,nounits"], capture_output=True, text=True).stdout
    deny = deny_cards()
    free = {}
    for line in out.splitlines():
        parts = [x.strip() for x in line.split(",")]
        if len(parts) < 5:
            continue
        idx, mem, util, pstate, uuid = parts[:5]
        if idx in deny:
            continue
        try:
            free_mb = int(float(mem)); int(float(util))
        except ValueError:
            continue  # "[N/A]" -> card unusable
        if not pstate.startswith("P"):
            continue  # "ERR"/"[GPU requires reset]"
        free[idx] = free_mb
        UUID[idx] = uuid
    return free


def job_header(path):
    cfg = {"minmb": 24000, "share": 1, "cards": None}
    with open(path) as f:
        for _ in range(10):
            line = f.readline()
            if not line:
                break
            if not line.startswith("#Q"):
                continue
            for k, v in re.findall(r"(\w+)=([^#]+?)(?=\s+\w+=|\s*$)", line[2:].strip()):
                v = v.strip()
                if k == "minmb":
                    cfg["minmb"] = int(v)
                elif k == "share":
                    cfg["share"] = int(v)
                elif k == "cards":
                    cfg["cards"] = v.split()
    return cfg


def pending_jobs():
    return sorted(f for f in os.listdir(PEND) if f.endswith(".sh"))


def append_status(name, card, start, end, rc):
    new = not os.path.exists(STATUS)
    with open(STATUS, "a") as f:
        if new:
            f.write("name\tcard\tstart\tend\trc\n")
        f.write(f"{name}\t{card}\t{start}\t{end}\t{rc}\n")


def pid_alive(pid):
    try:
        os.kill(pid, 0)
        return os.path.exists(f"/proc/{pid}")
    except (ProcessLookupError, PermissionError):
        return False
    except OSError:
        return False


running = {}   # name -> dict(proc|pid, card, start, minmb, path)
# --- recover: a job left in running/ by a dead runner is ADOPTED if its process is still
# alive (pidfile queue/running/<name>.pid), otherwise it goes back to pending/. Relaunching
# a live job would collide on its run directory.
for f in sorted(os.listdir(RUN)):
    if not f.endswith(".sh"):
        continue
    pidf = os.path.join(RUN, f + ".pid")
    pid = card = None
    try:
        pid_s, card = open(pidf).read().split()
        pid = int(pid_s)
    except Exception:
        pass
    if pid and pid_alive(pid):
        running[f] = dict(proc=None, pid=pid, card=card or "?", t0=0, minmb=0,
                          path=os.path.join(RUN, f), start="adopted")
        log(f"adopted live job {f} (pid {pid}, card {card})")
    else:
        shutil.move(os.path.join(RUN, f), os.path.join(PEND, f))
        if os.path.exists(pidf):
            os.remove(pidf)
        log(f"recovered {f} -> pending (previous runner died, process gone)")
log(f"runner up: GPU_ALLOW={GPU_ALLOW} POLL={POLL}s GRACE={GRACE}s pending={len(pending_jobs())}")
it = 0
while True:
    it += 1
    now = time.time()
    # reap finished jobs
    for name in list(running):
        j = running[name]
        if j["proc"] is None:                      # adopted: poll the pid
            if pid_alive(j["pid"]):
                continue
            rc = 0  # exit code unknown; jobs are idempotent, results.csv tells the truth
        else:
            rc = j["proc"].poll()
            if rc is None:
                continue
        pidf = j["path"] + ".pid"
        if os.path.exists(pidf):
            os.remove(pidf)
        end = datetime.datetime.now().strftime("%m-%d %H:%M")
        dst = DONE if rc == 0 else FAIL
        shutil.move(j["path"], os.path.join(dst, name))
        append_status(name, j["card"], j["start"], end, rc)
        log(f"[{'DONE' if rc == 0 else 'FAIL rc=' + str(rc)}] {name} on card {j['card']}")
        del running[name]

    stopped = os.path.exists(STOP)
    if not stopped:
        free = gpu_free()
        # memory still reserved by young launches, and job count per card
        reserved, count = {}, {}
        for j in running.values():
            count[j["card"]] = count.get(j["card"], 0) + 1
            if now - j["t0"] < GRACE:
                reserved[j["card"]] = reserved.get(j["card"], 0) + j["minmb"]
        launched_cards = set()
        for name in pending_jobs():
            path = os.path.join(PEND, name)
            cfg = job_header(path)
            cards = [c for c in (cfg["cards"] or GPU_ALLOW) if c in free and c not in launched_cards]
            # most-free card first
            cards.sort(key=lambda c: -(free[c] - reserved.get(c, 0)))
            for c in cards:
                if count.get(c, 0) >= cfg["share"]:
                    continue
                if free[c] - reserved.get(c, 0) < cfg["minmb"]:
                    continue
                dst = os.path.join(RUN, name)
                shutil.move(path, dst)
                env = dict(os.environ, GPU=UUID[c], CUDA_VISIBLE_DEVICES=UUID[c],
                           CUDA_DEVICE_ORDER="PCI_BUS_ID", GPU_INDEX=c, QJOB=name)
                logf = open(os.path.join(LOGDIR, name.replace(".sh", ".log")), "a")
                proc = subprocess.Popen(["bash", dst], env=env, stdout=logf,
                                        stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                        start_new_session=True)
                with open(dst + ".pid", "w") as pf:
                    pf.write(f"{proc.pid} {c}\n")
                running[name] = dict(proc=proc, card=c, t0=now, minmb=cfg["minmb"], path=dst,
                                     start=datetime.datetime.now().strftime("%m-%d %H:%M"))
                count[c] = count.get(c, 0) + 1
                reserved[c] = reserved.get(c, 0) + cfg["minmb"]
                launched_cards.add(c)
                log(f"[LAUNCH] {name} -> card {c} ({free[c]} MiB free, need {cfg['minmb']}) pid {proc.pid}")
                break
    if it % HB_EVERY == 0:
        free = gpu_free()
        st = " ".join(f"g{c}:{free[c] // 1024}G" for c in sorted(free, key=int))
        who = ", ".join(f"{n}@{j['card']}" for n, j in running.items()) or "none"
        log(f"heartbeat{' (STOPPED)' if stopped else ''}: pending={len(pending_jobs())} "
            f"running=[{who}] free: {st}")
    time.sleep(POLL)
