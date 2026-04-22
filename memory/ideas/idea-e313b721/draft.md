---
id: idea-e313b721-draft
type: ideas
kind: idea_draft
title: Querybank-Normalized Teacher-Anchor Packet Interface After Hubness Diagnosis
  Draft
idea_id: idea-e313b721
quest_id: '002'
scope: quest
branch: idea/002-idea-e313b721
worktree_root: /home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-e313b721
next_target: hand off immediately to experiment for one bounded 16-frame smoke that
  compares raw global-bank scoring against querybank-normalized teacher-anchor scoring,
  dynamic inverted softmax if needed, and a csls-style control, then inspect both
  retrieval metrics and anchor concentration statistics before deciding whether single-bank
  normalization is enough.
method_brief: Build a continue-line child that keeps the current 16-frame teacher-anchor
  packet bundle and evaluation surface unchanged, but promotes Querybank Normalisation
  as the first concrete hubness correction. The first bounded experiment should compare
  raw global-bank scoring against QB-Norm / Dynamic Inverted Softmax, keep CSLS-style
  local scaling as a classical control, and treat hard shortlist pruning only as an
  optional secondary control rather than the main route.
selection_scores:
  winner: querybank_norm_or_dynamic_inverted_softmax
  evidence_quality: 5
  feasibility: 5
  comparability: 5
  expected_information_gain: 5
  downstream_usefulness: 4
  why_not_csls_first: good control but weaker cross-modal story
  why_not_dual_bank_first: too many new bank-policy choices before the lighter single-bank
    route is tested
mechanism_family: querybank_normalized_teacher_anchor_packet_interface
change_layer: retrieval_score_calibration
source_lens: active_hubness_diagnosis_plus_cross_modal_posthoc_normalization_literature
foundation_ref:
  kind: idea
  ref: idea-70dedd18
  branch: idea/002-idea-70dedd18
  worktree_root: /home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-70dedd18
  idea_id: idea-70dedd18
  label: Idea `idea-70dedd18` on `idea/002-idea-70dedd18`
foundation_reason: The active hubness-calibrated line already established that the
  16-frame failure looks like retrieval-time hub collapse rather than total packet-signal
  loss, but it still leaves the correction family too broad. Querybank normalization
  is the most directly relevant cross-modal, no-retraining first child route.
lineage_intent: continue_line
created_at: '2026-04-17T20:07:44+00:00'
updated_at: '2026-04-17T20:07:44+00:00'
tags:
- branch:idea/002-idea-e313b721
- idea-draft
- lineage:continue_line
---
# Querybank-Normalized Teacher-Anchor Packet Interface After Hubness Diagnosis

## Executive Summary

Promote the lightest cross-modal post-hoc hubness correction that preserves the frozen packet interface and does not require concurrent test access. This route dominates CSLS as the main child because it matches the current retrieval setting more directly, and it dominates dual-bank normalization as the first child because it is cheaper and cleaner while still probing the real bottleneck.

## Limitation / Bottleneck

The current hubness-calibrated packet line correctly explains the 16-frame failure as teacher-anchor hub collapse, but it is still too broad for the next measured step because several post-hoc hubness corrections remain plausible. The next child line should lock one concrete first correction before reopening training or widening the interface.

## Selected Claim

If the remaining 16-frame failure is mainly caused by gallery hubness rather than total packet-signal loss, then querybank-normalized teacher-anchor scoring should outperform raw global-bank retrieval and reduce concentration on anchors 0009/0010/0011 without any retraining.

## Theory and Method

Keep the frozen 16-frame packet bundle and teacher anchor bank fixed, then replace raw teacher-anchor similarity with a querybank-normalized or Dynamic Inverted Softmax style score that downweights hub anchors at inference time before final retrieval.

## Method Brief

Build a continue-line child that keeps the current 16-frame teacher-anchor packet bundle and evaluation surface unchanged, but promotes Querybank Normalisation as the first concrete hubness correction. The first bounded experiment should compare raw global-bank scoring against QB-Norm / Dynamic Inverted Softmax, keep CSLS-style local scaling as a classical control, and treat hard shortlist pruning only as an optional secondary control rather than the main route.

## Selection Scores

- winner: querybank_norm_or_dynamic_inverted_softmax
- evidence_quality: 5
- feasibility: 5
- comparability: 5
- expected_information_gain: 5
- downstream_usefulness: 4
- why_not_csls_first: good control but weaker cross-modal story
- why_not_dual_bank_first: too many new bank-policy choices before the lighter single-bank route is tested

## Diversity Tags

- Mechanism family: querybank_normalized_teacher_anchor_packet_interface
- Change layer: retrieval_score_calibration
- Source lens: active_hubness_diagnosis_plus_cross_modal_posthoc_normalization_literature

## Code-Level Change Plan

Keep the frozen 16-frame packet bundle and teacher anchor bank fixed, then replace raw teacher-anchor similarity with a querybank-normalized or Dynamic Inverted Softmax style score that downweights hub anchors at inference time before final retrieval.

## Evaluation / Falsification Plan

Improve over the current raw global-bank 16-frame top-1 accuracy of 0.125 while reducing anchor concentration away from the 0009/0010/0011 hub cluster, and do so with a rerunnable inference-only change that is easier to defend in the paper than another training-side repair.

## Risks / Caveats / Implementation Notes

- Single-bank querybank normalization may only reshuffle the same errors without materially reducing hub concentration.
- On the tiny 16-frame surface, the querybank could overfit or under-estimate gallery-side hubness.
- If this route fails, the correct next move is dual-bank normalization or a return to query-side geometry repair rather than more cosmetic re-ranking.

## Evidence / References

- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-70dedd18/artifacts/ideas/literature_survey.md`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-70dedd18/memory/ideas/idea-70dedd18/idea.md`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/teacher-anchored-packet-adapter-smoke-r1/experiments/main/teacher_anchored_packet_adapter_smoke_r1/RUN.md`

## Foundation Choice

- Lineage intent: `continue_line`
- Foundation: `Idea `idea-70dedd18` on `idea/002-idea-70dedd18``
- Reason: The active hubness-calibrated line already established that the 16-frame failure looks like retrieval-time hub collapse rather than total packet-signal loss, but it still leaves the correction family too broad. Querybank normalization is the most directly relevant cross-modal, no-retraining first child route.

## Next Target

hand off immediately to experiment for one bounded 16-frame smoke that compares raw global-bank scoring against querybank-normalized teacher-anchor scoring, dynamic inverted softmax if needed, and a csls-style control, then inspect both retrieval metrics and anchor concentration statistics before deciding whether single-bank normalization is enough.
