#!/usr/bin/env python3
"""Run local Grounding DINO + SAM2 forklift frontend over a TorWIC frame window."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEQUENCE = (
    ROOT
    / "data"
    / "TorWIC_SLAM_Dataset"
    / "Jun. 23, 2022"
    / "Aisle_CW_Run_1"
    / "Aisle_CW_Run_1"
)
DEFAULT_OUTPUT_ROOT = ROOT / "outputs"


def read_times(sequence_dir: Path) -> list[float]:
    return [
        float(line.strip())
        for line in (sequence_dir / "frame_times.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sequence-dir", type=Path, default=DEFAULT_SEQUENCE)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--session-id", default="torwic_jun23_aisle_cw_run1")
    parser.add_argument("--start-frame", type=int, required=True)
    parser.add_argument("--end-frame-exclusive", type=int, required=True)
    parser.add_argument("--prompt", default="forklift.")
    parser.add_argument("--box-threshold", type=float, default=0.25)
    parser.add_argument("--text-threshold", type=float, default=0.20)
    parser.add_argument("--max-detections", type=int, default=4)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def has_forklift_summary(output_dir: Path) -> bool:
    frontend = output_dir / "frontend_output"
    return any(frontend.glob("forklift*_summary.json"))


def main() -> None:
    args = parse_args()
    if args.end_frame_exclusive <= args.start_frame:
        raise ValueError("--end-frame-exclusive must be greater than --start-frame")

    times = read_times(args.sequence_dir)
    script = ROOT / "tools" / "demo_local_grounded_sam2_observations.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")

    results: list[dict[str, object]] = []
    for frame_index in range(args.start_frame, args.end_frame_exclusive):
        rgb_path = args.sequence_dir / "image_left" / f"{frame_index:06d}.png"
        if not rgb_path.is_file():
            raise FileNotFoundError(f"Missing RGB frame: {rgb_path}")
        output_dir = args.output_root / f"{args.session_id}_f{frame_index:06d}"
        if has_forklift_summary(output_dir) and not args.force:
            results.append(
                {
                    "frame_index": frame_index,
                    "status": "skipped_existing",
                    "output_dir": str(output_dir.relative_to(ROOT)),
                }
            )
            continue

        cmd = [
            sys.executable,
            str(script),
            "--rgb",
            str(rgb_path),
            "--prompt",
            args.prompt,
            "--output-dir",
            str(output_dir),
            "--session-id",
            args.session_id,
            "--frame-id",
            f"{frame_index:06d}",
            "--frame-index",
            str(frame_index),
            "--timestamp",
            str(times[frame_index]),
            "--box-threshold",
            str(args.box_threshold),
            "--text-threshold",
            str(args.text_threshold),
            "--max-detections",
            str(args.max_detections),
            "--grounding-device",
            "cuda",
            "--sam2-device",
            "cuda",
        ]
        completed = subprocess.run(cmd, cwd=ROOT, env=env, text=True, capture_output=True)
        if completed.returncode != 0:
            results.append(
                {
                    "frame_index": frame_index,
                    "status": "failed",
                    "output_dir": str(output_dir.relative_to(ROOT)),
                    "stderr_tail": completed.stderr[-2000:],
                }
            )
            raise RuntimeError(json.dumps(results[-1], indent=2, ensure_ascii=False))
        results.append(
            {
                "frame_index": frame_index,
                "status": "generated",
                "output_dir": str(output_dir.relative_to(ROOT)),
            }
        )

    generated = sum(1 for item in results if item["status"] == "generated")
    skipped = sum(1 for item in results if item["status"] == "skipped_existing")
    payload = {
        "status": "torwic_forklift_frontend_window_complete",
        "sequence": str(args.sequence_dir.relative_to(ROOT)),
        "frame_window": [args.start_frame, args.end_frame_exclusive],
        "generated": generated,
        "skipped_existing": skipped,
        "results": results,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
