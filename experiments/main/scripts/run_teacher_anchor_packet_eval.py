#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import torch
import torch.nn.functional as F


HUB_CLUSTER_IDS = ("0009", "0010", "0011")


@dataclass(frozen=True)
class PacketBundle:
    bundle_id: str
    bundle_dir: Path
    manifest: dict[str, object]
    sample_ids: list[str]
    payloads: list[dict[str, object]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate raw and hubness-corrected teacher-anchor packet scoring on "
            "one or more frozen teacher-packet bundles."
        )
    )
    parser.add_argument(
        "--bundle-dir",
        dest="bundle_dirs",
        type=Path,
        nargs="+",
        required=True,
        help="Teacher packet bundle directories. One or more values are allowed.",
    )
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
        help="Base logit scale used by the teacher-anchor scoring rules.",
    )
    parser.add_argument(
        "--csls-k",
        type=int,
        default=3,
        help="Top-k neighborhood used by the CSLS correction.",
    )
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_packet_bundle(bundle_dir: Path) -> PacketBundle:
    manifest_path = bundle_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    frames = sorted(
        manifest["frames"],
        key=lambda item: int(item.get("frame_index", item["sample_id"])),
    )
    sample_ids: list[str] = []
    payloads: list[dict[str, object]] = []
    for frame in frames:
        packet_relpath = frame.get("packet_relpath")
        if packet_relpath is None:
            raise KeyError(f"Manifest frame in {bundle_dir} is missing packet_relpath.")
        sample_ids.append(str(frame["sample_id"]))
        payloads.append(torch.load(bundle_dir / str(packet_relpath), map_location="cpu"))
    return PacketBundle(
        bundle_id=bundle_dir.name,
        bundle_dir=bundle_dir,
        manifest=manifest,
        sample_ids=sample_ids,
        payloads=payloads,
    )


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


def raw_similarity_scores(query_raw: torch.Tensor, anchor_key_raw: torch.Tensor) -> torch.Tensor:
    normalized_queries = normalize_rows(query_raw)
    normalized_keys = normalize_rows(anchor_key_raw)
    return normalized_queries @ normalized_keys.T


def qb_norm_logits(raw_scores: torch.Tensor, logit_scale: float) -> torch.Tensor:
    anchor_mean = raw_scores.mean(dim=0, keepdim=True)
    anchor_std = raw_scores.std(dim=0, keepdim=True, unbiased=False).clamp_min(1e-6)
    return logit_scale * ((raw_scores - anchor_mean) / anchor_std)


def dis_logits(raw_scores: torch.Tensor, logit_scale: float) -> torch.Tensor:
    scaled = logit_scale * raw_scores
    log_anchor_prior = torch.logsumexp(scaled, dim=0, keepdim=True) - math.log(raw_scores.shape[0])
    return scaled - log_anchor_prior


def csls_logits(raw_scores: torch.Tensor, logit_scale: float, csls_k: int) -> torch.Tensor:
    neighbor_k = max(1, min(csls_k, raw_scores.shape[1]))
    query_density = raw_scores.topk(neighbor_k, dim=1).values.mean(dim=1, keepdim=True)
    anchor_density = raw_scores.T.topk(neighbor_k, dim=1).values.mean(dim=1).unsqueeze(0)
    return logit_scale * (2.0 * raw_scores - query_density - anchor_density)


