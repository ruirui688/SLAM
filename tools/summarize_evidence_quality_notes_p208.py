#!/usr/bin/env python3
"""Summarize P207 evidence-quality notes without creating labels.

P208 is a read-only QA summarizer for the P207 notes template after reviewers
fill evidence-quality fields.  It reports quality distributions and blocker
rates only.  It never creates admission labels, same-object labels, weak-label
targets, or training data.
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

import build_evidence_quality_notes_p207 as p207


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_NOTES_CSV = ROOT / "paper/evidence/raw_evidence_quality_notes_p207.csv"
DEFAULT_SUMMARY_JSON = ROOT / "paper/evidence/evidence_quality_notes_summary_p208.json"
DEFAULT_SUMMARY_MD = ROOT / "paper/export/evidence_quality_notes_summary_p208.md"
DEFAULT_BLOCKERS_CSV = ROOT / "paper/evidence/evidence_quality_notes_blockers_p208.csv"

NOTE_FIELDS = list(p207.NOTE_COLUMNS)
GROUP_FIELDS = ["canonical_label", "source", "row_source", "session_id"]
BLOCKER_ROW_COLUMNS = [
    "audit_sample_id",
    "canonical_label",
    "source",
    "row_source",
    "session_id",
    "frame_index",
    "quality_blocker",
    "visibility_quality",
    "mask_alignment_quality",
    "depth_quality",
    "occlusion_level",
    "blur_level",
    "reviewer_note",
]

PROHIBITED_COLUMNS = set(p207.PROHIBITED_COLUMNS) | {
    "admission_label",
    "admission_decision",
    "same_object_decision",
    "same_object",
    "different_object",
    "selection_v5_label",
    "selection_v5_score",
    "predicted_admit",
    "admit_probability",
    "same_object_probability",
}

UNSAFE_EXTRA_COLUMN_PATTERN = re.compile(
    r"(human|label|admit|admission|same[_ -]?object|different[_ -]?object|"
    r"target|weak|selection|model|prediction|probability)",
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def count_distribution(rows: list[dict[str, str]], column: str) -> dict[str, int]:
    counts = Counter(str(row.get(column) or "") for row in rows)
    ordered: dict[str, int] = {}
    allowed = p207.ALLOWED_VALUES.get(column)
    if allowed is not None:
        for value in allowed:
            ordered["blank" if value == "" else value] = counts.get(value, 0)
        for value in sorted(set(counts) - set(allowed)):
            ordered[value] = counts[value]
    else:
        ordered["blank"] = counts.get("", 0)
        nonblank = sum(count for value, count in counts.items() if value)
        ordered["nonblank"] = nonblank
    return ordered


def safe_row_ref(row: dict[str, str], index: int) -> dict[str, str]:
    return {
        "csv_row": str(index),
        "audit_sample_id": str(row.get("audit_sample_id") or ""),
        "canonical_label": str(row.get("canonical_label") or ""),
        "source": str(row.get("source") or ""),
        "row_source": str(row.get("row_source") or ""),
        "session_id": str(row.get("session_id") or ""),
        "frame_index": str(row.get("frame_index") or ""),
    }


def validate_notes(rows: list[dict[str, str]], columns: list[str]) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    prohibited = sorted(set(columns) & PROHIBITED_COLUMNS)
    for column in prohibited:
        issues.append({"csv_row": "", "audit_sample_id": "", "column": column, "code": "prohibited_label_or_proxy_column"})

    missing_required = [column for column in p207.NOTES_COLUMNS if column not in columns]
    for column in missing_required:
        issues.append({"csv_row": "", "audit_sample_id": "", "column": column, "code": "missing_required_column"})

    extra_unsafe = [
        column
        for column in columns
        if column not in p207.NOTES_COLUMNS and column not in prohibited and UNSAFE_EXTRA_COLUMN_PATTERN.search(column)
    ]
    for column in sorted(extra_unsafe):
        issues.append({"csv_row": "", "audit_sample_id": "", "column": column, "code": "unsafe_extra_column_name"})

    seen_ids: set[str] = set()
    duplicate_ids: set[str] = set()
    invalid_rows: list[dict[str, str]] = []
    reviewer_note_label_text_rows: list[dict[str, str]] = []

    for index, row in enumerate(rows, start=2):
        ref = safe_row_ref(row, index)
        audit_id = ref["audit_sample_id"]
        if not audit_id:
            issues.append({**ref, "column": "audit_sample_id", "code": "blank_audit_sample_id"})
        elif audit_id in seen_ids:
            duplicate_ids.add(audit_id)
        seen_ids.add(audit_id)

        for column, allowed in p207.ALLOWED_VALUES.items():
            value = str(row.get(column) or "")
            if value not in allowed:
                item = {**ref, "column": column, "code": "invalid_allowed_value", "value": value}
                issues.append(item)
                invalid_rows.append(item)

        note = str(row.get("reviewer_note") or "")
        if "\n" in note or "\r" in note:
            issues.append({**ref, "column": "reviewer_note", "code": "multiline_note_not_allowed"})
        if len(note) > 500:
            issues.append({**ref, "column": "reviewer_note", "code": "reviewer_note_too_long", "value": str(len(note))})
        if p207.LABEL_DECISION_PATTERN.search(note):
            item = {**ref, "column": "reviewer_note", "code": "possible_label_decision_text", "value_preview": note[:120]}
            issues.append(item)
            reviewer_note_label_text_rows.append(item)

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
            warnings.append({**ref, "column": "quality_blocker", "code": "quality_blocker_without_quality_detail"})

    for audit_id in sorted(duplicate_ids):
        issues.append({"csv_row": "", "audit_sample_id": audit_id, "column": "audit_sample_id", "code": "duplicate_audit_sample_id"})

    try:
        p207_validation = p207.validate_note_rows(rows, columns)
    except SystemExit as exc:
        p207_validation = {
            "status": "FAIL",
            "issue_count": 1,
            "warning_count": 0,
            "issues": [{"code": "p207_validator_refusal", "message": str(exc)}],
            "warnings": [],
        }
    return {
        "status": "PASS" if not issues and p207_validation["status"] == "PASS" else "FAIL",
        "row_count": len(rows),
        "issue_count": len(issues),
        "warning_count": len(warnings),
        "issues": issues,
        "warnings": warnings,
        "p207_validation_status": p207_validation["status"],
        "p207_issue_count": p207_validation["issue_count"],
        "p207_warning_count": p207_validation["warning_count"],
        "p207_issues": p207_validation.get("issues", []),
        "p207_warnings": p207_validation.get("warnings", []),
        "invalid_value_rows": invalid_rows,
        "reviewer_note_label_text_rows": reviewer_note_label_text_rows,
        "prohibited_columns_present": prohibited,
        "unsafe_extra_columns_present": sorted(extra_unsafe),
    }


def summarize_blocker_rates(rows: list[dict[str, str]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for group_field in GROUP_FIELDS:
        grouped: dict[str, Counter[str]] = defaultdict(Counter)
        for row in rows:
            key = str(row.get(group_field) or "")
            blocker = str(row.get("quality_blocker") or "")
            grouped[key]["rows"] += 1
            grouped[key]["yes"] += int(blocker == "yes")
            grouped[key]["no"] += int(blocker == "no")
            grouped[key]["blank"] += int(blocker == "")
            grouped[key]["invalid"] += int(blocker not in {"", "no", "yes"})
        output[group_field] = {
            key: {
                "rows": counts["rows"],
                "quality_blocker_yes": counts["yes"],
                "quality_blocker_no": counts["no"],
                "quality_blocker_blank": counts["blank"],
                "quality_blocker_invalid": counts["invalid"],
                "quality_blocker_yes_rate": round(counts["yes"] / counts["rows"], 6) if counts["rows"] else 0.0,
            }
            for key, counts in sorted(grouped.items())
        }
    return output


def build_blocker_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in rows:
        if str(row.get("quality_blocker") or "") != "yes":
            continue
        out.append({column: str(row.get(column) or "") for column in BLOCKER_ROW_COLUMNS})
    return out


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    validation = payload["validation"]
    lines = [
        "# P208 Evidence-Quality Notes Summary",
        "",
        f"**Status:** `{payload['status']}`; P195 remains `{payload['p195_status']}`.",
        "",
        "## Scope",
        "",
        "P208 summarizes P207 evidence-quality notes only. It reports blank counts, allowed-value distributions, and quality-blocker rates. It does not create admission labels, same-object labels, training data, or admission-control claims.",
        "",
        "## Current Results",
        "",
        f"- Rows: {summary['rows']}",
        f"- All note fields blank: {summary['all_note_fields_blank']}",
        f"- Quality blockers: {summary['quality_blocker_yes_count']} yes / {summary['rows']} rows",
        f"- Validation: {validation['status']} ({validation['issue_count']} issues, {validation['warning_count']} warnings)",
        f"- Prohibited label/proxy columns present: {', '.join(validation['prohibited_columns_present']) if validation['prohibited_columns_present'] else 'none'}",
        f"- Reviewer notes with admission/same-object-like text: {len(validation['reviewer_note_label_text_rows'])}",
        "",
        "## Note Field Distributions",
        "",
    ]
    for column, distribution in summary["note_field_distributions"].items():
        rendered = ", ".join(f"{key}={value}" for key, value in distribution.items())
        lines.append(f"- `{column}`: {rendered}")
    lines.extend(["", "## Quality Blocker Rates", ""])
    for group_field in GROUP_FIELDS:
        lines.append(f"### By `{group_field}`")
        for key, item in summary["quality_blocker_rates_by"][group_field].items():
            display = key if key else "(blank)"
            lines.append(
                f"- {display}: {item['quality_blocker_yes']}/{item['rows']} yes "
                f"(rate={item['quality_blocker_yes_rate']:.6f}, blank={item['quality_blocker_blank']})"
            )
        lines.append("")
    lines.extend(
        [
            "## Rows Requiring Attention",
            "",
            f"- Rows with `quality_blocker=yes`: {summary['quality_blocker_yes_count']}",
            f"- Rows with invalid allowed values: {len(validation['invalid_value_rows'])}",
            f"- Rows with possible label-decision text in `reviewer_note`: {len(validation['reviewer_note_label_text_rows'])}",
            "",
            "## Scientific Boundary",
            "",
            "P208 is read-only evidence-quality QA. It does not fill or infer `human_admit_label` or `human_same_object_label`, does not use weak/model/selection fields as labels, does not train, and does not alter raw images or data.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def summarize(notes_csv: Path, summary_json: Path, summary_md: Path, blockers_csv: Path) -> dict[str, Any]:
    rows, columns = read_csv(notes_csv)
    validation = validate_notes(rows, columns)
    note_blank_counts = {column: sum(1 for row in rows if not str(row.get(column) or "")) for column in NOTE_FIELDS}
    distributions = {column: count_distribution(rows, column) for column in NOTE_FIELDS}
    quality_blocker_rows = build_blocker_rows(rows)
    summary = {
        "rows": len(rows),
        "note_blank_counts": note_blank_counts,
        "all_note_fields_blank": all(count == len(rows) for count in note_blank_counts.values()),
        "note_field_distributions": distributions,
        "quality_blocker_yes_count": len(quality_blocker_rows),
        "quality_blocker_yes_rate": round(len(quality_blocker_rows) / len(rows), 6) if rows else 0.0,
        "quality_blocker_rates_by": summarize_blocker_rates(rows),
        "category_counts": dict(sorted(Counter(str(row.get("canonical_label") or "") for row in rows).items())),
        "source_counts": dict(sorted(Counter(str(row.get("source") or "") for row in rows).items())),
        "row_source_counts": dict(sorted(Counter(str(row.get("row_source") or "") for row in rows).items())),
        "session_counts": dict(sorted(Counter(str(row.get("session_id") or "") for row in rows).items())),
    }
    payload = {
        "phase": "P208-evidence-quality-notes-summary",
        "status": "PASS" if validation["status"] == "PASS" else "FAIL",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {"notes_csv": rel(notes_csv)},
        "outputs": {"summary_json": rel(summary_json), "summary_md": rel(summary_md), "blockers_csv": rel(blockers_csv)},
        "p195_status": "BLOCKED",
        "scientific_boundary": (
            "Read-only evidence-quality notes QA only. P208 summarizes allowed P207 quality fields and "
            "quality_blocker rates; it creates no admission or same-object labels, does not use weak/model/"
            "selection fields as labels, does not train, and does not alter raw evidence."
        ),
        "constraints_observed": {
            "human_admit_label_created_or_filled": False,
            "human_same_object_label_created_or_filled": False,
            "weak_admission_or_model_predictions_used_as_labels": False,
            "admission_or_semantic_stability_training_performed": False,
            "downloads_performed": False,
            "raw_images_or_data_modified": False,
        },
        "schema": {
            "note_columns": NOTE_FIELDS,
            "allowed_values": p207.ALLOWED_VALUES,
            "quality_blocker_group_fields": GROUP_FIELDS,
        },
        "summary": summary,
        "validation": validation,
        "quality_blocker_rows": quality_blocker_rows,
        "rows_requiring_attention": {
            "quality_blocker_rows": quality_blocker_rows,
            "invalid_value_rows": validation["invalid_value_rows"],
            "reviewer_note_label_text_rows": validation["reviewer_note_label_text_rows"],
        },
    }
    write_json(summary_json, payload)
    write_markdown(summary_md, payload)
    write_csv(blockers_csv, quality_blocker_rows, BLOCKER_ROW_COLUMNS)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize P207 evidence-quality notes without creating labels")
    parser.add_argument("--notes-csv", default=str(DEFAULT_NOTES_CSV))
    parser.add_argument("--summary-json", default=str(DEFAULT_SUMMARY_JSON))
    parser.add_argument("--summary-md", default=str(DEFAULT_SUMMARY_MD))
    parser.add_argument("--blockers-csv", default=str(DEFAULT_BLOCKERS_CSV))
    args = parser.parse_args()

    payload = summarize(
        repo_path(args.notes_csv),
        repo_path(args.summary_json),
        repo_path(args.summary_md),
        repo_path(args.blockers_csv),
    )
    print(
        json.dumps(
            {
                "status": payload["status"],
                "rows": payload["summary"]["rows"],
                "all_note_fields_blank": payload["summary"]["all_note_fields_blank"],
                "quality_blocker_yes_count": payload["summary"]["quality_blocker_yes_count"],
                "validation_status": payload["validation"]["status"],
                "issue_count": payload["validation"]["issue_count"],
                "warning_count": payload["validation"]["warning_count"],
                "p195_status": payload["p195_status"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if payload["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
