"""
Minimal OVO-style 2D -> 3D object initialization.

This script intentionally implements only the geometric initialization layer
described by OVO (Open-Vocabulary Online Semantic Mapping for SLAM):

1. Input: one RGB-D frame and one 2D segmentation mask.
2. Convert masked depth pixels into 3D points via camera intrinsics.
3. Output: the object's 3D point cloud fragment / 3D segment.

It does not implement SLAM, multi-view fusion, CLIP aggregation, global
tracking, loop closure, or any higher-level OVO modules.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from PIL import Image


@dataclass(frozen=True)
class CameraIntrinsics:
    fx: float
    fy: float
    cx: float
    cy: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rgb", type=Path, required=True, help="Path to the RGB frame.")
    parser.add_argument("--depth", type=Path, required=True, help="Path to the aligned depth image.")
    parser.add_argument("--mask", type=Path, required=True, help="Path to the binary 2D mask.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory to save outputs.")
    parser.add_argument(
        "--object-name",
        type=str,
        default="object",
        help="Object name used in output file names and metadata.",
    )
    parser.add_argument(
        "--calibration-file",
        type=Path,
        default=None,
        help="Optional TorWIC-style calibrations.txt file.",
    )
    parser.add_argument(
        "--camera-key",
        type=str,
        default="Camera1",
        help="Camera prefix inside calibrations.txt, e.g. Camera1 or Camera2.",
    )
    parser.add_argument("--fx", type=float, default=None, help="Focal length in x.")
    parser.add_argument("--fy", type=float, default=None, help="Focal length in y.")
    parser.add_argument("--cx", type=float, default=None, help="Principal point x.")
    parser.add_argument("--cy", type=float, default=None, help="Principal point y.")
    parser.add_argument(
        "--depth-scale",
        type=float,
        default=1000.0,
        help="Divide uint16 depth values by this factor to obtain meters.",
    )
    parser.add_argument(
        "--min-depth-m",
        type=float,
        default=0.1,
        help="Ignore points closer than this depth in meters.",
    )
    parser.add_argument(
        "--max-depth-m",
        type=float,
        default=10.0,
        help="Ignore points farther than this depth in meters.",
    )
    parser.add_argument(
        "--mask-threshold",
        type=int,
        default=127,
        help="Pixels above this value are treated as inside the mask.",
    )
    return parser.parse_args()


def load_intrinsics(args: argparse.Namespace) -> CameraIntrinsics:
    if args.calibration_file is not None:
        calibration_text = args.calibration_file.read_text(encoding="utf-8")
        values = {}
        for key in ("fx", "fy", "cx", "cy"):
            marker = f"{args.camera_key}.{key}:"
            for line in calibration_text.splitlines():
                if marker in line:
                    values[key] = float(line.split(":", 1)[1].strip())
                    break
        if len(values) == 4:
            return CameraIntrinsics(**values)
        missing = sorted({"fx", "fy", "cx", "cy"} - set(values))
        raise ValueError(f"Missing intrinsics {missing} in calibration file {args.calibration_file}")

    explicit = {"fx": args.fx, "fy": args.fy, "cx": args.cx, "cy": args.cy}
    if all(value is not None for value in explicit.values()):
        return CameraIntrinsics(
            fx=float(args.fx),
            fy=float(args.fy),
            cx=float(args.cx),
            cy=float(args.cy),
        )

    raise ValueError("Provide either --calibration-file or all of --fx --fy --cx --cy.")


def load_rgb_depth_mask(
    rgb_path: Path,
    depth_path: Path,
    mask_path: Path,
    mask_threshold: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rgb = np.array(Image.open(rgb_path).convert("RGB"), dtype=np.uint8)
    depth = np.array(Image.open(depth_path), dtype=np.uint16)
    mask = np.array(Image.open(mask_path).convert("L"), dtype=np.uint8) > mask_threshold

    if rgb.shape[:2] != depth.shape[:2] or rgb.shape[:2] != mask.shape[:2]:
        raise ValueError(
            f"Shape mismatch: rgb={rgb.shape[:2]}, depth={depth.shape[:2]}, mask={mask.shape[:2]}"
        )

    return rgb, depth, mask


def backproject_masked_points(
    rgb: np.ndarray,
    depth_u16: np.ndarray,
    mask: np.ndarray,
    intrinsics: CameraIntrinsics,
    depth_scale: float,
    min_depth_m: float,
    max_depth_m: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    depth_m = depth_u16.astype(np.float32) / float(depth_scale)
    valid = mask & np.isfinite(depth_m) & (depth_m > min_depth_m) & (depth_m < max_depth_m)

    v_coords, u_coords = np.nonzero(valid)
    if len(u_coords) == 0:
        raise ValueError("No valid masked depth pixels remained after depth filtering.")

    z = depth_m[v_coords, u_coords]
    x = (u_coords.astype(np.float32) - intrinsics.cx) * z / intrinsics.fx
    y = (v_coords.astype(np.float32) - intrinsics.cy) * z / intrinsics.fy
    points = np.stack([x, y, z], axis=1)
    colors = rgb[v_coords, u_coords]
    pixels = np.stack([u_coords, v_coords], axis=1)
    return points, colors, pixels


def write_ascii_ply(path: Path, points: np.ndarray, colors: np.ndarray) -> None:
    with path.open("w", encoding="utf-8") as handle:
        handle.write("ply\n")
        handle.write("format ascii 1.0\n")
        handle.write(f"element vertex {len(points)}\n")
        handle.write("property float x\n")
        handle.write("property float y\n")
        handle.write("property float z\n")
        handle.write("property uchar red\n")
        handle.write("property uchar green\n")
        handle.write("property uchar blue\n")
        handle.write("end_header\n")
        for point, color in zip(points, colors):
            handle.write(
                f"{point[0]:.6f} {point[1]:.6f} {point[2]:.6f} "
                f"{int(color[0])} {int(color[1])} {int(color[2])}\n"
            )


def point_cloud_stats(points: np.ndarray) -> dict[str, object]:
    mins = points.min(axis=0)
    maxs = points.max(axis=0)
    centroid = points.mean(axis=0)
    return {
        "num_points": int(points.shape[0]),
        "centroid_xyz_m": centroid.tolist(),
        "bbox_min_xyz_m": mins.tolist(),
        "bbox_max_xyz_m": maxs.tolist(),
        "bbox_size_xyz_m": (maxs - mins).tolist(),
    }


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def main() -> None:
    args = parse_args()
    intrinsics = load_intrinsics(args)
    rgb, depth, mask = load_rgb_depth_mask(args.rgb, args.depth, args.mask, args.mask_threshold)
    points, colors, pixels = backproject_masked_points(
        rgb=rgb,
        depth_u16=depth,
        mask=mask,
        intrinsics=intrinsics,
        depth_scale=args.depth_scale,
        min_depth_m=args.min_depth_m,
        max_depth_m=args.max_depth_m,
    )

    ensure_dir(args.output_dir)
    stem = args.object_name.replace(" ", "_")
    ply_path = args.output_dir / f"{stem}_pointcloud.ply"
    npz_path = args.output_dir / f"{stem}_pointcloud.npz"
    json_path = args.output_dir / f"{stem}_summary.json"

    write_ascii_ply(ply_path, points, colors)
    np.savez_compressed(
        npz_path,
        points_xyz_m=points.astype(np.float32),
        colors_rgb_u8=colors.astype(np.uint8),
        pixels_uv=pixels.astype(np.int32),
    )

    summary = {
        "method": "OVO-inspired minimal object initialization",
        "rgb_path": str(args.rgb),
        "depth_path": str(args.depth),
        "mask_path": str(args.mask),
        "object_name": args.object_name,
        "intrinsics": {
            "fx": intrinsics.fx,
            "fy": intrinsics.fy,
            "cx": intrinsics.cx,
            "cy": intrinsics.cy,
        },
        "depth_scale": args.depth_scale,
        "min_depth_m": args.min_depth_m,
        "max_depth_m": args.max_depth_m,
        "coordinate_frame": "camera",
        "stats": point_cloud_stats(points),
        "outputs": {
            "ply": str(ply_path),
            "npz": str(npz_path),
        },
    }
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
