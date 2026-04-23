"""Result parsing and comparison utilities."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def parse_scalar(value: str) -> Any:
    """Parse a CSV field into bool, int, float, or the original string."""

    stripped = value.strip()
    try:
        if stripped.lower() in {"true", "false"}:
            return stripped.lower() == "true"
        if any(ch in stripped for ch in (".", "e", "E")):
            number = float(stripped)
            return int(number) if number.is_integer() else number
        return int(stripped)
    except ValueError:
        return value


def parse_results_file(path: Path) -> dict[str, Any]:
    """Parse the single-row NVRC aggregate results file."""

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    if len(rows) != 1:
        raise ValueError(f"Expected exactly one aggregated row in {path}, found {len(rows)}")
    return {key: parse_scalar(value) for key, value in rows[0].items()}


def resolve_results_path(path_like: str) -> Path:
    """Resolve either an experiment directory or a direct results file path."""

    path = Path(path_like).expanduser().resolve()
    if path.is_dir():
        return path / "results" / "all.txt"
    return path


def result_name(results_path: Path) -> str:
    if results_path.parent.name == "results":
        return results_path.parents[1].name
    return results_path.stem


def compare_results(targets: list[str]) -> list[dict[str, Any]]:
    """Load and rank result rows by teacher consistency, PSNR, then bitrate."""

    rows: list[dict[str, Any]] = []
    for target in targets:
        results_path = resolve_results_path(target)
        rows.append(
            {
                "name": result_name(results_path),
                "results_path": str(results_path),
                **parse_results_file(results_path),
            }
        )

    rows.sort(
        key=lambda row: (
            float(row.get("teacher-mse_avg", float("inf"))),
            -float(row.get("psnr_avg", float("-inf"))),
            float(row.get("bpp_avg", float("inf"))),
        )
    )
    return rows
