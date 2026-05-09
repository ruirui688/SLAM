#!/usr/bin/env python3
"""Run a bounded raw-vs-masked DROID-SLAM smoke test.

This is a deliberately small P132 bridge: it consumes the existing backend
input pack, runs the same DROID-SLAM runtime on raw and masked RGB lists, and
writes estimated trajectories plus a manifest. It is not a full benchmark.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
import traceback
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import cv2
import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
DROID_ROOT = Path("/home/rui/tram/thirdparty/DROID-SLAM")
DEFAULT_WEIGHTS = Path("/home/rui/tram/data/pretrain/droid.pth")
DEFAULT_INPUT = ROOT / "outputs" / "dynamic_slam_backend_input_pack"
DEFAULT_OUTPUT = ROOT / "outputs" / "dynamic_slam_backend_smoke_p132"

# TorWIC left-camera calibration, from Oct. 12, 2022/calibrations.txt.
DEFAULT_CALIB = (621.397474650905, 620.649424677401, 649.644481364277, 367.908146431575)
DEFAULT_DISTORTION = (
    0.0754678811883405,
    -0.0314893098110791,
    0.00101924098521082,
    0.00209529701722382,
    -0.000935223936623030,
)


@dataclass
class RunResult:
    label: str
    status: str
    rgb_list: str
    estimate_tum: str | None
    frame_count: int
    trajectory_rows: int
    error: str | None = None


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_rgb_list(path: Path, limit: int | None) -> list[tuple[float, Path]]:
    rows: list[tuple[float, Path]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        timestamp_s, image_s = line.split(maxsplit=1)
        image_path = ROOT / image_s
        rows.append((float(timestamp_s), image_path))
        if limit is not None and len(rows) >= limit:
            break
    return rows


def image_stream(
    rgb_rows: list[tuple[float, Path]],
    calib: tuple[float, float, float, float],
    distortion: tuple[float, float, float, float, float],
    image_area: int,
) -> Iterator[tuple[float, torch.Tensor, torch.Tensor]]:
    fx, fy, cx, cy = calib
    k = np.array([[fx, 0.0, cx], [0.0, fy, cy], [0.0, 0.0, 1.0]], dtype=np.float32)
    d = np.array(distortion, dtype=np.float32)

    for timestamp, image_path in rgb_rows:
        image = cv2.imread(str(image_path))
        if image is None:
            raise FileNotFoundError(f"Could not read RGB frame: {image_path}")
        h0, w0, _ = image.shape
        image = cv2.undistort(image, k, d)
        scale = (image_area / float(h0 * w0)) ** 0.5
        h1 = int(h0 * scale)
        w1 = int(w0 * scale)
        image = cv2.resize(image, (w1, h1), interpolation=cv2.INTER_AREA)
        image = image[: h1 - h1 % 8, : w1 - w1 % 8]
        tensor = torch.as_tensor(image).permute(2, 0, 1)

        intrinsics = torch.as_tensor([fx, fy, cx, cy], dtype=torch.float32)
        intrinsics[0::2] *= image.shape[1] / w0
        intrinsics[1::2] *= image.shape[0] / h0
        yield timestamp, tensor[None], intrinsics


def write_tum(path: Path, rgb_rows: list[tuple[float, Path]], trajectory: np.ndarray) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = min(len(rgb_rows), len(trajectory))
    lines = ["# timestamp tx ty tz qx qy qz qw"]
    for (timestamp, _), pose in zip(rgb_rows[:rows], trajectory[:rows]):
        tx, ty, tz, qx, qy, qz, qw = [float(value) for value in pose[:7]]
        lines.append(f"{timestamp:.9f} {tx:.12g} {ty:.12g} {tz:.12g} {qx:.12g} {qy:.12g} {qz:.12g} {qw:.12g}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rows


def build_droid_args(args: argparse.Namespace) -> argparse.Namespace:
    droid_args = argparse.Namespace()
    droid_args.weights = str(args.weights)
    droid_args.buffer = args.buffer
    droid_args.image_size = [240, 320]
    droid_args.disable_vis = True
    droid_args.beta = args.beta
    droid_args.filter_thresh = args.filter_thresh
    droid_args.warmup = args.warmup
    droid_args.keyframe_thresh = args.keyframe_thresh
    droid_args.frontend_thresh = args.frontend_thresh
    droid_args.frontend_window = args.frontend_window
    droid_args.frontend_radius = args.frontend_radius
    droid_args.frontend_nms = args.frontend_nms
    droid_args.backend_thresh = args.backend_thresh
    droid_args.backend_radius = args.backend_radius
    droid_args.backend_nms = args.backend_nms
    droid_args.upsample = False
    droid_args.stereo = False
    return droid_args


def run_one(label: str, rgb_list: Path, output_dir: Path, args: argparse.Namespace) -> RunResult:
    sys.path.insert(0, str(DROID_ROOT / "droid_slam"))
    from droid import Droid

    rgb_rows = read_rgb_list(rgb_list, args.frame_limit)
    estimate_path = output_dir / f"{label}_estimate_tum.txt"
    log_path = output_dir / f"{label}_droid_stdout.txt"
    droid_args = build_droid_args(args)

    capture = io.StringIO()
    try:
        with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
            droid = None
            for tstamp, image, intrinsics in image_stream(rgb_rows, args.calib, args.distortion, args.image_area):
                if droid is None:
                    droid_args.image_size = [image.shape[2], image.shape[3]]
                    droid = Droid(droid_args)
                droid.track(tstamp, image, intrinsics=intrinsics)
            if droid is None:
                raise RuntimeError("No frames were loaded")
            trajectory = droid.terminate(
                image_stream(rgb_rows, args.calib, args.distortion, args.image_area),
                backend=args.global_ba,
            )
        rows = write_tum(estimate_path, rgb_rows, trajectory)
        status = "ok" if rows > 0 else "empty_trajectory"
        error = None
    except Exception as exc:  # pragma: no cover - runtime diagnostic path
        status = "failed"
        rows = 0
        error = f"{type(exc).__name__}: {exc}"
        capture.write("\n")
        capture.write(traceback.format_exc())

    log_path.write_text(capture.getvalue(), encoding="utf-8")
    return RunResult(
        label=label,
        status=status,
        rgb_list=rel(rgb_list),
        estimate_tum=rel(estimate_path) if estimate_path.exists() else None,
        frame_count=len(rgb_rows),
        trajectory_rows=rows,
        error=error,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--weights", type=Path, default=DEFAULT_WEIGHTS)
    parser.add_argument("--frame-limit", type=int, default=8)
    parser.add_argument("--image-area", type=int, default=384 * 512)
    parser.add_argument("--buffer", type=int, default=128)
    parser.add_argument("--warmup", type=int, default=4)
    parser.add_argument("--filter-thresh", type=float, default=0.5)
    parser.add_argument("--keyframe-thresh", type=float, default=2.25)
    parser.add_argument("--frontend-thresh", type=float, default=12.0)
    parser.add_argument("--frontend-window", type=int, default=12)
    parser.add_argument("--frontend-radius", type=int, default=2)
    parser.add_argument("--frontend-nms", type=int, default=1)
    parser.add_argument("--backend-thresh", type=float, default=15.0)
    parser.add_argument("--backend-radius", type=int, default=2)
    parser.add_argument("--backend-nms", type=int, default=3)
    parser.add_argument("--beta", type=float, default=0.6)
    parser.add_argument(
        "--global-ba",
        action="store_true",
        help="Enable DROID global bundle adjustment. Disabled by default because the bounded smoke window can be too short for proximity edges.",
    )
    parser.set_defaults(calib=DEFAULT_CALIB, distortion=DEFAULT_DISTORTION)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    torch.multiprocessing.set_start_method("spawn", force=True)

    raw_result = run_one("raw", args.input_dir / "raw" / "rgb.txt", args.output_dir, args)
    masked_result = run_one("masked", args.input_dir / "masked" / "rgb.txt", args.output_dir, args)

    manifest = {
        "artifact": "P132 dynamic SLAM backend smoke run",
        "created": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "status": "ok" if raw_result.status == "ok" and masked_result.status == "ok" else "needs_followup",
        "claim_boundary": "Bounded DROID-SLAM smoke run only; not yet a full ATE/RPE benchmark or navigation claim.",
        "runtime": {
            "python": sys.executable,
            "torch": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "droid_root": str(DROID_ROOT),
            "weights": str(args.weights),
        },
        "input_dir": rel(args.input_dir),
        "output_dir": rel(args.output_dir),
        "frame_limit": args.frame_limit,
        "global_ba": args.global_ba,
        "runs": [asdict(raw_result), asdict(masked_result)],
        "next_step": "If both runs are ok, evaluate raw/masked estimates against groundtruth.txt with evo APE/RPE.",
    }
    manifest_path = args.output_dir / "dynamic_slam_backend_smoke_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
