#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from pathlib import Path


FRAME_INDEX_RE = re.compile(r"^\((\d+)\s+\d+\s+\d+\)$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Package original/reconstructed frames and metrics into a machine-facing interface bundle."
    )
    parser.add_argument("--source-run-dir", type=Path, required=True, help="Completed NVRC run directory.")
    parser.add_argument("--dataset-dir", type=Path, required=True, help="Directory containing original PNG frames.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Output bundle directory.")
    parser.add_argument(
        "--decoded-metrics-path",
        type=Path,
        default=None,
        help="Optional override for decoded metrics.txt.",
    )
    parser.add_argument(
        "--eval-metrics-path",
        type=Path,
        default=None,
        help="Optional override for eval metrics.txt.",
    )
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def parse_results_csv(path: Path) -> dict[str, float | str]:
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        row = next(reader)
    parsed: dict[str, float | str] = {}
    for key, value in row.items():
        if value is None:
            parsed[key] = ""
            continue
        try:
            parsed[key] = float(value)
        except ValueError:
            parsed[key] = value
    return parsed


def parse_patch_metrics(path: Path) -> dict[int, dict[str, float]]:
    metrics_by_frame: dict[int, dict[str, float]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            parts = [part.strip() for part in line.split(",") if part.strip()]
            frame_match = FRAME_INDEX_RE.match(parts[0])
            if frame_match is None:
                raise ValueError(f"Unrecognized metrics line: {line}")
            frame_index = int(frame_match.group(1))
            frame_metrics: dict[str, float] = {}
            for metric_part in parts[1:]:
                key, value = metric_part.split(":", 1)
                frame_metrics[key.strip()] = float(value.strip())
            metrics_by_frame[frame_index] = frame_metrics
    return metrics_by_frame


def copy_file(src: Path, dst: Path) -> None:
    ensure_dir(dst.parent)
    shutil.copy2(src, dst)


def build_bundle(
    source_run_dir: Path,
    dataset_dir: Path,
    output_dir: Path,
    decoded_metrics_path: Path,
    eval_metrics_path: Path,
) -> Path:
    decoded_dir = source_run_dir / "outputs" / "0000" / "decoded" / "None" / dataset_dir.name
    result_csv = source_run_dir / "results" / "all.txt"
    args_yaml = source_run_dir / "args.yaml"

    if not decoded_dir.exists():
        raise FileNotFoundError(f"Decoded frame directory not found: {decoded_dir}")
    if not result_csv.exists():
        raise FileNotFoundError(f"Aggregate result file not found: {result_csv}")
    if not args_yaml.exists():
        raise FileNotFoundError(f"Run args file not found: {args_yaml}")

    original_frames = sorted(dataset_dir.glob("*.png"))
    reconstructed_frames = sorted(decoded_dir.glob("*.png"))
    if not original_frames:
        raise FileNotFoundError(f"No original PNG frames found under {dataset_dir}")
    if len(original_frames) != len(reconstructed_frames):
        raise ValueError(
            f"Frame count mismatch: {len(original_frames)} original vs {len(reconstructed_frames)} reconstructed"
        )

    decoded_metrics = parse_patch_metrics(decoded_metrics_path)
    eval_metrics = parse_patch_metrics(eval_metrics_path)
    aggregate_metrics = parse_results_csv(result_csv)

    original_out = output_dir / "original"
    reconstructed_out = output_dir / "reconstructed"
    metadata_out = output_dir / "metadata"
    ensure_dir(original_out)
    ensure_dir(reconstructed_out)
    ensure_dir(metadata_out)

    manifest_frames: list[dict[str, object]] = []
    for frame_index, (orig_src, recon_src) in enumerate(zip(original_frames, reconstructed_frames)):
        orig_dst = original_out / orig_src.name
        recon_dst = reconstructed_out / recon_src.name
        copy_file(orig_src, orig_dst)
        copy_file(recon_src, recon_dst)
        manifest_frames.append(
            {
                "frame_index": frame_index,
                "sample_id": orig_src.stem,
                "original_relpath": str(orig_dst.relative_to(output_dir)),
                "reconstructed_relpath": str(recon_dst.relative_to(output_dir)),
                "decoded_metrics": decoded_metrics.get(frame_index, {}),
                "eval_metrics": eval_metrics.get(frame_index, {}),
            }
        )

    copy_file(args_yaml, metadata_out / "args.yaml")
    copy_file(result_csv, metadata_out / "aggregate_results.csv")
    copy_file(decoded_metrics_path, metadata_out / "decoded_metrics.txt")
    copy_file(eval_metrics_path, metadata_out / "eval_metrics.txt")

    manifest = {
        "bundle_version": 1,
        "source_run_dir": str(source_run_dir),
        "dataset_dir": str(dataset_dir),
        "aggregate_metrics": aggregate_metrics,
        "frame_count": len(manifest_frames),
        "frames": manifest_frames,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest_path


def main() -> None:
    args = parse_args()
    source_run_dir = args.source_run_dir.resolve()
    dataset_dir = args.dataset_dir.resolve()
    output_dir = args.output_dir.resolve()
    decoded_metrics_path = (
        args.decoded_metrics_path.resolve()
        if args.decoded_metrics_path is not None
        else source_run_dir / "outputs" / "0000" / "decoded" / "None" / "metrics.txt"
    )
    eval_metrics_path = (
        args.eval_metrics_path.resolve()
        if args.eval_metrics_path is not None
        else source_run_dir / "outputs" / "0000" / "eval" / "0" / "metrics.txt"
    )

    manifest_path = build_bundle(
        source_run_dir=source_run_dir,
        dataset_dir=dataset_dir,
        output_dir=output_dir,
        decoded_metrics_path=decoded_metrics_path,
        eval_metrics_path=eval_metrics_path,
    )
    print(f"Wrote interface bundle manifest to {manifest_path}")


if __name__ == "__main__":
    main()
