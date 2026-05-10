#!/usr/bin/env python3
"""Audit raw TorWIC segmentation-to-observation joins for P202.

P202 is a mapping and quality-report phase only.  It reads local P193/P197
rows, generated observation indexes/manifests, and local TorWIC raw zips or
extracted files.  It does not create human labels, does not use weak/model
admission predictions as target labels, and does not train models.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data/TorWIC_SLAM_Dataset"
ANNOTATED_ZIP = DATA_ROOT / "Oct. 12, 2022/AnnotatedSemanticSet_Finetuning.zip"

DATE_BY_TOKEN = {
    "2022-06-15": "Jun. 15, 2022",
    "2022-06-23": "Jun. 23, 2022",
    "2022-10-12": "Oct. 12, 2022",
}

P193_CSV = ROOT / "paper/evidence/admission_frame_dataset_p193.csv"
P199_CSV = ROOT / "paper/evidence/semantic_stability_dataset_p199.csv"
P197_BOUNDARY_CSV = ROOT / "paper/evidence/admission_boundary_label_sheet_p197_semantic_review.csv"
P197_PAIR_CSV = ROOT / "paper/evidence/association_pair_candidates_p197_semantic_review.csv"

P199_CATEGORIES = {
    "fork_truck",
    "rack_shelf",
    "fixed_machinery",
    "misc_static_feature",
    "pylon_cone",
}

CSV_COLUMNS = [
    "audit_row_id",
    "row_source",
    "row_role",
    "sample_id",
    "observation_id",
    "source",
    "session_id",
    "frame_id",
    "frame_index",
    "observation_index_path",
    "manifest_path",
    "observation_index_exists",
    "observation_found",
    "manifest_exists",
    "manifest_instance_found",
    "date_dir",
    "route",
    "join_status",
    "join_method",
    "join_reason",
    "raw_segmentation_color_left_path",
    "raw_segmentation_greyscale_left_path",
    "raw_segmentation_color_right_path",
    "raw_segmentation_greyscale_right_path",
    "raw_rgb_left_path",
    "raw_depth_left_path",
    "raw_evidence_paths_existing",
    "raw_evidence_paths_total",
    "source_semantic_path",
    "canonical_label",
    "resolved_label",
    "tracklet_id",
    "physical_key",
]


@dataclass(frozen=True)
class ZipIndex:
    zip_path: Path
    members: frozenset[str]


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
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


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def path_from_repo(value: str) -> Path:
    if not value:
        return Path("")
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT / path


def evidence_exists(value: str) -> bool:
    if not value:
        return False
    if "::" in value:
        zip_part, member = value.split("::", 1)
        zip_path = path_from_repo(zip_part)
        try:
            with zipfile.ZipFile(zip_path) as archive:
                return member in archive.namelist()
        except Exception:
            return False
    return path_from_repo(value).exists()


def session_to_date_route(session_id: str) -> tuple[str | None, str | None]:
    match = re.search(r"2022-\d\d-\d\d", session_id or "")
    if not match:
        return None, None
    date_token = match.group(0)
    date_dir = DATE_BY_TOKEN.get(date_token)
    if not date_dir:
        return None, None
    route = session_id.split(date_token + "__", 1)[-1]
    return date_dir, route


def frame_token(value: Any) -> str | None:
    try:
        return f"{int(str(value).strip()):06d}"
    except Exception:
        return None


def build_zip_index(data_root: Path) -> dict[tuple[str, str], ZipIndex]:
    out: dict[tuple[str, str], ZipIndex] = {}
    for zip_path in sorted(data_root.glob("*/*.zip")):
        if zip_path.name == ANNOTATED_ZIP.name:
            continue
        try:
            with zipfile.ZipFile(zip_path) as archive:
                members = frozenset(archive.namelist())
        except Exception:
            continue
        out[(zip_path.parent.name, zip_path.stem)] = ZipIndex(zip_path=zip_path, members=members)
    return out


def build_frame_route_index(zip_index: dict[tuple[str, str], ZipIndex]) -> dict[str, set[tuple[str, str]]]:
    out: dict[str, set[tuple[str, str]]] = defaultdict(set)
    pattern = re.compile(r"/image_left/(\d{6})\.png$")
    for key, index in zip_index.items():
        for member in index.members:
            match = pattern.search(member)
            if match:
                out[match.group(1)].add(key)
    return out


def iter_json_files(*roots: Path) -> list[Path]:
    paths: list[Path] = []
    for root in roots:
        if root.exists():
            paths.extend(root.glob("**/*.json"))
    return sorted(set(paths))


def build_observation_indexes() -> tuple[dict[str, Path], dict[str, Path]]:
    by_session: dict[str, Path] = {}
    by_observation: dict[str, Path] = {}
    for path in iter_json_files(ROOT / "outputs", ROOT / "tmp", ROOT / "examples"):
        if "thirdparty" in path.parts or path.name != "observations_index.json":
            continue
        payload = load_json(path)
        if not payload:
            continue
        session_id = str(payload.get("session_id") or "")
        if session_id and session_id not in by_session:
            by_session[session_id] = path
        for observation in payload.get("observations") or []:
            observation_id = str(observation.get("observation_id") or "")
            if observation_id and observation_id not in by_observation:
                by_observation[observation_id] = path
    return by_session, by_observation


def find_observation(index_path: Path, observation_id: str, object_name: str = "") -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    payload = load_json(index_path)
    if not payload:
        return None, None
    observations = payload.get("observations") or []
    found = None
    if observation_id:
        found = next((item for item in observations if str(item.get("observation_id")) == observation_id), None)
    if found is None and object_name:
        found = next((item for item in observations if str(item.get("object_name")) == object_name), None)
    return found, payload


def find_manifest_instance(manifest_path: str, object_name: str, resolved_label: str) -> tuple[bool, str]:
    path = path_from_repo(manifest_path)
    payload = load_json(path)
    if not payload:
        return False, ""
    for instance in payload.get("instances") or []:
        if object_name and str(instance.get("object_name")) == object_name:
            return True, rel(path)
        if resolved_label and str(instance.get("resolved_label")) == resolved_label:
            return True, rel(path)
    return False, rel(path)


def add_member_path(paths: dict[str, str], key: str, index: ZipIndex | None, route: str, subdir: str, frame: str) -> None:
    if not index:
        return
    member = f"{route}/{subdir}/{frame}.png"
    if member in index.members:
        paths[key] = f"{rel(index.zip_path)}::{member}"


def local_raw_path(date_dir: str, route: str, subdir: str, frame: str) -> str:
    path = DATA_ROOT / date_dir / route / route / subdir / f"{frame}.png"
    return rel(path) if path.exists() else ""


def raw_frame_evidence(
    session_id: str,
    frame_index: str,
    zip_index: dict[tuple[str, str], ZipIndex],
) -> dict[str, Any]:
    date_dir, route = session_to_date_route(session_id)
    if not date_dir or not route:
        return {
            "status": "unmatched",
            "reason": "session_id_does_not_contain_supported_torwic_date_route",
            "date_dir": date_dir or "",
            "route": route or "",
            "paths": {},
        }
    frame = frame_token(frame_index)
    if not frame:
        return {
            "status": "unmatched",
            "reason": "invalid_or_missing_frame_index",
            "date_dir": date_dir,
            "route": route,
            "paths": {},
        }
    index = zip_index.get((date_dir, route))
    paths: dict[str, str] = {}
    for key, subdir in [
        ("raw_segmentation_color_left_path", "segmentation_color_left"),
        ("raw_segmentation_greyscale_left_path", "segmentation_greyscale_left"),
        ("raw_segmentation_color_right_path", "segmentation_color_right"),
        ("raw_segmentation_greyscale_right_path", "segmentation_greyscale_right"),
        ("raw_rgb_left_path", "image_left"),
        ("raw_depth_left_path", "depth_left"),
    ]:
        local = local_raw_path(date_dir, route, subdir, frame)
        if local:
            paths[key] = local
        else:
            add_member_path(paths, key, index, route, subdir, frame)
    has_left_masks = bool(paths.get("raw_segmentation_color_left_path")) and bool(paths.get("raw_segmentation_greyscale_left_path"))
    has_rgb_depth = bool(paths.get("raw_rgb_left_path")) and bool(paths.get("raw_depth_left_path"))
    if has_left_masks and has_rgb_depth:
        status = "exact"
        reason = "session_date_route_frame_found_left_color_greyscale_rgb_depth"
    elif any(paths.values()):
        status = "partial"
        reason = "session_date_route_frame_has_some_raw_evidence_but_not_complete_left_mask_rgb_depth"
    else:
        status = "unmatched"
        reason = "no_raw_frame_members_or_extracted_files_found"
    return {
        "status": status,
        "reason": reason,
        "date_dir": date_dir,
        "route": route,
        "frame": frame,
        "paths": paths,
    }


def observation_id_from_sample(sample_id: str) -> str:
    return sample_id.split(":", 1)[1] if ":" in sample_id else sample_id


def object_name_from_observation_id(observation_id: str) -> str:
    match = re.search(r"_(\d{6})_(\d{3})$", observation_id or "")
    if not match:
        return ""
    # The numeric suffix alone is not a stable object name, so leave object
    # identity to observation-index lookup.
    return ""


def audit_observation_row(
    row: dict[str, str],
    row_source: str,
    row_role: str,
    audit_row_id: str,
    by_session: dict[str, Path],
    by_observation: dict[str, Path],
    zip_index: dict[tuple[str, str], ZipIndex],
) -> dict[str, Any]:
    sample_id = row.get("sample_id") or row.get("p193_sample_id") or ""
    observation_id = row.get("observation_id") or observation_id_from_sample(sample_id)
    session_id = row.get("session_id") or ""
    frame_index = row.get("frame_index") or ""
    if not frame_index and row.get("frame_id"):
        frame_index = row["frame_id"].rsplit("_", 1)[-1]
    object_name = row.get("object_name") or object_name_from_observation_id(observation_id)
    index_path_text = row.get("observation_index_path") or ""
    index_path = path_from_repo(index_path_text) if index_path_text else by_observation.get(observation_id) or by_session.get(session_id)
    observation_found = False
    manifest_path = ""
    manifest_exists = False
    manifest_instance_found = False
    observation_index_exists = bool(index_path and Path(index_path).exists())
    resolved_label = row.get("resolved_label") or ""
    canonical_label = row.get("canonical_label") or ""
    if observation_index_exists:
        observation, payload = find_observation(Path(index_path), observation_id, object_name)
        observation_found = observation is not None
        if observation:
            object_name = object_name or str(observation.get("object_name") or "")
            resolved_label = resolved_label or str(observation.get("resolved_label") or observation.get("grounding_label") or "")
            canonical_label = canonical_label or resolved_label
            manifest_path = str((payload or {}).get("manifest_path") or "")
            if not frame_index:
                frame_index = str(observation.get("frame_index") or "")
        elif payload:
            manifest_path = str(payload.get("manifest_path") or "")
    if manifest_path:
        manifest_exists = path_from_repo(manifest_path).exists()
        manifest_instance_found, manifest_path = find_manifest_instance(manifest_path, object_name, resolved_label)

    raw = raw_frame_evidence(session_id, frame_index, zip_index)
    paths = raw["paths"]
    evidence_paths = [value for value in paths.values() if value]
    existing_count = sum(1 for value in evidence_paths if evidence_exists(value))
    complete_index_join = observation_index_exists and observation_found
    if raw["status"] == "exact" and complete_index_join:
        join_status = "exact"
        join_method = "observation_id_or_session_index_plus_torwic_session_date_route_frame"
        join_reason = raw["reason"]
    elif raw["status"] in {"exact", "partial"} or complete_index_join:
        join_status = "partial"
        join_method = "partial_observation_or_raw_frame_evidence"
        join_reason = raw["reason"] if raw["status"] != "unmatched" else "observation_index_join_found_without_raw_frame_evidence"
    else:
        join_status = "unmatched"
        join_method = "none"
        join_reason = raw["reason"]

    out = {
        "audit_row_id": audit_row_id,
        "row_source": row_source,
        "row_role": row_role,
        "sample_id": sample_id,
        "observation_id": observation_id,
        "source": row.get("source", ""),
        "session_id": session_id,
        "frame_id": row.get("frame_id", ""),
        "frame_index": frame_index,
        "observation_index_path": rel(index_path) if index_path else "",
        "manifest_path": manifest_path,
        "observation_index_exists": int(observation_index_exists),
        "observation_found": int(observation_found),
        "manifest_exists": int(manifest_exists),
        "manifest_instance_found": int(manifest_instance_found),
        "date_dir": raw.get("date_dir", ""),
        "route": raw.get("route", ""),
        "join_status": join_status,
        "join_method": join_method,
        "join_reason": join_reason,
        "source_semantic_path": row.get("source_semantic_path") or row.get("source_semantic_path_a") or row.get("source_semantic_path_b") or "",
        "canonical_label": canonical_label,
        "resolved_label": resolved_label,
        "tracklet_id": row.get("tracklet_id", ""),
        "physical_key": row.get("physical_key", ""),
        "raw_evidence_paths_existing": existing_count,
        "raw_evidence_paths_total": len(evidence_paths),
    }
    out.update({column: paths.get(column, "") for column in CSV_COLUMNS if column.endswith("_path") and column.startswith("raw_")})
    return out


def make_attempt_rows(
    by_session: dict[str, Path],
    by_observation: dict[str, Path],
    zip_index: dict[tuple[str, str], ZipIndex],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    counter = 1
    for source_name, path in [("p193", P193_CSV), ("p199", P199_CSV)]:
        for row in read_csv(path):
            rows.append(audit_observation_row(row, source_name, "observation", f"p202_{counter:05d}", by_session, by_observation, zip_index))
            counter += 1
    for row in read_csv(P197_BOUNDARY_CSV):
        rows.append(audit_observation_row(row, "p197_boundary", "review_observation", f"p202_{counter:05d}", by_session, by_observation, zip_index))
        counter += 1
    for row in read_csv(P197_PAIR_CSV):
        for side in ["a", "b"]:
            side_row = {
                "sample_id": row.get(f"sample_id_{side}", ""),
                "session_id": row.get(f"session_id_{side}", ""),
                "frame_id": row.get(f"frame_id_{side}", ""),
                "frame_index": row.get(f"frame_id_{side}", "").rsplit("_", 1)[-1],
                "source": row.get("source", ""),
                "canonical_label": row.get("canonical_label", ""),
                "source_semantic_path": row.get(f"source_semantic_path_{side}", ""),
            }
            rows.append(audit_observation_row(side_row, "p197_pair", f"pair_side_{side}", f"p202_{counter:05d}", by_session, by_observation, zip_index))
            counter += 1
    return rows


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_status = Counter(row["join_status"] for row in rows)
    by_source_status: dict[str, Counter[str]] = defaultdict(Counter)
    by_session_status: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        by_source_status[row.get("row_source", "")][row["join_status"]] += 1
        by_session_status[row.get("session_id", "")][row["join_status"]] += 1
    def rates(counter: Counter[str]) -> dict[str, Any]:
        total = sum(counter.values())
        return {
            "total": total,
            "exact": counter["exact"],
            "partial": counter["partial"],
            "unmatched": counter["unmatched"],
            "exact_rate": round(counter["exact"] / total, 6) if total else 0.0,
            "partial_rate": round(counter["partial"] / total, 6) if total else 0.0,
            "unmatched_rate": round(counter["unmatched"] / total, 6) if total else 0.0,
        }
    return {
        "total_rows_attempted": len(rows),
        "status_counts": dict(sorted(by_status.items())),
        "overall_rates": rates(by_status),
        "per_source_join_rates": {key: rates(value) for key, value in sorted(by_source_status.items())},
        "per_session_join_rates": {key: rates(value) for key, value in sorted(by_session_status.items())},
        "evidence_path_existence": {
            "raw_evidence_paths_existing": sum(int(row.get("raw_evidence_paths_existing") or 0) for row in rows),
            "raw_evidence_paths_total": sum(int(row.get("raw_evidence_paths_total") or 0) for row in rows),
            "rows_with_observation_index": sum(int(row.get("observation_index_exists") or 0) for row in rows),
            "rows_with_observation_found": sum(int(row.get("observation_found") or 0) for row in rows),
            "rows_with_manifest": sum(int(row.get("manifest_exists") or 0) for row in rows),
            "rows_with_manifest_instance": sum(int(row.get("manifest_instance_found") or 0) for row in rows),
        },
    }


def positive_entries(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        entries = [value]
    elif isinstance(value, list):
        entries = [item for item in value if isinstance(item, dict)]
    else:
        entries = []
    return [entry for entry in entries if int(entry.get("numPixels") or 0) > 0]


def annotated_category_audit(frame_route_index: dict[str, set[tuple[str, str]]]) -> dict[str, Any]:
    if not ANNOTATED_ZIP.exists():
        return {"available": False, "path": rel(ANNOTATED_ZIP), "categories_beyond_p199": {}}
    category_frames: dict[str, set[str]] = defaultdict(set)
    category_files: Counter[str] = Counter()
    samples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with zipfile.ZipFile(ANNOTATED_ZIP) as archive:
        raw_names = sorted(name for name in archive.namelist() if name.endswith("/raw_labels_2d.json"))
        for name in raw_names:
            parts = name.split("/")
            frame_dir = parts[1] if len(parts) > 2 else ""
            frame = frame_token(frame_dir) or frame_dir
            try:
                payload = json.loads(archive.read(name))
            except Exception:
                continue
            mapping = payload.get("labelMapping") or {}
            for category, value in mapping.items():
                entries = positive_entries(value)
                if not entries:
                    continue
                category_files[category] += 1
                category_frames[category].add(frame)
                if len(samples[category]) < 5:
                    routes = sorted(frame_route_index.get(frame, set()))
                    samples[category].append(
                        {
                            "raw_label_path": name,
                            "annotated_frame_id": frame,
                            "route_frame_hit_count": len(routes),
                            "route_frame_hits_sample": [f"{date}/{route}" for date, route in routes[:8]],
                        }
                    )
    out: dict[str, Any] = {}
    for category in sorted(set(category_frames) - P199_CATEGORIES):
        ambiguous = 0
        absent = 0
        unique = 0
        for frame in category_frames[category]:
            hit_count = len(frame_route_index.get(frame, set()))
            if hit_count == 0:
                absent += 1
            elif hit_count == 1:
                unique += 1
            else:
                ambiguous += 1
        if ambiguous or absent:
            status = "unmatched"
            reason = "annotated_frame_ids_match_zero_or_multiple_torwic_routes_without_session_route_metadata"
        else:
            status = "partial"
            reason = "frame_ids_have_unique_route_hits_but_no_observation_id_tracklet_or_object_identity"
        out[category] = {
            "raw_label_files_with_positive_pixels": category_files[category],
            "unique_annotated_frame_ids": len(category_frames[category]),
            "unique_route_frame_hits": unique,
            "ambiguous_route_frame_hits": ambiguous,
            "absent_route_frame_hits": absent,
            "join_status": status,
            "unmatched_reason": reason,
            "samples": samples[category],
        }
    return {
        "available": True,
        "path": rel(ANNOTATED_ZIP),
        "categories_beyond_p199": out,
        "overall_blocker": (
            "AnnotatedSemanticSet frame directories are numeric frame ids and per-camera image_N labels. "
            "They do not encode TorWIC date/route/session or object observation identity. Some frame ids "
            "exist in many TorWIC routes, so linking them to observations would require guessing."
        ),
    }


def human_label_audit() -> dict[str, Any]:
    files = {
        "boundary_p197": (P197_BOUNDARY_CSV, "human_admit_label"),
        "pairs_p197": (P197_PAIR_CSV, "human_same_object_label"),
        "boundary_p194": (ROOT / "paper/evidence/admission_boundary_label_sheet_p194.csv", "human_admit_label"),
        "pairs_p194": (ROOT / "paper/evidence/association_pair_candidates_p194.csv", "human_same_object_label"),
    }
    out: dict[str, Any] = {}
    for key, (path, column) in files.items():
        rows = read_csv(path)
        nonblank = sum(1 for row in rows if str(row.get(column, "")).strip())
        out[key] = {"path": rel(path), "column": column, "rows": len(rows), "blank": len(rows) - nonblank, "nonblank": nonblank}
    return out


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    metrics = payload["metrics"]
    lines = [
        "# P202 Raw Segmentation Join Audit",
        "",
        f"**Status:** {payload['status']}",
        "",
        "## Boundary",
        "",
        payload["scientific_boundary"],
        "",
        "## Join Metrics",
        "",
        f"- Total rows attempted: {metrics['total_rows_attempted']}",
        f"- Exact joins: {metrics['status_counts'].get('exact', 0)}",
        f"- Partial joins: {metrics['status_counts'].get('partial', 0)}",
        f"- Unmatched: {metrics['status_counts'].get('unmatched', 0)}",
        f"- Overall rates: {metrics['overall_rates']}",
        "",
        "## Per-Source Join Rates",
        "",
    ]
    for source, item in metrics["per_source_join_rates"].items():
        lines.append(f"- {source}: {item}")
    lines.extend(["", "## Evidence Path Existence", ""])
    for key, value in metrics["evidence_path_existence"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Additional Raw Category Blockers", ""])
    blockers = payload["annotated_semantic_set"]["categories_beyond_p199"]
    for category, item in blockers.items():
        lines.append(
            f"- {category}: {item['join_status']} - {item['unmatched_reason']} "
            f"(frames={item['unique_annotated_frame_ids']}, ambiguous={item['ambiguous_route_frame_hits']}, absent={item['absent_route_frame_hits']})"
        )
    lines.extend(
        [
            "",
            "## Label Gate",
            "",
            f"- P195 status: {payload['p195_status']}",
            "- Human label columns remain blank; no human labels, admission labels, or same-object labels were created.",
            "",
            "## Outputs",
            "",
            f"- JSON: `{payload['outputs']['json']}`",
            f"- CSV: `{payload['outputs']['csv']}`",
            "",
            f"**P203 recommendation:** {payload['p203_recommendation']}",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", default="paper/evidence/raw_segmentation_join_audit_p202.json")
    parser.add_argument("--output-csv", default="paper/evidence/raw_segmentation_join_audit_p202.csv")
    parser.add_argument("--output-md", default="paper/export/raw_segmentation_join_audit_p202.md")
    args = parser.parse_args()

    zip_index = build_zip_index(DATA_ROOT)
    frame_route_index = build_frame_route_index(zip_index)
    by_session, by_observation = build_observation_indexes()
    rows = make_attempt_rows(by_session, by_observation, zip_index)
    metrics = aggregate(rows)
    label_audit = human_label_audit()
    p195_status = "BLOCKED" if all(item["nonblank"] == 0 for item in label_audit.values()) else "RECHECK_REQUIRED"
    payload = {
        "phase": "P202-raw-segmentation-to-observation-join-audit",
        "status": "JOIN_AUDIT_COMPLETE_P195_STILL_BLOCKED",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scientific_boundary": (
            "P202 audits evidence-based joins only. It does not create labels, does not use P193/P197 weak "
            "admission fields or model predictions as targets, and does not train admission-control or "
            "semantic-stability models."
        ),
        "inputs": {
            "p193_csv": rel(P193_CSV),
            "p199_csv": rel(P199_CSV),
            "p197_boundary_csv": rel(P197_BOUNDARY_CSV),
            "p197_pair_csv": rel(P197_PAIR_CSV),
            "torwic_data_root": rel(DATA_ROOT),
            "annotated_semantic_zip": rel(ANNOTATED_ZIP),
        },
        "outputs": {
            "json": args.output_json,
            "csv": args.output_csv,
            "markdown": args.output_md,
        },
        "constraints_observed": {
            "human_labels_created": False,
            "weak_admission_or_model_predictions_used_as_targets": False,
            "admission_or_semantic_stability_training_performed": False,
            "downloads_performed": False,
        },
        "metrics": metrics,
        "annotated_semantic_set": annotated_category_audit(frame_route_index),
        "human_label_audit": label_audit,
        "p195_status": p195_status,
        "p203_recommendation": (
            "Use the P202 evidence map to build a no-label raw-frame evidence join helper, but do not "
            "materialize expanded auxiliary training rows until object-level raw category masks can be "
            "linked to observation_id/tracklet/physical_key without ambiguous AnnotatedSemanticSet route guesses. "
            "P195 remains blocked until independent human admission and same-object labels exist."
        ),
        "audit_rows": rows[:20],
    }
    write_json(ROOT / args.output_json, payload)
    write_csv(ROOT / args.output_csv, rows, CSV_COLUMNS)
    write_markdown(ROOT / args.output_md, payload)
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
