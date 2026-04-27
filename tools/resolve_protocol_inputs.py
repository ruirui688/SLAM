#!/usr/bin/env python3
"""
Resolve a TorWIC protocol config into concrete session/frame execution items.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
RGB_DIR_HINTS = ("rgb", "image", "images", "left")
DEPTH_DIR_HINTS = ("depth",)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--json-out", type=Path)
    p.add_argument("--limit-frames", type=int, default=0, help="override frame count if > 0")
    return p.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _score_path(path: Path) -> tuple[int, int, str]:
    lowered_parts = [part.lower() for part in path.parts]
    has_depth = any(hint in part for hint in DEPTH_DIR_HINTS for part in lowered_parts)
    has_rgb_hint = any(hint in part for hint in RGB_DIR_HINTS for part in lowered_parts)
    depth_penalty = 1 if has_depth else 0
    rgb_bonus = 0 if has_rgb_hint else 1
    return (depth_penalty, rgb_bonus, str(path))


def find_rgb_frames(session_path: Path) -> list[Path]:
    search_roots = [session_path / "rgb", session_path / "RGB", session_path]
    for sub in search_roots:
        if not sub.exists() or not sub.is_dir():
            continue

        direct_files = sorted(
            (p for p in sub.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS),
            key=_score_path,
        )
        direct_files = [p for p in direct_files if "depth" not in str(p).lower()]
        if direct_files:
            return direct_files

        recursive_files = sorted(
            (p for p in sub.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS),
            key=_score_path,
        )
        recursive_files = [p for p in recursive_files if "depth" not in str(p).lower()]
        if recursive_files:
            return recursive_files

    return []


def main() -> None:
    args = parse_args()
    config = load_json(args.config)
    frame_window = config.get("frame_window", {})
    mode = frame_window.get("mode", "first_n")
    count = int(frame_window.get("count", 0))
    if args.limit_frames > 0:
        count = args.limit_frames

    plan_items = []
    for session in config.get("sessions", []):
        session_path = Path(session["path"])
        rgb_frames = find_rgb_frames(session_path)
        if mode == "first_n" and count > 0:
            rgb_frames = rgb_frames[:count]

        item = {
            "date": session.get("date"),
            "sequence": session.get("sequence"),
            "session_path": str(session_path),
            "num_rgb_frames": len(rgb_frames),
            "rgb_frames": [str(p) for p in rgb_frames],
        }
        plan_items.append(item)

    payload = {
        "protocol_id": config.get("protocol_id"),
        "revisit_type": config.get("revisit_type"),
        "frame_window": {"mode": mode, "count": count},
        "num_sessions": len(plan_items),
        "sessions": plan_items,
    }

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
