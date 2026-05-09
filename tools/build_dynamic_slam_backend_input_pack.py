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

import cv2
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter


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


def load_dynamic_masks_from_summaries(summary_dirs: list[Path] | None, label_prefix: str) -> dict[int, list[Path]]:
    if not summary_dirs:
        return {}
    masks_by_frame: dict[int, list[Path]] = {}
    seen: set[Path] = set()
    for summary_dir in summary_dirs:
        for summary_path in sorted(summary_dir.glob(f"{label_prefix}*_summary.json")):
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
            rgb_path = Path(payload["rgb_path"])
            try:
                frame_index = int(rgb_path.stem)
            except ValueError:
                continue
            mask_value = payload.get("mask_path") or payload.get("outputs", {}).get("mask")
            if not mask_value:
                continue
            mask_path = Path(mask_value)
            if mask_path.exists() and mask_path not in seen:
                masks_by_frame.setdefault(frame_index, []).append(mask_path)
                seen.add(mask_path)
    return masks_by_frame


def combine_masks(mask_paths: list[Path], size: tuple[int, int]) -> Image.Image:
    combined = Image.new("L", size, 0)
    for mask_path in mask_paths:
        mask = Image.open(mask_path).convert("L")
        if mask.size != size:
            mask = mask.resize(size, Image.Resampling.NEAREST)
        combined = ImageChops.lighter(combined, mask)
    return combined


def nearest_mask_frame(frame_index: int, masks_by_frame: dict[int, list[Path]], radius: int) -> int | None:
    if radius <= 0 or not masks_by_frame:
        return None
    candidates = [
        (abs(frame_index - candidate), candidate)
        for candidate in masks_by_frame
        if 0 < abs(frame_index - candidate) <= radius
    ]
    if not candidates:
        return None
    return min(candidates)[1]


def dilate_mask(mask: Image.Image, pixels: int) -> Image.Image:
    if pixels <= 0:
        return mask
    kernel = pixels * 2 + 1
    if kernel % 2 == 0:
        kernel += 1
    return mask.filter(ImageFilter.MaxFilter(kernel))


def load_gray_frame(sequence_dir: Path, frame_index: int) -> np.ndarray:
    path = sequence_dir / "image_left" / f"{frame_index:06d}.png"
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(f"Missing RGB frame for flow propagation: {path}")
    return image


def warp_mask_between_frames(mask: Image.Image, sequence_dir: Path, src_index: int, dst_index: int) -> Image.Image:
    """Warp a mask from src_index to dst_index using backward dense optical flow."""
    if src_index == dst_index:
        return mask
    current = np.asarray(mask.convert("L"), dtype=np.uint8)
    step = 1 if dst_index > src_index else -1
    src = src_index
    while src != dst_index:
        dst = src + step
        gray_src = load_gray_frame(sequence_dir, src)
        gray_dst = load_gray_frame(sequence_dir, dst)
        if current.shape != gray_src.shape:
            current = cv2.resize(current, (gray_src.shape[1], gray_src.shape[0]), interpolation=cv2.INTER_NEAREST)
        flow_dst_to_src = cv2.calcOpticalFlowFarneback(
            gray_dst,
            gray_src,
            None,
            pyr_scale=0.5,
            levels=3,
            winsize=21,
            iterations=3,
            poly_n=5,
            poly_sigma=1.2,
            flags=0,
        )
        h, w = gray_dst.shape
        grid_x, grid_y = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
        map_x = grid_x + flow_dst_to_src[..., 0]
        map_y = grid_y + flow_dst_to_src[..., 1]
        current = cv2.remap(
            current,
            map_x,
            map_y,
            interpolation=cv2.INTER_NEAREST,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0,
        )
        _, current = cv2.threshold(current, 1, 255, cv2.THRESH_BINARY)
        src = dst
    return Image.fromarray(current, mode="L")


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


