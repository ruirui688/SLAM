#!/usr/bin/env python3
"""
Build a protocol-driven cross-session summary with stable-selection-compatible fields.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

LABEL_ALIASES = {
    'fork': 'forklift',
    'forklift': 'forklift',
    'table': 'work table',
    'work table': 'work table',
    'barrier': 'barrier',
    'yellow barrier': 'barrier',
    'rack': 'warehouse rack',
    'warehouse rack': 'warehouse rack',
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inputs', nargs='+', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--max-center-distance', type=float, default=180.0)
    p.add_argument('--max-size-ratio-diff', type=float, default=0.6)
    return p.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def normalize_label(label: str) -> str:
    normalized = ' '.join(str(label).strip().lower().split())
    return LABEL_ALIASES.get(normalized, normalized)


def center_of(obj: dict[str, Any]) -> list[float] | None:
    v = obj.get('geometry_profile', {}).get('reference_centroid_xyz')
    if isinstance(v, list) and len(v) == 3:
        return [float(x) for x in v]
    return None


def size_of(obj: dict[str, Any]) -> list[float] | None:
    v = obj.get('geometry_profile', {}).get('reference_bbox_size_xyz')
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
    if normalize_label(a.get('canonical_label', 'unknown')) != normalize_label(b.get('canonical_label', 'unknown')):
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
    raw_labels = {}
    states = {}
    sessions = set()
    frames = set()
    centers = []
    sizes = []
    for item in items:
        normalized = normalize_label(item.get('canonical_label', 'unknown'))
        raw = str(item.get('canonical_label', 'unknown'))
        state = str(item.get('state', 'unknown'))
        labels[normalized] = labels.get(normalized, 0) + 1
        raw_labels[raw] = raw_labels.get(raw, 0) + 1
        states[state] = states.get(state, 0) + 1
        sessions.add(item.get('source_session', 'unknown'))
        frames.add(item.get('source_frame', 'unknown'))
        c = center_of(item)
        if c is not None:
            centers.append(c)
        s = size_of(item)
        if s is not None:
            sizes.append(s)
    mean_center = [sum(v) / len(v) for v in zip(*centers)] if centers else None
    mean_size = [sum(v) / len(v) for v in zip(*sizes)] if sizes else None
    canonical = max(labels.items(), key=lambda kv: kv[1])[0] if labels else 'unknown'
    dom_state = max(states.items(), key=lambda kv: kv[1])[0] if states else 'unknown'
    return {
        'cluster_id': cluster_id,
        'canonical_label': canonical,
        'dominant_state': dom_state,
        'session_count': len(sessions),
        'sessions': sorted(sessions),
        'frame_count': len(frames),
        'support_count': len(items),
        'label_histogram': labels,
        'raw_label_histogram': raw_labels,
        'state_histogram': states,
        'mean_center_xyz': mean_center,
        'mean_size_xyz': mean_size,
    }


def main() -> None:
    args = parse_args()
    items = []
    for path in args.inputs:
        objs = load_json(path)
        source_session = path.parent.parent.name if path.parent.name == 'map_output' else path.stem
        source_frame = path.parent.parent.parent.name if path.parent.name == 'map_output' else path.stem
        for obj in objs:
            x = dict(obj)
            x['source_session'] = source_session
            x['source_frame'] = source_frame
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

    payload = {
        'num_inputs': len(args.inputs),
        'num_frame_level_objects': len(items),
        'num_cross_session_clusters': len(clusters),
        'clusters': [summarize_cluster(f'cluster_{i+1:04d}', c) for i, c in enumerate(clusters)],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'output': str(args.output), 'num_frame_level_objects': len(items), 'num_cross_session_clusters': len(clusters)}, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
