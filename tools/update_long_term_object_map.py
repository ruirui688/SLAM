"""
Build and update long-term MapObject records from session-level TrackletRecord files.

This is the third runnable bridge in the paper-v1 pipeline:
ObjectObservation -> TrackletRecord -> MapObject -> MapRevision

The initial implementation is intentionally simple and interpretable.
It matches tracklets to existing map objects using:
- canonical label equality
- 3D centroid proximity
- 3D size similarity

Outputs:
- map_objects.json
- map_revisions.json
- one JSON file per map object under <output-dir>/map_objects/
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


DEFAULT_STATE = "candidate"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tracklets-index", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--session-id", type=str, default=None)
    parser.add_argument("--map-objects", type=Path, default=None, help="Existing map_objects.json")
    parser.add_argument("--map-revisions", type=Path, default=None, help="Existing map_revisions.json")
    parser.add_argument("--max-centroid-distance", type=float, default=2.0, help="meters")
    parser.add_argument("--max-size-ratio-diff", type=float, default=0.75)
    parser.add_argument("--stable-min-sessions", type=int, default=2)
    parser.add_argument("--dynamic-threshold", type=float, default=0.6)
    return parser.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def centroid_of_tracklet(tracklet: dict[str, Any]) -> list[float] | None:
    centroid = tracklet.get("aggregated_geometry", {}).get("centroid_xyz")
    if isinstance(centroid, list) and len(centroid) == 3:
        return [float(v) for v in centroid]
    return None


def size_of_tracklet(tracklet: dict[str, Any]) -> list[float] | None:
    size = tracklet.get("aggregated_geometry", {}).get("bbox_size_xyz")
    if isinstance(size, list) and len(size) == 3:
        return [float(v) for v in size]
    return None


def centroid_of_object(obj: dict[str, Any]) -> list[float] | None:
    centroid = obj.get("geometry_profile", {}).get("reference_centroid_xyz")
    if isinstance(centroid, list) and len(centroid) == 3:
        return [float(v) for v in centroid]
    return None


def size_of_object(obj: dict[str, Any]) -> list[float] | None:
    size = obj.get("geometry_profile", {}).get("reference_bbox_size_xyz")
    if isinstance(size, list) and len(size) == 3:
        return [float(v) for v in size]
    return None


def euclidean(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return float(sum(values) / len(values))


def average_vec(vectors: list[list[float]]) -> list[float] | None:
    if not vectors:
        return None
    return [sum(vals) / len(vals) for vals in zip(*vectors)]


def size_ratio_diff(a: list[float], b: list[float]) -> float:
    diffs = []
    for x, y in zip(a, b):
        denom = max(abs(x), abs(y), 1e-6)
        diffs.append(abs(x - y) / denom)
    return float(sum(diffs) / len(diffs))


def compute_scores(obj: dict[str, Any]) -> dict[str, float]:
    lifecycle = obj.get("lifecycle", {})
    semantic = obj.get("semantic_profile", {})
    sessions = lifecycle.get("observed_sessions", []) or []
    num_sessions = len(set(sessions))
    time_span_days = float(lifecycle.get("time_span_days", 0) or 0)
    num_tracklets = float(lifecycle.get("num_tracklets", 0) or 0)
    mean_gate = float(semantic.get("mean_semantic_gate_score", 0.0) or 0.0)
    unknown_ratio = float(semantic.get("unknown_ratio", 0.0) or 0.0)

    persistence = min(1.0, 0.35 * num_sessions + 0.15 * min(time_span_days / 30.0, 1.0) + 0.1 * min(num_tracklets / 3.0, 1.0))
    stability = max(0.0, min(1.0, 0.75 * mean_gate + 0.25 * (1.0 - unknown_ratio)))
    dynamic = max(0.0, min(1.0, 0.5 * unknown_ratio + 0.1 * max(0.0, 1.0 - min(num_sessions / 2.0, 1.0))))
    trust = max(0.0, min(1.0, persistence * stability * (1.0 - dynamic)))

    return {
        "persistence_score": persistence,
        "stability_score": stability,
        "dynamic_score": dynamic,
        "association_confidence": float(obj.get("scores", {}).get("association_confidence", 0.0) or 0.0),
        "map_trust_score": trust,
    }


def update_state(obj: dict[str, Any], stable_min_sessions: int, dynamic_threshold: float) -> str:
    lifecycle = obj.get("lifecycle", {})
    scores = obj.get("scores", {})
    num_sessions = len(set(lifecycle.get("observed_sessions", []) or []))
    dynamic_score = float(scores.get("dynamic_score", 0.0) or 0.0)
    canonical_label = str(obj.get("canonical_label", "unknown")).lower()

    if canonical_label in {"person", "forklift", "agv"}:
        return "dynamic_agent"
    if dynamic_score >= dynamic_threshold:
        return "dynamic_agent"
    if num_sessions >= stable_min_sessions and float(scores.get("stability_score", 0.0) or 0.0) >= 0.5:
        return "stable"
    if num_sessions <= 1:
        return "candidate"
    return "transient"


def match_tracklet_to_object(
    tracklet: dict[str, Any],
    objects: list[dict[str, Any]],
    session_id: str,
    max_centroid_distance: float,
    max_size_ratio_diff: float,
) -> tuple[int | None, float | None]:
    label = str(tracklet.get("canonical_label", "unknown"))
    centroid = centroid_of_tracklet(tracklet)
    size = size_of_tracklet(tracklet)

    best_idx = None
    best_score = None
    for idx, obj in enumerate(objects):
        if str(obj.get("canonical_label", "unknown")) != label:
            continue

        observed_sessions = set(obj.get("lifecycle", {}).get("observed_sessions", []) or [])
        # Do not merge multiple same-session tracklets into one long-term object in v1.
        # This preserves intra-session same-class instances and postpones stronger fusion
        # decisions to the cross-session stage.
        if session_id in observed_sessions:
            continue

        obj_centroid = centroid_of_object(obj)
        obj_size = size_of_object(obj)
        if centroid is None or obj_centroid is None:
            continue
        distance = euclidean(centroid, obj_centroid)
        if distance > max_centroid_distance:
            continue
        ratio_diff = 0.0
        if size is not None and obj_size is not None:
            ratio_diff = size_ratio_diff(size, obj_size)
            if ratio_diff > max_size_ratio_diff:
                continue
        score = max(0.0, 1.0 - distance / max_centroid_distance) * 0.7 + max(0.0, 1.0 - ratio_diff / max(max_size_ratio_diff, 1e-6)) * 0.3
        if best_score is None or score > best_score:
            best_idx = idx
            best_score = float(score)
    return best_idx, best_score


def make_new_object(tracklet: dict[str, Any], session_id: str, object_id: str, revision_id: str) -> dict[str, Any]:
    label_distribution = dict(tracklet.get("label_distribution", {}))
    canonical_label = str(tracklet.get("canonical_label", "unknown"))
    mean_gate = float(tracklet.get("temporal_stats", {}).get("mean_semantic_gate_score", 0.0) or 0.0)
    geometry = tracklet.get("aggregated_geometry", {})
    obj = {
        "map_object_id": object_id,
        "object_type": "object",
        "state": DEFAULT_STATE,
        "canonical_label": canonical_label,
        "label_distribution": label_distribution,
        "semantic_profile": {
            "clip_label_histogram": label_distribution,
            "mean_semantic_gate_score": mean_gate,
            "mean_entropy": None,
            "unknown_ratio": float(label_distribution.get("unknown", 0)) / max(sum(label_distribution.values()), 1),
        },
        "geometry_profile": {
            "reference_centroid_xyz": geometry.get("centroid_xyz"),
            "reference_bbox_size_xyz": geometry.get("bbox_size_xyz"),
            "geometry_model_type": "tracklet_aggregate",
            "geometry_model_path": geometry.get("merged_pointcloud_path"),
            "occupancy_region": None,
        },
        "lifecycle": {
            "first_seen_session": session_id,
            "last_seen_session": session_id,
            "observed_sessions": [session_id],
            "num_observations": int(tracklet.get("num_observations", 0) or 0),
            "num_tracklets": 1,
            "time_span_days": 0,
        },
        "scores": {
            "persistence_score": 0.0,
            "stability_score": 0.0,
            "dynamic_score": 0.0,
            "association_confidence": 1.0,
            "map_trust_score": 0.0,
        },
        "status_flags": {
            "is_structural": False,
            "is_movable": False,
            "is_transient": False,
            "is_dynamic_agent": False,
            "needs_review": False,
        },
        "support": {
            "support_observation_ids": [],
            "support_tracklet_ids": [tracklet["tracklet_id"]],
            "evidence_count": int(tracklet.get("num_observations", 0) or 0),
        },
        "update_info": {
            "created_revision": revision_id,
            "last_updated_revision": revision_id,
            "last_update_reason": "new_tracklet",
        },
    }
    obj["scores"] = compute_scores(obj)
    obj["state"] = update_state(obj, stable_min_sessions=2, dynamic_threshold=0.6)
    return obj


def merge_tracklet_into_object(
    obj: dict[str, Any],
    tracklet: dict[str, Any],
    session_id: str,
    revision_id: str,
    association_confidence: float,
    stable_min_sessions: int,
    dynamic_threshold: float,
) -> tuple[str, str]:
    before_state = str(obj.get("state", DEFAULT_STATE))

    label_distribution = obj.setdefault("label_distribution", {})
    for label, count in tracklet.get("label_distribution", {}).items():
        label_distribution[label] = int(label_distribution.get(label, 0)) + int(count)
    obj["canonical_label"] = max(label_distribution.items(), key=lambda kv: kv[1])[0]

    semantic = obj.setdefault("semantic_profile", {})
    semantic["clip_label_histogram"] = dict(label_distribution)
    old_gate = semantic.get("mean_semantic_gate_score")
    new_gate = tracklet.get("temporal_stats", {}).get("mean_semantic_gate_score")
    semantic["mean_semantic_gate_score"] = mean([v for v in [old_gate, new_gate] if v is not None])
    semantic["unknown_ratio"] = float(label_distribution.get("unknown", 0)) / max(sum(label_distribution.values()), 1)

    geometry = obj.setdefault("geometry_profile", {})
    old_centroid = geometry.get("reference_centroid_xyz")
    new_centroid = tracklet.get("aggregated_geometry", {}).get("centroid_xyz")
    geometry["reference_centroid_xyz"] = average_vec([v for v in [old_centroid, new_centroid] if isinstance(v, list) and len(v) == 3])
    old_size = geometry.get("reference_bbox_size_xyz")
    new_size = tracklet.get("aggregated_geometry", {}).get("bbox_size_xyz")
    geometry["reference_bbox_size_xyz"] = average_vec([v for v in [old_size, new_size] if isinstance(v, list) and len(v) == 3])

    lifecycle = obj.setdefault("lifecycle", {})
    sessions = lifecycle.setdefault("observed_sessions", [])
    if session_id not in sessions:
        sessions.append(session_id)
    lifecycle["last_seen_session"] = session_id
    lifecycle["num_observations"] = int(lifecycle.get("num_observations", 0)) + int(tracklet.get("num_observations", 0) or 0)
    lifecycle["num_tracklets"] = int(lifecycle.get("num_tracklets", 0)) + 1
    lifecycle["time_span_days"] = max(float(lifecycle.get("time_span_days", 0) or 0), float(len(set(sessions)) - 1) * 7.0)

    support = obj.setdefault("support", {})
    support.setdefault("support_tracklet_ids", []).append(tracklet["tracklet_id"])
    support["evidence_count"] = int(lifecycle.get("num_observations", 0))

    update_info = obj.setdefault("update_info", {})
    update_info["last_updated_revision"] = revision_id
    update_info["last_update_reason"] = "matched_new_tracklet"

    scores = compute_scores(obj)
    scores["association_confidence"] = float(association_confidence)
    obj["scores"] = scores
    obj["state"] = update_state(obj, stable_min_sessions=stable_min_sessions, dynamic_threshold=dynamic_threshold)
    after_state = str(obj["state"])
    return before_state, after_state


def main() -> None:
    args = parse_args()
    payload = load_json(args.tracklets_index)
    session_id = args.session_id or str(payload.get("session_id", "unknown_session"))
    tracklets = payload.get("tracklets", [])

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    objects_dir = output_dir / "map_objects"
    objects_dir.mkdir(parents=True, exist_ok=True)

    map_objects_path = args.map_objects or (output_dir / "map_objects.json")
    map_revisions_path = args.map_revisions or (output_dir / "map_revisions.json")

    map_objects: list[dict[str, Any]] = load_json(map_objects_path) if map_objects_path.is_file() else []
    map_revisions: list[dict[str, Any]] = load_json(map_revisions_path) if map_revisions_path.is_file() else []

    revision_id = f"rev_{len(map_revisions) + 1:05d}"
    created_object_ids: list[str] = []
    updated_object_ids: list[str] = []
    state_transitions: list[dict[str, str]] = []

    for tracklet in tracklets:
        match_idx, match_score = match_tracklet_to_object(
            tracklet,
            map_objects,
            session_id=session_id,
            max_centroid_distance=args.max_centroid_distance,
            max_size_ratio_diff=args.max_size_ratio_diff,
        )
        if match_idx is None:
            object_id = f"obj_{len(map_objects) + 1:06d}"
            obj = make_new_object(tracklet, session_id, object_id, revision_id)
            map_objects.append(obj)
            created_object_ids.append(object_id)
            if obj["state"] != DEFAULT_STATE:
                state_transitions.append(
                    {
                        "map_object_id": object_id,
                        "from": DEFAULT_STATE,
                        "to": str(obj["state"]),
                        "reason": "new_object_initial_scoring",
                    }
                )
        else:
            obj = map_objects[match_idx]
            before_state, after_state = merge_tracklet_into_object(
                obj,
                tracklet,
                session_id,
                revision_id,
                association_confidence=float(match_score or 0.0),
                stable_min_sessions=args.stable_min_sessions,
                dynamic_threshold=args.dynamic_threshold,
            )
            updated_object_ids.append(str(obj["map_object_id"]))
            if before_state != after_state:
                state_transitions.append(
                    {
                        "map_object_id": str(obj["map_object_id"]),
                        "from": before_state,
                        "to": after_state,
                        "reason": "cross_session_support",
                    }
                )

    for obj in map_objects:
        save_json(objects_dir / f"{obj['map_object_id']}.json", obj)
    save_json(map_objects_path, map_objects)

    revision = {
        "revision_id": revision_id,
        "session_id": session_id,
        "trigger_type": "session_ingest",
        "new_tracklet_count": len(tracklets),
        "updated_object_ids": updated_object_ids,
        "created_object_ids": created_object_ids,
        "state_transitions": state_transitions,
        "notes": f"ingest {session_id}",
    }
    map_revisions.append(revision)
    save_json(map_revisions_path, map_revisions)

    print(
        json.dumps(
            {
                "revision": revision,
                "num_map_objects": len(map_objects),
                "map_objects_path": str(map_objects_path),
                "map_revisions_path": str(map_revisions_path),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
