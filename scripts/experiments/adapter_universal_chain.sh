#!/usr/bin/env bash
# adapter_universal_chain.sh -- train the UNIVERSAL (receiver-side) adapter for InternVL.
#
# CVPR-27 main configuration (approved 2026-10-01): one adapter per backbone, fitted
# once on donor videos that are DISJOINT from every evaluation pool, then frozen;
# all per-video codecs are trained against the frozen adapter and only codec bits
# are counted. This script produces that adapter and then queues the G1 pilot.
#
# Donors: 16 Video-MME "Life Record" videos (outside the motion pool) + 16 EgoSchema
# clips outside common-100. Multi-pass round-robin instead of a single chain:
#   round 1  lr 1e-3   10 epochs/video   round 2  lr 5e-4   round 3  lr 2.5e-4
# Each step warm-starts the adapter from the previous step (NVRC_INIT_ADAPTER);
# codecs are throwaway. Idempotent: a step whose adapter already exists is reused.
#
# Runs as ONE queue job (sequential by nature). GPU comes from $GPU (queue_runner).
#   queue job:  bash scripts/experiments/adapter_universal_chain.sh
set -uo pipefail
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
export PYTHONPATH=src PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
       HF_HOME=/mnt/nas/xinyizheng/.hfcache TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 \
       INTERNVL_MODEL_PATH=/mnt/nas/xinyizheng/InternVL2_5-8B
R=/mnt/nas/xinyizheng/vidtok_out
U=$R/exp_shared_adapter_u
GPU="${GPU:?GPU must be set (queue_runner sets it)}"
export NUM_FRAMES=128 SAMPLING=uniform RES=256
mkdir -p "$U" logs
LOG(){ echo "[u-chain $(date '+%m-%d %H:%M')] $*"; }

VMME_DONORS=(0eJvnKwGThw 0kRsiSdDFYg 1evyOuQz-jM 25Pt1AZO9EM 2LDriAWltwM 3HEYqZgC4ko 3MJNKd10kxM 4IenX7OHumk
             5WIdIs3A9Ok 5i5Be73ESUc 6Pt3-NDxzRk 9aGgBzToUz4 CKYw_RG7i7w EP2rD6lr2Xk EhLOdDfaC7Y Fibq4aA-GVc)
EGO_DONORS=(3f61b913-9920-4fbd-ba0f-93f41c255279 402503fc-6f1b-4865-aea2-98f82349f1a4 4070a4e2-14d5-4618-9889-dd18a416e2b5
            40c8c634-c4a1-4a00-a480-0aa652e7246e 410a6007-f759-4f9a-8196-0dad61934929 41e8027c-6c31-4e95-86b1-109eb4b9a470
            425f2fb4-a2a7-4925-94b5-25f6b0b85f78 429e2791-b050-4184-9837-de7c201f94c8 455ec904-69ad-4f53-829b-c1eb2ffab59a
            4561a47c-7756-4e36-ab43-80d11230b2ae 456447c2-98ca-4285-94dc-d2f0d1b398f6 45e313dd-9b30-444e-9577-b15a21cb59b4
            45fd8bca-c836-4601-b2c8-cc2a08cf8f86 46853bef-9052-428d-8e61-df684147f4af 46e1aee1-adea-4c9c-ac5b-9d933a3d3a43
            470dad8b-6c95-440c-b990-5b123ec64497)
# interleave the two domains so no round ends on a single-domain streak
ORDER=(); for i in "${!VMME_DONORS[@]}"; do ORDER+=("vmme:${VMME_DONORS[$i]}" "ego:${EGO_DONORS[$i]}"); done
ROUND_LR=(1e-3 5e-4 2.5e-4); EPOCHS=10

