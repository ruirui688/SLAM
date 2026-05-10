#!/usr/bin/env python3
"""Build and triage the P206 diversity-first no-label raw evidence packet."""
from __future__ import annotations

import argparse
import csv
import json
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from triage_raw_evidence_packet_p205 import (
    TRIAGE_CSV_COLUMNS,
    check_prohibited_columns,
    duplicate_map,
    load_image_tools,
    summarize as summarize_triage,
    triage_rows,
)


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_INDEX_CSV = ROOT / "paper/evidence/raw_segmentation_evidence_index_p203.csv"
DEFAULT_INDEX_JSON = ROOT / "paper/evidence/raw_segmentation_evidence_index_p203.json"
DEFAULT_PACKET_JSON = ROOT / "paper/evidence/raw_evidence_diverse_packet_p206.json"
DEFAULT_PACKET_CSV = ROOT / "paper/evidence/raw_evidence_diverse_packet_p206.csv"
DEFAULT_PACKET_MD = ROOT / "paper/export/raw_evidence_diverse_packet_p206.md"
DEFAULT_TRIAGE_JSON = ROOT / "paper/evidence/raw_evidence_diverse_packet_triage_p206.json"
DEFAULT_TRIAGE_CSV = ROOT / "paper/evidence/raw_evidence_diverse_packet_triage_p206.csv"
DEFAULT_TRIAGE_MD = ROOT / "paper/export/raw_evidence_diverse_packet_triage_p206.md"
DEFAULT_MAX_SAMPLES = 32

PATH_COLUMNS = [
    "raw_segmentation_color_left_path",
    "raw_segmentation_greyscale_left_path",
    "raw_segmentation_color_right_path",
    "raw_segmentation_greyscale_right_path",
    "raw_rgb_left_path",
    "raw_depth_left_path",
]

PACKET_COLUMNS = [
    "audit_sample_id",
    "p203_index_row_id",
    "p202_audit_row_id",
    "row_source",
    "row_role",
    "sample_id",
    "observation_id",
    "canonical_label",
    "source",
    "session_id",
    "frame_index",
    "tracklet_id",
    "physical_key",
    "raw_segmentation_color_left_path",
    "raw_segmentation_greyscale_left_path",
    "raw_segmentation_color_right_path",
    "raw_segmentation_greyscale_right_path",
    "raw_rgb_left_path",
    "raw_depth_left_path",
    "why_sampled",
    "diversity_constraints",
    "no_label_inspection_note",
    "raw_evidence_issue_note",
]

PROHIBITED_COLUMNS = {
    "human_admit_label",
    "human_same_object_label",
    "target_admit",
    "current_weak_label",
    "selection_v5",
    "model_prediction",
    "model_probability",
    "weak_label",
    "weak_label_a",
    "weak_label_b",
    "model_probability_a",
    "model_probability_b",
}

TARGET_CATEGORIES = ["forklift", "barrier", "work table", "warehouse rack"]
TARGET_SOURCES = ["same_day", "cross_day", "cross_month", "hallway"]
TARGET_ROW_SOURCES = ["p193", "p197_boundary", "p197_pair", "p199"]


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def repo_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


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


def evidence_exists(value: str) -> bool:
    if not value:
        return False
    if "::" in value:
        zip_part, member = value.split("::", 1)
        try:
            with zipfile.ZipFile(repo_path(zip_part)) as archive:
                return member in archive.namelist()
        except Exception:
            return False
    return repo_path(value).exists()


def stable_index(row: dict[str, str]) -> int:
    value = row.get("index_row_id", "")
    try:
        return int(value.rsplit("_", 1)[1])
    except (IndexError, ValueError):
        return 10**9


def coverage_tokens(row: dict[str, str]) -> set[str]:
    category = row.get("canonical_label", "")
    source = row.get("source", "")
    row_source = row.get("row_source", "")
    session = row.get("session_id", "")
    return {
        f"category:{category}",
        f"source:{source}",
        f"row_source:{row_source}",
        f"category_source:{category}|{source}",
        f"category_row_source:{category}|{row_source}",
        f"source_row_source:{source}|{row_source}",
        f"session:{session}",
    }


