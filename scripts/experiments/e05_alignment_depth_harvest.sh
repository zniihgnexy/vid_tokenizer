#!/usr/bin/env bash
# e05_alignment_depth_harvest.sh -- E-05 alignment-depth ablation harvests on the VMME motion-115 pool (per-video adapter runs):
#   C1 final-layer (Latent-INR-style) cap_r1 phases 1-3 (phase 0 exists), final cap_r1_lamb025 phases 0-3,
#   C2 multi-layer ours cap_r1_nmulti phases 0-3. Codec-only (--no-oracle); oracle rows come from the main harvests.
cd /home/xinyizheng/vid_tokenizer || exit 1
R=/mnt/nas/xinyizheng/vidtok_out/gate1_vmme; mkdir -p queue/pending
ENV='set -uo pipefail
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
export PYTHONPATH=src PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True HF_HOME=/mnt/nas/xinyizheng/.hfcache TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 INTERNVL_MODEL_PATH=/mnt/nas/xinyizheng/InternVL2_5-8B'
job(){ # job <name> <interface> <rate> <phase>
  { echo "#Q minmb=24000 share=2"; echo "$ENV"; echo "export QA_SAMPLE_OFFSET=$4"
    echo "python tools/harvest_stratified.py --dataset vmme_long_motion --out-root $R --manifest-dir outputs/datasets/vmme_long_motion --manifest-file questions.jsonl --interface $2 --rates $3 --no-oracle --crfs __none__ --out $R/stratified_${2}_${3}_off$4.csv"
  } > "queue/pending/$1.sh"
}
n=0
for ph in 1 2 3; do job 075_e05h_final_cap_r1_off$ph final cap_r1 $ph; n=$((n+1)); done
for ph in 0 1 2 3; do job 075_e05h_final_lamb025_off$ph final cap_r1_lamb025 $ph; n=$((n+1)); job 075_e05h_nmulti_off$ph ours cap_r1_nmulti $ph; n=$((n+1)); done
echo "queued $n E-05 harvest jobs (075_e05h_*)"
