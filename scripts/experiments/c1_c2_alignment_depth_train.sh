#!/usr/bin/env bash
# c1_c2_alignment_depth_train.sh <set> -- queue per-video ablation jobs on the 115 Video-MME motion videos
# (per-video adapter, as all ablations). Sets: smoke | c1_cap_r1 | c1_lamb025 | c2_nmulti
#   C1 = final-layer (N=24, Latent-INR-style) alignment at cap_r1 and lamb025
#   C2 = multi-layer joint alignment (6+12+18) at cap_r1
cd /home/xinyizheng/vid_tokenizer || exit 1
R=/mnt/nas/xinyizheng/vidtok_out; SET="${1:?set}"
HDR='#Q minmb=24000 share=1
set -uo pipefail
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
export PYTHONPATH=src PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True HF_HOME=/mnt/nas/xinyizheng/.hfcache TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 INTERNVL_MODEL_PATH=/mnt/nas/xinyizheng/InternVL2_5-8B
export DATASET=vmme_long_motion DATASET_CONFIG=configs/datasets/vmme_long_motion.yaml DATASET_MANIFEST_DIR=outputs/datasets/vmme_long_motion
export NUM_FRAMES=128 SAMPLING=uniform RES=256'
MOTION=$(python3 -c "
import json;print(' '.join(sorted({json.loads(l)['video_idx'] for l in open('outputs/datasets/vmme_long_motion/questions.jsonl') if json.loads(l)['domain'] in {'Sports Competition','Artistic Performance','Film & Television'}})))")
mk(){ # mk <jobname> <out_root> <train args> <eval args>
  { echo "$HDR"; echo "export OUT_ROOT=$2 RESULTS_CSV=$2/results.csv"
    echo "bash scripts/units/train_codec.sh $3 --gpu \$GPU --epochs \${EPOCHS:-30}"
    echo "bash scripts/units/eval_downstream.sh $4 --gpu \$GPU"; } > "queue/pending/$1.sh"
}
case "$SET" in
  smoke)  # 1 video, 1 epoch each, scratch root; proves the new profiles run end to end
    u=$(echo $MOTION | cut -d" " -f1); mkdir -p $R/_smoke/_videos; [ -e $R/_smoke/_videos/vmme_long_motion ] || ln -s $R/gate1_vmme/_videos/vmme_long_motion $R/_smoke/_videos/vmme_long_motion
    mk 015_smoke_nmulti $R/_smoke "--uuid $u --rate cap --capacity r1 --teacher-layer multi --backbone internvl --layer mid --interface ours" "--uuid $u --rate cap --capacity r1 --loss-variant nmulti --backbone internvl --layer mid --interface ours"
    sed -i 's/\${EPOCHS:-30}/1/' queue/pending/015_smoke_nmulti.sh
    mk 016_smoke_final_lamb025 $R/_smoke "--uuid $u --rate cap --capacity r1 --loss-variant lamb025 --backbone internvl --layer mid --interface final" "--uuid $u --rate cap --capacity r1 --loss-variant lamb025 --backbone internvl --layer mid --interface final"
    sed -i 's/\${EPOCHS:-30}/1/' queue/pending/016_smoke_final_lamb025.sh ;;
  c1_cap_r1)  for u in $MOTION; do mk 060_c1_final_cap_r1_$u $R/gate1_vmme "--uuid $u --rate cap --capacity r1 --backbone internvl --layer mid --interface final" "--uuid $u --rate cap --capacity r1 --backbone internvl --layer mid --interface final"; done ;;
  c1_lamb025) for u in $MOTION; do mk 061_c1_final_lamb025_$u $R/gate1_vmme "--uuid $u --rate cap --capacity r1 --loss-variant lamb025 --backbone internvl --layer mid --interface final" "--uuid $u --rate cap --capacity r1 --loss-variant lamb025 --backbone internvl --layer mid --interface final"; done ;;
  c2_nmulti)  for u in $MOTION; do mk 062_c2_nmulti_cap_r1_$u $R/gate1_vmme "--uuid $u --rate cap --capacity r1 --teacher-layer multi --backbone internvl --layer mid --interface ours" "--uuid $u --rate cap --capacity r1 --loss-variant nmulti --backbone internvl --layer mid --interface ours"; done ;;
  *) echo "unknown set"; exit 2;;
esac
echo "queued: $(ls queue/pending | grep -c .) pending jobs"
