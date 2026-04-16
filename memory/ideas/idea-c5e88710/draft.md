---
id: idea-c5e88710-draft
type: ideas
kind: idea_draft
title: Query-Distinct Packet Bridge After Collapse Evidence Draft
idea_id: idea-c5e88710
quest_id: '002'
scope: quest
branch: idea/002-idea-c5e88710
worktree_root: /home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-c5e88710
next_target: implement a collapse-localization package that measures where chunk discrimination
  disappears and, if it is lost in the query packet head, test one minimal anti-collapse
  query control on the same frozen widened four-chunk surface
method_brief: Keep the same frozen widened chunk bundles and the current chunk-aware
  evaluator as diagnostic controls. First localize where chunk discrimination disappears
  by comparing target fields, exported predicted packets, and any query-side packet
  head or projection. Only if the collapse localizes to the predicted packet side,
  add the smallest diversity-preserving control justified by the literature, such
  as stop-gradient asymmetry, a variance floor, redundancy reduction, or a chunk-level
  contrastive calibration, then re-evaluate on the same four-chunk bounded surface.
selection_scores:
  winner: candidate_a_query_side_packet_collapse_diagnosis
  candidate_b: direct anti-collapse regularization deferred until localization
  candidate_c: abandon packet bridge now rejected as premature
mechanism_family: diversity_preserving_packet_bridge
change_layer: query_side_packet_head
source_lens: local_collapse_evidence_plus_ssl_anti_collapse_literature
foundation_ref:
  kind: idea
  ref: idea-955ff951
  branch: idea/002-idea-955ff951
  worktree_root: /home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-955ff951
  idea_id: idea-955ff951
  label: Idea `idea-955ff951` on `idea/002-idea-955ff951`
foundation_reason: Use the current chunk-aware branch as the foundation because it
  already contains the failed evaluator, the exact widened smoke outputs, and the
  direct collapse probe that motivates the next route.
lineage_intent: continue_line
created_at: '2026-04-15T10:09:27+00:00'
updated_at: '2026-04-15T10:09:27+00:00'
tags:
- branch:idea/002-idea-c5e88710
- idea-draft
- lineage:continue_line
---
# Query-Distinct Packet Bridge After Collapse Evidence

## Executive Summary

This draft records the selected idea before implementation.

## Limitation / Bottleneck

The chunk-aware local-burst smoke falsified the main rescue hypothesis: every packet-side chunk-aware bridge metric stayed at four-way chance even though the target-feature sanity route remained perfect. A direct chunk-level cosine probe shows the decisive bottleneck: pred_feat and pred_delta are identical across widened chunk bundles, while target_feat and target_delta still vary. The next line must restore or at least localize query-side chunk discrimination before any further bridge claim is meaningful.

## Selected Claim

The current failure is primarily a query-side representation-collapse problem rather than a chunk-aggregation problem. If chunk discrimination is preserved somewhere before or around the query packet head, one minimal diversity-preserving control should lift the chunk-aware bridge above four-way chance without changing the frozen widened data surface.

## Theory and Method

TBD

## Method Brief

Keep the same frozen widened chunk bundles and the current chunk-aware evaluator as diagnostic controls. First localize where chunk discrimination disappears by comparing target fields, exported predicted packets, and any query-side packet head or projection. Only if the collapse localizes to the predicted packet side, add the smallest diversity-preserving control justified by the literature, such as stop-gradient asymmetry, a variance floor, redundancy reduction, or a chunk-level contrastive calibration, then re-evaluate on the same four-chunk bounded surface.

## Selection Scores

- winner: candidate_a_query_side_packet_collapse_diagnosis
- candidate_b: direct anti-collapse regularization deferred until localization
- candidate_c: abandon packet bridge now rejected as premature

## Diversity Tags

- Mechanism family: diversity_preserving_packet_bridge
- Change layer: query_side_packet_head
- Source lens: local_collapse_evidence_plus_ssl_anti_collapse_literature

## Code-Level Change Plan

TBD

## Evaluation / Falsification Plan

Either recover chunk-aware packet bridge performance above 0.25 on the same bounded surface, or decisively show that the packet bridge line should be downgraded because query-side collapse already happens before any local bridge fix can act.

## Risks / Caveats / Implementation Notes

- The collapse may already exist before packet export, leaving no local query-head fix.
- A tiny-surface anti-collapse control may overfit or create a misleading apparent gain.
- If no query-side surface retains chunk discrimination, the packet line may need a broader route change.

## Evidence / References

- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-955ff951/experiments/main/evals/shared_gating_ego4d16f_chunk_aware_packet_smoke_r1/report.md`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-955ff951/experiments/main/evals/shared_gating_ego4d16f_chunk_aware_packet_smoke_r1/summary.json`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-955ff951/artifacts/ideas/literature_survey.md`

## Foundation Choice

- Lineage intent: `continue_line`
- Foundation: `Idea `idea-955ff951` on `idea/002-idea-955ff951``
- Reason: Use the current chunk-aware branch as the foundation because it already contains the failed evaluator, the exact widened smoke outputs, and the direct collapse probe that motivates the next route.

## Next Target

implement a collapse-localization package that measures where chunk discrimination disappears and, if it is lost in the query packet head, test one minimal anti-collapse query control on the same frozen widened four-chunk surface
