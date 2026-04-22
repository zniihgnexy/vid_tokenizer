---
id: idea-253b77bd-draft
type: ideas
kind: idea_draft
title: Relation-Consistent Packet Alignment After Blueprint Downgrade Draft
idea_id: idea-253b77bd
quest_id: '002'
scope: quest
branch: idea/002-idea-253b77bd
worktree_root: /home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-253b77bd
next_target: run one bounded relation-consistency repair package on the same frozen
  surface, then compare its predicted-to-target packet metrics directly against the
  downgraded blueprint result before widening scope.
method_brief: Promote the current route from diagnosis-only to one bounded relation-consistency
  repair. The line keeps the accepted baseline, frozen upstream bundle contract, and
  current packet evaluator unchanged, but replaces further blueprint-style or variance-only
  fixes with one relation-preserving repair family that directly matches the remaining
  predicted-to-target alignment bottleneck.
selection_scores:
  winner: candidate_a_relation_consistency_repair
  candidate_b: candidate_b_more_blueprint_or_variance_only_repair
  candidate_c: candidate_c_reopen_broad_route_selection
  why_winner: A is the nearest literature-backed repair that targets the remaining
    predicted-to-target alignment gap and is already validated in the local code path.
  why_not_b: The blueprint downgrade already showed that extra self-discrimination
    is not enough to recover target alignment.
  why_not_c: A broader redesign would skip a cheap, interpretable, already-implemented
    nearby repair before it is properly tested.
mechanism_family: relation_consistent_packet_bridge
change_layer: teacher_relation_alignment
source_lens: blueprint_downgrade_plus_relation_distillation_literature
foundation_ref:
  kind: idea
  ref: idea-c5e88710
  branch: idea/002-idea-c5e88710
  worktree_root: /home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-c5e88710
  idea_id: idea-c5e88710
  label: Idea `idea-c5e88710` on `idea/002-idea-c5e88710`
foundation_reason: Use the current active head as the foundation because it already
  contains the locked collapse-localization evidence, the completed blueprint downgrade,
  the smoke-validated relation config, and the same bounded export/eval surfaces needed
  for an interpretable next repair.
lineage_intent: continue_line
created_at: '2026-04-16T11:49:34+00:00'
updated_at: '2026-04-16T11:49:34+00:00'
tags:
- branch:idea/002-idea-253b77bd
- idea-draft
- lineage:continue_line
---
# Relation-Consistent Packet Alignment After Blueprint Downgrade

## Executive Summary

This draft records the selected idea before implementation.

## Limitation / Bottleneck

The completed blueprint-plus-semantic-change-plus-temporal-delta repair no longer looks like a pure constant-vector failure, but it still fails the key machine-facing criterion: predicted packets remain poorly aligned to target packets on the same frozen bounded surface. The decisive local evidence is that target-side packet discrimination stays perfect while predicted-to-target packet retrieval remains near chance, so the next line must test a repair that directly preserves cross-view structure rather than only increasing self-discrimination.

## Selected Claim

If the remaining bottleneck is relational misalignment rather than missing self-variance, then one bounded teacher-relation-consistency repair should improve at least one predicted-to-target packet comparison beyond the current blueprint result while keeping the same frozen export, bundle, and evaluation surfaces.

## Theory and Method

Keep the same frozen widened surface, packet export path, and bounded teacher-packet evaluator. Switch the next nearby repair family to teacher-side relation preservation by enabling teacher_relation_consistency together with the already active temporal-delta and semantic-change controls, then interpret the result against the blueprint downgrade on the same bounded surface.

## Method Brief

Promote the current route from diagnosis-only to one bounded relation-consistency repair. The line keeps the accepted baseline, frozen upstream bundle contract, and current packet evaluator unchanged, but replaces further blueprint-style or variance-only fixes with one relation-preserving repair family that directly matches the remaining predicted-to-target alignment bottleneck.

## Selection Scores

- winner: candidate_a_relation_consistency_repair
- candidate_b: candidate_b_more_blueprint_or_variance_only_repair
- candidate_c: candidate_c_reopen_broad_route_selection
- why_winner: A is the nearest literature-backed repair that targets the remaining predicted-to-target alignment gap and is already validated in the local code path.
- why_not_b: The blueprint downgrade already showed that extra self-discrimination is not enough to recover target alignment.
- why_not_c: A broader redesign would skip a cheap, interpretable, already-implemented nearby repair before it is properly tested.

## Diversity Tags

- Mechanism family: relation_consistent_packet_bridge
- Change layer: teacher_relation_alignment
- Source lens: blueprint_downgrade_plus_relation_distillation_literature

## Code-Level Change Plan

Keep the same frozen widened surface, packet export path, and bounded teacher-packet evaluator. Switch the next nearby repair family to teacher-side relation preservation by enabling teacher_relation_consistency together with the already active temporal-delta and semantic-change controls, then interpret the result against the blueprint downgrade on the same bounded surface.

## Evaluation / Falsification Plan

Either recover a measurable predicted-to-target packet alignment gain over the blueprint baseline on the same bounded surface, or obtain a cleaner negative result that justifies downgrading the packet-bridge line again instead of stacking more auxiliary losses.

## Risks / Caveats / Implementation Notes

- None recorded yet.

## Evidence / References

- `artifacts/ideas/literature_survey.md`
- `status.md`
- `PLAN.md`
- `CHECKLIST.md`
- `experiments/main/evals/shared_gating_blueprint_repair_teacher_packet_smoke_r1/summary.json`
- `experiments/main/upstream_shared_gating_snapshot/third_party/NVRC/scripts/configs/tasks/overfit/l1_teacher-resnet18-relation-semchange-delta.yaml`
- `experiments/main/upstream_shared_gating_snapshot/third_party/NVRC/tasks.py`

## Foundation Choice

- Lineage intent: `continue_line`
- Foundation: `Idea `idea-c5e88710` on `idea/002-idea-c5e88710``
- Reason: Use the current active head as the foundation because it already contains the locked collapse-localization evidence, the completed blueprint downgrade, the smoke-validated relation config, and the same bounded export/eval surfaces needed for an interpretable next repair.

## Next Target

run one bounded relation-consistency repair package on the same frozen surface, then compare its predicted-to-target packet metrics directly against the downgraded blueprint result before widening scope.
