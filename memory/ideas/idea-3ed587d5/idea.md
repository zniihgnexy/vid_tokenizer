---
id: idea-3ed587d5
type: ideas
kind: idea
title: From Machine-Oriented Video Compression to a Usable Downstream Pipeline
quest_id: '002'
scope: quest
branch: idea/002-idea-3ed587d5
worktree_root: /home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-3ed587d5
next_target: experiment
method_brief: 'Candidate A wins this round: do not reopen upstream codec-line ranking.
  Instead, treat the current compression module as a frozen upstream asset, package
  a machine-facing interface, and run one minimal downstream task with a frozen consumer
  model. Start from reconstructed video plus aligned metadata because it is the least
  confounded and most compatible with the current asset bundle; defer feature-packet
  transfer and direct VLM/LLM semantic-packet demos to later rounds.'
selection_scores: null
mechanism_family: machine_facing_downstream_interface
change_layer: null
source_lens: null
foundation_ref:
  kind: idea
  ref: idea-9948c3dd
  branch: idea/002-idea-9948c3dd
  worktree_root: /home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-9948c3dd
  idea_id: idea-9948c3dd
  label: Idea `idea-9948c3dd` on `idea/002-idea-9948c3dd`
foundation_reason: The user frames the next step as a new quest rather than an extension
  of the old compression question. Within the current runtime, the clean equivalent
  is to open a new durable line from the confirmed upstream asset instead of revising
  the old variant-ranking question in place.
lineage_intent: continue_line
created_at: '2026-04-14T14:40:36+00:00'
updated_at: '2026-04-14T14:40:36+00:00'
tags:
- branch:idea/002-idea-3ed587d5
- next:experiment
- lineage:continue_line
- family:machine-facing-downstream-interface
---
# From Machine-Oriented Video Compression to a Usable Downstream Pipeline

## Problem

The current quest validates a machine-oriented compression/tokenizer line and teacher-consistency feasibility, but it still lacks a stable machine-facing downstream interface and an end-to-end downstream evaluation surface.

## Hypothesis

If the inherited upstream compression line is frozen and exported first as reconstructed clips plus aligned metadata, then a frozen egocentric downstream consumer can retain enough utility relative to original video to justify further feature-packet or larger-model integration.

## Mechanism

Freeze the inherited checkpoint/config/data subset, define a first export schema around reconstructed video and aligned metadata, compare original-vs-reconstructed downstream utility with one frozen retrieval or classification consumer, and only then extend toward feature packets or larger multimodal interfaces.

## Method Brief

Candidate A wins this round: do not reopen upstream codec-line ranking. Instead, treat the current compression module as a frozen upstream asset, package a machine-facing interface, and run one minimal downstream task with a frozen consumer model. Start from reconstructed video plus aligned metadata because it is the least confounded and most compatible with the current asset bundle; defer feature-packet transfer and direct VLM/LLM semantic-packet demos to later rounds.

## Expected Gain

This route should deliver the first runnable end-to-end pipeline, the first result batch on original-vs-reconstructed downstream utility, and a cleaner decision surface for whether a more machine-native feature-packet or larger-model interface is worth pursuing next.

## Selection Scores

- Not recorded

## Diversity Tags

- Mechanism family: machine_facing_downstream_interface
- Change layer: Not recorded
- Source lens: Not recorded

## Decision Reason

Serious candidates were: A) reconstructed video plus aligned metadata with a frozen downstream consumer, B) tokenizer/teacher feature packet with a lightweight transfer head, and C) direct semantic-packet to VLM/LLM demo. A wins because it preserves the frozen-upstream contract, gives the least confounded first experiment, and matches the current asset bundle. B is more machine-native but currently lacks maintained export hooks and would add too much new plumbing in round one. C is attractive as a demo but too ambiguous for the first scientific checkpoint because failures would be hard to attribute across compression, interface, and prompting.

## Foundation

- Lineage Intent: `continue_line`
- Kind: `idea`
- Ref: `idea-9948c3dd`
- Branch: `idea/002-idea-9948c3dd`
- Worktree: `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-9948c3dd`
- Reason: The user frames the next step as a new quest rather than an extension of the old compression question. Within the current runtime, the clean equivalent is to open a new durable line from the confirmed upstream asset instead of revising the old variant-ranking question in place.

## Risks

- The first-stage novelty is more about interface and pipeline value than a new compression algorithm.
- The imported baseline package does not yet expose maintained downstream-task hooks.
- The feature-packet route remains higher risk until the basic pipeline is stable.

## Evidence Paths

- `artifacts/ideas/literature_survey.md`
- `baselines/imported/nvrc-local-source/json/metric_contract.json`
- `baselines/imported/nvrc-local-source/verification.md`
- `memory/knowledge/active-user-requirements.md`

## Next Target

experiment
