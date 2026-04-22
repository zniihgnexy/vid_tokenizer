# Related Work Map

## Current Positioning

This paper line should be presented as a **bounded feasibility step** over a frozen packet surface.

It is **not** claiming:

- a new video coding architecture
- a task-general feature compression scheme
- a broadly validated downstream adapter for egocentric retrieval

It **is** claiming:

- on one fixed widened teacher-anchor retrieval surface, query-adaptive arbitration recovers more headline retrieval signal than two static packet routes
- the gain is interpretable because the upstream packet bundle stays frozen throughout the comparison

## Family 1: Machine-Facing Video Coding And Feature Compression

Relevant papers already surfaced in the quest literature survey:

- `2001.03569` Video Coding for Machines: machine-facing coding should be treated as its own interface problem, not only as reconstruction coding.
- `2110.09241` Video Coding for Machine: compact representations should support downstream analytic tasks, not only one codec-internal target.
- `2404.04848` Task-Aware Encoder Control for Deep Video Compression: freezing most of the upstream system and adapting the interface/controller is a defensible design pattern.
- `2503.23772` TransVFC: feature-space transfer is a strong longer-term route, but it assumes richer export and transfer machinery than this paper currently uses.

Current distinction:

- those works motivate why machine-facing interfaces matter
- this paper does not introduce a new machine-oriented codec or feature-transform stack
- this paper asks a narrower question: does the already exported frozen teacher-anchor packet surface contain usable downstream structure that a better readout rule can recover?

## Family 2: Egocentric Downstream Consumers

Relevant papers already surfaced in the quest literature survey:

- `2206.01670` Egocentric Video-Language Pretraining: retrieval/classification is a meaningful first downstream task family.
- `2212.04501` Learning Video Representations from Large Language Models (LaViLa): a frozen video-language style consumer is a practical downstream interface target.
- `2407.16658` EgoCVR: egocentric retrieval is meaningful but temporally demanding, which justifies keeping the current claim bounded.

Current distinction:

- these works justify the downstream task surface
- this paper is not claiming a stronger egocentric retriever
- the novelty lives in the frozen packet-surface readout question, not in the downstream consumer itself

## Family 3: Retrieval Alignment And Lightweight Adaptation

Relevant papers already surfaced in the quest literature survey:

- `2207.07285` X-CLIP: multi-grained retrieval benefits from preserving coarse and fine temporal structure.
- `2410.15624` Test-time Adaptation for Cross-modal Retrieval with Query Shift: query-side shift can materially hurt retrieval and may require adaptation.
- `2206.13559` ST-Adapter: lightweight temporal adapters can improve frozen-backbone video transfer.
- `2205.13535` AdaptFormer: small adapters are credible when the main issue is transfer rather than re-training the backbone.
- `2301.07868` MV-Adapter: retrieval-oriented lightweight video adaptation is literature-supported.

Current distinction:

- these works justify why lightweight downstream adaptation is scientifically plausible
- this paper still stays below that claim level: it uses a hand-built query-adaptive arbitration rule rather than a learned broad adapter family
- the safe wording is "bounded downstream arbitration over a frozen packet surface", not "general machine-facing adapter"

## Safe Novelty Boundary

The safest novelty statement for the current draft is:

1. the upstream teacher-anchor packet bundle is held fixed
2. the comparison surface is fixed
3. query-adaptive arbitration improves the headline retrieval target over both static parent routes on that surface
4. therefore the frozen packet surface already contains downstream-recoverable structure that static routing leaves underused

## Citation Follow-Up

Before bundle preparation, convert the paper ids above into final bibliography entries and add in-text citations to the draft. The minimum paper-facing citation set should cover:

- one VCM / machine-facing coding reference
- one feature-transfer / frozen-interface reference
- one egocentric downstream-task reference
- one retrieval-adaptation or multi-grained alignment reference
