# Status

Baseline reuse is already resolved: `nvrc-local-source` remains the accepted
upstream asset.

Current stage: `experiment`

Current judgment:
- The relation repair is now a completed negative result, not the active route.
- The first bounded repair package has been narrowed to one minimal
  predicted-side variance-floor intervention in the current teacher-loss path.
- `pred_feat` is the primary intervention surface for the first pass because it
  is directly accessible and maps cleanly to the observed collapse evidence.
- `pred_delta` remains an optional secondary extension, but it is intentionally
  off in the first config to avoid adding a second moving part before smoke
  validation.
- The export and evaluation surface stays fixed in this pass:
  - same frozen widened dataset family
  - same packet export tools
  - same teacher-packet evaluator
- The immediate question is now implementation validity, not route selection:
  can the variance-floor repair be wired cleanly and smoke-tested without
  widening the experiment surface?

Deferred:
- another teacher-side auxiliary-loss repair
- broader packet-interface redesign before one bounded predicted-side repair is measured
- deeper multimodal / VLM integration before the packet bridge is trustworthy
- reopening codec-line ranking

Next durable action:
- finish wiring the variance-floor repair package
- run the lightweight teacher-loss smoke
- if the smoke is clean, decide whether to open a dedicated `run/*` branch for
  the bounded main experiment