def build_universe(rows: list[dict[str, str]]) -> set[str]:
    universe: set[str] = set()
    for row in rows:
        if row.get("canonical_label") in TARGET_CATEGORIES:
            universe.add(f"category:{row['canonical_label']}")
        if row.get("source") in TARGET_SOURCES:
            universe.add(f"source:{row['source']}")
        if row.get("row_source") in TARGET_ROW_SOURCES:
            universe.add(f"row_source:{row['row_source']}")
        if row.get("canonical_label") in TARGET_CATEGORIES and row.get("source") in TARGET_SOURCES:
            universe.add(f"category_source:{row['canonical_label']}|{row['source']}")
        if row.get("canonical_label") in TARGET_CATEGORIES and row.get("row_source") in TARGET_ROW_SOURCES:
            universe.add(f"category_row_source:{row['canonical_label']}|{row['row_source']}")
        if row.get("source") in TARGET_SOURCES and row.get("row_source") in TARGET_ROW_SOURCES:
            universe.add(f"source_row_source:{row['source']}|{row['row_source']}")
        if row.get("session_id"):
            universe.add(f"session:{row['session_id']}")
    return universe


def row_sort_key(row: dict[str, str]) -> tuple[str, str, str, str, str, int]:
    return (
        row.get("row_source", ""),
        row.get("canonical_label", ""),
        row.get("source", ""),
        row.get("session_id", ""),
        row.get("frame_index", ""),
        stable_index(row),
    )


def select_rows(rows: list[dict[str, str]], max_samples: int) -> tuple[list[dict[str, str]], dict[str, Any]]:
    candidates = sorted(rows, key=row_sort_key)
    universe = build_universe(candidates)
    uncovered = set(universe)
    selected: list[dict[str, str]] = []
    used_index_rows: set[str] = set()
    used_sample_ids: set[str] = set()
    used_session_frames: set[tuple[str, str]] = set()
    used_physical_keys: set[str] = set()

    def can_use(row: dict[str, str], strict: bool) -> bool:
        if row.get("index_row_id", "") in used_index_rows:
            return False
        if not strict:
            return True
        if row.get("sample_id", "") in used_sample_ids:
            return False
        if (row.get("session_id", ""), row.get("frame_index", "")) in used_session_frames:
            return False
        physical_key = row.get("physical_key", "")
        return not (physical_key and physical_key in used_physical_keys)

    while len(selected) < max_samples:
        best: dict[str, str] | None = None
        best_score: tuple[int, int, int, int, int, int, int, int] | None = None
        for row in candidates:
            if not can_use(row, strict=True):
                continue
            tokens = coverage_tokens(row)
            gain = len(tokens & uncovered)
            category_count = sum(item.get("canonical_label") == row.get("canonical_label") for item in selected)
            source_count = sum(item.get("source") == row.get("source") for item in selected)
            row_source_count = sum(item.get("row_source") == row.get("row_source") for item in selected)
            primary_gain = sum(
                1
                for token in [
                    f"category:{row.get('canonical_label', '')}",
                    f"source:{row.get('source', '')}",
                    f"row_source:{row.get('row_source', '')}",
                ]
                if token in uncovered
            )
            score = (
                gain * 10 + primary_gain * 20,
                -max(category_count, source_count, row_source_count),
                -category_count,
                -source_count,
                -row_source_count,
                1 if row.get("physical_key") else 0,
                -stable_index(row),
                -len(selected),
            )
            if best_score is None or score > best_score:
                best = row
                best_score = score
        if best is None:
            break
        selected.append(best)
        used_index_rows.add(best.get("index_row_id", ""))
        used_sample_ids.add(best.get("sample_id", ""))
        used_session_frames.add((best.get("session_id", ""), best.get("frame_index", "")))
        if best.get("physical_key"):
            used_physical_keys.add(best["physical_key"])
        uncovered -= coverage_tokens(best)

    if len(selected) < max_samples:
        for row in candidates:
            if len(selected) >= max_samples:
                break
            if not can_use(row, strict=False):
                continue
            selected.append(row)
            used_index_rows.add(row.get("index_row_id", ""))

    selected = sorted(selected, key=stable_index)
    sample_counts = Counter(row.get("sample_id", "") for row in selected if row.get("sample_id"))
    frame_counts = Counter((row.get("session_id", ""), row.get("frame_index", "")) for row in selected)
    physical_counts = Counter(row.get("physical_key", "") for row in selected if row.get("physical_key"))
    return selected, {
        "universe_tokens": len(universe),
        "covered_tokens": len(universe - uncovered),
        "uncovered_tokens": sorted(uncovered),
        "strict_unique_selection_completed": len(selected) == max_samples,
        "duplicate_sample_id_groups": {k: v for k, v in sorted(sample_counts.items()) if v > 1},
        "duplicate_session_frame_groups": {"|".join(k): v for k, v in sorted(frame_counts.items()) if v > 1},
        "duplicate_nonblank_physical_key_groups": {k: v for k, v in sorted(physical_counts.items()) if v > 1},
        "blank_physical_key_rows": sum(1 for row in selected if not row.get("physical_key")),
    }


