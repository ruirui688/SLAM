#!/usr/bin/env python3
"""Build the P214 evidence-only release bundle.

P214 packages the P206-P213 no-label evidence governance stack for paper/export
support. It reads existing artifacts, writes a compact manifest plus appendix,
and intentionally creates no admission or same-object labels, performs no
training, downloads nothing, and does not touch raw data.
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

P195_JSON = ROOT / "paper/evidence/independent_supervision_gate_p195.json"
P206_TRIAGE_JSON = ROOT / "paper/evidence/raw_evidence_diverse_packet_triage_p206.json"
P209_JSON = ROOT / "paper/evidence/evidence_quality_safety_tests_p209.json"
P210_JSON = ROOT / "paper/evidence/evidence_note_ingestion_audit_p210.json"
P211_JSON = ROOT / "paper/evidence/cross_phase_evidence_index_p211.json"
P212_JSON = ROOT / "paper/evidence/release_governance_summary_p212.json"
PROGRESS_MD = ROOT / "RESEARCH_PROGRESS.md"

OUTPUT_JSON = ROOT / "paper/evidence/evidence_only_release_bundle_p214.json"
OUTPUT_CSV = ROOT / "paper/evidence/evidence_only_release_bundle_p214.csv"
OUTPUT_MD = ROOT / "paper/export/evidence_only_release_bundle_p214.md"

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

MANIFEST_COLUMNS = [
    "phase",
    "artifact_role",
    "path",
    "exists",
    "sha256",
    "status",
    "claim_boundary",
]


def rel(path: Path | str) -> str:
    candidate = Path(path)
    try:
        return str(candidate.relative_to(ROOT))
    except ValueError:
        return str(candidate)


def repo_path(value: str | Path) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else ROOT / candidate


def sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_columns(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle).fieldnames or [])


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


def run_git(args: list[str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.stdout.rstrip("\n")


def git_info() -> dict[str, str]:
    return {
        "commit": run_git(["rev-parse", "HEAD"]),
        "short_commit": run_git(["rev-parse", "--short=12", "HEAD"]),
        "subject": run_git(["show", "-s", "--format=%s", "HEAD"]),
        "branch": run_git(["branch", "--show-current"]),
    }


def entry(phase: str, role: str, path: str, status: str, boundary: str) -> dict[str, Any]:
    full_path = repo_path(path)
    return {
        "phase": phase,
        "artifact_role": role,
        "path": path,
        "exists": full_path.exists(),
        "sha256": sha256(full_path),
        "status": status,
        "claim_boundary": boundary,
    }


def p195_status() -> dict[str, Any]:
    data = load_json(P195_JSON)
    boundary = data.get("label_audit", {}).get("boundary", {})
    pairs = data.get("label_audit", {}).get("pairs", {})
    labels_blank = (
        data.get("status") == "BLOCKED"
        and boundary.get("blank") == boundary.get("total")
        and boundary.get("valid") == 0
        and pairs.get("blank") == pairs.get("total")
        and pairs.get("valid") == 0
    )
    return {
        "status": data.get("status"),
        "labels_blank": labels_blank,
        "human_admit_label": {
            "blank": boundary.get("blank"),
            "valid": boundary.get("valid"),
            "total": boundary.get("total"),
        },
        "human_same_object_label": {
            "blank": pairs.get("blank"),
            "valid": pairs.get("valid"),
            "total": pairs.get("total"),
        },
    }


def verification_summary() -> dict[str, Any]:
    p195 = p195_status()
    p206 = load_json(P206_TRIAGE_JSON)
    p209 = load_json(P209_JSON)
    p210 = load_json(P210_JSON)
    p211 = load_json(P211_JSON)
    p212 = load_json(P212_JSON)

    p206_summary = p206.get("summary", {})
    p210_readiness = p210.get("readiness", {})
    p212_readiness = p212.get("release_readiness_status")
    p206_row_count = len(p206.get("triage_rows", []))

    checks = {
        "p195_blocked": p195.get("status") == "BLOCKED" and p195.get("labels_blank") is True,
        "p212_ready_no_label_evidence_only": p212_readiness == "READY_NO_LABEL_EVIDENCE_ONLY",
        "p209_pass": p209.get("status") == "PASS"
        and p209.get("passed_case_count") == p209.get("case_count"),
        "p210_ready_empty": p210_readiness.get("status") == "READY_EMPTY",
        "p211_pass": p211.get("status") == "PASS",
        "p206_qa_zero_issues": p206_summary.get("issue_counts") == {}
        and p206_summary.get("rows_by_issue_level", {}).get("OK") == p206_row_count
        and p206_row_count == 32,
        "human_labels_remain_blank": p195.get("labels_blank") is True,
    }
    checks["overall"] = "PASS" if all(checks.values()) else "FAIL"

    return {
        "status": checks["overall"],
        "checks": checks,
        "p195": p195,
        "p206": {
            "status": p206.get("status"),
            "rows": p206_row_count,
            "issue_counts": p206_summary.get("issue_counts"),
            "rows_by_issue_level": p206_summary.get("rows_by_issue_level"),
        },
        "p209": {
            "status": p209.get("status"),
            "case_count": p209.get("case_count"),
            "passed_case_count": p209.get("passed_case_count"),
        },
        "p210": {
            "status": p210.get("status"),
            "readiness": p210_readiness.get("status"),
        },
        "p211": {
            "status": p211.get("status"),
            "artifact_count": p211.get("artifact_count"),
        },
        "p212": {
            "release_readiness_status": p212_readiness,
        },
    }


def scan_output_columns() -> dict[str, Any]:
    blocked = [column for column in MANIFEST_COLUMNS if column.lower() in PROHIBITED_FIELD_NAMES]
    return {
        "status": "PASS" if not blocked else "FAIL",
        "columns": MANIFEST_COLUMNS,
        "prohibited_columns_present": blocked,
    }


def p213_cleanup_summary() -> dict[str, Any]:
    text = PROGRESS_MD.read_text(encoding="utf-8")
    marker = "## 2026-05-10 P213"
    start = text.find(marker)
    if start == -1:
        return {"status": "MISSING_PROGRESS_ENTRY", "source": rel(PROGRESS_MD)}
    next_section = text.find("\n## ", start + len(marker))
    section = text[start:] if next_section == -1 else text[start:next_section]
    ready = "READY_NO_LABEL_EVIDENCE_ONLY" in section
    blocked = "P195 still BLOCKED" in section or "P195 remains `BLOCKED`" in section
    return {
        "status": "COMPLETE_READY_NO_LABEL_EVIDENCE_ONLY" if ready and blocked else "CHECK_PROGRESS_ENTRY",
        "source": rel(PROGRESS_MD),
        "source_sha256": sha256(PROGRESS_MD),
        "summary": "P213 cleaned the P206-P212 no-label release state and preserved the P195 blocked label boundary.",
    }


def build_manifest() -> list[dict[str, Any]]:
    evidence_only_boundary = (
        "No-label evidence governance only; creates no admission/same-object labels, "
        "does not train, and does not support learned admission-control claims."
    )
    p206_boundary = (
        "Raw evidence packet and QA only; semantic/category evidence is not admission ground truth."
    )
    p207_boundary = "Evidence-quality notes protocol only; note fields are not labels."
    p208_boundary = "Summary of blank evidence-quality notes only; no label inference or training."
    p209_boundary = "Safety regression tests for evidence-quality tooling only."
    p210_boundary = "Quality-only ingestion audit; READY_EMPTY because all note fields are blank."
    p211_boundary = "Artifact governance index for the no-label evidence stack only."
    p212_boundary = "Release governance is READY_NO_LABEL_EVIDENCE_ONLY; learned admission remains blocked."
    p213_boundary = "Cleanup confirmed no-label release readiness without creating labels."

    return [
        entry("P206", "diverse_packet_json", "paper/evidence/raw_evidence_diverse_packet_p206.json", "DIVERSE_AUDIT_PACKET_BUILT_P195_STILL_BLOCKED", p206_boundary),
        entry("P206", "diverse_packet_csv", "paper/evidence/raw_evidence_diverse_packet_p206.csv", "DIVERSE_AUDIT_PACKET_BUILT_P195_STILL_BLOCKED", p206_boundary),
        entry("P206", "diverse_packet_report", "paper/export/raw_evidence_diverse_packet_p206.md", "DIVERSE_AUDIT_PACKET_BUILT_P195_STILL_BLOCKED", p206_boundary),
        entry("P206", "triage_json", "paper/evidence/raw_evidence_diverse_packet_triage_p206.json", "DIVERSE_PACKET_TRIAGE_COMPLETE_P195_STILL_BLOCKED", p206_boundary),
        entry("P206", "triage_csv", "paper/evidence/raw_evidence_diverse_packet_triage_p206.csv", "DIVERSE_PACKET_TRIAGE_COMPLETE_P195_STILL_BLOCKED", p206_boundary),
        entry("P206", "triage_report", "paper/export/raw_evidence_diverse_packet_triage_p206.md", "DIVERSE_PACKET_TRIAGE_COMPLETE_P195_STILL_BLOCKED", p206_boundary),
        entry("P207", "quality_notes_json", "paper/evidence/raw_evidence_quality_notes_p207.json", "BLANK_TEMPLATE_P195_STILL_BLOCKED", p207_boundary),
        entry("P207", "quality_notes_csv", "paper/evidence/raw_evidence_quality_notes_p207.csv", "BLANK_TEMPLATE_P195_STILL_BLOCKED", p207_boundary),
        entry("P207", "quality_notes_protocol", "paper/export/raw_evidence_quality_notes_protocol_p207.md", "PROTOCOL_READY_P195_STILL_BLOCKED", p207_boundary),
        entry("P208", "quality_notes_summary_json", "paper/evidence/evidence_quality_notes_summary_p208.json", "PASS", p208_boundary),
        entry("P208", "quality_blockers_csv", "paper/evidence/evidence_quality_notes_blockers_p208.csv", "PASS_ZERO_BLOCKERS", p208_boundary),
        entry("P208", "quality_notes_summary_report", "paper/export/evidence_quality_notes_summary_p208.md", "PASS", p208_boundary),
        entry("P209", "safety_tests_json", "paper/evidence/evidence_quality_safety_tests_p209.json", "PASS", p209_boundary),
        entry("P209", "safety_tests_report", "paper/export/evidence_quality_safety_tests_p209.md", "PASS", p209_boundary),
        entry("P210", "ingestion_audit_json", "paper/evidence/evidence_note_ingestion_audit_p210.json", "READY_EMPTY", p210_boundary),
        entry("P210", "ingestion_manifest_csv", "paper/evidence/evidence_note_ingestion_manifest_p210.csv", "READY_EMPTY_QUALITY_ONLY", p210_boundary),
        entry("P210", "ingestion_audit_report", "paper/export/evidence_note_ingestion_audit_p210.md", "READY_EMPTY", p210_boundary),
        entry("P211", "cross_phase_index_json", "paper/evidence/cross_phase_evidence_index_p211.json", "PASS", p211_boundary),
        entry("P211", "cross_phase_index_csv", "paper/evidence/cross_phase_evidence_index_p211.csv", "PASS", p211_boundary),
        entry("P211", "cross_phase_index_report", "paper/export/cross_phase_evidence_index_p211.md", "PASS", p211_boundary),
        entry("P212", "release_governance_json", "paper/evidence/release_governance_summary_p212.json", "READY_NO_LABEL_EVIDENCE_ONLY", p212_boundary),
        entry("P212", "release_governance_report", "paper/export/release_governance_summary_p212.md", "READY_NO_LABEL_EVIDENCE_ONLY", p212_boundary),
        entry("P213", "cleanup_status", "RESEARCH_PROGRESS.md", p213_cleanup_summary()["status"], p213_boundary),
        entry("P214", "bundle_builder_script", "tools/build_evidence_only_release_bundle_p214.py", "BUILDS_EVIDENCE_ONLY_RELEASE_BUNDLE", evidence_only_boundary),
    ]


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    verification = payload["verification"]
    p195 = verification["p195"]
    lines = [
        "# P214 Evidence-Only Release Bundle",
        "",
        f"**Bundle status:** `{payload['bundle_status']}`",
        f"**Evidence governance status:** `READY_NO_LABEL_EVIDENCE_ONLY`",
        f"**Learned admission control:** `BLOCKED`",
        "",
        "## Claim Boundary",
        "",
        "P214 packages no-label evidence governance only. Evidence-only governance is ready, but learned admission control remains blocked. No human admission labels exist, no human same-object labels exist, and no admission/same-object labels were generated. Semantic/category evidence must not be reported as admission ground truth.",
        "",
        "This bundle does not create labels, infer labels, train models, download data, modify raw data, or support learned admission-control claims.",
        "",
        "## Human Label Gate",
        "",
        f"- P195 status: `{p195['status']}`",
        f"- `human_admit_label`: {p195['human_admit_label']['blank']} blank / {p195['human_admit_label']['valid']} valid / {p195['human_admit_label']['total']} total",
        f"- `human_same_object_label`: {p195['human_same_object_label']['blank']} blank / {p195['human_same_object_label']['valid']} valid / {p195['human_same_object_label']['total']} total",
        "",
        "## Bundle Manifest",
        "",
        "| Phase | Role | Status | Path | SHA-256 | Claim boundary |",
        "|---|---|---|---|---|---|",
    ]
    for item in payload["manifest"]:
        digest = item["sha256"][:12] if item["sha256"] else ""
        lines.append(
            f"| {item['phase']} | {item['artifact_role']} | `{item['status']}` | `{item['path']}` | `{digest}` | {item['claim_boundary']} |"
        )

    lines.extend(
        [
            "",
            "## Final Checklist",
            "",
            f"- P195 BLOCKED: `{'PASS' if verification['checks']['p195_blocked'] else 'FAIL'}`",
            f"- P212 READY_NO_LABEL_EVIDENCE_ONLY: `{'PASS' if verification['checks']['p212_ready_no_label_evidence_only'] else 'FAIL'}`",
            f"- P209 PASS: `{'PASS' if verification['checks']['p209_pass'] else 'FAIL'}`",
            f"- P210 READY_EMPTY: `{'PASS' if verification['checks']['p210_ready_empty'] else 'FAIL'}`",
            f"- P211 PASS: `{'PASS' if verification['checks']['p211_pass'] else 'FAIL'}`",
            f"- P206 QA zero issues: `{'PASS' if verification['checks']['p206_qa_zero_issues'] else 'FAIL'}`",
            "",
            "## Verification",
            "",
            f"- Bundle output schema has no prohibited row-level decision/proxy columns: `{payload['schema_scan']['status']}`",
            f"- Human labels remain blank: `{'PASS' if verification['checks']['human_labels_remain_blank'] else 'FAIL'}`",
            f"- Overall verification: `{verification['status']}`",
            "",
            "## P215 Recommendation",
            "",
            "Keep the next step on the same boundary unless independent human labels are collected. Recommended P215 options are either a paper-facing appendix integration pass for the P214 bundle, or a separate label-collection/import phase that keeps semantic/category evidence out of the admission ground-truth path.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build() -> dict[str, Any]:
    manifest = build_manifest()
    verification = verification_summary()
    schema_scan = scan_output_columns()
    p213 = p213_cleanup_summary()
    status = "READY_NO_LABEL_EVIDENCE_ONLY" if verification["status"] == "PASS" and schema_scan["status"] == "PASS" else "BLOCKED"
    payload = {
        "phase": "P214-evidence-only-release-bundle",
        "bundle_status": status,
        "current_git": git_info(),
        "inputs": {
            "p195_gate_json": rel(P195_JSON),
            "p206_triage_json": rel(P206_TRIAGE_JSON),
            "p209_safety_json": rel(P209_JSON),
            "p210_ingestion_audit_json": rel(P210_JSON),
            "p211_index_json": rel(P211_JSON),
            "p212_governance_json": rel(P212_JSON),
            "research_progress": rel(PROGRESS_MD),
        },
        "outputs": {
            "json": rel(OUTPUT_JSON),
            "csv": rel(OUTPUT_CSV),
            "markdown": rel(OUTPUT_MD),
        },
        "manifest": manifest,
        "verification": verification,
        "schema_scan": schema_scan,
        "p213_cleanup": p213,
        "claim_boundary": (
            "P214 packages no-label evidence governance only. Evidence-only governance is ready; "
            "learned admission control remains blocked; no human labels exist; no admission/same-object "
            "labels were generated; semantic/category evidence must not be reported as admission ground truth."
        ),
        "constraints_observed": {
            "human_admit_label_created_or_filled": False,
            "human_same_object_label_created_or_filled": False,
            "admission_or_same_object_labels_inferred": False,
            "training_performed": False,
            "downloads_performed": False,
            "raw_data_modified": False,
            "protected_untracked_thirdparty_or_orb_paths_touched": False,
        },
        "p215_recommendation": (
            "Either integrate this evidence-only bundle into the paper appendix/export path, or collect/import "
            "independent human labels through the existing P195/P196 protocol before any learned admission-control claim."
        ),
    }
    write_json(OUTPUT_JSON, payload)
    write_csv(OUTPUT_CSV, manifest, MANIFEST_COLUMNS)
    write_markdown(OUTPUT_MD, payload)
    return payload


def main() -> int:
    payload = build()
    print(
        json.dumps(
            {
                "bundle_status": payload["bundle_status"],
                "verification": payload["verification"]["status"],
                "manifest_rows": len(payload["manifest"]),
                "schema_scan": payload["schema_scan"]["status"],
                "outputs": payload["outputs"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
