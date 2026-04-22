---
id: idea-301dcd71-draft
type: ideas
kind: idea_draft
title: Teacher-Feature Packet Interface After Reconstructed-Video Bottleneck Draft
idea_id: idea-301dcd71
quest_id: '002'
scope: quest
branch: idea/002-idea-301dcd71
worktree_root: /home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-301dcd71
next_target: experiment
method_brief: Keep the same frozen upstream module, sample ids, and bounded tiny-local
  surface. Extend the bundle contract with teacher/tokenizer-side feature packets
  or semantic packets, then evaluate original-side versus packet-side machine use
  with the same frozen downstream comparison shape. Treat the current reconstructed-video
  result as a bounded baseline for the new interface rather than scaling it directly
  to a heavier multimodal stack.
selection_scores: null
mechanism_family: teacher_feature_packet_interface
change_layer: null
source_lens: null
foundation_ref:
  kind: idea
  ref: idea-3ed587d5
  branch: idea/002-idea-3ed587d5
  worktree_root: /home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-3ed587d5
  idea_id: idea-3ed587d5
  label: Idea `idea-3ed587d5` on `idea/002-idea-3ed587d5`
foundation_reason: 'The current line already proved the pipeline skeleton and bundle
  export path, but it also exposed a concrete bottleneck: reconstructed-video delivery
  is too lossy for the first frozen resnet18 consumer. A child line should preserve
  the validated export contract while changing only the machine-facing interface layer.'
lineage_intent: continue_line
created_at: '2026-04-14T15:19:21+00:00'
updated_at: '2026-04-14T15:19:21+00:00'
tags:
- branch:idea/002-idea-301dcd71
- idea-draft
- lineage:continue_line
---
# Teacher-Feature Packet Interface After Reconstructed-Video Bottleneck

## Executive Summary

Current evidence favors branching within the same downstream-pipeline story rather than reopening upstream codec selection or directly scaling the weak reconstructed-video interface.

## Limitation / Bottleneck

The frozen upstream module and export bundle are now validated, but reconstructed-video delivery collapses on the first frozen downstream consumer, so the next step must preserve machine-usable structure more directly than decoded frames alone.

## Selected Claim

If the downstream interface exports teacher/tokenizer feature packets instead of relying only on reconstructed frames, a frozen downstream consumer should preserve identity-level retrieval structure better while keeping the pipeline machine-facing and rerunnable.

## Theory and Method

TBD

## Method Brief

Keep the same frozen upstream module, sample ids, and bounded tiny-local surface. Extend the bundle contract with teacher/tokenizer-side feature packets or semantic packets, then evaluate original-side versus packet-side machine use with the same frozen downstream comparison shape. Treat the current reconstructed-video result as a bounded baseline for the new interface rather than scaling it directly to a heavier multimodal stack.

## Selection Scores

- Not recorded

## Diversity Tags

- Mechanism family: teacher_feature_packet_interface
- Change layer: Not recorded
- Source lens: Not recorded

## Code-Level Change Plan

TBD

## Evaluation / Falsification Plan

Improve downstream retrieval preservation over the reconstructed-video control while keeping the pipeline machine-facing and compatible with later larger-model integration.

## Risks / Caveats / Implementation Notes

- Feature export may require new hook points and clean metadata alignment.
- A packet-side consumer can drift too close to the upstream teacher objective if the evaluation surface is not kept independent enough.

## Evidence / References

- None recorded yet.

## Foundation Choice

- Lineage intent: `continue_line`
- Foundation: `Idea `idea-3ed587d5` on `idea/002-idea-3ed587d5``
- Reason: The current line already proved the pipeline skeleton and bundle export path, but it also exposed a concrete bottleneck: reconstructed-video delivery is too lossy for the first frozen resnet18 consumer. A child line should preserve the validated export contract while changing only the machine-facing interface layer.

## Next Target

experiment
