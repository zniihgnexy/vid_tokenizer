# Main Experiment Plan

## 1. Objective

- run id: `beauty-no-teacher-comparator-v1`
- experiment tier: `auxiliary/dev`
- selected idea in `1-2` sentences:
  - Keep the same local NVRC Beauty smoke setting that already finished end to end, but turn off the teacher loss term while keeping the teacher metric path alive.
  - Use that matched comparator to test whether the teacher objective changes rate-distortion and teacher-consistency behavior on this local Apple Silicon path before spending more compute on broader runs.
- user's core requirements:
  - preserve the tokenizer branch design
  - keep the project machine-oriented rather than human-oriented
  - recommend an Anaconda or conda-managed environment
  - save code and content changes locally under `/Users/wf24018/home/vid_tokenizer`
  - ask for user approval before any GitHub push
- non-negotiable constraints:
  - baseline comparison anchor remains `nvrc-local-source`
  - the accepted baseline is attached and paper-backed, not locally reproduced on this machine
  - keep quest artifacts under the quest root even when implementation edits happen in the local repo
  - do not claim UVG comparability until both the environment and the evaluation surface support it honestly
  - keep GitHub pushes paused until the user explicitly approves one
- research question:
  - On the same bounded Beauty setting, does adding the teacher loss improve the local machine-oriented signal enough to justify further implementation effort?
- null hypothesis:
  - the teacher loss does not materially improve the local Beauty smoke relative to an otherwise matched no-teacher comparator
- alternative hypothesis:
  - the teacher-aware run yields a meaningfully better teacher-consistency metric, and possibly a better local tradeoff, than the no-teacher comparator under the same setting

## 2. Baseline And Comparability

- baseline id: `nvrc-local-source`
- baseline variant: none
- accepted comparable metric:
  - `uvg_bd_rate_reduction_pct_vs_vtm_ra_psnr`
- current non-comparable evidence:
  - the completed teacher-aware Beauty smoke finished end to end with:
    - final train `576/576`: `loss=2.5809`, `bpp=2.3976`, `psnr=14.6588`, `teacher-mse=0.0374`
    - final decoded-model aggregate eval: `bpp_avg=2.0910`, `psnr_avg=14.9552`, `teacher-mse_avg=0.0363`
    - bitstream size `17343904` bits
    - train time `5412.86s`
  - this validates the local teacher-aware NVRC path on one bounded Beauty smoke, but it is still not comparable to the accepted UVG paper contract
- comparability rule for this pass:
  - keep the dataset, frame count, patch size, model config, compression config, environment, and fallback path fixed
  - change only the teacher-loss contribution by overriding `teacher_loss_weight` from `0.2` to `0.0`
  - keep `teacher_enable=true` so `teacher-mse` remains measurable and the comparator stays informative
- exact metric keys that decide current pass value:
  - `bpp_avg`
  - `psnr_avg`
  - `teacher-mse_avg`
  - `train_time_avg`

## 3. Current Evidence And Environment Facts

- the local repo at `/Users/wf24018/home/vid_tokenizer` now has a working `NVRC` conda environment
- the full repo-local UVG frame surface is restored under `/Users/wf24018/home/vid_tokenizer/Datasets/UVG/1920x1080`
- the vendored HOME-side compatibility path resolves correctly through `/Users/wf24018/Datasets/PNG/UVG/1920x1080`
- the local repo already supports teacher-related task fields and CLI overrides through:
  - `third_party/NVRC/tasks.py`
  - `third_party/NVRC/main_utils.py`
  - `third_party/NVRC/teacher_utils.py`
- the current teacher-bootstrap task config is:
  - `third_party/NVRC/scripts/configs/tasks/overfit/l1_teacher-bootstrap.yaml`
- that config already keeps `teacher_enable=true`, `teacher_type=mean_pool`, and `teacher_loss_weight=0.2`
- because the CLI already exposes `--teacher-loss-weight`, the matched comparator does not require any new code change
- the completed teacher-aware smoke used:
  - `PYTORCH_ENABLE_MPS_FALLBACK=1`
  - `num_frames=4`
  - `Beauty`
  - patch size `1 120 120`
  - output root `/Users/wf24018/DeepScientist/quests/001/experiments/main/beauty_teacher_tiny_smoke_retry3_mpsfb`

## 4. Candidate Routes

1. Matched no-teacher comparator on the same Beauty setting.
Why it is strong:
It isolates the mechanism under the same local runtime and gives the clearest next evidence per unit time.

2. Scale the same teacher-aware run to more frames or more clips.
Why it is weaker now:
It moves toward broader evidence, but without a local comparator it still does not tell us whether the teacher term itself is helping.

