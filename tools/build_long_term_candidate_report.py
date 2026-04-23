"""
Build a practical long-term candidate report from multi-session industrial runs.

This script turns the current real TorWIC outputs into a directly usable summary for
project iteration: stable-like candidates, dynamic-agent candidates, semantic-drift
candidates, and a markdown report for humans.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

LABEL_ALIASES = {
    'fork': 'forklift',
    'forklift': 'forklift',
    'table': 'work table',
    'work table': 'work table',
    'barrier': 'yellow barrier',
    'yellow barrier': 'yellow barrier',
    'rack': 'warehouse rack',
    'warehouse rack': 'warehouse rack',
}


def normalize_label(label: str) -> str:
    normalized = ' '.join(str(label).strip().lower().split())
    return LABEL_ALIASES.get(normalized, normalized)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inputs', nargs='+', type=Path, required=True, help='map_objects.json files')
    p.add_argument('--json-out', type=Path, required=True)
    p.add_argument('--md-out', type=Path, required=True)
    return p.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def main() -> None:
    args = parse_args()
    items = []
    for path in args.inputs:
        objs = load_json(path)
        source_session = path.parent.parent.name if path.parent.name == 'map_output' else path.stem
        for obj in objs:
            items.append({
                'session': source_session,
                'label': normalize_label(obj.get('canonical_label', 'unknown')),
                'raw_label': str(obj.get('canonical_label', 'unknown')),
                'state': str(obj.get('state', 'unknown')),
            })

    by_label = defaultdict(list)
    for item in items:
        by_label[item['label']].append(item)

    stable_candidates = []
    dynamic_candidates = []
    drift_candidates = []
    for label, group in sorted(by_label.items()):
        sessions = sorted(set(x['session'] for x in group))
        state_hist = Counter(x['state'] for x in group)
        raw_hist = Counter(x['raw_label'] for x in group)
        entry = {
            'label': label,
            'count': len(group),
            'session_count': len(sessions),
            'sessions': sessions,
            'state_histogram': dict(state_hist),
            'raw_label_histogram': dict(raw_hist),
        }
        if len(sessions) >= 2 and state_hist.get('dynamic_agent', 0) < len(group) / 2:
            stable_candidates.append(entry)
        if state_hist.get('dynamic_agent', 0) >= max(2, len(group) / 2):
            dynamic_candidates.append(entry)
        if len(raw_hist) >= 2:
            drift_candidates.append(entry)

    stable_candidates.sort(key=lambda x: (-x['session_count'], -x['count'], x['label']))
    dynamic_candidates.sort(key=lambda x: (-x['count'], x['label']))
    drift_candidates.sort(key=lambda x: (-x['session_count'], -x['count'], x['label']))

    payload = {
        'num_items': len(items),
        'stable_candidates': stable_candidates,
        'dynamic_candidates': dynamic_candidates,
        'semantic_drift_candidates': drift_candidates,
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')

    lines = []
    lines.append('# Long-Term Candidate Report\n')
    lines.append(f'- Total frame-level map objects: {len(items)}')
    lines.append(f'- Stable-like candidates: {len(stable_candidates)}')
    lines.append(f'- Dynamic candidates: {len(dynamic_candidates)}')
    lines.append(f'- Semantic-drift candidates: {len(drift_candidates)}\n')

    def add_section(title: str, entries: list[dict[str, Any]]) -> None:
        lines.append(f'## {title}\n')
        if not entries:
            lines.append('- None\n')
            return
        for entry in entries:
            lines.append(f"- **{entry['label']}** | count={entry['count']} | sessions={entry['session_count']} | states={entry['state_histogram']} | raw={entry['raw_label_histogram']}")
        lines.append('')

    add_section('Stable-like candidates', stable_candidates)
    add_section('Dynamic candidates', dynamic_candidates)
    add_section('Semantic-drift candidates', drift_candidates)

    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'json_out': str(args.json_out), 'md_out': str(args.md_out)}, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
