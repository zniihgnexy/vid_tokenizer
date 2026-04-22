---
id: idea-d3d22136-draft
type: ideas
kind: idea_draft
title: Sparse Local Teacher-Anchor Packet Interface After Global Bank Collapse Draft
idea_id: idea-d3d22136
quest_id: '002'
scope: quest
branch: idea/002-idea-d3d22136
worktree_root: /home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-d3d22136
next_target: run a bounded smoke on the same 16-frame packet bundle that compares
  the current global teacher-bank adapter against a sparse/local shortlist variant
  and diagnoses whether prediction mass spreads away from the 0009/0010/0011 collapse
  centers.
method_brief: Build a child packet-interface line that keeps the current bundle/export
  path and comparison surface but changes the adapter from a global retrieval-time
  teacher memory bank into a sparse/local teacher-anchor interface. Candidate shortlist
  formation should come from packet-side similarity structure, and the evaluation
  should preserve the same direct packet controls so we can tell whether collapse
  genuinely relaxes rather than being hidden.
selection_scores:
  evidence_quality: 4
  feasibility: 4
  comparability: 5
  expected_information_gain: 5
  downstream_usefulness: 4
mechanism_family: sparse_local_packet_interface
change_layer: null
source_lens: null
foundation_ref:
  kind: branch
  ref: run/teacher_anchored_packet_adapter_smoke_r1
  branch: run/teacher_anchored_packet_adapter_smoke_r1
  worktree_root: /home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/teacher-anchored-packet-adapter-smoke-r1
  label: Branch `run/teacher_anchored_packet_adapter_smoke_r1`
foundation_reason: null
lineage_intent: continue_line
created_at: '2026-04-17T15:15:00+00:00'
updated_at: '2026-04-17T15:15:00+00:00'
tags:
- branch:idea/002-idea-d3d22136
- idea-draft
- lineage:continue_line
---
# Sparse Local Teacher-Anchor Packet Interface After Global Bank Collapse

## Executive Summary

This route wins because the strongest evidence now says packet-side signal exists but the current failure mode is global-bank collapse, not total absence of signal. Widening the current global memory-bank formulation would mostly remeasure a known instability, while writing or larger-model handoff would overstate support. A constrained child interface directly addresses the observed collapse and preserves comparability to the current experiment.

## Limitation / Bottleneck

The current global teacher-gallery anchor adapter rescues packet retrieval on the bounded 4-frame bundle but collapses badly on the 16-frame follow-up, concentrating all 16 queries onto only three anchors and leaving the interface too unstable for downstream pipeline claims.

## Selected Claim

If the teacher-anchor packet interface constrains anchor selection through a sparse or local shortlist and strengthens query distinctness before target-feature projection, then it can retain the packet-side rescue effect seen on the 4-frame bundle while avoiding the global-bank collapse observed on the 16-frame bundle.

## Theory and Method

Replace the global teacher-bank softmax with a constrained anchor-selection stage that limits candidate anchors using packet-side locality or sparsity before projecting into target feature space.

## Method Brief

Build a child packet-interface line that keeps the current bundle/export path and comparison surface but changes the adapter from a global retrieval-time teacher memory bank into a sparse/local teacher-anchor interface. Candidate shortlist formation should come from packet-side similarity structure, and the evaluation should preserve the same direct packet controls so we can tell whether collapse genuinely relaxes rather than being hidden.

## Selection Scores

- evidence_quality: 4
- feasibility: 4
- comparability: 5
- expected_information_gain: 5
- downstream_usefulness: 4

## Diversity Tags

- Mechanism family: sparse_local_packet_interface
- Change layer: Not recorded
- Source lens: Not recorded

## Code-Level Change Plan

Replace the global teacher-bank softmax with a constrained anchor-selection stage that limits candidate anchors using packet-side locality or sparsity before projecting into target feature space.

## Evaluation / Falsification Plan

Recover materially better 16-frame retrieval than the current global teacher-bank result (top-1 0.125) while preserving or improving over the direct pred_feat baseline (top-1 0.0625) and reducing collapse into the 0009/0010/0011 anchor cluster.

## Risks / Caveats / Implementation Notes

- A sparse shortlist could simply mask the current collapse without fixing the geometry.
- If the shortlist heuristic is too brittle, it may overfit the tiny bundle and fail even at the same bounded scale.

## Evidence / References

- None recorded yet.

## Foundation Choice

- Lineage intent: `continue_line`
- Foundation: `Branch `run/teacher_anchored_packet_adapter_smoke_r1``
- Reason: Use the current active foundation.

## Next Target

run a bounded smoke on the same 16-frame packet bundle that compares the current global teacher-bank adapter against a sparse/local shortlist variant and diagnoses whether prediction mass spreads away from the 0009/0010/0011 collapse centers.