set_ds(){  # set_ds vmme|ego OUT_ROOT
  case "$1" in
    vmme) export DATASET=vmme_long_motion DATASET_CONFIG=configs/datasets/vmme_long_motion.yaml \
                 DATASET_MANIFEST_DIR=outputs/datasets/vmme_long_motion;;
    ego)  export DATASET=egoschema DATASET_CONFIG=configs/datasets/egoschema.yaml \
                 DATASET_MANIFEST_DIR=outputs/datasets/egoschema;;
  esac
  export OUT_ROOT="$2" RESULTS_CSV="$2/results.csv"
  # reuse the existing frame caches instead of re-extracting into the new OUT_ROOT
  mkdir -p "$OUT_ROOT/_videos"
  [ -e "$OUT_ROOT/_videos/vmme_long_motion" ] || ln -s "$R/gate1_vmme/_videos/vmme_long_motion" "$OUT_ROOT/_videos/vmme_long_motion"
  [ -e "$OUT_ROOT/_videos/egoschema" ]        || ln -s "$R/gate1_egos/_videos/egoschema"        "$OUT_ROOT/_videos/egoschema"
}
find_adpt(){ find "$1" -name codec_adapter.pt 2>/dev/null | head -1; }

A=""   # current adapter path ("" = fresh init for the very first step)
step=0
for r in 1 2 3; do
  LR="${ROUND_LR[$((r-1))]}"
  for item in "${ORDER[@]}"; do
    ds="${item%%:*}"; u="${item#*:}"; step=$((step+1))
    set_ds "$ds" "$U/round$r"
    RUNDIR="$OUT_ROOT/$DATASET/internvl/mid/ours/cap_r1/$u"
    NEXT="$(find_adpt "$RUNDIR")"
    if [[ -n "$NEXT" ]]; then
      LOG "step $step r$r $ds $u: adapter exists, reuse"
    else
      LOG "step $step r$r $ds $u: train (lr=$LR, init=${A:-fresh}) on gpu$GPU"
      # a stale, adapter-less run dir would make train_codec skip or NVRC refuse to create the dir
      [[ -d "$RUNDIR" ]] && { mkdir -p "$U/_stale"; mv "$RUNDIR" "$U/_stale/r${r}_${u}_$(date +%s)"; }
      if [[ -n "$A" ]]; then
        NVRC_INIT_ADAPTER="$A" NVRC_ADAPTER_LR="$LR" bash scripts/units/train_codec.sh --uuid "$u" \
            --rate cap --capacity r1 --backbone internvl --layer mid --interface ours \
            --gpu "$GPU" --epochs "$EPOCHS" > "logs/uchain_r${r}_${u}.log" 2>&1
        grep -q "WARM-START adapter" "$RUNDIR"/codec.log 2>/dev/null || LOG "WARN warm-start line not found in codec.log for $u"
      else
        NVRC_ADAPTER_LR="$LR" bash scripts/units/train_codec.sh --uuid "$u" \
            --rate cap --capacity r1 --backbone internvl --layer mid --interface ours \
            --gpu "$GPU" --epochs "$EPOCHS" > "logs/uchain_r${r}_${u}.log" 2>&1
      fi
      NEXT="$(find_adpt "$RUNDIR")"
    fi
    [[ -n "$NEXT" ]] || { LOG "FATAL step $step produced no adapter (see logs/uchain_r${r}_${u}.log)"; exit 1; }
    A="$NEXT"
  done
  cp "$A" "$U/adapter_after_round$r.pt"
  LOG "round $r done -> $U/adapter_after_round$r.pt"
done
cp "$A" "$U/universal_adapter_internvl_v1.pt"
python3 - "$U" "${ORDER[@]}" <<'PY'
import json, sys, datetime
U=sys.argv[1]; order=sys.argv[2:]
json.dump({"adapter":"universal_adapter_internvl_v1.pt","backbone":"InternVL2_5-8B","align_layer":12,
           "donors":order,"rounds":3,"epochs_per_step":10,"adapter_lr":[1e-3,5e-4,2.5e-4],
           "capacity":"r1","frames":128,"res":256,"created":datetime.datetime.now().isoformat()},
          open(f"{U}/universal_adapter_internvl_v1.json","w"), indent=1)
PY
LOG "UNIVERSAL ADAPTER READY: $U/universal_adapter_internvl_v1.pt"

