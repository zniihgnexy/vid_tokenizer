---
id: idea-e0d17d22
type: ideas
kind: idea
title: Delta-Packet Bridge to Frozen Consumer Space
quest_id: '002'
scope: quest
branch: idea/002-idea-e0d17d22
worktree_root: /home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-e0d17d22
next_target: prepare the bounded delta-packet bridge experiment package on a wider
  surface and compare delta-only, delta-dominant concat, and reconstructed-video control
  under one frozen consumer space
method_brief: 'Build a delta-packet bridge rather than another pure packet-similarity
  check: widen the bounded surface, compare reconstructed-video control against delta-only
  and delta-dominant concat bridge variants, and keep static-context sidecar fusion
  only as a deferred control if the primary bridge stabilizes.'
selection_scores:
  winner: candidate_b_delta_packet_bridge
  candidate_a: required robustness sub-check inside the first experiment package
  candidate_c: deferred because local evidence already shows static-heavy fusion can
    hurt
mechanism_family: delta_packet_consumer_bridge
change_layer: downstream_consumer_bridge
source_lens: local_evidence_plus_temporal_motion_literature
foundation_ref:
  kind: idea
  ref: idea-6bfed938
  branch: idea/002-idea-6bfed938
  worktree_root: /home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-6bfed938
  idea_id: idea-6bfed938
  label: Idea `idea-6bfed938` on `idea/002-idea-6bfed938`
foundation_reason: Use the current active head as the foundation because it already
  isolated the winning temporal-change signal and ruled out plain static packet as
  the default interface. The clean next move is a child line that changes only the
  downstream bridge layer.
lineage_intent: continue_line
created_at: '2026-04-15T08:16:07+00:00'
updated_at: '2026-04-15T08:16:07+00:00'
tags:
- branch:idea/002-idea-e0d17d22
- next:prepare the bounded delta-packet bridge experiment package on a wider surface
  and compare delta-only, delta-dominant concat, and reconstructed-video control under
  one frozen consumer space
- lineage:continue_line
- family:delta-packet-consumer-bridge
---
# Delta-Packet Bridge to Frozen Consumer Space

## Problem

The delta-first packet follow-up stabilized on the frozen 4-frame surface: `delta-only` and `8x delta concat` both reach top-1 0.75 with mean rank 1.25, while reconstructed-video control and plain static packet stay at 0.25 and naive weighted fusion drops to 0.5. The current line still stops at packet-to-packet similarity, so the next child line must convert the validated temporal-change packet into a true downstream consumer-facing interface without assuming a full external foundation-model stack.

## Hypothesis

If the machine-facing signal is concentrated in temporal change, then a lightweight temporal adapter that maps delta-dominant packets into a frozen consumer embedding space will preserve downstream retrieval/probing structure more faithfully than reconstructed video or static-heavy packet fusion under the same frozen upstream contract.

## Mechanism

Freeze the upstream codec and the current packet exporter, keep temporal delta as the primary payload, and add a small consumer-side bridge that reads delta-only or delta-dominant packet sequences and emits consumer-facing embeddings for bounded retrieval or probing. The first experiment package should widen the bounded sample surface while keeping the same comparison contract so adapter gains are not confounded with a changed evaluation surface.

## Method Brief

Build a delta-packet bridge rather than another pure packet-similarity check: widen the bounded surface, compare reconstructed-video control against delta-only and delta-dominant concat bridge variants, and keep static-context sidecar fusion only as a deferred control if the primary bridge stabilizes.

## Expected Gain

Move the project from packet similarity into a runnable machine-facing bridge layer, while preserving the local dependency boundary and the current delta-first evidence. This is the smallest credible step toward the user's longer-term foundation-model pipeline goal.

## Selection Scores

- winner: candidate_b_delta_packet_bridge
- candidate_a: required robustness sub-check inside the first experiment package
- candidate_c: deferred because local evidence already shows static-heavy fusion can hurt

## Diversity Tags

- Mechanism family: delta_packet_consumer_bridge
- Change layer: downstream_consumer_bridge
- Source lens: local_evidence_plus_temporal_motion_literature

## Decision Reason

Three serious candidates were considered: A) only widen the current delta validation surface, B) promote delta packets into a lightweight frozen-consumer bridge, and C) add a static-context sidecar with gated fusion. B wins because it keeps the incumbent delta-first signal, advances the user-requested pipeline-building goal, and stays feasible with the repo's current assets; A is too conservative as the sole next line, and C adds a new confound before the simpler bridge is tested.

## Foundation

- Lineage Intent: `continue_line`
- Kind: `idea`
- Ref: `idea-6bfed938`
- Branch: `idea/002-idea-6bfed938`
- Worktree: `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-6bfed938`
- Reason: Use the current active head as the foundation because it already isolated the winning temporal-change signal and ruled out plain static packet as the default interface. The clean next move is a child line that changes only the downstream bridge layer.

## Risks

- The current evidence still comes from a tiny 4-frame surface, so the first adapter experiment can overfit unless the bounded surface is widened immediately.
- The repo does not yet contain a reusable large-model dependency path, so the bridge must stay lightweight and local in this round.
- Static context may still matter, but current evidence says adding it too early can reintroduce noise.

## Evidence Paths

- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-44a0e404/experiments/main/evals/delta_dominant_teacher_packet_followup_r1/summary.json`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-44a0e404/artifacts/ideas/literature_survey.md`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-44a0e404/memory/ideas/idea-44a0e404/idea.md`

## Next Target

prepare the bounded delta-packet bridge experiment package on a wider surface and compare delta-only, delta-dominant concat, and reconstructed-video control under one frozen consumer space
