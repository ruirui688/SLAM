#!/usr/bin/env python3
"""Build a Git-tracked paper evidence digest from ignored experiment outputs."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
EVIDENCE_DIR = ROOT / "paper" / "evidence"


PROTOCOLS = [
    {
        "key": "same_day_aisle",
        "name": "Same-day Aisle",
        "role": "Primary Aisle ladder",
        "summary": OUTPUTS / "same_day_richer__recomputed_summary.json",
        "selection": OUTPUTS / "same_day_richer__recomputed_selection_v5.json",
        "subset": OUTPUTS / "same_day_richer__recomputed_subset.json",
    },
    {
        "key": "cross_day_aisle",
        "name": "Cross-day Aisle",
        "role": "Primary Aisle ladder",
        "summary": OUTPUTS / "cross_day_richer__recomputed_summary.json",
        "selection": OUTPUTS / "cross_day_richer__recomputed_selection_v5.json",
        "subset": OUTPUTS / "cross_day_richer__recomputed_subset.json",
    },
    {
        "key": "cross_month_aisle",
        "name": "Cross-month Aisle",
        "role": "Primary Aisle ladder",
        "summary": OUTPUTS / "cross_month_richer__recomputed_summary.json",
        "selection": OUTPUTS / "cross_month_richer__recomputed_selection_v5.json",
        "subset": OUTPUTS / "cross_month_richer__recomputed_subset.json",
    },
    {
        "key": "hallway_broader_validation",
        "name": "Hallway broader validation",
        "role": "Secondary scene-transfer validation",
        "summary": OUTPUTS / "torwic_hallway_protocol_current_summary_v1.json",
        "selection": OUTPUTS / "torwic_hallway_protocol_current_selection_v5.json",
        "subset": OUTPUTS / "torwic_hallway_protocol_current_subset.json",
    },
]

BACKEND_METRICS = [
    {
        "key": "p132_p133_8_frame_smoke",
        "name": "P132/P133 8-frame DROID-SLAM smoke",
        "path": OUTPUTS / "dynamic_slam_backend_smoke_p132" / "p132_p133_raw_vs_masked_metrics.json",
    },
    {
        "key": "p134_64_frame_global_ba",
        "name": "P134 64-frame DROID-SLAM global BA",
        "path": OUTPUTS
        / "dynamic_slam_backend_smoke_p134_64_global_ba"
        / "p134_64_frame_global_ba_metrics.json",
    },
    {
        "key": "p135_semantic_masks",
        "name": "P135 existing semantic masks",
        "path": OUTPUTS
        / "dynamic_slam_backend_smoke_p135_64_semantic_masks_global_ba"
        / "p135_semantic_mask_metrics.json",
    },
    {
        "key": "p136_temporal_mask_stress",
        "name": "P136 temporal mask stress test",
        "path": OUTPUTS
        / "dynamic_slam_backend_smoke_p136_64_temporal_mask_stress_global_ba"
        / "p136_temporal_mask_stress_metrics.json",
    },
    {
        "key": "p137_flow_mask_stress",
        "name": "P137 optical-flow mask stress test",
        "path": OUTPUTS
        / "dynamic_slam_backend_smoke_p137_64_flow_mask_stress_global_ba"
        / "p137_flow_mask_stress_metrics.json",
    },
    {
        "key": "p138_first8_real_masks",
        "name": "P138 first-eight real semantic masks",
        "path": OUTPUTS
        / "dynamic_slam_backend_smoke_p138_64_first8_real_masks_global_ba"
        / "p138_first8_real_mask_metrics.json",
    },
    {
        "key": "p139_first16_real_masks",
        "name": "P139 first-sixteen real semantic masks",
        "path": OUTPUTS
        / "dynamic_slam_backend_smoke_p139_64_first16_real_masks_global_ba"
        / "p139_first16_real_mask_metrics.json",
    },
    {
        "key": "p140_first32_real_masks",
        "name": "P140 first-thirty-two real semantic masks",
        "path": OUTPUTS
        / "dynamic_slam_backend_smoke_p140_64_first32_real_masks_global_ba"
        / "p140_first32_real_mask_metrics.json",
    },
]


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def label_counts(items: list[dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for item in items:
        counts[item["canonical_label"]] += 1
    return counts


def reason_counts(items: list[dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for item in items:
        for reason in item.get("reject_reasons", []):
            counts[reason] += 1
    return counts


def row_for_protocol(protocol: dict[str, Any]) -> dict[str, Any]:
    summary = read_json(protocol["summary"])
    selection = read_json(protocol["selection"])
    selected = selection["selected"]
    rejected = selection["rejected"]
    dynamic_rejected = sum(
        1 for item in rejected if "dynamic_contamination" in item.get("reject_reasons", [])
    )
    return {
        "key": protocol["key"],
        "name": protocol["name"],
        "role": protocol["role"],
        "sessions": summary["num_inputs"],
        "frame_level_objects": summary["num_frame_level_objects"],
        "cross_session_clusters": summary["num_cross_session_clusters"],
        "retained_stable_objects": len(selected),
        "rejected_clusters": len(rejected),
        "dynamic_rejected_clusters": dynamic_rejected,
        "retained_labels": dict(label_counts(selected)),
        "rejected_labels": dict(label_counts(rejected)),
        "rejection_reasons": dict(reason_counts(rejected)),
        "criteria": selection["criteria"],
        "source_summary": str(protocol["summary"].relative_to(ROOT)),
        "source_selection": str(protocol["selection"].relative_to(ROOT)),
        "source_subset": str(protocol["subset"].relative_to(ROOT)),
    }


def write_csv(rows: list[dict[str, Any]]) -> None:
    path = EVIDENCE_DIR / "protocol_summary.csv"
    fields = [
        "name",
        "role",
        "sessions",
        "frame_level_objects",
        "cross_session_clusters",
        "retained_stable_objects",
        "rejected_clusters",
        "dynamic_rejected_clusters",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in fields})


def normalize_backend_metrics(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
    metrics = payload.get("metrics", {})
    raw = metrics.get("raw") or metrics.get("raw RGB")
    masked = (
        metrics.get("masked")
        or metrics.get("semantic_masked")
        or metrics.get("semantic masked RGB")
        or metrics.get("temporal propagated masked RGB")
        or metrics.get("flow propagated masked RGB")
        or metrics.get("first-eight real masked RGB")
        or metrics.get("first-sixteen real masked RGB")
        or metrics.get("first-thirty-two real masked RGB")
        or next((value for key, value in metrics.items() if key != "raw RGB" and key != "raw"), None)
    )
    return raw or {}, masked


def backend_row_for_metric(metric: dict[str, Any]) -> dict[str, Any] | None:
    path = metric["path"]
    if not path.exists():
        return None
    payload = read_json(path)
    raw, masked = normalize_backend_metrics(payload)
    coverage = payload.get("mask_coverage", {})
    delta = payload.get("delta_masked_minus_raw") or payload.get("metrics", {}).get("delta_masked_minus_raw", {})
    return {
        "key": metric["key"],
        "name": metric["name"],
        "source": str(path.relative_to(ROOT)),
        "scope": payload.get("scope", ""),
        "raw_ape_rmse_m": raw.get("ape_rmse_m"),
        "raw_rpe_rmse_m": raw.get("rpe_rmse_m"),
        "masked_ape_rmse_m": masked.get("ape_rmse_m") if masked else None,
        "masked_rpe_rmse_m": masked.get("rpe_rmse_m") if masked else None,
        "delta_ape_rmse_m": delta.get("ape_rmse_m"),
        "delta_rpe_rmse_m": delta.get("rpe_rmse_m"),
        "masked_frames": coverage.get("masked_frame_count"),
        "total_frames": coverage.get("total_frames"),
        "mean_mask_coverage_percent": coverage.get("mean_coverage_percent")
        or coverage.get("mean_coverage_over_64_frames_percent"),
        "claim_boundary": payload.get("claim_boundary", ""),
        "interpretation": payload.get("interpretation", ""),
    }


def write_backend_metrics(rows: list[dict[str, Any]]) -> None:
    json_path = EVIDENCE_DIR / "dynamic_slam_backend_metrics.json"
    csv_path = EVIDENCE_DIR / "dynamic_slam_backend_metrics.csv"
    json_path.write_text(json.dumps({"backend_metrics": rows}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    fields = [
        "name",
        "raw_ape_rmse_m",
        "masked_ape_rmse_m",
        "delta_ape_rmse_m",
        "raw_rpe_rmse_m",
        "masked_rpe_rmse_m",
        "delta_rpe_rmse_m",
        "masked_frames",
        "total_frames",
        "mean_mask_coverage_percent",
        "source",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def write_cluster_csv(rows: list[dict[str, Any]], selected: bool) -> None:
    path = EVIDENCE_DIR / ("retained_clusters.csv" if selected else "rejected_clusters.csv")
    fields = [
        "protocol",
        "cluster_id",
        "canonical_label",
        "support_count",
        "session_count",
        "frame_count",
        "dynamic_ratio",
        "label_purity",
        "reject_reasons",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for protocol in PROTOCOLS:
            selection = read_json(protocol["selection"])
            clusters = selection["selected" if selected else "rejected"]
            for cluster in clusters:
                writer.writerow(
                    {
                        "protocol": protocol["name"],
                        "cluster_id": cluster["cluster_id"],
                        "canonical_label": cluster["canonical_label"],
                        "support_count": cluster["support_count"],
                        "session_count": cluster["session_count"],
                        "frame_count": cluster["frame_count"],
                        "dynamic_ratio": f"{cluster['dynamic_ratio']:.3f}",
                        "label_purity": f"{cluster['label_purity']:.3f}",
                        "reject_reasons": ";".join(cluster.get("reject_reasons", [])),
                    }
                )


def markdown_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Protocol | Role | Sessions | Frame objects | Clusters | Retained | Rejected | Dynamic rejected |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {name} | {role} | {sessions} | {frame_level_objects} | "
            "{cross_session_clusters} | {retained_stable_objects} | "
            "{rejected_clusters} | {dynamic_rejected_clusters} |".format(**row)
        )
    return "\n".join(lines)


def write_readme(rows: list[dict[str, Any]], backend_rows: list[dict[str, Any]]) -> None:
    aggregate_reasons: Counter[str] = Counter()
    for row in rows:
        aggregate_reasons.update(row["rejection_reasons"])

    lines = [
        "# Paper Evidence Pack",
        "",
        "This directory is the Git-tracked digest of the current TorWIC evidence.",
        "It is regenerated from ignored experiment outputs under `outputs/` so the",
        "paper tables remain auditable without committing raw data, model outputs,",
        "videos, point clouds, or full generated output directories.",
        "",
        "Regenerate from the repository root:",
        "",
        "```bash",
        "make evidence-pack",
        "```",
        "",
        "## Protocol Summary",
        "",
        markdown_table(rows),
        "",
        "## Rejection Reason Totals",
        "",
        "| Reason | Count |",
        "|---|---:|",
    ]
    for reason, count in sorted(aggregate_reasons.items()):
        lines.append(f"| `{reason}` | {count} |")
    if backend_rows:
        lines.extend(
            [
                "",
                "## Dynamic SLAM Backend Metrics",
                "",
                "| Experiment | Raw APE | Masked APE | Raw RPE | Masked RPE | Mask coverage |",
                "|---|---:|---:|---:|---:|---:|",
            ]
        )
        for row in backend_rows:
            coverage = ""
            if row.get("masked_frames") is not None and row.get("total_frames") is not None:
                coverage = f"{row['masked_frames']}/{row['total_frames']}"
            if row.get("mean_mask_coverage_percent") is not None:
                coverage = f"{coverage} ({row['mean_mask_coverage_percent']:.6f}%)" if coverage else f"{row['mean_mask_coverage_percent']:.6f}%"
            lines.append(
                f"| {row['name']} | {row.get('raw_ape_rmse_m', '')} | "
                f"{row.get('masked_ape_rmse_m', '')} | {row.get('raw_rpe_rmse_m', '')} | "
                f"{row.get('masked_rpe_rmse_m', '')} | {coverage} |"
            )
    lines.extend(
        [
            "",
            "## Tracked Files",
            "",
            "- `protocol_summary.csv`: compact table for paper/result table reuse.",
            "- `retained_clusters.csv`: retained cluster-level traceability.",
            "- `rejected_clusters.csv`: rejected cluster-level traceability.",
            "- `evidence_summary.json`: full digest with source artifact paths.",
            "- `dynamic_slam_backend_metrics.csv`: compact APE/RPE backend table.",
            "- `dynamic_slam_backend_metrics.json`: full backend metric digest.",
            "",
            "## Source Artifact Policy",
            "",
            "The source JSON and markdown artifacts remain under ignored `outputs/` paths.",
            "This pack records their relative paths in `evidence_summary.json` and should",
            "be refreshed whenever the underlying protocol outputs change.",
            "",
        ]
    )
    (EVIDENCE_DIR / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    rows = [row_for_protocol(protocol) for protocol in PROTOCOLS]
    backend_rows = [row for metric in BACKEND_METRICS if (row := backend_row_for_metric(metric)) is not None]
    write_csv(rows)
    write_cluster_csv(rows, selected=True)
    write_cluster_csv(rows, selected=False)
    write_backend_metrics(backend_rows)
    (EVIDENCE_DIR / "evidence_summary.json").write_text(
        json.dumps({"protocols": rows}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_readme(rows, backend_rows)
    print(f"Wrote evidence pack to {EVIDENCE_DIR}")


if __name__ == "__main__":
    main()
