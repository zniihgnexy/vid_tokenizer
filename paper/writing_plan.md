# Writing Plan

## Current Objective

Turn the current paper line into a bounded, defensible feasibility note centered on query-adaptive arbitration over a frozen teacher-anchor packet surface, while making the later repaired broader validation explicit as a claim-boundary guardrail rather than silently drafting past it.

## Strongest Evidence

- Main-text anchor:
  - `query_adaptive_teacher_anchor_arbitration_smoke_r1`
  - safe headline numbers:
    - query-adaptive top-1: `0.15625`
    - raw-global top-1: `0.125`
    - temporal-context top-1: `0.09375`
    - query-adaptive hub share: `0.28125`
    - raw-global hub share: `0.59375`
- Broader boundary note:
  - `query_adaptive_broader_retrieval_validation_smoke_r1`
  - query-adaptive keeps the best non-oracle top-1 at `0.125`
  - raw-global and temporal-context both sit at `0.10416666666666667`
  - temporal-context keeps the best mean-match-rank `7.8125`
  - temporal-context also keeps the best chunk-top1 `0.3333333333333333`
- Downstream-consumer boundary note:
  - `delta_packet_bridge_consumer_chunked16f_smoke_r1`
  - weakest direct control top-1: `0.0625`
  - both low-capacity ridge bridge routes: `0.0`

## Hard Constraints

- Keep the upstream packet bundle frozen in the paper story.
- Do not claim a new codec, task-general feature transfer stack, or broad machine-facing adapter.
- Keep the paper scoped to one bounded widened teacher-anchor retrieval surface.
- Acknowledge the chunk-level tradeoff and the lack of broader validation early in the draft.
- Keep broader downstream-consumer transfer explicitly unsupported until a stronger consumer evaluation succeeds.

## Completed In This Pass

- Recovered the active paper line from a missing `selected_outline` and missing `draft` state by syncing the older bounded paper contract into the current paper worktree.
- Narrowed the paper title and abstract promise.
- Added a related-work positioning map grounded in the existing quest survey.
- Added an explicit claim-evidence map with two safe claims.
- Linked the active evidence item to those claims in the paper ledger.
- Added a citation-backed positioning paragraph to the draft and created `paper/references.bib`.
- Added a first proofing report, a language-issues note, and a markdown-first bundle manifest for the current bounded draft.
- Mapped the earlier chunked 16-frame QB-Norm revalidation back into the active paper contract as appendix-only robustness evidence.
- Integrated the repaired broader three-bundle validation as a claim-boundary note so the draft no longer says that broader validation is still missing.
- Added the first negative downstream-consumer bridge smoke as a future-work boundary note rather than silent supporting evidence.

## Next Revisions

1. Check that the synchronized draft, selected outline, and paper-line state stay mutually consistent on the active paper worktree.
2. If consistency holds, record a writing-progress artifact for the repaired paper contract and refreshed first draft.
3. Only after that, decide whether to resubmit a markdown-first paper bundle or do one more skeptical review pass.
