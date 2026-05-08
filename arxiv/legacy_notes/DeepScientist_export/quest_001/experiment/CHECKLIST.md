# Main Experiment Checklist

## Identity

- run id: `beauty-no-teacher-comparator-v1`
- idea id: `idea-3f64faf1`
- branch: `idea/001-idea-3f64faf1`
- stage: `experiment`

## Planning

- [x] selected idea summarized in `1-2` sentences
- [x] baseline and comparability contract confirmed
- [x] completed teacher-aware Beauty smoke result extracted from saved files
- [x] strongest next route chosen explicitly
- [x] no-push-without-approval rule kept active

## Comparator Design

- [x] same dataset and frame count preserved
- [x] same model and compression configs preserved
- [x] same fallback path preserved
- [x] teacher metric path kept measurable
- [x] comparator change narrowed to `teacher_loss_weight=0.0`
- [x] fresh output directory chosen

## Execution

- [x] launch `beauty_no_teacher_tiny_smoke_r1_mpsfb`
- [x] confirm new output directory and first log lines exist
- [x] confirm the first train checkpoint is finite
- [ ] keep GitHub pushes paused until user approval is requested and granted

## Validation

- [ ] comparator reaches terminal completion
- [ ] saved result files contain `bpp_avg`
- [ ] saved result files contain `psnr_avg`
- [ ] saved result files contain `teacher-mse_avg`
- [ ] teacher-aware vs no-teacher comparison summarized durably

## Current Next Step

- [ ] keep the matched no-teacher Beauty comparator under watch until terminal completion or a clear failure signal