def why_sampled(row: dict[str, str], coverage_seen: dict[str, set[str]]) -> str:
    reasons: list[str] = []
    fields = [
        ("category", row.get("canonical_label", "")),
        ("source", row.get("source", "")),
        ("row_source", row.get("row_source", "")),
        ("category/source", f"{row.get('canonical_label', '')}|{row.get('source', '')}"),
        ("category/row_source", f"{row.get('canonical_label', '')}|{row.get('row_source', '')}"),
        ("source/row_source", f"{row.get('source', '')}|{row.get('row_source', '')}"),
        ("session", row.get("session_id", "")),
    ]
    for key, value in fields:
        if value and value not in coverage_seen[key]:
            reasons.append(f"adds {key} coverage: {value}")
        coverage_seen[key].add(value)
    if not reasons:
        reasons.append("fills diversity cap while preserving unique sample/frame constraints")
    return "; ".join(reasons)


def compact_packet_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    coverage_seen: dict[str, set[str]] = defaultdict(set)
    out: list[dict[str, Any]] = []
    for ordinal, row in enumerate(rows, start=1):
        packet_row = {
            "audit_sample_id": f"p206_{ordinal:03d}",
            "p203_index_row_id": row.get("index_row_id", ""),
            "p202_audit_row_id": row.get("p202_audit_row_id", ""),
            "row_source": row.get("row_source", ""),
            "row_role": row.get("row_role", ""),
            "sample_id": row.get("sample_id", ""),
            "observation_id": row.get("observation_id", ""),
            "canonical_label": row.get("canonical_label", ""),
            "source": row.get("source", ""),
            "session_id": row.get("session_id", ""),
            "frame_index": row.get("frame_index", ""),
            "tracklet_id": row.get("tracklet_id", ""),
            "physical_key": row.get("physical_key", ""),
            "why_sampled": why_sampled(row, coverage_seen),
            "diversity_constraints": "unique_sample_id;unique_session_frame;unique_nonblank_physical_key",
            "no_label_inspection_note": "",
            "raw_evidence_issue_note": "",
        }
        for column in PATH_COLUMNS:
            packet_row[column] = row.get(column, "")
        out.append(packet_row)
    return out


def nested_counts(rows: list[dict[str, Any]], outer_key: str, inner_key: str) -> dict[str, dict[str, int]]:
    nested: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        nested[str(row.get(outer_key, ""))][str(row.get(inner_key, ""))] += 1
    return {outer: dict(sorted(counter.items())) for outer, counter in sorted(nested.items())}


def coverage_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "sample_count": len(rows),
        "category_counts": dict(sorted(Counter(row["canonical_label"] for row in rows).items())),
        "source_counts": dict(sorted(Counter(row["source"] for row in rows).items())),
        "row_source_counts": dict(sorted(Counter(row["row_source"] for row in rows).items())),
        "session_count": len({row["session_id"] for row in rows}),
        "sessions": sorted({row["session_id"] for row in rows}),
        "category_source_counts": nested_counts(rows, "canonical_label", "source"),
        "category_row_source_counts": nested_counts(rows, "canonical_label", "row_source"),
        "source_row_source_counts": nested_counts(rows, "source", "row_source"),
    }


