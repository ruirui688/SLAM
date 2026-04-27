#!/usr/bin/env python3
"""
Run a lightweight protocol-driven execution plan for TorWIC configs.

Current scope:
- resolve session/frame inputs from a protocol config
- emit a runnable plan JSON for downstream execution
- optionally print shell commands that can be used to invoke existing pipeline entrypoints
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

REPO_ROOT = Path('/home/rui/slam')
RESOLVER = REPO_ROOT / 'tools' / 'resolve_protocol_inputs.py'
PIPELINE = REPO_ROOT / 'tools' / 'run_industrial_longterm_pipeline.sh'
DEFAULT_PROMPT = 'warehouse rack . barrier . work table . forklift .'


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', type=Path, required=True)
    p.add_argument('--limit-frames', type=int, default=0)
    p.add_argument('--prompt', type=str, default=DEFAULT_PROMPT)
    p.add_argument('--plan-json-out', type=Path)
    p.add_argument('--print-commands', action='store_true')
    return p.parse_args()


def run_resolver(config: Path, limit_frames: int) -> dict[str, Any]:
    cmd = ['python3', str(RESOLVER), '--config', str(config)]
    if limit_frames > 0:
        cmd += ['--limit-frames', str(limit_frames)]
    out = subprocess.check_output(cmd, text=True)
    return json.loads(out)


def build_plan(resolved: dict[str, Any], prompt: str) -> dict[str, Any]:
    protocol_id = resolved['protocol_id']
    items = []
    for session in resolved['sessions']:
        session_slug = f"{protocol_id}__{session['date']}__{session['sequence']}".replace(' ', '_')
        output_root = str(REPO_ROOT / 'outputs' / session_slug)
        for idx, pair in enumerate(session['frame_pairs']):
            rgb_path = pair['rgb_path']
            depth_path = pair['depth_path']
            items.append(
                {
                    'session_date': session['date'],
                    'sequence': session['sequence'],
                    'frame_index': idx,
                    'rgb_path': rgb_path,
                    'depth_path': depth_path,
                    'prompt': prompt,
                    'session_id': session_slug,
                    'output_root': output_root,
                    'command': f"{PIPELINE} '{rgb_path}' '{depth_path}' '{prompt}' '{session_slug}' '{idx}' '{output_root}'",
                }
            )
    return {
        'protocol_id': protocol_id,
        'revisit_type': resolved['revisit_type'],
        'num_sessions': resolved['num_sessions'],
        'num_items': len(items),
        'items': items,
    }


def main() -> None:
    args = parse_args()
    resolved = run_resolver(args.config, args.limit_frames)
    plan = build_plan(resolved, args.prompt)

    if args.plan_json_out:
        args.plan_json_out.parent.mkdir(parents=True, exist_ok=True)
        args.plan_json_out.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding='utf-8')

    if args.print_commands:
        for item in plan['items']:
            print(item['command'])
    else:
        print(json.dumps(plan, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
