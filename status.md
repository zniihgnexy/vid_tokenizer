# Status

Baseline reuse is already resolved: `nvrc-local-source` remains the accepted
upstream asset.

Current stage: `experiment`

Current judgment:
- The run is now on a dedicated branch:
  `run/teacher_anchored_packet_adapter_smoke_r1`.
- The chosen bounded experiment is no longer “find another local loss fix”.
  It is:
  use the existing `4`-frame teacher packet bundle as a retrieval-time memory
  bank and test whether one teacher gallery-anchor projection can improve the
  handoff into `target_feat` space.
- The current local bundle is sufficient:
  - packet payloads already expose `pred_feat`, `target_feat`, `pred_delta`,
    and `target_delta`
  - no exporter change is required for the first smoke
- The strongest bounded evidence right now is:
  - direct `pred_feat -> target_feat` top-1 is only `0.25`
  - direct joint packet matching can already reach `0.75`
  - the old leave-one-out ridge bridge stayed at `0.0`
  - the measured teacher gallery-anchor smoke now reaches `0.75` top-1 and
    `1.5` mean match rank in `target_feat` space with `delta_weight = 8.0` and
    `anchor_logit_scale = 16.0`
  - only query `0000` remains confused with `0001`; queries `0001`, `0002`, and
    `0003` are correct under the new adapter
- The main caveat is explicit:
  this first adapter is a gallery-memory interface, not yet a standalone
  learned bridge. That is acceptable for a first runnable packet-interface
  result batch because the user asked for pipeline evidence first.

Deferred:
- reopening upstream codec or loss-family ranking
- packet bundle schema redesign without concrete missing-field evidence
- a strict leave-one-out adapter as the first packet-interface claim
- direct VLM/LLM integration

Next durable action:
- record the result as a durable main experiment
- write the route decision from this measured packet-memory result
- then decide whether the next best move is a wider packet-memory validation
  package or a deeper interface redesign around the remaining `0000` / `0001`
  confusion
