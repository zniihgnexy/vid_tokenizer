# ResNet18 Teacher Handoff

This branch is the GitHub-safe handoff bundle for the latest machine-oriented NVRC line.
It is meant to be usable on another machine even though the live `third_party/NVRC` submodule in the main working tree still points at upstream.

## Latest trustworthy milestone

- confirmed baseline: `nvrc-uvg-paper-v1`
- active route: replace the placeholder `mean_pool` teacher with a real frozen visual teacher inside the existing NVRC teacher-loss path
- bounded smoke passed in the real `NVRC` environment with `teacher_type=resnet18_imagenet`
- smoke summary:
  - `loss_value=0.3649887442588806`
  - `feature_shape=[2, 4, 512]`
  - `teacher_mse_shape=[2, 4]`
  - `psnr_shape=[2, 4]`

## What this handoff branch contains

- `tokenizer_vid/third_party/NVRC/teacher_utils.py`
- `tokenizer_vid/tools/smoke_teacher_loss.py`
- the tiny-local pilot configs under `tokenizer_vid/third_party/NVRC/scripts/configs/`
- the `l1_teacher-resnet18-bootstrap.yaml` task config for the real teacher path

## How to resume on another machine

1. Clone the repository recursively.
2. Treat the mirrored files under `tokenizer_vid/third_party/NVRC/` as the source of truth for this pass.
3. Copy or merge those mirrored files into the live `third_party/NVRC` checkout on the target machine.
4. Run the bounded smoke with:
   `conda run -n NVRC python tokenizer_vid/tools/smoke_teacher_loss.py --teacher-type resnet18_imagenet`
5. If the smoke passes, launch the next tiny-local bounded pilot using the mirrored tiny configs and `l1_teacher-resnet18-bootstrap.yaml`.

## Important caveat

This branch is a portability bundle, not a full remote copy of every local-only experiment artifact.
The live submodule still tracks upstream, so another machine should not assume the upstream submodule alone is enough for this teacher-integration pass.
