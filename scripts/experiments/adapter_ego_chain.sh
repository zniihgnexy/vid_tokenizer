#!/usr/bin/env bash
# adapter_ego_chain.sh -- DIAGNOSTIC (2026-10-03): a per-DATASET receiver-side adapter for
# EgoSchema. The universal (VMME+Ego donor) adapter costs EgoSchema -0.08 accuracy at cap_r1
# (phase 0, 97 paired videos); this asks whether an adapter fitted only on the 16 EgoSchema donor
# clips (outside common-100) recovers it. Same round-robin recipe as the universal chain.
# Ends by queueing Ego common-100 x cap_r1 under the frozen Ego adapter (jobs 040z_*, i.e. after
# the A1 Ego rungs and before the A1 VMME rungs). Output root: R/ue_egos.
set -uo pipefail
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
export PYTHONPATH=src PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
       HF_HOME=/mnt/nas/xinyizheng/.hfcache TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 \
       INTERNVL_MODEL_PATH=/mnt/nas/xinyizheng/InternVL2_5-8B
R=/mnt/nas/xinyizheng/vidtok_out
U=$R/exp_shared_adapter_ego
GPU="${GPU:?GPU must be set (queue_runner sets it)}"
export NUM_FRAMES=128 SAMPLING=uniform RES=256
export DATASET=egoschema DATASET_CONFIG=configs/datasets/egoschema.yaml DATASET_MANIFEST_DIR=outputs/datasets/egoschema
mkdir -p "$U" logs
LOG(){ echo "[ego-chain $(date '+%m-%d %H:%M')] $*"; }
EGO_DONORS=(3f61b913-9920-4fbd-ba0f-93f41c255279 402503fc-6f1b-4865-aea2-98f82349f1a4 4070a4e2-14d5-4618-9889-dd18a416e2b5
            40c8c634-c4a1-4a00-a480-0aa652e7246e 410a6007-f759-4f9a-8196-0dad61934929 41e8027c-6c31-4e95-86b1-109eb4b9a470
            425f2fb4-a2a7-4925-94b5-25f6b0b85f78 429e2791-b050-4184-9837-de7c201f94c8 455ec904-69ad-4f53-829b-c1eb2ffab59a
            4561a47c-7756-4e36-ab43-80d11230b2ae 456447c2-98ca-4285-94dc-d2f0d1b398f6 45e313dd-9b30-444e-9577-b15a21cb59b4
            45fd8bca-c836-4601-b2c8-cc2a08cf8f86 46853bef-9052-428d-8e61-df684147f4af 46e1aee1-adea-4c9c-ac5b-9d933a3d3a43
            470dad8b-6c95-440c-b990-5b123ec64497)
ROUND_LR=(1e-3 5e-4 2.5e-4); EPOCHS=10
find_adpt(){ find "$1" -name codec_adapter.pt 2>/dev/null | head -1; }
A=""; step=0
for r in 1 2 3; do
  LR="${ROUND_LR[$((r-1))]}"
  export OUT_ROOT="$U/round$r" RESULTS_CSV="$U/round$r/results.csv"
  mkdir -p "$OUT_ROOT/_videos"; [ -e "$OUT_ROOT/_videos/egoschema" ] || ln -s "$R/gate1_egos/_videos/egoschema" "$OUT_ROOT/_videos/egoschema"
  for u in "${EGO_DONORS[@]}"; do
    step=$((step+1)); RUNDIR="$OUT_ROOT/egoschema/internvl/mid/ours/cap_r1/$u"
    NEXT="$(find_adpt "$RUNDIR")"
    if [[ -z "$NEXT" ]]; then
      LOG "step $step r$r $u: train (lr=$LR, init=${A:-fresh})"
      [[ -d "$RUNDIR" ]] && { mkdir -p "$U/_stale"; mv "$RUNDIR" "$U/_stale/r${r}_${u}_$(date +%s)"; }
      if [[ -n "$A" ]]; then NVRC_INIT_ADAPTER="$A" NVRC_ADAPTER_LR="$LR" bash scripts/units/train_codec.sh --uuid "$u" --rate cap --capacity r1 --backbone internvl --layer mid --interface ours --gpu "$GPU" --epochs "$EPOCHS" > "logs/egochain_r${r}_${u}.log" 2>&1
      else NVRC_ADAPTER_LR="$LR" bash scripts/units/train_codec.sh --uuid "$u" --rate cap --capacity r1 --backbone internvl --layer mid --interface ours --gpu "$GPU" --epochs "$EPOCHS" > "logs/egochain_r${r}_${u}.log" 2>&1; fi
      NEXT="$(find_adpt "$RUNDIR")"
    else LOG "step $step r$r $u: adapter exists, reuse"; fi
    [[ -n "$NEXT" ]] || { LOG "FATAL step $step produced no adapter"; exit 1; }
    A="$NEXT"
  done
  cp "$A" "$U/adapter_after_round$r.pt"; LOG "round $r done"
done
cp "$A" "$U/ego_adapter_internvl_v1.pt"
LOG "EGO ADAPTER READY: $U/ego_adapter_internvl_v1.pt"
# queue Ego common-100 x cap_r1 under the frozen Ego-only adapter
n=0
for u in $(grep -v '^$' outputs/gate1_egos/common100_uuids.txt); do
  cat > "queue/pending/040z_a1e_ego_cap_r1_${u}.sh" <<EOF
#Q minmb=24000 share=2
set -uo pipefail
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
export PYTHONPATH=src PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True HF_HOME=/mnt/nas/xinyizheng/.hfcache TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 INTERNVL_MODEL_PATH=/mnt/nas/xinyizheng/InternVL2_5-8B
export NUM_FRAMES=128 SAMPLING=uniform RES=256
export DATASET=egoschema DATASET_CONFIG=configs/datasets/egoschema.yaml DATASET_MANIFEST_DIR=outputs/datasets/egoschema OUT_ROOT=$R/ue_egos RESULTS_CSV=$R/ue_egos/results.csv
mkdir -p \$OUT_ROOT/_videos; [ -e \$OUT_ROOT/_videos/egoschema ] || ln -s $R/gate1_egos/_videos/egoschema \$OUT_ROOT/_videos/egoschema
export NVRC_FROZEN_ADAPTER=$U/ego_adapter_internvl_v1.pt
bash scripts/units/train_codec.sh --uuid $u --rate cap --capacity r1 --backbone internvl --layer mid --interface ours --gpu \$GPU --epochs 30
bash scripts/units/eval_downstream.sh --uuid $u --rate cap --capacity r1 --backbone internvl --layer mid --interface ours --gpu \$GPU
EOF
  n=$((n+1))
done
LOG "queued $n Ego-adapter jobs (040z_a1e_ego_cap_r1_*)"
