# configs/

```text
configs/
  datasets/   one YAML per dataset: video source, frame sampling, QA fields (see _TEMPLATE.yaml)
  vlm/        receiver specs (model path, input size, alignment layer)
```

The units read the dataset YAML named by `DATASET_CONFIG` (default `configs/datasets/$DATASET.yaml`)
through the `ds` helper in `scripts/units/_common.sh`, e.g. `ds frames.num_frames`.
Datasets used in the paper: `egoschema.yaml`, `vmme_long_motion.yaml`, `longvideobench.yaml`.
The others are kept for the older screening runs.

## Codec-side configs

The loss terms, λ and codec capacity are **not** defined here. They live in the patched NVRC
submodule and are selected by name:

| Selector | NVRC config |
|---|---|
| `--capacity r1` | `third_party/NVRC/scripts/configs/nvrc/models/teacher_cap_r1.yaml` |
| `--loss-variant lamb025` | `.../tasks/overfit/l1_teacher-pathway-b-mid-lamb025.yaml` (λ rung) |
| `--teacher-layer 1224` | `.../tasks/overfit/l1_teacher-pathway-b-mid[-<rung>]-N1224.yaml` (joint 12/24 alignment) |

The mapping from these flags to a launch profile is in `src/machine_codec_pipeline/profiles.py`
and `scripts/units/train_codec.sh`.
