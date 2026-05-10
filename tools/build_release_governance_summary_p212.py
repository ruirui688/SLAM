#!/usr/bin/env python3
"""Build the P212 release governance summary for no-label evidence export.

P212 consumes the P211 cross-phase evidence index and the current local git
state. It is a read-only release/export checker: it does not create labels,
does not train, does not download anything, and does not modify raw data or
real review notes.
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

P211_JSON = ROOT / "paper/evidence/cross_phase_evidence_index_p211.json"
P195_JSON = ROOT / "paper/evidence/independent_supervision_gate_p195.json"
OUTPUT_JSON = ROOT / "paper/evidence/release_governance_summary_p212.json"
OUTPUT_MD = ROOT / "paper/export/release_governance_summary_p212.md"

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

P212_OUTPUTS = {
    "paper/evidence/release_governance_summary_p212.json",
    "paper/export/release_governance_summary_p212.md",
}


def rel(path: Path | str) -> str:
    candidate = Path(path)
    try:
        return str(candidate.relative_to(ROOT))
    except ValueError:
        return str(candidate)


def repo_path(value: str | Path) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else ROOT / candidate


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


def scan_columns_for_blocked_fields(columns: list[str]) -> list[str]:
    blocked: list[str] = []
    for column in columns:
        if column.lower() in PROHIBITED_FIELD_NAMES:
            blocked.append(column)
    return sorted(blocked)


def git_info() -> dict[str, Any]:
    return {
        "commit": run_git(["rev-parse", "HEAD"]),
        "short_commit": run_git(["rev-parse", "--short=12", "HEAD"]),
        "subject": run_git(["show", "-s", "--format=%s", "HEAD"]),
        "committer_date": run_git(["show", "-s", "--format=%cI", "HEAD"]),
        "branch": run_git(["branch", "--show-current"]),
        "p206_p211_commits": [
            {
                "commit": line.split(" ", 1)[0],
                "subject": line.split(" ", 1)[1] if " " in line else "",
            }
            for line in run_git(["log", "--oneline", "--reverse", "aed1512..HEAD"]).splitlines()
            if line.strip()
        ],
    }


def parse_porcelain_line(line: str) -> dict[str, str]:
    status = line[:2]
    path_part = line[3:]
    if " -> " in path_part:
        path_part = path_part.split(" -> ", 1)[1]
    return {"status": status, "path": path_part}


def protected_untracked(path: str) -> bool:
    return path.startswith("thirdparty/") or path.startswith("tools/orb_slam3_headless")


def git_status_scope(relevant_paths: set[str]) -> dict[str, Any]:
    lines = run_git(["status", "--porcelain=v1", "--untracked-files=all"]).splitlines()
    tracked_relevant: list[dict[str, str]] = []
    untracked_relevant: list[dict[str, str]] = []
    ignored_protected: list[dict[str, str]] = []
    other_dirty: list[dict[str, str]] = []
    p212_generated: list[dict[str, str]] = []

    for line in lines:
        item = parse_porcelain_line(line)
        path = item["path"]
        status = item["status"]
        if path in P212_OUTPUTS:
            p212_generated.append(item)
        elif status == "??" and protected_untracked(path):
            ignored_protected.append(item)
        elif path in relevant_paths:
            if status == "??":
                untracked_relevant.append(item)
            else:
                tracked_relevant.append(item)
        else:
            other_dirty.append(item)

    return {
        "tracked_relevant": tracked_relevant,
        "untracked_relevant": untracked_relevant,
        "ignored_protected_untracked": {
            "count": len(ignored_protected),
            "roots": sorted({item["path"].split("/", 2)[0] if item["path"].startswith("thirdparty/") else item["path"] for item in ignored_protected}),
            "examples": ignored_protected[:10],
        },
        "other_dirty_count": len(other_dirty),
        "other_dirty_examples": other_dirty[:20],
        "p212_generated_outputs": p212_generated,
        "relevant_dirty_clean": not tracked_relevant and not untracked_relevant,
    }


def artifact_hash_check(p211: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for item in p211.get("artifacts", []):
        path = str(item["path"])
        current_hash = sha256(repo_path(path))
        recorded_hash = item.get("sha256")
        rows.append(
            {
                "path": path,
                "phase": item.get("generated_phase"),
                "role": item.get("role"),
                "exists": repo_path(path).exists(),
                "recorded_sha256": recorded_hash,
                "current_sha256": current_hash,
                "matches_p211": current_hash == recorded_hash,
            }
        )
    mismatches = [row for row in rows if not row["matches_p211"]]
    return {
        "status": "PASS" if not mismatches else "FAIL",
        "artifact_count": len(rows),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "artifacts": rows,
    }


def label_leakage_check() -> dict[str, Any]:
    csv_paths = [
        ROOT / "paper/evidence/raw_evidence_quality_notes_p207.csv",
        ROOT / "paper/evidence/evidence_quality_notes_blockers_p208.csv",
        ROOT / "paper/evidence/evidence_note_ingestion_manifest_p210.csv",
        ROOT / "paper/evidence/cross_phase_evidence_index_p211.csv",
    ]
    scans: list[dict[str, Any]] = []
    for path in csv_paths:
        columns = read_csv_columns(path) if path.exists() else []
        scans.append(
            {
                "path": rel(path),
                "exists": path.exists(),
                "column_count": len(columns),
                "prohibited_columns_present": scan_columns_for_blocked_fields(columns),
            }
        )
    blocked = [scan for scan in scans if scan["prohibited_columns_present"]]
    return {
        "status": "PASS" if not blocked else "FAIL",
        "scans": scans,
        "blocked_scan_count": len(blocked),
    }


def p195_gate_check(p195: dict[str, Any]) -> dict[str, Any]:
    boundary = p195.get("label_audit", {}).get("boundary", {})
    pairs = p195.get("label_audit", {}).get("pairs", {})
    status = p195.get("status")
    remains_blocked = (
        status == "BLOCKED"
        and boundary.get("valid") == 0
        and boundary.get("blank") == boundary.get("total")
        and pairs.get("valid") == 0
        and pairs.get("blank") == pairs.get("total")
    )
    return {
        "status": "PASS" if remains_blocked else "FAIL",
        "p195_status": status,
        "boundary_label_audit": boundary,
        "pair_label_audit": pairs,
        "decision": p195.get("decision"),
    }


def p209_check() -> dict[str, Any]:
    path = ROOT / "paper/evidence/evidence_quality_safety_tests_p209.json"
    data = load_json(path)
    ok = (
        data.get("status") == "PASS"
        and data.get("passed_case_count") == data.get("case_count")
        and data.get("real_p207_notes_hash_unchanged") is True
        and data.get("p195_status") == "BLOCKED"
    )
    return {
        "status": "PASS" if ok else "FAIL",
        "report": rel(path),
        "case_count": data.get("case_count"),
        "passed_case_count": data.get("passed_case_count"),
        "real_p207_notes_hash_unchanged": data.get("real_p207_notes_hash_unchanged"),
        "p195_status": data.get("p195_status"),
    }


def p210_check() -> dict[str, Any]:
    path = ROOT / "paper/evidence/evidence_note_ingestion_audit_p210.json"
    data = load_json(path)
    self_test = data.get("self_test", {})
    readiness = data.get("readiness", {})
    manifest = data.get("ingestion_manifest", {})
    ok = (
        data.get("status") == "PASS"
        and readiness.get("status") == "READY_EMPTY"
        and data.get("real_p207_notes_hash_unchanged") is True
        and self_test.get("status") == "PASS"
        and self_test.get("passed_case_count") == self_test.get("case_count")
        and manifest.get("contains_human_admit_label") is False
        and manifest.get("contains_human_same_object_label") is False
        and manifest.get("contains_admission_or_same_object_decision_field") is False
        and manifest.get("contains_canonical_label_field") is False
        and data.get("p195_status") == "BLOCKED"
    )
    return {
        "status": "PASS" if ok else "FAIL",
        "report": rel(path),
        "readiness": readiness.get("status"),
        "real_p207_notes_hash_unchanged": data.get("real_p207_notes_hash_unchanged"),
        "self_test_status": self_test.get("status"),
        "self_test_cases": f"{self_test.get('passed_case_count')}/{self_test.get('case_count')}",
        "manifest_quality_only": {
            "contains_boundary_human_label": manifest.get("contains_human_admit_label"),
            "contains_pair_human_label": manifest.get("contains_human_same_object_label"),
            "contains_decision_field": manifest.get("contains_admission_or_same_object_decision_field"),
            "contains_canonical_category_field": manifest.get("contains_canonical_label_field"),
        },
        "p195_status": data.get("p195_status"),
    }


def output_schema_check() -> dict[str, Any]:
    json_keys = [
        "checks",
        "claim_boundary",
        "constraints_observed",
        "current_git",
        "inputs",
        "outputs",
        "phase",
        "release_readiness_status",
        "recommendation",
    ]
    markdown_sections = [
        "P212 Release Governance Summary",
        "Release Status",
        "Governance Checks",
        "Dirty Worktree Scope",
        "Claim Boundary",
    ]
    blocked = scan_columns_for_blocked_fields(json_keys + markdown_sections)
    return {
        "status": "PASS" if not blocked else "FAIL",
        "p212_json_top_level_keys_checked": json_keys,
        "p212_markdown_sections_checked": markdown_sections,
        "prohibited_output_fields_present": blocked,
    }


def derive_release_status(checks: dict[str, Any]) -> str:
    if checks["label_leakage"]["status"] != "PASS" or checks["p212_output_schema"]["status"] != "PASS":
        return "BLOCKED_LABEL_LEAKAGE"
    if checks["p195_gate"]["status"] != "PASS":
        return "BLOCKED_GATE_UNEXPECTED"
    if checks["artifact_hashes"]["status"] != "PASS" or not checks["dirty_worktree"]["relevant_dirty_clean"]:
        return "BLOCKED_STALE_ARTIFACTS"
    if checks["p209_safety"]["status"] != "PASS" or checks["p210_readiness"]["status"] != "PASS":
        return "BLOCKED_STALE_ARTIFACTS"
    return "READY_NO_LABEL_EVIDENCE_ONLY"


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    checks = payload["checks"]
    lines = [
        "# P212 Release Governance Summary",
        "",
        f"**Release readiness:** `{payload['release_readiness_status']}`",
        f"**Current commit:** `{payload['current_git']['short_commit']}` - {payload['current_git']['subject']}",
        f"**P195 gate:** `{checks['p195_gate']['p195_status']}`",
        f"**P210 readiness:** `{checks['p210_readiness']['readiness']}`",
        "",
        "## Governance Checks",
        "",
        f"- P211 artifact hash comparison: `{checks['artifact_hashes']['status']}` ({checks['artifact_hashes']['mismatch_count']} mismatches / {checks['artifact_hashes']['artifact_count']} artifacts)",
        f"- Relevant dirty tracked/untracked status: `{'PASS' if checks['dirty_worktree']['relevant_dirty_clean'] else 'FAIL'}`",
        f"- P195 remains blocked with blank labels: `{checks['p195_gate']['status']}`",
        f"- P209 safety status: `{checks['p209_safety']['status']}` ({checks['p209_safety']['passed_case_count']}/{checks['p209_safety']['case_count']} cases)",
        f"- P210 quality-only readiness: `{checks['p210_readiness']['status']}`",
        f"- Label/proxy leakage scan: `{checks['label_leakage']['status']}`",
        f"- P212 output schema scan: `{checks['p212_output_schema']['status']}`",
        "",
        "## Dirty Worktree Scope",
        "",
        f"- Relevant tracked dirty paths: {len(checks['dirty_worktree']['tracked_relevant'])}",
        f"- Relevant untracked dirty paths: {len(checks['dirty_worktree']['untracked_relevant'])}",
        f"- Protected untracked paths ignored for readiness blocking: {checks['dirty_worktree']['ignored_protected_untracked']['count']}",
    ]
    for item in checks["dirty_worktree"]["tracked_relevant"]:
        lines.append(f"  - `{item['status']}` `{item['path']}`")
    for item in checks["dirty_worktree"]["untracked_relevant"]:
        lines.append(f"  - `{item['status']}` `{item['path']}`")

    lines.extend(
        [
            "",
            "## Artifact Drift",
            "",
        ]
    )
    if checks["artifact_hashes"]["mismatches"]:
        for item in checks["artifact_hashes"]["mismatches"]:
            lines.append(f"- `{item['path']}` recorded `{str(item['recorded_sha256'])[:12]}` current `{str(item['current_sha256'])[:12]}`")
    else:
        lines.append("- All P206-P211 artifact file hashes match the P211 index.")

    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            payload["claim_boundary"],
            "",
            "## Recommendation",
            "",
            payload["recommendation"],
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build() -> dict[str, Any]:
    p211 = load_json(P211_JSON)
    p195 = load_json(P195_JSON)
    relevant_paths = {str(item["path"]) for item in p211.get("artifacts", [])}
    checks = {
        "artifact_hashes": artifact_hash_check(p211),
        "dirty_worktree": git_status_scope(relevant_paths),
        "p195_gate": p195_gate_check(p195),
        "p209_safety": p209_check(),
        "p210_readiness": p210_check(),
        "label_leakage": label_leakage_check(),
        "p212_output_schema": output_schema_check(),
    }
    status = derive_release_status(checks)
    payload = {
        "phase": "P212-release-governance-summary",
        "release_readiness_status": status,
        "current_git": git_info(),
        "inputs": {
            "p211_index_json": rel(P211_JSON),
            "p195_gate_json": rel(P195_JSON),
        },
        "checks": checks,
        "outputs": {
            "json": rel(OUTPUT_JSON),
            "markdown": rel(OUTPUT_MD),
        },
        "claim_boundary": (
            "P212 is release governance for no-label evidence only. It does not create or infer "
            "human admission or same-object labels, does not train models, does not modify real "
            "notes or raw data, and does not support admission-control claims."
        ),
        "constraints_observed": {
            "boundary_human_labels_created_or_filled": False,
            "pair_human_labels_created_or_filled": False,
            "admission_or_same_object_labels_inferred": False,
            "training_performed": False,
            "downloads_performed": False,
            "real_notes_or_raw_data_modified": False,
            "protected_untracked_thirdparty_or_orb_paths_touched": False,
        },
        "recommendation": (
            "P213 should either restore/regenerate and commit the relevant dirty P206-P211 evidence "
            "artifacts before paper export, or explicitly archive this blocked governance summary as "
            "evidence that the current worktree is not release-clean. Keep P195 blocked until "
            "independent human admission and same-object labels exist."
        ),
    }
    write_json(OUTPUT_JSON, payload)
    write_markdown(OUTPUT_MD, payload)
    return payload


def main() -> int:
    payload = build()
    print(json.dumps({
        "release_readiness_status": payload["release_readiness_status"],
        "current_commit": payload["current_git"]["short_commit"],
        "p195_status": payload["checks"]["p195_gate"]["p195_status"],
        "p210_readiness": payload["checks"]["p210_readiness"]["readiness"],
        "artifact_hash_status": payload["checks"]["artifact_hashes"]["status"],
        "relevant_dirty_clean": payload["checks"]["dirty_worktree"]["relevant_dirty_clean"],
        "outputs": payload["outputs"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
