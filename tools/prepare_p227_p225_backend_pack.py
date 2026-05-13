#!/usr/bin/env python3
"""Prepare a DROID backend input pack from the P225 learned-mask sequence."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "outputs" / "temporal_masked_sequence_p225" / "sequence"
DEFAULT_OUTPUT = ROOT / "outputs" / "dynamic_slam_backend_input_pack_p227_p225_learned_mask"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_rgb_rows(path: Path, limit: int | None) -> list[tuple[float, str]]:
    rows: list[tuple[float, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        timestamp_s, image_s = line.split(maxsplit=1)
        rows.append((float(timestamp_s), image_s))
        if limit is not None and len(rows) >= limit:
            break
    return rows


def read_gt_rows(path: Path, limit: int | None) -> list[str]:
    rows: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        rows.append(line)
        if limit is not None and len(rows) >= limit:
            break
    return rows


def write_rgb_list(path: Path, rows: list[tuple[float, Path]]) -> None:
    lines = [f"{timestamp:.9f} {rel(image_path)}" for timestamp, image_path in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def copy_variant(source_root: Path, output_root: Path, label: str, frame_limit: int | None) -> list[tuple[float, Path]]:
    rows = read_rgb_rows(source_root / label / "rgb.txt", frame_limit)
    image_out = output_root / label / "image_left"
    image_out.mkdir(parents=True, exist_ok=True)
    copied: list[tuple[float, Path]] = []
    for index, (timestamp, image_rel) in enumerate(rows):
        src = source_root / label / image_rel
        dst = image_out / f"{index:06d}.png"
        if not src.exists():
            raise FileNotFoundError(src)
        shutil.copy2(src, dst)
        copied.append((timestamp, dst))
    write_rgb_list(output_root / label / "rgb.txt", copied)
    return copied


def count_mask_pixels(path: Path) -> tuple[int, int, int]:
    mask = Image.open(path).convert("L")
    histogram = mask.histogram()
    nonzero = sum(histogram[1:])
    width, height = mask.size
    return nonzero, width, height


def copy_masks(source_root: Path, output_root: Path, frame_limit: int | None) -> list[dict]:
    mask_out = output_root / "predicted_masks"
    mask_out.mkdir(parents=True, exist_ok=True)
    masks = sorted((source_root / "predicted_masks").glob("*_p218_pred_mask.png"))
    if frame_limit is not None:
        masks = masks[:frame_limit]
    entries = []
    for index, src in enumerate(masks):
        dst = mask_out / f"{index:06d}_p218_pred_mask.png"
        shutil.copy2(src, dst)
        mask_pixels, width, height = count_mask_pixels(dst)
        entries.append(
            {
                "frame_index": index,
                "predicted_mask": rel(dst),
                "source_mask": rel(src),
                "mask_pixels": mask_pixels,
                "coverage_ratio": mask_pixels / max(width * height, 1),
            }
        )
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--frame-limit", type=int, default=None)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_rows = copy_variant(args.source_dir, args.output_dir, "raw", args.frame_limit)
    masked_rows = copy_variant(args.source_dir, args.output_dir, "masked", args.frame_limit)
    if len(raw_rows) != len(masked_rows):
        raise RuntimeError(f"raw/masked row count mismatch: {len(raw_rows)} vs {len(masked_rows)}")

    gt_rows = read_gt_rows(args.source_dir / "raw" / "groundtruth.txt", args.frame_limit)
    gt_path = args.output_dir / "groundtruth.txt"
    gt_path.write_text("# timestamp tx ty tz qx qy qz qw\n" + "\n".join(gt_rows) + "\n", encoding="utf-8")
    for name in ("frame_times.txt", "calibrations.txt", "TorWIC_mono_left.yaml"):
        shutil.copy2(args.source_dir / "raw" / name, args.output_dir / name)

    mask_entries = copy_masks(args.source_dir, args.output_dir, args.frame_limit)
    manifest = {
        "artifact": "P227 P225 learned-mask DROID backend input pack",
        "created": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "status": "backend_input_pack_ready",
        "claim_boundary": "Compatibility pack only; it copies P225 raw/masked learned-mask sequence files and does not run SLAM or claim trajectory improvement.",
        "source_dir": rel(args.source_dir),
        "output_dir": rel(args.output_dir),
        "frame_count": len(raw_rows),
        "raw_rgb_list": rel(args.output_dir / "raw" / "rgb.txt"),
        "masked_rgb_list": rel(args.output_dir / "masked" / "rgb.txt"),
        "groundtruth_tum": rel(gt_path),
        "dynamic_mask_policy": "P225 bounded retrained SmallUNet predicted-mask region; masked RGB comes from P225 learned-mask package.",
        "predicted_mask_region_proxy": True,
        "frames": [
            {
                "frame_index": index,
                "timestamp": timestamp,
                "raw_rgb": rel(raw_path),
                "masked_rgb": rel(masked_rows[index][1]),
                "dynamic_mask": mask_entries[index]["predicted_mask"] if index < len(mask_entries) else None,
                "source_dynamic_mask": mask_entries[index]["source_mask"] if index < len(mask_entries) else None,
                "mask_pixels": mask_entries[index]["mask_pixels"] if index < len(mask_entries) else 0,
                "coverage_ratio": mask_entries[index]["coverage_ratio"] if index < len(mask_entries) else 0.0,
            }
            for index, (timestamp, raw_path) in enumerate(raw_rows)
        ],
    }
    manifest_path = args.output_dir / "backend_input_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
