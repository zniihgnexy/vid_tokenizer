#!/usr/bin/env bash
# e04_featcache_baselines.sh fit|grid0|grid1|pareto|ae -- E-04 feature-cache compression baselines (MASTER_PLAN §3.1, D-013).
#   fit     070: fit the shared book on the 32 universal-adapter donors -> R/exp_featcache/featcodec_internvl_v1.pt
#   grid0   071: phase-0 harvest of the full zero-training grid on Ego c100 + VMME motion-115
#   pareto  072: 4-phase harvest of the Pareto cells (PARETO_SPECS env, space separated)
# Harvest jobs wait (<= 3 h) for the book to appear so they can be queued together with the fit.
cd /home/xinyizheng/vid_tokenizer || exit 1
R=/mnt/nas/xinyizheng/vidtok_out; FC=$R/exp_featcache; BOOK=$FC/featcodec_internvl_v1.pt
MODE="${1:-grid0}"; mkdir -p queue/pending "$FC"
ENV='set -uo pipefail
cd /home/xinyizheng/vid_tokenizer
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
export PYTHONPATH=src PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True HF_HOME=/mnt/nas/xinyizheng/.hfcache TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 INTERNVL_MODEL_PATH=/mnt/nas/xinyizheng/InternVL2_5-8B'
WAIT="for i in \$(seq 1 180); do [ -f $BOOK ] && break; sleep 60; done; [ -f $BOOK ] || { echo 'book missing after 3h'; exit 1; }"
# phase-0 grid: pool K x PCA d x quantiser (bits before entropy coding: K*d*b/65536 bpp)
GRID_P64="p64_pca16_q4 p64_pca16_q2 p64_pca64_q4 p64_pca64_q2 p64_pca64_pq8 p64_pca64_pq16 p64_pca256_q4 p64_pca256_pq16 p64_pca16_q4_t p64_pca64_q4_t p64_fp16"
GRID_P16="p16_pca16_q8 p16_pca16_q4 p16_pca64_q8 p16_pca64_q4 p16_pca64_q4_t p16_pca64_pq8 p16_pca256_q4 p16_pca256_pq16 p16_q8 p16_pq32 p16_fp16"
GRID_P256="p256_pca16_q2 p256_pca16_q4_t p256_pca64_q2_t p256_fp16"
GRID="$GRID_P64 $GRID_P16 $GRID_P256"
# grid1 (after the Ego grid0 front, 10-17): the front rises with more tokens + PCA-64/256, so extend it in 0.1-2 bpp
GRID1="p256_pca64_pq8 p256_pca64_pq16 p256_pca64_q2 p256_pca64_q4 p256_pca256_pq16 p256_pca256_pq32 p256_pca256_q2 p64_pca256_pq32 p64_pca256_q2 p64_pca256_q8"
harvest_job(){ # harvest_job <name> <ego|vmme> <phase> <specs...>
  local name="$1" ds="$2" ph="$3"; shift 3
  if [ "$ds" = ego ]; then
    local D="--dataset egoschema --out-root $R/u_egos --manifest-dir outputs/datasets/egoschema --manifest-file manifest.jsonl --uuids-file outputs/gate1_egos/common100_uuids.txt"
  else
    local D="--dataset vmme_long_motion --out-root $R/u_vmme --manifest-dir outputs/datasets/vmme_long_motion --manifest-file questions.jsonl --uuids-file outputs/datasets/vmme_long_motion/motion115_uuids.txt"
  fi
  { echo "#Q minmb=24000 share=2"; echo "$ENV"; echo "$WAIT"; echo "export QA_SAMPLE_OFFSET=$ph"
    echo "python tools/featcache_harvest.py $D --book $BOOK --specs $* --out $FC/stratified_fc_${ds}_off$ph.csv"
  } > "queue/pending/$name.sh"
}
case "$MODE" in
  fit)
    { echo "#Q minmb=24000 share=2"; echo "$ENV"
      echo "python tools/featcache_fit.py --donors-file outputs/featcache/donors.txt --out $BOOK"
    } > queue/pending/070_e04_fit.sh; echo "queued 070_e04_fit";;
  grid0)
    harvest_job 071_e04h_ego_off0 ego 0 $GRID; harvest_job 071_e04h_vmme_off0 vmme 0 $GRID
    echo "queued 071_e04h_{ego,vmme}_off0 ($(echo $GRID | wc -w) specs)";;
  grid1)
    harvest_job 071b_e04h_ego_off0 ego 0 $GRID1; harvest_job 071b_e04h_vmme_off0 vmme 0 $GRID1
    # separate output files so grid0 results are never overwritten
    sed -i "s#stratified_fc_\(ego\|vmme\)_off0.csv#stratified_fc1_\1_off0.csv#" queue/pending/071b_e04h_ego_off0.sh queue/pending/071b_e04h_vmme_off0.sh
    echo "queued 071b_e04h_{ego,vmme}_off0 ($(echo $GRID1 | wc -w) specs)";;
  ae)   # B4 (D-017): learned autoencoder cells, 4 phases, both pools; models = $FC/ae/*.pt at generation time
    AEM=$(ls $FC/ae/p*_ae_*.pt 2>/dev/null | tr "\n" " "); [ -n "$AEM" ] || { echo "no AE models in $FC/ae"; exit 1; }
    for ph in 0 1 2 3; do
      for ds in ego vmme; do
        harvest_job 086_e04ae_${ds}_off$ph $ds $ph __dummy__
        sed -i "s#--specs __dummy__#--ae-models $AEM#; s#stratified_fc_${ds}_off$ph.csv#stratified_fcae_${ds}_off$ph.csv#" queue/pending/086_e04ae_${ds}_off$ph.sh
      done
    done
    echo "queued 086_e04ae_{ego,vmme}_off{0..3} ($(echo $AEM | wc -w) models)";;
  pareto)
    [ -n "${PARETO_SPECS:-}" ] || { echo "set PARETO_SPECS"; exit 1; }
    for ph in 1 2 3; do harvest_job 072_e04h_ego_off$ph ego $ph $PARETO_SPECS; harvest_job 072_e04h_vmme_off$ph vmme $ph $PARETO_SPECS; done
    echo "queued 072_e04h_{ego,vmme}_off{1,2,3}";;
  *) echo "usage: $0 fit|grid0|pareto"; exit 2;;
esac
