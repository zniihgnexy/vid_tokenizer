#!/usr/bin/env bash
# e11_main_results.sh <universal_adapter.pt> [train|harvest|egorung] -- A1: the CVPR-27 main results under the
# frozen universal adapter (bits = codec stream only).
#   train    queue one job per (dataset, rung, video): train codec against the frozen adapter + eval
#            EgoSchema common-100 x {lamb006, lamb025, cap_r1, lamb150}
#            Video-MME 115 motion videos x {lamb006, lamb025, cap_r1}
#            -> R/u_egos, R/u_vmme (fresh roots; gate1_* keep the per-video-adapter results)
#   harvest  queue the 4-phase stratified harvests once training is complete
# Jobs are idempotent (train_codec skips a trained video; eval appends a row).
cd /home/xinyizheng/vid_tokenizer || exit 1
R=/mnt/nas/xinyizheng/vidtok_out
ADPT="${1:?path to universal adapter .pt}"; MODE="${2:-train}"
# E-11 main configuration (G-A, 2026-10-04): DELTA_MODE=film adds the per-video FiLM delta
# (counted in the bitstream), TLAYER=1224 trains with joint layer-12/24 alignment. Both optional.
DELTA_MODE="${DELTA_MODE:-}"; TLAYER="${TLAYER:-}"
TL_TRAIN=""; [ -n "$TLAYER" ] && TL_TRAIN="--teacher-layer $TLAYER"
evflags(){ # eval flags for a rung: with TLAYER the loss-variant tag is <rung>_n<TLAYER> (cap_r1 -> n<TLAYER>)
  if [ -z "$TLAYER" ]; then lv "$1"; elif [ "$1" = cap_r1 ]; then echo "--loss-variant n$TLAYER"; else echo "--loss-variant ${1}_n$TLAYER"; fi; }
