# Status

Baseline reuse is already resolved: `nvrc-local-source` is the accepted upstream asset.

Current stage: `experiment_prep`

Current judgment:
- The next line should not reopen old compression-variant ranking.
- The parent downstream line already proved the pipeline skeleton: frozen upstream export plus frozen downstream consumer is runnable end to end.
- The reconstructed-video handoff is now a bounded control result, not the preferred interface winner.
- The key parent-line comparison is `original_to_original_top1_accuracy=1.0`, `reconstructed_to_original_top1_accuracy=0.25`, and `reconstructed_to_original_mean_match_rank=2.5`.
- The delta-first packet follow-up stabilized on the same frozen 4-frame surface: `delta-only_top1_accuracy=0.75`, `8x_delta_concat_top1_accuracy=0.75`, and `8x_delta_sum_top1_accuracy=0.5`.
- The active child line is `Delta-Packet Bridge to Frozen Consumer Space`.
- The scientific bottleneck is no longer "does any packet help?" but "can the validated temporal-change packet be turned into a true downstream consumer-facing interface?"
- The repo currently has reusable local assets around `torch` and `torchvision` plus the frozen `resnet18_imagenet` teacher/consumer path; there is no maintained large-model dependency path ready to reuse directly.
- The correct next move is therefore a lightweight local bridge plus a slightly wider bounded validation surface, not a direct VLM/LLM demo.

Current frontier:
1. Recommended: delta-packet bridge with `delta-only` and `delta-dominant concat` variants on a widened bounded surface.
2. Required robustness: keep a widened bounded validation of the current delta signal inside the first bridge experiment package.
3. Deferred: static-context sidecar or other fusion-heavy packet variants.
4. Deferred: larger multimodal or VLM/LLM integration after the bridge line proves itself on local assets.
5. Rejected for now: plain static feature packet as the default machine-facing winner.
6. Rejected for now: simple weighted-sum fusion as the default composition rule.
7. Rejected for now: further scaling of reconstructed video as the primary handoff layer.

Next durable action:
- lock the bridge experiment contract in `PLAN.md` and `CHECKLIST.md`
- pick the widened bounded sample surface
- implement the smallest adapter that maps delta packets into a frozen consumer space
- run one bounded smoke before the first bridge comparison
