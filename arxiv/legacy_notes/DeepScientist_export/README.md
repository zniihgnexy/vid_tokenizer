# DeepScientist Export

This directory is the GitHub-safe DeepScientist snapshot for this repo.

It is meant to preserve the resumable research state without pulling the full
local `DeepScientist/` runtime, caches, logs, secrets, or large transient data
into version control.

## What this export includes

- quest-level documents such as `brief.md`, `plan.md`, `status.md`, and `SUMMARY.md`
- the active user requirements snapshot
- the active experiment `PLAN.md` and `CHECKLIST.md`
- small run snapshots such as `args.yaml` and a tailed training log
- a current-state note that explains what was running and what should happen next

## What this export does not include

- private chain-of-thought
- connector credentials, local tokens, or daemon runtime state
- the full ignored local `DeepScientist/` mirror
- datasets, large binary outputs, or caches

## Refreshing the export

Run:

```bash
bash tools/export_deepscientist_snapshot.sh
```

By default, the script reads from `/Users/wf24018/DeepScientist/quests/001` and
refreshes `DeepScientist_export/quest_001/`.
