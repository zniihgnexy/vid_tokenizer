# Outputs

This folder is the canonical output area for the packaged pipeline.

Recommended layout:

```text
outputs/
├── demo/            # tiny synthetic demo outputs
├── examples/        # lightweight tracked example artifacts
├── runs/            # default destination for new NVRC runs
└── video_windows/   # extracted PNG windows and chunk indices
```

Git policy:

- keep `outputs/examples/` only when the bundle is lightweight and directly
  communicates a result
- keep `outputs/runs/` and `outputs/video_windows/` local unless you explicitly
  want to publish a curated artifact bundle
- if a real run produces checkpoints, decoded-frame folders, bitstreams, or
  rank logs, move those into `outputs/runs/` rather than leaving them inside a
  tracked example folder
