#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path

import torch
import torch.nn.functional as F


SELF_FIELDS = ["target_feat", "target_delta", "pred_feat", "pred_delta"]
CROSS_SPECS = [
    ("pred_feat", "target_feat"),
    ("pred_delta", "target_delta"),
    ("pred_delta", "target_feat"),
]
CHUNK_MODES = ["seq_concat", "frame_mean"]
MISSING_SURFACES = ["query_projection", "query_packet_head"]


@dataclass(frozen=True)
class ChunkBundle:
    chunk_id: str
    bundle_dir: Path
    manifest: dict[str, object]
    packet_paths: list[Path]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Localize where chunk discrimination collapses across widened teacher-packet bundles."
    )
    parser.add_argument(
        "--bundle-dirs",
        type=Path,
        nargs="+",
        required=True,
        help="Teacher packet bundle directories, one per chunk object.",
    )
    parser.add_argument("--output-dir", type=Path, required=True, help="Output directory for localization results.")
    parser.add_argument(
        "--mode",
        choices=["smoke", "full"],
        default="smoke",
        help="Recorded execution mode. The bounded bundle count stays fixed in this round.",
    )
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_chunk_bundle(bundle_dir: Path) -> ChunkBundle:
    manifest_path = bundle_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    frames = sorted(manifest["frames"], key=lambda item: int(item["frame_index"]))
    packet_paths = [bundle_dir / str(frame["packet_relpath"]) for frame in frames]
    return ChunkBundle(chunk_id=bundle_dir.name, bundle_dir=bundle_dir, manifest=manifest, packet_paths=packet_paths)


def load_payloads(packet_paths: list[Path]) -> list[dict[str, object]]:
    return [torch.load(packet_path, map_location="cpu") for packet_path in packet_paths]


def chunk_raw_embedding(payloads: list[dict[str, object]], field: str, chunk_mode: str) -> torch.Tensor:
    per_frame = torch.stack(
        [torch.as_tensor(payload[field], dtype=torch.float32).flatten() for payload in payloads],
        dim=0,
    )
    if chunk_mode == "seq_concat":
        return per_frame.reshape(-1)
    if chunk_mode == "frame_mean":
        return per_frame.mean(dim=0)
    raise ValueError(f"Unsupported chunk mode: {chunk_mode}")


def normalize_rows(rows: torch.Tensor) -> torch.Tensor:
    return F.normalize(rows, dim=1)


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


def similarity_stats(similarity: torch.Tensor) -> dict[str, float]:
    chunk_count = similarity.shape[0]
    mask = ~torch.eye(chunk_count, dtype=torch.bool)
    offdiag = similarity[mask]
    return {
        "diag_mean": float(torch.diag(similarity).mean().item()),
        "offdiag_mean": float(offdiag.mean().item()),
        "offdiag_min": float(offdiag.min().item()),
        "offdiag_max": float(offdiag.max().item()),
    }


