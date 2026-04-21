# Bounded Query-Adaptive Arbitration over Frozen Teacher-Anchor Packet Bundles

## Abstract

This draft studies a narrow but concrete question: on a fixed widened teacher-anchor retrieval surface, can query-adaptive arbitration extract more downstream retrieval signal from frozen packet bundles than static packet routes? We start from a frozen upstream machine-oriented compression pipeline whose packet bundle interface is already exportable, but whose downstream retrieval behavior remains weak when the handoff is reduced to reconstructed frames or a static packet route. On the current bounded widened teacher-anchor surface, a query-adaptive arbitration rule improves retrieval `top1_accuracy` to `0.15625`, compared with `0.125` for the raw-global route and `0.09375` for the temporal-context route, while also reducing hub-cluster concentration from `0.59375` to `0.28125`.

We emphasize that this is a bounded local result rather than a general interface claim: a later repaired three-bundle follow-up keeps the headline non-oracle top-1 edge for query-adaptive (`0.125` versus `0.10417` for both parent routes), but temporal-context retains the best ranking and chunk-level diagnostics on that broader surface. The contribution is therefore a feasibility result about downstream readout over a frozen packet surface, not a new video coding architecture or a broadly validated machine-facing adapter.

## 1. Problem and Motivation

The larger project goal is to turn a machine-oriented video compression stack into a usable machine-facing interface for downstream models. The current quest has already established that the upstream packet surface can be exported and reused, but the main bottleneck is no longer "can the compression module run?" The bottleneck is whether a frozen packet surface can be handed to a downstream consumer in a way that preserves useful retrieval structure.

Earlier branches showed two important limits. First, reconstructed-video handoff is runnable but loses too much downstream structure to serve as the preferred machine interface. Second, static packet routes can collapse onto a small anchor cluster, which produces brittle nearest-neighbor behavior even when the upstream pipeline itself is stable. This motivates a more adaptive downstream readout over the frozen packet surface.

Relative to VCM-style machine-facing coding work and frozen-interface transfer systems \cite{duan2020vcm,ge2024taskaware,sun2025transvfc}, this manuscript does not propose a new codec or a task-general feature compression scheme. Relative to egocentric video-language pretraining and multi-grained retrieval systems \cite{lin2022egovlp,zhao2022lavila,ma2022xclip}, it does not claim a broadly validated downstream adapter. Its contribution is narrower: given a frozen packet surface that is already exportable, we show that query-adaptive arbitration can recover more retrieval signal than static routing on one fixed bounded surface, which clarifies where the next stage of interface work should focus.

## 2. Frozen Upstream Interface Contract

The current paper line keeps the upstream teacher-anchor packet bundle frozen. We do not change the coding backbone in this stage, and we do not claim a new coding-gain result from this bounded retrieval experiment. The accepted NVRC metrics remain in the recorded run for compatibility with the confirmed baseline contract, but they are reference-only placeholders here rather than the surface that distinguishes the new route.

What changes in this line is only the downstream arbitration logic over already-exported packet representations. That makes the current result interpretable as a machine-interface study: if a better downstream decision rule can extract more retrieval signal from the same frozen packets, then the packet surface is carrying useful structure even before any larger-model integration.

## 3. Query-Adaptive Arbitration Hypothesis

The working hypothesis is that the teacher-anchor packet surface contains complementary signals that static routing rules fail to combine well. Raw-global routing keeps wider coverage but suffers from hub concentration. Temporal-context routing can reduce collapse in some cases, but it is not reliably stronger on the main retrieval target. A query-adaptive rule should therefore perform better if it can decide when to trust each parent route without changing the upstream packets themselves.

In the current bounded smoke, the rule is intentionally simple and non-learned: it keeps the raw-global route by default and switches to the temporal-context route only when the two parent routes disagree and the raw route remains hub-risky. No retraining, learned fusion weights, or packet-schema changes are introduced in this pass.

This is deliberately a narrow hypothesis. The claim is not that query-adaptive arbitration solves the full downstream interface problem, and not that it dominates every metric. The claim is only that on the current bounded surface, adaptive route choice can recover useful signal that static packet routes leave on the table.

## 4. Bounded Query-Adaptive Evaluation

We evaluate on the same bounded widened teacher-anchor retrieval surface used by the parent routes. The comparison isolates downstream arbitration only: the packet surface, evaluation harness, and local retrieval setup stay fixed.

| Route | Top-1 accuracy | Chunk top-1 accuracy | Hub-cluster share |
|---|---:|---:|---:|
| Raw-global | 0.12500 | 0.21875 | 0.59375 |
| Temporal-context | 0.09375 | 0.37500 | 0.28125 |
| Query-adaptive | 0.15625 | 0.25000 | 0.28125 |
| Oracle best-of-two | 0.15625 | 0.34375 | n/a |

The main positive result is that query-adaptive arbitration reaches the best observed `top1_accuracy` on this surface, improving over both static parents and matching the best-of-two oracle on the headline retrieval target. Just as important, it avoids the severe hub concentration seen in the raw-global route. This suggests the adaptive rule is not merely trading one collapse mode for another.

The oracle row is included only as a diagnostic upper bound on this bounded surface. It is not a deployable route, because it assumes hindsight access to which parent route will win for each query.

At the same time, the win is not uniform across all submetrics. Temporal-context still has higher chunk-level top-1 accuracy (`0.37500`) than the query-adaptive rule (`0.25000`). This means the current route should be described as a bounded retrieval improvement rather than a globally dominant interface. The current evidence supports "better headline retrieval on this surface" more strongly than "better on every downstream statistic."

The result should also be read as evidence about the packet surface, not only about the arbitration rule. Because the upstream packet bundle is frozen throughout this comparison, any gain from the adaptive route says that useful downstream structure is already present in the exported teacher-anchor representation and is being left underused by the two static routes.

## 5. Outcome Interpretation and Next Route

The current result is enough to justify a first paper-style draft because it shows a real and interpretable positive local signal on a fixed downstream surface. The useful conclusion is that the frozen packet bundle already contains recoverable downstream structure, and that adaptive arbitration over teacher-anchor packet routes is a credible mechanism for extracting more of it.

The main limitation is scope, but the boundary is now clearer than before. The headline evidence in this draft still comes from one bounded local retrieval surface and not from a larger downstream model. A later repaired three-bundle validation preserved the best non-oracle top-1 for query-adaptive (`0.125` versus `0.10417` for both static parents), but it did not preserve uniform dominance: temporal-context still had the best `mean_match_rank` (`7.8125`) and `chunk_top1_accuracy` (`0.33333`). That follow-up supports carrying query-adaptive forward as the current incumbent readout rule, while also making it clear that broader superiority is still unsupported. An earlier wider-surface QB-Norm revalidation is therefore kept only as appendix-level robustness evidence: it improved anchor geometry without improving top-1 retrieval, which is exactly why the current manuscript does not claim broader route stability.

A separate first downstream-consumer bridge smoke on the recovered `16`-sample chunked teacher-packet bundle was also negative: the weakest direct control stayed at `0.0625` top-1, while both low-capacity ridge bridge variants fell to `0.0`. This extra negative result sharpens the same boundary from a different angle: broader consumer transfer is still unsupported, so the paper should keep that direction in future work rather than treat it as hidden supporting evidence.

The next route should therefore preserve this narrow claim in writing while preparing one of two strengthening moves: either broader validation on additional retrieval surfaces, or a larger machine-facing consumer that tests whether the same packet signal survives beyond the current local smoke setting.
