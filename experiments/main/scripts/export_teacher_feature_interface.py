#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import re
import shutil
from pathlib import Path

import torch
import torch.nn.functional as F
from PIL import Image
from torchvision.transforms.functional import pil_to_tensor


FRAME_INDEX_RE = re.compile(r"^\((\d+)\s+\d+\s+\d+\)$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Package original/reconstructed frames plus frozen teacher feature packets into a "
            "machine-facing interface bundle."
        )
    )
    parser.add_argument("--source-run-dir", type=Path, required=True, help="Completed NVRC run directory.")
    parser.add_argument("--dataset-dir", type=Path, required=True, help="Directory containing original PNG frames.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Output bundle directory.")
    parser.add_argument(
        "--teacher-utils-path",
        type=Path,
        default=None,
        help="Optional override for the vendored NVRC teacher_utils.py module.",
    )
    parser.add_argument(
        "--teacher-type",
        type=str,
        default="resnet18_imagenet",
        help="Frozen teacher backbone name to instantiate from teacher_utils.py.",
    )
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda"],
        default="auto",
        help="Device selection policy for teacher feature extraction.",
    )
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


def pick_device(device_arg: str) -> torch.device:
    if device_arg == "cpu":
        return torch.device("cpu")
    if device_arg == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is not available.")
        return torch.device("cuda")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


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


