---
id: idea-2835dace-draft
type: ideas
kind: idea_draft
title: Query-Side Anti-Collapse Packet Repair After Relation Failure Draft
idea_id: idea-2835dace
quest_id: '002'
scope: quest
branch: idea/002-idea-2835dace
worktree_root: /home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-2835dace
next_target: revise the current branch control files and hand off to experiment for
  one bounded predicted-side localization-plus-repair package whose first repair is
  an explicit variance-floor control on the accessible packet surfaces.
method_brief: Keep the same frozen widened bridge surface, packet exporter, and packet
  evaluator as controls. First confirm whether deeper query-side surfaces such as
  query_projection or query_packet_head can be exposed cheaply; if not, treat pred_feat
  and pred_delta as the intervention surface. Then test exactly one bounded predicted-side
  anti-collapse repair, with a variance-floor-first choice and decorrelation as a
  secondary fallback, before re-evaluating on the exact same bounded packet interface.
selection_scores:
  winner: candidate_a_variance_floor_first_on_accessible_predicted_packet_surfaces
  candidate_b: candidate_b_decorrelation_or_redundancy_reduction_followup
  candidate_c: candidate_c_return_to_interface_redesign
  why_winner: Two measured teacher-side repair families already failed, the target
    branch is already fixed and asymmetric, and the current code path exposes predicted
    packet tensors that are a direct fit for explicit variance control.
  why_not_b: A stronger decorrelation objective is broader and less interpretable
    than the smallest variance-first repair.
  why_not_c: The direct predicted-side collapse evidence is still too strong to skip
    one bounded predicted-side repair.
mechanism_family: query_side_anti_collapse_packet_bridge
change_layer: query_side_packet_head
source_lens: relation_negative_result_plus_query_collapse_evidence
foundation_ref:
  kind: run
  ref: shared_gating_relation_semchange_delta_smoke_r1
  branch: run/shared_gating_relation_semchange_delta_smoke_r1
  worktree_root: /home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/shared-gating-relation-semchange-delta-smoke-r1
  run_id: shared_gating_relation_semchange_delta_smoke_r1
  label: Run `shared_gating_relation_semchange_delta_smoke_r1` on `run/shared_gating_relation_semchange_delta_smoke_r1`
foundation_reason: null
lineage_intent: null
created_at: '2026-04-17T08:39:23+00:00'
updated_at: '2026-04-17T14:01:57+00:00'
tags:
- branch:idea/002-idea-2835dace
- idea-draft
---
# Query-Side Anti-Collapse Packet Repair After Relation Failure

## Executive Summary

Keep the current anti-collapse branch as the incumbent, but tighten the mechanism choice inside it: do not return to another teacher-side repair, and do not jump to packet-interface redesign before one bounded predicted-side variance-first repair is measured.

## Limitation / Bottleneck

The relation-consistency repair became a second negative result on the same frozen widened bridge surface. Target packets remain discriminative, but both blueprint and relation repairs fail to recover predicted-to-target packet alignment, while the earlier localization package still says the earliest accessible collapse surface is exported predicted packets or earlier.

## Selected Claim

If the packet bridge now fails because predicted-side packet representations have insufficient diversity before or around the accessible query-side packet surfaces, then one minimal predicted-side anti-collapse control should recover more predicted-to-target alignment than another teacher-side regularizer on the same frozen surface.

## Theory and Method

Stay localization-first, then act on the nearest accessible predicted-side packet surfaces. The first repair should be an explicit variance-floor control on predicted packet features or deltas, with stronger decorrelation kept as fallback only if variance-first is too weak.

## Method Brief

Keep the same frozen widened bridge surface, packet exporter, and packet evaluator as controls. First confirm whether deeper query-side surfaces such as query_projection or query_packet_head can be exposed cheaply; if not, treat pred_feat and pred_delta as the intervention surface. Then test exactly one bounded predicted-side anti-collapse repair, with a variance-floor-first choice and decorrelation as a secondary fallback, before re-evaluating on the exact same bounded packet interface.

## Selection Scores

- winner: candidate_a_variance_floor_first_on_accessible_predicted_packet_surfaces
- candidate_b: candidate_b_decorrelation_or_redundancy_reduction_followup
- candidate_c: candidate_c_return_to_interface_redesign
- why_winner: Two measured teacher-side repair families already failed, the target branch is already fixed and asymmetric, and the current code path exposes predicted packet tensors that are a direct fit for explicit variance control.
- why_not_b: A stronger decorrelation objective is broader and less interpretable than the smallest variance-first repair.
- why_not_c: The direct predicted-side collapse evidence is still too strong to skip one bounded predicted-side repair.

## Diversity Tags

- Mechanism family: query_side_anti_collapse_packet_bridge
- Change layer: query_side_packet_head
- Source lens: relation_negative_result_plus_query_collapse_evidence

## Code-Level Change Plan

Stay localization-first, then act on the nearest accessible predicted-side packet surfaces. The first repair should be an explicit variance-floor control on predicted packet features or deltas, with stronger decorrelation kept as fallback only if variance-first is too weak.

## Evaluation / Falsification Plan

Either improve at least one predicted-to-target packet comparison beyond the downgraded blueprint and negative relation runs on the same frozen surface, or produce a cleaner negative result showing that accessible predicted-side anti-collapse repair cannot rescue the packet bridge.

## Risks / Caveats / Implementation Notes

- The true bottleneck may lie earlier than the currently accessible packet tensors.
- A variance-floor repair may improve diversity diagnostics without restoring target alignment.
- Exposing deeper query-side surfaces may require moderate exporter changes before a clean repair can be tested.

## Evidence / References

- `artifacts/idea/literature_survey.md`
- `experiments/main/evals/shared_gating_query_collapse_localization_smoke_r1/report.md`
- `experiments/main/evals/shared_gating_query_collapse_localization_smoke_r1/summary.json`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/shared-gating-relation-semchange-delta-smoke-r1/experiments/main/shared_gating_relation_semchange_delta_smoke_r1/RESULT.json`

## Foundation Choice

- Lineage intent: `manual`
- Foundation: `Run `shared_gating_relation_semchange_delta_smoke_r1` on `run/shared_gating_relation_semchange_delta_smoke_r1``
- Reason: Use the current active foundation.

## Next Target

revise the current branch control files and hand off to experiment for one bounded predicted-side localization-plus-repair package whose first repair is an explicit variance-floor control on the accessible packet surfaces.
