"""Tiny no-GPU demo for the pipeline output contract."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .io import write_json
from .profiles import ensure_profile
from .results import compare_results


DEMO_RUNS: tuple[dict[str, Any], ...] = (
    {
        "name": "bootstrap_demo",
        "profile": "bootstrap",
        "metrics": {
            "bpp_avg": 88.2109,
            "psnr_avg": 10.9099,
            "teacher-mse_avg": 0.5163,
        },
    },
    {
        "name": "shared_semchange_delta_demo",
        "profile": "shared_semchange_delta",
        "metrics": {
            "bpp_avg": 88.2109,
            "psnr_avg": 10.9243,
            "teacher-mse_avg": 0.5115,
        },
    },
)


def write_demo_results(output_root: Path) -> list[Path]:
    """Create two small result folders that mimic NVRC aggregate outputs."""

    result_paths: list[Path] = []
    for run in DEMO_RUNS:
        profile = ensure_profile(run["profile"])
        run_dir = output_root / run["name"]
        results_dir = run_dir / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        results_path = results_dir / "all.txt"
        metrics = run["metrics"]
        results_path.write_text(
            "bpp_avg,psnr_avg,teacher-mse_avg\n"
            f"{metrics['bpp_avg']},{metrics['psnr_avg']},{metrics['teacher-mse_avg']}\n",
            encoding="utf-8",
        )
        write_json(
            run_dir / "pipeline_summary.json",
            {
                "demo": True,
                "profile": asdict(profile),
                "experiment_dir": str(run_dir),
                "results_path": str(results_path),
                "metrics": metrics,
                "note": (
                    "Synthetic tiny-local summary for testing the orchestration "
                    "contract. This is not a new training run."
                ),
            },
        )
        result_paths.append(results_path)
    return result_paths


def run_demo(output_root: Path) -> list[dict[str, Any]]:
    output_root.mkdir(parents=True, exist_ok=True)
    result_paths = write_demo_results(output_root)
    comparison = compare_results([str(path) for path in result_paths])
    write_json(output_root / "demo_compare.json", comparison)
    return comparison
