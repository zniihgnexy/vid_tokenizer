# Literature Survey

## Pass Goal

Turn the failed `chunk-aware local-burst` smoke into a literature-grounded next direction. The new question is no longer whether a chunk-aware evaluator is cleaner; it is whether the predicted packet representation collapses across widened chunks before the downstream bridge can use it.

## Strongest Local Constraints

- The accepted baseline contract is still centered on UVG coding gain plus bounded local teacher-path feasibility.
- The upstream compression/module ranking should stay frozen; this pass is only about the downstream packet bridge.
- The widened 16-frame flat bridge already failed at near chance.
- The chunk-aware smoke also failed:
  - every packet-side chunk-aware metric stayed at `0.25` top-1 with `mean_match_rank=2.5`
  - the target-feature sanity route stayed at `1.0`
- A direct chunk-level cosine probe shows the real new bottleneck:
  - `pred_feat` cross-chunk cosine matrix is all `1.0`
  - `pred_delta` cross-chunk cosine matrix is all `1.0`
  - `target_feat` and `target_delta` still vary across chunks
- Therefore the next route should explain or repair predicted-packet collapse before claiming another interface rescue.

## Reused Prior Coverage

- User-supplied route judgment: the stable upstream story is a shared semantic-gated dual-path style machine-oriented tokenizer interface, and the next line should not reopen upstream variant ranking.
- Local baseline evidence: durable artifacts already cover coding metrics, teacher-smoke feasibility, and a runnable downstream pipeline skeleton.
- Existing VCM and downstream-interface survey coverage still matters for the broader quest framing:
  - `2001.03569` Video Coding for Machines: collaborative human/machine coding framing
  - `2110.09241` Video Coding for Machine: compact visual representation compression for multi-task analytics
  - `2404.04848` Task-Aware Encoder Control for Deep Video Compression: freeze codec, adapt task-facing control/interface
  - `2503.23772` TransVFC: transferable feature-compression route
  - `2206.01670` Egocentric Video-Language Pretraining: practical egocentric retrieval/classification consumer
  - `2212.04501` LaViLa: frozen video-language consumer route
  - `2407.16658` EgoCVR: temporally demanding egocentric retrieval benchmark

## Newly Added Papers And Comparisons

### 1. SimCLR: A Simple Framework for Contrastive Learning of Visual Representations

- Paper id: `2002.05709`
- Why it matters: keeps instance discrimination explicit through a contrastive objective and projection head.
- Takeaway for this pass: if the query packet branch has lost chunk discrimination entirely, a minimal contrastive calibration over chunks is a more defensible fix than more aggregation tricks.

### 2. SimSiam: Exploring Simple Siamese Representation Learning

- Paper id: `2011.10566`
- Why it matters: shows that collapse can happen even in simple prediction-based Siamese setups, and that stop-gradient asymmetry is a key anti-collapse ingredient.
- Takeaway for this pass: if the packet head behaves like a symmetric prediction branch, the next fix should first test whether a small asymmetry or stop-gradient style control is missing.

### 3. Barlow Twins: Self-Supervised Learning via Redundancy Reduction

- Paper id: `2103.03230`
- Why it matters: avoids trivial constant solutions by making cross-correlation close to identity and reducing redundancy across dimensions.
- Takeaway for this pass: if chunk queries have become identical vectors, redundancy-reduction style controls are a cleaner second-step fix than more heuristic packet fusion.

### 4. VICReg: Variance-Invariance-Covariance Regularization for Self-Supervised Learning

- Paper id: `2105.04906`
- Why it matters: makes anti-collapse explicit with a variance floor plus covariance regularization instead of relying on implicit architectural bias.
- Takeaway for this pass: a variance-preserving packet head is a concrete, literature-backed fallback if the diagnostic package localizes collapse to the exported query representation.

### 5. Bootstrap Your Own Latent (BYOL)

- Paper id: `2006.07733`
- Why it matters: keeps an online predictor and a slowly updated target branch asymmetric without negative pairs.
- Takeaway for this pass: if the target-side packet fields remain diverse while the predicted query packet collapses, a small target/query asymmetry is a cleaner first repair than changing the evaluator again.

### 6. TCLR: Temporal Contrastive Learning for Video Representation

- Paper id: `2101.07974`
- Why it matters: explicitly improves temporal diversity by discriminating non-overlapping clips and timesteps from the same video.
- Takeaway for this pass: if localization finds that chunk information survives before the final query projection, a chunk-local temporal contrastive calibration is a defensible fallback that matches the current bottleneck more directly than another static packet fusion.

