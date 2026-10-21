#!/usr/bin/env bash
# =============================================================================
#  control.sh  --  THE single file you edit to define an experiment.
#
#  Run it with:   bash scripts/run.sh            (clone-and-go, one command)
#  or directly:   bash scripts/launch/launch_local.sh
#
#  Read top-to-bottom: BLOCK 1 = set once per machine, BLOCK 2 = what you switch
#  between experiments, BLOCK 3 = defaults you rarely touch. Anything here can
#  also be overridden inline, e.g.:   DATASET=egoschema GPUS="0 1" bash scripts/run.sh
# =============================================================================


# =========================== BLOCK 1: MACHINE ================================
#  Edit these ONCE when you deploy to a new host. Everything else is relative.
export CONDA_ENV="${CONDA_ENV:-nvrc}"                       # conda env with torch/ffmpeg/pyarrow
export DATA_ROOT="${DATA_ROOT:-/mnt/nas/xinyizheng}"        # where datasets + model weights live
export INTERNVL_MODEL_PATH="${INTERNVL_MODEL_PATH:-$DATA_ROOT/InternVL2_5-8B}"  # VLM weights
export OUT_ROOT="${OUT_ROOT:-outputs/campaign}"            # where results/logs are written


# ========================= BLOCK 2: THE EXPERIMENT ==========================
#  These are the knobs that DISTINGUISH one experiment from another. The banner
#  at the bottom prints them so you always see "what am I about to run".

# ---- PROFILE presets: pick params by (video LENGTH x CONTENT type) ---------
#  Set PROFILE=<name> and it fills the encoding knobs below (NUM_FRAMES / SAMPLING
#  / EPOCHS / CAPACITIES). Any value you set inline still wins (precedence:
#  inline env > PROFILE > fallback default). Training is ONE-SHOT and its cost
#  AMORTIZES over reuse, so presets favor MORE epochs to minimize stored bitrate.
#
#  Tags: [CAL] = from pilot data; [TBD] = to be set by the calibration round
#  (the NUM_FRAMES frame-sweep on real long video -- see CALIBRATION note in BLOCK 3).
#  Once a combo is confirmed good, bump it from [TBD] to [CAL] here so it sticks.
export PROFILE="${PROFILE:-long_general}"
case "$PROFILE" in
  short)        # <=5 min, gist-level (EgoSchema). [CAL] short-video default.
     : "${NUM_FRAMES:=32}"  "${SAMPLING:=uniform}" "${EPOCHS:=30}"  "${CAPACITIES:=r1 g_mlo xs}" ;;
  long_general) # 10-60 min, mixed/static (LongVideoBench). [CAL: 128f = PARITY w/ HEVC@matched bpp AND oracle, n=25; r1 floor 0.115bpp]
     : "${NUM_FRAMES:=128}" "${SAMPLING:=uniform}" "${EPOCHS:=60}"  "${CAPACITIES:=r1 g_mlo xs}" ;;
  long_motion)  # 10-60 min, MOTION-RICH (HEVC weaker; ideal target). [TBD all]
     : "${NUM_FRAMES:=128}" "${SAMPLING:=uniform}" "${EPOCHS:=60}"  "${CAPACITIES:=g_mlo xs}" ;;
  xlong)        # hours-scale (HourVideo/MovieChat). [CAL: 256f drives r1 floor to 0.065bpp @ oracle acc, n=25; -0.04 vs HEVC@that bpp]
     : "${NUM_FRAMES:=256}" "${SAMPLING:=uniform}" "${EPOCHS:=100}" "${CAPACITIES:=r1 g_mlo}" ;;
  *) echo "[control] WARN: unknown PROFILE=$PROFILE (using fallbacks)" >&2 ;;
esac

# ---- DATASET --------------------------------------------------------------
# TRIED:  egoschema       -> gist-level MC, COMPRESSION-INSENSITIVE (HEVC ~oracle
#                            even at 0.04bpp) -> no room to win. ABANDONED.
#         mvbench_clevrer -> synthetic, ALSO easy to compress -> abandoned.
#         longvideobench  -> long (3-31min) visual QA, COMPRESSION-SENSITIVE
#                            (HEVC acc drops 0.61->0.44 as bitrate falls). << USE THIS.
export DATASET="${DATASET:-longvideobench}"    # -> configs/datasets/<DATASET>.yaml

# TRIED N_VIDEOS: 5 (cost calib) / 25 (probes) / 37-50 (paired accuracy). n>=25
#   needed for a readable trend (per-cell noise ~+/-0.08 at n=25-37).
export N_VIDEOS="${N_VIDEOS:-25}"

export RES="${RES:-256}"                       # TRIED only 256 (square). VLM tile is 448 internally.
export SAMPLING="${SAMPLING:-uniform}"         # TRIED: contiguous (first N) -> biased to clip start on
                                               #   long video; uniform (spread across whole clip) is
                                               #   the right one for long video. << USE uniform.
export NUM_FRAMES="${NUM_FRAMES:-32}"          # codec frame budget. TRIED 30 (egoschema) / 32 (LVB).
                                               #   NOTE eval/cost sweeps go 8..1024 (P2/P3c) separately.

export BACKBONES="${BACKBONES:-internvl}"      # TRIED only internvl (InternVL2.5-8B). eva_clip/clip/
                                               #   siglip = future cross-backbone (needs adapter shim).
