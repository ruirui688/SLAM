#!/usr/bin/env python3
"""Build the P199 no-human-label semantic-stability auxiliary dataset.

P199 is deliberately not an admission-control dataset.  It reuses P193
observation rows for geometry/provenance only, ignores P193 ``target_admit``,
and derives a weak auxiliary semantic/static-vs-dynamic target from TorWIC/P197
semantic categories.  Ambiguous semantic hints are kept in the CSV for audit
but excluded from the default training subset.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

STATIC_LIKE_CATEGORIES = {
    "wall_fence_pillar",
    "rack_shelf",
    "fixed_machinery",
    "misc_static_feature",
    "ceiling",
}
DYNAMIC_OR_NON_STATIC_LIKE_CATEGORIES = {
    "fork_truck",
    "person",
    "cart_pallet_jack",
    "pylon_cone",
    "misc_dynamic_feature",
    "misc_non_static_feature",
}

CANONICAL_TO_SEMANTIC_CATEGORIES = {
    "forklift": ["fork_truck"],
    "fork": ["fork_truck"],
    "rack forklift": ["fork_truck", "rack_shelf"],
    "warehouse rack": ["rack_shelf"],
    "rack": ["rack_shelf"],
    "barrier": ["misc_static_feature", "pylon_cone"],
    "work table": ["misc_static_feature", "fixed_machinery"],
    "work": ["misc_static_feature", "fixed_machinery"],
}

OUTPUT_COLUMNS = [
    "p199_sample_id",
    "p193_sample_id",
    "source",
    "split",
    "cluster_id",
    "canonical_label",
    "resolved_label",
    "observation_id",
    "session_id",
    "frame_id",
    "frame_index",
    "tracklet_id",
    "physical_key",
    "semantic_stability_target",
    "semantic_static_like",
    "semantic_target_status",
    "semantic_target_source",
    "semantic_categories",
    "semantic_hint",
    "semantic_evidence_status",
    "source_semantic_path",
    "label_source",
    "mean_center_x",
    "mean_center_y",
    "mean_size_x",
    "mean_size_y",
    "support_count",
    "mask_area_px",
    "bbox_width",
    "bbox_height",
    "semantic_gate_score",
    "observation_index_path",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def norm_label(value: Any) -> str:
    text = str(value or "").strip().lower().replace("_", " ").replace("-", " ")
    return re.sub(r"\s+", " ", text)


def split_categories(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def semantic_class(categories: list[str]) -> tuple[str, str, int | None]:
    has_static = any(category in STATIC_LIKE_CATEGORIES for category in categories)
    has_dynamic = any(category in DYNAMIC_OR_NON_STATIC_LIKE_CATEGORIES for category in categories)
    if has_static and not has_dynamic:
        return "static_like", "non_ambiguous", 1
    if has_dynamic and not has_static:
        return "dynamic_or_non_static_like", "non_ambiguous", 0
    if has_static and has_dynamic:
        return "ambiguous_static_and_dynamic", "ambiguous", None
    return "unknown", "unknown", None


def p197_index(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("sample_id", ""): row for row in rows if row.get("sample_id")}


def count_by(rows: list[dict[str, Any]], *keys: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        label = "|".join(str(row.get(key, "")) for key in keys)
        counts[label] += 1
    return dict(sorted(counts.items()))


def blank_audit(rows: list[dict[str, str]], columns: list[str]) -> dict[str, dict[str, int]]:
    audit: dict[str, dict[str, int]] = {}
    for column in columns:
        counts = Counter("blank" if str(row.get(column, "")).strip() == "" else "nonblank" for row in rows)
        audit[column] = {"blank": counts["blank"], "nonblank": counts["nonblank"]}
    return audit


def build_rows(p193_rows: list[dict[str, str]], p197_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    semantic_by_sample = p197_index(p197_rows)
    out: list[dict[str, Any]] = []
    for idx, row in enumerate(p193_rows, start=1):
        sample_id = row["sample_id"]
        review = semantic_by_sample.get(sample_id, {})
        canonical = norm_label(row.get("canonical_label"))
        categories = split_categories(review.get("semantic_hint_categories", ""))
        target_source = "p197_semantic_hint_categories"
        if not categories:
            categories = CANONICAL_TO_SEMANTIC_CATEGORIES.get(canonical, [])
            target_source = "canonical_label_to_p197_ontology_mapping"
        semantic_target, status, static_like = semantic_class(categories)
        out.append(
            {
                "p199_sample_id": f"p199_semantic_{idx:05d}",
                "p193_sample_id": sample_id,
                "source": row.get("source", ""),
                "split": row.get("split", ""),
                "cluster_id": row.get("cluster_id", ""),
                "canonical_label": row.get("canonical_label", ""),
                "resolved_label": row.get("resolved_label", ""),
                "observation_id": row.get("observation_id", ""),
                "session_id": row.get("session_id", ""),
                "frame_id": row.get("frame_id", ""),
                "frame_index": row.get("frame_index", ""),
                "tracklet_id": row.get("tracklet_id", ""),
                "physical_key": row.get("physical_key", ""),
                "semantic_stability_target": semantic_target,
                "semantic_static_like": "" if static_like is None else static_like,
                "semantic_target_status": status,
                "semantic_target_source": target_source,
                "semantic_categories": ";".join(categories),
                "semantic_hint": review.get("semantic_hint", ""),
                "semantic_evidence_status": review.get("semantic_evidence_status", ""),
                "source_semantic_path": review.get("source_semantic_path", ""),
                "label_source": "p199_auxiliary_semantic_category_static_dynamic_not_admission",
                "mean_center_x": row.get("mean_center_x", ""),
                "mean_center_y": row.get("mean_center_y", ""),
                "mean_size_x": row.get("mean_size_x", ""),
                "mean_size_y": row.get("mean_size_y", ""),
                "support_count": row.get("support_count", ""),
                "mask_area_px": row.get("mask_area_px", ""),
                "bbox_width": row.get("bbox_width", ""),
                "bbox_height": row.get("bbox_height", ""),
                "semantic_gate_score": row.get("semantic_gate_score", ""),
                "observation_index_path": row.get("observation_index_path", ""),
            }
        )
    return out


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    counts = payload["counts"]
    lines = [
        "# P199 Semantic-Stability Auxiliary Dataset",
        "",
        f"**Status:** {payload['status']}",
        "",
        "## Scientific Boundary",
        "",
        payload["scientific_boundary"],
        "",
        "## Dataset Counts",
        "",
        f"- Total rows: {counts['total_rows']}",
        f"- Non-ambiguous training-eligible rows: {counts['non_ambiguous_rows']}",
        f"- Ambiguous rows kept for audit, excluded from default training: {counts['ambiguous_rows']}",
        f"- Unknown rows: {counts['unknown_rows']}",
        f"- Target counts: `{counts['by_semantic_stability_target']}`",
        f"- Split/target counts: `{counts['by_split_and_target']}`",
        f"- Category counts: `{counts['by_canonical_label']}`",
        "",
        "## Label Policy",
        "",
        "- No `human_admit_label` or `human_same_object_label` values are created.",
        "- P193 `target_admit`, `current_weak_label`, `selection_v5`, and model predictions are not used as P199 targets.",
        "- The binary field `semantic_static_like` means static-like semantic category versus dynamic/non-static-like semantic category. It is not an admit/reject label.",
        "- Barrier rows are marked ambiguous because their P197 ontology hint contains both `misc_static_feature` and `pylon_cone`.",
        "",
        "## Outputs",
        "",
        f"- CSV: `{payload['outputs']['csv']}`",
        f"- JSON: `{payload['outputs']['json']}`",
        "",
        f"**Recommendation:** {payload['recommendation']}",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--p193-csv", default="paper/evidence/admission_frame_dataset_p193.csv")
    parser.add_argument("--p197-boundary-csv", default="paper/evidence/admission_boundary_label_sheet_p197_semantic_review.csv")
    parser.add_argument("--output-csv", default="paper/evidence/semantic_stability_dataset_p199.csv")
    parser.add_argument("--output-json", default="paper/evidence/semantic_stability_dataset_p199.json")
    parser.add_argument("--output-md", default="paper/export/semantic_stability_dataset_p199.md")
    args = parser.parse_args()

    p193_path = ROOT / args.p193_csv
    p197_path = ROOT / args.p197_boundary_csv
    p193_rows = read_csv(p193_path)
    p197_rows = read_csv(p197_path)
    rows = build_rows(p193_rows, p197_rows)

    non_ambiguous = [row for row in rows if row["semantic_target_status"] == "non_ambiguous"]
    ambiguous = [row for row in rows if row["semantic_target_status"] == "ambiguous"]
    unknown = [row for row in rows if row["semantic_target_status"] == "unknown"]

    split_target: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in non_ambiguous:
        split_target[row["split"]][row["semantic_stability_target"]] += 1

    payload: dict[str, Any] = {
        "phase": "P199-no-human-semantic-stability-auxiliary-dataset",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "BUILT",
        "scientific_boundary": (
            "P199 is a no-human-label auxiliary semantic stability dataset. It can support "
            "semantic/static-vs-dynamic prior experiments, but it does not replace independent "
            "admission labels, does not unblock P195, and does not justify learned admission-control claims."
        ),
        "inputs": {
            "p193_csv": args.p193_csv,
            "p197_boundary_csv": args.p197_boundary_csv,
        },
        "outputs": {
            "csv": args.output_csv,
            "json": args.output_json,
            "md": args.output_md,
        },
        "target_definition": {
            "field": "semantic_static_like",
            "positive_class": "static_like semantic category",
            "negative_class": "dynamic_or_non_static_like semantic category",
            "excluded_default_training_statuses": ["ambiguous", "unknown"],
            "not_admission_control": True,
        },
        "constraints_observed": {
            "human_admit_label_filled": False,
            "human_same_object_label_filled": False,
            "p193_target_admit_used_as_target": False,
            "selection_v5_or_current_weak_label_used_as_target": False,
            "model_prediction_used_as_target": False,
            "downloads_performed": False,
        },
        "semantic_hint_sets": {
            "static_like": sorted(STATIC_LIKE_CATEGORIES),
            "dynamic_or_non_static_like": sorted(DYNAMIC_OR_NON_STATIC_LIKE_CATEGORIES),
            "canonical_mapping": CANONICAL_TO_SEMANTIC_CATEGORIES,
        },
        "counts": {
            "total_rows": len(rows),
            "non_ambiguous_rows": len(non_ambiguous),
            "ambiguous_rows": len(ambiguous),
            "unknown_rows": len(unknown),
            "by_semantic_stability_target": count_by(rows, "semantic_stability_target"),
            "by_split_and_target": {split: dict(sorted(targets.items())) for split, targets in sorted(split_target.items())},
            "by_canonical_label": count_by(rows, "canonical_label"),
            "by_target_source": count_by(rows, "semantic_target_source"),
            "by_semantic_evidence_status": count_by(rows, "semantic_evidence_status"),
        },
        "human_label_audit": blank_audit(
            p197_rows,
            ["human_admit_label", "human_label_confidence", "human_notes"],
        ),
        "recommendation": (
            "Use the non-ambiguous subset only for a bounded semantic/static-dynamic smoke. "
            "Keep P195 blocked until real human admission and same-object labels exist."
        ),
    }

    write_csv(ROOT / args.output_csv, rows, OUTPUT_COLUMNS)
    write_json(ROOT / args.output_json, payload)
    write_markdown(ROOT / args.output_md, payload)
    print(json.dumps({"outputs": payload["outputs"], "counts": payload["counts"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
