#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path

import torch
import torch.nn.functional as F


@dataclass(frozen=True)
class PacketFrame:
    sample_id: str
    packet_path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate lightweight delta-packet bridges into the frozen consumer "
            "feature space using leave-one-out ridge adapters."
        )
    )
    parser.add_argument("--bundle-dir", type=Path, required=True, help="Teacher packet bundle directory.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for bridge outputs.")
    parser.add_argument(
        "--mode",
        choices=["smoke", "full"],
        default="smoke",
        help="Execution mode label for durable outputs.",
    )
    parser.add_argument(
        "--delta-weight",
        type=float,
        default=8.0,
        help="Weight applied to delta features in concat-based bridge inputs.",
    )
    parser.add_argument(
        "--ridge-lambda",
        type=float,
        default=1.0,
        help="L2 regularization for the leave-one-out ridge bridge.",
    )
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_packet_frames(bundle_dir: Path) -> tuple[dict[str, object], list[PacketFrame]]:
    manifest_path = bundle_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    frames: list[PacketFrame] = []
    for frame in manifest["frames"]:
        packet_relpath = frame.get("packet_relpath")
        if packet_relpath is None:
            raise KeyError("Manifest frame is missing packet_relpath.")
        frames.append(
            PacketFrame(
                sample_id=frame["sample_id"],
                packet_path=bundle_dir / packet_relpath,
            )
        )
    return manifest, frames


def load_payloads(frames: list[PacketFrame]) -> list[dict[str, object]]:
    return [torch.load(frame.packet_path, map_location="cpu") for frame in frames]


def build_field_embeddings(payloads: list[dict[str, object]], components: list[tuple[str, float]]) -> torch.Tensor:
    rows: list[torch.Tensor] = []
    for payload in payloads:
        chunks = [
            float(weight) * torch.as_tensor(payload[field], dtype=torch.float32).flatten()
            for field, weight in components
        ]
        rows.append(torch.cat(chunks, dim=0))
    return torch.stack(rows, dim=0)


def normalize_rows(embeddings: torch.Tensor) -> torch.Tensor:
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


def fit_ridge_map(features: torch.Tensor, targets: torch.Tensor, ridge_lambda: float) -> torch.Tensor:
    ones = torch.ones(features.shape[0], 1, dtype=features.dtype)
    augmented = torch.cat((features, ones), dim=1)
    gram = augmented.T @ augmented
    reg = torch.eye(gram.shape[0], dtype=features.dtype) * ridge_lambda
    reg[-1, -1] = 0.0
    weights = torch.linalg.solve(gram + reg, augmented.T @ targets)
    return weights


def loo_bridge_embeddings(
    source_embeddings: torch.Tensor,
    target_embeddings: torch.Tensor,
    ridge_lambda: float,
) -> torch.Tensor:
    predictions: list[torch.Tensor] = []
    for holdout_idx in range(source_embeddings.shape[0]):
        train_mask = torch.ones(source_embeddings.shape[0], dtype=torch.bool)
        train_mask[holdout_idx] = False
        train_source = source_embeddings[train_mask]
        train_target = target_embeddings[train_mask]
        weights = fit_ridge_map(train_source, train_target, ridge_lambda)
        holdout_source = torch.cat(
            (
                source_embeddings[holdout_idx],
                torch.ones(1, dtype=source_embeddings.dtype),
            )
        )
        predictions.append(holdout_source @ weights)
    return normalize_rows(torch.stack(predictions, dim=0))


