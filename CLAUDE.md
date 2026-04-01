# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project studies **machine-oriented egocentric video compression** using INR-based neural video compression. See `CLAUDE_readme.md` for the comprehensive fixed project definition—it contains the core research idea, terminology, constraints, and intended storyline.

**One-sentence summary:** Learn compact compressed representations for egocentric video that preserve tokenizer-level machine-understanding signals, not primarily human visual quality.

## Core Architecture

The project implements the following pipeline:

```
x (original video)
├─→ NVRC encoder → z (compressed latent) → decoder → x_hat (reconstructed)
└─→ Tokenizer T ──────────────────────────→ y (machine representation)
                                           ↓
                                        y_hat (reconstructed representation)

Objective: minimize ||y_hat - y||²  (tokenizer/teacher consistency)
```

### Key Components (to be implemented)

1. **Compression Backbone (NVRC-style)**
   - INR-based encoder/decoder
   - Produces compact latent representation `z`
   - Handles per-video fitting and reconstruction

2. **Tokenizer/Teacher Branch**
   - Maps video → machine representations (continuous features, not just discrete tokens)
   - Options: CLIP embeddings, patch tokens, hidden states, frame embeddings
   - Used to extract `y` from original video and `y_hat` from reconstructed video

3. **Training Objective**
   - Primary: `L_tok = ||tokenizer(x_hat) - tokenizer(x)||²` (machine representation consistency)
   - Secondary: `L_rec` (reconstruction fidelity), `L_rate` (compression efficiency)
   - Combined: `L = λ_rate * L_rate + λ_rec * L_rec + λ_tok * L_tok`

### Important Assumptions

- **INR-based methods require per-video instance fitting**—do not assume the codec is universally pretrained
- The tokenizer is the _definition of what information matters_—the framework is not task-specific feature distillation
- Machine representation consistency is central; pixel quality is secondary
- Multiple tokenizers can be explored for generalization, but this is currently speculative

## Typical Code Structure (Expected Layout)

```
vid_tokenizer/
├── CLAUDE.md                    # This file
├── CLAUDE_readme.md             # Immutable core project definition
├── src/
│   ├── compression/             # NVRC encoder/decoder, latent handling
│   ├── tokenizer/               # Tokenizer/teacher models and feature extraction
│   ├── loss/                    # Loss functions (reconstruction, rate, tokenizer consistency)
│   ├── models/                  # Utility models or wrappers
│   └── data/                    # Data loading for egocentric video
├── experiments/                 # Experiment configs and scripts
├── configs/                     # Default configs (compression, tokenizer, training)
└── requirements.txt             # Dependencies
```

## Development Workflow

### Setup & Dependencies
```bash
# Install dependencies
pip install -r requirements.txt

# (If using conda)
# conda create -n vid_tokenizer python=3.10
# conda activate vid_tokenizer
# pip install -r requirements.txt
```

### Running Experiments
```bash
# Train compression model with tokenizer consistency
python -m experiments.train \
  --config configs/baseline.yaml \
  --data-path /path/to/egocentric/video \
  --tokenizer clip

# Evaluate compression on machine-understanding metrics
python -m experiments.evaluate \
  --checkpoint results/compression.pt \
  --tokenizer clip
```

### Development Guidelines

1. **Preserve the tokenizer branch design**—do not collapse it into pure reconstruction loss
2. **Distinguish per-video fitting from method generality**—be explicit about INR assumptions
3. **Tokenizer is flexible**—support multiple options (CLIP, patch tokens, hidden states) rather than locking to one
4. **Validate machine understanding, not just PSNR**—measure downstream utility (e.g., classification, detection on compressed-then-reconstructed videos)
5. **Log machine representations early**—visualize `y` vs `y_hat` alignment to debug tokenizer consistency
6. **Test with multiple tokenizers**—ensure the compression learns general machine-relevant features

### Common Commands (to be implemented)

```bash
# Run tests
pytest tests/

# Run linting
black src/ experiments/
flake8 src/ experiments/

# Profile tokenizer consistency loss
python -m experiments.debug_tokenizer \
  --checkpoint results/compression.pt \
  --sample-video /path/to/sample.mp4

# Ablate loss weights
python -m experiments.ablate_loss \
  --config configs/baseline.yaml \
  --lambda-rate 0.1 0.01 0.001 \
  --lambda-rec 1.0 \
  --lambda-tok 1.0 10.0 100.0
```

## Key Terminology (from CLAUDE_readme.md)

- **`x`**: Original egocentric video
- **`z`**: Compact compressed latent representation
- **`x_hat`**: Reconstructed video after decompression
- **`y = T(x)`**: Machine representation (features/tokens) of original video
- **`y_hat = T(x_hat)`**: Machine representation of reconstructed video
- **`T` (tokenizer/teacher)**: Visual tokenization function—extracts machine-usable features (not limited to text tokenization)
- **NVRC / INR**: Neural video compression backbone (may require per-video fitting)
- **Machine-oriented compression**: Optimizes for downstream machine understanding, not human visual quality

## What NOT to Do

- Do not frame the project as ordinary (human-oriented) video compression
- Do not assume a fully universal pretrained codec—per-video fitting is expected with INR
- Do not collapse the tokenizer branch into ordinary feature distillation
- Do not lock the tokenizer choice early—design for multiple teachers
- Do not assume all downstream tasks are pre-determined—keep evaluation general
- Do not rewrite the core idea without explicit user approval

## Open Research Questions (Active Design Items)

1. Which tokenizer/teacher representation is most effective? (CLIP, hidden states, patch tokens, etc.)
2. Should tokenizers be fixed or sampled during training for better generalization?
3. What is the ideal balance among `L_rate`, `L_rec`, and `L_tok`?
4. Should the method remain per-video INR fitting or evolve toward a general codec?
5. Which downstream tasks best validate machine-understanding preservation?
6. How should compression quality be measured for machine understanding rather than only human perception?

These should be investigated experimentally; do not assume they are already settled.

## References & Context

- `CLAUDE_readme.md` — Immutable project definition, constraints, and storyline
- Relevant literature: INR-based video compression, egocentric vision, vision-language models, video tokenization
