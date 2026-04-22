---
id: idea-70dedd18-draft
type: ideas
kind: idea_draft
title: Hubness-Calibrated Teacher-Anchor Packet Interface After Global-Bank Collapse
  Draft
idea_id: idea-70dedd18
quest_id: '002'
scope: quest
branch: idea/002-idea-70dedd18
worktree_root: /home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-70dedd18
next_target: run a bounded 16-frame smoke on the existing teacher-anchor packet bundle
  that compares raw global-bank scoring against at least one hubness-calibrated scoring
  rule and optionally one hard-shortlist control, then inspect both retrieval metrics
  and anchor concentration statistics before deciding whether the packet interface
  is stable enough to widen.
method_brief: Build a child packet-interface line that keeps the current 16-frame
  bundle, teacher anchor bank, and evaluation surface fixed, and test one or two hubness-calibrated
  similarity rules against the current raw global-bank scorer. Hard shortlist pruning
  is kept only as a secondary control, not the primary mechanism. The goal is to determine
  whether inference-time calibration alone can rescue interface stability before any
  training-side repair.
selection_scores:
  evidence_quality: 5
  feasibility: 5
  comparability: 5
  expected_information_gain: 5
  downstream_usefulness: 4
mechanism_family: hubness_calibrated_packet_interface
change_layer: retrieval_score_calibration
source_lens: local_collapse_evidence_plus_hubness_and_cross_modal_retrieval_literature
foundation_ref:
  kind: idea
  ref: idea-d3d22136
  branch: idea/002-idea-d3d22136
  worktree_root: /home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-d3d22136
  idea_id: idea-d3d22136
  label: Idea `idea-d3d22136` on `idea/002-idea-d3d22136`
foundation_reason: The current active sparse/local shortlist line correctly localized
  the failure to retrieval-time collapse, but it is still too broad. The strongest
  local evidence and the newly refreshed literature both point to hubness-calibrated
  score correction as the most defensible next refinement inside the same family.
lineage_intent: continue_line
created_at: '2026-04-17T19:55:20+00:00'
updated_at: '2026-04-17T19:55:20+00:00'
tags:
- branch:idea/002-idea-70dedd18
- idea-draft
- lineage:continue_line
---
# Hubness-Calibrated Teacher-Anchor Packet Interface After Global-Bank Collapse

## Executive Summary

This child line wins because the current failure pattern is dominated by hub concentration rather than by complete loss of packet signal. A hubness-calibrated inference-time correction is more principled and more comparable than hard top-k pruning, and much cheaper and cleaner than reopening training-side anti-collapse repair before the retrieval geometry itself is properly tested.

## Limitation / Bottleneck

The current teacher-anchor packet interface shows a real but unstable machine-facing signal: it reaches strong retrieval on the bounded 4-frame packet bundle, but on the 16-frame follow-up the global teacher bank collapses many queries onto a few anchors, leaving the interface too hub-dominated to support a scalable downstream handoff claim.

## Selected Claim

If the 16-frame failure is primarily a hubness problem rather than total packet-signal loss, then a hubness-calibrated similarity rule over the existing teacher anchor bank can recover materially better retrieval stability than raw global-bank scoring without reopening training or exporter design.

## Theory and Method

Keep the frozen packet bundle and teacher anchor bank, but replace raw global-bank similarity with a density-aware cross-space correction such as locally scaled similarity, Globally Corrected ranking, CSLS-style correction, or Querybank-Normalisation / Dynamic Inverted Softmax style normalization before final retrieval or projection.

## Method Brief

Build a child packet-interface line that keeps the current 16-frame bundle, teacher anchor bank, and evaluation surface fixed, and test one or two hubness-calibrated similarity rules against the current raw global-bank scorer. Hard shortlist pruning is kept only as a secondary control, not the primary mechanism. The goal is to determine whether inference-time calibration alone can rescue interface stability before any training-side repair.

## Selection Scores

- evidence_quality: 5
- feasibility: 5
- comparability: 5
- expected_information_gain: 5
- downstream_usefulness: 4

## Diversity Tags

- Mechanism family: hubness_calibrated_packet_interface
- Change layer: retrieval_score_calibration
- Source lens: local_collapse_evidence_plus_hubness_and_cross_modal_retrieval_literature

## Code-Level Change Plan

Keep the frozen packet bundle and teacher anchor bank, but replace raw global-bank similarity with a density-aware cross-space correction such as locally scaled similarity, Globally Corrected ranking, CSLS-style correction, or Querybank-Normalisation / Dynamic Inverted Softmax style normalization before final retrieval or projection.

## Evaluation / Falsification Plan

Improve over the current 16-frame global-bank result (`top1=0.125`) while reducing anchor concentration away from the `0009/0010/0011` hub cluster, and do so without retraining so the packet-interface story stays clean and rerunnable.

## Risks / Caveats / Implementation Notes

- Hubness calibration might only reshuffle rankings without materially reducing collapse.
- If so, the correct next move will be query-side geometry repair rather than more re-ranking heuristics.
- There is also a risk that local-density correction works only on the tiny bounded surface and does not transfer to a wider packet bank.

## Evidence / References

- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-d3d22136/artifacts/ideas/literature_survey.md`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-d3d22136/memory/ideas/idea-d3d22136/idea.md`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/teacher-anchored-packet-adapter-smoke-r1/experiments/main/teacher_anchored_packet_adapter_smoke_r1/RUN.md`

## Foundation Choice

- Lineage intent: `continue_line`
- Foundation: `Idea `idea-d3d22136` on `idea/002-idea-d3d22136``
- Reason: The current active sparse/local shortlist line correctly localized the failure to retrieval-time collapse, but it is still too broad. The strongest local evidence and the newly refreshed literature both point to hubness-calibrated score correction as the most defensible next refinement inside the same family.

## Next Target

run a bounded 16-frame smoke on the existing teacher-anchor packet bundle that compares raw global-bank scoring against at least one hubness-calibrated scoring rule and optionally one hard-shortlist control, then inspect both retrieval metrics and anchor concentration statistics before deciding whether the packet interface is stable enough to widen.
