#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torchvision.models import ResNet18_Weights, resnet18


@dataclass(frozen=True)
class BundleFrame:
    sample_id: str
    original_path: Path
    reconstructed_path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a frozen torchvision retrieval/matching consumer on an interface bundle."
    )
    parser.add_argument("--bundle-dir", type=Path, required=True, help="Interface bundle directory.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Output directory for evaluation results.")
    parser.add_argument(
        "--model",
        choices=["resnet18"],
        default="resnet18",
        help="Frozen vision backbone to use for the first downstream comparison.",
    )
    parser.add_argument(
        "--mode",
        choices=["smoke", "full"],
        default="smoke",
        help="Recorded execution mode. The bounded bundle size stays fixed in this round.",
    )
    parser.add_argument("--batch-size", type=int, default=16, help="Embedding batch size.")
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda"],
        default="auto",
        help="Device selection policy.",
    )
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_bundle_frames(bundle_dir: Path) -> tuple[dict[str, object], list[BundleFrame]]:
    manifest_path = bundle_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    frames: list[BundleFrame] = []
    for frame in manifest["frames"]:
        frames.append(
            BundleFrame(
                sample_id=frame["sample_id"],
                original_path=bundle_dir / frame["original_relpath"],
                reconstructed_path=bundle_dir / frame["reconstructed_relpath"],
            )
        )
    return manifest, frames


def pick_device(device_arg: str) -> torch.device:
    if device_arg == "cpu":
        return torch.device("cpu")
    if device_arg == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is not available.")
        return torch.device("cuda")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def build_model(model_name: str, device: torch.device) -> tuple[nn.Module, object, dict[str, str]]:
    if model_name != "resnet18":
        raise ValueError(f"Unsupported model: {model_name}")

    weights = ResNet18_Weights.DEFAULT
    model = resnet18(weights=weights)
    feature_extractor = nn.Sequential(*list(model.children())[:-1]).to(device)
    feature_extractor.eval()
    meta = {
        "model_name": model_name,
        "weights_name": getattr(weights, "name", "DEFAULT"),
    }
    return feature_extractor, weights.transforms(), meta


def load_rgb_image(path: Path) -> Image.Image:
    with Image.open(path) as image:
        return image.convert("RGB")


def compute_embeddings(
    paths: list[Path],
    model: nn.Module,
    transform: object,
    device: torch.device,
    batch_size: int,
) -> torch.Tensor:
    outputs: list[torch.Tensor] = []
    with torch.inference_mode():
        for start in range(0, len(paths), batch_size):
            batch_paths = paths[start : start + batch_size]
            images = [transform(load_rgb_image(path)) for path in batch_paths]
            batch = torch.stack(images, dim=0).to(device)
            features = model(batch).flatten(1)
            outputs.append(features.cpu())
    embeddings = torch.cat(outputs, dim=0)
    return F.normalize(embeddings, dim=1)


def cosine_similarity_matrix(query_embeddings: torch.Tensor, gallery_embeddings: torch.Tensor) -> torch.Tensor:
    return query_embeddings @ gallery_embeddings.T


def retrieval_rows(
    query_ids: list[str],
    gallery_ids: list[str],
    similarity_matrix: torch.Tensor,
) -> list[dict[str, object]]:
    gallery_index = {sample_id: idx for idx, sample_id in enumerate(gallery_ids)}
    rows: list[dict[str, object]] = []
    for query_idx, query_id in enumerate(query_ids):
        target_idx = gallery_index[query_id]
        scores = similarity_matrix[query_idx]
        sorted_indices = torch.argsort(scores, descending=True)
        top_idx = int(sorted_indices[0].item())
        match_rank = int((sorted_indices == target_idx).nonzero(as_tuple=False)[0].item()) + 1
        nonmatch_scores = torch.cat((scores[:target_idx], scores[target_idx + 1 :]))
        best_nonmatch_similarity = float(nonmatch_scores.max().item()) if len(nonmatch_scores) else 0.0
        matching_similarity = float(scores[target_idx].item())
        rows.append(
            {
                "query_id": query_id,
                "predicted_id": gallery_ids[top_idx],
                "correct": top_idx == target_idx,
                "match_rank": match_rank,
                "matching_similarity": matching_similarity,
                "top1_similarity": float(scores[top_idx].item()),
                "best_nonmatch_similarity": best_nonmatch_similarity,
                "margin_vs_best_nonmatch": matching_similarity - best_nonmatch_similarity,
            }
        )
    return rows


