#!/usr/bin/env python3
"""P209 regression tests for P207/P208 evidence-quality safety checks.

The harness copies the P207 notes CSV into a temporary directory, mutates only
the temporary copy, and exercises P207 validation plus P208 summary behavior.
It does not edit real notes, create human labels, train, download, or touch raw
evidence files.
"""
from __future__ import annotations

import csv
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any, Callable

import build_evidence_quality_notes_p207 as p207
import summarize_evidence_quality_notes_p208 as p208


ROOT = Path(__file__).resolve().parents[1]
REAL_NOTES_CSV = ROOT / "paper/evidence/raw_evidence_quality_notes_p207.csv"
DEFAULT_OUTPUT_JSON = ROOT / "paper/evidence/evidence_quality_safety_tests_p209.json"
DEFAULT_OUTPUT_MD = ROOT / "paper/export/evidence_quality_safety_tests_p209.md"


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
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


def run_p207_validation(notes_csv: Path) -> dict[str, Any]:
    try:
        payload = p207.validate(notes_csv)
        validation = payload["validation"]
        return {
            "status": payload["status"],
            "issue_count": validation["issue_count"],
            "warning_count": validation["warning_count"],
            "issue_codes": compact_issue_codes(validation.get("issues", [])),
            "warning_codes": compact_issue_codes(validation.get("warnings", [])),
            "note_fields_blank": validation.get("note_fields_blank"),
        }
    except SystemExit as exc:
        return {
            "status": "FAIL",
            "issue_count": 1,
            "warning_count": 0,
            "issue_codes": ["p207_validator_refusal"],
            "warning_codes": [],
            "note_fields_blank": None,
            "refusal": str(exc),
        }


def run_p208_summary(notes_csv: Path, output_dir: Path, case_name: str) -> dict[str, Any]:
    payload = p208.summarize(
        notes_csv,
        output_dir / f"{case_name}_summary.json",
        output_dir / f"{case_name}_summary.md",
        output_dir / f"{case_name}_blockers.csv",
    )
    validation = payload["validation"]
    summary = payload["summary"]
    return {
        "status": payload["status"],
        "validation_status": validation["status"],
        "issue_count": validation["issue_count"],
        "warning_count": validation["warning_count"],
        "issue_codes": compact_issue_codes(validation.get("issues", [])),
        "warning_codes": compact_issue_codes(validation.get("warnings", [])),
        "p207_validation_status": validation["p207_validation_status"],
        "p207_issue_count": validation["p207_issue_count"],
        "p207_warning_count": validation["p207_warning_count"],
        "p207_issue_codes": compact_issue_codes(validation.get("p207_issues", [])),
        "invalid_value_rows": len(validation["invalid_value_rows"]),
        "reviewer_note_label_text_rows": len(validation["reviewer_note_label_text_rows"]),
        "prohibited_columns_present": validation["prohibited_columns_present"],
        "unsafe_extra_columns_present": validation["unsafe_extra_columns_present"],
        "rows": summary["rows"],
        "all_note_fields_blank": summary["all_note_fields_blank"],
        "quality_blocker_yes_count": summary["quality_blocker_yes_count"],
        "quality_blocker_rows": [
            {
                "audit_sample_id": row.get("audit_sample_id", ""),
                "quality_blocker": row.get("quality_blocker", ""),
                "visibility_quality": row.get("visibility_quality", ""),
                "reviewer_note": row.get("reviewer_note", ""),
            }
            for row in payload["quality_blocker_rows"]
        ],
        "note_field_distributions": summary["note_field_distributions"],
    }


def mutate_invalid_allowed_value(rows: list[dict[str, str]], columns: list[str]) -> tuple[list[dict[str, str]], list[str]]:
    rows[0]["visibility_quality"] = "opaque"
    return rows, columns


def mutate_prohibited_column(rows: list[dict[str, str]], columns: list[str]) -> tuple[list[dict[str, str]], list[str]]:
    columns = columns + ["human_admit_label"]
    rows[0]["human_admit_label"] = ""
    return rows, columns


def mutate_reviewer_note_label_text(rows: list[dict[str, str]], columns: list[str]) -> tuple[list[dict[str, str]], list[str]]:
    rows[0]["reviewer_note"] = "Evidence looks clear, but do not admit/reject in this field."
    return rows, columns


def mutate_quality_blocker(rows: list[dict[str, str]], columns: list[str]) -> tuple[list[dict[str, str]], list[str]]:
    rows[0]["visibility_quality"] = "poor"
    rows[0]["quality_blocker"] = "yes"
    rows[0]["reviewer_note"] = "Evidence quality blocks visual inspection."
    return rows, columns


def mutate_allowed_distributions(rows: list[dict[str, str]], columns: list[str]) -> tuple[list[dict[str, str]], list[str]]:
    rows[0]["occlusion_level"] = "low"
    rows[0]["blur_level"] = "none"
    rows[0]["quality_blocker"] = "no"
    return rows, columns


