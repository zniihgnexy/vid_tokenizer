#!/usr/bin/env bash
# e03_pool_expansion.sh train|harvest|fsweep -- E-03 evaluation-pool expansion under the main configuration
# (D-016 candidate, MASTER_PLAN §3.1): detail-sensitive pools where the INR advantage should show.
#   LongVideoBench 100 (outputs/datasets/longvideobench/manifest.jsonl) x {cap_r1, lamb025}
#   Video-MME long, NON-motion domains minus the 16 adapter donors (48 videos) x {cap_r1}
# train    080: per video: oracle + HEVC ladder (crf 28 33 40 45 51) [one job], and per rung: train+eval [one job]
# harvest  085: 4-phase stratified harvests (ours rungs + oracle + HEVC) and the 8 E-04 Pareto cells
cd /home/xinyizheng/vid_tokenizer || exit 1
R=/mnt/nas/xinyizheng/vidtok_out
ADPT=$R/exp_shared_adapter_u/universal_adapter_internvl_v1.pt
BOOK=$R/exp_featcache/featcodec_internvl_v1.pt
MODE="${1:-train}"; mkdir -p queue/pending
ENV='set -uo pipefail
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
export PYTHONPATH=src PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True HF_HOME=/mnt/nas/xinyizheng/.hfcache TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 INTERNVL_MODEL_PATH=/mnt/nas/xinyizheng/InternVL2_5-8B
export NUM_FRAMES=128 SAMPLING=uniform RES=256'
MAIN="export NVRC_FROZEN_ADAPTER=$ADPT NVRC_ADAPTER_DELTA=film RATE_SUFFIX=_dfilm"   # D-010 main config
dsenv(){ case "$1" in
  lvb)  echo "export DATASET=longvideobench DATASET_CONFIG=configs/datasets/longvideobench.yaml DATASET_MANIFEST_DIR=outputs/datasets/longvideobench OUT_ROOT=$R/u_lvb RESULTS_CSV=$R/u_lvb/results.csv";;
  vmme) echo "export DATASET=vmme_long_motion DATASET_CONFIG=configs/datasets/vmme_long_motion.yaml DATASET_MANIFEST_DIR=outputs/datasets/vmme_long_motion OUT_ROOT=$R/u_vmme RESULTS_CSV=$R/u_vmme/results.csv"
        echo "mkdir -p \$OUT_ROOT/_videos; [ -e \$OUT_ROOT/_videos/vmme_long_motion ] || ln -s $R/gate1_vmme/_videos/vmme_long_motion \$OUT_ROOT/_videos/vmme_long_motion";;
