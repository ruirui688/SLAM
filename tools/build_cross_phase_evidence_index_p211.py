#!/usr/bin/env python3
"""Build the P211 cross-phase evidence index and staleness report.

P211 is read-only artifact governance for the P206-P210 no-label evidence QA
stack.  It indexes scripts/reports/artifacts and checks whether the current
local files remain mutually consistent.  It does not edit notes or raw data,
create labels, train models, or download anything.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

OUTPUT_JSON = ROOT / "paper/evidence/cross_phase_evidence_index_p211.json"
OUTPUT_CSV = ROOT / "paper/evidence/cross_phase_evidence_index_p211.csv"
OUTPUT_MD = ROOT / "paper/export/cross_phase_evidence_index_p211.md"

NOTE_FIELDS = [
    "visibility_quality",
    "mask_alignment_quality",
    "depth_quality",
    "occlusion_level",
    "blur_level",
    "reviewer_note",
    "quality_blocker",
]

ROW_ID_FIELDS = [
    "audit_sample_id",
    "p203_index_row_id",
    "p202_audit_row_id",
    "row_source",
    "row_role",
    "sample_id",
    "observation_id",
    "source",
    "session_id",
    "frame_index",
    "tracklet_id",
    "physical_key",
]

P210_MANIFEST_FIELDS = [
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
    *NOTE_FIELDS,
]

PROHIBITED_FIELD_NAMES = {
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
    "admission_label",
    "admission_decision",
    "same_object_decision",
    "different_object",
    "predicted_admit",
    "admit_probability",
    "same_object_probability",
}


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def repo_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def row_count_for_artifact(path: Path) -> int | None:
    if not path.exists() or not path.is_file():
        return None
    if path.suffix.lower() == ".csv":
        rows, _ = read_csv(path)
        return len(rows)
    if path.suffix.lower() != ".json":
        return None
    data = load_json(path)
    for key in ("rows", "triage_rows", "cases", "quality_blocker_rows"):
        value = data.get(key)
        if isinstance(value, list):
            return len(value)
    summary = data.get("summary")
    if isinstance(summary, dict) and isinstance(summary.get("rows"), int):
        return int(summary["rows"])
    for key in ("row_count", "case_count"):
        value = data.get(key)
        if isinstance(value, int):
            return value
    return None


def artifact(
    path: str,
    phase: str,
    role: str,
    dependencies: list[str],
    artifact_type: str,
) -> dict[str, Any]:
    full_path = repo_path(path)
    exists = full_path.exists()
    stat = full_path.stat() if exists else None
    entry: dict[str, Any] = {
        "path": path,
        "artifact_type": artifact_type,
        "exists": exists,
        "size_bytes": stat.st_size if stat else None,
        "sha256": sha256(full_path),
        "row_count": row_count_for_artifact(full_path),
        "generated_phase": phase,
        "role": role,
        "expected_upstream_dependencies": dependencies,
    }
    if exists:
        entry["mtime_utc"] = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
    return entry


def artifact_plan() -> list[dict[str, Any]]:
    return [
        artifact("tools/build_diverse_raw_evidence_packet_p206.py", "P206", "producer_script", ["P203 raw segmentation evidence index"], "script"),
        artifact("paper/evidence/raw_evidence_diverse_packet_p206.json", "P206", "diverse_packet_json", ["paper/evidence/raw_segmentation_evidence_index_p203.json"], "evidence"),
        artifact("paper/evidence/raw_evidence_diverse_packet_p206.csv", "P206", "diverse_packet_csv", ["paper/evidence/raw_segmentation_evidence_index_p203.csv"], "evidence"),
        artifact("paper/export/raw_evidence_diverse_packet_p206.md", "P206", "diverse_packet_report", ["paper/evidence/raw_evidence_diverse_packet_p206.json"], "report"),
        artifact("paper/evidence/raw_evidence_diverse_packet_triage_p206.json", "P206", "triage_json", ["paper/evidence/raw_evidence_diverse_packet_p206.json"], "evidence"),
        artifact("paper/evidence/raw_evidence_diverse_packet_triage_p206.csv", "P206", "triage_csv", ["paper/evidence/raw_evidence_diverse_packet_p206.csv"], "evidence"),
        artifact("paper/export/raw_evidence_diverse_packet_triage_p206.md", "P206", "triage_report", ["paper/evidence/raw_evidence_diverse_packet_triage_p206.json"], "report"),
        artifact("tools/build_evidence_quality_notes_p207.py", "P207", "producer_and_validator_script", ["P206 diverse packet"], "script"),
        artifact("paper/evidence/raw_evidence_quality_notes_p207.json", "P207", "blank_quality_notes_json", ["paper/evidence/raw_evidence_diverse_packet_p206.json"], "evidence"),
        artifact("paper/evidence/raw_evidence_quality_notes_p207.csv", "P207", "blank_quality_notes_csv", ["paper/evidence/raw_evidence_diverse_packet_p206.csv"], "evidence"),
        artifact("paper/export/raw_evidence_quality_notes_protocol_p207.md", "P207", "quality_notes_protocol", ["paper/evidence/raw_evidence_quality_notes_p207.json"], "report"),
        artifact("tools/summarize_evidence_quality_notes_p208.py", "P208", "summary_script", ["P207 notes"], "script"),
        artifact("paper/evidence/evidence_quality_notes_summary_p208.json", "P208", "quality_notes_summary_json", ["paper/evidence/raw_evidence_quality_notes_p207.csv"], "evidence"),
        artifact("paper/evidence/evidence_quality_notes_blockers_p208.csv", "P208", "quality_blockers_csv", ["paper/evidence/raw_evidence_quality_notes_p207.csv"], "evidence"),
        artifact("paper/export/evidence_quality_notes_summary_p208.md", "P208", "quality_notes_summary_report", ["paper/evidence/evidence_quality_notes_summary_p208.json"], "report"),
        artifact("tools/test_evidence_quality_safety_p209.py", "P209", "safety_test_script", ["P207 notes", "P208 summary behavior"], "script"),
        artifact("paper/evidence/evidence_quality_safety_tests_p209.json", "P209", "safety_test_report_json", ["tools/test_evidence_quality_safety_p209.py", "paper/evidence/raw_evidence_quality_notes_p207.csv"], "evidence"),
        artifact("paper/export/evidence_quality_safety_tests_p209.md", "P209", "safety_test_report_md", ["paper/evidence/evidence_quality_safety_tests_p209.json"], "report"),
        artifact("tools/audit_evidence_note_ingestion_p210.py", "P210", "ingestion_audit_script", ["P207 notes", "P208 validation"], "script"),
        artifact("paper/evidence/evidence_note_ingestion_audit_p210.json", "P210", "ingestion_audit_json", ["paper/evidence/raw_evidence_quality_notes_p207.csv"], "evidence"),
        artifact("paper/evidence/evidence_note_ingestion_manifest_p210.csv", "P210", "quality_only_ingestion_manifest", ["paper/evidence/raw_evidence_quality_notes_p207.csv"], "evidence"),
        artifact("paper/export/evidence_note_ingestion_audit_p210.md", "P210", "ingestion_audit_report", ["paper/evidence/evidence_note_ingestion_audit_p210.json"], "report"),
    ]


def check(name: str, status: str, details: str, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "details": details,
        "evidence": evidence or {},
    }


def compare_row_ids(left: list[dict[str, str]], right: list[dict[str, str]], fields: list[str]) -> tuple[bool, dict[str, Any]]:
    left_keys = [tuple(str(row.get(field, "")) for field in fields) for row in left]
    right_keys = [tuple(str(row.get(field, "")) for field in fields) for row in right]
    return left_keys == right_keys, {
        "left_rows": len(left),
        "right_rows": len(right),
        "fields_compared": fields,
        "left_only_count": sum((Counter(left_keys) - Counter(right_keys)).values()),
        "right_only_count": sum((Counter(right_keys) - Counter(left_keys)).values()),
    }


def note_blank_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    return {field: sum(1 for row in rows if not str(row.get(field, ""))) for field in NOTE_FIELDS}


def scan_columns_for_blocked_fields(columns: list[str]) -> list[str]:
    lower = {column.lower(): column for column in columns}
    return sorted(lower[name] for name in lower if name in PROHIBITED_FIELD_NAMES)


def build_staleness_checks() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    paths = {
        "p206_packet_json": ROOT / "paper/evidence/raw_evidence_diverse_packet_p206.json",
        "p206_packet_csv": ROOT / "paper/evidence/raw_evidence_diverse_packet_p206.csv",
        "p206_triage_json": ROOT / "paper/evidence/raw_evidence_diverse_packet_triage_p206.json",
        "p207_json": ROOT / "paper/evidence/raw_evidence_quality_notes_p207.json",
        "p207_csv": ROOT / "paper/evidence/raw_evidence_quality_notes_p207.csv",
        "p208_json": ROOT / "paper/evidence/evidence_quality_notes_summary_p208.json",
        "p208_blockers_csv": ROOT / "paper/evidence/evidence_quality_notes_blockers_p208.csv",
        "p209_json": ROOT / "paper/evidence/evidence_quality_safety_tests_p209.json",
        "p210_json": ROOT / "paper/evidence/evidence_note_ingestion_audit_p210.json",
        "p210_manifest_csv": ROOT / "paper/evidence/evidence_note_ingestion_manifest_p210.csv",
    }

    missing = sorted(name for name, path in paths.items() if not path.exists())
    checks.append(check("required_artifacts_exist", "PASS" if not missing else "FAIL", "All required P206-P210 artifacts exist." if not missing else f"Missing artifacts: {missing}", {"missing": missing}))
    if missing:
        return checks

    p206 = load_json(paths["p206_packet_json"])
    p206_rows_csv, p206_columns = read_csv(paths["p206_packet_csv"])
    p206_triage = load_json(paths["p206_triage_json"])
    p207 = load_json(paths["p207_json"])
    p207_rows_csv, p207_columns = read_csv(paths["p207_csv"])
    p208 = load_json(paths["p208_json"])
    p208_blockers, p208_blocker_columns = read_csv(paths["p208_blockers_csv"])
    p209 = load_json(paths["p209_json"])
    p210 = load_json(paths["p210_json"])
    p210_manifest, p210_manifest_columns = read_csv(paths["p210_manifest_csv"])

    triage_summary = p206_triage.get("summary", {})
    issue_counts = triage_summary.get("issue_counts", {})
    rows_by_issue = triage_summary.get("rows_by_issue_level", {})
    triage_ok = not issue_counts and rows_by_issue.get("OK") == len(p206_rows_csv)
    checks.append(check(
        "p206_triage_has_zero_issues",
        "PASS" if triage_ok else "FAIL",
        "P206 triage reports zero issue counts and all packet rows OK." if triage_ok else "P206 triage has issues or non-OK rows.",
        {"issue_counts": issue_counts, "rows_by_issue_level": rows_by_issue, "packet_rows": len(p206_rows_csv)},
    ))

    row_match, row_match_evidence = compare_row_ids(p206_rows_csv, p207_rows_csv, ROW_ID_FIELDS)
    checks.append(check(
        "p207_notes_match_p206_packet_row_ids",
        "PASS" if row_match else "FAIL",
        "P207 notes preserve P206 packet row identities in order." if row_match else "P207 notes differ from P206 packet row identities.",
        row_match_evidence,
    ))

    p207_summary = p207.get("summary", {})
    current_blank_counts = note_blank_counts(p207_rows_csv)
    p207_blank_ok = all(value == len(p207_rows_csv) for value in current_blank_counts.values())
    p207_status_ok = p207.get("validation", {}).get("status") == "PASS" and p207_summary.get("rows") == len(p207_rows_csv)
    checks.append(check(
        "p207_notes_current_and_blank",
        "PASS" if p207_status_ok and p207_blank_ok else "FAIL",
        "P207 notes validate and all evidence-quality note fields remain blank." if p207_status_ok and p207_blank_ok else "P207 notes are stale, invalid, or no longer blank.",
        {"json_rows": p207_summary.get("rows"), "csv_rows": len(p207_rows_csv), "note_blank_counts": current_blank_counts, "validation_status": p207.get("validation", {}).get("status")},
    ))

    p208_summary = p208.get("summary", {})
    p208_validation = p208.get("validation", {})
    p208_counts_match = (
        p208_summary.get("rows") == len(p207_rows_csv)
        and p208_summary.get("note_blank_counts") == current_blank_counts
        and len(p208_blockers) == sum(1 for row in p207_rows_csv if str(row.get("quality_blocker", "")) == "yes")
    )
    checks.append(check(
        "p208_summary_matches_current_p207_notes",
        "PASS" if p208.get("status") == "PASS" and p208_validation.get("status") == "PASS" and p208_counts_match else "FAIL",
        "P208 summary row counts, blank counts, and blocker rows match current P207 notes. P208 stores no source hash, so this uses content-derived counts instead of timestamp ordering.",
        {
            "p208_status": p208.get("status"),
            "p208_validation_status": p208_validation.get("status"),
            "p208_rows": p208_summary.get("rows"),
            "current_p207_rows": len(p207_rows_csv),
            "p208_blocker_rows": len(p208_blockers),
            "current_quality_blocker_yes_rows": sum(1 for row in p207_rows_csv if str(row.get("quality_blocker", "")) == "yes"),
            "hash_available_in_p208": False,
        },
    ))

    p207_hash = sha256(paths["p207_csv"])
    p209_hash_ok = p209.get("real_p207_notes_sha256_before") == p207_hash and p209.get("real_p207_notes_sha256_after") == p207_hash
    p209_ok = p209.get("status") == "PASS" and p209.get("passed_case_count") == p209.get("case_count") and p209.get("real_p207_notes_hash_unchanged") is True and p209_hash_ok
    checks.append(check(
        "p209_safety_tests_pass_against_current_p207_hash",
        "PASS" if p209_ok else "FAIL",
        "P209 safety tests pass and recorded P207 notes hashes match the current notes CSV." if p209_ok else "P209 safety report is stale or failing.",
        {
            "status": p209.get("status"),
            "passed_case_count": p209.get("passed_case_count"),
            "case_count": p209.get("case_count"),
            "current_p207_sha256": p207_hash,
            "recorded_sha256_before": p209.get("real_p207_notes_sha256_before"),
            "recorded_sha256_after": p209.get("real_p207_notes_sha256_after"),
        },
    ))

    p210_hash_ok = p210.get("real_p207_notes_sha256_before") == p207_hash and p210.get("real_p207_notes_sha256_after") == p207_hash
    p210_summary = p210.get("summary", {})
    p210_readiness = p210.get("readiness", {})
    p210_self = p210.get("self_test", {})
    p210_ok = (
        p210.get("status") == "PASS"
        and p210_readiness.get("status") == "READY_EMPTY"
        and p210_hash_ok
        and p210_summary.get("rows") == len(p207_rows_csv)
        and p210_summary.get("manifest_rows") == len(p210_manifest)
        and p210_self.get("status") == "PASS"
        and p210_self.get("passed_case_count") == p210_self.get("case_count")
    )
    checks.append(check(
        "p210_ingestion_audit_matches_current_p207_hash",
        "PASS" if p210_ok else "FAIL",
        "P210 audit is READY_EMPTY, hash-compatible with current P207 notes, and self-test passed." if p210_ok else "P210 audit is stale or failing.",
        {
            "status": p210.get("status"),
            "readiness": p210_readiness.get("status"),
            "current_p207_sha256": p207_hash,
            "recorded_sha256_before": p210.get("real_p207_notes_sha256_before"),
            "recorded_sha256_after": p210.get("real_p207_notes_sha256_after"),
            "self_test_status": p210_self.get("status"),
            "self_test_cases": f"{p210_self.get('passed_case_count')}/{p210_self.get('case_count')}",
        },
    ))

    manifest_row_match, manifest_evidence = compare_row_ids(
        [{field: row.get(field, "") for field in P210_MANIFEST_FIELDS} for row in p207_rows_csv],
        p210_manifest,
        P210_MANIFEST_FIELDS,
    )
    manifest_blocked_fields = scan_columns_for_blocked_fields(p210_manifest_columns)
    manifest_safe = manifest_row_match and not manifest_blocked_fields and "canonical_label" not in p210_manifest_columns
    checks.append(check(
        "p210_manifest_is_quality_only_and_matches_p207_notes",
        "PASS" if manifest_safe else "FAIL",
        "P210 manifest matches current P207 rows for quality-only fields and excludes blocked decision/proxy fields plus canonical category names." if manifest_safe else "P210 manifest is stale or contains disallowed fields.",
        {**manifest_evidence, "blocked_fields_present": manifest_blocked_fields, "contains_canonical_category_field": "canonical_label" in p210_manifest_columns},
    ))

    generated_csv_columns = ["path", "artifact_type", "exists", "size_bytes", "sha256", "row_count", "generated_phase", "role", "expected_upstream_dependencies"]
    generated_csv_blocked = scan_columns_for_blocked_fields(generated_csv_columns)
    source_blocked = {
        "p206_packet_csv": scan_columns_for_blocked_fields(p206_columns),
        "p207_notes_csv": scan_columns_for_blocked_fields(p207_columns),
        "p208_blockers_csv": scan_columns_for_blocked_fields(p208_blocker_columns),
        "p210_manifest_csv": scan_columns_for_blocked_fields(p210_manifest_columns),
    }
    generated_safe = not generated_csv_blocked
    checks.append(check(
        "generated_index_has_no_row_level_decision_or_proxy_columns",
        "PASS" if generated_safe else "FAIL",
        "P211 artifact-level CSV schema contains no row-level decision/proxy fields. Source artifacts are scanned separately for governance visibility.",
        {"p211_csv_blocked_fields": generated_csv_blocked, "source_artifact_blocked_fields": source_blocked},
    ))

    p195_statuses = {
        "p206_packet": p206.get("p195_status"),
        "p206_triage": p206_triage.get("p195_status"),
        "p207": p207.get("p195_status"),
        "p208": p208.get("p195_status"),
        "p209": p209.get("p195_status"),
        "p210": p210.get("p195_status"),
    }
    p195_ok = all(status == "BLOCKED" for status in p195_statuses.values())
    checks.append(check(
        "p195_remains_blocked_across_stack",
        "PASS" if p195_ok else "FAIL",
        "All indexed P206-P210 governance artifacts keep P195 BLOCKED." if p195_ok else "At least one artifact does not report P195 BLOCKED.",
        p195_statuses,
    ))

    return checks


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    status = payload["staleness"]["status"]
    artifact_count = payload["artifact_count"]
    lines = [
        "# P211 Cross-Phase Evidence Index",
        "",
        f"**Status:** `{status}`; P195 remains `{payload['p195_status']}`.",
        "",
        "## Scope",
        "",
        "P211 is read-only artifact governance for the P206-P210 no-label evidence QA stack. It links existing local artifacts and checks hash/row-id consistency without creating labels, training data, or admission-control claims.",
        "",
        "## Artifact Index",
        "",
        f"- Indexed artifacts: {artifact_count}",
        f"- JSON index: `{payload['outputs']['json']}`",
        f"- CSV index: `{payload['outputs']['csv']}`",
        "",
        "| Phase | Role | Path | Exists | Rows | SHA-256 |",
        "|---|---|---|---:|---:|---|",
    ]
    for item in payload["artifacts"]:
        digest = item["sha256"][:12] if item["sha256"] else ""
        rows = "" if item["row_count"] is None else str(item["row_count"])
        lines.append(f"| {item['generated_phase']} | {item['role']} | `{item['path']}` | {item['exists']} | {rows} | `{digest}` |")
    lines.extend(["", "## Staleness Checks", ""])
    for item in payload["staleness"]["checks"]:
        lines.append(f"- `{item['name']}`: `{item['status']}` - {item['details']}")
    lines.extend(
        [
            "",
            "## Limits",
            "",
            "- P208 does not store the P207 notes source hash, so P211 checks P208 by current row counts, blank note counts, and blocker-row consistency rather than relying on noisy filesystem timestamp ordering.",
            "- The CSV artifact index is artifact-level metadata only; it is not an ingestible row-level evidence table.",
            "",
            "## Scientific Boundary",
            "",
            "P211 does not fill or infer human admission or same-object labels, does not modify real notes or raw data, does not train, and does not support admission-control claims.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build() -> dict[str, Any]:
    artifacts = artifact_plan()
    checks = build_staleness_checks()
    failing = [item for item in checks if item["status"] == "FAIL"]
    warnings = [item for item in checks if item["status"] == "WARN"]
    status = "FAIL" if failing else "WARN" if warnings else "PASS"
    payload = {
        "phase": "P211-cross-phase-evidence-index",
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "staleness": {
            "status": status,
            "fail_count": len(failing),
            "warning_count": len(warnings),
            "checks": checks,
        },
        "outputs": {
            "json": rel(OUTPUT_JSON),
            "csv": rel(OUTPUT_CSV),
            "markdown": rel(OUTPUT_MD),
        },
        "p195_status": "BLOCKED",
        "p212_recommendation": "Keep P195 blocked until independent human admission/same-object labels exist. If staying no-label, add a read-only release-style governance summary that compares artifact hashes across commits and flags drift before paper export.",
        "scientific_boundary": (
            "Artifact governance for the no-label P206-P210 evidence QA stack only. "
            "P211 creates no admission or same-object labels, does not train, does not modify notes/raw data, "
            "and does not support admission-control claims."
        ),
        "constraints_observed": {
            "human_admit_label_created_or_filled": False,
            "human_same_object_label_created_or_filled": False,
            "admission_or_same_object_labels_inferred": False,
            "admission_or_semantic_stability_training_performed": False,
            "downloads_performed": False,
            "real_notes_or_raw_data_modified": False,
        },
    }
    csv_columns = ["path", "artifact_type", "exists", "size_bytes", "sha256", "row_count", "generated_phase", "role", "expected_upstream_dependencies"]
    csv_rows = [
        {
            **{key: item.get(key) for key in csv_columns if key != "expected_upstream_dependencies"},
            "expected_upstream_dependencies": ";".join(item["expected_upstream_dependencies"]),
        }
        for item in artifacts
    ]
    write_json(OUTPUT_JSON, payload)
    write_csv(OUTPUT_CSV, csv_rows, csv_columns)
    write_markdown(OUTPUT_MD, payload)
    return payload


def main() -> int:
    payload = build()
    print(json.dumps({
        "status": payload["status"],
        "artifact_count": payload["artifact_count"],
        "staleness_status": payload["staleness"]["status"],
        "outputs": payload["outputs"],
        "p195_status": payload["p195_status"],
    }, indent=2, sort_keys=True))
    return 0 if payload["status"] in {"PASS", "WARN"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