def load_teacher_module(path: Path):
    spec = importlib.util.spec_from_file_location("teacher_utils_runtime", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load teacher_utils module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_rgb_tensor(path: Path) -> torch.Tensor:
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        return pil_to_tensor(rgb).float() / 255.0


def load_video_tensor(paths: list[Path], device: torch.device) -> torch.Tensor:
    if not paths:
        raise ValueError("Expected at least one frame path.")
    frames = [load_rgb_tensor(path) for path in paths]
    return torch.stack(frames, dim=1).unsqueeze(0).to(device)


def build_bundle(
    source_run_dir: Path,
    dataset_dir: Path,
    output_dir: Path,
    decoded_metrics_path: Path,
    eval_metrics_path: Path,
    teacher_utils_path: Path,
    teacher_type: str,
    device: torch.device,
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
    if not teacher_utils_path.exists():
        raise FileNotFoundError(f"teacher_utils.py not found: {teacher_utils_path}")

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

    teacher_utils = load_teacher_module(teacher_utils_path)
    teacher_adapter = teacher_utils.build_teacher_adapter(
        enable=True,
        teacher_type=teacher_type,
        detach_target=True,
    ).to(device)
    teacher_adapter.eval()

    original_video = load_video_tensor(original_frames, device)
    reconstructed_video = load_video_tensor(reconstructed_frames, device)

    with torch.inference_mode():
        pred_feat, target_feat = teacher_adapter.consistency_features(reconstructed_video, original_video)
        pred_delta, target_delta = teacher_adapter.temporal_delta_consistency_features(
            pred_feat=pred_feat,
            target_feat=target_feat,
        )
        consistency_map = teacher_adapter.consistency_map(
            pred=None,
            target=None,
            pred_feat=pred_feat,
            target_feat=target_feat,
        )
        semantic_weights = teacher_adapter.semantic_change_weights(target_feat=target_feat)
        feature_cosine = F.cosine_similarity(pred_feat[0], target_feat[0], dim=1)
        delta_cosine = F.cosine_similarity(pred_delta[0], target_delta[0], dim=1)

    pred_feat = pred_feat.cpu()
    target_feat = target_feat.cpu()
    pred_delta = pred_delta.cpu()
    target_delta = target_delta.cpu()
    consistency_map = consistency_map.cpu()
    semantic_weights = semantic_weights.cpu()
    feature_cosine = feature_cosine.cpu()
    delta_cosine = delta_cosine.cpu()

    original_out = output_dir / "original"
    reconstructed_out = output_dir / "reconstructed"
    packets_out = output_dir / "packets"
    metadata_out = output_dir / "metadata"
    ensure_dir(original_out)
    ensure_dir(reconstructed_out)
    ensure_dir(packets_out)
    ensure_dir(metadata_out)

    manifest_frames: list[dict[str, object]] = []
    for frame_index, (orig_src, recon_src) in enumerate(zip(original_frames, reconstructed_frames)):
        orig_dst = original_out / orig_src.name
        recon_dst = reconstructed_out / recon_src.name
        packet_dst = packets_out / f"{orig_src.stem}.pt"
        copy_file(orig_src, orig_dst)
        copy_file(recon_src, recon_dst)

        packet_payload = {
            "frame_index": frame_index,
            "sample_id": orig_src.stem,
            "teacher_type": teacher_type,
            "pred_feat": pred_feat[0, frame_index].clone(),
            "target_feat": target_feat[0, frame_index].clone(),
            "pred_delta": pred_delta[0, frame_index].clone(),
            "target_delta": target_delta[0, frame_index].clone(),
            "consistency_mse": float(consistency_map[0, frame_index].item()),
            "semantic_weight": float(semantic_weights[0, frame_index].item()),
            "feature_cosine": float(feature_cosine[frame_index].item()),
            "delta_cosine": float(delta_cosine[frame_index].item()),
        }
        torch.save(packet_payload, packet_dst)

        manifest_frames.append(
            {
                "frame_index": frame_index,
                "sample_id": orig_src.stem,
                "original_relpath": str(orig_dst.relative_to(output_dir)),
                "reconstructed_relpath": str(recon_dst.relative_to(output_dir)),
                "packet_relpath": str(packet_dst.relative_to(output_dir)),
                "decoded_metrics": decoded_metrics.get(frame_index, {}),
                "eval_metrics": eval_metrics.get(frame_index, {}),
                "packet_metrics": {
                    "consistency_mse": float(consistency_map[0, frame_index].item()),
                    "semantic_weight": float(semantic_weights[0, frame_index].item()),
                    "feature_cosine": float(feature_cosine[frame_index].item()),
                    "delta_cosine": float(delta_cosine[frame_index].item()),
                },
            }
        )

    copy_file(args_yaml, metadata_out / "args.yaml")
    copy_file(result_csv, metadata_out / "aggregate_results.csv")
    copy_file(decoded_metrics_path, metadata_out / "decoded_metrics.txt")
    copy_file(eval_metrics_path, metadata_out / "eval_metrics.txt")

    teacher_packet_summary = {
        "teacher_type": teacher_type,
        "device": str(device),
        "feature_dim": int(pred_feat.shape[-1]),
        "frame_count": int(pred_feat.shape[1]),
        "mean_feature_cosine": float(feature_cosine.mean().item()),
        "mean_delta_cosine": float(delta_cosine.mean().item()),
        "mean_consistency_mse": float(consistency_map.mean().item()),
        "mean_semantic_weight": float(semantic_weights.mean().item()),
        "packet_fields": ["pred_feat", "target_feat", "pred_delta", "target_delta"],
    }

    manifest = {
        "bundle_version": 2,
        "interface_type": "teacher_feature_packet",
        "source_run_dir": str(source_run_dir),
        "dataset_dir": str(dataset_dir),
        "teacher_utils_path": str(teacher_utils_path),
        "aggregate_metrics": aggregate_metrics,
        "teacher_packet_summary": teacher_packet_summary,
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
    teacher_utils_path = (
        args.teacher_utils_path.resolve()
        if args.teacher_utils_path is not None
        else source_run_dir.parent / "upstream_shared_gating_snapshot" / "third_party" / "NVRC" / "teacher_utils.py"
    )
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
    device = pick_device(args.device)

    manifest_path = build_bundle(
        source_run_dir=source_run_dir,
        dataset_dir=dataset_dir,
        output_dir=output_dir,
        decoded_metrics_path=decoded_metrics_path,
        eval_metrics_path=eval_metrics_path,
        teacher_utils_path=teacher_utils_path,
        teacher_type=args.teacher_type,
        device=device,
    )
    print(f"Wrote teacher feature interface bundle manifest to {manifest_path}")


if __name__ == "__main__":
    main()