esac; }
lv(){ [ "$1" = cap_r1 ] && echo "" || echo "--loss-variant $1"; }
ev(){ [ "$1" = cap_r1 ] && echo "--loss-variant n1224" || echo "--loss-variant ${1}_n1224"; }
LVB=$(python3 -c "import json;print(' '.join(json.loads(l)['video_idx'] for l in open('outputs/datasets/longvideobench/manifest.jsonl')))")
# non-motion VMME videos MINUS the 16 universal-adapter donors (evaluation pools stay disjoint from donors)
VMME_NM=$(python3 -c "
import json;M={'Sports Competition','Artistic Performance','Film & Television'}
don={l.split()[1] for l in open('outputs/featcache/donors.txt') if l.startswith('vmme_long_motion')}
print(' '.join(sorted({json.loads(l)['video_idx'] for l in open('outputs/datasets/vmme_long_motion/questions.jsonl') if json.loads(l)['domain'] not in M}-don)))")
if [ "$MODE" = fsweep ]; then
  # E-03b frame-budget probe (phase 0, LVB): 16 query frames at full tokens; 32 query frames with the
  # cache pooled to 64 tokens/frame (ours + oracle via --pixel-cache-pool, featcache p64 cells, AE p64 models)
  AEM64=$(ls $R/exp_featcache/ae/p64_ae_*.pt 2>/dev/null | tr "\n" " ")
  D="--dataset longvideobench --out-root $R/u_lvb --manifest-dir outputs/datasets/longvideobench --manifest-file manifest.jsonl"
  { echo "#Q minmb=24000 share=2"; echo "$ENV"; dsenv lvb; echo "export QA_SAMPLE_OFFSET=0"
    echo "python tools/harvest_stratified.py $D --interface ours --rates cap_r1_n1224_dfilm cap_r1_lamb025_n1224_dfilm --crfs 28 33 40 --sample-count 16 --out $R/u_lvb/stratified_u_n1224_dfilm_f16_off0.csv"
    echo "python tools/featcache_harvest.py $D --book $BOOK --specs p16_pca64_pq8 p64_pca64_pq8 p64_pca64_q2 p256_pca64_pq8 p64_pca256_pq32 --ae-models $AEM64 --sample-count 16 --out $R/exp_featcache/stratified_fc_lvb_f16_off0.csv"
  } > queue/pending/087_e03b_lvb_f16_off0.sh
  { echo "#Q minmb=24000 share=2"; echo "$ENV"; dsenv lvb; echo "export QA_SAMPLE_OFFSET=0"
    echo "python tools/harvest_stratified.py $D --interface ours --rates cap_r1_n1224_dfilm cap_r1_lamb025_n1224_dfilm --crfs 33 --pool 64 --pixel-cache-pool 64 --sample-count 32 --out $R/u_lvb/stratified_u_n1224_dfilm_f32p64_off0.csv"
    echo "python tools/featcache_harvest.py $D --book $BOOK --specs p64_pca64_pq8 p64_pca64_q2 p64_pca256_pq32 --ae-models $AEM64 --sample-count 32 --out $R/exp_featcache/stratified_fc_lvb_f32_off0.csv"
  } > queue/pending/087_e03b_lvb_f32_off0.sh
  echo "queued 087_e03b_lvb_{f16,f32}_off0"
elif [ "$MODE" = train ]; then
  n=0
  for ds in lvb vmme; do
    if [ $ds = lvb ]; then VIDS=$LVB; RUNGS="cap_r1 lamb025"; else VIDS=$VMME_NM; RUNGS="cap_r1"; fi
    for u in $VIDS; do
      { echo "#Q minmb=24000 share=2"; echo "$ENV"; dsenv $ds
        echo "bash scripts/units/eval_oracle.sh --uuid $u --gpu \$GPU"
        for c in 28 33 40 45 51; do echo "bash scripts/units/baseline_pixel.sh --uuid $u --crf $c --gpu \$GPU"; done
      } > "queue/pending/080_e03_${ds}_ref_${u}.sh"; n=$((n+1))
      for rung in $RUNGS; do
        { echo "#Q minmb=24000 share=2"; echo "$ENV"; dsenv $ds; echo "$MAIN"
          echo "bash scripts/units/train_codec.sh --uuid $u --rate cap --capacity r1 $(lv $rung) --teacher-layer 1224 --backbone internvl --layer mid --interface ours --gpu \$GPU --epochs 30"
          echo "bash scripts/units/eval_downstream.sh --uuid $u --rate cap --capacity r1 $(ev $rung) --backbone internvl --layer mid --interface ours --gpu \$GPU"
        } > "queue/pending/081_e03_${ds}_${rung}_${u}.sh"; n=$((n+1))
      done
    done
  done
  echo "queued $n E-03 jobs (080 ref: oracle+HEVC, 081 main-config train+eval); LVB=$(echo $LVB | wc -w) VMME-nonmotion=$(echo $VMME_NM | wc -w)"
else
  echo "$VMME_NM" | tr ' ' '\n' > outputs/datasets/vmme_long_motion/nonmotion48_uuids.txt
  PARETO="p16_pca64_pq8 p16_pca256_pq16 p64_pca64_pq8 p64_pca64_q2 p256_pca64_pq8 p64_pca256_pq32 p256_pca256_pq32 p256_pca256_q2"
  AEM=$(ls $R/exp_featcache/ae/p*_ae_*.pt 2>/dev/null | tr "\n" " "); AEARG=""; [ -n "$AEM" ] && AEARG="--ae-models $AEM"
  # harvests must not start before every 081 training job has finished (they only read finished run dirs)
  WAIT081="while ls queue/pending queue/running | grep -q '^081_e03_'; do sleep 120; done"   # ls exits 2 if any glob is empty, so test the output instead
  for ph in 0 1 2 3; do
    { echo "#Q minmb=24000 share=2"; echo "$ENV"; dsenv lvb; echo "$WAIT081"; echo "export QA_SAMPLE_OFFSET=$ph"
      echo "python tools/harvest_stratified.py --dataset longvideobench --out-root $R/u_lvb --manifest-dir outputs/datasets/longvideobench --manifest-file manifest.jsonl --interface ours --rates cap_r1_n1224_dfilm cap_r1_lamb025_n1224_dfilm --crfs 28 33 40 45 51 --out $R/u_lvb/stratified_u_n1224_dfilm_off$ph.csv"
      echo "python tools/featcache_harvest.py --dataset longvideobench --out-root $R/u_lvb --manifest-dir outputs/datasets/longvideobench --manifest-file manifest.jsonl --book $BOOK --specs $PARETO $AEARG --out $R/exp_featcache/stratified_fc_lvb_off$ph.csv"
    } > "queue/pending/085_e03h_lvb_off$ph.sh"
    { echo "#Q minmb=24000 share=2"; echo "$ENV"; dsenv vmme; echo "$WAIT081"; echo "export QA_SAMPLE_OFFSET=$ph"
      echo "python tools/harvest_stratified.py --dataset vmme_long_motion --out-root $R/u_vmme --manifest-dir outputs/datasets/vmme_long_motion --manifest-file questions.jsonl --interface ours --rates cap_r1_n1224_dfilm --crfs 28 33 40 45 51 --out $R/u_vmme/stratified_u_n1224_dfilm_nonmotion_off$ph.csv"
      echo "python tools/featcache_harvest.py --dataset vmme_long_motion --out-root $R/u_vmme --manifest-dir outputs/datasets/vmme_long_motion --manifest-file questions.jsonl --uuids-file outputs/datasets/vmme_long_motion/nonmotion48_uuids.txt --book $BOOK --specs $PARETO $AEARG --out $R/exp_featcache/stratified_fc_vmme_nonmotion_off$ph.csv"
    } > "queue/pending/085_e03h_vmme_off$ph.sh"
  done
  echo "queued 8 E-03 harvest jobs (085_e03h_{lvb,vmme}_off*); NOTE vmme harvest covers all 179 videos (motion rows duplicate 046 and are filtered at analysis time)"
fi
