# Teacher-Anchored Packet Adapter Literature Survey

## Scope

This survey supports the active idea `idea-76fee64d`. The question for this pass
is no longer “which anti-collapse regularizer should be tried next?” but rather:
given a frozen upstream packet bundle that is already exportable, which
retrieval/adapter/distillation route is the most defensible next bounded step
for turning that packet surface into a more usable machine-facing interface?

## Reused Durable Coverage

- Reused the parent downstream control result:
  - `original_to_original_top1_accuracy = 1.0`
  - `reconstructed_to_original_top1_accuracy = 0.25`
  - `reconstructed_to_original_mean_match_rank = 2.5`
  This keeps reconstructed video as a bounded control rather than the preferred
  machine-facing handoff.
- Reused the existing teacher-feature packet exporter and its manifest contract.
  The current bundle already contains frame-level packet paths, decoded/eval
  metrics, aggregate metrics, and `teacher_packet_summary`.
- Reused prior packet-side measurements showing that the current bottleneck is
  not simply “no bridge exists”:
  - direct packet comparisons are weak but non-zero
  - the naive ridge bridge can be worse than the direct packet controls
- Reused the corrected variance-floor run only as route evidence:
  it is now a valid measured result, but its trade-off is mixed and therefore
  does not dominate the interface-level route.
- Reused the earlier anti-collapse literature sweep as background only. BYOL,
  SimSiam, VICReg, Barlow Twins, DINO, and dimensional-collapse analyses still
  explain why collapse mattered, but they are no longer the main decision-making
  neighborhood for this interface-focused pass.

## Newly Added Papers This Pass

### 1. CLIP4Clip

- Paper: Luo et al., “CLIP4Clip: An Empirical Study of CLIP for End to End Video Clip Retrieval” (arXiv:2104.08860)
- Mechanism:
  start from a frozen or lightly adapted image-language backbone and transfer it
  into video retrieval with compact temporal aggregation.
- Useful signal:
  strong video retrieval performance can be achieved by reusing a pretrained
  feature space rather than rebuilding the encoder stack from scratch.
- Translation to this quest:
  supports the decision to keep the upstream packet surface frozen and focus the
  next change on the downstream adapter/evaluator layer.

### 2. X-Pool

- Paper: Gorti et al., “X-Pool: Cross-Modal Language-Video Attention for Text-Video Retrieval” (arXiv:2203.15086)
- Mechanism:
  query-conditioned attention that emphasizes the most relevant video sub-regions
  instead of using text-agnostic frame pooling.
- Useful signal:
  better retrieval can come from conditioning the aggregation path on a stable
  guide rather than from changing the base feature extractor.
- Translation to this quest:
  supports a teacher-anchored adapter route where packet aggregation or mapping
  is conditioned on a stable teacher-side anchor instead of using only flat
  packet concatenation.

### 3. X-CLIP

- Paper: Ma et al., “X-CLIP: End-to-End Multi-grained Contrastive Learning for Video-Text Retrieval” (arXiv:2207.07285)
- Mechanism:
  multi-grained and cross-grained similarity aggregation, plus attention over the
  similarity matrix, to focus on essential frames and words.
- Useful signal:
  retrieval quality can hinge on how coarse and fine features are aggregated, not
  just on whether a backbone is strong.
- Translation to this quest:
  strengthens the case that the next missing comparison is an aggregation or
  adapter change over the current packet surface, not another codec-side change.

### 4. TS2-Net

- Paper: Liu et al., “TS2-Net: Token Shift and Selection Transformer for Text-Video Retrieval” (arXiv:2207.07852)
- Mechanism:
  temporally shift token features and select informative tokens in spatial and
  temporal dimensions.
- Useful signal:
  token usefulness is not uniform; selection and structured aggregation can
  matter as much as raw token presence.
- Translation to this quest:
  supports the hypothesis that a teacher-anchored adapter should probably act as
  a selective weighting or coefficient mechanism over packet components rather
  than as another unstructured flat bridge.

### 5. TeachCLIP

- Paper: Tian et al., “TeachCLIP: Multi-Grained Teaching for Efficient Text-to-Video Retrieval” (arXiv:2308.01217)
- Mechanism:
  distill heavy, fine-grained teacher models into an efficient student retrieval
  model with an attentional frame-feature aggregation block.
