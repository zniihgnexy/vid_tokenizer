# Frozen Consumer Evaluation

- model: `resnet18`
- weights: `IMAGENET1K_V1`
- device: `cuda`

| Comparison | Top-1 Accuracy | Mean Match Rank | Mean Matching Similarity | Mean Margin vs Best Nonmatch |
|---|---:|---:|---:|---:|
| original_to_original | 1.0000 | 1.0000 | 1.0000 | 0.0710 |
| reconstructed_to_original | 0.2500 | 2.5000 | 0.5595 | -0.0649 |
| original_to_reconstructed | 0.2500 | 2.2500 | 0.5595 | -0.0189 |
