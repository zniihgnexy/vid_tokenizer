# NVRC patch

`third_party/NVRC` is the upstream repository pinned as a git submodule at
`ccc432d21bdb6a04a453de588c12396d16af0d81`. All of our codec-side changes are in one patch:

```bash
bash scripts/setup_nvrc.sh          # submodule init + git apply (idempotent)
# or by hand:
cd third_party/NVRC && git apply -p1 ../../patches/nvrc_machine_oriented_pipeline.patch
```

## What the patch adds

| Area | Files (upstream-relative) | Change |
|---|---|---|
| Feature-space distortion | `losses.py`, `teacher_utils.py`, `tasks.py` | distortion measured against a frozen VLM vision encoder at one or more layers (`teacher_hidden_layer_index: 12`, `24` or `[12, 24]`) |
| Receiver-side adapter | `codec_to_vit_adapter.py`, `token_head.py`, `tasks.py` | maps decoded frames into the ViT token space; can be loaded frozen via `NVRC_FROZEN_ADAPTER` |
| Per-video delta | `tasks.py` | FiLM (or LoRA) delta on the frozen adapter, `NVRC_ADAPTER_DELTA=film`, entropy-coded and counted in the bitstream; learning rate `NVRC_ADAPTER_LR` (default 1e-3) |
| Logging | `main_utils.py` | heatmaps handle multi-layer targets |
| Codec plumbing | `main_nvrc.py`, `models/hinerv.py`, `models/__init__.py`, `compress_models/__init__.py`, `utils.py` | wiring for the teacher pathway and token export |
| Exploratory teachers | `l1_teacher-resnet18-*`, `l1_teacher-dinov2-*`, `l1_teacher-bootstrap.yaml`, tiny debug configs | earlier experiments, not used in the paper |
| Task configs | `scripts/configs/tasks/overfit/l1_teacher-pathway-b-mid-*.yaml` | rate rungs (`lamb006` … `lamb150`), final-layer (`final-*`), multi-layer (`Nmulti`, `N1224` and per-rung `*-N1224`) |
| Model configs | `scripts/configs/nvrc/models/teacher_cap_*.yaml` | codec capacity points (`r1` is the paper setting) |

The patch was regenerated for this release with `diff -ruN upstream ours` from the working tree used
for the experiments, and it applies cleanly to the pinned commit. Two edits were replayed from our
patch scripts rather than copied from the server (adapter learning-rate env var, multi-layer
heatmap); they should be diffed against the server's `third_party/NVRC` before the camera-ready.
