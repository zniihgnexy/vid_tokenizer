#!/usr/bin/env bash
# timing_bench.sh -- E-14: end-to-end encode wall time per video on an EXCLUSIVE card (queue job share=1).
# 10 EgoSchema common-100 videos x {ours main config 30 epochs, ours warm-start 10 epochs, HEVC crf33 (x265),
# VVC qp32 (vvenc faster), feature cache (ViT tokens + pca64-q2 / AE z128 l1)}. Writes R/exp_timing/timing.csv.
set -uo pipefail
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
export PYTHONPATH=src PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True HF_HOME=/mnt/nas/xinyizheng/.hfcache TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 INTERNVL_MODEL_PATH=/mnt/nas/xinyizheng/InternVL2_5-8B
export NUM_FRAMES=128 SAMPLING=uniform RES=256
R=/mnt/nas/xinyizheng/vidtok_out; T=$R/exp_timing; ADPT=$R/exp_shared_adapter_u/universal_adapter_internvl_v1.pt
mkdir -p $T/_videos $T/tmp; [ -e $T/_videos/egoschema ] || ln -s $R/gate1_egos/_videos/egoschema $T/_videos/egoschema
export DATASET=egoschema DATASET_CONFIG=configs/datasets/egoschema.yaml DATASET_MANIFEST_DIR=outputs/datasets/egoschema OUT_ROOT=$T RESULTS_CSV=$T/results.csv
OUT=$T/timing.csv; [ -f $OUT ] || echo "uuid,method,secs,host_gpu" > $OUT
VIDS=$(grep -v '^$' outputs/gate1_egos/common100_uuids.txt | head -10)
DONOR_U=$(grep -v '^$' outputs/gate1_egos/common100_uuids.txt | tail -1)
DONOR=$(ls -d $R/u_egos/egoschema/internvl/mid/ours/cap_r1_n1224_dfilm/$DONOR_U/*_chunk00 | head -1)
GNAME=$(nvidia-smi --query-gpu=name --format=csv,noheader -i "$GPU" 2>/dev/null | head -1)
tm(){ local u=$1 m=$2; shift 2; local t0=$(date +%s%N); "$@" >/dev/null 2>&1; local rc=$?; local t1=$(date +%s%N)
      echo "$u,$m,$(( (t1-t0)/1000000 ))e-3,$GNAME" | sed 's/\([0-9]*\)\([0-9]\{3\}\)e-3/\1.\2/' >> $OUT; return $rc; }
for u in $VIDS; do
  F=$T/_videos/egoschema/${u}_256_uniform
  tm $u ours_main_30ep env NVRC_FROZEN_ADAPTER=$ADPT NVRC_ADAPTER_DELTA=film RATE_SUFFIX=_dfilm bash scripts/units/train_codec.sh --uuid $u --rate cap --capacity r1 --teacher-layer 1224 --backbone internvl --layer mid --interface ours --gpu $GPU --epochs 30
  tm $u ours_warmstart_10ep env NVRC_FROZEN_ADAPTER=$ADPT NVRC_ADAPTER_DELTA=film RATE_SUFFIX=_dfilm_ws10 NVRC_INIT_CODEC=$DONOR bash scripts/units/train_codec.sh --uuid $u --rate cap --capacity r1 --teacher-layer 1224 --backbone internvl --layer mid --interface ours --gpu $GPU --epochs 10
  tm $u hevc_crf33 ffmpeg -y -framerate 30 -pattern_type glob -i "$F/*.png" -c:v libx265 -crf 33 -pix_fmt yuv420p -x265-params log-level=error $T/tmp/$u.mp4
  ffmpeg -y -framerate 30 -pattern_type glob -i "$F/*.png" -pix_fmt yuv420p $T/tmp/$u.y4m >/dev/null 2>&1
  tm $u vvc_qp32 third_party/baselines/vvenc/install/bin/vvencapp --preset faster -i $T/tmp/$u.y4m -q 32 -o $T/tmp/$u.266
  rm -f $T/tmp/$u.y4m
done
python tools/timing_featcache.py --frames-root $T/_videos/egoschema --uuids $VIDS --gpu-name "$GNAME" --out $OUT
echo "timing done -> $OUT"
