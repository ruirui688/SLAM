#!/usr/bin/env python3
"""Build the P204 no-label raw evidence audit packet.

The packet samples representative P203 raw segmentation/RGB-D evidence rows for
inspection only. It does not create labels, infer admission/same-object status,
use weak/model targets, or train any model.
"""
from __future__ import annotations

import argparse
import csv
import json
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_INDEX_CSV = ROOT / "paper/evidence/raw_segmentation_evidence_index_p203.csv"
DEFAULT_OUTPUT_JSON = ROOT / "paper/evidence/raw_evidence_audit_packet_p204.json"
DEFAULT_OUTPUT_CSV = ROOT / "paper/evidence/raw_evidence_audit_packet_p204.csv"
DEFAULT_OUTPUT_MD = ROOT / "paper/export/raw_evidence_audit_packet_p204.md"
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


def token_set(row: dict[str, str]) -> set[str]:
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
    present_categories = {row.get("canonical_label", "") for row in rows}
    present_sources = {row.get("source", "") for row in rows}
    present_row_sources = {row.get("row_source", "") for row in rows}
    universe: set[str] = set()
    universe.update(f"category:{name}" for name in TARGET_CATEGORIES if name in present_categories)
    universe.update(f"source:{name}" for name in TARGET_SOURCES if name in present_sources)
    universe.update(f"row_source:{name}" for name in TARGET_ROW_SOURCES if name in present_row_sources)

    observed_category_source = Counter()
    observed_category_row_source = Counter()
    observed_source_row_source = Counter()
    sessions_by_source: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        category = row.get("canonical_label", "")
        source = row.get("source", "")
        row_source = row.get("row_source", "")
        session = row.get("session_id", "")
        if category in TARGET_CATEGORIES and source in TARGET_SOURCES:
            observed_category_source[f"category_source:{category}|{source}"] += 1
        if category in TARGET_CATEGORIES and row_source in TARGET_ROW_SOURCES:
            observed_category_row_source[f"category_row_source:{category}|{row_source}"] += 1
        if source in TARGET_SOURCES and row_source in TARGET_ROW_SOURCES:
            observed_source_row_source[f"source_row_source:{source}|{row_source}"] += 1
        if source in TARGET_SOURCES and session:
            sessions_by_source[source].add(session)

    universe.update(observed_category_source)
    universe.update(observed_category_row_source)
    universe.update(observed_source_row_source)

    for source, sessions in sessions_by_source.items():
        for session in sorted(sessions)[:2]:
            universe.add(f"session:{session}")
    return universe


def row_sort_key(row: dict[str, str]) -> tuple[str, str, str, str, int]:
    return (
        row.get("canonical_label", ""),
        row.get("source", ""),
        row.get("row_source", ""),
        row.get("physical_key", ""),
        stable_index(row),
    )


def select_rows(rows: list[dict[str, str]], max_samples: int) -> tuple[list[dict[str, str]], dict[str, Any]]:
    candidates = sorted(rows, key=row_sort_key)
    universe = build_universe(candidates)
    uncovered = set(universe)
    selected: list[dict[str, str]] = []
    used_physical_keys: set[str] = set()
    used_index_rows: set[str] = set()

    while uncovered and len(selected) < max_samples:
        best: dict[str, str] | None = None
        best_score: tuple[int, int, int, int] | None = None
        for row in candidates:
            index_row_id = row.get("index_row_id", "")
            if index_row_id in used_index_rows:
                continue
            tokens = token_set(row)
            gain = len(tokens & uncovered)
            if gain == 0:
                continue
            physical_key = row.get("physical_key", "")
            duplicate_penalty = 1 if physical_key and physical_key in used_physical_keys else 0
            # Higher gain is better; unique physical keys and earlier stable rows win ties.
            score = (gain, -duplicate_penalty, -stable_index(row), -len(selected))
            if best_score is None or score > best_score:
                best = row
                best_score = score
        if best is None:
            break
        selected.append(best)
        used_index_rows.add(best.get("index_row_id", ""))
        if best.get("physical_key"):
            used_physical_keys.add(best["physical_key"])
        uncovered -= token_set(best)

    if len(selected) < max_samples:
        for row in candidates:
            if len(selected) >= max_samples:
                break
            index_row_id = row.get("index_row_id", "")
            physical_key = row.get("physical_key", "")
            if index_row_id in used_index_rows:
                continue
            if physical_key and physical_key in used_physical_keys:
                continue
            selected.append(row)
            used_index_rows.add(index_row_id)
            if physical_key:
                used_physical_keys.add(physical_key)

    if len(selected) < max_samples:
        for row in candidates:
            if len(selected) >= max_samples:
                break
            index_row_id = row.get("index_row_id", "")
            if index_row_id in used_index_rows:
                continue
            selected.append(row)
            used_index_rows.add(index_row_id)

    selected = sorted(selected, key=stable_index)
    nonblank_physical_keys = [row.get("physical_key", "") for row in selected if row.get("physical_key", "")]
    selection_debug = {
        "universe_tokens": len(universe),
        "covered_tokens": len(universe - uncovered),
        "uncovered_tokens": sorted(uncovered),
        "rows_with_nonblank_physical_key": len(nonblank_physical_keys),
        "rows_with_blank_physical_key": len(selected) - len(nonblank_physical_keys),
        "unique_nonblank_physical_keys": len(set(nonblank_physical_keys)),
        "duplicate_nonblank_physical_key_count": len(nonblank_physical_keys) - len(set(nonblank_physical_keys)),
    }
    return selected, selection_debug


