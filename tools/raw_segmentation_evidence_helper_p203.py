#!/usr/bin/env python3
"""Reusable raw-frame evidence helper for P203.

P203 turns the P202 exact raw segmentation/RGB-D evidence join into a small
repo-local lookup utility.  It reads local evidence artifacts only.  It does
not create labels, does not use weak/model admission fields as targets, does
not train models, and does not materialize expanded AnnotatedSemanticSet rows.
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

DEFAULT_P202_CSV = ROOT / "paper/evidence/raw_segmentation_join_audit_p202.csv"
DEFAULT_JSON = ROOT / "paper/evidence/raw_segmentation_evidence_index_p203.json"
DEFAULT_CSV = ROOT / "paper/evidence/raw_segmentation_evidence_index_p203.csv"
DEFAULT_MD = ROOT / "paper/export/raw_segmentation_evidence_helper_p203.md"

INDEX_COLUMNS = [
    "index_row_id",
    "p202_audit_row_id",
    "row_source",
    "row_role",
    "sample_id",
    "observation_id",
    "source",
    "session_id",
    "frame_index",
    "raw_segmentation_color_left_path",
    "raw_segmentation_greyscale_left_path",
    "raw_segmentation_color_right_path",
    "raw_segmentation_greyscale_right_path",
    "raw_rgb_left_path",
    "raw_depth_left_path",
    "canonical_label",
    "tracklet_id",
    "physical_key",
    "join_status",
    "join_method",
    "join_reason",
    "raw_evidence_paths_existing",
    "raw_evidence_paths_total",
]

PATH_COLUMNS = [
    "raw_segmentation_color_left_path",
    "raw_segmentation_greyscale_left_path",
    "raw_segmentation_color_right_path",
    "raw_segmentation_greyscale_right_path",
    "raw_rgb_left_path",
    "raw_depth_left_path",
]

PROHIBITED_LABEL_COLUMNS = {
    "human_admit_label",
    "human_same_object_label",
    "target_admit",
    "current_weak_label",
    "selection_v5",
    "model_prediction",
    "weak_label",
    "weak_label_a",
    "weak_label_b",
    "model_probability",
    "model_probability_a",
    "model_probability_b",
}


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def repo_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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


def load_index(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def row_key(row: dict[str, Any]) -> str:
    return str(row.get("sample_id") or row.get("observation_id") or row.get("index_row_id") or "")


def compact_row(source: dict[str, str], ordinal: int) -> dict[str, Any]:
    row = {column: source.get(column, "") for column in INDEX_COLUMNS}
    row["index_row_id"] = f"p203_{ordinal:05d}"
    row["p202_audit_row_id"] = source.get("audit_row_id", "")
    return row


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_status = Counter(str(row.get("join_status") or "") for row in rows)
    by_source = Counter(str(row.get("row_source") or "") for row in rows)
    by_session = Counter(str(row.get("session_id") or "") for row in rows)
    by_category = Counter(str(row.get("canonical_label") or "") for row in rows)
    by_source_category: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        by_source_category[str(row.get("row_source") or "")][str(row.get("canonical_label") or "")] += 1
    path_total = sum(sum(1 for column in PATH_COLUMNS if row.get(column)) for row in rows)
    path_existing = sum(sum(1 for column in PATH_COLUMNS if evidence_exists(str(row.get(column) or ""))) for row in rows)
    return {
        "rows": len(rows),
        "status_counts": dict(sorted(by_status.items())),
        "row_source_counts": dict(sorted(by_source.items())),
        "session_counts": dict(sorted(by_session.items())),
        "category_counts": dict(sorted(by_category.items())),
        "source_category_counts": {
            source: dict(sorted(counter.items())) for source, counter in sorted(by_source_category.items())
        },
        "path_existence": {
            "raw_evidence_paths_existing": path_existing,
            "raw_evidence_paths_total": path_total,
            "all_paths_exist": path_existing == path_total,
        },
    }


def validate_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    missing: list[dict[str, str]] = []
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
                        "index_row_id": str(row.get("index_row_id") or ""),
                        "row_source": str(row.get("row_source") or ""),
                        "sample_id": str(row.get("sample_id") or ""),
                        "observation_id": str(row.get("observation_id") or ""),
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
        "missing": missing[:50],
    }


def build_index(input_csv: Path, output_json: Path, output_csv: Path) -> dict[str, Any]:
    source_rows = read_csv(input_csv)
    source_fields = set(source_rows[0].keys()) if source_rows else set()
    leaked_columns = sorted(source_fields & PROHIBITED_LABEL_COLUMNS)
    if leaked_columns:
        raise SystemExit(f"Refusing to index prohibited label/proxy columns: {', '.join(leaked_columns)}")

    exact_rows = [row for row in source_rows if row.get("join_status") == "exact"]
    rows = [compact_row(row, index + 1) for index, row in enumerate(exact_rows)]
    summary = summarize_rows(rows)
    validation = validate_rows(rows)
    payload = {
        "phase": "P203-raw-segmentation-evidence-helper",
        "status": "EVIDENCE_INDEX_BUILT_P195_STILL_BLOCKED",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scientific_boundary": (
            "Reusable no-label evidence lookup only. This index contains raw frame evidence paths and "
            "provenance from P202 exact joins; it does not contain generated human/admission/same-object "
            "labels and does not train or materialize expanded AnnotatedSemanticSet training rows."
        ),
        "inputs": {"p202_csv": rel(input_csv)},
        "outputs": {"json": rel(output_json), "csv": rel(output_csv)},
        "constraints_observed": {
            "human_labels_created": False,
            "weak_admission_or_model_predictions_used_as_targets": False,
            "admission_or_semantic_stability_training_performed": False,
            "expanded_annotated_semantic_training_rows_materialized": False,
            "downloads_performed": False,
        },
        "p195_status": "BLOCKED",
        "summary": summary,
        "validation": validation,
        "rows": rows,
    }
    write_json(output_json, payload)
    write_csv(output_csv, rows, INDEX_COLUMNS)
    return payload


def lookup_rows(rows: list[dict[str, Any]], sample_id: str = "", observation_id: str = "") -> list[dict[str, Any]]:
    matches = rows
    if sample_id:
        matches = [row for row in matches if str(row.get("sample_id") or "") == sample_id]
    if observation_id:
        matches = [row for row in matches if str(row.get("observation_id") or "") == observation_id]
    return matches


def print_lookup(matches: list[dict[str, Any]]) -> None:
    if not matches:
        print(json.dumps({"matches": 0}, indent=2, sort_keys=True))
        return
    out = []
    for row in matches:
        out.append(
            {
                "index_row_id": row.get("index_row_id", ""),
                "row_source": row.get("row_source", ""),
                "row_role": row.get("row_role", ""),
                "sample_id": row.get("sample_id", ""),
                "observation_id": row.get("observation_id", ""),
                "session_id": row.get("session_id", ""),
                "frame_index": row.get("frame_index", ""),
                "canonical_label": row.get("canonical_label", ""),
                "tracklet_id": row.get("tracklet_id", ""),
                "physical_key": row.get("physical_key", ""),
                "paths": {column: row.get(column, "") for column in PATH_COLUMNS if row.get(column)},
            }
        )
    print(json.dumps({"matches": len(matches), "rows": out}, indent=2, sort_keys=True))


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    validation = payload["validation"]
    lines = [
        "# P203 Raw Segmentation Evidence Helper",
        "",
        f"**Status:** {payload['status']}",
        "",
        "## Boundary",
        "",
        payload["scientific_boundary"],
        "",
        "## Index Counts",
        "",
        f"- Rows: {summary['rows']}",
        f"- Join status counts: {summary['status_counts']}",
        f"- Row source counts: {summary['row_source_counts']}",
        f"- Raw evidence paths: {validation['raw_evidence_paths_existing']}/{validation['raw_evidence_paths_total']} existing",
        f"- All paths exist: {validation['all_paths_exist']}",
        "",
        "## CLI",
        "",
        "```bash",
        "python3 tools/raw_segmentation_evidence_helper_p203.py build",
        "python3 tools/raw_segmentation_evidence_helper_p203.py lookup --sample-id SAMPLE_ID",
        "python3 tools/raw_segmentation_evidence_helper_p203.py lookup --observation-id OBSERVATION_ID",
        "python3 tools/raw_segmentation_evidence_helper_p203.py summarize",
        "python3 tools/raw_segmentation_evidence_helper_p203.py validate",
        "```",
        "",
        "## Outputs",
        "",
        f"- JSON index: `{payload['outputs']['json']}`",
        f"- CSV index: `{payload['outputs']['csv']}`",
        "",
        "## Label Gate",
        "",
        "- P195 remains `BLOCKED`.",
        "- Human label columns remain blank; this helper does not write or infer them.",
        "",
        "## P204 Recommendation",
        "",
        "Use this helper for reviewer/audit sampling and raw evidence packet inspection. Do not expand "
        "AnnotatedSemanticSet categories into object-level training rows until route/session/object identity "
        "is available for a safe join.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="P203 no-label raw segmentation evidence helper")
    parser.add_argument("--index-json", default=str(DEFAULT_JSON))
    parser.add_argument("--index-csv", default=str(DEFAULT_CSV))
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="Build/cache the P203 index from P202 exact rows")
    build.add_argument("--p202-csv", default=str(DEFAULT_P202_CSV))
    build.add_argument("--output-md", default=str(DEFAULT_MD))

    lookup = subparsers.add_parser("lookup", help="Lookup raw evidence by sample_id and/or observation_id")
    lookup.add_argument("--sample-id", default="")
    lookup.add_argument("--observation-id", default="")

    subparsers.add_parser("summarize", help="Summarize join coverage by source, session, and category")
    subparsers.add_parser("validate", help="Validate indexed raw evidence paths still exist")

    args = parser.parse_args()
    index_json = repo_path(args.index_json)
    index_csv = repo_path(args.index_csv)

    if args.command == "build":
        payload = build_index(repo_path(args.p202_csv), index_json, index_csv)
        write_markdown(repo_path(args.output_md), payload)
        print(json.dumps({"status": payload["status"], "summary": payload["summary"], "validation": payload["validation"]}, indent=2, sort_keys=True))
        return 0

    payload = load_index(index_json)
    rows = payload.get("rows") or []
    if args.command == "lookup":
        if not args.sample_id and not args.observation_id:
            raise SystemExit("lookup requires --sample-id and/or --observation-id")
        print_lookup(lookup_rows(rows, args.sample_id, args.observation_id))
        return 0
    if args.command == "summarize":
        print(json.dumps(summarize_rows(rows), indent=2, sort_keys=True))
        return 0
    if args.command == "validate":
        result = validate_rows(rows)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["all_paths_exist"] else 2
    raise SystemExit(f"unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
