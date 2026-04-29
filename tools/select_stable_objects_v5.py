"""
Select stable objects from first-8-frame cross-session clusters with a stronger v5 rule.

This version adds a simple label-purity term using raw label histograms so that clusters with
excessive alias fragmentation are penalized even if they span multiple sessions.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True, help='torwic_cross_session_first8_clusters.json')
    p.add_argument('--json-out', type=Path, required=True)
    p.add_argument('--md-out', type=Path, required=True)
    p.add_argument('--min-sessions', type=int, default=2)
    p.add_argument('--min-frames', type=int, default=4)
    p.add_argument('--min-support', type=int, default=6)
    p.add_argument('--max-dynamic-ratio', type=float, default=0.20)
    p.add_argument('--min-label-purity', type=float, default=0.70)
    return p.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def main() -> None:
    args = parse_args()
    data = load_json(args.input)
    clusters = data.get('clusters', [])

    selected = []
    rejected = []
    for cluster in clusters:
        support = int(cluster.get('support_count', 0))
        sessions = int(cluster.get('session_count', 0))
        frames = int(cluster.get('frame_count', support))
        state_hist = cluster.get('state_histogram', {})
        raw_hist = cluster.get('raw_label_histogram', {})
        dynamic_ratio = float(state_hist.get('dynamic_agent', 0)) / max(support, 1)
        label_purity = max(raw_hist.values()) / max(sum(raw_hist.values()), 1) if raw_hist else 0.0
        keep = (
            sessions >= args.min_sessions
            and frames >= args.min_frames
            and support >= args.min_support
            and dynamic_ratio <= args.max_dynamic_ratio
            and label_purity >= args.min_label_purity
        )
        reject_reasons = []
        if sessions < args.min_sessions:
            reject_reasons.append('single_session_or_low_session_support')
        if frames < args.min_frames:
            reject_reasons.append('insufficient_frame_support')
        if support < args.min_support:
            reject_reasons.append('low_support')
        if dynamic_ratio > args.max_dynamic_ratio:
            reject_reasons.append('dynamic_contamination')
        if label_purity < args.min_label_purity:
            reject_reasons.append('label_fragmentation')
        if not reject_reasons and not keep:
            reject_reasons.append('other_threshold_gap')

        item = dict(cluster)
        item['frame_count'] = frames
        item['dynamic_ratio'] = dynamic_ratio
        item['label_purity'] = label_purity
        item['reject_reasons'] = reject_reasons
        if keep:
            selected.append(item)
        else:
            rejected.append(item)

    selected.sort(key=lambda x: (-x['session_count'], -x['support_count'], x['canonical_label']))
    rejected.sort(key=lambda x: (-x['session_count'], -x['support_count'], x['canonical_label']))

    payload = {
        'criteria': {
            'min_sessions': args.min_sessions,
            'min_frames': args.min_frames,
            'min_support': args.min_support,
            'max_dynamic_ratio': args.max_dynamic_ratio,
            'min_label_purity': args.min_label_purity,
        },
        'selected': selected,
        'rejected': rejected,
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')

    lines = ['# Stable Object Selection Report v5\n']
    lines.append('## Criteria')
    for k, v in payload['criteria'].items():
        lines.append(f'- {k}: {v}')
    lines.append('')
    lines.append('## Selected stable objects')
    if not selected:
        lines.append('- None')
    else:
        for item in selected:
            lines.append(
                f"- **{item['canonical_label']}** | support={item['support_count']} | sessions={item['session_count']} | frames={item['frame_count']} | dynamic_ratio={item['dynamic_ratio']:.2f} | label_purity={item['label_purity']:.2f} | raw={item.get('raw_label_histogram', {})}"
            )
    lines.append('')
    lines.append('## Rejected clusters')
    if not rejected:
        lines.append('- None')
    else:
        for item in rejected[:12]:
            lines.append(
                f"- **{item['canonical_label']}** | support={item['support_count']} | sessions={item['session_count']} | frames={item['frame_count']} | dynamic_ratio={item['dynamic_ratio']:.2f} | label_purity={item['label_purity']:.2f} | raw={item.get('raw_label_histogram', {})}"
            )

    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'selected': len(selected), 'rejected': len(rejected), 'json_out': str(args.json_out)}, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
