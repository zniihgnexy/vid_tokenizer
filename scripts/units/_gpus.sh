#!/usr/bin/env bash
# _gpus.sh -- elastic GPU selection for a SHARED server. A GPU is usable only if it
# has >= MIN_MB free RIGHT NOW (never collide with other users). GPU_ALLOW (space-sep
# indices) restricts to MY allowed cards (e.g. "0 1 2 3 4 5"); empty = all.
# free_gpus MIN_MB -> usable GPU indices, most-free first.
free_gpus() {
  local min="${1:-22000}" allow="${GPU_ALLOW:-}"
  nvidia-smi --query-gpu=index,memory.free --format=csv,noheader,nounits 2>/dev/null \
    | sed 's/,//' | awk -v m="$min" -v allow="$allow" '
        BEGIN{na=split(allow,A," "); for(i=1;i<=na;i++)ok[A[i]]=1}
        ($2+0)>=m { if(na==0 || ok[$1]) print $2, $1 }' \
    | sort -rn | awk '{print $2}'
}
