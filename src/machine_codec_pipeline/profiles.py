"""Built-in teacher-aware experiment profiles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Profile:
    """One teacher-aware NVRC profile exposed by the launcher."""

    name: str
    task_config: str
    description: str
    smoke_args: tuple[str, ...]


PROFILES: dict[str, Profile] = {
    "no_teacher": Profile(
        name="no_teacher",
        task_config="l1_no_teacher.yaml",
        description="Pure L1 reconstruction loss with no semantic teacher guidance. Ablation baseline.",
        smoke_args=(),
    ),
    "bootstrap": Profile(
        name="bootstrap",
        task_config="l1_teacher-resnet18-bootstrap.yaml",
        description="Baseline teacher-consistency path with frozen ResNet18 features.",
        smoke_args=("--teacher-type", "resnet18_imagenet"),
    ),
    "internvit_teacher": Profile(
        name="internvit_teacher",
        task_config="l1_teacher-internvit.yaml",
        description="Teacher-consistency path using the downstream VLM's own frozen "
        "InternViT encoder (Pathway B Phase 1).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b": Profile(
        name="pathway_b",
        task_config="l1_teacher-pathway-b.yaml",
        description="Pathway B: a token head maps the INR's internal feature layer to "
        "VLM tokens, trained against frozen InternViT tokens (token-consistency loss).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid": Profile(
        name="pathway_b_mid",
        task_config="l1_teacher-pathway-b-mid.yaml",
        description="Pathway B-mid: codec adapter projects INR feature to ViT-shaped "
        "patch embeddings, routed through frozen InternViT layers 1..N and aligned "
        "to the oracle's layer-N hidden state via smooth_L1 + (1-cos).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_n6": Profile(
        name="pathway_b_mid_n6",
        task_config="l1_teacher-pathway-b-mid-N6.yaml",
        description="Pathway B-mid layer-sweep variant: alignment at InternViT layer N=6.",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_lamb006_n1224": Profile(
        name="pathway_b_mid_lamb006_n1224",
        task_config="l1_teacher-pathway-b-mid-lamb006-N1224.yaml",
        description="E-11: lamb006 rung, joint alignment at layers 12 and 24.",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_lamb025_n1224": Profile(
        name="pathway_b_mid_lamb025_n1224",
        task_config="l1_teacher-pathway-b-mid-lamb025-N1224.yaml",
        description="E-11: lamb025 rung, joint alignment at layers 12 and 24.",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_lamb050_n1224": Profile(
        name="pathway_b_mid_lamb050_n1224",
        task_config="l1_teacher-pathway-b-mid-lamb050-N1224.yaml",
        description="D-020: lamb050 rung, joint alignment at layers 12 and 24.",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_lamb150_n1224": Profile(
        name="pathway_b_mid_lamb150_n1224",
        task_config="l1_teacher-pathway-b-mid-lamb150-N1224.yaml",
        description="E-11: lamb150 rung, joint alignment at layers 12 and 24.",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_n1224": Profile(
        name="pathway_b_mid_n1224",
        task_config="l1_teacher-pathway-b-mid-N1224.yaml",
        description="E-01b: joint hidden-state alignment at layers 12 and 24.",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_nmulti": Profile(
        name="pathway_b_mid_nmulti",
        task_config="l1_teacher-pathway-b-mid-Nmulti.yaml",
        description="CVPR-27 ablation C2: joint hidden-state alignment at layers 6+12+18.",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_final_lamb025": Profile(
        name="pathway_b_mid_final_lamb025",
        task_config="l1_teacher-pathway-b-mid-final-lamb025.yaml",
        description="CVPR-27 ablation C1: final-layer (N=24) alignment at lamb=0.25.",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_n18": Profile(
        name="pathway_b_mid_n18",
        task_config="l1_teacher-pathway-b-mid-N18.yaml",
        description="Pathway B-mid layer-sweep variant: alignment at InternViT layer N=18.",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_w0": Profile(
        name="pathway_b_mid_w0",
        task_config="l1_teacher-pathway-b-mid-w0.yaml",
        description="Loss ablation: pure SmoothL1 hidden alignment (cosine weight w=0).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_w1": Profile(
        name="pathway_b_mid_w1",
        task_config="l1_teacher-pathway-b-mid-w1.yaml",
        description="Loss ablation: pure cosine hidden alignment (cosine weight w=1).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_eta0": Profile(
        name="pathway_b_mid_eta0",
        task_config="l1_teacher-pathway-b-mid-eta0.yaml",
        description="Loss ablation: no pixel anchor (eta=0).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_lamb012": Profile(
        name="pathway_b_mid_lamb012",
        task_config="l1_teacher-pathway-b-mid-lamb012.yaml",
        description="Low-rate densify: lamb=0.012 on r1 (target ~0.035 bpp, overlaps VCM-RS grid).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_lamb003": Profile(
        name="pathway_b_mid_lamb003",
        task_config="l1_teacher-pathway-b-mid-lamb003.yaml",
        description="Low-rate densify: lamb=0.003 on r1 (target ~0.014 bpp, overlaps VCM-RS grid).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_lamb025": Profile(
        name="pathway_b_mid_lamb025",
        task_config="l1_teacher-pathway-b-mid-lamb025.yaml",
        description="Low-rate probe: distortion weight lamb=0.25 on r1 (loss = lamb*D + R).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_lamb050": Profile(
        name="pathway_b_mid_lamb050",
        task_config="l1_teacher-pathway-b-mid-lamb050.yaml",
        description="Mid-rate densify: lamb=0.5 on r1 (target ~0.08 bpp, fills 0.05-0.12 gap).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_lamb150": Profile(
        name="pathway_b_mid_lamb150",
        task_config="l1_teacher-pathway-b-mid-lamb150.yaml",
        description="Upper-rate densify: lamb=1.5 on r1 (target ~0.15 bpp, above cap_r1).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_lamb006": Profile(
        name="pathway_b_mid_lamb006",
        task_config="l1_teacher-pathway-b-mid-lamb006.yaml",
        description="Low-rate probe: distortion weight lamb=0.0625 on r1.",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_lamb4": Profile(
        name="pathway_b_mid_lamb4",
        task_config="l1_teacher-pathway-b-mid-lamb4.yaml",
        description="Low-rate probe: rate weight lamb=4 on r1 (A2 lambda pivot).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_lamb16": Profile(
        name="pathway_b_mid_lamb16",
        task_config="l1_teacher-pathway-b-mid-lamb16.yaml",
        description="Low-rate probe: rate weight lamb=16 on r1 (A2 lambda pivot).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_w025": Profile(
        name="pathway_b_mid_w025",
        task_config="l1_teacher-pathway-b-mid-w025.yaml",
        description="Loss local sensitivity: cosine weight w=0.25 (EXP-036).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_w075": Profile(
        name="pathway_b_mid_w075",
        task_config="l1_teacher-pathway-b-mid-w075.yaml",
        description="Loss local sensitivity: cosine weight w=0.75 (EXP-036).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_eta005": Profile(
        name="pathway_b_mid_eta005",
        task_config="l1_teacher-pathway-b-mid-eta005.yaml",
        description="Loss local sensitivity: pixel anchor eta=0.005 (EXP-036).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_eta02": Profile(
        name="pathway_b_mid_eta02",
        task_config="l1_teacher-pathway-b-mid-eta02.yaml",
        description="Loss local sensitivity: pixel anchor eta=0.02 (EXP-036).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_n24": Profile(
        name="pathway_b_mid_n24",
        task_config="l1_teacher-pathway-b-mid-N24.yaml",
        description="Layer sweep equal-rate variant: alignment at InternViT layer N=24 "
                    "under the SAME mid profile/lambda (fixes the EXP-021/022 N24 "
                    "interface-final confound).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_rate_lo": Profile(
        name="pathway_b_mid_rate_lo",
        task_config="l1_teacher-pathway-b-mid-rate-lo.yaml",
        description="Pathway B-mid (low rate point, lamb=0.25).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_rate_mid": Profile(
        name="pathway_b_mid_rate_mid",
        task_config="l1_teacher-pathway-b-mid-rate-mid.yaml",
        description="Pathway B-mid (mid rate point, lamb=1.0).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_rate_hi": Profile(
        name="pathway_b_mid_rate_hi",
        task_config="l1_teacher-pathway-b-mid-rate-hi.yaml",
        description="Pathway B-mid (high rate point, lamb=4.0).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_instructblip": Profile(
        name="pathway_b_mid_instructblip",
        task_config="l1_teacher-pathway-b-mid-instructblip.yaml",
        description="Pathway B-mid aligned to InstructBLIP's EVA-CLIP layer 20 "
        "(second VLM backbone; capacity set via --model-config).",
        smoke_args=("--teacher-type", "instructblip"),
    ),
    "pathway_b_mid_qwen25vl": Profile(
        name="pathway_b_mid_qwen25vl",
        task_config="l1_teacher-pathway-b-mid-qwen25vl.yaml",
        description="Pathway B-mid aligned to Qwen2.5-VL-7B's vision ViT mid block "
        "N=16 of 32 (distinct windowed-attention architecture, third backbone; "
        "capacity via --model-config).",
        smoke_args=("--teacher-type", "qwen25vl"),
    ),
    "pathway_b_mid_llavavideo": Profile(
        name="pathway_b_mid_llavavideo",
        task_config="l1_teacher-pathway-b-mid-llavavideo.yaml",
        description="Pathway B-mid aligned to LLaVA-Video's SigLIP layer 26 "
        "(video-capable second backbone; capacity via --model-config).",
        smoke_args=("--teacher-type", "llava_video"),
    ),
    "pathway_b_mid_llavavideo_n18": Profile(
        name="pathway_b_mid_llavavideo_n18",
        task_config="l1_teacher-pathway-b-mid-llavavideo-N18.yaml",
        description="LLaVA-Video layer sweep: align at SigLIP N=18.",
        smoke_args=("--teacher-type", "llava_video"),
    ),
    "pathway_b_mid_llavavideo_n20": Profile(
        name="pathway_b_mid_llavavideo_n20",
        task_config="l1_teacher-pathway-b-mid-llavavideo-N20.yaml",
        description="LLaVA-Video layer sweep: align at SigLIP N=20.",
        smoke_args=("--teacher-type", "llava_video"),
    ),
    "pathway_b_mid_rate_vlo": Profile(
        name="pathway_b_mid_rate_vlo",
        task_config="l1_teacher-pathway-b-mid-rate-vlo.yaml",
        description="Pathway B-mid (very-low rate point, lamb=0.0625).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    # Ultra-low probes added after Stage-1 calibration found vlo only reaches
    # ~0.6 bpp (the lambda knob saturates). These test whether even lower lambda
    # pushes bpp toward the ~0.1 regime where the win vs HEVC should appear.
    "pathway_b_mid_rate_xlo": Profile(
        name="pathway_b_mid_rate_xlo",
        task_config="l1_teacher-pathway-b-mid-rate-xlo.yaml",
        description="Pathway B-mid (extra-low rate, lamb=0.015625 = vlo/4).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_rate_xxlo": Profile(
        name="pathway_b_mid_rate_xxlo",
        task_config="l1_teacher-pathway-b-mid-rate-xxlo.yaml",
        description="Pathway B-mid (extra-extra-low rate, lamb=0.00390625 = vlo/16).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_rate_vhi": Profile(
        name="pathway_b_mid_rate_vhi",
        task_config="l1_teacher-pathway-b-mid-rate-vhi.yaml",
        description="Pathway B-mid (very-high rate point, lamb=16.0).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    # --- FINAL-EMBEDDING baseline (Latent-INR-style): same codec/rate/loss as the
    # mid-layer profiles above, but alignment depth = the LAST InternViT layer (24)
    # instead of 12. This is the mandatory baseline that isolates the "mid-layer"
    # claim (PQ1/PQ2). interface=final in the units maps to these.
    "pathway_b_mid_final_rate_vlo": Profile(
        name="pathway_b_mid_final_rate_vlo",
        task_config="l1_teacher-pathway-b-mid-final-rate-vlo.yaml",
        description="Final-embedding baseline (very-low rate, lamb=0.0625, layer=24).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_final_rate_lo": Profile(
        name="pathway_b_mid_final_rate_lo",
        task_config="l1_teacher-pathway-b-mid-final-rate-lo.yaml",
        description="Final-embedding baseline (low rate, lamb=0.25, layer=24).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_final_rate_mid": Profile(
        name="pathway_b_mid_final_rate_mid",
        task_config="l1_teacher-pathway-b-mid-final-rate-mid.yaml",
        description="Final-embedding baseline (mid rate, lamb=1.0, layer=24).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_final_rate_hi": Profile(
        name="pathway_b_mid_final_rate_hi",
        task_config="l1_teacher-pathway-b-mid-final-rate-hi.yaml",
        description="Final-embedding baseline (high rate, lamb=4.0, layer=24).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "pathway_b_mid_final_rate_vhi": Profile(
        name="pathway_b_mid_final_rate_vhi",
        task_config="l1_teacher-pathway-b-mid-final-rate-vhi.yaml",
        description="Final-embedding baseline (very-high rate, lamb=16.0, layer=24).",
        smoke_args=("--teacher-type", "internvit"),
    ),
    "blueprint": Profile(
        name="blueprint",
        task_config="l1_teacher-resnet18-blueprint.yaml",
        description="Low-rank semantic blueprint distilled from frozen teacher targets.",
        smoke_args=(
            "--teacher-type",
            "resnet18_imagenet",
            "--semantic-blueprint",
            "--semantic-blueprint-rank",
            "16",
        ),
    ),
    "readout": Profile(
        name="readout",
        task_config="l1_teacher-resnet18-readout.yaml",
        description="Frozen random readout bank over teacher features.",
        smoke_args=(
            "--teacher-type",
            "resnet18_imagenet",
            "--function-readout-consistency",
            "--function-readout-weight",
            "1.0",
            "--function-readout-bank-size",
            "4",
            "--function-readout-hidden-dim",
            "64",
            "--function-readout-out-dim",
            "16",
            "--function-readout-seed",
            "0",
        ),
    ),
    "relation": Profile(
        name="relation",
        task_config="l1_teacher-resnet18-relation.yaml",
        description="Relation-preserving auxiliary loss on pairwise teacher similarities.",
        smoke_args=(
            "--teacher-type",
            "resnet18_imagenet",
            "--relation-consistency",
            "--relation-mode",
            "cosine",
            "--relation-weight",
            "1.0",
        ),
    ),
    "semchange": Profile(
        name="semchange",
        task_config="l1_teacher-resnet18-semchange.yaml",
        description="Teacher loss reweighted by semantic change magnitude.",
        smoke_args=(
            "--teacher-type",
            "resnet18_imagenet",
            "--semantic-change-weighting",
            "--semantic-change-floor",
            "0.25",
            "--semantic-change-gamma",
            "1.0",
        ),
    ),
    "semchange_delta": Profile(
        name="semchange_delta",
        task_config="l1_teacher-resnet18-semchange-delta.yaml",
        description="Semantic-change weighting plus temporal delta consistency.",
        smoke_args=(
            "--teacher-type",
            "resnet18_imagenet",
            "--semantic-change-weighting",
            "--semantic-change-floor",
            "0.25",
            "--semantic-change-gamma",
            "1.0",
            "--temporal-delta-consistency",
            "--temporal-delta-weight",
            "1.0",
        ),
    ),
    "semchange_gamma2": Profile(
        name="semchange_gamma2",
        task_config="l1_teacher-resnet18-semchange-gamma2.yaml",
        description="Semantic-change weighting with a sharper gamma=2 emphasis.",
        smoke_args=(
            "--teacher-type",
            "resnet18_imagenet",
            "--semantic-change-weighting",
            "--semantic-change-floor",
            "0.25",
            "--semantic-change-gamma",
            "2.0",
        ),
    ),
    "shared_semchange_delta": Profile(
        name="shared_semchange_delta",
        task_config="l1_teacher-resnet18-shared-semchange-delta.yaml",
        description="Temporal delta consistency gated by the same semantic-change weights.",
        smoke_args=(
            "--teacher-type",
            "resnet18_imagenet",
            "--semantic-change-weighting",
            "--semantic-change-floor",
            "0.25",
            "--semantic-change-gamma",
            "1.0",
            "--temporal-delta-consistency",
            "--temporal-delta-weight",
            "1.0",
            "--temporal-delta-semantic-gating",
        ),
    ),
}


def ensure_profile(name: str) -> Profile:
    """Return a profile by name or stop with a concise CLI-facing error."""

    try:
        return PROFILES[name]
    except KeyError as exc:
        raise SystemExit(f"Unknown profile: {name}") from exc


def task_config_path(profile: Profile) -> Path:
    """Return the NVRC task-config path for a profile."""

    return Path("scripts/configs/tasks/overfit") / profile.task_config