3. Jump directly toward paper-facing writing.
Why it is not justified:
The current result is still a bounded smoke and needs one tighter local comparison before it can support a stronger claim.

- chosen route:
  - route 1, the matched no-teacher comparator
- why it currently dominates:
  - it preserves the same environment and data surface
  - it avoids new implementation risk
  - it answers the most important local mechanism question next

## 5. Execution Design

- minimal experiment:
  - launch one fresh Beauty smoke with the same command surface as the completed teacher-aware run
  - override `--teacher-loss-weight 0.0`
  - keep `teacher_enable=true` so `teacher-mse` remains measurable
  - write outputs under a new experiment directory
- execution command:
  - `cd /Users/wf24018/home/vid_tokenizer/third_party/NVRC && PYTORCH_ENABLE_MPS_FALLBACK=1 conda run -n NVRC python main_nvrc.py --exp-config scripts/configs/nvrc/overfit/tiny-1e.yaml --train-task-config scripts/configs/tasks/overfit/l1_teacher-bootstrap.yaml --eval-task-config scripts/configs/tasks/overfit/l1_teacher-bootstrap.yaml --compress-model-config scripts/configs/nvrc/compress_models/nvrc_tiny_s1.yaml --model-config scripts/configs/nvrc/models/teacher_tiny_32.yaml --train-dataset-dir /Users/wf24018/home/vid_tokenizer/Datasets/UVG/1920x1080 --eval-dataset-dir /Users/wf24018/home/vid_tokenizer/Datasets/UVG/1920x1080 --train-dataset Beauty --eval-dataset Beauty --start-frame 0 --num-frames 4 --train-patch-size 1 120 120 --eval-patch-size 1 120 120 --teacher-loss-weight 0.0 --output /Users/wf24018/DeepScientist/quests/001/experiments/main --exp-name beauty_no_teacher_tiny_smoke_r1_mpsfb --workers 0`
- expected outputs:
  - new experiment directory under `experiments/main/beauty_no_teacher_tiny_smoke_r1_mpsfb`
  - `args.yaml`, `rank_0/logs.txt`, checkpoint files, and result files
  - one direct local comparison against the completed teacher-aware smoke
- success criteria:
  - the comparator reaches terminal completion on the same bounded setting
  - final `bpp_avg`, `psnr_avg`, and `teacher-mse_avg` are extractable from saved result files
  - the comparison can be summarized durably without overstating paper-level significance
- abandonment or downgrade criteria:
  - if the comparator fails before the first eval boundary, stop and record the failure as runtime drift rather than mechanism evidence
  - if the comparator only partially runs, preserve the partial output and classify it honestly instead of merging it into the completed teacher-aware result

## 6. Runtime Strategy

- execution surface:
  - local repo edits stay under `/Users/wf24018/home/vid_tokenizer`
  - quest outputs stay under `/Users/wf24018/DeepScientist/quests/001`
- safe efficiency levers:
  - reuse the existing `NVRC` environment
  - reuse the restored Beauty dataset surface
  - reuse the same configs and fallback path
  - change only the teacher-loss weight and output directory
- monitoring rule:
  - launch the comparator as a detached managed run
  - treat it as slow but valid unless logs or process state show explicit failure
- live checkpoint:
  - at `2026-04-08 00:46:03` local log time, the comparator reached `144/576` with `loss=3.0573`, `bpp=2.8609`, `psnr=13.9184`, and `teacher-mse=0.0472`
  - this clears the earlier uncertainty about a silent stall and justifies continued supervision instead of a restart

## 7. Checklist Link

- checklist path:
  - `/Users/wf24018/DeepScientist/quests/001/.ds/worktrees/idea-idea-3f64faf1/CHECKLIST.md`
- next unchecked item:
  - keep supervising the matched no-teacher Beauty comparator until terminal completion or a clear failure signal

## 8. Revision Log

| Time | What changed | Why it changed | Impact on comparability or runtime |
|---|---|---|---|
| 2026-04-08 | Replaced the stale live-watch plan with a completed teacher-run summary and a matched no-teacher comparator plan | The teacher-aware Beauty smoke already finished end to end, so the old “keep supervising retry3” contract was no longer the real next step | The next compute now answers a tighter local mechanism question instead of repeating already-resolved monitoring work |
| 2026-04-08 | Recorded the first finite no-teacher comparator checkpoint at `144/576` and shifted the next action to continued supervision | The run stayed quiet for a long window, but the saved log later produced real numeric training output | Confirms the current MPS fallback run is slow but valid, so a restart would waste compute without improving evidence |