export INTERFACES="${INTERFACES:-ours pixel oracle}"  # methods to compare (legend in BLOCK 3).
                                               #   TRIED: ours, final, pixel, oracle. 'final' (final-
                                               #   layer align) ~= ours, dropped to save compute.
# RATE axis = INR CAPACITY (the real rate lever; lambda saturates ~0.5bpp, see RATES below).
# TRIED capacities -> measured bpp (LVB, r1 is the floor):
#   g_xlo~0.33  g_lo~0.33  r1~0.29  g_mlo~0.65/0.68  xs~0.83/0.89  s/m/l ~1.0 (bigger INR, ~no lower bpp)
#   FINDING: bitrate set by base feature-grid LEVEL, not decoder width; floor ~0.29bpp.
export CAPACITIES="${CAPACITIES:-r1 g_mlo xs}" # 3 spread points: low/mid/high bitrate.
export GPUS="${GPUS:-4 5}"                      # round-robin, one job/card. Shared server: pick FREE
                                               #   cards (>=20GB free) or model-load OOMs.


# ============================ BLOCK 3: DEFAULTS =============================
#  Sensible defaults; touch only for ablations / fine control.
export DATASETS="${DATASETS:-$DATASET}"        # multi-dataset axis (usually just $DATASET)
export LAYERS="${LAYERS:-mid}"                 # alignment depth. TRIED: mid(layer 12) and final(24);
                                               #   mid is the method, final is a baseline.
# TRIED EPOCHS: 15 / 30 / 60 / 100. FINDING: accuracy is FLAT vs epochs (~0.61), but more
#   epochs LOWER bitrate at fixed accuracy (bpp 0.39->0.28->0.20->0.16) -- and raise one-shot
#   encode time (252->394->689->1092 s/video). 30 = quick-iteration sweet spot; PROFILES use
#   60-100 for DEPLOYMENT (one-shot cost amortizes over reuse -> buy lower bitrate).
export EPOCHS="${EPOCHS:-30}"
# ---- CALIBRATION ROUND (fills the [TBD] PROFILE values; do once per scope) ----
#  Goal: per video-LENGTH class, find the params (mainly NUM_FRAMES, then EPOCHS,
#  CAPACITIES) that minimize bitrate while keeping downstream accuracy ~on par with
#  HEVC. Training is one-shot/amortizable, so this calibration cost is paid once.
#  Protocol (run on a few real long videos of the target type):
#    1. NUM_FRAMES sweep {32,64,128,256} at fixed CAPACITIES -> bpp & acc vs frames
#       (the INR amortization curve; expect bpp down as frames up; watch acc).
#    2. at the best NUM_FRAMES, sweep EPOCHS {30,60,100} -> pick lowest bpp at flat acc.
#    3. confirm vs HEVC at matched bitrate; record the winning combo into the PROFILE
#       case above and flip its tag [TBD]->[CAL].
#  Keep a separate PROFILE per (length x content) so motion-rich vs static can differ.
export PIXEL_CRFS="${PIXEL_CRFS:-18 23 28 33 38}"   # HEVC quality points -> its own rate curve.
                                               #   TRIED 18..38; on LVB acc falls 0.61->0.44.
export RESULTS_CSV="${RESULTS_CSV:-$OUT_ROOT/results.csv}"
#  INTERFACES legend: ours = mid-layer pixel-free | final = final-layer baseline
#  | pixel = HEVC reconstruct-then-feed | oracle = raw video (ceiling).
#  ---- DEPRECATED rate lever: lambda (RATES) ----
#  TRIED RATES (lambda) vlo..vhi = 0.0625/0.25/1/4/16, plus xlo/xxlo down to 0.0039.
#  FINDING: 256x lambda change only moved bitrate 1.0->0.5bpp (SATURATES). Use CAPACITIES
#  (INR size) as the rate lever instead. RATES is only read when CAPACITIES is empty.
export RATES="${RATES:-vlo lo mid hi vhi}"
#  ---- eval-time TOKEN REDUCTION (not a launcher knob; in tools/token_reduction_*.py) ----
#  TRIED tokens/frame: 256(full) / 64 / 16 / 4. FINDING: 64 is LOSSLESS (acc = 256), 16/4 drop.
#  64 tok/frame -> ~3.7x lower per-query LLM cost, ~2x less memory, ~2x longer feasible video.


# ----------------------------- banner (don't edit) --------------------------
# Print once per run even though several scripts source this file.
if [[ -z "${_CONTROL_BANNER_SHOWN:-}" ]]; then
export _CONTROL_BANNER_SHOWN=1
cat >&2 <<BANNER
[control] ============ EXPERIMENT ============
[control]  dataset   : $DATASET   (n=$N_VIDEOS, res=$RES, sampling=$SAMPLING, frames=$NUM_FRAMES)
[control]  backbone  : $BACKBONES   model=$INTERNVL_MODEL_PATH
[control]  methods   : $INTERFACES
[control]  rate axis : capacities=[$CAPACITIES]  (or lambda RATES if empty)  crfs=[$PIXEL_CRFS]
[control]  compute   : GPUS=[$GPUS]  epochs=$EPOCHS  env=$CONDA_ENV
[control]  output    : $OUT_ROOT  (csv: $RESULTS_CSV)
[control] ====================================
BANNER
fi
