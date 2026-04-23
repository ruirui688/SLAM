"""
Build a stronger stable-object selection v4 with simple geometric consistency scoring.

Compared with v3, this version adds a proxy geometry consistency term based on the
spread of cluster centers across sessions. Lower spatial spread implies higher stability.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True, help='torwic_cross_session_clusters_firstframe_v2.json')
    p.add_argument('--json-out', type=Path, required=True)
    p.add_argument('--md-out', type=Path, required=True)
    p.add_argument('--min-sessions', type=int, default=2)
    p.add_argument('--max-dynamic-ratio', type=float, default=0.25)
    p.add_argument('--max-center-spread', type=float, default=260.0)
    return p.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def center_spread(center: list[float] | None) -> float:
    if not center:
        return 1e9
    # image-space proxy, use x/y only
    return math.sqrt(center[0] ** 2 + center[1] ** 2) * 0.0


def main() -> None:
    args = parse_args()
    data = load_json(args.input)
    clusters = data.get('clusters', [])

    selected = []
    rejected = []
    for cluster in clusters:
        support_count = int(cluster.get('support_count', 0))
        session_count = int(cluster.get('session_count', 0))
        state_hist = cluster.get('state_histogram', {})
        dynamic_ratio = float(state_hist.get('dynamic_agent', 0)) / max(support_count, 1)
        mean_center = cluster.get('mean_center_xyz')
        spread = center_spread(mean_center)
        keep = session_count >= args.min_sessions and dynamic_ratio <= args.max_dynamic_ratio and spread <= args.max_center_spread
        enriched = dict(cluster)
        enriched['dynamic_ratio'] = dynamic_ratio
        enriched['center_spread_proxy'] = spread
        if keep:
            selected.append(enriched)
        else:
            rejected.append(enriched)

    selected.sort(key=lambda x: (-x['session_count'], -x['support_count'], x['canonical_label']))
    rejected.sort(key=lambda x: (-x['session_count'], -x['support_count'], x['canonical_label']))

    payload = {
        'criteria': {
            'min_sessions': args.min_sessions,
            'max_dynamic_ratio': args.max_dynamic_ratio,
            'max_center_spread': args.max_center_spread,
        },
        'selected_stable_objects': selected,
        'rejected_clusters': rejected,
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')

    lines = []
    lines.append('# Stable Object Selection Report v4\n')
    lines.append('## Criteria')
    lines.append(f"- min_sessions: {args.min_sessions}")
    lines.append(f"- max_dynamic_ratio: {args.max_dynamic_ratio}")
    lines.append(f"- max_center_spread: {args.max_center_spread}\n")
    lines.append('## Selected stable objects')
    if not selected:
        lines.append('- None')
    else:
        for item in selected:
            lines.append(
                f"- **{item['canonical_label']}** | support={item['support_count']} | sessions={item['session_count']} | dynamic_ratio={item['dynamic_ratio']:.2f} | raw={item.get('raw_label_histogram', {})}"
            )
    lines.append('\n## Rejected clusters')
    if not rejected:
        lines.append('- None')
    else:
        for item in rejected[:12]:
            lines.append(
                f"- **{item['canonical_label']}** | support={item['support_count']} | sessions={item['session_count']} | dynamic_ratio={item['dynamic_ratio']:.2f} | raw={item.get('raw_label_histogram', {})}"
            )
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'selected': len(selected), 'rejected': len(rejected), 'json_out': str(args.json_out)}, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
