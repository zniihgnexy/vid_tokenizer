# Baseline Verification

## Conclusion

`nvrc-local-source` is accepted again for the current quest.
The current machine now has both a repaired real-teacher smoke path and one bounded `main_nvrc.py` pilot that completes the train -> encode -> decode -> re-evaluate loop.

## What Was Verified

1. `main_nvrc.py --help` runs in the `NVRC` conda environment.
2. `tools/smoke_teacher_loss.py` runs with `mean_pool`.
3. `tools/smoke_teacher_loss.py --teacher-type resnet18_imagenet` runs with feature shape `[2, 4, 512]` and `loss_value=0.3541456162929535`.
4. A bounded tiny-local pilot runs through the real NVRC entrypoint with the repaired `resnet18_imagenet` teacher path.

## Current-Machine Pilot

- output root: `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/001/experiments/main/teacher_tiny_local_pilot_r3`
- result file: `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/001/experiments/main/teacher_tiny_local_pilot_r3/results/all.txt`
- checkpoint root: `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/001/experiments/main/teacher_tiny_local_pilot_r3/checkpoints/0000`
- bitstream root: `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/001/experiments/main/teacher_tiny_local_pilot_r3/bitstreams`

Aggregated metrics:

- `size=361312`
- `bpp_avg=88.2109`
- `bpp_est_avg=93.7221`
- `psnr_avg=10.8996`
- `teacher-mse_avg=0.5145`
- `train_time_avg=1.8261`
- `ent_enc_time_avg=8.1575`
- `ent_dec_time_avg=14.1926`

## Repair Notes

- The remote handoff bundle was trustworthy but incomplete for the current local tree because it did not include the missing `tasks.py` and `main_utils.py` teacher wiring.
- The local repair also needed one extra compatibility fix so `OverfitTask` accepts both scalar `lamb` and single-element list `lamb`.

## Caveats

- The accepted paper-facing comparator remains the NVRC paper's UVG Random Access surface.
- The current quest's tiny-local result is a feasibility and bootstrap signal only.
- These tiny-local numbers should not be presented as paper-comparable benchmark evidence.

## Recommended Next Anchor

Move to the `idea` stage.
The baseline question is now settled enough to start choosing the first tokenizer-consistency improvement direction on top of this repaired and locally verified NVRC line.
