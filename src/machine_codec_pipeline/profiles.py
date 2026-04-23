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
    "bootstrap": Profile(
        name="bootstrap",
        task_config="l1_teacher-resnet18-bootstrap.yaml",
        description="Baseline teacher-consistency path with frozen ResNet18 features.",
        smoke_args=("--teacher-type", "resnet18_imagenet"),
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
