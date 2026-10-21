#!/usr/bin/env bash
# e10_internvl35.sh train|harvest -- E-10 reduced (D-016): InternVL3.5-8B as a second receiver, EgoSchema
# common-100 x cap_r1 under the main configuration (frozen 3.5 universal adapter + 2 KB FiLM + 12/24).
#   train    091: per video: codec training in the nvrc env (vision-only 3.5 teacher) + QA eval with the
#                 vidtok_qwen python (transformers 4.57; token-injection path verified 10-18)
#   harvest  095: 4-phase stratified harvest (ours + oracle + HEVC ladder) in the vidtok_qwen env
# Jobs wait (<= 24 h) for the 3.5 adapter produced by scripts/experiments/adapter_universal_chain_internvl35.sh (queue 090).
cd /home/xinyizheng/vid_tokenizer || exit 1
R=/mnt/nas/xinyizheng/vidtok_out; M=/mnt/nas/xinyizheng/InternVL3_5-8B
ADPT=$R/exp_shared_adapter_u35/universal_adapter_internvl35_v1.pt
QPY=/mnt/nas/xinyizheng/envs/vidtok_qwen/bin
OUT=$R/ivl35_egos
MODE="${1:-train}"; mkdir -p queue/pending "$OUT/_videos"
[ -e $OUT/_videos/egoschema ] || ln -s $R/gate1_egos/_videos/egoschema $OUT/_videos/egoschema
ENV="set -uo pipefail
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
export PYTHONPATH=src PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True HF_HOME=/mnt/nas/xinyizheng/.hfcache TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 INTERNVL_MODEL_PATH=$M
export NUM_FRAMES=128 SAMPLING=uniform RES=256
export DATASET=egoschema DATASET_CONFIG=configs/datasets/egoschema.yaml DATASET_MANIFEST_DIR=outputs/datasets/egoschema OUT_ROOT=$OUT RESULTS_CSV=$OUT/results.csv"
WAIT="for i in \$(seq 1 1440); do [ -f $ADPT ] && break; sleep 60; done; [ -f $ADPT ] || { echo 'adapter missing after 24h'; exit 1; }"
if [ "$MODE" = train ]; then
  n=0
  for u in $(grep -v '^$' outputs/gate1_egos/common100_uuids.txt); do
    { echo "#Q minmb=24000 share=2"; echo "$ENV"; echo "$WAIT"
      echo "export NVRC_FROZEN_ADAPTER=$ADPT NVRC_ADAPTER_DELTA=film RATE_SUFFIX=_dfilm"
      echo "bash scripts/units/train_codec.sh --uuid $u --rate cap --capacity r1 --teacher-layer 1224 --backbone internvl --layer mid --interface ours --gpu \$GPU --epochs 30"
      echo "PATH=$QPY:\$PATH bash scripts/units/eval_downstream.sh --uuid $u --rate cap --capacity r1 --loss-variant n1224 --backbone internvl --layer mid --interface ours --gpu \$GPU"
    } > "queue/pending/091_e10_ego_cap_r1_${u}.sh"; n=$((n+1))
  done
  echo "queued $n E-10 train+eval jobs (091_e10_ego_cap_r1_*)"
else
  # harvests only read finished run dirs: wait until no 091 training job is pending or running
  WAIT091="while ls queue/pending queue/running | grep -q '^091_e10_'; do sleep 120; done"
  for ph in 0 1 2 3; do
    { echo "#Q minmb=24000 share=2"; echo "$ENV"; echo "$WAIT091"; echo "export QA_SAMPLE_OFFSET=$ph"
      echo "$QPY/python tools/harvest_stratified.py --model-path $M --dataset egoschema --out-root $OUT --manifest-dir outputs/datasets/egoschema --manifest-file manifest.jsonl --interface ours --rates cap_r1_n1224_dfilm --crfs 28 33 40 45 51 --out $OUT/stratified_u35_n1224_dfilm_off$ph.csv"
    } > "queue/pending/095_e10h_ego_off$ph.sh"
  done
  echo "queued 095_e10h_ego_off{0..3}"
fi
