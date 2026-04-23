"""
Select stable long-term objects from cross-session candidate summaries.

This script converts the current candidate-mining outputs into a stricter stable-object list
by combining:
- session coverage
- dynamic-agent suppression
- semantic drift penalty

It is intended as a practical bridge from exploratory candidate mining to a more directly
usable long-term object subset for later mapping and paper reporting.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True, help='torwic_candidate_tables_v2.json')
    p.add_argument('--json-out', type=Path, required=True)
    p.add_argument('--md-out', type=Path, required=True)
    p.add_argument('--min-sessions', type=int, default=2)
    p.add_argument('--max-dynamic-ratio', type=float, default=0.34)
    p.add_argument('--max-drift-variants', type=int, default=2)
    return p.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def main() -> None:
    args = parse_args()
    data = load_json(args.input)
    stable_candidates = data.get('stable_candidates', [])

    selected = []
    rejected = []
    for item in stable_candidates:
        count = int(item.get('count', 0))
        session_count = int(item.get('session_count', 0))
        state_hist = item.get('state_histogram', {})
        raw_hist = item.get('raw_label_histogram', {})
        dynamic_ratio = float(state_hist.get('dynamic_agent', 0)) / max(count, 1)
        drift_variants = len(raw_hist)

        passes = (
            session_count >= args.min_sessions
            and dynamic_ratio <= args.max_dynamic_ratio
            and drift_variants <= args.max_drift_variants
        )
        enriched = dict(item)
        enriched['dynamic_ratio'] = dynamic_ratio
        enriched['drift_variants'] = drift_variants
        if passes:
            selected.append(enriched)
        else:
            rejected.append(enriched)

    selected.sort(key=lambda x: (-x['session_count'], -x['count'], x['label']))
    rejected.sort(key=lambda x: (-x['session_count'], -x['count'], x['label']))

    payload = {
        'criteria': {
            'min_sessions': args.min_sessions,
            'max_dynamic_ratio': args.max_dynamic_ratio,
            'max_drift_variants': args.max_drift_variants,
        },
        'selected_stable_objects': selected,
        'rejected_candidates': rejected,
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')

    lines = []
    lines.append('# Stable Object Selection Report\n')
    lines.append('## Criteria')
    lines.append(f"- min_sessions: {args.min_sessions}")
    lines.append(f"- max_dynamic_ratio: {args.max_dynamic_ratio}")
    lines.append(f"- max_drift_variants: {args.max_drift_variants}\n")

    lines.append('## Selected stable objects')
    if not selected:
        lines.append('- None')
    else:
        for item in selected:
            lines.append(
                f"- **{item['label']}** | count={item['count']} | sessions={item['session_count']} | "
                f"dynamic_ratio={item['dynamic_ratio']:.2f} | raw={item['raw_label_histogram']}"
            )
    lines.append('')
    lines.append('## Rejected candidates')
    if not rejected:
        lines.append('- None')
    else:
        for item in rejected:
            lines.append(
                f"- **{item['label']}** | count={item['count']} | sessions={item['session_count']} | "
                f"dynamic_ratio={item['dynamic_ratio']:.2f} | raw={item['raw_label_histogram']}"
            )

    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({
        'json_out': str(args.json_out),
        'md_out': str(args.md_out),
        'selected': len(selected),
        'rejected': len(rejected),
    }, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
