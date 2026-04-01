## Project Identity

This project studies **machine-oriented egocentric video compression**.

The core idea is to compress egocentric videos into a **compact representation** that is easier to store and transmit, while preserving the information needed by downstream machine understanding models. The compression target is **not primarily human visual quality**, but **machine-usable semantic and temporal information**.

This document is the **fixed core project definition**. Future development, discussion, literature search, implementation, and experimental design should stay aligned with this document unless the user explicitly decides to revise the core idea.

---

## Fixed Core Idea

The current project idea is:

- Input: an egocentric video sequence `x`
- Compression backbone: an INR-based neural video compression method, currently discussed in the context of **NVRC-style** pipelines
- Reconstruction: `x_hat`, reconstructed from the compressed representation
- Teacher / tokenizer branch:
  - `x -> tokenizer -> y`
  - `x_hat -> tokenizer -> y_hat`
- Main machine-oriented training signal:
  - minimize the difference between `y` and `y_hat`
  - currently understood as a feature-level consistency objective such as MSE on continuous token/feature representations

The intended training sketch is:

```text
x -> NVRC -> x_hat -> tokenizer -> y_hat
x --------------------> tokenizer -> y
loss(y_hat, y)
````

The meaning of this design is:

* the model should learn to compress video into a smaller form
* the compressed-and-reconstructed video should still produce nearly the same machine representation as the original video
* therefore, the compression preserves information useful for downstream machine understanding

This project should **not** be reframed as ordinary human-perception video compression unless the user explicitly requests that change.

---

## Problem Statement

Egocentric videos are long, redundant, storage-heavy, and expensive to process directly with large vision or vision-language models. Traditional video compression mainly optimizes for human viewing quality, but this may not preserve the information most useful for machine reasoning.

This project asks:

> Can we compress egocentric videos into compact representations while preserving the information required by tokenizer-level machine understanding?

The goal is to build a compression framework that is:

1. compact enough for storage/transmission efficiency,
2. useful for downstream machine tasks,
3. ideally less tied to any single downstream large model.

---

## Current Intended Storyline

The current paper/storyline should remain centered around the following logic:

1. **Egocentric videos are long and costly** to store, transmit, and process.
2. **Traditional video compression is human-oriented**, not necessarily machine-oriented.
3. For downstream understanding, what matters is not only pixel fidelity, but whether compressed videos still preserve the representations used by machine models.
4. Therefore, the project uses a tokenizer/teacher branch to define what information should be preserved.
5. The core objective is to make the machine representation of the compressed video close to that of the original video.
6. The project aims at **machine-friendly compression**, not merely visual reconstruction quality.

When helping with writing, coding, or experiment planning, always preserve this storyline.

---

## Important Definitions

### 1. `x`

Original egocentric video.

### 2. `NVRC`

Current compression backbone family under consideration. In current understanding, this refers to an **INR-based neural video compression** framework.

### 3. `x_hat`

Reconstructed video after compression.

### 4. `tokenizer`

In this project, "tokenizer" does **not necessarily mean a text tokenizer**.

It should be understood more broadly as a **visual tokenization / feature extraction / teacher front-end** that maps video into machine-usable representations.

Possible forms include:

* patch tokens
* frame embeddings
* clip embeddings
* hidden states
* continuous visual features

Unless otherwise stated, future discussions should treat the tokenizer as a **teacher representation interface**, not as a language-only tokenizer.

### 5. `y` and `y_hat`

* `y = tokenizer(x)`
* `y_hat = tokenizer(x_hat)`

These are machine representations extracted from original and compressed videos.

### 6. Core machine-oriented objective

Preserve representation consistency:

```text
y_hat ≈ y
```

A default mathematical form is:

```text
L_tok = || tokenizer(x_hat) - tokenizer(x) ||^2
```

In practice, this usually refers to **continuous feature matching**, not direct MSE on discrete token IDs.

---

## Current Technical Interpretation

The project currently interprets the pipeline as:

* a video is compressed into a compact representation
* the compressed representation is smaller and therefore more storage-friendly
* after reconstruction, the resulting video should still be compatible with tokenizer-based downstream processing
* the preserved target is **machine-relevant information**, not necessarily all pixel detail

This project should be described as:

* **machine-oriented video compression**
* **video coding for machine understanding**
* **tokenizer-level semantic consistency preservation**

Avoid simplifying the project into:

* "just making videos smaller"
* "ordinary reconstruction compression"
* "tokenizer for tokenizer’s sake"

The tokenizer branch is used because it defines **what information matters to the machine**.

---

## INR / NVRC Assumption and Limitation

A critical current assumption is:

* the compression backbone is INR-based
* INR-based video methods are currently understood as often requiring **per-video instance fitting / overfitting**
* therefore, this project should **not automatically be described as a fully universal one-shot compression network**

Current default understanding:

* each video may require its own fitting/compression process
* the output is a compact representation specialized to that video
* the broader contribution is the **framework and objective design**, not necessarily a universally pre-trained codec

When discussing generalization, carefully distinguish between:

### A. codec parameter generalization

Whether one trained compression network directly applies to all unseen videos.

### B. method-level generalization

Whether the **idea**, **objective**, and **machine-oriented compression principle** generalize across videos, teachers, or tasks.

Do not blur these two meanings.

---

## Generalization View of the Tokenizer Branch

A current deeper interpretation of the project is:

* the tokenizer/teacher branch defines what machine-relevant information should survive compression
* if training uses multiple possible tokenizers/teachers, the compression model may learn more general machine-relevant information
* the intuition is that if the model is trained to preserve representations under one subset of teachers, it may also perform well under another subset

However, this is currently an **interpretation and future direction**, not yet a locked experimental design.

Therefore:

* keep the current core idea unchanged
* multi-tokenizer or teacher randomization may be discussed as a future design option
* do not convert the project into a different teacher-learning paper unless explicitly requested

---

## Current Research Goal

The present goal is **not** to finalize one specific downstream model.

Instead, the project seeks to learn a compressed representation that can remain useful for **general downstream machine understanding**.

This means:

* do not lock the project too early to one foundation model
* do not assume one fixed tokenizer is the only valid choice
* preserve the project’s intended **generalization-oriented framing**

A good default description is:

> Learn a compact compressed representation for egocentric video that preserves tokenizer-level machine understanding signals and remains useful for downstream tasks.

---

## Non-Goals

Unless the user explicitly changes direction, the project is **not currently**:

1. a pure human-visual video compression project,
2. a standard task-specific feature distillation project,
3. a universal pretrained codec that is guaranteed to work zero-shot on all videos,
4. a pure 3D reconstruction project,
5. a pure tokenizer design project,
6. a benchmark-only downstream task paper.

These may be discussed, but they are not the current main story.

---

## Optional Extension Space (Do Not Turn Into Main Idea Automatically)

The project may have natural extension space toward **3D-aware / geometry-aware compression**, especially because egocentric videos often contain spatial and motion information important for downstream reasoning.

However, this must be treated as:

* a future extension,
* or an auxiliary branch,
* not a replacement of the current core idea.

If discussed, the correct framing is:

* preserve semantic information through tokenizer consistency
* optionally preserve geometric cues through depth/pose/3D-aware consistency
* but the main pipeline remains a **machine-oriented egocentric video compression framework**

Do not rewrite the project into a full 3D compression paper unless explicitly requested.

---

## Recommended Default Mathematical View

The current project can be formalized with the following default notation:

### Compression and reconstruction

```text
x -> C -> z -> D -> x_hat
```

Where:

* `x` is the original egocentric video
* `z` is the compact compressed representation
* `C` is the encoder/compression process
* `D` is the decoder/reconstruction process

### Teacher branch

```text
y = T(x)
y_hat = T(x_hat)
```

Where:

* `T` is the tokenizer / teacher representation model

### Main machine-oriented loss

```text
L_tok = || y_hat - y ||^2
```

### Possible broader loss form

```text
L = λ_rate * L_rate + λ_rec * L_rec + λ_tok * L_tok
```

Where:

* `L_rate` controls compactness / bitrate / storage cost
* `L_rec` controls reconstruction fidelity
* `L_tok` controls machine-representation consistency

Important:

* `L_tok` is conceptually central in this project
* `L_rec` is supportive, not necessarily the main objective
* the project should not drift back into a purely pixel-driven story

---

## Current Open Questions

These questions are still open and should be treated as active research/design items:

1. What exact tokenizer/teacher should be used?
2. What representation should `y` be?

   * hidden states?
   * patch tokens?
   * frame embeddings?
   * clip embeddings?
3. Should the tokenizer be fixed or sampled from multiple teachers?
4. What is the right balance among rate, reconstruction, and token consistency?
5. Should the method remain pure INR/per-video fitting, or later move toward a more general codec?
6. Which downstream tasks are the most appropriate validation targets?
7. How should compression quality be evaluated for machine understanding rather than only human perception?

These should be answered gradually. Do not pretend they are already settled.

---

## Guidance for Future AI Assistance

When helping this project, always follow these rules:

### 1. Preserve the fixed core idea

Do not replace the current project with a different one.

### 2. Distinguish core idea from optional extensions

Clearly label:

* current core
* optional future extension
* speculative idea

### 3. Explain in beginner-friendly language first

The user is still relatively new to this area. Prefer:

* intuition first
* then equations
* then implementation implications

### 4. Avoid hidden assumption jumps

Do not silently assume:

* tokenizer means NLP tokenizer
* INR means universal codec
* better pixel quality always means better downstream utility

### 5. Keep the project machine-oriented

Always maintain the distinction between:

* human-oriented compression
* machine-oriented compression

### 6. Be precise about INR limitations

When discussing INR-based backbones, explicitly distinguish:

* per-video fitting
* method-level generality
* codec-level universality

### 7. Do not overclaim

Do not write as if:

* the project already solves generalization
* the tokenizer setting is finalized
* the downstream validation protocol is settled
* the 3D extension is already part of the locked main method

### 8. When proposing improvements

Improvements should be framed as:

* minimal extension,
* deeper interpretation,
* or optional future branch,
  not as forced redesign.

---

## Current Default One-Sentence Project Summary

This project studies an INR-based machine-oriented compression framework for egocentric video, aiming to learn compact representations whose reconstructed videos preserve tokenizer-level machine-understanding signals for downstream tasks.

---

## Current Default Abstract-Style Summary

We study machine-oriented compression for egocentric video. Instead of optimizing compression primarily for human visual quality, the project aims to learn compact representations that preserve the information needed by downstream machine understanding models. The current framework follows an INR-based compression pipeline, where an original video is compressed and reconstructed, and a tokenizer/teacher branch is used to enforce consistency between the machine representations of the original and reconstructed videos. The core objective is to maintain tokenizer-level semantic and temporal information under compression while improving storage efficiency. The project remains generalization-oriented in spirit, but does not currently assume a fully universal one-shot codec; under the current understanding of INR-based methods, per-video fitting remains an important consideration.

---

## Current Chinese Summary

本项目研究的是一种**面向机器理解的第一视角视频压缩框架**。核心目标不是单纯提高人眼观看下的重建质量，而是在显著压缩视频表示、降低存储与传输成本的同时，尽可能保留后续 tokenizer / teacher 模型以及下游机器理解任务所需要的语义与时序信息。当前框架基于 INR-style / NVRC-style 的视频压缩思路，将原始视频压缩并重建，然后通过 tokenizer 分支约束原始视频与压缩重建视频的机器表征保持一致。项目当前强调的是**machine-oriented compression**，而不是普通的 human-oriented video compression；同时也默认注意到 INR 方法可能具有每个视频单独拟合的特点，因此当前并不自动假设这是一个完全通用的一次训练全局适用的压缩网络。后续所有开发、论文叙述与实验设计都应以这一核心定义为准。

---

## Final Constraint

This document is the stable core context for future development.

Unless the user explicitly approves a revision:

* do not redefine the project,
* do not swap out the main storyline,
* do not collapse the tokenizer branch into ordinary reconstruction,
* do not silently convert the method into a different compression paradigm,
* do not overstate universality beyond what INR-based assumptions support.

```

如果你愿意，我下一步可以直接继续给你补一份 **配套的 `PROJECT_PLAN.md`**，把这个固定核心文档再拆成：
- 当前已确定内容
- 未确定但可探索内容
- 近期最小可执行实验路径  
这样你后面用这个 repo 跑起来会更顺。
