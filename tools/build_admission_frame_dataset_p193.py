#!/usr/bin/env python3
"""Build P193 frame-/observation-level admission dataset from existing TorWIC outputs.

No downloads. This expands the P190 51-cluster weak-label table into
observation-level samples by joining existing observation_output indices to
selection_v5 cluster decisions. Labels remain weak labels inherited from the
cluster gate; the output records that risk explicitly.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import math
import re
from pathlib import Path
from typing import Any

SOURCE_CONFIG = {
    "same_day": {
        "selection": "outputs/torwic_same_day_aisle_bundle_selection_v5.json",
        "split": "train",
        "session_prefix": "torwic_same_day_aisle_bundle_v1__",
    },
    "cross_day": {
        "selection": "outputs/torwic_cross_day_aisle_bundle_selection_v5.json",
        "split": "train",
        "session_prefix": "torwic_cross_day_aisle_bundle_v1__",
    },
    "cross_month": {
        "selection": "outputs/torwic_cross_month_aisle_bundle_selection_v5.json",
        "split": "val",
        "session_prefix": "torwic_cross_month_aisle_bundle_v1__",
    },
    "hallway": {
        "selection": "outputs/torwic_hallway_protocol_current_selection_v5.json",
        "split": "test",
        "session_prefix": "torwic_hallway_benchmark_batch2_v1__",
    },
}

FEATURE_FIELDS = [
    "session_count",
    "frame_count",
    "support_count",
    "dynamic_ratio",
    "label_purity",
    "mean_center_x",
    "mean_center_y",
    "mean_size_x",
    "mean_size_y",
    "is_forklift_like",
    "is_infrastructure_like",
]

CSV_COLUMNS = [
    "sample_id",
    "source",
    "split",
    "cluster_id",
    "target_admit",
    "canonical_label",
    "resolved_label",
    "observation_id",
    "session_id",
    "frame_id",
    "frame_index",
    "tracklet_id",
    "physical_key",
    "join_distance",
    "dedup_status",
    "label_source",
] + FEATURE_FIELDS + [
    "cluster_session_count",
    "cluster_frame_count",
    "cluster_support_count",
    "cluster_dynamic_ratio",
    "cluster_label_purity",
    "semantic_gate_score",
    "mask_area_px",
    "bbox_width",
    "bbox_height",
    "observation_index_path",
]

INFRA_LABELS = {"barrier", "yellow barrier", "work table", "warehouse rack"}


def norm_label(value: Any) -> str:
    text = str(value or "").strip().lower().replace("_", " ").replace("-", " ")
    text = re.sub(r"\s+", " ", text)
    if text in {"fork", "fork lift", "forklift truck", "rack forklift"}:
        return "forklift"
    return text


def fnum(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def first2(values: Any) -> tuple[float, float]:
    if isinstance(values, list) and len(values) >= 2:
        return fnum(values[0]), fnum(values[1])
    return 0.0, 0.0


def load_clusters(root: Path) -> dict[str, list[dict[str, Any]]]:
    clusters_by_source: dict[str, list[dict[str, Any]]] = {}
    for source, cfg in SOURCE_CONFIG.items():
        path = root / cfg["selection"]
        data = json.loads(path.read_text())
        clusters: list[dict[str, Any]] = []
        for bucket, target in [("selected", 1), ("rejected", 0)]:
            for item in data.get(bucket, []):
                center_x, center_y = first2(item.get("mean_center_xyz"))
                size_x, size_y = first2(item.get("mean_size_xyz"))
                clusters.append({
                    "source": source,
                    "split": cfg["split"],
                    "target_admit": target,
                    "cluster_id": item.get("cluster_id", ""),
                    "canonical_label": norm_label(item.get("canonical_label")),
                    "sessions": set(item.get("sessions") or []),
                    "session_count": fnum(item.get("session_count")),
                    "frame_count": fnum(item.get("frame_count")),
                    "support_count": fnum(item.get("support_count")),
                    "dynamic_ratio": fnum(item.get("dynamic_ratio")),
                    "label_purity": fnum(item.get("label_purity")),
                    "center_x": center_x,
                    "center_y": center_y,
                    "size_x": size_x,
                    "size_y": size_y,
                    "selection_path": str(path),
                })
        clusters_by_source[source] = clusters
    return clusters_by_source


def detect_source(session_id: str) -> str | None:
    for source, cfg in SOURCE_CONFIG.items():
        if session_id.startswith(cfg["session_prefix"]):
            return source
    return None


def physical_session(session_id: str) -> str:
    parts = session_id.split("__", 1)
    return parts[1] if len(parts) == 2 else session_id


def bbox_size(obs: dict[str, Any]) -> tuple[float, float]:
    geom = obs.get("geometry") or {}
    sx, sy = first2(geom.get("bbox_size_xyz"))
    if sx and sy:
        return sx, sy
    box = obs.get("bbox_xyxy") or []
    if len(box) >= 4:
        return abs(fnum(box[2]) - fnum(box[0])), abs(fnum(box[3]) - fnum(box[1]))
    return 0.0, 0.0


def centroid(obs: dict[str, Any]) -> tuple[float, float]:
    geom = obs.get("geometry") or {}
    cx, cy = first2(geom.get("centroid_xyz"))
    if cx or cy:
        return cx, cy
    box = obs.get("bbox_xyxy") or []
    if len(box) >= 4:
        return (fnum(box[0]) + fnum(box[2])) / 2.0, (fnum(box[1]) + fnum(box[3])) / 2.0
    return 0.0, 0.0


def join_distance(cluster: dict[str, Any], obs: dict[str, Any]) -> float:
    cx, cy = centroid(obs)
    sx, sy = bbox_size(obs)
    center_dist = math.hypot(cx - cluster["center_x"], cy - cluster["center_y"]) / 320.0
    size_dist = math.hypot(sx - cluster["size_x"], sy - cluster["size_y"]) / 240.0
    return center_dist + 0.5 * size_dist


def best_cluster(source: str, obs: dict[str, Any], clusters_by_source: dict[str, list[dict[str, Any]]]) -> tuple[dict[str, Any] | None, float]:
    label = norm_label(obs.get("resolved_label") or obs.get("grounding_label") or obs.get("object_name"))
    session_id = str(obs.get("session_id", ""))
    candidates = [
        c for c in clusters_by_source.get(source, [])
        if c["canonical_label"] == label and session_id in c["sessions"]
    ]
    # Some historic outputs call rack+forklift ambiguous objects forklift-like.
    if not candidates and "fork" in label:
        candidates = [
            c for c in clusters_by_source.get(source, [])
            if c["canonical_label"] == "forklift" and session_id in c["sessions"]
        ]
    if not candidates:
        return None, float("inf")
    best = min(candidates, key=lambda c: join_distance(c, obs))
    return best, join_distance(best, obs)


def make_sample(source: str, cluster: dict[str, Any], obs: dict[str, Any], distance: float, index_path: str) -> dict[str, Any]:
    label = norm_label(obs.get("resolved_label") or obs.get("grounding_label") or obs.get("object_name"))
    cx, cy = centroid(obs)
    sx, sy = bbox_size(obs)
    mask_area = fnum(obs.get("mask_area_px") or ((obs.get("geometry") or {}).get("num_points")))
    semantic = fnum(obs.get("semantic_gate_score") or obs.get("clip_similarity") or obs.get("grounding_score"))
    session_id = str(obs.get("session_id", ""))
    frame_index = int(fnum(obs.get("frame_index"), -1))
    object_name = str(obs.get("object_name") or obs.get("observation_id") or "")
    physical_key = f"{physical_session(session_id)}::{frame_index:06d}::{object_name}"
    is_forklift = 1 if ("fork" in label or "lift" in label) else 0
    is_infra = 1 if label in INFRA_LABELS else 0
    return {
        "sample_id": f"{source}:{obs.get('observation_id')}",
        "source": source,
        "split": cluster["split"],
        "cluster_id": cluster["cluster_id"],
        "target_admit": int(cluster["target_admit"]),
        "canonical_label": cluster["canonical_label"],
        "resolved_label": label,
        "observation_id": obs.get("observation_id", ""),
        "session_id": session_id,
        "frame_id": obs.get("frame_id", ""),
        "frame_index": frame_index,
        "tracklet_id": obs.get("tracklet_id", ""),
        "physical_key": physical_key,
        "join_distance": round(distance, 6),
        "dedup_status": "raw",
        "label_source": "weak_cluster_selection_v5_nearest_label_geometry_join",
        # Frame-/observation-level features for the trainer's existing schema.
        "session_count": 1.0,
        "frame_count": 1.0,
        "support_count": mask_area,
        "dynamic_ratio": float(is_forklift),
        "label_purity": semantic,
        "mean_center_x": cx,
        "mean_center_y": cy,
        "mean_size_x": sx,
        "mean_size_y": sy,
        "is_forklift_like": is_forklift,
        "is_infrastructure_like": is_infra,
        # Provenance / leakage audit columns.
        "cluster_session_count": cluster["session_count"],
        "cluster_frame_count": cluster["frame_count"],
        "cluster_support_count": cluster["support_count"],
        "cluster_dynamic_ratio": cluster["dynamic_ratio"],
        "cluster_label_purity": cluster["label_purity"],
        "semantic_gate_score": semantic,
        "mask_area_px": mask_area,
        "bbox_width": sx,
        "bbox_height": sy,
        "observation_index_path": index_path,
    }


def deduplicate(samples: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    # Avoid same physical observation appearing in both train and validation via
    # same_day/cross_day/cross_month protocol overlaps. Prefer train samples for
    # duplicated Aisle observations so the model has enough training support;
    # Hallway is a distinct test branch and normally does not collide.
    source_priority = {"hallway": 0, "cross_day": 1, "same_day": 2, "cross_month": 3}
    sorted_samples = sorted(samples, key=lambda s: (source_priority.get(str(s["source"]), 99), float(s["join_distance"])))
    kept_by_key: dict[str, dict[str, Any]] = {}
    duplicate_count = 0
    for sample in sorted_samples:
        key = str(sample["physical_key"])
        if key not in kept_by_key:
            kept_by_key[key] = sample
        else:
            duplicate_count += 1
    kept = []
    for sample in kept_by_key.values():
        sample = dict(sample)
        sample["dedup_status"] = "kept_split_exclusive_physical_key"
        kept.append(sample)
    split_sets: dict[str, set[str]] = {}
    for sample in kept:
        split_sets.setdefault(str(sample["split"]), set()).add(str(sample["physical_key"]))
    cross_split_overlap = sorted(set.intersection(*split_sets.values())) if len(split_sets) == 3 else []
    return kept, {
        "raw_samples": len(samples),
        "deduplicated_samples": len(kept),
        "removed_duplicate_physical_keys": duplicate_count,
        "dedup_key": "physical_session(session_id)::frame_index::object_name",
        "cross_split_overlap_after_dedup": len(cross_split_overlap),
        "source_priority": source_priority,
    }


def counts(samples: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {"total": len(samples), "by_split": {}, "by_source": {}, "by_label": {}}
    for sample in samples:
        split = str(sample["split"])
        source = str(sample["source"])
        label = "admit" if int(sample["target_admit"]) == 1 else "reject"
        out["by_split"].setdefault(split, {"n": 0, "admit": 0, "reject": 0})
        out["by_split"][split]["n"] += 1
        out["by_split"][split][label] += 1
        out["by_source"].setdefault(source, {"n": 0, "admit": 0, "reject": 0})
        out["by_source"][source]["n"] += 1
        out["by_source"][source][label] += 1
        out["by_label"].setdefault(str(sample["canonical_label"]), {"n": 0, "admit": 0, "reject": 0})
        out["by_label"][str(sample["canonical_label"])]["n"] += 1
        out["by_label"][str(sample["canonical_label"])][label] += 1
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outputs-root", default="outputs")
    parser.add_argument("--cluster-labels", default="paper/evidence/admission_scorer_dataset_p190.csv")
    parser.add_argument("--output-json", default="paper/evidence/admission_frame_dataset_p193.json")
    parser.add_argument("--output-csv", default="paper/evidence/admission_frame_dataset_p193.csv")
    parser.add_argument("--raw-output-csv", default="paper/evidence/admission_frame_dataset_p193_raw.csv")
    args = parser.parse_args()

    root = Path(".").resolve()
    outputs_root = root / args.outputs_root
    clusters_by_source = load_clusters(root)
    index_paths = sorted(glob.glob(str(outputs_root / "torwic_*" / "observation_output" / "observations_index.json")))
    backend_manifests = sorted(glob.glob(str(outputs_root / "dynamic_slam_backend*" / "backend_input_manifest.json")))

    raw_samples: list[dict[str, Any]] = []
    join_stats = {
        "observation_index_files_scanned": 0,
        "observations_seen": 0,
        "observations_joined": 0,
        "skipped_non_protocol_source": 0,
        "skipped_no_cluster_match": 0,
    }
    source_files: set[str] = set()
    for index_path in index_paths:
        data = json.loads(Path(index_path).read_text())
        session_id = str(data.get("session_id", ""))
        source = detect_source(session_id)
        join_stats["observation_index_files_scanned"] += 1
        if source is None:
            join_stats["skipped_non_protocol_source"] += len(data.get("observations") or [])
            continue
        source_files.add(str(Path(index_path).relative_to(root)))
        for obs in data.get("observations") or []:
            join_stats["observations_seen"] += 1
            cluster, distance = best_cluster(source, obs, clusters_by_source)
            if cluster is None:
                join_stats["skipped_no_cluster_match"] += 1
                continue
            raw_samples.append(make_sample(source, cluster, obs, distance, str(Path(index_path).relative_to(root))))
            join_stats["observations_joined"] += 1

    deduped, dedup_info = deduplicate(raw_samples)
    out_json = root / args.output_json
    out_csv = root / args.output_csv
    raw_csv = root / args.raw_output_csv
    out_json.parent.mkdir(parents=True, exist_ok=True)

    for path, rows in [(out_csv, deduped), (raw_csv, raw_samples)]:
        with path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, lineterminator="\n")
            writer.writeheader()
            for row in rows:
                writer.writerow({col: row.get(col, "") for col in CSV_COLUMNS})

    payload = {
        "phase": "P193-frame-level-admission-dataset-expansion",
        "environment_basis": "README.md §0.3 tram environment; no downloads; existing TorWIC outputs only",
        "cluster_label_source": args.cluster_labels,
        "selection_sources": {source: cfg["selection"] for source, cfg in SOURCE_CONFIG.items()},
        "source_files": sorted(source_files),
        "backend_input_manifests_scanned_for_inventory": [str(Path(p).relative_to(root)) for p in backend_manifests],
        "features": FEATURE_FIELDS,
        "target": "target_admit inherited as weak label from nearest same-label selection_v5 cluster",
        "join_strategy": "For each observation, choose same-protocol/same-session/same-label cluster with nearest image-plane centroid/size to the observation geometry.",
        "dedup_strategy": dedup_info,
        "join_stats": join_stats,
        "counts": counts(deduped),
        "raw_counts": counts(raw_samples),
        "outputs": {
            "deduplicated_csv": str(out_csv.relative_to(root)),
            "raw_csv": str(raw_csv.relative_to(root)),
            "json": str(out_json.relative_to(root)),
        },
        "weak_label_leakage_risks": [
            "Labels are inherited from selection_v5 cluster decisions, not independent human frame labels.",
            "dynamic_ratio is represented by forklift-like label at observation level, so it can proxy the reject rule.",
            "Same physical observations appear in same_day/cross_day/cross_month protocol outputs; split-exclusive physical-key dedup removes direct duplicates but cannot remove all scene-level correlation.",
            "Cluster assignment is nearest same-label geometry, so ambiguous repeated racks/barriers can still receive noisy labels.",
        ],
        "p194_recommendation": "Create independent boundary-label sheet and/or pairwise cross-session association labels from retained false positives/false negatives before claiming model improvement over rule gate.",
        "samples_preview": deduped[:10],
    }
    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({
        "output_json": str(out_json.relative_to(root)),
        "output_csv": str(out_csv.relative_to(root)),
        "raw_output_csv": str(raw_csv.relative_to(root)),
        "counts": payload["counts"],
        "raw_counts": payload["raw_counts"],
        "join_stats": join_stats,
        "dedup_strategy": dedup_info,
        "source_file_count": len(source_files),
        "backend_manifest_count": len(backend_manifests),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
