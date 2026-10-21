#!/usr/bin/env bash
# LVB baselines (matched rate each) recon + harvest, after ours training. Elastic-ish.
set -eo pipefail
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
export PYTHONPATH=src HF_HOME=/mnt/nas/xinyizheng/.hfcache TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1
R=/mnt/nas/xinyizheng/vidtok_out
export DATASET=lvb_long25 DATASET_CONFIG=configs/datasets/lvb_long25.yaml DATASET_MANIFEST_DIR=outputs/datasets/lvb_long25
export OUT_ROOT=$R/gate1_lvb RESULTS_CSV=$R/gate1_lvb/results.csv NUM_FRAMES=128 SAMPLING=uniform RES=256
# wait for ours training done
until grep -q "LVB OURS TRAIN: DONE" logs/lvb_ours_train.log 2>/dev/null; do sleep 300; done
mapfile -t U < <(python -c "import json;print('\n'.join(sorted({json.loads(l)['video_idx'] for l in open('$DATASET_MANIFEST_DIR/manifest.jsonl')})))")
echo "######## LVB baselines: ${#U[@]} videos @ $(date) ########"
GPU="${GPU:-6}"
for u in "${U[@]}"; do
  bash scripts/units/baseline_pixel.sh --uuid "$u" --crf 33 --gpu $GPU >/dev/null 2>&1 || echo "[WARN] hevc $u"
  bash scripts/units/baseline_vvc.sh   --uuid "$u" --qp 36 --gpu $GPU --recon-only >/dev/null 2>&1 || echo "[WARN] vvc $u"
  bash scripts/units/baseline_dcvc.sh  --uuid "$u" --qp 28 --gpu $GPU --recon-only >/dev/null 2>&1 || echo "[WARN] dcvc $u"
  bash scripts/units/baseline_smcpp.sh --uuid "$u" --crf 43 --gpu $GPU --recon-only >/dev/null 2>&1 || echo "[WARN] smcpp $u"
  bash scripts/units/baseline_ugicm.sh --uuid "$u" --q 1 --gpu $GPU --recon-only >/dev/null 2>&1 || echo "[WARN] ugicm $u"
  bash scripts/units/baseline_vcmrs.sh --uuid "$u" --qp 27 --gpu $GPU --recon-only >/dev/null 2>&1 || echo "[WARN] vcmrs $u"
done
echo "LVB BASELINES RECON: DONE @ $(date)"
# harvest all (ours + baselines + oracle)
CUDA_VISIBLE_DEVICES=$GPU python tools/harvest_stratified.py --out-root $R/gate1_lvb --dataset lvb_long25 \
  --manifest-dir outputs/datasets/lvb_long25 --rates cap_r1 --interface ours \
  --crfs 33 --vvc-qps 36 --dcvc-qps 28 --smcpp-crfs 43 --ugicm-qs 1 --vcmrs-qps 27 \
  --out $R/gate1_lvb/stratified_lvb.csv
echo "LVB HARVEST: DONE @ $(date)"
