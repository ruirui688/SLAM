"""
Build TrackletRecord files from ObjectObservation outputs.

This script groups observations within a single session into lightweight
tracklets by resolved label and 3D centroid proximity. It is intentionally
simple and explainable, matching the paper v1 design.

Inputs:
- observations_index.json from build_object_observations.py

Outputs:
- tracklets_index.json
- one JSON file per tracklet under <output-dir>/tracklets/
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observations-index", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--session-id", type=str, default=None)
    parser.add_argument("--max-centroid-distance", type=float, default=1.5, help="meters")
    parser.add_argument("--min-tracklet-confidence", type=float, default=0.0)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def centroid_of(observation: dict[str, Any]) -> list[float] | None:
    geometry = observation.get("geometry", {})
    centroid = geometry.get("centroid_xyz")
    if centroid is None:
        return None
    if not isinstance(centroid, list) or len(centroid) != 3:
        return None
    return [float(v) for v in centroid]


def euclidean(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return float(sum(values) / len(values))


def aggregate_tracklet(tracklet_id: str, session_id: str, observations: list[dict[str, Any]]) -> dict[str, Any]:
    observations = sorted(observations, key=lambda item: (item.get("frame_index", 0), item.get("observation_id", "")))
    labels: dict[str, int] = {}
    gate_scores: list[float] = []
    geometry_scores: list[float] = []
    centroids: list[list[float]] = []
    bbox_sizes: list[list[float]] = []

    for obs in observations:
        label = str(obs.get("resolved_label", "unknown"))
        labels[label] = labels.get(label, 0) + 1
        gate = obs.get("semantic_gate_score")
        if gate is not None:
            gate_scores.append(float(gate))
        quality = obs.get("quality", {})
        geo_score = quality.get("geometry_quality_score")
        if geo_score is not None:
            geometry_scores.append(float(geo_score))
        centroid = centroid_of(obs)
        if centroid is not None:
            centroids.append(centroid)
        bbox_size = obs.get("geometry", {}).get("bbox_size_xyz")
        if isinstance(bbox_size, list) and len(bbox_size) == 3:
            bbox_sizes.append([float(v) for v in bbox_size])

    canonical_label = max(labels.items(), key=lambda kv: kv[1])[0] if labels else "unknown"
    centroid_xyz = None
    if centroids:
        centroid_xyz = [sum(vals) / len(vals) for vals in zip(*centroids)]
    bbox_size_xyz = None
    if bbox_sizes:
        bbox_size_xyz = [sum(vals) / len(vals) for vals in zip(*bbox_sizes)]

    tracklet_confidence_terms = [v for v in [mean(gate_scores), mean(geometry_scores)] if v is not None]
    tracklet_confidence = mean(tracklet_confidence_terms) if tracklet_confidence_terms else 0.0

    return {
        "tracklet_id": tracklet_id,
        "session_id": session_id,
        "observation_ids": [obs["observation_id"] for obs in observations],
        "start_frame_id": observations[0].get("frame_id") if observations else None,
        "end_frame_id": observations[-1].get("frame_id") if observations else None,
        "num_observations": len(observations),
        "canonical_label": canonical_label,
        "label_distribution": labels,
        "aggregated_geometry": {
            "centroid_xyz": centroid_xyz,
            "bbox_size_xyz": bbox_size_xyz,
            "merged_pointcloud_path": None,
        },
        "temporal_stats": {
            "duration_frames": (observations[-1].get("frame_index", 0) - observations[0].get("frame_index", 0) + 1)
            if observations
            else 0,
            "missing_frames": 0,
            "label_flip_count": max(0, len(labels) - 1),
            "mean_semantic_gate_score": mean(gate_scores),
            "mean_geometry_quality_score": mean(geometry_scores),
        },
        "tracklet_confidence": tracklet_confidence,
    }


def main() -> None:
    args = parse_args()
    payload = load_json(args.observations_index)
    session_id = args.session_id or str(payload.get("session_id", "unknown_session"))
    observations = payload.get("observations", [])

    groups: list[list[dict[str, Any]]] = []
    for obs in sorted(observations, key=lambda item: (item.get("frame_index", 0), item.get("observation_id", ""))):
        label = str(obs.get("resolved_label", "unknown"))
        centroid = centroid_of(obs)
        assigned = False
        for group in groups:
            ref = group[-1]
            ref_label = str(ref.get("resolved_label", "unknown"))
            ref_centroid = centroid_of(ref)
            if label != ref_label:
                continue
            if centroid is None or ref_centroid is None:
                continue
            if euclidean(centroid, ref_centroid) <= args.max_centroid_distance:
                group.append(obs)
                assigned = True
                break
        if not assigned:
            groups.append([obs])

    tracklets_dir = args.output_dir / "tracklets"
    tracklets_dir.mkdir(parents=True, exist_ok=True)

    tracklets: list[dict[str, Any]] = []
    for idx, group in enumerate(groups, start=1):
        tracklet_id = f"trk_{session_id}_{idx:03d}"
        tracklet = aggregate_tracklet(tracklet_id, session_id, group)
        if float(tracklet["tracklet_confidence"]) < args.min_tracklet_confidence:
            continue
        path = tracklets_dir / f"{tracklet_id}.json"
        path.write_text(json.dumps(tracklet, indent=2, ensure_ascii=False), encoding="utf-8")
        tracklets.append(tracklet)

    index_payload = {
        "session_id": session_id,
        "observations_index": str(args.observations_index),
        "num_tracklets": len(tracklets),
        "tracklet_paths": [str(tracklets_dir / f"{item['tracklet_id']}.json") for item in tracklets],
        "tracklets": tracklets,
    }
    index_path = args.output_dir / "tracklets_index.json"
    index_path.write_text(json.dumps(index_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(index_payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
