#!/usr/bin/env python3
"""Triage the P204 raw evidence packet for P205.

This is a deterministic raw-evidence QA pass. It checks path readability,
image dimensions, simple segmentation/depth non-empty properties, and packet
diversity. It does not create, infer, or consume admission/same-object labels
and does not train any model.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_PACKET_JSON = ROOT / "paper/evidence/raw_evidence_audit_packet_p204.json"
DEFAULT_INDEX_JSON = ROOT / "paper/evidence/raw_segmentation_evidence_index_p203.json"
DEFAULT_OUTPUT_JSON = ROOT / "paper/evidence/raw_evidence_issue_triage_p205.json"
DEFAULT_OUTPUT_CSV = ROOT / "paper/evidence/raw_evidence_issue_triage_p205.csv"
DEFAULT_OUTPUT_MD = ROOT / "paper/export/raw_evidence_issue_triage_p205.md"

PATH_COLUMNS = [
    "raw_segmentation_color_left_path",
    "raw_segmentation_greyscale_left_path",
    "raw_segmentation_color_right_path",
    "raw_segmentation_greyscale_right_path",
    "raw_rgb_left_path",
    "raw_depth_left_path",
]

SEGMENTATION_COLUMNS = [
    "raw_segmentation_color_left_path",
    "raw_segmentation_greyscale_left_path",
    "raw_segmentation_color_right_path",
    "raw_segmentation_greyscale_right_path",
]

TRIAGE_CSV_COLUMNS = [
    "audit_sample_id",
    "p203_index_row_id",
    "row_source",
    "row_role",
    "sample_id",
    "observation_id",
    "source",
    "session_id",
    "frame_index",
    "tracklet_id",
    "physical_key",
    "path_count",
    "paths_existing",
    "paths_readable",
    "row_dimensions",
    "row_dimensions_consistent",
    "segmentation_nontrivial_count",
    "depth_nonzero_pixel_count",
    "issue_level",
    "issue_codes",
    "warning_codes",
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


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def repo_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_image_tools() -> tuple[Any | None, Any | None, str]:
    try:
        from PIL import Image
    except Exception:
        return None, None, "pillow_unavailable"
    try:
        import numpy as np
    except Exception:
        return Image, None, "pillow_only_numpy_unavailable"
    return Image, np, "pillow_numpy"


def read_path_bytes(path_value: str) -> tuple[bytes | None, dict[str, Any]]:
    info: dict[str, Any] = {
        "path": path_value,
        "exists": False,
        "readable": False,
        "file_size": 0,
        "storage": "filesystem",
        "error": "",
    }
    if not path_value:
        info["error"] = "blank_path"
        return None, info
    if "::" in path_value:
        zip_part, member = path_value.split("::", 1)
        info["storage"] = "zip_member"
        try:
            with zipfile.ZipFile(repo_path(zip_part)) as archive:
                zinfo = archive.getinfo(member)
                data = archive.read(member)
            info["exists"] = True
            info["readable"] = True
            info["file_size"] = int(zinfo.file_size)
            return data, info
        except Exception as exc:
            info["error"] = f"{type(exc).__name__}: {exc}"
            return None, info
    path = repo_path(path_value)
    try:
        if not path.exists():
            info["error"] = "missing_path"
            return None, info
        info["exists"] = True
        info["file_size"] = int(path.stat().st_size)
        data = path.read_bytes()
        info["readable"] = True
        return data, info
    except Exception as exc:
        info["error"] = f"{type(exc).__name__}: {exc}"
        return None, info


def scalar(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    return value


def image_stats(path_value: str, column: str, Image: Any | None, np: Any | None) -> dict[str, Any]:
    data, info = read_path_bytes(path_value)
    info["path_column"] = column
    info["image_readable"] = False
    info["width"] = None
    info["height"] = None
    info["mode"] = ""
    info["bands"] = 0
    info["min"] = None
    info["max"] = None
    info["mean"] = None
    info["nonzero_pixels"] = None
    info["constant_image"] = None
    info["unique_values"] = None
    info["unique_pixel_values"] = None

    if data is None or Image is None:
        return info
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            info["image_readable"] = True
            info["width"], info["height"] = [int(v) for v in image.size]
            info["mode"] = str(image.mode)
            info["bands"] = len(image.getbands())
            extrema = image.getextrema()
            if info["bands"] == 1:
                min_value, max_value = extrema
            else:
                min_value = min(channel[0] for channel in extrema)
                max_value = max(channel[1] for channel in extrema)
            info["min"] = scalar(min_value)
            info["max"] = scalar(max_value)
            info["constant_image"] = bool(min_value == max_value)
            if np is not None:
                arr = np.asarray(image)
                info["mean"] = float(arr.mean()) if arr.size else None
                if arr.ndim == 2:
                    info["nonzero_pixels"] = int(np.count_nonzero(arr))
                    info["unique_values"] = int(np.unique(arr).size)
                elif arr.ndim == 3:
                    pixel_arr = arr.reshape(-1, arr.shape[-1])
                    info["nonzero_pixels"] = int(np.count_nonzero(np.any(pixel_arr != 0, axis=1)))
                    info["unique_pixel_values"] = int(np.unique(pixel_arr, axis=0).shape[0])
        return info
    except Exception as exc:
        info["error"] = f"{type(exc).__name__}: {exc}"
        return info


def packet_rows(packet: dict[str, Any]) -> list[dict[str, Any]]:
    rows = packet.get("rows", [])
    if not isinstance(rows, list):
        raise SystemExit("P204 packet JSON has no list-valued rows field")
    return rows


def check_prohibited_columns(rows: list[dict[str, Any]], context: str) -> list[str]:
    columns: set[str] = set()
    for row in rows:
        columns.update(row.keys())
    leaked = sorted(columns & PROHIBITED_COLUMNS)
    if leaked:
        raise SystemExit(f"Refusing to triage {context}; prohibited label/proxy columns present: {', '.join(leaked)}")
    return leaked


def row_dimension_summary(file_checks: list[dict[str, Any]]) -> tuple[list[str], bool]:
    dims = sorted(
        {
            f"{check['width']}x{check['height']}"
            for check in file_checks
            if check.get("image_readable") and check.get("width") and check.get("height")
        }
    )
    return dims, len(dims) <= 1


def duplicate_map(rows: list[dict[str, Any]], key_fn: Any) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        key = key_fn(row)
        if key:
            grouped[str(key)].append(str(row.get("audit_sample_id") or ""))
    return {key: ids for key, ids in sorted(grouped.items()) if len(ids) > 1}


def triage_rows(rows: list[dict[str, Any]], Image: Any | None, np: Any | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    duplicate_physical = duplicate_map(rows, lambda row: row.get("physical_key", ""))
    duplicate_frame = duplicate_map(rows, lambda row: (row.get("session_id", ""), row.get("frame_index", "")))
    duplicate_sample = duplicate_map(rows, lambda row: row.get("sample_id", ""))

    detail_rows: list[dict[str, Any]] = []
    csv_rows: list[dict[str, Any]] = []
    for row in rows:
        issue_codes: list[str] = []
        warning_codes: list[str] = []
        file_checks = [
            image_stats(str(row.get(column) or ""), column, Image, np)
            for column in PATH_COLUMNS
            if row.get(column)
        ]

        if len(file_checks) != len(PATH_COLUMNS):
            issue_codes.append("missing_expected_path_column")
        if any(not check["exists"] for check in file_checks):
            issue_codes.append("path_missing")
        if any(check["file_size"] == 0 for check in file_checks):
            issue_codes.append("zero_byte_file")
        if any(not check["readable"] for check in file_checks):
            issue_codes.append("path_unreadable")
        if Image is not None and any(not check["image_readable"] for check in file_checks):
            issue_codes.append("image_unreadable")

        dimensions, dimensions_consistent = row_dimension_summary(file_checks)
        if not dimensions_consistent:
            issue_codes.append("dimension_mismatch")

        segmentation_checks = [check for check in file_checks if check["path_column"] in SEGMENTATION_COLUMNS]
        trivial_segmentation = [check["path_column"] for check in segmentation_checks if check.get("constant_image") is True]
        if trivial_segmentation:
            warning_codes.append("segmentation_constant_image")
        segmentation_nontrivial_count = sum(1 for check in segmentation_checks if check.get("constant_image") is False)

        depth_check = next((check for check in file_checks if check["path_column"] == "raw_depth_left_path"), None)
        depth_nonzero = depth_check.get("nonzero_pixels") if depth_check else None
        if depth_check and depth_check.get("file_size") == 0:
            issue_codes.append("depth_zero_byte_file")
        if depth_check and depth_check.get("image_readable") and depth_check.get("max") == 0:
            warning_codes.append("depth_all_zero")

        physical_key = str(row.get("physical_key") or "")
        frame_key = str((row.get("session_id", ""), row.get("frame_index", "")))
        sample_key = str(row.get("sample_id") or "")
        if physical_key in duplicate_physical:
            warning_codes.append("duplicate_physical_key")
        if frame_key in duplicate_frame:
            warning_codes.append("duplicate_session_frame")
        if sample_key in duplicate_sample:
            warning_codes.append("duplicate_sample_id")

        issue_level = "ERROR" if issue_codes else ("WARN" if warning_codes else "OK")
        csv_row = {
            "audit_sample_id": row.get("audit_sample_id", ""),
            "p203_index_row_id": row.get("p203_index_row_id", ""),
            "row_source": row.get("row_source", ""),
            "row_role": row.get("row_role", ""),
            "sample_id": row.get("sample_id", ""),
            "observation_id": row.get("observation_id", ""),
            "source": row.get("source", ""),
            "session_id": row.get("session_id", ""),
            "frame_index": row.get("frame_index", ""),
            "tracklet_id": row.get("tracklet_id", ""),
            "physical_key": physical_key,
            "path_count": len(file_checks),
            "paths_existing": sum(1 for check in file_checks if check["exists"]),
            "paths_readable": sum(1 for check in file_checks if check["readable"] and check["image_readable"]),
            "row_dimensions": ";".join(dimensions),
            "row_dimensions_consistent": dimensions_consistent,
            "segmentation_nontrivial_count": segmentation_nontrivial_count,
            "depth_nonzero_pixel_count": depth_nonzero if depth_nonzero is not None else "",
            "issue_level": issue_level,
            "issue_codes": ";".join(sorted(set(issue_codes))),
            "warning_codes": ";".join(sorted(set(warning_codes))),
        }
        csv_rows.append(csv_row)
        detail_rows.append(
            {
                **csv_row,
                "file_checks": file_checks,
                "source_row": {
                    key: row.get(key, "")
                    for key in [
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
                },
            }
        )
    return detail_rows, csv_rows


def summarize(csv_rows: list[dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    issue_counter = Counter()
    warning_counter = Counter()
    for row in csv_rows:
        for code in str(row.get("issue_codes") or "").split(";"):
            if code:
                issue_counter[code] += 1
        for code in str(row.get("warning_codes") or "").split(";"):
            if code:
                warning_counter[code] += 1
    path_total = sum(int(row["path_count"]) for row in csv_rows)
    paths_existing = sum(int(row["paths_existing"]) for row in csv_rows)
    paths_readable = sum(int(row["paths_readable"]) for row in csv_rows)
    return {
        "sample_count": len(csv_rows),
        "path_total": path_total,
        "paths_existing": paths_existing,
        "paths_readable_images": paths_readable,
        "rows_by_issue_level": dict(sorted(Counter(row["issue_level"] for row in csv_rows).items())),
        "issue_counts": dict(sorted(issue_counter.items())),
        "warning_counts": dict(sorted(warning_counter.items())),
        "dimension_counts": dict(sorted(Counter(row["row_dimensions"] for row in csv_rows).items())),
        "category_counts": dict(sorted(Counter(str(row.get("canonical_label") or "") for row in rows).items())),
        "source_counts": dict(sorted(Counter(str(row.get("source") or "") for row in rows).items())),
        "row_source_counts": dict(sorted(Counter(str(row.get("row_source") or "") for row in rows).items())),
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    diversity = payload["diversity"]
    lines = [
        "# P205 Raw Evidence Issue Triage",
        "",
        f"**Status:** {payload['status']}",
        "",
        "## Boundary",
        "",
        payload["scientific_boundary"],
        "",
        "## Inputs and Outputs",
        "",
        f"- P204 packet: `{payload['inputs']['p204_packet_json']}`",
        f"- P203 index: `{payload['inputs']['p203_index_json']}`",
        f"- JSON triage: `{payload['outputs']['json']}`",
        f"- CSV triage: `{payload['outputs']['csv']}`",
        "",
        "## Summary",
        "",
        f"- Samples triaged: {summary['sample_count']}",
        f"- Referenced paths: {summary['paths_existing']}/{summary['path_total']} existing",
        f"- Readable images: {summary['paths_readable_images']}/{summary['path_total']}",
        f"- Rows by issue level: {summary['rows_by_issue_level']}",
        f"- Issue counts: {summary['issue_counts']}",
        f"- Warning counts: {summary['warning_counts']}",
        f"- Dimension counts: {summary['dimension_counts']}",
        "",
        "## Diversity Flags",
        "",
        f"- Unique physical keys: {diversity['unique_physical_keys']}/{diversity['rows_with_physical_key']} nonblank rows",
        f"- Duplicate physical keys: {len(diversity['duplicate_physical_keys'])}",
        f"- Unique session/frame pairs: {diversity['unique_session_frame_pairs']}/{summary['sample_count']} rows",
        f"- Duplicate session/frame pairs: {len(diversity['duplicate_session_frame_pairs'])}",
        f"- Duplicate sample IDs: {len(diversity['duplicate_sample_ids'])}",
        "",
        "## Row Triage",
        "",
        "| sample | level | dimensions | issue_codes | warning_codes | depth_nonzero_pixels |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["triage_rows"]:
        lines.append(
            "| {audit_sample_id} | {issue_level} | {row_dimensions} | {issue_codes} | {warning_codes} | {depth_nonzero_pixel_count} |".format(
                **{key: str(value).replace("|", "\\|") for key, value in row.items()}
            )
        )
    lines.extend(
        [
            "",
            "## Label Gate",
            "",
            "- P195 remains `BLOCKED`.",
            "- Human admission and same-object label fields remain blank in the independent-supervision gate.",
            "- This triage records file/readability/shape/non-empty evidence issues only; it does not support admission-control claims.",
            "",
            "## P206 Recommendation",
            "",
            "Use P205 as the raw-evidence QA baseline. If a future review step is needed, create a separate no-training visual inspection protocol that records evidence quality notes only, while keeping admission/same-object labels behind the independent human-label workflow.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_triage(packet_json: Path, index_json: Path, output_json: Path, output_csv: Path, output_md: Path) -> dict[str, Any]:
    packet = load_json(packet_json)
    index = load_json(index_json)
    rows = packet_rows(packet)
    index_rows = packet_rows(index)
    check_prohibited_columns(rows, "P204 packet")
    check_prohibited_columns(index_rows, "P203 index")

    Image, np, image_backend = load_image_tools()
    detail_rows, csv_rows = triage_rows(rows, Image, np)
    duplicate_physical = duplicate_map(rows, lambda row: row.get("physical_key", ""))
    duplicate_frame = duplicate_map(rows, lambda row: (row.get("session_id", ""), row.get("frame_index", "")))
    duplicate_sample = duplicate_map(rows, lambda row: row.get("sample_id", ""))
    physical_keys = [str(row.get("physical_key") or "") for row in rows if row.get("physical_key")]
    session_frame_pairs = [str((row.get("session_id", ""), row.get("frame_index", ""))) for row in rows]

    payload = {
        "phase": "P205-raw-evidence-issue-triage",
        "status": "ISSUE_TRIAGE_COMPLETE_P195_STILL_BLOCKED",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scientific_boundary": (
            "Raw evidence QA only. P205 validates local file existence, readability, image dimensions, "
            "segmentation non-triviality, depth readability/statistics, and packet diversity. It does not "
            "create or infer admission/same-object labels, does not use weak targets/model predictions as "
            "labels, and does not train admission-control or semantic-stability models."
        ),
        "inputs": {"p204_packet_json": rel(packet_json), "p203_index_json": rel(index_json)},
        "outputs": {"json": rel(output_json), "csv": rel(output_csv), "markdown": rel(output_md)},
        "image_backend": image_backend,
        "constraints_observed": {
            "human_labels_created": False,
            "admission_or_same_object_labels_inferred": False,
            "weak_admission_or_model_predictions_used_as_labels": False,
            "admission_or_semantic_stability_training_performed": False,
            "downloads_performed": False,
            "raw_images_or_data_modified": False,
        },
        "p195_status": "BLOCKED",
        "summary": summarize(csv_rows, rows),
        "diversity": {
            "rows_with_physical_key": len(physical_keys),
            "unique_physical_keys": len(set(physical_keys)),
            "duplicate_physical_keys": duplicate_physical,
            "unique_session_frame_pairs": len(set(session_frame_pairs)),
            "duplicate_session_frame_pairs": duplicate_frame,
            "duplicate_sample_ids": duplicate_sample,
        },
        "triage_rows": detail_rows,
    }
    write_json(output_json, payload)
    write_csv(output_csv, csv_rows, TRIAGE_CSV_COLUMNS)
    write_markdown(output_md, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Triage P204 raw evidence packet for P205")
    parser.add_argument("--packet-json", default=str(DEFAULT_PACKET_JSON))
    parser.add_argument("--index-json", default=str(DEFAULT_INDEX_JSON))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT_CSV))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    args = parser.parse_args()

    payload = build_triage(
        repo_path(args.packet_json),
        repo_path(args.index_json),
        repo_path(args.output_json),
        repo_path(args.output_csv),
        repo_path(args.output_md),
    )
    print(
        json.dumps(
            {
                "status": payload["status"],
                "image_backend": payload["image_backend"],
                "summary": payload["summary"],
                "diversity": payload["diversity"],
                "p195_status": payload["p195_status"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if not payload["summary"]["issue_counts"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