def duplicate_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    physical_keys = [str(row.get("physical_key") or "") for row in rows if row.get("physical_key")]
    session_frame_pairs = [str((row.get("session_id", ""), row.get("frame_index", ""))) for row in rows]
    return {
        "rows_with_physical_key": len(physical_keys),
        "unique_physical_keys": len(set(physical_keys)),
        "duplicate_physical_keys": duplicate_map(rows, lambda row: row.get("physical_key", "")),
        "unique_session_frame_pairs": len(set(session_frame_pairs)),
        "duplicate_session_frame_pairs": duplicate_map(rows, lambda row: (row.get("session_id", ""), row.get("frame_index", ""))),
        "duplicate_sample_ids": duplicate_map(rows, lambda row: row.get("sample_id", "")),
    }


def validate_packet(rows: list[dict[str, Any]]) -> dict[str, Any]:
    missing: list[dict[str, str]] = []
    blank_note_ok = all(row.get("no_label_inspection_note", "") == "" for row in rows) and all(
        row.get("raw_evidence_issue_note", "") == "" for row in rows
    )
    total = 0
    for row in rows:
        for column in PATH_COLUMNS:
            value = str(row.get(column) or "")
            if not value:
                continue
            total += 1
            if not evidence_exists(value):
                missing.append(
                    {
                        "audit_sample_id": str(row.get("audit_sample_id", "")),
                        "path_column": column,
                        "path": value,
                    }
                )
    return {
        "rows": len(rows),
        "raw_evidence_paths_total": total,
        "raw_evidence_paths_existing": total - len(missing),
        "missing_count": len(missing),
        "all_paths_exist": not missing,
        "non_label_review_note_fields_blank": blank_note_ok,
        "missing": missing,
    }