DELTA_ENV=""; [ -n "$DELTA_MODE" ] && DELTA_ENV="NVRC_ADAPTER_DELTA=$DELTA_MODE RATE_SUFFIX=_d$DELTA_MODE"
# Optional warm-start (E-02c): INIT_CODEC_EGO / INIT_CODEC_VMME = main-config donor run dirs, EPOCHS (default 30).
# With a donor the rate suffix gets _ws<EPOCHS> so warm-started runs never collide with scratch runs.
EPOCHS="${EPOCHS:-30}"; INIT_CODEC_EGO="${INIT_CODEC_EGO:-}"; INIT_CODEC_VMME="${INIT_CODEC_VMME:-}"
wsenv(){ local d="$1"; [ -n "$d" ] && echo "NVRC_INIT_CODEC=$d RATE_SUFFIX=_d${DELTA_MODE}_ws${EPOCHS}" || true; }
[ -f "$ADPT" ] || { echo "adapter not found: $ADPT"; exit 1; }
mkdir -p queue/pending
ENV='set -uo pipefail
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
export PYTHONPATH=src PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True HF_HOME=/mnt/nas/xinyizheng/.hfcache TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 INTERNVL_MODEL_PATH=/mnt/nas/xinyizheng/InternVL2_5-8B
export NUM_FRAMES=128 SAMPLING=uniform RES=256'
dsenv(){ # dsenv ego|vmme -> env lines + OUT_ROOT setup
  case "$1" in
    ego)  echo "export DATASET=egoschema DATASET_CONFIG=configs/datasets/egoschema.yaml DATASET_MANIFEST_DIR=outputs/datasets/egoschema OUT_ROOT=$R/u_egos RESULTS_CSV=$R/u_egos/results.csv"
          echo "mkdir -p \$OUT_ROOT/_videos; [ -e \$OUT_ROOT/_videos/egoschema ] || ln -s $R/gate1_egos/_videos/egoschema \$OUT_ROOT/_videos/egoschema";;
    vmme) echo "export DATASET=vmme_long_motion DATASET_CONFIG=configs/datasets/vmme_long_motion.yaml DATASET_MANIFEST_DIR=outputs/datasets/vmme_long_motion OUT_ROOT=$R/u_vmme RESULTS_CSV=$R/u_vmme/results.csv"
          echo "mkdir -p \$OUT_ROOT/_videos; [ -e \$OUT_ROOT/_videos/vmme_long_motion ] || ln -s $R/gate1_vmme/_videos/vmme_long_motion \$OUT_ROOT/_videos/vmme_long_motion";;
  esac
}
EGO=$(grep -v '^$' outputs/gate1_egos/common100_uuids.txt)
VMME=$(python3 -c "
import json;print(' '.join(sorted({json.loads(l)['video_idx'] for l in open('outputs/datasets/vmme_long_motion/questions.jsonl') if json.loads(l)['domain'] in {'Sports Competition','Artistic Performance','Film & Television'}})))")
lv(){ [ "$1" = cap_r1 ] && echo "" || echo "--loss-variant $1"; }

if [ "$MODE" = egorung ]; then
  # D-020 (2026-10-19): one extra EgoSchema rung under the main configuration (RUNG=lamb050 fills the
  # 0.037-0.130 bpp gap). Train+eval jobs (048) plus a 4-phase ours-only harvest (049) that waits for them.
  rung="${RUNG:?set RUNG=lambXXX}"; n=0
  for u in $EGO; do
    { echo "#Q minmb=24000 share=2"; echo "$ENV"; dsenv ego; echo "export NVRC_FROZEN_ADAPTER=$ADPT $DELTA_ENV $(wsenv "$INIT_CODEC_EGO")"
      echo "bash scripts/units/train_codec.sh --uuid $u --rate cap --capacity r1 $(lv $rung) $TL_TRAIN --backbone internvl --layer mid --interface ours --gpu \$GPU --epochs $EPOCHS"
      echo "bash scripts/units/eval_downstream.sh --uuid $u --rate cap --capacity r1 $(evflags $rung) --backbone internvl --layer mid --interface ours --gpu \$GPU"
    } > "queue/pending/048_a1x_ego_${rung}_${u}.sh"; n=$((n+1)); done
  SFX=""; [ -n "$TLAYER" ] && SFX="_n$TLAYER"; [ -n "$DELTA_MODE" ] && SFX="${SFX}_d$DELTA_MODE"
  WAIT048="while ls queue/pending queue/running | grep -q '^048_a1x_ego_${rung}_'; do sleep 120; done"
  for ph in 0 1 2 3; do
    { echo "#Q minmb=24000 share=2"; echo "$ENV"; dsenv ego; echo "$WAIT048"; echo "export QA_SAMPLE_OFFSET=$ph"
      echo "python tools/harvest_stratified.py --dataset egoschema --out-root $R/u_egos --manifest-dir outputs/datasets/egoschema --manifest-file manifest.jsonl --interface ours --rates cap_r1_${rung}$SFX --no-oracle --crfs __none__ --out $R/u_egos/stratified_u${SFX}_${rung}_off$ph.csv"
    } > "queue/pending/049_a1xh_ego_${rung}${SFX}_off$ph.sh"
  done
  echo "queued $n train jobs (048_a1x_ego_${rung}_*) + 4 harvest jobs (049_a1xh_ego_${rung}${SFX}_off*)"
elif [ "$MODE" = train ]; then
  n=0
  for rung in lamb006 lamb025 cap_r1 lamb150; do for u in $EGO; do
    { echo "#Q minmb=24000 share=2"; echo "$ENV"; dsenv ego; echo "export NVRC_FROZEN_ADAPTER=$ADPT $DELTA_ENV $(wsenv "$INIT_CODEC_EGO")"
      echo "bash scripts/units/train_codec.sh --uuid $u --rate cap --capacity r1 $(lv $rung) $TL_TRAIN --backbone internvl --layer mid --interface ours --gpu \$GPU --epochs $EPOCHS"
      echo "bash scripts/units/eval_downstream.sh --uuid $u --rate cap --capacity r1 $(evflags $rung) --backbone internvl --layer mid --interface ours --gpu \$GPU"
    } > "queue/pending/040_a1_ego_${rung}_${u}.sh"; n=$((n+1)); done; done
  for rung in lamb006 lamb025 cap_r1; do for u in $VMME; do
    { echo "#Q minmb=24000 share=2"; echo "$ENV"; dsenv vmme; echo "export NVRC_FROZEN_ADAPTER=$ADPT $DELTA_ENV $(wsenv "$INIT_CODEC_VMME")"
      echo "bash scripts/units/train_codec.sh --uuid $u --rate cap --capacity r1 $(lv $rung) $TL_TRAIN --backbone internvl --layer mid --interface ours --gpu \$GPU --epochs $EPOCHS"
      echo "bash scripts/units/eval_downstream.sh --uuid $u --rate cap --capacity r1 $(evflags $rung) --backbone internvl --layer mid --interface ours --gpu \$GPU"
    } > "queue/pending/041_a1_vmme_${rung}_${u}.sh"; n=$((n+1)); done; done
  echo "queued $n A1 training jobs (040_a1_ego_*, 041_a1_vmme_*)"
else
  # 4-phase harvests: ours rungs + oracle per phase; one job per (dataset, phase).
  # Rate tags carry the main-config suffix (e.g. _n1224_dfilm) so the harvest reads the E-11 run dirs;
  # without DELTA_MODE/TLAYER it reads the plain frozen-universal runs (the V1 lower bound).
  SFX=""; [ -n "$TLAYER" ] && SFX="_n$TLAYER"; [ -n "$DELTA_MODE" ] && SFX="${SFX}_d$DELTA_MODE"
  for ph in 0 1 2 3; do
    { echo "#Q minmb=24000 share=1"; echo "$ENV"; dsenv ego; echo "export QA_SAMPLE_OFFSET=$ph"
      echo "python tools/harvest_stratified.py --dataset egoschema --out-root $R/u_egos --manifest-dir outputs/datasets/egoschema --manifest-file manifest.jsonl --interface ours --rates cap_r1_lamb006$SFX cap_r1_lamb025$SFX cap_r1$SFX cap_r1_lamb150$SFX --crfs __none__ --out $R/u_egos/stratified_u${SFX}_off$ph.csv"
    } > "queue/pending/045_a1h_ego${SFX}_off$ph.sh"
    { echo "#Q minmb=24000 share=1"; echo "$ENV"; dsenv vmme; echo "export QA_SAMPLE_OFFSET=$ph"
      echo "python tools/harvest_stratified.py --dataset vmme_long_motion --out-root $R/u_vmme --manifest-dir outputs/datasets/vmme_long_motion --manifest-file questions.jsonl --interface ours --rates cap_r1_lamb006$SFX cap_r1_lamb025$SFX cap_r1$SFX --crfs __none__ --out $R/u_vmme/stratified_u${SFX}_off$ph.csv"
    } > "queue/pending/046_a1h_vmme${SFX}_off$ph.sh"
  done
  echo "queued 8 harvest jobs (045_a1h_ego${SFX}_off*, 046_a1h_vmme${SFX}_off*)"
fi
