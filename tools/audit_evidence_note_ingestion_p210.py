#!/usr/bin/env python3
"""Audit P207 evidence-quality note ingestion readiness.

P210 is read-only. It checks whether P207 reviewer notes can be ingested into
an evidence-quality-only downstream table. It does not create admission labels,
same-object labels, training rows, or admission-control claims.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import build_evidence_quality_notes_p207 as p207
import summarize_evidence_quality_notes_p208 as p208


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_NOTES_CSV = ROOT / "paper/evidence/raw_evidence_quality_notes_p207.csv"
DEFAULT_AUDIT_JSON = ROOT / "paper/evidence/evidence_note_ingestion_audit_p210.json"
DEFAULT_AUDIT_MD = ROOT / "paper/export/evidence_note_ingestion_audit_p210.md"
DEFAULT_MANIFEST_CSV = ROOT / "paper/evidence/evidence_note_ingestion_manifest_p210.csv"

READINESS_READY_EMPTY = "READY_EMPTY"
READINESS_READY_WITH_QUALITY_NOTES = "READY_WITH_QUALITY_NOTES"
READINESS_BLOCKED_INVALID_VALUES = "BLOCKED_INVALID_VALUES"
READINESS_BLOCKED_LABEL_LEAKAGE = "BLOCKED_LABEL_LEAKAGE"

QUALITY_ONLY_INGEST_FIELDS = [
    "audit_sample_id",
    "p203_index_row_id",
    "p202_audit_row_id",
    "sample_id",
    "observation_id",
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
    "visibility_quality",
    "mask_alignment_quality",
    "depth_quality",
    "occlusion_level",
    "blur_level",
    "reviewer_note",
    "quality_blocker",
]

NON_INGESTED_SOURCE_FIELDS = [
    "canonical_label",
    "row_source",
    "row_role",
]

LABEL_OR_PROXY_FIELD_PATTERNS = [
    "human_admit_label",
    "human_same_object_label",
    "target_admit",
    "current_weak_label",
    "selection_v5",
    "model_prediction",
    "model_probability",
    "weak_label",
    "admit_label",
    "same_object_label",
    "admission_label",
    "admission_decision",
    "same_object_decision",
    "different_object",
    "predicted_admit",
    "admit_probability",
    "same_object_probability",
]


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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def compact_issue_codes(items: list[dict[str, Any]]) -> list[str]:
    return sorted({str(item.get("code") or "") for item in items if item.get("code")})


def has_label_or_proxy_field(columns: list[str]) -> list[str]:
    lower = {column.lower(): column for column in columns}
    blocked = set(p207.PROHIBITED_COLUMNS) | set(p208.PROHIBITED_COLUMNS)
    direct = {lower_name for lower_name in lower if lower_name in blocked}
    pattern_hits = {
        lower_name
        for lower_name in lower
        for pattern in LABEL_OR_PROXY_FIELD_PATTERNS
        if pattern in lower_name
    }
    return sorted(lower[name] for name in direct | pattern_hits)


def count_note_values(rows: list[dict[str, str]]) -> dict[str, Any]:
    blank_counts = {column: 0 for column in p207.NOTE_COLUMNS}
    nonblank_counts = {column: 0 for column in p207.NOTE_COLUMNS}
    distributions: dict[str, dict[str, int]] = {}
    for column in p207.NOTE_COLUMNS:
        counts = Counter(str(row.get(column) or "") for row in rows)
        blank_counts[column] = counts.get("", 0)
        nonblank_counts[column] = sum(count for value, count in counts.items() if value)
        if column in p207.ALLOWED_VALUES:
            ordered: dict[str, int] = {}
            for value in p207.ALLOWED_VALUES[column]:
                ordered["blank" if value == "" else value] = counts.get(value, 0)
            for value in sorted(set(counts) - set(p207.ALLOWED_VALUES[column])):
                ordered[value] = counts[value]
            distributions[column] = ordered
        else:
            distributions[column] = {
                "blank": counts.get("", 0),
                "nonblank": sum(count for value, count in counts.items() if value),
            }
    return {
        "blank_counts": blank_counts,
        "nonblank_counts": nonblank_counts,
        "all_note_fields_blank": all(count == len(rows) for count in blank_counts.values()),
        "any_quality_note_present": any(count > 0 for count in nonblank_counts.values()),
        "distributions": distributions,
    }


def quality_only_manifest_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [{column: str(row.get(column) or "") for column in QUALITY_ONLY_INGEST_FIELDS} for row in rows]


def classify_readiness(
    rows: list[dict[str, str]],
    columns: list[str],
    validation: dict[str, Any],
    note_counts: dict[str, Any],
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    prohibited_columns = has_label_or_proxy_field(columns)
    reviewer_note_leakage = validation["reviewer_note_label_text_rows"]
    if prohibited_columns:
        reasons.append(f"prohibited label/proxy columns present: {', '.join(prohibited_columns)}")
    if reviewer_note_leakage:
        reasons.append(f"{len(reviewer_note_leakage)} reviewer_note rows contain admission/same-object-like text")
    if reasons:
        return READINESS_BLOCKED_LABEL_LEAKAGE, reasons

    invalid_rows = validation["invalid_value_rows"]
    hard_issue_codes = [
        code
        for code in compact_issue_codes(validation.get("issues", []))
        if code
        not in {
            "possible_label_decision_text",
            "prohibited_label_or_proxy_column",
        }
    ]
    if invalid_rows:
        reasons.append(f"{len(invalid_rows)} rows contain invalid allowed values")
    if hard_issue_codes:
        reasons.append(f"schema/readability validation issues: {', '.join(hard_issue_codes)}")
    if invalid_rows or hard_issue_codes or validation["status"] != "PASS":
        return READINESS_BLOCKED_INVALID_VALUES, reasons

    if not rows or note_counts["all_note_fields_blank"]:
        return READINESS_READY_EMPTY, ["all P207 evidence-quality note fields are blank"]

    return READINESS_READY_WITH_QUALITY_NOTES, ["valid non-label evidence-quality note fields are present"]


def build_ingestion_manifest() -> dict[str, Any]:
    return {
        "purpose": "evidence_quality_only_downstream_table",
        "ingested_fields": QUALITY_ONLY_INGEST_FIELDS,
        "non_ingested_source_fields": NON_INGESTED_SOURCE_FIELDS,
        "excluded_label_or_proxy_fields": sorted(set(p207.PROHIBITED_COLUMNS) | set(p208.PROHIBITED_COLUMNS)),
        "contains_human_admit_label": "human_admit_label" in QUALITY_ONLY_INGEST_FIELDS,
        "contains_human_same_object_label": "human_same_object_label" in QUALITY_ONLY_INGEST_FIELDS,
        "contains_admission_or_same_object_decision_field": any(
            blocked in field
            for field in QUALITY_ONLY_INGEST_FIELDS
            for blocked in ["admit", "admission", "same_object", "different_object", "target", "weak", "model"]
        ),
        "contains_canonical_label_field": "canonical_label" in QUALITY_ONLY_INGEST_FIELDS,
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    readiness = payload["readiness"]
    summary = payload["summary"]
    validation = payload["validation"]
    manifest = payload["ingestion_manifest"]
    lines = [
        "# P210 Evidence-Quality Note Ingestion Audit",
        "",
        f"**Readiness:** `{readiness['status']}`; P195 remains `{payload['p195_status']}`.",
        "",
        "## Scope",
        "",
        "P210 audits whether P207 evidence-quality reviewer notes are ingestible into a quality-only downstream table. It does not create labels, import labels, train models, or support admission-control claims.",
        "",
        "## Current Results",
        "",
        f"- Rows audited: {summary['rows']}",
        f"- All P207 note fields blank: {summary['all_note_fields_blank']}",
        f"- Any quality note present: {summary['any_quality_note_present']}",
        f"- Validation: `{validation['status']}` ({validation['issue_count']} issues, {validation['warning_count']} warnings)",
        f"- Reviewer-note label leakage rows: {len(validation['reviewer_note_label_text_rows'])}",
        f"- Prohibited label/proxy columns: {', '.join(validation['prohibited_columns_present']) if validation['prohibited_columns_present'] else 'none'}",
        f"- Real P207 notes hash unchanged: `{payload['real_p207_notes_hash_unchanged']}`",
        "",
        "## Ingestion Manifest",
        "",
        f"- Manifest CSV: `{payload['outputs']['manifest_csv']}`",
        f"- Fields ingested: {len(manifest['ingested_fields'])}",
        f"- Contains `human_admit_label`: `{manifest['contains_human_admit_label']}`",
        f"- Contains `human_same_object_label`: `{manifest['contains_human_same_object_label']}`",
        f"- Contains admission/same-object decision field: `{manifest['contains_admission_or_same_object_decision_field']}`",
        f"- Contains `canonical_label`: `{manifest['contains_canonical_label_field']}`",
        "",
        "Ingested fields:",
        "",
    ]
    lines.extend(f"- `{field}`" for field in manifest["ingested_fields"])
    lines.extend(["", "## Self-Test Results", ""])
    self_test = payload.get("self_test")
    if self_test:
        lines.append(f"- Overall: `{self_test['status']}` ({self_test['passed_case_count']}/{self_test['case_count']} cases)")
        for case in self_test["cases"]:
            marker = "PASS" if case["expected_outcome_met"] else "FAIL"
            lines.append(f"- `{case['name']}`: {marker}; readiness=`{case['actual_readiness']}` expected=`{case['expected_readiness']}`")
    else:
        lines.append("- Not run in this invocation.")
    lines.extend(
        [
            "",
            "## Scientific Boundary",
            "",
            "P210 is read-only evidence-quality note ingestion audit coverage. It does not fill or infer `human_admit_label` or `human_same_object_label`, does not use weak/model/selection fields as labels, does not train, and does not alter real P207 notes.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def audit(
    notes_csv: Path,
    audit_json: Path,
    audit_md: Path,
    manifest_csv: Path,
    *,
    include_self_test: bool,
) -> dict[str, Any]:
    before_hash = sha256(notes_csv)
    rows, columns = read_csv(notes_csv)
    validation = p208.validate_notes(rows, columns)
    note_counts = count_note_values(rows)
    readiness_status, readiness_reasons = classify_readiness(rows, columns, validation, note_counts)
    manifest_rows = quality_only_manifest_rows(rows)
    manifest = build_ingestion_manifest()
    after_hash = sha256(notes_csv)

    payload: dict[str, Any] = {
        "phase": "P210-evidence-note-ingestion-audit",
        "status": "PASS" if readiness_status.startswith("READY_") and before_hash == after_hash else "FAIL",
        "readiness": {
            "status": readiness_status,
            "reasons": readiness_reasons,
        },
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {"notes_csv": rel(notes_csv)},
        "outputs": {
            "audit_json": rel(audit_json),
            "audit_markdown": rel(audit_md),
            "manifest_csv": rel(manifest_csv),
        },
        "p195_status": "BLOCKED",
        "scientific_boundary": (
            "Read-only evidence-quality note ingestion audit only. P210 audits P207 quality-note "
            "ingestibility and quality-only safety boundaries; it creates no admission/same-object labels, "
            "does not import labels, does not train, and does not support admission-control claims."
        ),
        "constraints_observed": {
            "human_admit_label_created_or_filled": False,
            "human_same_object_label_created_or_filled": False,
            "weak_admission_or_model_predictions_used_as_labels": False,
            "admission_or_semantic_stability_training_performed": False,
            "downloads_performed": False,
            "real_p207_notes_modified": before_hash != after_hash,
        },
        "real_p207_notes_sha256_before": before_hash,
        "real_p207_notes_sha256_after": after_hash,
        "real_p207_notes_hash_unchanged": before_hash == after_hash,
        "summary": {
            "rows": len(rows),
            "source_columns": columns,
            "all_note_fields_blank": note_counts["all_note_fields_blank"],
            "any_quality_note_present": note_counts["any_quality_note_present"],
            "note_blank_counts": note_counts["blank_counts"],
            "note_nonblank_counts": note_counts["nonblank_counts"],
            "note_field_distributions": note_counts["distributions"],
            "manifest_rows": len(manifest_rows),
        },
        "validation": {
            "status": validation["status"],
            "issue_count": validation["issue_count"],
            "warning_count": validation["warning_count"],
            "issue_codes": compact_issue_codes(validation.get("issues", [])),
            "warning_codes": compact_issue_codes(validation.get("warnings", [])),
            "invalid_value_rows": validation["invalid_value_rows"],
            "reviewer_note_label_text_rows": validation["reviewer_note_label_text_rows"],
            "prohibited_columns_present": has_label_or_proxy_field(columns),
            "unsafe_extra_columns_present": validation["unsafe_extra_columns_present"],
            "p207_validation_status": validation["p207_validation_status"],
            "p207_issue_count": validation["p207_issue_count"],
            "p207_warning_count": validation["p207_warning_count"],
            "p207_issue_codes": compact_issue_codes(validation.get("p207_issues", [])),
        },
        "ingestion_manifest": manifest,
        "ingestion_manifest_preview": manifest_rows[:5],
    }

    if include_self_test:
        payload["self_test"] = run_self_test(write_report=False)
        if payload["self_test"]["status"] != "PASS":
            payload["status"] = "FAIL"

    write_csv(manifest_csv, manifest_rows, QUALITY_ONLY_INGEST_FIELDS)
    write_json(audit_json, payload)
    write_markdown(audit_md, payload)
    return payload


def mutate_valid_quality_notes(rows: list[dict[str, str]], columns: list[str]) -> tuple[list[dict[str, str]], list[str]]:
    rows[0]["visibility_quality"] = "clear"
    rows[0]["mask_alignment_quality"] = "good"
    rows[0]["depth_quality"] = "usable"
    rows[0]["occlusion_level"] = "low"
    rows[0]["blur_level"] = "none"
    rows[0]["quality_blocker"] = "no"
    rows[0]["reviewer_note"] = "Evidence quality is inspectable."
    return rows, columns


def mutate_invalid_value(rows: list[dict[str, str]], columns: list[str]) -> tuple[list[dict[str, str]], list[str]]:
    rows[0]["depth_quality"] = "excellent"
    return rows, columns


def mutate_prohibited_column(rows: list[dict[str, str]], columns: list[str]) -> tuple[list[dict[str, str]], list[str]]:
    columns = columns + ["human_same_object_label"]
    rows[0]["human_same_object_label"] = ""
    return rows, columns


def mutate_label_text(rows: list[dict[str, str]], columns: list[str]) -> tuple[list[dict[str, str]], list[str]]:
    rows[0]["reviewer_note"] = "This note says same object, which is forbidden here."
    return rows, columns


def run_self_case(
    name: str,
    expected_readiness: str,
    base_rows: list[dict[str, str]],
    base_columns: list[str],
    temp_dir: Path,
    mutator: Callable[[list[dict[str, str]], list[str]], tuple[list[dict[str, str]], list[str]]] | None = None,
) -> dict[str, Any]:
    rows = [dict(row) for row in base_rows]
    columns = list(base_columns)
    if mutator is not None:
        rows, columns = mutator(rows, columns)
    notes_csv = temp_dir / f"{name}.csv"
    write_csv(notes_csv, rows, columns)
    payload = audit(
        notes_csv,
        temp_dir / f"{name}.json",
        temp_dir / f"{name}.md",
        temp_dir / f"{name}_manifest.csv",
        include_self_test=False,
    )
    actual = payload["readiness"]["status"]
    return {
        "name": name,
        "expected_readiness": expected_readiness,
        "actual_readiness": actual,
        "expected_outcome_met": actual == expected_readiness,
        "status": payload["status"],
        "issue_codes": payload["validation"]["issue_codes"],
        "warning_codes": payload["validation"]["warning_codes"],
        "manifest_has_label_fields": (
            payload["ingestion_manifest"]["contains_human_admit_label"]
            or payload["ingestion_manifest"]["contains_human_same_object_label"]
            or payload["ingestion_manifest"]["contains_admission_or_same_object_decision_field"]
            or payload["ingestion_manifest"]["contains_canonical_label_field"]
        ),
    }


def run_self_test(*, write_report: bool = True) -> dict[str, Any]:
    base_rows, base_columns = read_csv(DEFAULT_NOTES_CSV)
    before_hash = sha256(DEFAULT_NOTES_CSV)
    with tempfile.TemporaryDirectory(prefix="p210_evidence_note_ingestion_") as temp_root:
        temp_dir = Path(temp_root)
        cases = [
            run_self_case("blank_notes_ready_empty", READINESS_READY_EMPTY, base_rows, base_columns, temp_dir),
            run_self_case(
                "valid_quality_notes_ready",
                READINESS_READY_WITH_QUALITY_NOTES,
                base_rows,
                base_columns,
                temp_dir,
                mutate_valid_quality_notes,
            ),
            run_self_case(
                "invalid_allowed_value_blocked",
                READINESS_BLOCKED_INVALID_VALUES,
                base_rows,
                base_columns,
                temp_dir,
                mutate_invalid_value,
            ),
            run_self_case(
                "prohibited_column_label_leakage_blocked",
                READINESS_BLOCKED_LABEL_LEAKAGE,
                base_rows,
                base_columns,
                temp_dir,
                mutate_prohibited_column,
            ),
            run_self_case(
                "reviewer_note_label_text_blocked",
                READINESS_BLOCKED_LABEL_LEAKAGE,
                base_rows,
                base_columns,
                temp_dir,
                mutate_label_text,
            ),
        ]
    after_hash = sha256(DEFAULT_NOTES_CSV)
    all_cases_passed = all(case["expected_outcome_met"] and not case["manifest_has_label_fields"] for case in cases)
    payload = {
        "status": "PASS" if all_cases_passed and before_hash == after_hash else "FAIL",
        "case_count": len(cases),
        "passed_case_count": sum(1 for case in cases if case["expected_outcome_met"] and not case["manifest_has_label_fields"]),
        "real_p207_notes_sha256_before": before_hash,
        "real_p207_notes_sha256_after": after_hash,
        "real_p207_notes_hash_unchanged": before_hash == after_hash,
        "cases": cases,
    }
    if write_report:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit P207 evidence-quality note ingestion readiness")
    parser.add_argument("--notes-csv", default=str(DEFAULT_NOTES_CSV))
    parser.add_argument("--audit-json", default=str(DEFAULT_AUDIT_JSON))
    parser.add_argument("--audit-md", default=str(DEFAULT_AUDIT_MD))
    parser.add_argument("--manifest-csv", default=str(DEFAULT_MANIFEST_CSV))
    parser.add_argument("--self-test", action="store_true", help="Run synthetic temporary fixture self-tests only")
    parser.add_argument("--include-self-test", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    if args.self_test:
        payload = run_self_test(write_report=True)
        return 0 if payload["status"] == "PASS" else 2

    payload = audit(
        repo_path(args.notes_csv),
        repo_path(args.audit_json),
        repo_path(args.audit_md),
        repo_path(args.manifest_csv),
        include_self_test=args.include_self_test,
    )
    print(
        json.dumps(
            {
                "status": payload["status"],
                "readiness": payload["readiness"]["status"],
                "rows": payload["summary"]["rows"],
                "all_note_fields_blank": payload["summary"]["all_note_fields_blank"],
                "manifest_fields": len(payload["ingestion_manifest"]["ingested_fields"]),
                "self_test_status": payload.get("self_test", {}).get("status", "not_run"),
                "p195_status": payload["p195_status"],
                "real_p207_notes_hash_unchanged": payload["real_p207_notes_hash_unchanged"],
                "outputs": payload["outputs"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if payload["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