def build_markdown_report(
    summary_by_name: dict[str, dict[str, float]],
    teacher_packet_summary: dict[str, object],
    delta_weight: float,
    ridge_lambda: float,
) -> str:
    lines = [
        "# Delta Packet Bridge Evaluation",
        "",
        f"- teacher_type: `{teacher_packet_summary['teacher_type']}`",
        f"- feature_dim: `{teacher_packet_summary['feature_dim']}`",
        f"- delta_weight: `{delta_weight}`",
        f"- ridge_lambda: `{ridge_lambda}`",
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
    lines.append("## Notes")
    lines.append("")
    lines.append("- `pred_feat_to_target_feat_direct` is the bridge-free control in the frozen consumer feature space.")
    lines.append("- `pred_delta_to_target_feat_direct` measures whether delta is already aligned without any learned bridge.")
    lines.append("- `delta_ridge_to_target_feat_loo` uses a leave-one-out ridge adapter from `pred_delta` into the consumer feature space.")
    lines.append(
        "- `feat_plus_delta_ridge_to_target_feat_loo` uses the same leave-one-out ridge bridge but with concatenated "
        "static plus weighted delta input."
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    bundle_dir = args.bundle_dir.resolve()
    output_dir = args.output_dir.resolve()
    ensure_dir(output_dir)

    manifest, frames = read_packet_frames(bundle_dir)
    payloads = load_payloads(frames)
    sample_ids = [frame.sample_id for frame in frames]

    target_feat = normalize_rows(build_field_embeddings(payloads, [("target_feat", 1.0)]))
    pred_feat = normalize_rows(build_field_embeddings(payloads, [("pred_feat", 1.0)]))
    pred_delta = normalize_rows(build_field_embeddings(payloads, [("pred_delta", 1.0)]))
    feat_plus_delta = build_field_embeddings(
        payloads,
        [("pred_feat", 1.0), ("pred_delta", args.delta_weight)],
    )

    bridge_specs: list[tuple[str, torch.Tensor]] = [
        ("pred_feat_to_target_feat_direct", pred_feat),
        ("pred_delta_to_target_feat_direct", pred_delta),
        (
            "delta_ridge_to_target_feat_loo",
            loo_bridge_embeddings(
                source_embeddings=build_field_embeddings(payloads, [("pred_delta", 1.0)]),
                target_embeddings=build_field_embeddings(payloads, [("target_feat", 1.0)]),
                ridge_lambda=args.ridge_lambda,
            ),
        ),
        (
            f"feat_plus_{str(args.delta_weight).replace('.', 'p')}x_delta_ridge_to_target_feat_loo",
            loo_bridge_embeddings(
                source_embeddings=feat_plus_delta,
                target_embeddings=build_field_embeddings(payloads, [("target_feat", 1.0)]),
                ridge_lambda=args.ridge_lambda,
            ),
        ),
        ("target_feat_to_target_feat", target_feat),
    ]

    summary_by_name: dict[str, dict[str, float]] = {}
    for comparison_name, query_embeddings in bridge_specs:
        similarity = cosine_similarity_matrix(query_embeddings, target_feat)
        rows = retrieval_rows(sample_ids, sample_ids, similarity)
        summary_by_name[comparison_name] = summarize_rows(rows)
        csv_path = output_dir / f"{comparison_name}.csv"
        write_csv(
            csv_path,
            [
                "query_id",
                "predicted_id",
                "correct",
                "match_rank",
                "matching_similarity",
                "top1_similarity",
                "best_nonmatch_similarity",
                "margin_vs_best_nonmatch",
            ],
            rows,
        )

    summary = {
        "bundle_dir": str(bundle_dir),
        "output_dir": str(output_dir),
        "mode": args.mode,
        "frame_count": len(sample_ids),
        "sample_ids": sample_ids,
        "delta_weight": args.delta_weight,
        "ridge_lambda": args.ridge_lambda,
        "consumer_space": "target_feat",
        "teacher_packet_summary": manifest["teacher_packet_summary"],
        "consumer_metrics": summary_by_name,
        "upstream_aggregate_metrics": manifest["aggregate_metrics"],
    }
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    report_path = output_dir / "report.md"
    report_path.write_text(
        build_markdown_report(
            summary_by_name=summary_by_name,
            teacher_packet_summary=manifest["teacher_packet_summary"],
            delta_weight=args.delta_weight,
            ridge_lambda=args.ridge_lambda,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