### 7. Implicit Variance Regularization in Non-Contrastive SSL

- Paper id: `2212.04858`
- Why it matters: explains why predictor-style asymmetry can avoid collapse through implicit variance regularization even under cosine-style objectives.
- Takeaway for this pass: because the current packet bridge already uses cosine-based comparisons, localizing per-dimension variance loss in the query head is more principled than guessing a heavier bridge objective first.

## Frontier

### Candidate A: Query-Side Packet Collapse Diagnosis on the Frozen Widened Surface

- Mechanism:
  - keep the same frozen widened chunk bundles and the current chunk-aware evaluator
  - instrument discrimination at three levels: target fields, exported predicted packets, and any query-side packet head or projection
  - if collapse localizes to the query-side packet head, test the smallest diversity-preserving control on the same bounded surface
- Why it is strong now:
  - directly matches the new evidence instead of guessing another evaluator variant
  - preserves the accepted comparability contract because the data, upstream export, and evaluator are already fixed
  - is the cheapest route that can tell whether the packet line is still salvageable
- Main risk:
  - the collapse may already exist before packet export, in which case a local query-head fix will not be enough

### Candidate B: Direct Diversity-Preserving Packet Head Without First Localizing the Collapse

- Mechanism:
  - move straight to a diversity-preserving packet head inspired by SimSiam or BYOL asymmetry, VICReg variance floors, Barlow Twins redundancy reduction, or TCLR-style temporal contrastive calibration
  - keep the current widened chunk surface as the validation set
- Why it is interesting:
  - most likely to produce an immediate measurable improvement if the collapse truly comes from the packet-side prediction head
- Why it is not first:
  - without localizing the failure layer, this mixes diagnosis and repair and makes the next negative result harder to interpret
- Main risk:
  - fixes the wrong layer and turns the next pass into another confounded “maybe the regularizer was wrong” story

### Candidate C: Abandon the Packet Bridge Line and Fall Back to Reconstructed or Target-Side Controls

- Mechanism:
  - treat the packet-side collapse as terminal and retreat to already-known reconstructed or target-side baselines
- Why it loses now:
  - the target fields remain discriminative, and older 4-frame local delta evidence was positive enough that one diagnostic pass is still justified
- Main risk:
  - abandons a still-explainable failure mode too early

## Winner

`Candidate A` wins this pass.

## Why Candidate A Wins

- It is the only route whose mechanism is already supported by direct local evidence: the query packets are constant while the target packets are not.
- It keeps the failure interpretable because it does not change the data surface, upstream export, or downstream evaluator before localizing the collapse.
- It preserves the option to import one small anti-collapse control from SimSiam, Barlow Twins, VICReg, BYOL, or TCLR only after the failing layer is identified.

## Strongest Reason Not To Choose The Alternatives

- `Candidate B`: the literature is relevant, but applying a regularizer before localizing the collapse would turn the next result into another confounded guess.
- `Candidate C`: it would throw away a live, explainable failure mode even though the target-side representations still carry chunk-specific structure.

## Recommended Next-Stage Research Questions

1. At which surface does chunk discrimination disappear: before packet export, inside the predicted packet head, or only after a specific bridge transform?
2. If the collapse localizes to the query-side packet head, is one minimal diversity-preserving control enough to lift chunk-aware bridge accuracy above four-way chance?
3. If no query-side surface retains chunk discrimination, should the packet bridge line be downgraded in favor of a cleaner upstream-facing interface claim?

## Recommended Next Experimental Designs

1. Collapse-localization run:
   measure cross-chunk discrimination at target fields, predicted packets, and any query-side projection/head
2. Minimal anti-collapse control run:
   only if localization points to the packet-side head, add one small stop-gradient, variance-floor, redundancy-reduction, or temporal-contrastive control and re-evaluate on the same four-chunk surface
3. Decision follow-up:
   continue the packet bridge only if chunk-aware bridge accuracy rises above chance with a non-collapsed query representation

## Unresolved Overlaps Or Missing Evidence

- We still need to localize whether the collapse is introduced before or after the exported packet files.
- The survey now supports four plausible repair families, but we do not yet know which one maps cleanly onto the current packet head:
  - target/query asymmetry
  - explicit variance floors
  - redundancy reduction
  - chunk-local temporal contrastive calibration
- If the discriminative signal is already gone upstream of packet export, the packet-bridge story may need a more serious downgrade than a local regularizer.

## Promotion Decision

- Promote now: `Candidate A`
- Defer until localization is complete: `Candidate B`
- Reject for now: `Candidate C`

## Recommended Next Stage

`experiment`