def teacher_anchor_projection(
    query_raw: torch.Tensor,
    anchor_key_raw: torch.Tensor,
    anchor_value_raw: torch.Tensor,
    corrected_logits: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    weights = corrected_logits.softmax(dim=1)
    normalized_values = normalize_rows(anchor_value_raw)
    projected = weights @ normalized_values
    return normalize_rows(projected), weights


def retrieval_rows(
    bundle_id: str,
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
                "bundle_id": bundle_id,
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
        "query_count": total,
    }


def build_anchor_weight_rows(
    bundle_id: str,
    query_ids: list[str],
    anchor_ids: list[str],
    weights: torch.Tensor,
) -> list[dict[str, object]]:
    hub_indices = [idx for idx, anchor_id in enumerate(anchor_ids) if anchor_id in HUB_CLUSTER_IDS]
    rows: list[dict[str, object]] = []
    for query_id, weight_row in zip(query_ids, weights.tolist()):
        top_index = max(range(len(weight_row)), key=lambda idx: weight_row[idx])
        hub_mass = sum(weight_row[idx] for idx in hub_indices)
        row = {
            "bundle_id": bundle_id,
            "query_id": query_id,
            "predicted_anchor_id": anchor_ids[top_index],
            "hub_cluster_weight_mass": hub_mass,
        }
        for anchor_id, value in zip(anchor_ids, weight_row):
            row[f"anchor_{anchor_id}"] = value
        rows.append(row)
    return rows


def summarize_anchor_weight_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    predicted_anchor_ids = [str(row["predicted_anchor_id"]) for row in rows]
    counts = Counter(predicted_anchor_ids)
    total = float(len(predicted_anchor_ids))
    hub_count = sum(counts[anchor_id] for anchor_id in HUB_CLUSTER_IDS)
    max_anchor_share = max(counts.values()) / total if counts else 0.0
    mean_hub_weight_mass = (
        sum(float(row["hub_cluster_weight_mass"]) for row in rows) / total if rows else 0.0
    )
    return {
        "unique_top1_anchor_count": len(counts),
        "max_top1_anchor_share": max_anchor_share,
        "hub_cluster_share_0009_0010_0011": hub_count / total if total else 0.0,
        "mean_weight_mass_on_hub_cluster": mean_hub_weight_mass,
        "top1_anchor_histogram": dict(sorted(counts.items())),
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
    diagnostics_by_name: dict[str, dict[str, object]],
    teacher_packet_summary: dict[str, object],
    bundle_dirs: list[Path],
    delta_weight: float,
    anchor_logit_scale: float,
    csls_k: int,
) -> str:
    lines = [
        "# Querybank Teacher-Anchor Packet Evaluation",
        "",
        f"- teacher_type: `{teacher_packet_summary['teacher_type']}`",
        f"- feature_dim: `{teacher_packet_summary['feature_dim']}`",
        f"- bundle_count: `{len(bundle_dirs)}`",
        f"- delta_weight: `{delta_weight}`",
        f"- anchor_logit_scale: `{anchor_logit_scale}`",
        f"- csls_k: `{csls_k}`",
        "- bundle_dirs:",
    ]
    lines.extend([f"  - `{bundle_dir}`" for bundle_dir in bundle_dirs])
    lines.extend(
        [
            "",
            "| Comparison | Top-1 Accuracy | Mean Match Rank | Mean Margin | Unique Top-1 Anchors | Max Anchor Share | Hub Cluster Share | Mean Hub Weight Mass |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for name, metrics in summary_by_name.items():
        diagnostics = diagnostics_by_name.get(name)
        if diagnostics is None:
            unique_anchors = "-"
            max_anchor_share = "-"
            hub_cluster_share = "-"
            mean_hub_weight_mass = "-"
        else:
            unique_anchors = str(diagnostics["unique_top1_anchor_count"])
            max_anchor_share = f"{diagnostics['max_top1_anchor_share']:.4f}"
            hub_cluster_share = f"{diagnostics['hub_cluster_share_0009_0010_0011']:.4f}"
            mean_hub_weight_mass = f"{diagnostics['mean_weight_mass_on_hub_cluster']:.4f}"
        lines.append(
            "| "
            f"{name} | "
            f"{metrics['top1_accuracy']:.4f} | "
            f"{metrics['mean_match_rank']:.4f} | "
            f"{metrics['mean_margin_vs_best_nonmatch']:.4f} | "
            f"{unique_anchors} | "
            f"{max_anchor_share} | "
            f"{hub_cluster_share} | "
            f"{mean_hub_weight_mass} |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `raw_global_bank_to_target_feat` is the current widened failure reference.",
            "- `qb_norm_teacher_anchor_to_target_feat` is the headline route for this smoke.",
            "- `dis_teacher_anchor_to_target_feat` keeps the Dynamic Inverted Softmax sibling visible inside the same bounded pass.",
            "- `csls_teacher_anchor_to_target_feat` is the classical local-scaling control.",
            "- Hub-cluster diagnostics use anchors `0009`, `0010`, and `0011`.",
        ]
    )
    return "\n".join(lines)


def evaluate_bundle(
    bundle: PacketBundle,
    delta_weight: float,
    anchor_logit_scale: float,
    csls_k: int,
) -> tuple[
    dict[str, list[dict[str, object]]],
    dict[str, list[dict[str, object]]],
    dict[str, torch.Tensor],
]:
    sample_ids = bundle.sample_ids
    payloads = bundle.payloads
    weight_label = format_weight(delta_weight)

    target_feat_raw = build_embeddings(payloads, [("target_feat", 1.0)])
    target_delta_raw = build_embeddings(payloads, [("target_delta", 1.0)])
    pred_feat_raw = build_embeddings(payloads, [("pred_feat", 1.0)])
    pred_delta_raw = build_embeddings(payloads, [("pred_delta", 1.0)])
    joint_pred_raw = build_embeddings(payloads, [("pred_feat", 1.0), ("pred_delta", delta_weight)])
    joint_target_raw = build_embeddings(payloads, [("target_feat", 1.0), ("target_delta", delta_weight)])

    target_feat = normalize_rows(target_feat_raw)
    target_delta = normalize_rows(target_delta_raw)
    pred_feat = normalize_rows(pred_feat_raw)
    pred_delta = normalize_rows(pred_delta_raw)
    joint_pred = normalize_rows(joint_pred_raw)
    joint_target = normalize_rows(joint_target_raw)

    direct_comparisons: list[tuple[str, torch.Tensor, torch.Tensor]] = [
        ("target_feat_to_target_feat", target_feat, target_feat),
        ("pred_feat_to_target_feat", pred_feat, target_feat),
        ("pred_delta_to_target_delta", pred_delta, target_delta),
        (
            f"pred_feat_plus_{weight_label}x_delta_concat_to_target_feat_plus_{weight_label}x_delta_concat",
            joint_pred,
            joint_target,
        ),
    ]

    raw_scores = raw_similarity_scores(joint_pred_raw, joint_target_raw)
    anchor_mode_specs = [
        ("raw_global_bank_to_target_feat", anchor_logit_scale * raw_scores),
        ("qb_norm_teacher_anchor_to_target_feat", qb_norm_logits(raw_scores, anchor_logit_scale)),
        ("dis_teacher_anchor_to_target_feat", dis_logits(raw_scores, anchor_logit_scale)),
        ("csls_teacher_anchor_to_target_feat", csls_logits(raw_scores, anchor_logit_scale, csls_k)),
    ]

    row_map: dict[str, list[dict[str, object]]] = {}
    anchor_weight_rows: dict[str, list[dict[str, object]]] = {}
    similarity_map: dict[str, torch.Tensor] = {}

    for comparison_name, query_embeddings, gallery_embeddings in direct_comparisons:
        similarity = cosine_similarity_matrix(query_embeddings, gallery_embeddings)
        row_map[comparison_name] = retrieval_rows(bundle.bundle_id, sample_ids, sample_ids, similarity)
        similarity_map[comparison_name] = similarity

    for comparison_name, corrected_logits in anchor_mode_specs:
        projected, weights = teacher_anchor_projection(
            query_raw=joint_pred_raw,
            anchor_key_raw=joint_target_raw,
            anchor_value_raw=target_feat_raw,
            corrected_logits=corrected_logits,
        )
        similarity = cosine_similarity_matrix(projected, target_feat)
        row_map[comparison_name] = retrieval_rows(bundle.bundle_id, sample_ids, sample_ids, similarity)
        anchor_weight_rows[comparison_name] = build_anchor_weight_rows(
            bundle_id=bundle.bundle_id,
            query_ids=sample_ids,
            anchor_ids=sample_ids,
            weights=weights,
        )
        similarity_map[comparison_name] = similarity

    return row_map, anchor_weight_rows, similarity_map


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    ensure_dir(output_dir)

    bundles = [load_packet_bundle(bundle_dir.resolve()) for bundle_dir in args.bundle_dirs]
    bundle_dirs = [bundle.bundle_dir for bundle in bundles]
    if not bundles:
        raise ValueError("At least one bundle directory is required.")

    reference_ids = bundles[0].sample_ids
    for bundle in bundles[1:]:
        if bundle.sample_ids != reference_ids:
            raise ValueError("All bundle directories must expose the same ordered sample ids for aggregation.")

    aggregated_rows: dict[str, list[dict[str, object]]] = defaultdict(list)
    aggregated_anchor_rows: dict[str, list[dict[str, object]]] = defaultdict(list)
    teacher_summary = bundles[0].manifest["teacher_packet_summary"]
    aggregate_metrics_by_bundle = {
        bundle.bundle_id: bundle.manifest.get("aggregate_metrics", {}) for bundle in bundles
    }

    for bundle in bundles:
        row_map, anchor_weight_rows, similarity_map = evaluate_bundle(
            bundle=bundle,
            delta_weight=args.delta_weight,
            anchor_logit_scale=args.anchor_logit_scale,
            csls_k=args.csls_k,
        )
        for comparison_name, rows in row_map.items():
            aggregated_rows[comparison_name].extend(rows)
            write_similarity_matrix(
                output_dir / f"similarity_{comparison_name}__{bundle.bundle_id}.csv",
                bundle.sample_ids,
                bundle.sample_ids,
                similarity_map[comparison_name],
            )
        for comparison_name, rows in anchor_weight_rows.items():
            aggregated_anchor_rows[comparison_name].extend(rows)

    summary_by_name = {
        comparison_name: summarize_rows(rows)
        for comparison_name, rows in sorted(aggregated_rows.items())
    }
    diagnostics_by_name = {
        comparison_name: summarize_anchor_weight_rows(rows)
        for comparison_name, rows in sorted(aggregated_anchor_rows.items())
    }

    for comparison_name, rows in sorted(aggregated_rows.items()):
        write_csv(output_dir / f"{comparison_name}_rows.csv", list(rows[0].keys()), rows)
    for comparison_name, rows in sorted(aggregated_anchor_rows.items()):
        write_csv(output_dir / f"anchor_weights_{comparison_name}.csv", list(rows[0].keys()), rows)

    report_text = build_markdown_report(
        summary_by_name=summary_by_name,
        diagnostics_by_name=diagnostics_by_name,
        teacher_packet_summary=teacher_summary,
        bundle_dirs=bundle_dirs,
        delta_weight=args.delta_weight,
        anchor_logit_scale=args.anchor_logit_scale,
        csls_k=args.csls_k,
    )
    (output_dir / "report.md").write_text(report_text, encoding="utf-8")

    summary = {
        "mode": args.mode,
        "bundle_dirs": [str(bundle_dir) for bundle_dir in bundle_dirs],
        "output_dir": str(output_dir),
        "delta_weight": args.delta_weight,
        "anchor_logit_scale": args.anchor_logit_scale,
        "csls_k": args.csls_k,
        "bundle_count": len(bundles),
        "frame_count_per_bundle": len(reference_ids),
        "teacher_packet_summary": teacher_summary,
        "aggregate_metrics_by_bundle": aggregate_metrics_by_bundle,
        "consumer_metrics": summary_by_name,
        "diagnostics": diagnostics_by_name,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Wrote querybank teacher-anchor packet evaluation to {output_dir}")


if __name__ == "__main__":
    main()
