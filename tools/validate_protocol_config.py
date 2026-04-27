#!/usr/bin/env python3
"""
Validate a TorWIC protocol config and summarize its runnable scope.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_TOP_LEVEL = [
    "protocol_id",
    "dataset",
    "description",
    "goal",
    "revisit_type",
    "sessions",
    "frame_window",
    "pipeline_outputs",
    "metrics",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--json", action="store_true", help="emit JSON summary")
    return p.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    args = parse_args()
    config = load_json(args.config)

    missing = [k for k in REQUIRED_TOP_LEVEL if k not in config]
    sessions = config.get("sessions", [])
    frame_window = config.get("frame_window", {})

    session_summaries = []
    missing_paths = []
    for session in sessions:
        path = Path(session["path"])
        exists = path.exists()
        if not exists:
            missing_paths.append(str(path))
        session_summaries.append(
            {
                "date": session.get("date"),
                "sequence": session.get("sequence"),
                "path": str(path),
                "exists": exists,
            }
        )

    summary = {
        "config": str(args.config),
        "protocol_id": config.get("protocol_id"),
        "revisit_type": config.get("revisit_type"),
        "num_sessions": len(sessions),
        "frame_window": frame_window,
        "pipeline_outputs": config.get("pipeline_outputs", []),
        "metrics": config.get("metrics", []),
        "missing_top_level": missing,
        "missing_paths": missing_paths,
        "sessions": session_summaries,
        "valid": not missing and not missing_paths,
    }

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return

    print(f"protocol_id: {summary['protocol_id']}")
    print(f"revisit_type: {summary['revisit_type']}")
    print(f"num_sessions: {summary['num_sessions']}")
    print(f"frame_window: {summary['frame_window']}")
    print(f"pipeline_outputs: {', '.join(summary['pipeline_outputs'])}")
    print(f"metrics: {', '.join(summary['metrics'])}")
    if missing:
        print(f"missing_top_level: {missing}")
    for item in session_summaries:
        status = "OK" if item['exists'] else "MISSING"
        print(f"- [{status}] {item['date']} {item['sequence']} -> {item['path']}")
    print(f"valid: {summary['valid']}")


if __name__ == "__main__":
    main()
