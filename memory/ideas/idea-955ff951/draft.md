---
id: idea-955ff951-draft
type: ideas
kind: idea_draft
title: Chunk-Aware Local-Burst Packet Interface Draft
idea_id: idea-955ff951
quest_id: '002'
scope: quest
branch: idea/002-idea-955ff951
worktree_root: /home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-955ff951
next_target: implement a chunk-aware bundle/evaluator with explicit burst grouping
  and local frame order.
method_brief: Keep the same frozen chunked export, but replace flat global matching
  with a chunk-aware bundle and consumer.
selection_scores: null
mechanism_family: chunk-aware packet interface
change_layer: null
source_lens: null
foundation_ref:
  kind: branch
  ref: idea-e0d17d22
  branch: idea-e0d17d22
  worktree_root: null
  label: Branch `idea-e0d17d22`
foundation_reason: null
lineage_intent: continue_line
created_at: '2026-04-15T09:35:06+00:00'
updated_at: '2026-04-15T09:35:06+00:00'
tags:
- branch:idea/002-idea-955ff951
- idea-draft
- lineage:continue_line
---
# Chunk-Aware Local-Burst Packet Interface

## Executive Summary

Global widened results regress to near chance, but per-chunk delta signal remains partially alive, so a structured local-burst reformulation is more justified than either stopping or claiming success.

## Limitation / Bottleneck

The widened 16-frame flat retrieval surface collapses to near chance even though some 4-frame chunks still preserve delta-first signal.

## Selected Claim

Preserving burst grouping and local position in the downstream packet interface will retain the surviving local signal better than flat clip-level retrieval.

## Theory and Method

Represent each frozen 4-frame chunk as a first-class packet group and evaluate chunk-aware matching before clip-level aggregation.

## Method Brief

Keep the same frozen chunked export, but replace flat global matching with a chunk-aware bundle and consumer.

## Selection Scores

- Not recorded

## Diversity Tags

- Mechanism family: chunk-aware packet interface
- Change layer: Not recorded
- Source lens: Not recorded

## Code-Level Change Plan

Represent each frozen 4-frame chunk as a first-class packet group and evaluate chunk-aware matching before clip-level aggregation.

## Evaluation / Falsification Plan

Turns the current mixed widened result into a more defensible interface question instead of forcing an unsupported flat retrieval claim.

## Risks / Caveats / Implementation Notes

- The remaining signal may be too burst-specific.
- Chunk-aware packaging may improve interpretation without improving usefulness.

## Evidence / References

- None recorded yet.

## Foundation Choice

- Lineage intent: `continue_line`
- Foundation: `Branch `idea-e0d17d22``
- Reason: Use the current active foundation.

## Next Target

implement a chunk-aware bundle/evaluator with explicit burst grouping and local frame order.
