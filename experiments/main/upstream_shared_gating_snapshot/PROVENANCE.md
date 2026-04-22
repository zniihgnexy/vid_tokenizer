# Frozen Upstream Provenance

This snapshot exists to make quest 002 self-contained while keeping the inherited
compression route frozen.

## Origin

- upstream source snapshot copied from the verified local NVRC tree used in quest 001
- inherited research line: `shared_semantic_gated_dual_path_tiny_local_r1`
- inherited checkpoint anchor:
  `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/001/.ds/worktrees/shared-semantic-gated-dual-path-tiny-local-r1/experiments/main/shared_semantic_gated_dual_path_tiny_local_r1/checkpoints/0000/pytorch_model.bin`

## Why This Snapshot Exists

- quest 002 needs a rerunnable, GitHub-shareable upstream module
- the accepted baseline package in quest 002 contains metrics and contracts, not a runnable source tree
- the downstream-interface round should inherit the upstream module rather than reopen codec-line ranking

## Current Execution Contract

- do not make research-level algorithm changes inside this snapshot during the downstream bootstrap round
- use `--resume ... --resume-model-only true --eval-only true` to reload the inherited checkpoint and regenerate paired outputs
- do not rely on the commented `--bitstream` restore stub as a decode-only path

## Verified Quest-002 Bootstrap Result

- quest-local eval-only export smoke completed successfully
- reproduced aggregate metrics:
  - `bpp_avg=88.2266`
  - `psnr_avg=10.9012`
  - `teacher-mse_avg=0.5126`
- validated interface bundle now exists with:
  - paired original and reconstructed frames
  - per-frame metrics
  - aggregate metrics manifest

## Next Intended Use

- keep this snapshot frozen
- build the first downstream machine-consumer comparison on top of the exported interface bundle
