"""Repository path resolution for launcher commands."""

from __future__ import annotations

from pathlib import Path


DEFAULT_EXP_CONFIG = Path("scripts/configs/nvrc/overfit/tiny-1e.yaml")
DEFAULT_DATA_CONFIG = Path("scripts/configs/data/video/png/tiny_local.yaml")
DEFAULT_COMPRESS_MODEL_CONFIG = Path(
    "scripts/configs/nvrc/compress_models/nvrc_tiny_s1.yaml"
)
DEFAULT_MODEL_CONFIG = Path("scripts/configs/nvrc/models/teacher_tiny_32.yaml")


def find_repo_root(explicit: str | None = None) -> Path:
    """Resolve the outer repository root.

    The editable package path and the current working directory are both
    considered so the CLI works from either ``python -m`` or the legacy script.
    """

    if explicit:
        return Path(explicit).expanduser().resolve()

    candidates = [Path.cwd(), *Path(__file__).resolve().parents]
    for candidate in candidates:
        if (candidate / "third_party" / "NVRC").exists():
            return candidate
    return Path(__file__).resolve().parents[2]


def nvrc_root(repo_root: Path) -> Path:
    return repo_root / "third_party" / "NVRC"


def smoke_script(repo_root: Path) -> Path:
    return repo_root / "tools" / "smoke_teacher_loss.py"


def default_output_root(repo_root: Path) -> Path:
    return repo_root / "runs"