def build_pack(
    sequence_dir: Path,
    output_dir: Path,
    frame_count: int,
    dynamic_mask_summary_dirs: list[Path] | None = None,
    dynamic_label_prefix: str = "forklift",
    temporal_propagation_radius: int = 0,
    dynamic_mask_dilation_px: int = 0,
    temporal_propagation_mode: str = "nearest",
) -> dict:
    image_dir = sequence_dir / "image_left"
    raw_dir = output_dir / "raw" / "image_left"
    masked_dir = output_dir / "masked" / "image_left"
    mask_dir = output_dir / "masked" / "dynamic_masks"
    for directory in (raw_dir, masked_dir, mask_dir):
        directory.mkdir(parents=True, exist_ok=True)

    timestamps = load_times(sequence_dir, frame_count)
    trajectory_rows = load_trajectory(sequence_dir, frame_count)
    source_mask = Image.open(SEGMENTATION_DIR / "forklift-mask.png").convert("L")
    dynamic_masks_by_frame = load_dynamic_masks_from_summaries(dynamic_mask_summary_dirs, dynamic_label_prefix)

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
        propagated_from: int | None = None
        if frame_index in dynamic_masks_by_frame:
            mask = combine_masks(dynamic_masks_by_frame[frame_index], rgb.size)
            dynamic_source = "existing semantic frontend masks"
        elif dynamic_mask_summary_dirs is not None:
            propagated_from = nearest_mask_frame(frame_index, dynamic_masks_by_frame, temporal_propagation_radius)
            if propagated_from is not None:
                mask = combine_masks(dynamic_masks_by_frame[propagated_from], rgb.size)
                if temporal_propagation_mode == "flow":
                    mask = warp_mask_between_frames(mask, sequence_dir, propagated_from, frame_index)
                    if mask.size != rgb.size:
                        mask = mask.resize(rgb.size, Image.Resampling.NEAREST)
                    dynamic_source = f"optical-flow propagation from frame {propagated_from:06d}"
                else:
                    dynamic_source = f"nearest-frame propagation from frame {propagated_from:06d}"
            else:
                mask = Image.new("L", rgb.size, 0)
                masked = rgb
                mask_pixels = 0
                dynamic_source = "empty"
        elif dynamic_mask_summary_dirs is None and frame_index == DYNAMIC_FRAME:
            mask = source_mask
            if mask.size != rgb.size:
                mask = mask.resize(rgb.size, Image.Resampling.NEAREST)
            dynamic_source = "forklift semantic example"
        else:
            mask = Image.new("L", rgb.size, 0)
            masked = rgb
            mask_pixels = 0
            dynamic_source = "empty"

        if dynamic_source != "empty":
            mask = dilate_mask(mask, dynamic_mask_dilation_px)
            masked = mask_dynamic_pixels(rgb, mask)
            mask_pixels = sum(1 for value in mask.getdata() if value > 0)

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
                "dynamic_mask_source": dynamic_source,
                "dynamic_mask_inputs": [
                    rel(path) for path in dynamic_masks_by_frame.get(
                        frame_index if propagated_from is None else propagated_from,
                        [],
                    )
                ],
                "propagated_from_frame": propagated_from,
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
        "dynamic_mask_policy": (
            f"Use existing {dynamic_label_prefix} semantic frontend masks when --dynamic-mask-summary-dir is provided; "
            "otherwise only frame 000002 uses the repository forklift semantic example mask."
        ),
        "dynamic_mask_summary_dirs": [rel(path) for path in dynamic_mask_summary_dirs] if dynamic_mask_summary_dirs else None,
        "dynamic_mask_summary_dir": rel(dynamic_mask_summary_dirs[0]) if dynamic_mask_summary_dirs else None,
        "temporal_propagation_radius": temporal_propagation_radius,
        "temporal_propagation_mode": temporal_propagation_mode,
        "dynamic_mask_dilation_px": dynamic_mask_dilation_px,
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
    parser.add_argument("--dynamic-mask-summary-dir", type=Path, action="append", default=None)
    parser.add_argument("--dynamic-label-prefix", default="forklift")
    parser.add_argument(
        "--temporal-propagation-radius",
        type=int,
        default=0,
        help="Copy the nearest available semantic mask to neighboring frames within this radius. Use as a diagnostic stress test, not as a true detector output.",
    )
    parser.add_argument("--dynamic-mask-dilation-px", type=int, default=0)
    parser.add_argument(
        "--temporal-propagation-mode",
        choices=("nearest", "flow"),
        default="nearest",
        help="Use nearest-frame mask copy or dense optical-flow warping for propagated diagnostic masks.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = build_pack(
        args.sequence_dir,
        args.output_dir,
        args.frame_count,
        args.dynamic_mask_summary_dir,
        args.dynamic_label_prefix,
        args.temporal_propagation_radius,
        args.dynamic_mask_dilation_px,
        args.temporal_propagation_mode,
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
