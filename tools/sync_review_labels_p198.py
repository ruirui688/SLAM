#!/usr/bin/env python3
"""P198 safe sync for human labels from P197 review CSVs into P194 sources.

This tool is intentionally a guardrail, not a labeler. It validates rows filled
by a human reviewer and, only with ``--apply``, copies reviewed ``human_*``
columns back to the P194 CSVs consumed by the P195 independent-label gate.
Semantic hints, weak labels, model outputs, and categories are never converted
into labels.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_BOUNDARY_SOURCE = Path("paper/evidence/admission_boundary_label_sheet_p194.csv")
DEFAULT_PAIR_SOURCE = Path("paper/evidence/association_pair_candidates_p194.csv")
DEFAULT_BOUNDARY_REVIEWED = Path("paper/evidence/admission_boundary_label_sheet_p197_semantic_review.csv")
DEFAULT_PAIR_REVIEWED = Path("paper/evidence/association_pair_candidates_p197_semantic_review.csv")
DEFAULT_OUTPUT_JSON = Path("paper/evidence/review_label_sync_p198.json")
DEFAULT_OUTPUT_MD = Path("paper/export/review_label_sync_p198.md")

BOUNDARY_LABEL = "human_admit_label"
PAIR_LABEL = "human_same_object_label"
BOUNDARY_CONFIDENCE = "human_label_confidence"
BOUNDARY_NOTES = "human_notes"


def repo_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def norm(value: Any) -> str:
    return str(value if value is not None else "").strip()


def nonblank_binary_labels(rows: list[dict[str, str]], column: str) -> list[str]:
    return [norm(row.get(column, "")) for row in rows if norm(row.get(column, "")) != ""]


def validate_key(rows: list[dict[str, str]], key: str, label: str, errors: list[str]) -> dict[str, Any]:
    if not rows:
        errors.append(f"{label}: no rows found")
        return {"rows": 0, "unique": 0, "duplicates": []}
    if key not in rows[0]:
        errors.append(f"{label}: required key column `{key}` is missing")
        return {"rows": len(rows), "unique": 0, "duplicates": []}
    values = [norm(row.get(key, "")) for row in rows]
    blanks = [i + 2 for i, value in enumerate(values) if not value]
    if blanks:
        errors.append(f"{label}: blank `{key}` values at CSV rows {blanks[:10]}")
    counts = Counter(values)
    duplicates = sorted(value for value, count in counts.items() if value and count > 1)
    if duplicates:
        errors.append(f"{label}: duplicate `{key}` values: {duplicates[:10]}")
    return {"rows": len(rows), "unique": len([v for v in counts if v]), "duplicates": duplicates}


def ensure_columns(columns: list[str], required: list[str], label: str, errors: list[str]) -> None:
    missing = [column for column in required if column not in columns]
    if missing:
        errors.append(f"{label}: missing required columns {missing}")


def validate_labels(
    rows: list[dict[str, str]],
    label_column: str,
    label_name: str,
    allowed_confidence: set[str],
    errors: list[str],
    warnings: list[str],
    *,
    confidence_column: str | None = None,
    notes_column: str | None = None,
) -> dict[str, int]:
    blank = valid = invalid = 0
    confidence_invalid = 0
    low_without_notes = 0
    for index, row in enumerate(rows, start=2):
        label_value = norm(row.get(label_column, ""))
        if label_value == "":
            blank += 1
        elif label_value in {"0", "1"}:
            valid += 1
        else:
            invalid += 1
            errors.append(f"{label_name}: invalid `{label_column}` value {label_value!r} at CSV row {index}")

        if confidence_column and confidence_column in row:
            confidence_value = norm(row.get(confidence_column, "")).lower()
            if confidence_value not in allowed_confidence:
                confidence_invalid += 1
                errors.append(
                    f"{label_name}: invalid `{confidence_column}` value {confidence_value!r} at CSV row {index}"
                )
            if label_value in {"0", "1"} and confidence_value == "low" and notes_column:
                if not norm(row.get(notes_column, "")):
                    low_without_notes += 1
    if low_without_notes:
        warnings.append(f"{label_name}: {low_without_notes} low-confidence nonblank labels have no notes")
    return {
        "total": len(rows),
        "blank": blank,
        "valid": valid,
        "invalid": invalid,
        "confidence_invalid": confidence_invalid,
    }


def validate_identity(
    source_rows: list[dict[str, str]],
    reviewed_rows: list[dict[str, str]],
    *,
    key: str,
    identity_columns: list[str],
    label: str,
    errors: list[str],
) -> dict[str, Any]:
    source_by_key = {norm(row.get(key, "")): row for row in source_rows}
    reviewed_by_key = {norm(row.get(key, "")): row for row in reviewed_rows}
    missing_in_review = sorted(set(source_by_key) - set(reviewed_by_key))
    extra_in_review = sorted(set(reviewed_by_key) - set(source_by_key))
    if missing_in_review:
        errors.append(f"{label}: reviewed CSV missing source keys: {missing_in_review[:10]}")
    if extra_in_review:
        errors.append(f"{label}: reviewed CSV has unknown keys: {extra_in_review[:10]}")

    mismatches: list[dict[str, str]] = []
    for row_key in sorted(set(source_by_key) & set(reviewed_by_key)):
        source = source_by_key[row_key]
        reviewed = reviewed_by_key[row_key]
        for column in identity_columns:
            if norm(source.get(column, "")) != norm(reviewed.get(column, "")):
                mismatches.append(
                    {
                        "key": row_key,
                        "column": column,
                        "source": norm(source.get(column, "")),
                        "reviewed": norm(reviewed.get(column, "")),
                    }
                )
    if mismatches:
        errors.append(f"{label}: row identity mismatches: {mismatches[:10]}")
    return {
        "missing_in_review": len(missing_in_review),
        "extra_in_review": len(extra_in_review),
        "identity_mismatches": len(mismatches),
    }


def shortcut_warning(
    rows: list[dict[str, str]],
    *,
    label_column: str,
    shortcut_column: str,
    label: str,
    warnings: list[str],
) -> dict[str, Any]:
    pairs = [
        (norm(row.get(label_column, "")), norm(row.get(shortcut_column, "")))
        for row in rows
        if norm(row.get(label_column, "")) in {"0", "1"} and shortcut_column in row
    ]
    if pairs and all(human == shortcut for human, shortcut in pairs):
        warnings.append(
            f"{label}: every nonblank `{label_column}` exactly equals `{shortcut_column}`; verify this was not copied"
        )
    return {"nonblank_compared": len(pairs), "all_equal": bool(pairs) and all(a == b for a, b in pairs)}


def single_class_check(
    rows: list[dict[str, str]],
    *,
    label_column: str,
    label: str,
    allow_single_class: bool,
    errors: list[str],
) -> dict[str, Any]:
    labels = nonblank_binary_labels(rows, label_column)
    classes = sorted(set(labels))
    if labels and len(classes) == 1 and not allow_single_class:
        errors.append(f"{label}: all nonblank `{label_column}` labels are class {classes[0]!r}; use --allow-single-class to permit")
    return {"nonblank": len(labels), "classes": classes, "counts": dict(Counter(labels))}


def copy_fields(
    source_rows: list[dict[str, str]],
    reviewed_rows: list[dict[str, str]],
    *,
    key: str,
    fields: list[str],
    label_column: str,
) -> dict[str, Any]:
    reviewed_by_key = {norm(row.get(key, "")): row for row in reviewed_rows}
    changed_cells = 0
    nonblank_labels_copied = 0
    for row in source_rows:
        reviewed = reviewed_by_key[norm(row.get(key, ""))]
        for field in fields:
            value = reviewed.get(field, "")
            if row.get(field, "") != value:
                changed_cells += 1
                row[field] = value
        if norm(reviewed.get(label_column, "")) in {"0", "1"}:
            nonblank_labels_copied += 1
    return {"changed_cells": changed_cells, "nonblank_labels_copied": nonblank_labels_copied}


def backup_file(path: Path, backup_dir: Path, timestamp: str) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / f"{path.stem}.{timestamp}{path.suffix}"
    shutil.copy2(path, backup)
    return backup


def run_gate() -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "tools/prepare_independent_supervision_p195.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    status = None
    parsed: dict[str, Any] | None = None
    try:
        parsed = json.loads(proc.stdout)
        status = parsed.get("status")
    except json.JSONDecodeError:
        pass
    return {
        "command": f"{sys.executable} tools/prepare_independent_supervision_p195.py",
        "returncode": proc.returncode,
        "status": status,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
        "parsed": parsed,
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# P198 Review Label Sync",
        "",
        f"**Status:** {payload['status']}",
        f"**Mode:** {payload['mode']}",
        f"**Decision:** {payload['decision']}",
        "",
        "## Label Counts",
        "",
        f"- Boundary labels copied: {payload['sync_plan']['boundary']['nonblank_labels_copied']}",
        f"- Pair labels copied: {payload['sync_plan']['pairs']['nonblank_labels_copied']}",
        f"- Boundary reviewed labels: {payload['validation']['boundary_labels']}",
        f"- Pair reviewed labels: {payload['validation']['pair_labels']}",
        "",
        "## Validation",
        "",
        f"- Errors: {len(payload['errors'])}",
        f"- Warnings: {len(payload['warnings'])}",
    ]
    if payload["errors"]:
        lines += ["", "### Errors", ""]
        lines += [f"- {error}" for error in payload["errors"]]
    if payload["warnings"]:
        lines += ["", "### Warnings", ""]
        lines += [f"- {warning}" for warning in payload["warnings"]]
    if payload.get("backups"):
        lines += ["", "## Backups", ""]
        lines += [f"- `{backup}`" for backup in payload["backups"]]
    if payload.get("gate_result"):
        gate = payload["gate_result"]
        lines += [
            "",
            "## P195 Gate",
            "",
            f"- Return code: {gate['returncode']}",
            f"- Status: {gate.get('status')}",
        ]
        parsed = gate.get("parsed") or {}
        reasons = (parsed.get("block_reasons") or (parsed.get("gate") or {}).get("block_reasons") or [])[:10]
        if reasons:
            lines += ["- Blocking reasons:"]
            lines += [f"  - {reason}" for reason in reasons]
    lines += [
        "",
        "## Scientific Boundary",
        "",
        "P198 only validates and synchronizes human-filled `human_*` fields. It does not infer labels from semantic hints, categories, weak labels, model predictions, or proxy fields.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boundary-source", default=str(DEFAULT_BOUNDARY_SOURCE))
    parser.add_argument("--pair-source", default=str(DEFAULT_PAIR_SOURCE))
    parser.add_argument("--boundary-reviewed", default=str(DEFAULT_BOUNDARY_REVIEWED))
    parser.add_argument("--pair-reviewed", default=str(DEFAULT_PAIR_REVIEWED))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--backup-dir", default="paper/evidence/backups")
    parser.add_argument("--confidence-values", default=",high,medium,low", help="Comma-separated allowed values; include an empty item for blank")
    parser.add_argument("--allow-single-class", action="store_true")
    parser.add_argument("--apply", action="store_true", help="Write validated human_* columns back to P194 source CSVs")
    parser.add_argument("--run-gate", action="store_true", help="Run P195 gate after validation/sync")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    errors: list[str] = []
    warnings: list[str] = []

    boundary_source = repo_path(args.boundary_source)
    pair_source = repo_path(args.pair_source)
    boundary_reviewed = repo_path(args.boundary_reviewed)
    pair_reviewed = repo_path(args.pair_reviewed)
    output_json = repo_path(args.output_json)
    output_md = repo_path(args.output_md)
    backup_dir = repo_path(args.backup_dir)
    allowed_confidence = {value.strip().lower() for value in args.confidence_values.split(",")}

    for path in [boundary_source, pair_source, boundary_reviewed, pair_reviewed]:
        if not path.exists():
            errors.append(f"missing input file: {rel(path)}")

    if errors:
        payload = {
            "phase": "P198-review-label-sync",
            "status": "INVALID",
            "mode": "apply" if args.apply else "dry-run",
            "decision": "input files are missing; no CSVs were modified",
            "errors": errors,
            "warnings": warnings,
            "validation": {},
            "sync_plan": {"boundary": {"changed_cells": 0, "nonblank_labels_copied": 0}, "pairs": {"changed_cells": 0, "nonblank_labels_copied": 0}},
            "backups": [],
            "gate_result": None,
        }
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        write_markdown(output_md, payload)
        print(json.dumps({"status": "INVALID", "errors": errors}, indent=2))
        return 2

    boundary_source_columns, boundary_source_rows = read_csv(boundary_source)
    pair_source_columns, pair_source_rows = read_csv(pair_source)
    boundary_reviewed_columns, boundary_reviewed_rows = read_csv(boundary_reviewed)
    pair_reviewed_columns, pair_reviewed_rows = read_csv(pair_reviewed)

    ensure_columns(boundary_source_columns, ["review_id", "sample_id", BOUNDARY_LABEL], "boundary source", errors)
    ensure_columns(boundary_reviewed_columns, ["review_id", "sample_id", BOUNDARY_LABEL], "boundary reviewed", errors)
    ensure_columns(pair_source_columns, ["pair_id", "sample_id_a", "sample_id_b", PAIR_LABEL], "pair source", errors)
    ensure_columns(pair_reviewed_columns, ["pair_id", "sample_id_a", "sample_id_b", PAIR_LABEL], "pair reviewed", errors)

    validation: dict[str, Any] = {
        "boundary_source_key": validate_key(boundary_source_rows, "review_id", "boundary source", errors),
        "boundary_reviewed_key": validate_key(boundary_reviewed_rows, "review_id", "boundary reviewed", errors),
        "pair_source_key": validate_key(pair_source_rows, "pair_id", "pair source", errors),
        "pair_reviewed_key": validate_key(pair_reviewed_rows, "pair_id", "pair reviewed", errors),
        "boundary_identity": validate_identity(
            boundary_source_rows,
            boundary_reviewed_rows,
            key="review_id",
            identity_columns=["sample_id"],
            label="boundary",
            errors=errors,
        ),
        "pair_identity": validate_identity(
            pair_source_rows,
            pair_reviewed_rows,
            key="pair_id",
            identity_columns=["sample_id_a", "sample_id_b"],
            label="pairs",
            errors=errors,
        ),
        "boundary_labels": validate_labels(
            boundary_reviewed_rows,
            BOUNDARY_LABEL,
            "boundary reviewed",
            allowed_confidence,
            errors,
            warnings,
            confidence_column=BOUNDARY_CONFIDENCE,
            notes_column=BOUNDARY_NOTES,
        ),
        "pair_labels": validate_labels(
            pair_reviewed_rows,
            PAIR_LABEL,
            "pair reviewed",
            allowed_confidence,
            errors,
            warnings,
        ),
        "boundary_shortcut": shortcut_warning(
            boundary_reviewed_rows,
            label_column=BOUNDARY_LABEL,
            shortcut_column="current_weak_label",
            label="boundary reviewed",
            warnings=warnings,
        ),
        "pair_shortcut": shortcut_warning(
            pair_reviewed_rows,
            label_column=PAIR_LABEL,
            shortcut_column="same_weak_label",
            label="pair reviewed",
            warnings=warnings,
        ),
        "boundary_class_check": single_class_check(
            boundary_reviewed_rows,
            label_column=BOUNDARY_LABEL,
            label="boundary reviewed",
            allow_single_class=args.allow_single_class,
            errors=errors,
        ),
        "pair_class_check": single_class_check(
            pair_reviewed_rows,
            label_column=PAIR_LABEL,
            label="pair reviewed",
            allow_single_class=args.allow_single_class,
            errors=errors,
        ),
    }

    boundary_human_fields = [field for field in boundary_source_columns if field.startswith("human_") and field in boundary_reviewed_columns]
    pair_human_fields = [field for field in pair_source_columns if field.startswith("human_") and field in pair_reviewed_columns]
    if BOUNDARY_LABEL not in boundary_human_fields:
        errors.append(f"boundary: `{BOUNDARY_LABEL}` is not available for sync")
    if PAIR_LABEL not in pair_human_fields:
        errors.append(f"pairs: `{PAIR_LABEL}` is not available for sync")

    sync_plan = {
        "boundary": copy_fields(
            [dict(row) for row in boundary_source_rows],
            boundary_reviewed_rows,
            key="review_id",
            fields=boundary_human_fields,
            label_column=BOUNDARY_LABEL,
        )
        if not errors
        else {"changed_cells": 0, "nonblank_labels_copied": 0},
        "pairs": copy_fields(
            [dict(row) for row in pair_source_rows],
            pair_reviewed_rows,
            key="pair_id",
            fields=pair_human_fields,
            label_column=PAIR_LABEL,
        )
        if not errors
        else {"changed_cells": 0, "nonblank_labels_copied": 0},
    }

    backups: list[str] = []
    applied = False
    if args.apply and not errors:
        timestamp = utc_timestamp()
        backups = [
            rel(backup_file(boundary_source, backup_dir, timestamp)),
            rel(backup_file(pair_source, backup_dir, timestamp)),
        ]
        boundary_copy = [dict(row) for row in boundary_source_rows]
        pair_copy = [dict(row) for row in pair_source_rows]
        copy_fields(boundary_copy, boundary_reviewed_rows, key="review_id", fields=boundary_human_fields, label_column=BOUNDARY_LABEL)
        copy_fields(pair_copy, pair_reviewed_rows, key="pair_id", fields=pair_human_fields, label_column=PAIR_LABEL)
        write_csv(boundary_source, boundary_source_columns, boundary_copy)
        write_csv(pair_source, pair_source_columns, pair_copy)
        applied = True

    gate_result = run_gate() if args.run_gate and not errors else None
    status = "INVALID" if errors else "VALID"
    mode = "apply" if args.apply else "dry-run"
    if errors:
        decision = "validation failed; no CSVs were modified"
    elif applied:
        decision = "validated and copied only reviewed human_* fields into P194 source CSVs"
    else:
        decision = "validated only; dry-run made no source CSV changes"

    payload = {
        "phase": "P198-review-label-sync",
        "status": status,
        "mode": mode,
        "decision": decision,
        "timestamp_utc": utc_timestamp(),
        "inputs": {
            "boundary_source": rel(boundary_source),
            "pair_source": rel(pair_source),
            "boundary_reviewed": rel(boundary_reviewed),
            "pair_reviewed": rel(pair_reviewed),
        },
        "outputs": {"json": rel(output_json), "markdown": rel(output_md)},
        "sync_fields": {"boundary": boundary_human_fields, "pairs": pair_human_fields},
        "validation": validation,
        "sync_plan": sync_plan,
        "errors": errors,
        "warnings": warnings,
        "backups": backups,
        "gate_result": gate_result,
        "constraints_observed": [
            "dry-run by default",
            "no fabricated labels",
            "no semantic hints, categories, weak labels, or model outputs converted into labels",
            "apply mode creates timestamped backups before writing",
            "only human_* columns are copied from reviewed rows keyed by review_id/pair_id",
        ],
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(output_md, payload)
    print(
        json.dumps(
            {
                "status": status,
                "mode": mode,
                "decision": decision,
                "boundary_labels_copied": sync_plan["boundary"]["nonblank_labels_copied"],
                "pair_labels_copied": sync_plan["pairs"]["nonblank_labels_copied"],
                "errors": errors,
                "warnings": warnings,
                "gate_status": gate_result.get("status") if gate_result else None,
                "outputs": payload["outputs"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if status == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