def expect_baseline(result: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if result["p207"]["status"] != "PASS":
        failures.append("P207 baseline validation did not pass")
    if result["p208"]["status"] != "PASS":
        failures.append("P208 baseline summary did not pass")
    if result["p208"]["all_note_fields_blank"] is not True:
        failures.append("P208 did not report all note fields blank")
    return not failures, failures


def expect_invalid_allowed_value(result: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if result["p207"]["status"] != "FAIL" or "invalid_allowed_value" not in result["p207"]["issue_codes"]:
        failures.append("P207 did not fail on invalid allowed value")
    if result["p208"]["status"] != "FAIL" or result["p208"]["invalid_value_rows"] != 1:
        failures.append("P208 did not report exactly one invalid allowed-value row")
    return not failures, failures


def expect_prohibited_column(result: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if result["p207"]["status"] != "FAIL" or "p207_validator_refusal" not in result["p207"]["issue_codes"]:
        failures.append("P207 did not refuse the prohibited column")
    if result["p208"]["status"] != "FAIL" or result["p208"]["prohibited_columns_present"] != ["human_admit_label"]:
        failures.append("P208 did not report the prohibited human_admit_label column")
    return not failures, failures


def expect_reviewer_note_label_text(result: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if result["p207"]["status"] != "FAIL" or "possible_label_decision_text" not in result["p207"]["issue_codes"]:
        failures.append("P207 did not detect reviewer-note label-decision text")
    if result["p208"]["status"] != "FAIL" or result["p208"]["reviewer_note_label_text_rows"] != 1:
        failures.append("P208 did not report exactly one reviewer-note label-decision row")
    return not failures, failures


def expect_quality_blocker(result: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if result["p207"]["status"] != "PASS":
        failures.append("P207 rejected a valid quality_blocker=yes row")
    if result["p208"]["status"] != "PASS":
        failures.append("P208 rejected a valid quality_blocker=yes row")
    if result["p208"]["quality_blocker_yes_count"] != 1:
        failures.append("P208 did not count exactly one quality blocker")
    if len(result["p208"]["quality_blocker_rows"]) != 1:
        failures.append("P208 did not emit exactly one blocker summary row")
    return not failures, failures


def expect_allowed_distributions(result: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    distributions = result["p208"]["note_field_distributions"]
    if result["p208"]["status"] != "PASS":
        failures.append("P208 rejected allowed low/none/no values")
    if distributions["occlusion_level"].get("low") != 1:
        failures.append("P208 did not count occlusion_level=low")
    if distributions["blur_level"].get("none") != 1:
        failures.append("P208 did not count blur_level=none")
    if distributions["quality_blocker"].get("no") != 1:
        failures.append("P208 did not count quality_blocker=no")
    return not failures, failures


CASE_SPECS: list[dict[str, Any]] = [
    {
        "name": "baseline_blank_notes_pass",
        "description": "Unmodified temporary P207 notes copy passes P207 validation and P208 summary.",
        "mutator": None,
        "expect": expect_baseline,
    },
    {
        "name": "invalid_allowed_value_fails",
        "description": "A non-domain visibility_quality value is rejected.",
        "mutator": mutate_invalid_allowed_value,
        "expect": expect_invalid_allowed_value,
    },
    {
        "name": "prohibited_label_proxy_column_fails",
        "description": "Adding human_admit_label to the temporary CSV is rejected.",
        "mutator": mutate_prohibited_column,
        "expect": expect_prohibited_column,
    },
    {
        "name": "reviewer_note_label_decision_text_detected",
        "description": "Admission/rejection wording in reviewer_note is detected as unsafe.",
        "mutator": mutate_reviewer_note_label_text,
        "expect": expect_reviewer_note_label_text,
    },
    {
        "name": "quality_blocker_yes_summary_row",
        "description": "A valid quality_blocker=yes note is counted and emitted in blocker rows.",
        "mutator": mutate_quality_blocker,
        "expect": expect_quality_blocker,
    },
    {
        "name": "allowed_low_none_quality_distributions_counted",
        "description": "Allowed low/none/no values are accepted and counted in distributions.",
        "mutator": mutate_allowed_distributions,
        "expect": expect_allowed_distributions,
    },
]


def run_case(
    spec: dict[str, Any],
    base_rows: list[dict[str, str]],
    base_columns: list[str],
    output_dir: Path,
) -> dict[str, Any]:
    rows = [dict(row) for row in base_rows]
    columns = list(base_columns)
    mutator: Callable[[list[dict[str, str]], list[str]], tuple[list[dict[str, str]], list[str]]] | None = spec["mutator"]
    if mutator is not None:
        rows, columns = mutator(rows, columns)

    notes_csv = output_dir / f"{spec['name']}.csv"
    write_csv(notes_csv, rows, columns)
    result = {
        "name": spec["name"],
        "description": spec["description"],
        "temp_notes_csv_name": notes_csv.name,
        "p207": run_p207_validation(notes_csv),
        "p208": run_p208_summary(notes_csv, output_dir, spec["name"]),
    }
    ok, failures = spec["expect"](result)
    result["expected_outcome_met"] = ok
    result["expectation_failures"] = failures
    return result


def build_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# P209 Evidence-Quality Safety Regression Tests",
        "",
        f"**Status:** `{payload['status']}`; P195 remains `{payload['p195_status']}`.",
        "",
        "## Scope",
        "",
        "P209 tests P207/P208 evidence-quality tooling with temporary synthetic copies of the P207 notes CSV only. It creates no labels, performs no training, downloads nothing, and does not modify real P207/P194/P196 label files.",
        "",
        "## Results",
        "",
    ]
    for case in payload["cases"]:
        marker = "PASS" if case["expected_outcome_met"] else "FAIL"
        lines.extend(
            [
                f"### {case['name']}",
                f"- Expected outcome: `{marker}`",
                f"- P207: `{case['p207']['status']}`; issues={case['p207']['issue_count']}; warnings={case['p207']['warning_count']}; codes={case['p207']['issue_codes'] or ['none']}",
                f"- P208: `{case['p208']['status']}`; issues={case['p208']['issue_count']}; warnings={case['p208']['warning_count']}; blocker_yes={case['p208']['quality_blocker_yes_count']}; label_text_rows={case['p208']['reviewer_note_label_text_rows']}",
            ]
        )
        if case["expectation_failures"]:
            lines.append(f"- Failures: {'; '.join(case['expectation_failures'])}")
        lines.append("")
    lines.extend(
        [
            "## Real-File Safety Checks",
            "",
            f"- Real P207 notes hash unchanged: `{payload['real_p207_notes_hash_unchanged']}`",
            f"- Real P207 note fields blank before/after harness: `{payload['real_p207_notes_blank_before_and_after']}`",
            "- Human label files were not opened for writing by this harness.",
            "",
            "## Scientific Boundary",
            "",
            "These tests validate safety behavior in evidence-quality tooling only. They do not fill or infer `human_admit_label` or `human_same_object_label`, do not train, and do not support admission-control claims.",
            "",
        ]
    )
    return "\n".join(lines)


def real_notes_all_blank(rows: list[dict[str, str]]) -> bool:
    return all(all(str(row.get(column) or "") == "" for column in p207.NOTE_COLUMNS) for row in rows)


def main() -> int:
    base_rows, base_columns = read_csv(REAL_NOTES_CSV)
    before_hash = sha256(REAL_NOTES_CSV)
    blank_before = real_notes_all_blank(base_rows)
    with tempfile.TemporaryDirectory(prefix="p209_evidence_quality_safety_") as temp_root:
        output_dir = Path(temp_root)
        cases = [run_case(spec, base_rows, base_columns, output_dir) for spec in CASE_SPECS]
    after_rows, _ = read_csv(REAL_NOTES_CSV)
    after_hash = sha256(REAL_NOTES_CSV)
    blank_after = real_notes_all_blank(after_rows)

    all_cases_passed = all(case["expected_outcome_met"] for case in cases)
    payload = {
        "phase": "P209-evidence-quality-safety-regression-tests",
        "status": "PASS" if all_cases_passed and before_hash == after_hash and blank_before and blank_after else "FAIL",
        "p195_status": "BLOCKED",
        "inputs": {"real_p207_notes_csv": rel(REAL_NOTES_CSV)},
        "outputs": {"json": rel(DEFAULT_OUTPUT_JSON), "markdown": rel(DEFAULT_OUTPUT_MD)},
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
        "real_p207_notes_blank_before_and_after": blank_before and blank_after,
        "case_count": len(cases),
        "passed_case_count": sum(1 for case in cases if case["expected_outcome_met"]),
        "cases": cases,
        "scientific_boundary": (
            "Safety/regression testing for P207/P208 evidence-quality tooling only. P209 uses temporary "
            "synthetic notes CSVs and does not create labels, train, modify real notes, or support "
            "admission-control claims."
        ),
        "p210_recommendation": (
            "Keep P195 blocked until independent human labels exist. Next no-label work should either add "
            "more read-only audit coverage around reviewer-note ingestion or collect/import independent "
            "P195/P196 human labels through the separate label protocol."
        ),
    }
    write_json(DEFAULT_OUTPUT_JSON, payload)
    DEFAULT_OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT_MD.write_text(build_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": payload["status"],
                "case_count": payload["case_count"],
                "passed_case_count": payload["passed_case_count"],
                "p195_status": payload["p195_status"],
                "real_p207_notes_hash_unchanged": payload["real_p207_notes_hash_unchanged"],
                "real_p207_notes_blank_before_and_after": payload["real_p207_notes_blank_before_and_after"],
                "outputs": payload["outputs"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if payload["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
