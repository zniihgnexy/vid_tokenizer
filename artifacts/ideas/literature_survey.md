# Literature Survey

## Pass Goal

Turn the confirmed upstream NVRC-derived compression asset into a literature-grounded next direction for a machine-facing downstream pipeline, without reopening the old question of which compression variant should win.

## Strongest Local Constraints

- The accepted baseline contract is still centered on UVG coding gain plus bounded local teacher-path feasibility.
- The imported baseline package contains verification and metric-contract records, but no maintained downstream-task code path.
- Active user requirements explicitly demote the old `readout` continuation and the `DINOv2 richer-teacher` line as default successors.
- The next line should inherit a frozen upstream module and answer whether compressed or reconstructed outputs remain useful for downstream machine understanding.

## Reused Prior Coverage

- User-supplied route judgment: the stable upstream story is a shared semantic-gated dual-path style machine-oriented tokenizer interface, and the next line should not reopen upstream variant ranking.
- Local baseline evidence: current durable artifacts cover coding metrics, teacher-smoke feasibility, and bounded reconstruction results, but not a downstream machine-facing interface.

## Newly Added Papers And Comparisons

### 1. Video Coding for Machines: A Paradigm of Collaborative Compression and Intelligent Analytics

- Paper id: `2001.03569`
- Why it matters: formalizes VCM as a bridge between human-facing reconstruction coding and machine-facing feature coding.
- Takeaway for this quest: the next line should treat the interface layer itself as the main object, not just one more codec tweak.

### 2. Video Coding for Machine: Compact Visual Representation Compression for Intelligent Collaborative Analytics

- Paper id: `2110.09241`
- Why it matters: argues that low-bitrate visual representations should support multiple downstream analytic tasks, not a single fixed task.
- Takeaway for this quest: feature-packet export is scientifically relevant, but it usually requires dedicated representation design and transfer machinery.

### 3. Task-Aware Encoder Control for Deep Video Compression

- Paper id: `2404.04848`
- Why it matters: shows that one codec with task-aware encoder control can support multiple machine tasks without retraining a decoder per task.
- Takeaway for this quest: freezing the upstream decoder and adapting only the interface/controller is a defensible first-stage design principle.

### 4. TransVFC: A Transformable Video Feature Compression Framework for Machines

- Paper id: `2503.23772`
- Why it matters: compresses video features once, then transfers them into new task spaces with lightweight modules.
- Takeaway for this quest: feature-space transfer is a strong second-stage route, but it is not the cheapest first runnable pipeline because it assumes explicit feature export and transform hooks.

### 5. Egocentric Video-Language Pretraining

- Paper id: `2206.01670`
- Why it matters: establishes egocentric retrieval and classification as stable downstream targets with open training and evaluation structure.
- Takeaway for this quest: a minimal downstream task can reasonably be retrieval or clip-level classification instead of a generative agent pipeline.

### 6. Learning Video Representations from Large Language Models

- Paper id: `2212.04501`
- Why it matters: LaViLa shows strong first-person retrieval and classification transfer, while also giving a later bridge toward larger language-model-conditioned interfaces.
- Takeaway for this quest: a frozen video-language model is a practical example downstream consumer for the first end-to-end pipeline.

### 7. EgoCVR: An Egocentric Benchmark for Fine-Grained Composed Video Retrieval

- Paper id: `2407.16658`
- Why it matters: highlights that egocentric retrieval is meaningful but temporally demanding.
- Takeaway for this quest: composed retrieval is valuable, but it is likely a second-step benchmark after a simpler original-vs-reconstructed retrieval or classification check.

## Frontier

### Candidate A: Reconstructed Video + Teacher-Aligned Metadata + Frozen Retrieval/Classification Consumer

- Mechanism: freeze the upstream compression line, export reconstructed clips plus aligned metadata, and compare original vs reconstructed inputs with a frozen egocentric downstream model.
- Why it is strong now:
  - matches the local asset boundary because reconstruction outputs already exist conceptually in the current package
  - avoids requiring a brand-new compressed-feature codec interface on day one
  - keeps the first comparison interpretable and fair
- Main risk: novelty is moderate because the first step is interface and pipeline value more than a new compression algorithm.

### Candidate B: Tokenizer/Teacher Feature Packet + Lightweight Projection/Transfer Head

- Mechanism: export machine-facing intermediate features and add a small task adapter inspired by VCM multi-task transfer papers.
- Why it is interesting:
  - closer to the long-term machine-native story
  - stronger conceptual novelty if it works
- Why it is not first:
  - current imported baseline package has no maintained feature-export code path
  - requires interface design, storage format, alignment rules, and adapter training all at once
- Main risk: high implementation and comparability risk in the first round.

### Candidate C: Direct VLM/LLM Demo over Compressed Semantic Packet

- Mechanism: connect a larger multimodal model directly to compressed-side packets and judge end-to-end outputs.
- Why it is tempting: strong demo appeal.
- Why it loses now:
  - too many confounds from prompting, API behavior, sampling, and interface design
  - weak attribution if the first result is poor
- Main risk: high ambiguity, low scientific interpretability for round one.

## Winner

`Candidate A` wins this pass.

## Why Candidate A Wins

- It inherits the current quest exactly as a frozen upstream asset rather than reopening codec-line ranking.
- It is the cleanest way to answer the user's main question: can the validated compression module serve a downstream machine consumer at all?
- It gives a minimally confounded first experiment surface:
  - original video input
  - reconstructed video input
  - optional later compressed-side interface input
- It stays compatible with a later move into feature packets or larger VLM/LLM interfaces once the basic pipeline is stable.

## Strongest Reason Not To Choose The Alternatives

- `Candidate B`: better long-term machine purity, but too much new plumbing for the first measured round.
- `Candidate C`: better demo value, but too many uncontrolled variables for the first scientific checkpoint.

## Recommended First-Stage Research Questions

1. Can the frozen upstream compression module export a stable machine-facing interface consisting of reconstructed clips plus aligned metadata?
2. How much downstream utility is lost when a frozen egocentric consumer uses reconstructed input instead of original input?
3. Is the gap small enough to justify a second-stage move toward feature-packet or semantic-packet interfaces?

## Recommended First-Stage Experimental Designs

1. Interface packaging run:
   freeze checkpoint/config/data subset and define the export schema
2. Minimal downstream pipeline run:
   original vs reconstructed comparison with one frozen downstream consumer
3. Optional extension run:
   add one compressed-side or feature-side input path only if the first pipeline is already stable

## Unresolved Overlaps Or Missing Evidence

- We still need one concrete downstream model/repo choice for the first implementation pass.
- We have not yet identified a direct prior work that already combines a frozen VCM-style upstream module with an egocentric downstream retrieval/classification pipeline in the exact way proposed here.
- The current quest has no durable downstream dataset or consumer contract yet; that must be fixed in the experiment stage.

## Promotion Decision

- Promote now: `Candidate A`
- Defer: `Candidate B`
- Reject for round one: `Candidate C`

## Recommended Next Stage

`experiment`