- Useful signal:
  teacher-guided aggregation can improve efficiency and quality without making
  retrieval-time cost explode.
- Translation to this quest:
  directly supports the current route: introduce a teacher-anchored adapter that
  keeps the runtime surface compact instead of widening to a larger-model stack.

### 6. VideoAdviser

- Paper: Wang et al., “VideoAdviser: Video Knowledge Distillation for Multimodal Transfer Learning” (arXiv:2309.15494)
- Mechanism:
  transfer multimodal video knowledge from a stronger teacher into a smaller
  student space for efficient downstream inference.
- Useful signal:
  a compact student representation can inherit useful multimodal structure from a
  teacher without requiring the full teacher computation at inference.
- Translation to this quest:
  supports treating the next bridge as a teacher-guided mapping from packet space
  into a more usable consumer space rather than a full end-to-end retraining
  problem.

## Code-Path Feasibility Readout

- Already available today:
  - `pred_feat`, `target_feat`, `pred_delta`, `target_delta`
  - frame-level packet metrics
  - aggregate run metrics
  - packet paths and teacher packet summary in the manifest
- Already measured today:
  - direct packet controls
  - a naive ridge bridge that performs worse than the direct packet control
- Not yet available today:
  - an explicit teacher-anchored adapter comparison in the packet-side evaluator
- Consequence:
  the next bounded step should reuse the current bundle contract and change the
  evaluator/adapter layer only.

## Serious Candidate Frontier

### Candidate A: reuse the current bundle and add a teacher-anchored adapter comparison

- What it changes:
  keep the exporter and manifest fixed, and add one adapter comparison that maps
  predicted packets into the frozen target space through a teacher-anchored
  basis, coefficient path, or similarly constrained guidance mechanism.
- Why it is serious:
  all required inputs are already present and this is the smallest route that
  directly tests the missing claim.

### Candidate B: redesign the bundle schema first

- What it changes:
  add new exported fields or a new manifest contract before testing another bridge.
- Why it remains alive:
  schema redesign may become necessary if the current bundle proves too weak.
- Why it is not first:
  there is not yet concrete evidence that the current manifest is insufficient.

### Candidate C: jump directly to a larger-model interface

- What it changes:
  attach the packet surface or reconstructed output to a larger consumer model.
- Why it remains alive:
  it is closer to the user's final pipeline ambition.
- Why it is not first:
  it would introduce too many confounds before the local packet handoff is
  trustworthy.

### Candidate D: continue local anti-collapse loss tuning

- What it changes:
  spend the next round inside the same variance-floor or related regularizer family.
- Why it remains alive:
  the last run is now a valid measured result.
- Why it is not first:
  the mixed result already weakened the case for another immediate local repair
  round, while the packet-side evidence now points to a higher-leverage adapter
  bottleneck.

## Selection For This Pass

- Winner: Candidate A
- Strongest support:
  the exporter already works, the bundle schema is stable, direct packet
  controls are weak but real, and the previously measured bridge is too weak.
  That combination makes “one better-scoped teacher-anchored adapter comparison”
  the most defensible next experiment package.
- Strongest reason not to choose Candidate B now:
  it would add schema churn before the current surface is actually exhausted.
- Strongest reason not to choose Candidate C now:
  it would blur the diagnosis before the local packet bridge itself is tested.
- Strongest reason not to choose Candidate D now:
  the latest valid run already answered the low-level implementation question but
  did not produce a clear enough payoff to dominate the interface-level route.
- Main residual risk:
  even a teacher-anchored adapter may fail if the predicted packet geometry is
  too damaged, in which case the correct next move would be a deeper interface
  redesign rather than more evaluator tuning.

## Still Missing Or Unresolved

- There is still no directly matching paper on compression-driven, fixed-teacher,
  video packet adapters with this exact evaluation contract.
- If the teacher-anchored adapter still fails, the next literature gap to close
  will be richer compression-side interfaces rather than more generic retrieval
  papers.

## Recommended Next Anchor

Keep `idea-76fee64d` as the active line, finish rewriting the control files
around this literature judgment, and then hand off to `experiment` for one
bounded packet-adapter smoke that reuses the current bundle and adds exactly one
teacher-anchored adapter comparison.
