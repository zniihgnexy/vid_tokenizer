#!/usr/bin/env bash
# d0_internvl35_screen.sh [smoke|screen] -- D0: InternVL3.5-8B (2025, InternViT-300M + Qwen3-8B) as the
# newer backbone. Runs in the NAS env vidtok_qwen (transformers 4.57). Weights must already be
# at /mnt/nas/xinyizheng/InternVL3_5-8B (scripts/ops/fetch_internvl35.sh).
#   smoke   backend gate test (pixel path == injection path) + one oracle QA
#   screen  Gate-0 regime screen, phase 0: oracle + HEVC crf{28,33,40,45,51} on the VMME motion
#           manifest (all 180 videos; motion filter applied at analysis) and EgoSchema (129)
cd /home/xinyizheng/vid_tokenizer || exit 1
R=/mnt/nas/xinyizheng/vidtok_out; M=/mnt/nas/xinyizheng/InternVL3_5-8B
PY=/mnt/nas/xinyizheng/envs/vidtok_qwen/bin/python
[ -f "$M/model.safetensors.index.json" ] && ls "$M"/model-0000*-of-00004.safetensors >/dev/null 2>&1 || { echo "weights incomplete at $M"; exit 1; }
HDR="#Q minmb=24000 share=2
set -uo pipefail
cd /home/xinyizheng/vid_tokenizer
export PYTHONPATH=src PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True HF_HOME=/mnt/nas/xinyizheng/.hfcache TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 INTERNVL_MODEL_PATH=$M"
case "${1:-smoke}" in
  smoke)
    IMG=$(ls $R/gate1_vmme/_videos/vmme_long_motion/*_256_uniform/*.png 2>/dev/null | head -1)
    [ -n "$IMG" ] || IMG=$(find $R/gate1_vmme/_videos/vmme_long_motion -name "*.png" | head -1)
    { echo "$HDR"; echo "$PY src/machine_codec_pipeline/vlm/internvl_backend.py --smoke --model-path $M --image $IMG"; } > queue/pending/050_d0_smoke_ivl35.sh
    echo "queued 050_d0_smoke_ivl35 (image $IMG)";;
  screen)
    for ds in vmme egos; do
      case $ds in vmme) DS=vmme_long_motion; MF=questions.jsonl; SRC=$R/gate1_vmme;; egos) DS=egoschema; MF=manifest.jsonl; SRC=$R/gate1_egos;; esac
      OUT=$R/ivl35_$ds; mkdir -p $OUT/_videos; [ -e $OUT/_videos/$DS ] || ln -s $SRC/_videos/$DS $OUT/_videos/$DS
      { echo "$HDR"; echo "export QA_SAMPLE_OFFSET=0"
        echo "$PY tools/harvest_stratified.py --model-path $M --dataset $DS --out-root $OUT --manifest-dir outputs/datasets/$DS --manifest-file $MF --interface ours --rates __none__ --crfs 28 33 40 45 51 --out $OUT/stratified_screen_off0.csv"
      } > queue/pending/051_d0_screen_$ds.sh
    done
    echo "queued 051_d0_screen_{vmme,egos}";;
esac
