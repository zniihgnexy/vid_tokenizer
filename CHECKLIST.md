# Main Experiment Checklist

Update this while planning, modifying code, running pilots, monitoring the full run, and validating the result.

## Identity

- run id: `shared_gating_interface_export_ego4d16f_smoke_r1`
- idea id: `idea-e0d17d22`
- stage: `experiment_prep`

## Planning

- [x] selected idea summarized in `1-2` sentences
- [x] parent-line evidence and baseline contract confirmed
- [x] bridge-specific risks listed
- [x] widened bounded sample surface chosen
- [x] widened-surface manifest or sample list written
- [x] reusable tiny config family recovered
- [x] exact widened rerun command shape chosen

## Implementation

- [x] bounded frame extraction helper implemented
- [x] local 16-frame bounded dataset generated
- [ ] widened export smoke launch script written
- [ ] control docs synced to the widened rerun route
- [x] risky logic sanity-checked for dataset/config alignment

## Pilot / Smoke

- [ ] widened upstream smoke command executed
- [ ] new `args.yaml` written under the widened output root
- [ ] output tree contains bitstream, decoded, eval, and results summaries
- [ ] metric keys match the old 4-frame export contract

## Validation

- [ ] widened bundle is ready for reconstructed and teacher interface exporters
- [ ] comparison against the old 4-frame export is interpretable
- [ ] next bridge-eval action after the widened smoke is explicit

## Notes

- old 4-frame export control:
  - `bpp_avg=88.2266`
  - `psnr_avg=10.9012`
  - `teacher-mse_avg=0.5126`
- parent-line downstream control:
  - `reconstructed_to_original_top1_accuracy=0.25`
  - `reconstructed_to_original_mean_match_rank=2.5`
- current 4-frame bridge smoke:
  - `pred_feat_to_target_feat_direct_top1_accuracy=0.25`
  - `pred_delta_to_target_feat_direct_top1_accuracy=0.5`
  - `delta_ridge_to_target_feat_loo_top1_accuracy=0.0`
  - `feat_plus_8p0x_delta_ridge_to_target_feat_loo_top1_accuracy=0.0`
- current widened surface:
  - dataset: `tmp/ego4d_bounded_bridge_r1/data/ego4d_small_bridge_16f`
  - shape: `16 x 32 x 32`
- recovered config family:
  - `tiny_local.yaml`
  - `tiny-1e.yaml`
  - `teacher_tiny_32.yaml`
  - `nvrc_tiny_s1.yaml`
  - `l1_teacher-resnet18-shared-semchange-delta.yaml`
- branch meaning:
  - the 4-frame bridge result stays as the bounded positive signal
  - the immediate blocker is now widened upstream export, not another 4-frame bridge tweak
  - the next bridge comparison depends on a successful widened export bundle
- next unchecked item:
  - write and execute the widened frozen export smoke entrypoint
