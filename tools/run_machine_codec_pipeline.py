#!/usr/bin/env python3
"""Backward-compatible wrapper for the packaged machine-codec CLI."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if SRC_ROOT.exists():
    sys.path.insert(0, str(SRC_ROOT))

from machine_codec_pipeline.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
