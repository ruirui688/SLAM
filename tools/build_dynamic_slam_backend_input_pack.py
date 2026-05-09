#!/usr/bin/env python3
"""Build a bounded raw-vs-masked visual SLAM backend input pack.

This script prepares the files that a downstream visual SLAM backend usually
needs: timestamped image lists, a matching ground-truth trajectory snippet, and
parallel raw/masked RGB folders. It intentionally does not run a backend or
report ATE/RPE.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEQUENCE = (
    ROOT
    / "data"
    / "TorWIC_SLAM_Dataset"
    / "Jun. 23, 2022"
    / "Aisle_CW_Run_1"
    / "Aisle_CW_Run_1"
)
SEGMENTATION_DIR = ROOT / "examples" / "semantic_segmentation_example"
DEFAULT_OUTPUT = ROOT / "outputs" / "dynamic_slam_backend_input_pack"
DYNAMIC_FRAME = 2


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_times(sequence_dir: Path, count: int) -> list[float]:
    values = read_lines(sequence_dir / "frame_times.txt")
    if len(values) < count:
        raise ValueError(f"Need {count} frame timestamps, found {len(values)} in {sequence_dir}")
    return [float(value) for value in values[:count]]


def load_trajectory(sequence_dir: Path, count: int) -> list[list[float]]:
    rows: list[list[float]] = []
    for line in read_lines(sequence_dir / "traj_gt.txt")[:count]:
        rows.append([float(value) for value in line.split()])
    if len(rows) < count:
        raise ValueError(f"Need {count} trajectory rows, found {len(rows)} in {sequence_dir}")
    return rows


def mask_dynamic_pixels(rgb: Image.Image, mask: Image.Image) -> Image.Image:
    mask_l = mask.convert("L")
    masked = rgb.copy()
    gray = Image.new("RGB", rgb.size, (118, 118, 118))
    masked.paste(gray, mask=mask_l)
    bbox = mask_l.getbbox()
    if bbox:
        draw = ImageDraw.Draw(masked)
        draw.rectangle(bbox, outline=(220, 38, 38), width=5)
    return masked


def write_rgb_list(path: Path, timestamps: list[float], image_paths: list[Path]) -> None:
    lines = [f"{timestamp:.9f} {rel(image_path)}" for timestamp, image_path in zip(timestamps, image_paths)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_groundtruth(path: Path, trajectory_rows: list[list[float]]) -> None:
    lines = ["# timestamp tx ty tz qx qy qz qw"]
    for row in trajectory_rows:
        if len(row) != 8:
            raise ValueError(f"Expected 8 trajectory values, got {len(row)}: {row}")
        lines.append(" ".join(f"{value:.12g}" for value in row))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_pack(sequence_dir: Path, output_dir: Path, frame_count: int) -> dict:
    image_dir = sequence_dir / "image_left"
    raw_dir = output_dir / "raw" / "image_left"
    masked_dir = output_dir / "masked" / "image_left"
    mask_dir = output_dir / "masked" / "dynamic_masks"
    for directory in (raw_dir, masked_dir, mask_dir):
        directory.mkdir(parents=True, exist_ok=True)

    timestamps = load_times(sequence_dir, frame_count)
    trajectory_rows = load_trajectory(sequence_dir, frame_count)
    source_mask = Image.open(SEGMENTATION_DIR / "forklift-mask.png").convert("L")

    raw_paths: list[Path] = []
    masked_paths: list[Path] = []
    frame_entries: list[dict] = []

    for frame_index in range(frame_count):
        name = f"{frame_index:06d}.png"
        source_rgb = image_dir / name
        if not source_rgb.exists():
            raise FileNotFoundError(f"Missing RGB frame: {source_rgb}")

        raw_path = raw_dir / name
        masked_path = masked_dir / name
        mask_path = mask_dir / name
        shutil.copy2(source_rgb, raw_path)

        rgb = Image.open(source_rgb).convert("RGB")
        if frame_index == DYNAMIC_FRAME:
            mask = source_mask
            if mask.size != rgb.size:
                mask = mask.resize(rgb.size, Image.Resampling.NEAREST)
            masked = mask_dynamic_pixels(rgb, mask)
            mask_pixels = sum(1 for value in mask.getdata() if value > 0)
        else:
            mask = Image.new("L", rgb.size, 0)
            masked = rgb
            mask_pixels = 0

        mask.save(mask_path)
        masked.save(masked_path, quality=95)
        raw_paths.append(raw_path)
        masked_paths.append(masked_path)
        frame_entries.append(
            {
                "frame_index": frame_index,
                "timestamp": timestamps[frame_index],
                "source_rgb": rel(source_rgb),
                "raw_rgb": rel(raw_path),
                "masked_rgb": rel(masked_path),
                "dynamic_mask": rel(mask_path),
                "dynamic_mask_source": "forklift semantic example" if frame_index == DYNAMIC_FRAME else "empty",
                "mask_pixels": mask_pixels,
                "coverage_ratio": mask_pixels / max(rgb.width * rgb.height, 1),
            }
        )

    raw_rgb_list = output_dir / "raw" / "rgb.txt"
    masked_rgb_list = output_dir / "masked" / "rgb.txt"
    groundtruth = output_dir / "groundtruth.txt"
    manifest_path = output_dir / "backend_input_manifest.json"
    write_rgb_list(raw_rgb_list, timestamps, raw_paths)
    write_rgb_list(masked_rgb_list, timestamps, masked_paths)
    write_groundtruth(groundtruth, trajectory_rows)

    manifest = {
        "status": "backend_input_pack_ready",
        "claim_boundary": "Prepares raw/masked RGB inputs and ground-truth snippet; does not run SLAM or report ATE/RPE.",
        "sequence": rel(sequence_dir),
        "frame_count": frame_count,
        "dynamic_mask_policy": "Only frame 000002 uses the tracked forklift semantic mask; other frames use empty masks.",
        "raw_rgb_list": rel(raw_rgb_list),
        "masked_rgb_list": rel(masked_rgb_list),
        "groundtruth_tum": rel(groundtruth),
        "frames": frame_entries,
        "next_backend_step": "Run the same backend on raw/rgb.txt and masked/rgb.txt, then compare against groundtruth.txt with evo_ape/evo_rpe.",
        "example_metric_commands": [
            "evo_ape tum outputs/dynamic_slam_backend_input_pack/groundtruth.txt raw_estimate.txt -va",
            "evo_ape tum outputs/dynamic_slam_backend_input_pack/groundtruth.txt masked_estimate.txt -va",
            "evo_rpe tum outputs/dynamic_slam_backend_input_pack/groundtruth.txt raw_estimate.txt -va",
            "evo_rpe tum outputs/dynamic_slam_backend_input_pack/groundtruth.txt masked_estimate.txt -va",
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sequence-dir", type=Path, default=DEFAULT_SEQUENCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--frame-count", type=int, default=8)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = build_pack(args.sequence_dir, args.output_dir, args.frame_count)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
