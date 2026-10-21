#!/usr/bin/env bash
# e12_e13_e14_controls.sh e12|e13|e14 -- D-024 controlled-variable completions (MASTER_PLAN §3.1).
#   e12  Ego 2x2 ablation at cap_r1 (frozen universal adapter): the two missing cells
#        A = FiLM delta + layer-12 alignment   (tag cap_r1_dfilm)
#        B = no delta   + layer-12/24 alignment (tag cap_r1_n1224)
#        100 train+eval jobs per cell (100_e12_*) + 4-phase ours-only harvest (130_e12h_*)
#   e13  controls on the MAIN configuration (cap_r1_n1224_dfilm), Ego + VMME-motion, 4 phases (099_e13_*):
#        frame shuffle, video mismatch, ours pooled to 64/16 tokens, cached-pixel path pooled 64/16
#   e14  isolated encode-time benchmark on an exclusive card, 10 Ego videos (120_e14_timing)
# Wait guards test "ls queue/pending queue/running" (always exit 0) -- the old "ls glob1 glob2 | grep"
# guard silently passed under `set -o pipefail` when one glob was empty (lamb050 incident, 10-20).
cd /home/xinyizheng/vid_tokenizer || exit 1
R=/mnt/nas/xinyizheng/vidtok_out
ADPT=$R/exp_shared_adapter_u/universal_adapter_internvl_v1.pt
MODE="${1:?e12|e13|e14}"; mkdir -p queue/pending
ENV='set -uo pipefail
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
export PYTHONPATH=src PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True HF_HOME=/mnt/nas/xinyizheng/.hfcache TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 INTERNVL_MODEL_PATH=/mnt/nas/xinyizheng/InternVL2_5-8B
export NUM_FRAMES=128 SAMPLING=uniform RES=256'
EGOENV="export DATASET=egoschema DATASET_CONFIG=configs/datasets/egoschema.yaml DATASET_MANIFEST_DIR=outputs/datasets/egoschema OUT_ROOT=$R/u_egos RESULTS_CSV=$R/u_egos/results.csv"
EGO_H="--dataset egoschema --out-root $R/u_egos --manifest-dir outputs/datasets/egoschema --manifest-file manifest.jsonl"
VMME_H="--dataset vmme_long_motion --out-root $R/u_vmme --manifest-dir outputs/datasets/vmme_long_motion --manifest-file questions.jsonl"
EGO=$(grep -v '^$' outputs/gate1_egos/common100_uuids.txt)
case "$MODE" in
  e12)
    n=0
    for u in $EGO; do
      { echo "#Q minmb=24000 share=2"; echo "$ENV"; echo "$EGOENV"
        echo "export NVRC_FROZEN_ADAPTER=$ADPT NVRC_ADAPTER_DELTA=film RATE_SUFFIX=_dfilm"
        echo "bash scripts/units/train_codec.sh --uuid $u --rate cap --capacity r1 --backbone internvl --layer mid --interface ours --gpu \$GPU --epochs 30"
        echo "bash scripts/units/eval_downstream.sh --uuid $u --rate cap --capacity r1 --backbone internvl --layer mid --interface ours --gpu \$GPU"
      } > "queue/pending/100_e12_A_film_l12_$u.sh"
      { echo "#Q minmb=24000 share=2"; echo "$ENV"; echo "$EGOENV"
        echo "export NVRC_FROZEN_ADAPTER=$ADPT"
        echo "bash scripts/units/train_codec.sh --uuid $u --rate cap --capacity r1 --teacher-layer 1224 --backbone internvl --layer mid --interface ours --gpu \$GPU --epochs 30"
        echo "bash scripts/units/eval_downstream.sh --uuid $u --rate cap --capacity r1 --loss-variant n1224 --backbone internvl --layer mid --interface ours --gpu \$GPU"
      } > "queue/pending/100_e12_B_nofilm_l1224_$u.sh"; n=$((n+2))
    done
    WAIT="while ls queue/pending queue/running | grep -q '^100_e12_'; do sleep 120; done"
    for ph in 0 1 2 3; do
      { echo "#Q minmb=24000 share=2"; echo "$ENV"; echo "$EGOENV"; echo "$WAIT"; echo "export QA_SAMPLE_OFFSET=$ph"
        echo "python tools/harvest_stratified.py $EGO_H --interface ours --rates cap_r1_dfilm cap_r1_n1224 --no-oracle --crfs __none__ --out $R/u_egos/stratified_e12_2x2_off$ph.csv"
      } > "queue/pending/130_e12h_ego_off$ph.sh"
    done
    echo "queued $n E-12 train jobs + 4 harvests";;
  e13)
    n=0
    for ds in ego vmme; do
      if [ $ds = ego ]; then H="$EGO_H"; D=$R/u_egos; else H="$VMME_H"; D=$R/u_vmme; fi
      for ph in 0 1 2 3; do
        for kind in shuffle mismatch pool64 pool16 pixcache; do
          case $kind in
            shuffle|mismatch) A="--interface ours --rates cap_r1_n1224_dfilm --crfs __none__ --ctrl $kind";;
            pool64) A="--interface ours --rates cap_r1_n1224_dfilm --crfs __none__ --pool 64 --no-oracle";;
            pool16) A="--interface ours --rates cap_r1_n1224_dfilm --crfs __none__ --pool 16 --no-oracle";;
            pixcache) A="--interface ours --rates __none__ --no-oracle --crfs 33 40 45 --pixel-cache-pool 64 16";;
          esac
          { echo "#Q minmb=24000 share=2"; echo "$ENV"; echo "export QA_SAMPLE_OFFSET=$ph"
            echo "python tools/harvest_stratified.py $H $A --out $D/stratified_e13_${kind}_off$ph.csv"
          } > "queue/pending/099_e13_${ds}_${kind}_off$ph.sh"; n=$((n+1))
        done
      done
    done
    echo "queued $n E-13 control harvests";;
  e14)
    { echo "#Q minmb=46000 share=1"; echo "bash tools/timing_bench.sh"; } > queue/pending/120_e14_timing.sh
    echo "queued 120_e14_timing (exclusive card)";;
esac