def why_sampled(row: dict[str, str], coverage_seen: dict[str, set[str]]) -> str:
    reasons: list[str] = []
    category = row.get("canonical_label", "")
    source = row.get("source", "")
    row_source = row.get("row_source", "")
    session = row.get("session_id", "")
    fields = [
        ("category", category),
        ("source", source),
        ("row_source", row_source),
        ("category/source", f"{category}|{source}"),
        ("category/row_source", f"{category}|{row_source}"),
        ("source/row_source", f"{source}|{row_source}"),
        ("session", session),
    ]
    for key, value in fields:
        if value and value not in coverage_seen[key]:
            reasons.append(f"adds {key} coverage: {value}")
        coverage_seen[key].add(value)
    if not reasons:
        reasons.append("fills deterministic packet cap with additional unique physical evidence")
    return "; ".join(reasons)


def compact_packet_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    coverage_seen: dict[str, set[str]] = defaultdict(set)
    out: list[dict[str, Any]] = []
    for ordinal, row in enumerate(rows, start=1):
        packet_row = {
            "audit_sample_id": f"p204_{ordinal:03d}",
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
            "no_label_inspection_note": "",
            "raw_evidence_issue_note": "",
        }
        for column in PATH_COLUMNS:
            packet_row[column] = row.get(column, "")
        out.append(packet_row)
    return out


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


def nested_counts(rows: list[dict[str, Any]], outer_key: str, inner_key: str) -> dict[str, dict[str, int]]:
    nested: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        nested[str(row.get(outer_key, ""))][str(row.get(inner_key, ""))] += 1
    return {outer: dict(sorted(counter.items())) for outer, counter in sorted(nested.items())}


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


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    coverage = payload["coverage"]
    validation = payload["validation"]
    lines = [
        "# P204 Raw Evidence Audit Packet",
        "",
        f"**Status:** {payload['status']}",
        "",
        "## Boundary",
        "",
        payload["scientific_boundary"],
        "",
        "## Inputs and Outputs",
        "",
        f"- Input P203 index: `{payload['inputs']['p203_index_csv']}`",
        f"- JSON packet: `{payload['outputs']['json']}`",
        f"- CSV packet: `{payload['outputs']['csv']}`",
        "",
        "## Coverage",
        "",
        f"- Samples: {coverage['sample_count']}",
        f"- Categories: {coverage['category_counts']}",
        f"- Sources: {coverage['source_counts']}",
        f"- Row sources: {coverage['row_source_counts']}",
        f"- Sessions: {coverage['session_count']}",
        f"- Raw evidence paths: {validation['raw_evidence_paths_existing']}/{validation['raw_evidence_paths_total']} existing",
        f"- All referenced paths exist: {validation['all_paths_exist']}",
        f"- Non-label inspection note fields blank: {validation['non_label_review_note_fields_blank']}",
        "",
        "## Label Gate",
        "",
        "- P195 remains `BLOCKED`.",
        "- Packet rows contain no human admission labels, no human same-object labels, no weak targets, and no model predictions.",
        "- Blank note columns are for raw-evidence inspection comments only; they must not be used to record admission or same-object labels.",
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
            "## P205 Recommendation",
            "",
            "Use this packet for human/agent raw-evidence inspection and to identify missing or ambiguous visual evidence. "
            "Keep P195 blocked until independent human admission and same-object labels exist; do not convert inspection notes "
            "into labels without a separate reviewed labeling protocol.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_packet(index_csv: Path, output_json: Path, output_csv: Path, output_md: Path, max_samples: int) -> dict[str, Any]:
    source_rows, source_columns = read_csv(index_csv)
    leaked_columns = sorted(set(source_columns) & PROHIBITED_COLUMNS)
    if leaked_columns:
        raise SystemExit(f"Refusing to build packet from prohibited columns: {', '.join(leaked_columns)}")
    if not source_rows:
        raise SystemExit(f"No rows found in {index_csv}")

    selected, selection_debug = select_rows(source_rows, max_samples)
    packet_rows = compact_packet_rows(selected)
    validation = validate_packet(packet_rows)
    payload = {
        "phase": "P204-raw-evidence-audit-packet",
        "status": "AUDIT_PACKET_BUILT_P195_STILL_BLOCKED",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scientific_boundary": (
            "No-label raw evidence inspection packet only. It samples P203 raw RGB/depth/segmentation evidence "
            "for reviewer inspection and audit coverage. It does not create or infer admission/same-object labels, "
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
        },
        "sampling_policy": {
            "deterministic": True,
            "max_samples": max_samples,
            "coverage_targets": {
                "canonical_label": TARGET_CATEGORIES,
                "source": TARGET_SOURCES,
                "row_source": TARGET_ROW_SOURCES,
                "additional": "observed category/source, category/row_source, source/row_source, and up to two sessions per source",
            },
            "duplicate_physical_key_policy": "avoid duplicate physical_key when possible; deterministic stable row order breaks ties",
            "selection_debug": selection_debug,
        },
        "coverage": coverage_summary(packet_rows),
        "validation": validation,
        "p195_status": "BLOCKED",
        "rows": packet_rows,
    }
    write_json(output_json, payload)
    write_csv(output_csv, packet_rows, PACKET_COLUMNS)
    write_markdown(output_md, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Build P204 no-label raw evidence audit packet")
    parser.add_argument("--index-csv", default=str(DEFAULT_INDEX_CSV))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT_CSV))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--max-samples", type=int, default=DEFAULT_MAX_SAMPLES)
    args = parser.parse_args()

    payload = build_packet(
        repo_path(args.index_csv),
        repo_path(args.output_json),
        repo_path(args.output_csv),
        repo_path(args.output_md),
        args.max_samples,
    )
    print(
        json.dumps(
            {
                "status": payload["status"],
                "coverage": payload["coverage"],
                "validation": payload["validation"],
                "p195_status": payload["p195_status"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if payload["validation"]["all_paths_exist"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