def variance_stats(raw_embeddings: torch.Tensor, normalized_embeddings: torch.Tensor) -> dict[str, float]:
    raw_var = raw_embeddings.var(dim=0, unbiased=False)
    norm_var = normalized_embeddings.var(dim=0, unbiased=False)
    return {
        "raw_mean_l2_norm": float(raw_embeddings.norm(dim=1).mean().item()),
        "raw_mean_dimension_variance": float(raw_var.mean().item()),
        "raw_max_dimension_variance": float(raw_var.max().item()),
        "normalized_mean_dimension_variance": float(norm_var.mean().item()),
        "normalized_max_dimension_variance": float(norm_var.max().item()),
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


def write_json(path: Path, payload: dict[str, object]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def self_surface_name(field: str, chunk_mode: str) -> str:
    return f"{field}_to_{field}_{chunk_mode}"


def cross_surface_name(query_field: str, gallery_field: str, chunk_mode: str) -> str:
    return f"{query_field}_to_{gallery_field}_{chunk_mode}"


def field_collapse_flag(metrics: dict[str, float], chance: float) -> bool:
    return metrics["top1_accuracy"] <= chance + 1e-9 and metrics["offdiag_mean"] >= 0.999


def build_markdown_report(
    mode: str,
    bundle_dirs: list[Path],
    chunk_ids: list[str],
    frame_count_per_chunk: int,
    chance_top1: float,
    self_summary: dict[str, dict[str, object]],
    cross_summary: dict[str, dict[str, object]],
    localization_judgment: dict[str, object],
) -> str:
    lines = [
        "# Query Collapse Localization",
        "",
        f"- mode: `{mode}`",
        f"- chunk_count: `{len(chunk_ids)}`",
        f"- frame_count_per_chunk: `{frame_count_per_chunk}`",
        f"- chance_top1: `{chance_top1:.4f}`",
        "- bundle_dirs:",
    ]
    lines.extend([f"  - `{bundle_dir}`" for bundle_dir in bundle_dirs])
    lines.extend(
        [
            "",
            "## Accessible Surfaces",
            "",
            "- accessible:",
            "  - `target_feat`",
            "  - `target_delta`",
            "  - `pred_feat`",
            "  - `pred_delta`",
            "- missing:",
            "  - `query_projection`",
            "  - `query_packet_head`",
            "",
            "## Self-Surface Discrimination",
            "",
            "| Surface | Top-1 | Mean Rank | Offdiag Mean Cosine | Raw Mean Dim Var | Collapsed |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for name, payload in self_summary.items():
        metrics = payload["retrieval"]
        sim = payload["similarity"]
        var = payload["variance"]
        lines.append(
            "| "
            f"{name} | "
            f"{metrics['top1_accuracy']:.4f} | "
            f"{metrics['mean_match_rank']:.4f} | "
            f"{sim['offdiag_mean']:.4f} | "
            f"{var['raw_mean_dimension_variance']:.6f} | "
            f"{payload['collapsed']} |"
        )
    lines.extend(
        [
            "",
            "## Cross-Surface Comparisons",
            "",
            "| Comparison | Top-1 | Mean Rank | Offdiag Mean Cosine | Mean Margin |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for name, payload in cross_summary.items():
        metrics = payload["retrieval"]
        sim = payload["similarity"]
        lines.append(
            "| "
            f"{name} | "
            f"{metrics['top1_accuracy']:.4f} | "
            f"{metrics['mean_match_rank']:.4f} | "
            f"{sim['offdiag_mean']:.4f} | "
            f"{metrics['mean_margin_vs_best_nonmatch']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Localization Judgment",
            "",
            f"- earliest_accessible_collapse_surface: `{localization_judgment['earliest_accessible_collapse_surface']}`",
            f"- predicted_packet_surface_collapsed: `{localization_judgment['predicted_packet_surface_collapsed']}`",
            f"- target_surface_discriminative: `{localization_judgment['target_surface_discriminative']}`",
            f"- recommendation: {localization_judgment['recommended_next_action']}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    ensure_dir(output_dir)

    bundles = [load_chunk_bundle(bundle_dir.resolve()) for bundle_dir in args.bundle_dirs]
    chunk_ids = [bundle.chunk_id for bundle in bundles]
    payloads_by_chunk = [load_payloads(bundle.packet_paths) for bundle in bundles]
    frame_count_per_chunk = len(payloads_by_chunk[0])
    if any(len(payloads) != frame_count_per_chunk for payloads in payloads_by_chunk):
        raise ValueError("All chunk bundles must contain the same number of frames.")

    chance_top1 = 1.0 / float(len(chunk_ids))
    self_summary: dict[str, dict[str, object]] = {}
    cross_summary: dict[str, dict[str, object]] = {}

    raw_embeddings_cache: dict[tuple[str, str], torch.Tensor] = {}
    normalized_embeddings_cache: dict[tuple[str, str], torch.Tensor] = {}

    for field in SELF_FIELDS:
        for chunk_mode in CHUNK_MODES:
            raw_embeddings = torch.stack(
                [chunk_raw_embedding(payloads, field, chunk_mode) for payloads in payloads_by_chunk],
                dim=0,
            )
            normalized_embeddings = normalize_rows(raw_embeddings)
            raw_embeddings_cache[(field, chunk_mode)] = raw_embeddings
            normalized_embeddings_cache[(field, chunk_mode)] = normalized_embeddings

            similarity = cosine_similarity_matrix(normalized_embeddings, normalized_embeddings)
            rows = retrieval_rows(chunk_ids, chunk_ids, similarity)
            name = self_surface_name(field, chunk_mode)
            payload = {
                "retrieval": summarize_rows(rows),
                "similarity": similarity_stats(similarity),
                "variance": variance_stats(raw_embeddings, normalized_embeddings),
            }
            payload["collapsed"] = field_collapse_flag(
                {**payload["retrieval"], **payload["similarity"]},
                chance_top1,
            )
            self_summary[name] = payload
            write_csv(output_dir / f"{name}_rows.csv", list(rows[0].keys()), rows)
            write_similarity_matrix(output_dir / f"similarity_{name}.csv", chunk_ids, chunk_ids, similarity)

    for query_field, gallery_field in CROSS_SPECS:
        for chunk_mode in CHUNK_MODES:
            query_embeddings = normalized_embeddings_cache[(query_field, chunk_mode)]
            gallery_embeddings = normalized_embeddings_cache[(gallery_field, chunk_mode)]
            similarity = cosine_similarity_matrix(query_embeddings, gallery_embeddings)
            rows = retrieval_rows(chunk_ids, chunk_ids, similarity)
            name = cross_surface_name(query_field, gallery_field, chunk_mode)
            cross_summary[name] = {
                "retrieval": summarize_rows(rows),
                "similarity": similarity_stats(similarity),
            }
            write_csv(output_dir / f"{name}_rows.csv", list(rows[0].keys()), rows)
            write_similarity_matrix(output_dir / f"similarity_{name}.csv", chunk_ids, chunk_ids, similarity)

    target_ok = (
        self_summary["target_feat_to_target_feat_seq_concat"]["retrieval"]["top1_accuracy"] == 1.0
        and not self_summary["target_feat_to_target_feat_seq_concat"]["collapsed"]
        and not self_summary["target_delta_to_target_delta_seq_concat"]["collapsed"]
    )
    pred_collapsed = (
        self_summary["pred_feat_to_pred_feat_seq_concat"]["collapsed"]
        and self_summary["pred_delta_to_pred_delta_seq_concat"]["collapsed"]
    )
    if pred_collapsed and target_ok:
        earliest_surface = "exported_predicted_packets_or_earlier"
        recommendation = (
            "Exported predicted packets are already collapsed while target packets remain discriminative. "
            "If deeper query-side projections are inaccessible, treat exported predicted packets as the earliest "
            "accessible collapse surface and test at most one minimal repair that acts on the query head or predictor."
        )
    elif target_ok:
        earliest_surface = "not_collapsed_on_accessible_surfaces"
        recommendation = (
            "Accessible surfaces still retain some chunk discrimination. Inspect the cross-surface rows before "
            "choosing whether a repair is necessary."
        )
    else:
        earliest_surface = "unclear_target_side_contract"
        recommendation = (
            "Target-side discrimination is not clean on the accessible surfaces. Re-check bundle integrity before "
            "attributing the failure to the query-side packet head."
        )

    localization_judgment = {
        "earliest_accessible_collapse_surface": earliest_surface,
        "predicted_packet_surface_collapsed": pred_collapsed,
        "target_surface_discriminative": target_ok,
        "missing_planned_surfaces": MISSING_SURFACES,
        "recommended_next_action": recommendation,
    }

    report_text = build_markdown_report(
        args.mode,
        [bundle.bundle_dir for bundle in bundles],
        chunk_ids,
        frame_count_per_chunk,
        chance_top1,
        self_summary,
        cross_summary,
        localization_judgment,
    )
    (output_dir / "report.md").write_text(report_text, encoding="utf-8")

    summary = {
        "mode": args.mode,
        "bundle_dirs": [str(bundle.bundle_dir) for bundle in bundles],
        "chunk_ids": chunk_ids,
        "frame_count_per_chunk": frame_count_per_chunk,
        "chance_top1": chance_top1,
        "accessible_surfaces": SELF_FIELDS,
        "missing_surfaces": MISSING_SURFACES,
        "self_surface_metrics": self_summary,
        "cross_surface_metrics": cross_summary,
        "localization_judgment": localization_judgment,
    }
    write_json(output_dir / "summary.json", summary)
    print(f"Wrote query collapse localization package to {output_dir}")


if __name__ == "__main__":
    main()
