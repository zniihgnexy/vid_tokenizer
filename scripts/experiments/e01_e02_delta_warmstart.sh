#!/usr/bin/env bash
# e01_e02_delta_warmstart.sh <smoke|e01|e02> -- MASTER_PLAN E-01 (per-video adapter delta) and E-02
# (warm-start) pilots as queue jobs. Pilot pools: 20 VMME pilot targets (same as G1) and the
# first 20 EgoSchema common-100 videos. Outputs: R/exp_delta (E-01), R/exp_warm (E-02).
#   smoke : 1 video x {dfilm, dlora8, ws10} x 1 epoch into R/_smoke   (validate code paths)
#   e01   : VMME 20 x {lamb025,cap_r1} x {dfilm,dlora8,dlora32}            = 120 jobs
#           Ego  20 x {lamb025,cap_r1} x {dfilm,dlora8,dlora32,v5film}      = 160 jobs
#   e02   : VMME 20 x {lamb025,cap_r1} x {ws10,ws15}                        =  80 jobs
cd /home/xinyizheng/vid_tokenizer || exit 1
R=/mnt/nas/xinyizheng/vidtok_out
UBASE=$R/exp_shared_adapter_u/universal_adapter_internvl_v1.pt
EBASE=$R/exp_shared_adapter_ego/ego_adapter_internvl_v1.pt
DONOR=$(ls -d $R/exp_shared_adapter_u/round3/vmme_long_motion/internvl/mid/ours/cap_r1/Fibq4aA-GVc/*_chunk00 | head -1)
SET="${1:?smoke|e01|e02}"
VMME=$(cat $R/exp_shared_adapter_u/pilot_targets.txt | tr '\n' ' ')
EGO=$(head -20 outputs/gate1_egos/common100_uuids.txt | tr '\n' ' ')
ENV='set -uo pipefail
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
export PYTHONPATH=src PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True HF_HOME=/mnt/nas/xinyizheng/.hfcache TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 INTERNVL_MODEL_PATH=/mnt/nas/xinyizheng/InternVL2_5-8B
export NUM_FRAMES=128 SAMPLING=uniform RES=256'
dsenv(){ case "$1" in
  vmme) echo "export DATASET=vmme_long_motion DATASET_CONFIG=configs/datasets/vmme_long_motion.yaml DATASET_MANIFEST_DIR=outputs/datasets/vmme_long_motion OUT_ROOT=$2 RESULTS_CSV=$2/results.csv"
        echo "mkdir -p \$OUT_ROOT/_videos; [ -e \$OUT_ROOT/_videos/vmme_long_motion ] || ln -s $R/gate1_vmme/_videos/vmme_long_motion \$OUT_ROOT/_videos/vmme_long_motion";;
  ego)  echo "export DATASET=egoschema DATASET_CONFIG=configs/datasets/egoschema.yaml DATASET_MANIFEST_DIR=outputs/datasets/egoschema OUT_ROOT=$2 RESULTS_CSV=$2/results.csv"
        echo "mkdir -p \$OUT_ROOT/_videos; [ -e \$OUT_ROOT/_videos/egoschema ] || ln -s $R/gate1_egos/_videos/egoschema \$OUT_ROOT/_videos/egoschema";;
esac; }
lv(){ [ "$1" = cap_r1 ] && echo "" || echo "--loss-variant $1"; }
# variant -> env lines
venv(){ case "$1" in
  dfilm)  echo "export NVRC_FROZEN_ADAPTER=$UBASE NVRC_ADAPTER_DELTA=film RATE_SUFFIX=_dfilm";;
  dlora8) echo "export NVRC_FROZEN_ADAPTER=$UBASE NVRC_ADAPTER_DELTA=lora8 RATE_SUFFIX=_dlora8";;
  dlora32) echo "export NVRC_FROZEN_ADAPTER=$UBASE NVRC_ADAPTER_DELTA=lora32 RATE_SUFFIX=_dlora32";;
  v5film) echo "export NVRC_FROZEN_ADAPTER=$EBASE NVRC_ADAPTER_DELTA=film RATE_SUFFIX=_v5film";;
  ws10)   echo "export NVRC_INIT_CODEC=$DONOR RATE_SUFFIX=_ws10";;
  ws15)   echo "export NVRC_INIT_CODEC=$DONOR RATE_SUFFIX=_ws15";;
esac; }
epochs(){ case "$1" in ws10) echo 10;; ws15) echo 15;; *) echo 30;; esac; }
mk(){ # mk <jobname> <ds> <out_root> <uuid> <rung> <variant> [epochs]
  local name=$1 ds=$2 root=$3 u=$4 rung=$5 var=$6 ep=${7:-$(epochs $6)}
  { echo "#Q minmb=24000 share=2"; echo "$ENV"; dsenv $ds $root; venv $var
    echo "bash scripts/units/train_codec.sh --uuid $u --rate cap --capacity r1 $(lv $rung) --backbone internvl --layer mid --interface ours --gpu \$GPU --epochs $ep"
    echo "bash scripts/units/eval_downstream.sh --uuid $u --rate cap --capacity r1 $(lv $rung) --backbone internvl --layer mid --interface ours --gpu \$GPU"
  } > "queue/pending/$name.sh"
}
[ -f "$UBASE" ] || { echo "missing $UBASE"; exit 1; }
[ -n "$DONOR" ] || { echo "missing donor run dir"; exit 1; }
case "$SET" in
  smoke)
    u=$(echo $VMME | cut -d' ' -f1); mkdir -p $R/_smoke
    mk 012_smoke_dfilm  vmme $R/_smoke $u cap_r1 dfilm 1
    mk 012_smoke_dlora8 vmme $R/_smoke $u cap_r1 dlora8 1
    mk 012_smoke_ws10   vmme $R/_smoke $u cap_r1 ws10 1
    echo "queued 3 smoke jobs";;
  e01)
    n=0
    for u in $VMME; do for rung in lamb025 cap_r1; do for v in dfilm dlora8 dlora32; do mk 030_e01_vmme_${v}_${rung}_$u vmme $R/exp_delta $u $rung $v; n=$((n+1)); done; done; done
    [ -f "$EBASE" ] || echo "WARN: ego base adapter missing, v5film jobs will fail until $EBASE exists"
    for u in $EGO; do for rung in lamb025 cap_r1; do for v in dfilm dlora8 dlora32 v5film; do mk 031_e01_ego_${v}_${rung}_$u ego $R/exp_delta $u $rung $v; n=$((n+1)); done; done; done
    echo "queued $n E-01 jobs";;
  e02)
    n=0
    for u in $VMME; do for rung in lamb025 cap_r1; do for v in ws10 ws15; do mk 032_e02_vmme_${v}_${rung}_$u vmme $R/exp_warm $u $rung $v; n=$((n+1)); done; done; done
    echo "queued $n E-02 jobs";;
esac

# ---- E-01b (added 2026-10-04 after the FiLM diagnostic): frozen base + FiLM delta, but the codec is
# aligned at layers 12 AND 24 jointly, so it also compensates downstream drift that the frozen adapter
# leaves behind (layer-12 cosine was already >= per-video, yet accuracy dropped).
if [ "$SET" = e01b ]; then
  n=0
  for u in $VMME; do
    name=030_e01b_vmme_dfilm_n1224_cap_r1_$u
    { echo "#Q minmb=24000 share=2"; echo "$ENV"; dsenv vmme $R/exp_delta; venv dfilm
      echo "bash scripts/units/train_codec.sh --uuid $u --rate cap --capacity r1 --teacher-layer 1224 --backbone internvl --layer mid --interface ours --gpu \$GPU --epochs 30"
      echo "bash scripts/units/eval_downstream.sh --uuid $u --rate cap --capacity r1 --loss-variant n1224 --backbone internvl --layer mid --interface ours --gpu \$GPU"
    } > "queue/pending/$name.sh"; n=$((n+1))
  done
  echo "queued $n E-01b jobs"
fi
if [ "$SET" = smoke_e01b ]; then
  u=$(echo $VMME | cut -d' ' -f1)
  { echo "#Q minmb=24000 share=2"; echo "$ENV"; dsenv vmme $R/_smoke; venv dfilm
    echo "bash scripts/units/train_codec.sh --uuid $u --rate cap --capacity r1 --teacher-layer 1224 --backbone internvl --layer mid --interface ours --gpu \$GPU --epochs 1"
    echo "bash scripts/units/eval_downstream.sh --uuid $u --rate cap --capacity r1 --loss-variant n1224 --backbone internvl --layer mid --interface ours --gpu \$GPU"
  } > queue/pending/013_smoke_dfilm_n1224.sh; echo "queued 013_smoke_dfilm_n1224"
fi

# ---- E-01b on EgoSchema (the decisive pool) + E-01c control (dual-layer, frozen base, NO delta)
if [ "$SET" = e01b_ego ]; then
  n=0
  for u in $EGO; do
    name=029x_e01b_ego_dfilm_n1224_cap_r1_$u
    { echo "#Q minmb=24000 share=2"; echo "$ENV"; dsenv ego $R/exp_delta; venv dfilm
      echo "bash scripts/units/train_codec.sh --uuid $u --rate cap --capacity r1 --teacher-layer 1224 --backbone internvl --layer mid --interface ours --gpu \$GPU --epochs 30"
      echo "bash scripts/units/eval_downstream.sh --uuid $u --rate cap --capacity r1 --loss-variant n1224 --backbone internvl --layer mid --interface ours --gpu \$GPU"
    } > "queue/pending/$name.sh"; n=$((n+1))
  done
  echo "queued $n E-01b Ego jobs"
fi
if [ "$SET" = e01c ]; then
  n=0
  for u in $VMME; do
    name=029y_e01c_vmme_frozen_n1224_cap_r1_$u
    { echo "#Q minmb=24000 share=2"; echo "$ENV"; dsenv vmme $R/exp_delta; echo "export NVRC_FROZEN_ADAPTER=$UBASE RATE_SUFFIX=_frozen"
      echo "bash scripts/units/train_codec.sh --uuid $u --rate cap --capacity r1 --teacher-layer 1224 --backbone internvl --layer mid --interface ours --gpu \$GPU --epochs 30"
      echo "bash scripts/units/eval_downstream.sh --uuid $u --rate cap --capacity r1 --loss-variant n1224 --backbone internvl --layer mid --interface ours --gpu \$GPU"
    } > "queue/pending/$name.sh"; n=$((n+1))
  done
  echo "queued $n E-01c jobs"
fi

# ---- E-02b (2026-10-04): warm-start under the MAIN configuration (frozen base + FiLM + 12/24 alignment)
if [ "$SET" = e02b ]; then
  n=0
  for u in $VMME; do for rung in lamb025 cap_r1; do
    name=035_e02b_vmme_main_ws10_${rung}_$u
    if [ "$rung" = cap_r1 ]; then LVT=""; LVE="--loss-variant n1224"; else LVT="--loss-variant $rung"; LVE="--loss-variant ${rung}_n1224"; fi
    { echo "#Q minmb=24000 share=2"; echo "$ENV"; dsenv vmme $R/exp_warm
      echo "export NVRC_FROZEN_ADAPTER=$UBASE NVRC_ADAPTER_DELTA=film NVRC_INIT_CODEC=$DONOR RATE_SUFFIX=_dfilm_ws10"
      echo "bash scripts/units/train_codec.sh --uuid $u --rate cap --capacity r1 $LVT --teacher-layer 1224 --backbone internvl --layer mid --interface ours --gpu \$GPU --epochs 10"
      echo "bash scripts/units/eval_downstream.sh --uuid $u --rate cap --capacity r1 $LVE --backbone internvl --layer mid --interface ours --gpu \$GPU"
    } > "queue/pending/$name.sh"; n=$((n+1))
  done; done
  echo "queued $n E-02b jobs"
fi

# ---- E-02c (2026-10-04): warm-start under the main config, but from a MAIN-CONFIG donor
# (an E-01b run), because the per-video-adapter donor transfers badly (E-02b: bpp x1.15, acc down).
if [ "$SET" = e02c ]; then
  DONOR_M=$(ls -d $R/exp_delta/vmme_long_motion/internvl/mid/ours/cap_r1_n1224_dfilm/$(echo $VMME | cut -d' ' -f1)/*_chunk00 | head -1)
  [ -n "$DONOR_M" ] || { echo "no main-config donor run"; exit 1; }
  n=0
  for u in $VMME; do
    [ "$u" = "$(echo $VMME | cut -d' ' -f1)" ] && continue   # donor itself excluded
    name=035_e02c_vmme_main_ws10m_cap_r1_$u
    { echo "#Q minmb=24000 share=2"; echo "$ENV"; dsenv vmme $R/exp_warm
      echo "export NVRC_FROZEN_ADAPTER=$UBASE NVRC_ADAPTER_DELTA=film NVRC_INIT_CODEC=$DONOR_M RATE_SUFFIX=_dfilm_ws10m"
      echo "bash scripts/units/train_codec.sh --uuid $u --rate cap --capacity r1 --teacher-layer 1224 --backbone internvl --layer mid --interface ours --gpu \$GPU --epochs 10"
      echo "bash scripts/units/eval_downstream.sh --uuid $u --rate cap --capacity r1 --loss-variant n1224 --backbone internvl --layer mid --interface ours --gpu \$GPU"
    } > "queue/pending/$name.sh"; n=$((n+1))
  done
  echo "queued $n E-02c jobs (donor $DONOR_M)"
fi
