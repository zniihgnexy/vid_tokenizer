---
id: idea-44a0e404
type: ideas
kind: idea
title: Delta-Dominant Teacher Packet Interface After Static Feature Packet Bottleneck
quest_id: '002'
scope: quest
branch: idea/002-idea-44a0e404
worktree_root: /home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-44a0e404
next_target: prepare and run the smallest delta-first packet follow-up package on
  the same frozen 4-frame surface, then decide whether the line deserves wider validation
  or a broader downstream consumer.
method_brief: Reuse the current teacher packet exporter/evaluator scaffold and the
  same 4-frame frozen comparison surface. The next bounded step is a delta-first packet
  follow-up that tests pure delta and heavy-delta-gated variants before any scaling
  or larger-model integration.
selection_scores: null
mechanism_family: delta_dominant_teacher_packet
change_layer: null
source_lens: null
foundation_ref:
  kind: idea
  ref: idea-301dcd71
  branch: idea/002-idea-301dcd71
  worktree_root: /home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-301dcd71
  idea_id: idea-301dcd71
  label: Idea `idea-301dcd71` on `idea/002-idea-301dcd71`
foundation_reason: null
lineage_intent: continue_line
created_at: '2026-04-15T07:55:04+00:00'
updated_at: '2026-04-15T07:55:04+00:00'
tags:
- branch:idea/002-idea-44a0e404
- next:prepare and run the smallest delta-first packet follow-up package on the same
  frozen 4-frame surface, then decide whether the line deserves wider validation or
  a broader downstream consumer.
- lineage:continue_line
- family:delta-dominant-teacher-packet
---
# Delta-Dominant Teacher Packet Interface After Static Feature Packet Bottleneck

## Problem

The first teacher-packet smoke on the frozen 4-frame surface shows that plain static feature packet does not outperform the reconstructed-video control: pred_feat_to_target_feat top-1 remains 0.25 with mean match rank 2.5. The route needs a new child line that keeps the same frozen upstream contract but changes the packet emphasis.

## Hypothesis

The machine-facing value of the packet interface is concentrated in temporal change structure, so a delta-dominant packet should preserve retrieval structure more reliably than both reconstructed video and plain static feature packet under the same frozen upstream contract.

## Mechanism

Make temporal delta the primary packet signal and treat static teacher features as optional secondary context rather than the default interface payload. Keep the existing exporter and evaluator scaffold, but center future packet views and comparisons on delta-first or heavy-delta-gated representations.

## Method Brief

Reuse the current teacher packet exporter/evaluator scaffold and the same 4-frame frozen comparison surface. The next bounded step is a delta-first packet follow-up that tests pure delta and heavy-delta-gated variants before any scaling or larger-model integration.

## Expected Gain

Turn a mixed first smoke into a cleaner next route: keep the observed 0.75 top-1 delta signal while dropping plain-feature complexity that does not beat the 0.25 reconstructed-video control.

## Selection Scores

- Not recorded

## Diversity Tags

- Mechanism family: delta_dominant_teacher_packet
- Change layer: Not recorded
- Source lens: Not recorded

## Decision Reason

Measured evidence from the current line supports a route shift: delta-only packet retrieval reaches top-1 0.75 with mean rank 1.25, while plain feature packet stays at top-1 0.25 and heavy delta-dominant concat reaches the same 0.75 top-1 only when delta clearly dominates.

## Foundation

- Lineage Intent: `continue_line`
- Kind: `idea`
- Ref: `idea-301dcd71`
- Branch: `idea/002-idea-301dcd71`
- Worktree: `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-301dcd71`
- Reason: No explicit reason recorded.

## Risks

- The current evidence comes from a tiny 4-frame smoke surface, so delta gains may be brittle.
- A pure delta packet may lose useful static context if weighting is pushed too far.
- Packet/sample alignment must remain exact so the follow-up comparison stays trustworthy.

## Evidence Paths

- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-301dcd71/experiments/main/evals/shared_gating_teacher_packet_smoke_r1/summary.json`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-301dcd71/experiments/main/evals/shared_gating_teacher_packet_smoke_r1/weight_sweep.json`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-301dcd71/artifacts/decisions/decision-41ab5396.json`

## Next Target

prepare and run the smallest delta-first packet follow-up package on the same frozen 4-frame surface, then decide whether the line deserves wider validation or a broader downstream consumer.
