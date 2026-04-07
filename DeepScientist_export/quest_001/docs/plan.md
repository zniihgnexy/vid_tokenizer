# Idea Plan

## Objective

Select the first literature-grounded machine-oriented direction relative to the accepted NVRC baseline, then hand off cleanly into experiment planning.

## Strongest Evidence And Sources

- Accepted attached baseline: `nvrc-local-source`.
- Fixed project definition in the user repository: keep `x -> NVRC -> x_hat` and preserve machine representations through a teacher/tokenizer branch.
- Durable idea survey: `artifacts/idea/literature_survey.md`.
- Code feasibility finding: the user repository contains project-definition documents plus vendored NVRC code, and NVRC already exposes an extensible task/loss path in `third_party/NVRC/tasks.py`.

## Constraints And Comparability Rules

- Keep the project machine-oriented; do not collapse into human-oriented compression.
- Keep the first direction compatible with the accepted NVRC comparison anchor.
- Do not replace the project with direct feature compression or task-aware control as the main story.
- Do not introduce a new dataset or an unrelated evaluation regime in the first direction.
- Preserve the caveat that the baseline is attached and paper-backed, not locally reproduced on this machine.
- Prefer an Anaconda or conda-managed environment for local implementation and reproducibility work.
- Save implementation changes in the local project tree at `/Users/wf24018/home/vid_tokenizer` while keeping quest artifacts under the quest root.
- Do not push project changes to GitHub unless the user has reviewed the changes and explicitly approved the push.

## Candidate Routes

1. Add a frozen global teacher consistency loss on reconstructed video.
2. Add dense patch-token or hidden-state consistency.
3. Add multi-teacher sampling or teacher randomization.

## Chosen Route

Chosen route: keep the NVRC reconstruction/rate backbone and add a frozen global teacher consistency loss between original and reconstructed video representations.

Why this route currently dominates:

- It is the closest route to the fixed project definition.
- It best matches the current codebase boundary.
- It is easier to defend as a clean first paper step than direct feature compression or task-aware encoder control.
- It is smaller and safer than dense token supervision or multi-teacher training.

## Success Criteria

- The literature floor is durable and explicit.
- The serious frontier is reduced to `2-3` candidates with clear tradeoffs.
- One selected idea is submitted durably as a new research line.
- The next anchor becomes `experiment` with a concrete implementation plan.

## Downgrade Or Abandonment Criteria

- If the chosen teacher path requires global context that cannot be integrated cleanly into the current NVRC task pipeline, downgrade to a simpler pooled representation.
- If a closer prior paper invalidates the current claim framing, narrow the claim to transfer-to-INR value rather than novelty.
- If the first teacher route becomes too expensive or too model-specific, revisit dense or multi-teacher routes only after the single-teacher path is concretely blocked.

## Recommended Next Anchor

Submit the selected idea durably, seed a lightweight outline candidate, and continue into experiment planning for the smallest credible implementation pass.

## Added Follow-Up Tasks For Remote GPU Migration

Date added: 2026-04-08

1. Prepare the code repo for a clean GitHub-backed handoff.
- Keep code, docs, setup notes, and helper scripts in the main repo.
- Keep datasets, outputs, local runtime state, and scratch folders out of GitHub.

2. Preserve the NVRC experiment changes with real Git history.
- Create or choose a user-controlled remote for `third_party/NVRC`.
- Commit the local teacher-consistency code and config changes there.
- Update the parent repo submodule pointer only after that commit is reachable remotely.

3. Prepare the SSH-only GPU bootstrap path.
- Clone the parent repo recursively on the new machine.
- Rebuild the conda environment with a GPU-appropriate PyTorch install.
- Restore or redownload the UVG dataset surface there.

4. Preserve durable DeepScientist quest history outside the code repo.
- Sync quest documents, artifacts, baselines, experiments, literature, and memory when exact research continuity is needed.
- Treat live local runs as non-resumable processes and restart from durable outputs if needed.

5. Keep GitHub pushes approval-gated.
- Before any push, present the proposed parent-repo and NVRC-submodule commits for user review and approval.
