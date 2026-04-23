"""
Aggregate multiple per-frame MapObject outputs into a lightweight cross-session summary.

This script is a paper/prototyping bridge for the current stage where each frame is still
processed independently. It does not perform full lifelong fusion yet. Instead, it clusters
frame-level map objects across frames and sessions using label + image-space geometry,
producing a first cross-session summary that is useful for analysis and paper tables.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--inputs", nargs="+", type=Path, required=True, help="map_objects.json files")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--max-center-distance", type=float, default=180.0)
    p.add_argument("--max-size-ratio-diff", type=float, default=0.6)
    return p.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def center_of(obj: dict[str, Any]) -> list[float] | None:
    v = obj.get("geometry_profile", {}).get("reference_centroid_xyz")
    if isinstance(v, list) and len(v) == 3:
        return [float(x) for x in v]
    return None


def size_of(obj: dict[str, Any]) -> list[float] | None:
    v = obj.get("geometry_profile", {}).get("reference_bbox_size_xyz")
    if isinstance(v, list) and len(v) == 3:
        return [float(x) for x in v]
    return None


def euclidean(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def size_ratio_diff(a: list[float], b: list[float]) -> float:
    vals = []
    for x, y in zip(a, b):
        denom = max(abs(x), abs(y), 1e-6)
        vals.append(abs(x - y) / denom)
    return sum(vals) / len(vals)


def mergeable(a: dict[str, Any], b: dict[str, Any], max_center_distance: float, max_size_ratio_diff: float) -> bool:
    if a.get("canonical_label") != b.get("canonical_label"):
        return False
    ca, cb = center_of(a), center_of(b)
    sa, sb = size_of(a), size_of(b)
    if ca is None or cb is None:
        return False
    if euclidean(ca, cb) > max_center_distance:
        return False
    if sa is not None and sb is not None and size_ratio_diff(sa, sb) > max_size_ratio_diff:
        return False
    return True


def summarize_cluster(cluster_id: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    labels = {}
    sessions = set()
    states = {}
    centers = []
    sizes = []
    for item in items:
        label = str(item.get("canonical_label", "unknown"))
        labels[label] = labels.get(label, 0) + 1
        state = str(item.get("state", "unknown"))
        states[state] = states.get(state, 0) + 1
        src = item.get("source_session", "unknown")
        sessions.add(src)
        c = center_of(item)
        if c is not None:
            centers.append(c)
        s = size_of(item)
        if s is not None:
            sizes.append(s)
    canonical_label = max(labels.items(), key=lambda kv: kv[1])[0] if labels else "unknown"
    dominant_state = max(states.items(), key=lambda kv: kv[1])[0] if states else "unknown"
    mean_center = [sum(v) / len(v) for v in zip(*centers)] if centers else None
    mean_size = [sum(v) / len(v) for v in zip(*sizes)] if sizes else None
    return {
        "cluster_id": cluster_id,
        "canonical_label": canonical_label,
        "dominant_state": dominant_state,
        "label_histogram": labels,
        "state_histogram": states,
        "sessions": sorted(sessions),
        "session_count": len(sessions),
        "support_count": len(items),
        "mean_center_xyz": mean_center,
        "mean_size_xyz": mean_size,
    }


def main() -> None:
    args = parse_args()
    items: list[dict[str, Any]] = []
    for path in args.inputs:
        objs = load_json(path)
        source_session = path.parent.parent.name if path.parent.name == 'map_output' else path.stem
        for obj in objs:
            x = dict(obj)
            x["source_session"] = source_session
            items.append(x)

    clusters: list[list[dict[str, Any]]] = []
    for item in items:
        matched = False
        for cluster in clusters:
            if mergeable(item, cluster[0], args.max_center_distance, args.max_size_ratio_diff):
                cluster.append(item)
                matched = True
                break
        if not matched:
            clusters.append([item])

    summary = {
        "num_inputs": len(args.inputs),
        "num_frame_level_objects": len(items),
        "num_cross_session_clusters": len(clusters),
        "clusters": [summarize_cluster(f"cluster_{i+1:04d}", cluster) for i, cluster in enumerate(clusters)],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "num_frame_level_objects": len(items),
        "num_cross_session_clusters": len(clusters),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
