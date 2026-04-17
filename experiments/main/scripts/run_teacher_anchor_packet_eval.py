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
            "Evaluate a teacher gallery-anchor packet adapter that projects "
            "predicted packet queries into target feature space."
        )
    )
    parser.add_argument("--bundle-dir", type=Path, required=True, help="Teacher packet bundle directory.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for evaluation outputs.")
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
        help="Weight applied to delta vectors in the joint packet query/key space.",
    )
    parser.add_argument(
        "--anchor-logit-scale",
        type=float,
        default=16.0,
        help="Softmax logit scale for the teacher gallery-anchor projection.",
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


def format_weight(weight: float) -> str:
    return str(weight).replace(".", "p")


def build_embeddings(
    payloads: list[dict[str, object]],
    components: list[tuple[str, float]],
) -> torch.Tensor:
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


def write_similarity_matrix(path: Path, row_ids: list[str], col_ids: list[str], matrix: torch.Tensor) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["query_id", *col_ids])
        for query_id, scores in zip(row_ids, matrix.tolist()):
            writer.writerow([query_id, *[f"{score:.6f}" for score in scores]])


def teacher_gallery_anchor_projection(
    query_embeddings: torch.Tensor,
    anchor_key_embeddings: torch.Tensor,
    anchor_value_embeddings: torch.Tensor,
    logit_scale: float,
) -> tuple[torch.Tensor, torch.Tensor]:
    normalized_queries = normalize_rows(query_embeddings)
    normalized_keys = normalize_rows(anchor_key_embeddings)
    normalized_values = normalize_rows(anchor_value_embeddings)
    weights = (logit_scale * (normalized_queries @ normalized_keys.T)).softmax(dim=1)
    projected = weights @ normalized_values
    return normalize_rows(projected), weights


def write_anchor_weights(path: Path, query_ids: list[str], anchor_ids: list[str], weights: torch.Tensor) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["query_id", *anchor_ids])
        for query_id, row in zip(query_ids, weights.tolist()):
            writer.writerow([query_id, *[f"{value:.6f}" for value in row]])


def build_markdown_report(
    summary_by_name: dict[str, dict[str, float]],
    teacher_packet_summary: dict[str, object],
    delta_weight: float,
    anchor_logit_scale: float,
) -> str:
    lines = [
        "# Teacher Gallery-Anchor Packet Evaluation",
        "",
        f"- teacher_type: `{teacher_packet_summary['teacher_type']}`",
        f"- feature_dim: `{teacher_packet_summary['feature_dim']}`",
        f"- delta_weight: `{delta_weight}`",
        f"- anchor_logit_scale: `{anchor_logit_scale}`",
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
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `teacher_gallery_anchor_joint_to_target_feat` uses the teacher packet gallery as a retrieval-time memory bank.",
            "- Query keys are built from `pred_feat + delta_weight * pred_delta`.",
            "- Anchor keys are built from `target_feat + delta_weight * target_delta`.",
            "- Anchor values are normalized `target_feat` vectors, so the adapter explicitly projects into target feature space.",
        ]
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
    weight_label = format_weight(args.delta_weight)

    target_feat_raw = build_embeddings(payloads, [("target_feat", 1.0)])
    target_delta_raw = build_embeddings(payloads, [("target_delta", 1.0)])
    pred_feat_raw = build_embeddings(payloads, [("pred_feat", 1.0)])
    pred_delta_raw = build_embeddings(payloads, [("pred_delta", 1.0)])
    joint_pred_raw = build_embeddings(payloads, [("pred_feat", 1.0), ("pred_delta", args.delta_weight)])
    joint_target_raw = build_embeddings(payloads, [("target_feat", 1.0), ("target_delta", args.delta_weight)])

    target_feat = normalize_rows(target_feat_raw)
    target_delta = normalize_rows(target_delta_raw)
    pred_feat = normalize_rows(pred_feat_raw)
    pred_delta = normalize_rows(pred_delta_raw)
    joint_pred = normalize_rows(joint_pred_raw)
    joint_target = normalize_rows(joint_target_raw)

    teacher_anchor_proj, teacher_anchor_weights = teacher_gallery_anchor_projection(
        query_embeddings=joint_pred_raw,
        anchor_key_embeddings=joint_target_raw,
        anchor_value_embeddings=target_feat_raw,
        logit_scale=args.anchor_logit_scale,
    )

    comparisons: list[tuple[str, torch.Tensor, torch.Tensor]] = [
        ("target_feat_to_target_feat", target_feat, target_feat),
        ("pred_feat_to_target_feat", pred_feat, target_feat),
        ("pred_delta_to_target_delta", pred_delta, target_delta),
        (
            f"pred_feat_plus_{weight_label}x_delta_concat_to_target_feat_plus_{weight_label}x_delta_concat",
            joint_pred,
            joint_target,
        ),
        ("teacher_gallery_anchor_joint_to_target_feat", teacher_anchor_proj, target_feat),
    ]

    summary_by_name: dict[str, dict[str, float]] = {}
    for comparison_name, query_embeddings, gallery_embeddings in comparisons:
        similarity = cosine_similarity_matrix(query_embeddings, gallery_embeddings)
        rows = retrieval_rows(sample_ids, sample_ids, similarity)
        summary_by_name[comparison_name] = summarize_rows(rows)
        write_csv(output_dir / f"{comparison_name}_rows.csv", list(rows[0].keys()), rows)
        write_similarity_matrix(
            output_dir / f"similarity_{comparison_name}.csv",
            sample_ids,
            sample_ids,
            similarity,
        )

    write_anchor_weights(
        output_dir / "teacher_gallery_anchor_weights.csv",
        query_ids=sample_ids,
        anchor_ids=sample_ids,
        weights=teacher_anchor_weights,
    )

    report_text = build_markdown_report(
        summary_by_name=summary_by_name,
        teacher_packet_summary=manifest["teacher_packet_summary"],
        delta_weight=args.delta_weight,
        anchor_logit_scale=args.anchor_logit_scale,
    )
    (output_dir / "report.md").write_text(report_text, encoding="utf-8")

    summary = {
        "mode": args.mode,
        "bundle_dir": str(bundle_dir),
        "output_dir": str(output_dir),
        "delta_weight": args.delta_weight,
        "anchor_logit_scale": args.anchor_logit_scale,
        "anchor_bank_type": "teacher_gallery_memory",
        "frame_count": len(frames),
        "sample_ids": sample_ids,
        "upstream_aggregate_metrics": manifest["aggregate_metrics"],
        "teacher_packet_summary": manifest["teacher_packet_summary"],
        "consumer_metrics": summary_by_name,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Wrote teacher gallery-anchor packet evaluation to {output_dir}")


if __name__ == "__main__":
    main()
