#!/usr/bin/env bash
# Generate queue jobs for the B1 (cached-pixel-path) and B2 (shuffle / mismatch) controls on the
# existing caches (per-video adapter, phase-0 grid). Mechanism tests; rerun on universal-adapter
# caches later is cheap. Outputs -> R/gate1_{vmme,egos}/stratified_ctrl_*.csv
cd /home/xinyizheng/vid_tokenizer || exit 1
R=/mnt/nas/xinyizheng/vidtok_out
mkdir -p queue/pending
HDR='#Q minmb=24000 share=1
set -uo pipefail
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
export PYTHONPATH=src PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True HF_HOME=/mnt/nas/xinyizheng/.hfcache TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 INTERNVL_MODEL_PATH=/mnt/nas/xinyizheng/InternVL2_5-8B'
mk(){ # mk <jobname> <dataset> <manifest> <out_root> <extra harvest args...>
  local name=$1 ds=$2 mf=$3 root=$4; shift 4
  { echo "$HDR"; echo "python tools/harvest_stratified.py --dataset $ds --out-root $root --manifest-dir outputs/datasets/$ds --manifest-file $mf $* --out $root/stratified_${name#*_}.csv"; } > "queue/pending/$name.sh"
}
# B2: shuffle / mismatch, ours@cap_r1 + oracle (same frames, token path)
mk 030_ctrl_shuffle_vmme   vmme_long_motion questions.jsonl $R/gate1_vmme --interface ours --rates cap_r1 --crfs __none__ --ctrl shuffle
mk 031_ctrl_mismatch_vmme  vmme_long_motion questions.jsonl $R/gate1_vmme --interface ours --rates cap_r1 --crfs __none__ --ctrl mismatch
mk 032_ctrl_shuffle_egos   egoschema manifest.jsonl $R/gate1_egos --interface ours --rates cap_r1 --crfs __none__ --ctrl shuffle
mk 033_ctrl_mismatch_egos  egoschema manifest.jsonl $R/gate1_egos --interface ours --rates cap_r1 --crfs __none__ --ctrl mismatch
# B1: cached pixel path (oracle + HEVC crf33/40/45 tokens cached once, pooled to 64/16)
mk 034_ctrl_pixcache_vmme  vmme_long_motion questions.jsonl $R/gate1_vmme --interface ours --rates __none__ --no-oracle --crfs 33 40 45 --pixel-cache-pool 64 16
mk 035_ctrl_pixcache_egos  egoschema manifest.jsonl $R/gate1_egos --interface ours --rates __none__ --no-oracle --crfs 33 40 45 --pixel-cache-pool 64 16
ls queue/pending