def summarize_rows(rows: list[dict[str, object]]) -> dict[str, float]:
    total = float(len(rows))
    correct = sum(1.0 for row in rows if row["correct"])
    mean_rank = sum(float(row["match_rank"]) for row in rows) / total
    mean_matching_similarity = sum(float(row["matching_similarity"]) for row in rows) / total
    mean_best_nonmatch_similarity = sum(float(row["best_nonmatch_similarity"]) for row in rows) / total
    mean_margin = sum(float(row["margin_vs_best_nonmatch"]) for row in rows) / total
    return {
        "top1_accuracy": correct / total,
        "mean_match_rank": mean_rank,
        "mean_matching_similarity": mean_matching_similarity,
        "mean_best_nonmatch_similarity": mean_best_nonmatch_similarity,
        "mean_margin_vs_best_nonmatch": mean_margin,
    }


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_similarity_matrix(path: Path, row_ids: list[str], col_ids: list[str], matrix: torch.Tensor) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["query_id", *col_ids])
        for query_id, scores in zip(row_ids, matrix.tolist()):
            writer.writerow([query_id, *[f"{score:.6f}" for score in scores]])


def build_markdown_report(
    model_meta: dict[str, str],
    device: str,
    summary_by_name: dict[str, dict[str, float]],
) -> str:
    lines = [
        "# Frozen Consumer Evaluation",
        "",
        f"- model: `{model_meta['model_name']}`",
        f"- weights: `{model_meta['weights_name']}`",
        f"- device: `{device}`",
        "",
        "| Comparison | Top-1 Accuracy | Mean Match Rank | Mean Matching Similarity | Mean Margin vs Best Nonmatch |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, metrics in summary_by_name.items():
        lines.append(
            "| "
            f"{name} | "
            f"{metrics['top1_accuracy']:.4f} | "
            f"{metrics['mean_match_rank']:.4f} | "
            f"{metrics['mean_matching_similarity']:.4f} | "
            f"{metrics['mean_margin_vs_best_nonmatch']:.4f} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    bundle_dir = args.bundle_dir.resolve()
    output_dir = args.output_dir.resolve()
    ensure_dir(output_dir)

    manifest, frames = read_bundle_frames(bundle_dir)
    device = pick_device(args.device)
    model, transform, model_meta = build_model(args.model, device)

    sample_ids = [frame.sample_id for frame in frames]
    original_paths = [frame.original_path for frame in frames]
    reconstructed_paths = [frame.reconstructed_path for frame in frames]

    original_embeddings = compute_embeddings(original_paths, model, transform, device, args.batch_size)
    reconstructed_embeddings = compute_embeddings(reconstructed_paths, model, transform, device, args.batch_size)

    o2o = cosine_similarity_matrix(original_embeddings, original_embeddings)
    r2o = cosine_similarity_matrix(reconstructed_embeddings, original_embeddings)
    o2r = cosine_similarity_matrix(original_embeddings, reconstructed_embeddings)

    o2o_rows = retrieval_rows(sample_ids, sample_ids, o2o)
    r2o_rows = retrieval_rows(sample_ids, sample_ids, r2o)
    o2r_rows = retrieval_rows(sample_ids, sample_ids, o2r)

    summary_by_name = {
        "original_to_original": summarize_rows(o2o_rows),
        "reconstructed_to_original": summarize_rows(r2o_rows),
        "original_to_reconstructed": summarize_rows(o2r_rows),
    }

    write_csv(
        output_dir / "original_to_original_rows.csv",
        list(o2o_rows[0].keys()),
        o2o_rows,
    )
    write_csv(
        output_dir / "reconstructed_to_original_rows.csv",
        list(r2o_rows[0].keys()),
        r2o_rows,
    )
    write_csv(
        output_dir / "original_to_reconstructed_rows.csv",
        list(o2r_rows[0].keys()),
        o2r_rows,
    )

    write_similarity_matrix(output_dir / "similarity_original_to_original.csv", sample_ids, sample_ids, o2o)
    write_similarity_matrix(output_dir / "similarity_reconstructed_to_original.csv", sample_ids, sample_ids, r2o)
    write_similarity_matrix(output_dir / "similarity_original_to_reconstructed.csv", sample_ids, sample_ids, o2r)

    report_text = build_markdown_report(model_meta, str(device), summary_by_name)
    (output_dir / "report.md").write_text(report_text, encoding="utf-8")

    summary = {
        "mode": args.mode,
        "bundle_dir": str(bundle_dir),
        "output_dir": str(output_dir),
        "device": str(device),
        "batch_size": args.batch_size,
        "frame_count": len(frames),
        "sample_ids": sample_ids,
        "model": model_meta,
        "upstream_aggregate_metrics": manifest["aggregate_metrics"],
        "consumer_metrics": summary_by_name,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Wrote frozen consumer evaluation to {output_dir}")


if __name__ == "__main__":
    main()
