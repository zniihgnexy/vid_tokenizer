#!/usr/bin/env bash
# Fetch InternVL3.5-8B weights to NAS with patient, indefinite retries (outbound TLS to
# huggingface.co / hf-mirror.com is intermittent from this host). Alternates endpoints,
# resumes partial files, sleeps 5 min between failed attempts. Stop: touch STOP_FETCH_IVL35
sleep 20
source ~/anaconda3/etc/profile.d/conda.sh && conda activate nvrc
export HF_HOME=/mnt/nas/xinyizheng/.hfcache HF_HUB_OFFLINE=0 TRANSFORMERS_OFFLINE=0 HF_HUB_ENABLE_HF_TRANSFER=0 HF_HUB_DOWNLOAD_TIMEOUT=60
DST=/mnt/nas/xinyizheng/InternVL3_5-8B
cd /home/xinyizheng/vid_tokenizer
for i in $(seq 1 500); do
  [ -f STOP_FETCH_IVL35 ] && { echo "stop file found"; exit 0; }
  if [ $((i % 2)) = 1 ]; then EP=https://hf-mirror.com; else EP=https://huggingface.co; fi
  echo "attempt $i via $EP $(date '+%m-%d %H:%M')"
  HF_ENDPOINT=$EP timeout 3600 huggingface-cli download OpenGVLab/InternVL3_5-8B --local-dir "$DST" --max-workers 2 \
    && { echo "DONE $(date)"; du -sh "$DST"; ls "$DST"/*.safetensors; exit 0; }
  echo "  failed; have: $(du -sh $DST 2>/dev/null | cut -f1)"
  sleep 300
done
echo "GAVE UP $(date)"
