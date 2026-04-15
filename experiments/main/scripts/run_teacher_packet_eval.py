#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path

import torch
import torch.nn.functional as F


COMPARISON_SPECS = [
    ("target_feat_to_target_feat", ["target_feat"], ["target_feat"]),
    ("pred_feat_to_target_feat", ["pred_feat"], ["target_feat"]),
    ("pred_delta_to_target_delta", ["pred_delta"], ["target_delta"]),
    (
        "pred_feat_plus_delta_to_target_feat_plus_delta",
        ["pred_feat", "pred_delta"],
        ["target_feat", "target_delta"],
    ),
]


@dataclass(frozen=True)
class PacketFrame:
    sample_id: str
    packet_path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate teacher feature packets with retrieval-style packet matching metrics."
    )
    parser.add_argument("--bundle-dir", type=Path, required=True, help="Teacher packet interface bundle directory.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Output directory for evaluation results.")
    parser.add_argument(
        "--mode",
        choices=["smoke", "full"],
        default="smoke",
        help="Recorded execution mode. The bounded bundle size stays fixed in this round.",
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


def build_embeddings(payloads: list[dict[str, object]], fields: list[str]) -> torch.Tensor:
    rows: list[torch.Tensor] = []
    for payload in payloads:
        chunks = [torch.as_tensor(payload[field], dtype=torch.float32).flatten() for field in fields]
        rows.append(torch.cat(chunks, dim=0))
    return F.normalize(torch.stack(rows, dim=0), dim=1)


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
    summary_by_name: dict[str, dict[str, float]],
    teacher_packet_summary: dict[str, object],
) -> str:
    lines = [
        "# Teacher Packet Evaluation",
        "",
        f"- teacher_type: `{teacher_packet_summary['teacher_type']}`",
        f"- feature_dim: `{teacher_packet_summary['feature_dim']}`",
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

    manifest, frames = read_packet_frames(bundle_dir)
    payloads = load_payloads(frames)
    sample_ids = [frame.sample_id for frame in frames]

    summary_by_name: dict[str, dict[str, float]] = {}
    for comparison_name, query_fields, gallery_fields in COMPARISON_SPECS:
        query_embeddings = build_embeddings(payloads, query_fields)
        gallery_embeddings = build_embeddings(payloads, gallery_fields)
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

    report_text = build_markdown_report(summary_by_name, manifest["teacher_packet_summary"])
    (output_dir / "report.md").write_text(report_text, encoding="utf-8")

    summary = {
        "mode": args.mode,
        "bundle_dir": str(bundle_dir),
        "output_dir": str(output_dir),
        "frame_count": len(frames),
        "sample_ids": sample_ids,
        "upstream_aggregate_metrics": manifest["aggregate_metrics"],
        "teacher_packet_summary": manifest["teacher_packet_summary"],
        "consumer_metrics": summary_by_name,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Wrote teacher packet evaluation to {output_dir}")


if __name__ == "__main__":
    main()
