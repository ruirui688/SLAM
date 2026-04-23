"""
Export a practical stable-object subset from first-8-frame cross-session stable selection.

This script turns the selected stable clusters into a small reusable artifact that can be
used as the current long-term stable-object layer of the project.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True, help='torwic_stable_object_selection_first8.json')
    p.add_argument('--json-out', type=Path, required=True)
    p.add_argument('--md-out', type=Path, required=True)
    return p.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def main() -> None:
    args = parse_args()
    data = load_json(args.input)
    selected = data.get('selected', [])

    subset = []
    for idx, item in enumerate(selected, start=1):
        subset.append(
            {
                'stable_object_id': f'stable_{idx:03d}',
                'canonical_label': item.get('canonical_label'),
                'support_count': item.get('support_count'),
                'session_count': item.get('session_count'),
                'frame_count': item.get('frame_count'),
                'sessions': item.get('sessions', []),
                'dominant_state': item.get('dominant_state'),
                'raw_label_histogram': item.get('raw_label_histogram', {}),
                'mean_center_xyz': item.get('mean_center_xyz'),
                'mean_size_xyz': item.get('mean_size_xyz'),
            }
        )

    payload = {
        'num_stable_objects': len(subset),
        'stable_objects': subset,
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')

    lines = ['# Stable Object Subset\n']
    lines.append(f'- num_stable_objects: {len(subset)}\n')
    for item in subset:
        lines.append(
            f"- **{item['stable_object_id']}** | label={item['canonical_label']} | support={item['support_count']} | sessions={item['session_count']} | frames={item['frame_count']} | raw={item['raw_label_histogram']}"
        )
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'json_out': str(args.json_out), 'md_out': str(args.md_out), 'num_stable_objects': len(subset)}, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