def write_packet_markdown(path: Path, payload: dict[str, Any]) -> None:
    coverage = payload["coverage"]
    validation = payload["validation"]
    diversity = payload["diversity"]
    lines = [
        "# P206 Diverse Raw Evidence Packet",
        "",
        f"**Status:** {payload['status']}",
        "",
        "## Boundary",
        "",
        payload["scientific_boundary"],
        "",
        "## Coverage",
        "",
        f"- Samples: {coverage['sample_count']}",
        f"- Categories: {coverage['category_counts']}",
        f"- Sources: {coverage['source_counts']}",
        f"- Row sources: {coverage['row_source_counts']}",
        f"- Sessions: {coverage['session_count']}",
        f"- Raw evidence paths: {validation['raw_evidence_paths_existing']}/{validation['raw_evidence_paths_total']} existing",
        f"- Duplicate sample-id groups: {len(diversity['duplicate_sample_ids'])}",
        f"- Duplicate session/frame groups: {len(diversity['duplicate_session_frame_pairs'])}",
        f"- Duplicate nonblank physical-key groups: {len(diversity['duplicate_physical_keys'])}",
        "",
        "## Tradeoffs",
        "",
        f"- Uncovered secondary coverage tokens: {payload['sampling_policy']['selection_debug']['uncovered_tokens']}",
        "- Blank physical keys are unavoidable for P197 boundary and pair rows because those rows do not carry physical keys in the P203 index.",
        "",
        "## Label Gate",
        "",
        "- P195 remains `BLOCKED`.",
        "- Packet rows contain no human admission labels, no human same-object labels, no weak targets, and no model predictions.",
        "- Blank note columns are for raw-evidence quality comments only.",
        "",
        "## Sample Index",
        "",
        "| audit_sample_id | category | source | row_source | session | frame | why_sampled |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {audit_sample_id} | {canonical_label} | {source} | {row_source} | {session_id} | {frame_index} | {why_sampled} |".format(
                **{key: str(value).replace("|", "\\|") for key, value in row.items()}
            )
        )
    lines.extend(
        [
            "",
            "## P207 Recommendation",
            "",
            "Use the P206 packet as the preferred no-label raw-evidence audit set. Keep P195 blocked until independent human admission and same-object labels exist.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_triage_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    diversity = payload["diversity"]
    lines = [
        "# P206 Diverse Raw Evidence Packet Triage",
        "",
        f"**Status:** {payload['status']}",
        "",
        "## Boundary",
        "",
        payload["scientific_boundary"],
        "",
        "## Summary",
        "",
        f"- Samples triaged: {summary['sample_count']}",
        f"- Referenced paths: {summary['paths_existing']}/{summary['path_total']} existing",
        f"- Readable images: {summary['paths_readable_images']}/{summary['path_total']}",
        f"- Rows by issue level: {summary['rows_by_issue_level']}",
        f"- Issue counts: {summary['issue_counts']}",
        f"- Warning counts: {summary['warning_counts']}",
        f"- Dimension counts: {summary['dimension_counts']}",
        "",
        "## Diversity Flags",
        "",
        f"- Unique physical keys: {diversity['unique_physical_keys']}/{diversity['rows_with_physical_key']} nonblank rows",
        f"- Duplicate physical-key groups: {len(diversity['duplicate_physical_keys'])}",
        f"- Unique session/frame pairs: {diversity['unique_session_frame_pairs']}/{summary['sample_count']} rows",
        f"- Duplicate session/frame groups: {len(diversity['duplicate_session_frame_pairs'])}",
        f"- Duplicate sample-id groups: {len(diversity['duplicate_sample_ids'])}",
        "",
        "## Row Triage",
        "",
        "| sample | level | dimensions | issue_codes | warning_codes | depth_nonzero_pixels |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["triage_rows"]:
        lines.append(
            "| {audit_sample_id} | {issue_level} | {row_dimensions} | {issue_codes} | {warning_codes} | {depth_nonzero_pixel_count} |".format(
                **{key: str(value).replace("|", "\\|") for key, value in row.items()}
            )
        )
    lines.extend(
        [
            "",
            "## Label Gate",
            "",
            "- P195 remains `BLOCKED`.",
            "- Human admission and same-object label fields remain blank in the independent-supervision gate.",
            "- This triage records file/readability/shape/non-empty evidence issues only.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_packet(
    index_csv: Path,
    output_json: Path,
    output_csv: Path,
    output_md: Path,
    max_samples: int,
) -> dict[str, Any]:
    source_rows, source_columns = read_csv(index_csv)
    leaked_columns = sorted(set(source_columns) & PROHIBITED_COLUMNS)
    if leaked_columns:
        raise SystemExit(f"Refusing to build packet from prohibited columns: {', '.join(leaked_columns)}")
    if not source_rows:
        raise SystemExit(f"No rows found in {index_csv}")

    selected, selection_debug = select_rows(source_rows, max_samples)
    packet_rows = compact_packet_rows(selected)
    validation = validate_packet(packet_rows)
    diversity = duplicate_summary(packet_rows)
    payload = {
        "phase": "P206-diverse-raw-evidence-packet",
        "status": "DIVERSE_AUDIT_PACKET_BUILT_P195_STILL_BLOCKED",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scientific_boundary": (
            "No-label raw evidence inspection packet only. P206 improves packet diversity for local raw "
            "RGB/depth/segmentation evidence review. It does not create or infer admission/same-object labels, "
            "does not use weak targets/model predictions as labels, and does not train admission-control or "
            "semantic-stability models."
        ),
        "inputs": {"p203_index_csv": rel(index_csv)},
        "outputs": {"json": rel(output_json), "csv": rel(output_csv), "markdown": rel(output_md)},
        "constraints_observed": {
            "human_labels_created": False,
            "admission_or_same_object_labels_inferred": False,
            "weak_admission_or_model_predictions_used_as_labels": False,
            "admission_or_semantic_stability_training_performed": False,
            "downloads_performed": False,
            "raw_images_or_data_modified": False,
        },
        "sampling_policy": {
            "deterministic": True,
            "max_samples": max_samples,
            "priority_order": [
                "avoid duplicate sample_id",
                "avoid duplicate session_id+frame_index",
                "avoid duplicate nonblank physical_key",
                "cover required categories, sources, row sources, pairings, and sessions",
            ],
            "coverage_targets": {
                "canonical_label": TARGET_CATEGORIES,
                "source": TARGET_SOURCES,
                "row_source": TARGET_ROW_SOURCES,
                "additional": "observed category/source, category/row_source, source/row_source, and session coverage",
            },
            "selection_debug": selection_debug,
        },
        "coverage": coverage_summary(packet_rows),
        "diversity": diversity,
        "validation": validation,
        "p195_status": "BLOCKED",
        "rows": packet_rows,
    }
    write_json(output_json, payload)
    write_csv(output_csv, packet_rows, PACKET_COLUMNS)
    write_packet_markdown(output_md, payload)
    return payload


def build_triage(
    packet_payload: dict[str, Any],
    index_json: Path,
    output_json: Path,
    output_csv: Path,
    output_md: Path,
) -> dict[str, Any]:
    index_payload = json.loads(index_json.read_text(encoding="utf-8"))
    rows = packet_payload["rows"]
    index_rows = index_payload.get("rows", [])
    check_prohibited_columns(rows, "P206 packet")
    check_prohibited_columns(index_rows, "P203 index")

    Image, np, image_backend = load_image_tools()
    detail_rows, csv_rows = triage_rows(rows, Image, np)
    payload = {
        "phase": "P206-diverse-raw-evidence-packet-triage",
        "status": "DIVERSE_PACKET_TRIAGE_COMPLETE_P195_STILL_BLOCKED",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scientific_boundary": (
            "Raw evidence QA only. P206 validates local file existence, readability, image dimensions, "
            "segmentation non-triviality, depth readability/statistics, and packet diversity. It does not "
            "create or infer admission/same-object labels, does not use weak targets/model predictions as "
            "labels, and does not train admission-control or semantic-stability models."
        ),
        "inputs": {
            "p206_packet_json": packet_payload["outputs"]["json"],
            "p203_index_json": rel(index_json),
        },
        "outputs": {"json": rel(output_json), "csv": rel(output_csv), "markdown": rel(output_md)},
        "image_backend": image_backend,
        "constraints_observed": packet_payload["constraints_observed"],
        "p195_status": "BLOCKED",
        "summary": summarize_triage(csv_rows, rows),
        "diversity": duplicate_summary(rows),
        "triage_rows": detail_rows,
    }
    write_json(output_json, payload)
    write_csv(output_csv, csv_rows, TRIAGE_CSV_COLUMNS)
    write_triage_markdown(output_md, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and triage P206 diverse no-label raw evidence packet")
    parser.add_argument("--index-csv", default=str(DEFAULT_INDEX_CSV))
    parser.add_argument("--index-json", default=str(DEFAULT_INDEX_JSON))
    parser.add_argument("--packet-json", default=str(DEFAULT_PACKET_JSON))
    parser.add_argument("--packet-csv", default=str(DEFAULT_PACKET_CSV))
    parser.add_argument("--packet-md", default=str(DEFAULT_PACKET_MD))
    parser.add_argument("--triage-json", default=str(DEFAULT_TRIAGE_JSON))
    parser.add_argument("--triage-csv", default=str(DEFAULT_TRIAGE_CSV))
    parser.add_argument("--triage-md", default=str(DEFAULT_TRIAGE_MD))
    parser.add_argument("--max-samples", type=int, default=DEFAULT_MAX_SAMPLES)
    args = parser.parse_args()

    packet_payload = build_packet(
        repo_path(args.index_csv),
        repo_path(args.packet_json),
        repo_path(args.packet_csv),
        repo_path(args.packet_md),
        args.max_samples,
    )
    triage_payload = build_triage(
        packet_payload,
        repo_path(args.index_json),
        repo_path(args.triage_json),
        repo_path(args.triage_csv),
        repo_path(args.triage_md),
    )
    print(
        json.dumps(
            {
                "packet_status": packet_payload["status"],
                "triage_status": triage_payload["status"],
                "coverage": packet_payload["coverage"],
                "validation": packet_payload["validation"],
                "diversity": triage_payload["diversity"],
                "qa_summary": triage_payload["summary"],
                "p195_status": packet_payload["p195_status"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if packet_payload["validation"]["all_paths_exist"] and not triage_payload["summary"]["issue_counts"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
