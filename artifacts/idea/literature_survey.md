# Query-Side Anti-Collapse Literature Survey

## Scope

This survey supports the active idea `idea-2835dace` on the frozen widened packet
bridge surface. The question for this pass is narrow: after two negative
teacher-side repair attempts, which minimal anti-collapse mechanism is most
defensible for the predicted-side packet bottleneck without reopening codec
ranking or changing the packet evaluator?

## Reused Durable Coverage

- Reused local evidence from the earlier collapse-localization package:
  exported predicted packets are already collapsed while target packets remain
  discriminative, and the earliest accessible collapse surface is
  `exported_predicted_packets_or_earlier`.
- Reused the bounded blueprint downgrade and the bounded relation negative
  result as the two measured failures that weaken further teacher-side repair.
- Reused prior idea-line notes that already narrowed the candidate mechanism
  families to localization-first anti-collapse controls rather than evaluator
  redesign.

## Newly Added Papers This Pass

### 1. BYOL

- Paper: Grill et al., "Bootstrap your own latent" (arXiv:2006.07733)
- Mechanism: online/target asymmetry with EMA teacher
- Useful signal:
  a non-contrastive learner can avoid collapse through asymmetric prediction
  structure rather than negatives.
- Translation to this quest:
  useful as a comparison point, but weaker as the first local repair here
  because the current target path is already fixed through frozen teacher
  features; adding more stop-gradient-like asymmetry alone is unlikely to change
  the accessible failure surface.

### 2. SimSiam

- Paper: Chen and He, "Exploring Simple Siamese Representation Learning"
  (arXiv:2011.10566)
- Mechanism: stop-gradient as a key anti-collapse ingredient
- Useful signal:
  explicit asymmetry can be decisive when both branches would otherwise co-adapt
  into collapse.
- Translation to this quest:
  important as disconfirming context. The current quest already uses a fixed
  teacher target, so the main lesson is not "add stop-gradient again", but
  "check whether the current collapse is really caused by missing asymmetry". The
  answer here appears to be no.

### 3. VICReg

- Paper: Bardes et al., "VICReg" (arXiv:2105.04906)
- Mechanism: explicit variance floor plus covariance regularization
- Useful signal:
  collapse can be addressed directly with a per-dimension variance term instead
  of relying on implicit architectural bias.
- Translation to this quest:
  this is the best first-match mechanism for the current bottleneck because the
  measured failure is exactly low-diversity predicted-side packet structure on an
  otherwise fixed comparison surface.

### 4. Barlow Twins

- Paper: Zbontar et al., "Barlow Twins" (arXiv:2103.03230)
- Mechanism: redundancy reduction via cross-correlation identity objective
- Useful signal:
  decorrelation can prevent trivial constant or low-information embeddings
  without negative pairs or momentum updates.
- Translation to this quest:
  a plausible second-choice repair if a pure variance floor is too weak, but it
  is a larger objective change than the variance-first route and is therefore
  better kept as the immediate fallback rather than the first intervention.

### 5. DINO

- Paper: Caron et al., "Emerging Properties in Self-Supervised Vision
  Transformers" (arXiv:2104.14294)
- Mechanism: self-distillation with teacher-student asymmetry
- Useful signal:
  teacher-side stabilization and distilled targets can preserve semantic
  structure.
- Translation to this quest:
  relevant mostly as a reminder that teacher-side stabilization can help when
  the teacher branch itself is trainable. Here the teacher encoder is already
  fixed, so DINO is weaker support for another teacher-side repair than for
  keeping the teacher features as the stable target surface.

### 6. Understanding Dimensional Collapse in Contrastive SSL

- Paper: Jing et al., "Understanding Dimensional Collapse in Contrastive
  Self-supervised Learning" (arXiv:2110.09348)
- Mechanism: collapse diagnosis and representation-space direct optimization
- Useful signal:
  collapse is not only a trivial all-constant failure; a representation can
  retain some task signal while still shrinking into a low-dimensional subspace.
- Translation to this quest:
  this strengthens the current interpretation of the blueprint result: improved
  self-discrimination is not enough if predicted-side representations still do
  not span a useful alignment space against targets.

### 7. Understanding Collapse in Non-Contrastive Siamese Representation Learning

- Paper: Li et al., "Understanding Collapse in Non-Contrastive Siamese
  Representation Learning" (arXiv:2209.15007)
- Mechanism: collapse metrics and size-sensitivity analysis
- Useful signal:
  partial dimensional collapse can forecast downstream weakness even when a
  system does not look fully degenerate.
- Translation to this quest:
  matches the current observed pattern closely: the packet bridge no longer looks
  like a pure constant-vector failure, but the measured alignment remains too
  weak to support downstream use.

## Code-Path Feasibility Readout

- Accessible today:
  `pred_feat`, `target_feat`, `pred_delta`, `target_delta`, relation matrices,
  and the current packet export/evaluator surfaces.
- Not exposed today:
  `query_projection` and `query_packet_head`; the localization package records
  them as missing surfaces.
- Consequence:
  the first repair should favor mechanisms that can act on currently accessible
  predicted-side tensors. This makes explicit variance control more feasible than
  a new asymmetric twin-branch objective.

## Serious Candidate Frontier

### Candidate A: localization-first plus explicit variance-floor repair

- What it changes:
  add a bounded predicted-side anti-collapse control on the accessible
  `pred_feat` / `pred_delta` surfaces, with an optional lightweight covariance
  term only if needed.
- Why it fits:
  matches the measured failure mode directly, preserves the existing evaluation
  contract, and is the smallest credible code change.

### Candidate B: redundancy-reduction or covariance-heavy repair

- What it changes:
  move beyond a variance floor and explicitly decorrelate predicted packet
  dimensions.
- Why it remains alive:
  Barlow-style decorrelation is well motivated if variance alone improves
  diagnostics but not target alignment.
- Why it is not first:
  it is a broader objective change and would be harder to interpret if the next
  result is still negative.

### Candidate C: return to interface redesign

- What it changes:
  give up on another local repair and go back to chunk-aware or packet-structure
  redesign.
- Why it remains alive:
  if deeper query-side surfaces stay inaccessible or a bounded predicted-side
  repair still fails, the correct move is to reopen interface-level redesign.
- Why it is not first:
  the direct predicted-side collapse evidence is too strong to skip one minimal
  predicted-side repair.

## Selection For This Pass

- Winner: Candidate A, localization-first plus explicit variance-floor repair
- Strongest support:
  two measured teacher-side repairs already failed, the teacher target is
  already asymmetric and fixed, and the accessible failure surface is low-diversity
  predicted-side packet structure.
- Strongest reason not to choose Candidate B now:
  it adds more objective complexity before the smallest direct anti-collapse
  control is tested.
- Strongest reason not to choose Candidate C now:
  it would abandon the clearest local bottleneck before one bounded
  predicted-side repair is measured.
- Main residual risk:
  the true failure may lie earlier than the currently accessible packet tensors,
  in which case even a clean variance-floor repair will only produce a clearer
  negative result rather than a rescue.

## Still Missing Or Unresolved

- No directly matching paper studies collapse in a compression-driven,
  fixed-teacher, predicted-packet bridge with this exact packet evaluator.
- A later pass may need one more video-specific temporal-discrimination paper if
  the variance-first repair fails and temporal-local contrastive calibration
  becomes the next serious fallback.

## Recommended Next Anchor

Stay on `idea-2835dace`, revise the branch control files around this literature
judgment, then hand off to `experiment` for one bounded predicted-side
localization-plus-repair package whose first repair is an explicit variance-floor
control on the accessible packet surfaces.
