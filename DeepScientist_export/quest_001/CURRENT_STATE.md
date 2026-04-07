# Quest 001 Current State

Snapshot intent: let another machine resume the same research line from GitHub
without needing the full local DeepScientist runtime tree.

## Current route

- quest: `001`
- goal: machine-oriented video tokenizer / NVRC direction
- stage: `experiment`
- active idea: frozen-teacher consistency on top of the NVRC reconstruction-rate backbone
- confirmed baseline: `nvrc-local-source`

## Active experiment status

- active run: matched no-teacher Beauty comparator
- run name: `beauty_no_teacher_tiny_smoke_r1_mpsfb`
- status at snapshot time: running, slow but valid on the current Apple Silicon machine
- latest finite checkpoint observed from the saved log:
  - log time: `2026-04-08 00:46:03`
  - progress: `144/576`
  - `loss=3.0573`
  - `bpp=2.8609`
  - `psnr=13.9184`
  - `teacher-mse=0.0472`

## Git and portability state

- parent repo commit verified on `origin/main`: `9c4a934` (`docs: add remote gpu handoff prep`)
- the parent-repo GitHub handoff files are present and coherent
- the local `third_party/NVRC` submodule still contains local research edits that are not preserved by the parent repo alone
- another machine should read `REMOTE_GPU_PREPARATION.md` before assuming the NVRC submodule state is complete

## Resume guidance

1. Clone the repo and read `REMOTE_GPU_PREPARATION.md`.
2. Read the quest documents under `DeepScientist_export/quest_001/docs/`.
3. Read the active experiment files under `DeepScientist_export/quest_001/experiment/`.
4. Inspect the copied run snapshot under `DeepScientist_export/quest_001/run_snapshots/`.
5. Preserve or fork the NVRC submodule changes before expecting identical teacher-consistency behavior on another machine.

## Explicit limit

This export contains durable research state, not private chain-of-thought.
The practical resume surface is the combination of quest documents, experiment
control files, run snapshots, and the migration note.
