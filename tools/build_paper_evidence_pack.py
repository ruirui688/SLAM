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


def write_readme(rows: list[dict[str, Any]]) -> None:
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
    lines.extend(
        [
            "",
            "## Tracked Files",
            "",
            "- `protocol_summary.csv`: compact table for paper/result table reuse.",
            "- `retained_clusters.csv`: retained cluster-level traceability.",
            "- `rejected_clusters.csv`: rejected cluster-level traceability.",
            "- `evidence_summary.json`: full digest with source artifact paths.",
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
    write_csv(rows)
    write_cluster_csv(rows, selected=True)
    write_cluster_csv(rows, selected=False)
    (EVIDENCE_DIR / "evidence_summary.json").write_text(
        json.dumps({"protocols": rows}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_readme(rows)
    print(f"Wrote evidence pack to {EVIDENCE_DIR}")


if __name__ == "__main__":
    main()