# ---- queue the G1 pilot: same 20 paired targets as pilots R1/R2, two rungs, frozen adapter
TARGETS="$(python3 - <<'PY'
import csv, json, collections
MOTION={'Sports Competition','Artistic Performance','Film & Television'}
u2d={json.loads(l)['video_idx']: json.loads(l).get('domain') for l in open('outputs/datasets/vmme_long_motion/questions.jsonl')}
rows=csv.DictReader(open('/mnt/nas/xinyizheng/vidtok_out/gate1_vmme/stratified_n179.csv'))
cnt=collections.Counter(r['uuid'] for r in rows if r['interface']=='ours' and r['rate']=='cap_r1'
                        and r['bucket']=='temporal' and u2d.get(r['uuid']) in MOTION)
print(' '.join(u for u,_ in cnt.most_common(20)))
PY
)"
echo "$TARGETS" | tr ' ' '\n' > "$U/pilot_targets.txt"
mkdir -p queue/pending
n=0
for u in $TARGETS; do for rung in lamb025 cap_r1; do
  if [[ "$rung" == cap_r1 ]]; then LV=""; else LV="--loss-variant $rung"; fi
  cat > "queue/pending/020_upilot_${rung}_${u}.sh" <<EOF
#Q minmb=24000 share=1
# G1 pilot: frozen universal adapter, target $u, rung $rung (generated by adapter_universal_chain.sh)
set -uo pipefail
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
export PYTHONPATH=src PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True HF_HOME=/mnt/nas/xinyizheng/.hfcache TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 INTERNVL_MODEL_PATH=/mnt/nas/xinyizheng/InternVL2_5-8B
export DATASET=vmme_long_motion DATASET_CONFIG=configs/datasets/vmme_long_motion.yaml DATASET_MANIFEST_DIR=outputs/datasets/vmme_long_motion
export OUT_ROOT=$U/pilot RESULTS_CSV=$U/pilot/results.csv NUM_FRAMES=128 SAMPLING=uniform RES=256
mkdir -p \$OUT_ROOT/_videos; [ -e \$OUT_ROOT/_videos/vmme_long_motion ] || ln -s $R/gate1_vmme/_videos/vmme_long_motion \$OUT_ROOT/_videos/vmme_long_motion
export NVRC_FROZEN_ADAPTER=$U/universal_adapter_internvl_v1.pt
bash scripts/units/train_codec.sh --uuid $u --rate cap --capacity r1 $LV --backbone internvl --layer mid --interface ours --gpu \$GPU --epochs 30
bash scripts/units/eval_downstream.sh --uuid $u --rate cap --capacity r1 $LV --backbone internvl --layer mid --interface ours --gpu \$GPU
EOF
  n=$((n+1))
done; done
LOG "queued $n pilot jobs (020_upilot_*) -> queue/pending"

# watcher (outside the queue so it never holds a card): when all pilot outputs exist, queue the harvest
setsid nohup bash -c "
cd /home/xinyizheng/vid_tokenizer
for i in \$(seq 1 576); do
  done_n=\$(ls queue/done/020_upilot_*.sh queue/failed/020_upilot_*.sh 2>/dev/null | wc -l)
  [ \"\$done_n\" -ge $n ] && break; sleep 300
done
cat > queue/pending/029_upilot_harvest.sh <<'EOH'
#Q minmb=24000 share=1
set -uo pipefail
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
export PYTHONPATH=src HF_HOME=/mnt/nas/xinyizheng/.hfcache TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 INTERNVL_MODEL_PATH=/mnt/nas/xinyizheng/InternVL2_5-8B
U=/mnt/nas/xinyizheng/vidtok_out/exp_shared_adapter_u
python tools/harvest_stratified.py --dataset vmme_long_motion --out-root \$U/pilot \
  --manifest-dir outputs/datasets/vmme_long_motion --manifest-file questions.jsonl \
  --interface ours --rates cap_r1 cap_r1_lamb025 --no-oracle --crfs __none__ \
  --out \$U/pilot/stratified_upilot.csv
EOH
echo \"[u-watch] harvest job queued \$(date)\"
" > logs/upilot_watch.log 2>&1 < /dev/null &
LOG "pilot watcher started (logs/upilot_watch.log). Chain job finished."
