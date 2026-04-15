# Main Experiment Plan

## 1. Objective

- run id: `delta_packet_bridge_smoke_r1`
- selected idea in `1-2` sentences: Keep the same frozen shared-gating upstream module and the validated packet exporter, but promote temporal delta from a packet-similarity winner into a true downstream bridge. This child line exists because reconstructed video and plain static packet both stall at `top1=0.25`, while delta-led packet views rise to `0.75` on the same frozen surface.
- user's core requirements:
  - keep the pipeline runnable from upstream compression to downstream machine use
  - produce an inspectable result batch that shows whether this direction is worth doing
  - focus the innovation on pipeline/interface construction rather than reopening codec novelty
  - leave behind code that can be rerun locally and later shared cleanly
- non-negotiable user constraints:
  - do not reopen the upstream codec-line ranking
  - keep the accepted `nvrc-local-source` baseline contract visible
  - treat reconstructed video as a bounded control, not as the default winner
  - avoid a confounded direct VLM/LLM demo before the local bridge is proven
- current pass objective: build the smallest consumer-facing bridge for delta packets and test it on a widened bounded surface
- research question: Can a lightweight delta-packet adapter preserve retrieval or probing structure more faithfully than reconstructed video under the same frozen upstream contract?
- null hypothesis: even with a delta-dominant packet, a consumer-facing bridge still fails to improve meaningfully over the reconstructed-video control
- alternative hypothesis: temporal-change packets carry the useful machine-facing structure, and a lightweight adapter can expose that structure more faithfully than decoded frames or static-heavy packet fusion

## 2. Baseline And Comparability

- baseline id: `nvrc-local-source`
- baseline variant: `tiny-local-teacher-pilot-r3`
- inherited upstream metrics:
  - `bpp_avg=88.2266`
  - `psnr_avg=10.9012`
  - `teacher-mse_avg=0.5126`
- parent-line downstream control:
  - `original_to_original_top1_accuracy=1.0`
  - `reconstructed_to_original_top1_accuracy=0.25`
  - `reconstructed_to_original_mean_match_rank=2.5`
- current packet evidence:
  - `pred_delta_to_target_delta_top1_accuracy=0.75`
  - `pred_feat_plus_8p0x_delta_concat_to_target_feat_plus_8p0x_delta_concat_top1_accuracy=0.75`
  - `pred_feat_plus_8p0x_delta_sum_to_target_feat_plus_8p0x_delta_sum_top1_accuracy=0.5`
- comparison rule:
  - keep the same frozen upstream checkpoint and teacher type
  - widen only the bounded sample surface, not the upstream contract
  - compare reconstructed-video control, `delta-only`, and `delta-dominant concat` bridge variants in the same consumer space
  - record any new adapter explicitly instead of hiding it inside the packet exporter
- comparability risks:
  - widening the surface may accidentally change sample composition too much if not kept bounded and documented
  - adapter gains could be confused with packet gains if the comparison does not keep the packet variants parallel
  - static-context fusion can reintroduce noise and hide whether temporal change is actually the signal source

## 3. Code Translation Plan

| Path | Current role | Planned change | Why this is needed | Risk |
|---|---|---|---|---|
| `experiments/main/scripts/export_teacher_feature_interface.py` | reusable packet exporter | keep as the packet source of truth and expose whatever minimal metadata the bridge needs | preserves compatibility with the validated packet scaffold | low |
| `experiments/main/scripts/run_teacher_packet_eval.py` | packet similarity evaluator | reuse or refactor only the common packet-loading logic | the bridge should inherit the same packet contract, not invent a parallel loader | low |
| `experiments/main/scripts/run_frozen_consumer_eval.py` | parent-line reconstructed-video evaluator | reuse metric/report structure where possible | keeps the bridge comparison legible against the parent control | low |
| `experiments/main/scripts/` | experiment script root | add or extend one lightweight bridge evaluation script | this is the new minimal bridge layer | medium |
| `experiments/main/interface_bundles/` | packet bundle roots | reuse the existing bundle format and add widened-surface outputs under a new bounded root | keeps evidence auditable and parallel to the current packet work | low |
| `experiments/main/evals/` | evaluation roots | store widened bridge summaries, reports, and bridge embeddings under a new run folder | makes the next decision depend on durable outputs rather than chat memory | low |

## 4. Execution Design

- minimal experiment:
  - use the only currently available 4-frame packet surface as a bounded smoke
  - load the existing delta packets from the frozen exporter
  - compare direct delta alignment and lightweight bridge variants in the frozen consumer space
  - treat any learned adapter result on this surface as smoke only, not as a robustness claim
- smoke / pilot plan:
  - verify packet/sample alignment on the widened surface
  - run the bridge only on the bounded widened subset
  - confirm that metrics are interpretable and directly comparable to the parent control
- expected outputs:
  - bridge evaluation script and configuration
  - one 4-frame smoke summary for direct and learned bridge variants
  - one judgment on whether the bridge signal is strong enough to justify seeking a wider surface
- stop condition:
  - the widened bridge smoke runs end to end and produces an interpretable comparison
- abandonment condition:
  - no widened bounded surface is available without breaking the current contract
  - the adapter path becomes larger than a minimal local extension
  - packet/sample alignment on the widened surface cannot be trusted

## 5. Runtime Strategy

- immediate next actions:
  - keep the completed 4-frame smoke as the bounded first bridge result
  - search for or regenerate a wider bounded packet surface
  - treat direct delta alignment as incumbent and learned bridge variants as currently unsupported on this smoke surface
- artifact locations:
  - parent control root:
    `../idea-idea-3ed587d5/experiments/main/shared_gating_downstream_interface_bootstrap_r1/downstream_eval/`
  - current packet follow-up root:
    `../idea-idea-44a0e404/experiments/main/evals/delta_dominant_teacher_packet_followup_r1/`
  - new bridge eval root:
    `experiments/main/evals/delta_packet_bridge_smoke_r1/`
- safe efficiency levers:
  - keep the upstream frozen
  - keep the bridge lightweight and local
  - prefer widened bounded smoke before any heavier run

## 6. Fallbacks And Recovery

- if a true consumer-space bridge is too large:
  - fall back to direct delta alignment as the current bridge layer
- if the widened bounded surface is unavailable:
  - record that limitation explicitly and keep the current 4-frame result as smoke only
- if `delta-dominant concat` collapses while `delta-only` stays strong:
  - continue with `delta-only` as the active bridge payload and downgrade concat to control
- if both bridge variants collapse:
  - classify the line as not yet consumer-ready and route back through decision before scaling

## 7. Checklist Link

- checklist path: `CHECKLIST.md`
- next unchecked item: find or regenerate a wider bounded packet surface under the same upstream contract
