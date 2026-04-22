# Review Report

## Summary

The revised draft is now materially safer than the previous version. It is defensible as a **bounded feasibility note** about downstream readout over a frozen teacher-anchor packet surface, and the earlier over-claiming risk has been reduced sharply by the narrowed title, the earlier scope limitation, the explicit claim-evidence map, the related-work positioning note, and the new broader-validation boundary note. The core scientific question is now legible: on one fixed widened teacher-anchor retrieval surface, can a simple query-adaptive arbitration rule recover more headline retrieval signal than two static packet routes?

Current overall judgment: **defensible citation-backed bounded bundle-ready draft package, with one remaining runtime-side delivery-registration blocker**.

No new experiment is required for the current narrow claim. The major manuscript-positioning blocker from the previous pass has now been reduced: the draft carries a citation-backed positioning paragraph, a bibliography surface, a proofing report, and a markdown-first bundle manifest. The main remaining blocker is now runtime-side bundle registration rather than evidence, novelty uncertainty, or missing manuscript package files.

## Core Claims Reviewed

- `C1`: Query-adaptive arbitration improves headline retrieval top-1 accuracy on the bounded widened teacher-anchor surface.
- `C2`: The frozen teacher-anchor packet surface contains downstream-recoverable structure that static routing underuses on that same surface.

## Strongest Current Evidence

- Main experiment `query_adaptive_teacher_anchor_arbitration_smoke_r1` remains the single main-text evidence anchor.
- Top-1 accuracy improves from `0.125` and `0.09375` for the two static parent routes to `0.15625`.
- Hub-cluster share drops from `0.59375` to `0.28125` without changing the upstream packet bundle.
- The claim-evidence map now keeps both defended claims tied to the same bounded evidence item and records the key limitations explicitly.

## Weakest Current Evidence

- The draft is citation-backed, but it still has only the minimum positioning surface rather than a fully polished reviewer-facing manuscript package.
- The broader three-bundle validation is correctly treated only as a claim-boundary note rather than a second fully developed main-text result.

## Top Likely Rejection Reasons

1. The reader cannot verify novelty or positioning from the draft alone because the literature grounding still lives mainly outside the manuscript.
2. The current evidence remains intentionally narrow, so any reader expecting cross-surface generalization would push back if the claim scope drifted broader again.
3. A fast reviewer may still want one sentence more on why the current rule counts as a hand-built arbitration heuristic rather than a learned broad adapter, though this risk is now much smaller after the latest wording fix.

## Strengths

- The title and abstract promise now match the actual evidence scope.
- The main limitation appears early instead of being buried at the end.
- The draft no longer hides the non-uniform metric outcome.
- The arbitration rule is now described as a simple non-learned heuristic rather than an unspecified adapter family.
- The claim-evidence map and related-work map make the paper line much more auditable.

## Weaknesses

- The package is markdown-first rather than venue-formatted LaTeX/PDF.
- The broader validation remains a boundary-setting note, not a second polished main-text experiment.

## Key Issues

### R1. The draft package is scientifically ready, but durable bundle registration is still blocked by runtime anchor drift

Severity: moderate  
Type: runtime-delivery  
Blocks finalize: no

Evidence:

- `paper/proofing/proofing_report.md` and `paper/paper_bundle_manifest.json` now exist.
- `artifact.get_paper_contract_health(...)` now reports `bundle_status = present` and `finalize_ready = true`.
- The most recent `artifact.submit_paper_bundle(...)` attempt still failed with an unsupported active-anchor error, so delivery registration is not yet durable even though the files exist.

Why it matters:

- The science is now narrower and cleaner, and the manuscript can already be treated as a bundle-ready internal paper line.
- We still should not claim the bundle has been durably registered if the runtime has not actually recorded that delivery state.

Recommendation:

- Keep the current scientific scope fixed.
- Treat this as a runtime-side closure problem, not as a manuscript or experiment gap.
- Retry durable bundle registration only if the runtime state changes; otherwise carry the blocker explicitly into the final closure surfaces.

## Actionable Suggestions

1. Keep the current two-claim boundary; do not broaden the story before new evidence exists.
2. Treat the manuscript package as content-complete and focus only on delivery bookkeeping.
3. Run one final fast read only to catch packaging regressions before any externalized handoff.

## Storyline Advice

- The current best storyline is now stable:
  1. the upstream packet surface is frozen and exportable,
  2. static routes leave retrieval signal underused,
  3. a simple non-learned query-adaptive arbitration rule recovers part of that signal on one bounded surface,
  4. therefore the packet surface is promising enough to justify later strengthening work.
- Do not drift back toward a generic “machine-facing adapter” headline until broader evidence exists.

## Priority Revision Plan

1. Closure-only: register the bundle durably if the runtime allows it, or document the delivery-registration blocker explicitly if it does not.
2. Writing-only if needed: fix any small packaging regressions discovered during the final read.

## Experiment Inventory And Research Experiment Plan

No mandatory new experiment is required for the **current narrow claim**.

Optional future strengthening remains the same as before:

- broader retrieval validation on additional surfaces
- a larger downstream consumer

Those are later strengthening moves, not prerequisites for the current bounded paper line.

## Novelty Verification And Related-Work Matrix

| Family | Representative papers already surfaced locally | Current paper's distinction |
|---|---|---|
| Machine-facing video coding / feature compression | `2001.03569`, `2110.09241`, `2404.04848`, `2503.23772` | We do not propose a new codec or feature-transfer stack; we test readout over a frozen packet surface. |
| Egocentric downstream consumers | `2206.01670`, `2212.04501`, `2407.16658` | We do not claim a stronger retriever; these works justify why retrieval is a meaningful downstream task. |
| Retrieval alignment / lightweight adaptation | `2207.07285`, `2410.15624`, `2206.13559`, `2205.13535`, `2301.07868` | We stay below the learned-adapter claim level and defend only a bounded arbitration heuristic. |

## References

- `paper/related_work_map.md`
- `paper/references.bib`
- `paper/claim_evidence_map.json`
- `paper/draft.md`
- `paper/evidence_ledger.json`
- `paper/proofing/proofing_report.md`
- `paper/paper_bundle_manifest.json`
