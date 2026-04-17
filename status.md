# Status

Baseline reuse is already resolved: `nvrc-local-source` remains the accepted
upstream asset.

Current stage: `experiment`

Current judgment:
- The relation repair remains the earlier negative result; the active evidence
  line is now the corrected predicted-side variance-floor run on the dedicated
  `run/*` branch.
- The first bounded real run initially looked valid but was invalidated because
  the new variance-floor fields were not forwarded through
  `create_overfit_task(...)`, leaving the effective regularizer at `0.0`.
- That passthrough bug is now fixed and the corrected bounded run has completed
  with `pred_variance_weight=1.0` active in both training and evaluation logs.
- `pred_feat` remains the primary intervention surface for this first pass
  because it is directly accessible and maps cleanly to the observed collapse
  evidence.
- `pred_delta` remains an optional secondary extension and stays off in the
  first config to avoid a second moving part.
- The export and evaluation surface stayed fixed throughout this pass:
  - same frozen widened dataset family
  - same packet export tools
  - same teacher-packet evaluator
- The corrected bounded result is mixed rather than clearly positive:
  - `teacher-mse_avg` improved from `0.4888` to `0.4821`
  - `bpp_avg` worsened from `23.8555` to `23.9277`
  - `psnr_avg` slipped from `10.4642` to `10.4509`
- The immediate question is no longer implementation validity; it is route
  judgment: whether this first effective repair deserves a larger follow-up or
  whether the next effort should move upward to a packet/interface-level change.

Deferred:
- another teacher-side auxiliary-loss repair
- broader packet-interface redesign before one bounded predicted-side repair is measured
- deeper multimodal / VLM integration before the packet bridge is trustworthy
- reopening codec-line ranking

Next durable action:
- record the corrected bounded main experiment durably on this run line
- write the post-result decision with the current trade-off and caveat
- choose whether to continue scaling the repair or shift to a higher-level
  packet/interface route
