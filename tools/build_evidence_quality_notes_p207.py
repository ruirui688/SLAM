#!/usr/bin/env python3
"""Build and validate P207 raw-evidence quality notes.

P207 creates a safe notes template for the P206 no-label raw evidence packet.
The notes are for evidence quality only: visibility, occlusion, blur, mask
alignment, depth usability, short reviewer notes, and whether evidence quality
blocks inspection.  The script does not create admission labels, same-object
labels, weak-label targets, or training data.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_PACKET_JSON = ROOT / "paper/evidence/raw_evidence_diverse_packet_p206.json"
DEFAULT_NOTES_CSV = ROOT / "paper/evidence/raw_evidence_quality_notes_p207.csv"
DEFAULT_NOTES_JSON = ROOT / "paper/evidence/raw_evidence_quality_notes_p207.json"
DEFAULT_PROTOCOL_MD = ROOT / "paper/export/raw_evidence_quality_notes_protocol_p207.md"

PATH_COLUMNS = [
    "raw_segmentation_color_left_path",
    "raw_segmentation_greyscale_left_path",
    "raw_segmentation_color_right_path",
    "raw_segmentation_greyscale_right_path",
    "raw_rgb_left_path",
    "raw_depth_left_path",
]

IDENTIFIER_COLUMNS = [
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
]

NOTE_COLUMNS = [
    "visibility_quality",
    "mask_alignment_quality",
    "depth_quality",
    "occlusion_level",
    "blur_level",
    "reviewer_note",
    "quality_blocker",
]

NOTES_COLUMNS = IDENTIFIER_COLUMNS + PATH_COLUMNS + NOTE_COLUMNS

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
    "admit_label",
    "same_object_label",
}

ALLOWED_VALUES = {
    "visibility_quality": ["", "clear", "partial", "poor", "not_assessable"],
    "mask_alignment_quality": ["", "good", "minor_issue", "major_issue", "not_assessable"],
    "depth_quality": ["", "usable", "limited", "unusable", "not_assessable"],
    "occlusion_level": ["", "none", "low", "medium", "high", "not_assessable"],
    "blur_level": ["", "none", "low", "medium", "high", "not_assessable"],
    "quality_blocker": ["", "no", "yes"],
}

LABEL_DECISION_PATTERN = re.compile(
    r"\b("
    r"admit|admitted|reject|rejected|accept|accepted|"
    r"same\s*object|different\s*object|same-object|different-object|"
    r"same_object|different_object|human_admit_label|human_same_object_label|"
    r"target_admit|current_weak_label|selection_v5"
    r")\b",
    re.IGNORECASE,
)


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


def load_packet(path: Path) -> dict[str, Any]:
    packet = json.loads(path.read_text(encoding="utf-8"))
    rows = packet.get("rows")
    if not isinstance(rows, list):
        raise SystemExit(f"{path} has no list-valued rows field")
    return packet


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


def check_prohibited_columns(columns: set[str], context: str) -> list[str]:
    leaked = sorted(columns & PROHIBITED_COLUMNS)
    if leaked:
        raise SystemExit(f"Refusing {context}; prohibited label/proxy columns present: {', '.join(leaked)}")
    return leaked


def build_note_rows(packet_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in packet_rows:
        row = {column: source.get(column, "") for column in IDENTIFIER_COLUMNS + PATH_COLUMNS}
        for column in NOTE_COLUMNS:
            row[column] = ""
        rows.append(row)
    return rows


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    path_total = 0
    paths_existing = 0
    for row in rows:
        for column in PATH_COLUMNS:
            value = str(row.get(column) or "")
            if not value:
                continue
            path_total += 1
            if evidence_exists(value):
                paths_existing += 1
    note_blank_counts = {column: sum(1 for row in rows if not str(row.get(column) or "")) for column in NOTE_COLUMNS}
    return {
        "rows": len(rows),
        "category_counts": dict(sorted(Counter(str(row.get("canonical_label") or "") for row in rows).items())),
        "source_counts": dict(sorted(Counter(str(row.get("source") or "") for row in rows).items())),
        "row_source_counts": dict(sorted(Counter(str(row.get("row_source") or "") for row in rows).items())),
        "raw_evidence_paths_total": path_total,
        "raw_evidence_paths_existing": paths_existing,
        "all_paths_exist": path_total == paths_existing,
        "note_blank_counts": note_blank_counts,
        "all_note_fields_blank": all(count == len(rows) for count in note_blank_counts.values()),
    }


def validate_note_rows(rows: list[dict[str, str]], columns: list[str]) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    check_prohibited_columns(set(columns), "P207 notes validation")

    missing_required = [column for column in NOTES_COLUMNS if column not in columns]
    extra_note_like = [
        column
        for column in columns
        if column not in NOTES_COLUMNS and ("label" in column.lower() or "admit" in column.lower() or "same" in column.lower())
    ]
    for column in missing_required:
        issues.append({"row": "", "column": column, "code": "missing_required_column", "value": ""})
    for column in extra_note_like:
        issues.append({"row": "", "column": column, "code": "unsafe_extra_column_name", "value": ""})

    seen_ids: set[str] = set()
    duplicate_ids: set[str] = set()
    for index, row in enumerate(rows, start=2):
        audit_id = str(row.get("audit_sample_id") or "")
        if not audit_id:
            issues.append({"row": str(index), "column": "audit_sample_id", "code": "blank_audit_sample_id", "value": ""})
        elif audit_id in seen_ids:
            duplicate_ids.add(audit_id)
        seen_ids.add(audit_id)

        for column, allowed in ALLOWED_VALUES.items():
            value = str(row.get(column) or "")
            if value not in allowed:
                issues.append({"row": str(index), "column": column, "code": "invalid_allowed_value", "value": value})

        note = str(row.get("reviewer_note") or "")
        if "\n" in note or "\r" in note:
            issues.append({"row": str(index), "column": "reviewer_note", "code": "multiline_note_not_allowed", "value": ""})
        if len(note) > 500:
            issues.append({"row": str(index), "column": "reviewer_note", "code": "reviewer_note_too_long", "value": str(len(note))})
        if LABEL_DECISION_PATTERN.search(note):
            issues.append({"row": str(index), "column": "reviewer_note", "code": "possible_label_decision_text", "value": note[:120]})

        for column in PATH_COLUMNS:
            value = str(row.get(column) or "")
            if not value:
                issues.append({"row": str(index), "column": column, "code": "blank_evidence_path", "value": ""})
            elif not evidence_exists(value):
                issues.append({"row": str(index), "column": column, "code": "missing_evidence_path", "value": value})

    for audit_id in sorted(duplicate_ids):
        issues.append({"row": "", "column": "audit_sample_id", "code": "duplicate_audit_sample_id", "value": audit_id})

    for row in rows:
        if str(row.get("quality_blocker") or "") == "yes" and not any(
            str(row.get(column) or "")
            for column in [
                "visibility_quality",
                "mask_alignment_quality",
                "depth_quality",
                "occlusion_level",
                "blur_level",
                "reviewer_note",
            ]
        ):
            warnings.append(
                {
                    "row": str(row.get("audit_sample_id") or ""),
                    "column": "quality_blocker",
                    "code": "quality_blocker_without_quality_detail",
                    "value": "yes",
                }
            )

    note_fields_blank = all(all(str(row.get(column) or "") == "" for column in NOTE_COLUMNS) for row in rows)
    return {
        "status": "PASS" if not issues else "FAIL",
        "row_count": len(rows),
        "issue_count": len(issues),
        "warning_count": len(warnings),
        "issues": issues,
        "warnings": warnings,
        "note_fields_blank": note_fields_blank,
        "allowed_values": ALLOWED_VALUES,
    }


def write_protocol(path: Path, payload: dict[str, Any]) -> None:
    def domain(column: str) -> str:
        values = ["blank" if value == "" else value for value in ALLOWED_VALUES[column]]
        return ", ".join(f"`{value}`" for value in values)

    lines = [
        "# P207 Raw Evidence Quality Notes Protocol",
        "",
        "**Status:** evidence-quality notes only; P195 remains `BLOCKED`.",
        "",
        "## Scope",
        "",
        "This protocol is for reviewing the P206 diversity-first raw evidence packet for visual evidence quality only. It may record whether the RGB/depth/segmentation evidence is clear enough for later inspection, but it must not record object-admission decisions or same-object association decisions.",
        "",
        "## Allowed Note Fields",
        "",
        "| column | allowed values | meaning |",
        "| --- | --- | --- |",
        f"| `visibility_quality` | {domain('visibility_quality')} | Whether the object evidence is visually inspectable in the image. |",
        f"| `mask_alignment_quality` | {domain('mask_alignment_quality')} | Whether the segmentation mask appears aligned enough for evidence review. |",
        f"| `depth_quality` | {domain('depth_quality')} | Whether the depth image appears usable for evidence inspection. |",
        f"| `occlusion_level` | {domain('occlusion_level')} | Apparent visual occlusion level only. |",
        f"| `blur_level` | {domain('blur_level')} | Apparent motion/focus blur level only. |",
        "| `reviewer_note` | free text, <=500 chars | Short evidence-quality note. Do not write label decisions here. |",
        f"| `quality_blocker` | {domain('quality_blocker')} | `yes` only when evidence quality prevents reliable evidence inspection. |",
        "",
        "Blank values are valid. The generated P207 notes template intentionally leaves all note fields blank.",
        "",
        "## Forbidden Content",
        "",
        "- Do not fill, infer, or store `human_admit_label`.",
        "- Do not fill, infer, or store `human_same_object_label`.",
        "- Do not write admit/reject, accept/reject, same-object/different-object, or equivalent decisions in any P207 note field.",
        "- Do not copy `target_admit`, `current_weak_label`, `selection_v5`, model predictions, model probabilities, or weak labels into P207.",
        "- Do not turn `canonical_label`, category names, row source, source, mask quality, depth quality, occlusion, blur, or reviewer notes into admission labels or same-object labels.",
        "- Do not train models or tune admission-control thresholds from P207 notes.",
        "- Do not edit raw images, depth, segmentation files, the P206 packet, or upstream evidence data while using this protocol.",
        "",
        "## Validation",
        "",
        "Run:",
        "",
        "```bash",
        "python3 tools/build_evidence_quality_notes_p207.py validate",
        "```",
        "",
        "Validation checks allowed value domains, evidence path existence, duplicate/blank sample IDs, prohibited label/proxy columns, and possible label-decision text in `reviewer_note`.",
        "",
        "## Current Template Summary",
        "",
        f"- Notes CSV: `{payload['outputs']['csv']}`",
        f"- Notes JSON: `{payload['outputs']['json']}`",
        f"- Rows: {payload['summary']['rows']}",
        f"- Raw evidence paths: {payload['summary']['raw_evidence_paths_existing']}/{payload['summary']['raw_evidence_paths_total']} existing",
        f"- All note fields blank: {payload['summary']['all_note_fields_blank']}",
        "",
        "## Scientific Boundary",
        "",
        "P207 records evidence quality only. It creates no labels, performs no training, and does not support learned admission-control claims. P195 remains blocked until independent human admission and same-object labels exist.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build(packet_json: Path, notes_csv: Path, notes_json: Path, protocol_md: Path) -> dict[str, Any]:
    packet = load_packet(packet_json)
    packet_rows = packet["rows"]
    packet_columns = set()
    for row in packet_rows:
        packet_columns.update(row.keys())
    check_prohibited_columns(packet_columns, "P207 notes build from P206 packet")

    rows = build_note_rows(packet_rows)
    summary = summarize_rows(rows)
    validation = validate_note_rows([{key: str(value) for key, value in row.items()} for row in rows], NOTES_COLUMNS)
    payload = {
        "phase": "P207-evidence-quality-notes-protocol",
        "status": "EVIDENCE_QUALITY_NOTES_TEMPLATE_BUILT_P195_STILL_BLOCKED",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scientific_boundary": (
            "Evidence-quality notes only. P207 preserves P206 row identifiers and local raw evidence paths, "
            "adds blank non-label quality-note fields, validates allowed values, and does not create or infer "
            "admission/same-object labels or train models."
        ),
        "inputs": {"p206_packet_json": rel(packet_json)},
        "outputs": {"csv": rel(notes_csv), "json": rel(notes_json), "protocol": rel(protocol_md)},
        "constraints_observed": {
            "human_admit_label_created_or_filled": False,
            "human_same_object_label_created_or_filled": False,
            "weak_admission_or_model_predictions_used_as_labels": False,
            "admission_or_semantic_stability_training_performed": False,
            "downloads_performed": False,
            "raw_images_or_data_modified": False,
        },
        "p195_status": "BLOCKED",
        "schema": {
            "identifier_columns": IDENTIFIER_COLUMNS,
            "path_columns": PATH_COLUMNS,
            "note_columns": NOTE_COLUMNS,
            "allowed_values": ALLOWED_VALUES,
            "reviewer_note_rules": {
                "max_chars": 500,
                "multiline_allowed": False,
                "label_decision_text_allowed": False,
            },
        },
        "summary": summary,
        "validation": validation,
        "rows": rows,
    }
    write_csv(notes_csv, rows, NOTES_COLUMNS)
    write_json(notes_json, payload)
    write_protocol(protocol_md, payload)
    return payload


def validate(notes_csv: Path, output_json: Path | None = None) -> dict[str, Any]:
    rows, columns = read_csv(notes_csv)
    validation = validate_note_rows(rows, columns)
    summary = summarize_rows(rows) if not validation["issues"] else {"rows": len(rows)}
    payload = {
        "phase": "P207-evidence-quality-notes-validation",
        "status": "PASS" if validation["status"] == "PASS" else "FAIL",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {"notes_csv": rel(notes_csv)},
        "p195_status": "BLOCKED",
        "scientific_boundary": (
            "Validation checks evidence-quality note schema and values only. It does not interpret notes as "
            "admission/same-object labels and does not train models."
        ),
        "summary": summary,
        "validation": validation,
    }
    if output_json is not None:
        write_json(output_json, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or validate P207 evidence-quality notes")
    subparsers = parser.add_subparsers(dest="command")

    build_parser = subparsers.add_parser("build", help="Build blank P207 notes template and protocol")
    build_parser.add_argument("--packet-json", default=str(DEFAULT_PACKET_JSON))
    build_parser.add_argument("--notes-csv", default=str(DEFAULT_NOTES_CSV))
    build_parser.add_argument("--notes-json", default=str(DEFAULT_NOTES_JSON))
    build_parser.add_argument("--protocol-md", default=str(DEFAULT_PROTOCOL_MD))

    validate_parser = subparsers.add_parser("validate", help="Validate filled or blank P207 notes")
    validate_parser.add_argument("--notes-csv", default=str(DEFAULT_NOTES_CSV))
    validate_parser.add_argument("--output-json", default="")

    args = parser.parse_args()
    command = args.command or "build"
    if command == "build":
        payload = build(
            repo_path(args.packet_json),
            repo_path(args.notes_csv),
            repo_path(args.notes_json),
            repo_path(args.protocol_md),
        )
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "summary": payload["summary"],
                    "validation_status": payload["validation"]["status"],
                    "p195_status": payload["p195_status"],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if payload["validation"]["status"] == "PASS" else 2
    if command == "validate":
        output_json = repo_path(args.output_json) if args.output_json else None
        payload = validate(repo_path(args.notes_csv), output_json)
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "row_count": payload["validation"]["row_count"],
                    "issue_count": payload["validation"]["issue_count"],
                    "warning_count": payload["validation"]["warning_count"],
                    "note_fields_blank": payload["validation"]["note_fields_blank"],
                    "p195_status": payload["p195_status"],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if payload["status"] == "PASS" else 2
    parser.error(f"unknown command: {command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
