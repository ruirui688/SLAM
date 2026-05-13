#!/usr/bin/env python3
"""Evaluate P235 soft/boundary-aware frontend masks.

This tool reuses the P233/P225 probability windows and builds frontend packs
whose masked images avoid hard black cutout boundaries by attenuating or
feathering high-probability regions. It is intentionally bounded to short
frontend smoke evidence.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import io
import json
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import apply_confidence_gated_mask_module_p228 as p228  # noqa: E402


OUTPUT_ROOT = ROOT / "outputs/soft_boundary_mask_p235"
EVIDENCE_JSON = ROOT / "paper/evidence/soft_boundary_mask_p235.json"
EVIDENCE_CSV = ROOT / "paper/evidence/soft_boundary_mask_p235.csv"
EXPORT_MD = ROOT / "paper/export/soft_boundary_mask_p235.md"
P233_JSON = ROOT / "paper/evidence/gated_mask_multi_window_p233.json"
P234_JSON = ROOT / "paper/evidence/gated_mask_failure_sweep_p234.json"

WINDOWS = {
    "aisle_cw_0840_0899": {
        "id": "aisle_cw_0840_0899",
        "sequence_label": "Oct. 12, 2022 Aisle_CW",
        "start_index": 840,
        "end_index": 899,
        "source_dir": ROOT / "outputs/gated_mask_multi_window_p233/aisle_cw_0840_0899/temporal_masked_sequence_p225/sequence",
        "priority": "failure_regression",
    },
    "aisle_cw_0480_0539": {
        "id": "aisle_cw_0480_0539",
        "sequence_label": "Oct. 12, 2022 Aisle_CW",
        "start_index": 480,
        "end_index": 539,
        "source_dir": ROOT / "outputs/temporal_masked_sequence_p225/sequence",
        "priority": "original_story_seed",
    },
    "aisle_cw_0120_0179": {
        "id": "aisle_cw_0120_0179",
        "sequence_label": "Oct. 12, 2022 Aisle_CW",
        "start_index": 120,
        "end_index": 179,
        "source_dir": ROOT / "outputs/gated_mask_multi_window_p233/aisle_cw_0120_0179/temporal_masked_sequence_p225/sequence",
        "priority": "p233_backtest",
    },
}


@dataclass(frozen=True)
class SoftVariant:
    variant_id: str
    method: str
    probability_threshold: float = 0.60
    dilation_px: int = 0
    min_component_area_px: int = 256
    max_coverage: float = 0.12
    target_coverage: float = 0.10
    attenuation_alpha: float = 0.35
    feather_sigma: float = 0.0
    mean_fill: bool = False


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_rgb_rows(path: Path, limit: int | None = None) -> list[tuple[float, str]]:
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


def read_gt_rows(path: Path, limit: int | None = None) -> list[str]:
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(f"{ts:.9f} {rel(img)}" for ts, img in rows) + "\n", encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def variants() -> list[SoftVariant]:
    return [
        SoftVariant("alpha035_thr060_cap012_min256", "alpha_attenuation", attenuation_alpha=0.35),
        SoftVariant("alpha050_thr060_cap012_min256", "alpha_attenuation", attenuation_alpha=0.50),
        SoftVariant("feather035_sigma5_thr060_cap012_min256", "feathered_boundary", attenuation_alpha=0.35, feather_sigma=5.0),
        SoftVariant("feather050_sigma7_thr060_cap012_min256", "feathered_boundary", attenuation_alpha=0.50, feather_sigma=7.0),
        SoftVariant("meanfill035_feather5_thr060_cap012_min256", "mean_color_feather", attenuation_alpha=0.35, feather_sigma=5.0, mean_fill=True),
    ]


def mask_from_probability(probability: np.ndarray, variant: SoftVariant) -> tuple[np.ndarray, dict[str, Any]]:
    params = p228.GateParams(
        probability_threshold=variant.probability_threshold,
        dilation_px=variant.dilation_px,
        min_component_area_px=variant.min_component_area_px,
        max_coverage=variant.max_coverage,
        target_coverage=variant.target_coverage,
        mask_value=0,
    )
    return p228.build_mask(probability, params)


def alpha_map_from_mask(mask: np.ndarray, variant: SoftVariant) -> np.ndarray:
    alpha = mask.astype(np.float32) * variant.attenuation_alpha
    if variant.feather_sigma > 0 and np.any(mask):
        ksize = int(round(variant.feather_sigma * 6.0)) | 1
        feathered = cv2.GaussianBlur(alpha, (ksize, ksize), variant.feather_sigma)
        alpha = np.maximum(alpha, feathered)
        alpha = np.clip(alpha, 0.0, variant.attenuation_alpha)
    return alpha


def apply_soft_mask(raw: np.ndarray, mask: np.ndarray, variant: SoftVariant) -> tuple[np.ndarray, dict[str, Any]]:
    alpha = alpha_map_from_mask(mask, variant)
    if variant.mean_fill and np.any(mask):
        fill_color = raw[mask].mean(axis=0, keepdims=True).reshape(1, 1, 3)
    else:
        fill_color = np.zeros((1, 1, 3), dtype=np.float32)
    raw_f = raw.astype(np.float32)
    soft = raw_f * (1.0 - alpha[..., None]) + fill_color.astype(np.float32) * alpha[..., None]
    output = np.clip(np.rint(soft), 0, 255).astype(np.uint8)
    stats = {
        "mean_soft_alpha": float(alpha.mean()),
        "max_soft_alpha": float(alpha.max()) if alpha.size else 0.0,
        "nonzero_alpha_pixels": int(np.count_nonzero(alpha > 0.001)),
    }
    return output, stats


def copy_sidecars(source_dir: Path, sequence_dir: Path, pack_dir: Path, frame_limit: int | None) -> None:
    for dst_variant in ("raw", "masked"):
        for name in ("TorWIC_mono_left.yaml", "calibrations.txt", "frame_times.txt", "groundtruth.txt", "traj_gt.txt"):
            src = source_dir / "raw" / name
            if src.exists():
                shutil.copy2(src, sequence_dir / dst_variant / name)
    gt_rows = read_gt_rows(source_dir / "raw" / "groundtruth.txt", frame_limit)
    (pack_dir / "groundtruth.txt").write_text(
        "# timestamp tx ty tz qx qy qz qw\n" + "\n".join(gt_rows) + "\n",
        encoding="utf-8",
    )
    for name in ("frame_times.txt", "calibrations.txt", "TorWIC_mono_left.yaml"):
        shutil.copy2(source_dir / "raw" / name, pack_dir / name)


def build_variant_pack(args: argparse.Namespace, window: dict[str, Any], variant: SoftVariant) -> dict[str, Any]:
    source_dir = window["source_dir"]
    variant_root = args.output_root / window["id"] / variant.variant_id
    sequence_dir = variant_root / "temporal_masked_sequence_p235_soft_boundary"
    pack_dir = variant_root / "dynamic_slam_backend_input_pack_p235_soft_boundary"
    for path in (
        sequence_dir / "sequence/raw/image_left",
        sequence_dir / "sequence/masked/image_left",
        sequence_dir / "sequence/predicted_masks",
        sequence_dir / "sequence/probabilities",
        pack_dir / "raw/image_left",
        pack_dir / "masked/image_left",
        pack_dir / "predicted_masks",
        pack_dir / "probabilities",
    ):
        path.mkdir(parents=True, exist_ok=True)

    raw_rows: list[tuple[float, Path]] = []
    masked_rows: list[tuple[float, Path]] = []
    pack_raw_rows: list[tuple[float, Path]] = []
    pack_masked_rows: list[tuple[float, Path]] = []
    frames: list[dict[str, Any]] = []
    rows = read_rgb_rows(source_dir / "raw/rgb.txt", args.frame_limit)
    raw_shape: tuple[int, int] | None = None
    for index, (timestamp, image_rel) in enumerate(rows):
        raw_src = source_dir / "raw" / image_rel
        prob_src = source_dir / "probabilities" / f"{index:06d}_p218_prob.png"
        raw = np.array(Image.open(raw_src).convert("RGB"))
        probability_u8 = np.array(Image.open(prob_src).convert("L"))
        probability = probability_u8.astype(np.float32) / 255.0
        mask, mask_stats = mask_from_probability(probability, variant)
        masked, soft_stats = apply_soft_mask(raw, mask, variant)
        raw_shape = raw.shape[:2]

        raw_name = f"{index:06d}.png"
        mask_name = f"{index:06d}_p235_soft_boundary_mask.png"
        prob_name = f"{index:06d}_p218_prob.png"
        seq_raw = sequence_dir / "sequence/raw/image_left" / raw_name
        seq_masked = sequence_dir / "sequence/masked/image_left" / raw_name
        seq_mask = sequence_dir / "sequence/predicted_masks" / mask_name
        seq_prob = sequence_dir / "sequence/probabilities" / prob_name
        pack_raw = pack_dir / "raw/image_left" / raw_name
        pack_masked = pack_dir / "masked/image_left" / raw_name
        pack_mask = pack_dir / "predicted_masks" / mask_name
        pack_prob = pack_dir / "probabilities" / prob_name

        Image.fromarray(raw).save(seq_raw)
        Image.fromarray(masked).save(seq_masked)
        Image.fromarray((mask.astype(np.uint8) * 255), mode="L").save(seq_mask)
        shutil.copy2(prob_src, seq_prob)
        shutil.copy2(seq_raw, pack_raw)
        shutil.copy2(seq_masked, pack_masked)
        shutil.copy2(seq_mask, pack_mask)
        shutil.copy2(seq_prob, pack_prob)
        raw_rows.append((timestamp, seq_raw))
        masked_rows.append((timestamp, seq_masked))
        pack_raw_rows.append((timestamp, pack_raw))
        pack_masked_rows.append((timestamp, pack_masked))
        frames.append(
            {
                "frame_index": index,
                "timestamp": timestamp,
                "raw_rgb": rel(pack_raw),
                "masked_rgb": rel(pack_masked),
                "dynamic_mask": rel(pack_mask),
                "source_probability": rel(prob_src),
                **mask_stats,
                **soft_stats,
            }
        )

    write_rgb_list(sequence_dir / "sequence/raw/rgb.txt", raw_rows)
    write_rgb_list(sequence_dir / "sequence/masked/rgb.txt", masked_rows)
    write_rgb_list(pack_dir / "raw/rgb.txt", pack_raw_rows)
    write_rgb_list(pack_dir / "masked/rgb.txt", pack_masked_rows)
    copy_sidecars(source_dir, sequence_dir / "sequence", pack_dir, args.frame_limit)

    h, w = raw_shape if raw_shape else (0, 0)
    total_area = len(frames) * h * w
    mask_pixels = sum(int(frame["mask_pixels"]) for frame in frames)
    alpha_pixels = sum(int(frame["nonzero_alpha_pixels"]) for frame in frames)
    manifest = {
        "artifact": "P235 soft boundary mask frontend pack",
        "created": now(),
        "status": "backend_input_pack_ready",
        "claim_boundary": "Bounded frontend smoke only; no full benchmark, navigation, independent-label, learned-admission, or manuscript-body claim. P195 remains BLOCKED.",
        "window_id": window["id"],
        "sequence_label": window["sequence_label"],
        "source_indices": [window["start_index"], window["end_index"]],
        "source_dir": rel(source_dir),
        "sequence_output": rel(sequence_dir),
        "output_dir": rel(pack_dir),
        "frame_count": len(frames),
        "raw_rgb_list": rel(pack_dir / "raw/rgb.txt"),
        "masked_rgb_list": rel(pack_dir / "masked/rgb.txt"),
        "groundtruth_tum": rel(pack_dir / "groundtruth.txt"),
        "dynamic_mask_policy": "P235 soft/boundary-aware frontend attenuation over P225 probability maps; no hard black mask boundary by default.",
        "module_parameters": variant.__dict__,
        "mask_summary": {
            "total_mask_pixels": int(mask_pixels),
            "mean_coverage_percent": round((mask_pixels / max(total_area, 1)) * 100.0, 6),
            "coverage_capped_frames": [frame["frame_index"] for frame in frames if frame["coverage_capped"]],
            "nonzero_mask_frames": sum(1 for frame in frames if frame["mask_pixels"] > 0),
            "total_soft_alpha_pixels": int(alpha_pixels),
            "mean_soft_alpha_percent": round((sum(float(frame["mean_soft_alpha"]) for frame in frames) / max(len(frames), 1)) * 100.0, 6),
        },
        "frames": frames,
    }
    for output in (pack_dir / "backend_input_manifest.json", sequence_dir / "backend_input_manifest.json"):
        write_json(output, manifest)
    return manifest


def count_keypoints(image_path: Path, mask_path: Path | None, orb: cv2.ORB) -> tuple[int, int, int]:
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(image_path)
    keypoints = orb.detect(image, None)
    total = len(keypoints)
    if mask_path is None or not mask_path.exists():
        return total, 0, 0
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        raise FileNotFoundError(mask_path)
    region_pixels = int(np.count_nonzero(mask > 0))
    in_region = 0
    for kp in keypoints:
        x = min(max(int(round(kp.pt[0])), 0), mask.shape[1] - 1)
        y = min(max(int(round(kp.pt[1])), 0), mask.shape[0] - 1)
        if mask[y, x] > 0:
            in_region += 1
    return total, in_region, region_pixels


def orb_sanity(input_dir: Path, frame_limit: int | None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    raw_rows = p228.read_backend_rgb_list(input_dir / "raw/rgb.txt", frame_limit)
    masked_rows = p228.read_backend_rgb_list(input_dir / "masked/rgb.txt", frame_limit)
    orb = cv2.ORB_create(nfeatures=1000)
    frame_rows: list[dict[str, Any]] = []
    totals = {
        "frames": 0,
        "raw_total_keypoints": 0,
        "masked_total_keypoints": 0,
        "raw_predicted_mask_region_keypoints": 0,
        "masked_predicted_mask_region_keypoints": 0,
        "predicted_mask_region_pixels": 0,
    }
    for index, ((timestamp, raw_path), (_, masked_path)) in enumerate(zip(raw_rows, masked_rows)):
        mask_path = input_dir / "predicted_masks" / f"{index:06d}_p235_soft_boundary_mask.png"
        raw_total, raw_region, region_pixels = count_keypoints(raw_path, mask_path, orb)
        masked_total, masked_region, _ = count_keypoints(masked_path, mask_path, orb)
        row = {
            "frame_index": index,
            "timestamp": timestamp,
            "raw_total_keypoints": raw_total,
            "masked_total_keypoints": masked_total,
            "raw_predicted_mask_region_keypoints": raw_region,
            "masked_predicted_mask_region_keypoints": masked_region,
            "predicted_mask_region_pixels": region_pixels,
            "predicted_mask_region_keypoint_delta_masked_minus_raw": masked_region - raw_region,
            "total_keypoint_delta_masked_minus_raw": masked_total - raw_total,
        }
        frame_rows.append(row)
        totals["frames"] += 1
        for key in totals:
            if key != "frames":
                totals[key] += int(row[key])
    totals["predicted_mask_region_proxy"] = True
    totals["raw_to_masked_total_keypoint_delta"] = totals["masked_total_keypoints"] - totals["raw_total_keypoints"]
    totals["raw_to_masked_predicted_region_keypoint_delta"] = (
        totals["masked_predicted_mask_region_keypoints"] - totals["raw_predicted_mask_region_keypoints"]
    )
    totals["total_keypoints_stable"] = abs(totals["raw_to_masked_total_keypoint_delta"]) <= max(60, int(0.02 * max(totals["raw_total_keypoints"], 1)))
    return totals, frame_rows


def write_orb_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    p228.write_orb_csv(path, rows)


def run_command(command: list[str], timeout_seconds: int) -> dict[str, Any]:
    start = time.time()
    try:
        completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=timeout_seconds, check=False)
        return {
            "command": " ".join(command),
            "returncode": completed.returncode,
            "duration_seconds": round(time.time() - start, 3),
            "stdout_tail": completed.stdout[-4000:],
            "stderr_tail": completed.stderr[-4000:],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": " ".join(command),
            "returncode": None,
            "duration_seconds": round(time.time() - start, 3),
            "stdout_tail": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "",
            "timed_out": True,
        }


def compact_metrics(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = read_json(path)
    metrics = payload.get("metrics", {})
    masked_key = next((key for key in metrics if key != "raw RGB"), None)
    if not masked_key:
        return None
    return {
        "metrics_json": rel(path),
        "raw": metrics["raw RGB"],
        "masked": metrics[masked_key],
        "delta_masked_minus_raw": payload.get("delta_masked_minus_raw", {}),
    }


def trajectory_neutral(metrics: dict[str, Any] | None, tolerance_m: float) -> bool:
    if not metrics:
        return False
    return (
        metrics["masked"]["ape_rmse_m"] <= metrics["raw"]["ape_rmse_m"] + tolerance_m
        and metrics["masked"]["rpe_rmse_m"] <= metrics["raw"]["rpe_rmse_m"] + tolerance_m
    )


def run_droid_gate(args: argparse.Namespace, result: dict[str, Any], frame_limit: int) -> dict[str, Any]:
    output_dir = args.output_root / result["window_id"] / result["variant_id"] / f"dynamic_slam_backend_smoke_p235_{frame_limit}"
    prefix = f"p235_{result['window_id']}_{result['variant_id']}_{frame_limit}f_metrics"
    smoke_cmd = [
        sys.executable,
        "tools/run_dynamic_slam_backend_smoke.py",
        "--input-dir",
        result["pack_dir"],
        "--output-dir",
        rel(output_dir),
        "--frame-limit",
        str(frame_limit),
    ]
    smoke_result = run_command(smoke_cmd, args.droid_timeout_seconds)
    manifest_path = output_dir / "dynamic_slam_backend_smoke_manifest.json"
    manifest = read_json(manifest_path) if manifest_path.exists() else {}
    runs_ok = manifest.get("status") == "ok" and all(run.get("status") == "ok" for run in manifest.get("runs", []))
    metrics_result: dict[str, Any] | None = None
    metrics = None
    if smoke_result["returncode"] == 0 and runs_ok:
        metrics_cmd = [
            sys.executable,
            "tools/evaluate_dynamic_slam_metrics.py",
            "--input-dir",
            result["pack_dir"],
            "--output-dir",
            rel(output_dir),
            "--artifact",
            f"P235 {frame_limit}-frame soft-boundary mask metrics ({result['window_id']} {result['variant_id']})",
            "--scope",
            f"P235 bounded frontend smoke: {frame_limit} frames from {result['window_id']}.",
            "--masked-label",
            f"masked RGB (P235 {result['variant_id']} soft-boundary frontend)",
            "--output-prefix",
            prefix,
            "--interpretation",
            "P235 bounded soft-boundary frontend smoke; no full benchmark or navigation claim.",
        ]
        metrics_result = run_command(metrics_cmd, 180)
        if metrics_result["returncode"] == 0:
            metrics = compact_metrics(output_dir / f"{prefix}.json")
    return {
        "frame_limit": frame_limit,
        "output_dir": rel(output_dir),
        "smoke_command": smoke_result,
        "smoke_manifest": rel(manifest_path) if manifest_path.exists() else None,
        "smoke_status": manifest.get("status", "missing_manifest"),
        "runs": manifest.get("runs", []),
        "metrics_command": metrics_result,
        "metrics": metrics,
        "trajectory_neutral": trajectory_neutral(metrics, args.neutral_tolerance_m),
    }


def evaluate_variant(args: argparse.Namespace, window: dict[str, Any], variant: SoftVariant) -> dict[str, Any]:
    with contextlib.redirect_stdout(io.StringIO()):
        manifest = build_variant_pack(args, window, variant)
    pack_dir = Path(manifest["output_dir"])
    orb_summary, orb_rows = orb_sanity(pack_dir, None)
    orb_csv = args.output_root / window["id"] / variant.variant_id / f"{window['id']}_{variant.variant_id}_orb_features.csv"
    write_orb_csv(orb_csv, orb_rows)
    delta = orb_summary["raw_to_masked_predicted_region_keypoint_delta"]
    raw_region = max(orb_summary["raw_predicted_mask_region_keypoints"], 1)
    not_significant_reverse = delta <= max(30, int(round(raw_region * args.orb_reverse_tolerance_fraction)))
    result = {
        "window_id": window["id"],
        "sequence_label": window["sequence_label"],
        "start_index": window["start_index"],
        "end_index": window["end_index"],
        "window_priority": window["priority"],
        "variant_id": variant.variant_id,
        "method": variant.method,
        "parameters": variant.__dict__,
        "pack_dir": manifest["output_dir"],
        "manifest": rel(pack_dir / "backend_input_manifest.json"),
        "mask_summary": manifest["mask_summary"],
        "orb_feature_sanity": orb_summary | {"orb_feature_csv": rel(orb_csv)},
        "orb_proxy_down": delta < 0,
        "orb_proxy_not_significant_reverse": not_significant_reverse,
        "droid_gates": [],
    }
    return result


def write_csv(path: Path, payload: dict[str, Any]) -> None:
    rows = []
    for result in payload["evaluations"]:
        orb = result["orb_feature_sanity"]
        gate16 = next((gate for gate in result["droid_gates"] if gate["frame_limit"] == 16), {})
        gate60 = next((gate for gate in result["droid_gates"] if gate["frame_limit"] == 60), {})
        rows.append(
            {
                "window_id": result["window_id"],
                "variant_id": result["variant_id"],
                "method": result["method"],
                "status": result["status"],
                "mean_coverage_percent": result["mask_summary"]["mean_coverage_percent"],
                "mean_soft_alpha_percent": result["mask_summary"]["mean_soft_alpha_percent"],
                "raw_total_keypoints": orb["raw_total_keypoints"],
                "masked_total_keypoints": orb["masked_total_keypoints"],
                "total_keypoint_delta": orb["raw_to_masked_total_keypoint_delta"],
                "raw_region_keypoints": orb["raw_predicted_mask_region_keypoints"],
                "masked_region_keypoints": orb["masked_predicted_mask_region_keypoints"],
                "region_keypoint_delta": orb["raw_to_masked_predicted_region_keypoint_delta"],
                "droid_16f_neutral": gate16.get("trajectory_neutral"),
                "droid_16f_delta_ape": (gate16.get("metrics") or {}).get("delta_masked_minus_raw", {}).get("ape_rmse_m"),
                "droid_16f_delta_rpe": (gate16.get("metrics") or {}).get("delta_masked_minus_raw", {}).get("rpe_rmse_m"),
                "droid_60f_neutral": gate60.get("trajectory_neutral"),
                "droid_60f_delta_ape": (gate60.get("metrics") or {}).get("delta_masked_minus_raw", {}).get("ape_rmse_m"),
                "droid_60f_delta_rpe": (gate60.get("metrics") or {}).get("delta_masked_minus_raw", {}).get("rpe_rmse_m"),
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# P235 Soft Boundary Mask Frontend",
        "",
        f"Status: `{payload['status']}`",
        "",
        f"Claim boundary: {payload['claim_boundary']}",
        "",
        "## Scope",
        "",
        "- First regression window: `aisle_cw_0840_0899`.",
        "- Backtest windows: `aisle_cw_0480_0539` and `aisle_cw_0120_0179` for the selected variant.",
        "- No manuscript-body edits; evidence is export-only.",
        "",
        "## Metrics",
        "",
        "| Window | Variant | Method | Coverage | Soft alpha | Region kp raw->soft | Delta | Total delta | DROID 16f | DROID 60f | Status |",
        "|---|---|---|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for result in payload["evaluations"]:
        orb = result["orb_feature_sanity"]
        gate16 = next((gate for gate in result["droid_gates"] if gate["frame_limit"] == 16), None)
        gate60 = next((gate for gate in result["droid_gates"] if gate["frame_limit"] == 60), None)
        d16 = "not_run" if not gate16 else f"neutral={gate16['trajectory_neutral']}"
        d60 = "not_run" if not gate60 else f"neutral={gate60['trajectory_neutral']}"
        lines.append(
            f"| `{result['window_id']}` | `{result['variant_id']}` | {result['method']} | "
            f"{result['mask_summary']['mean_coverage_percent']:.6f}% | {result['mask_summary']['mean_soft_alpha_percent']:.6f}% | "
            f"{orb['raw_predicted_mask_region_keypoints']}->{orb['masked_predicted_mask_region_keypoints']} | "
            f"{orb['raw_to_masked_predicted_region_keypoint_delta']} | {orb['raw_to_masked_total_keypoint_delta']} | "
            f"{d16} | {d60} | `{result['status']}` |"
        )
    lines += [
        "",
        "## Decision",
        "",
        payload["decision"],
        "",
        "## Next Plan",
        "",
    ]
    for item in payload["next_plan"]:
        lines.append(f"- {item}")
    lines += [
        "",
        "## Files",
        "",
        f"- JSON: `{payload['outputs']['json']}`",
        f"- CSV: `{payload['outputs']['csv']}`",
        f"- Markdown: `{payload['outputs']['markdown']}`",
        f"- Output root: `{payload['outputs']['output_root']}`",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--neutral-tolerance-m", type=float, default=0.001)
    parser.add_argument("--orb-reverse-tolerance-fraction", type=float, default=0.05)
    parser.add_argument("--droid-timeout-seconds", type=int, default=300)
    parser.add_argument("--frame-limit", type=int, default=None)
    parser.add_argument("--skip-droid", action="store_true")
    args = parser.parse_args()

    for required in (P233_JSON, P234_JSON):
        if not required.exists():
            raise FileNotFoundError(required)
    for window in WINDOWS.values():
        if not window["source_dir"].exists():
            raise FileNotFoundError(window["source_dir"])

    command_line = " ".join([sys.executable, "tools/apply_soft_boundary_mask_p235.py", *sys.argv[1:]])
    failure_results = [evaluate_variant(args, WINDOWS["aisle_cw_0840_0899"], variant) for variant in variants()]
    selected = sorted(
        failure_results,
        key=lambda r: (
            r["orb_feature_sanity"]["raw_to_masked_predicted_region_keypoint_delta"],
            abs(r["orb_feature_sanity"]["raw_to_masked_total_keypoint_delta"]),
        ),
    )[0]

    if not args.skip_droid and (selected["orb_proxy_down"] or selected["orb_proxy_not_significant_reverse"]):
        selected["droid_gates"].append(run_droid_gate(args, selected, 16))
        gate16 = selected["droid_gates"][-1]
        if gate16["trajectory_neutral"]:
            selected["droid_gates"].append(run_droid_gate(args, selected, 60))

    best_variant = next(v for v in variants() if v.variant_id == selected["variant_id"])
    backtests = [evaluate_variant(args, WINDOWS["aisle_cw_0480_0539"], best_variant), evaluate_variant(args, WINDOWS["aisle_cw_0120_0179"], best_variant)]
    if not args.skip_droid and selected["droid_gates"] and selected["droid_gates"][0]["trajectory_neutral"]:
        for result in backtests:
            if result["orb_proxy_down"] or result["orb_proxy_not_significant_reverse"]:
                result["droid_gates"].append(run_droid_gate(args, result, 16))

    all_results = failure_results + backtests
    for result in all_results:
        gate60 = next((gate for gate in result["droid_gates"] if gate["frame_limit"] == 60), None)
        gate16 = next((gate for gate in result["droid_gates"] if gate["frame_limit"] == 16), None)
        if result["window_id"] == "aisle_cw_0840_0899" and result["variant_id"] == selected["variant_id"]:
            if (result["orb_proxy_down"] or result["orb_proxy_not_significant_reverse"]) and result["orb_feature_sanity"]["total_keypoints_stable"] and (gate60 or gate16) and (gate60 or gate16)["trajectory_neutral"]:
                result["status"] = "candidate_soft_boundary_v1"
            else:
                result["status"] = "soft_mask_not_sufficient"
        else:
            result["status"] = "backtest_orb_proxy_down" if result["orb_proxy_down"] else "backtest_orb_proxy_not_down"

    candidate = selected["status"] == "candidate_soft_boundary_v1"
    status = "candidate_soft_boundary_v1" if candidate else "soft_mask_not_sufficient"
    if candidate:
        decision = (
            f"`{selected['variant_id']}` avoids the strong 840-899 ORB proxy reversal and is DROID-neutral in the bounded gate. "
            "Treat it only as a candidate frontend smoke module pending more windows and independent labels."
        )
        next_plan = [
            "Keep the soft-boundary candidate as a bounded frontend v1, not a paper-level benchmark claim.",
            "Add temporal/motion consistency before expanding beyond these three short windows.",
            "Retain P195 BLOCKED until independent human labels are available.",
        ]
    else:
        decision = (
            "Soft attenuation/feathering reduced the hard-boundary artifact but did not satisfy both the 840-899 ORB and DROID gate. "
            "Treat soft masks alone as insufficient."
        )
        next_plan = [
            "Move toward temporal or motion-aware network input rather than further post-processing-only mask styling.",
            "Use the 840-899 window as the first regression gate for any next frontend module.",
            "Do not expand claims beyond bounded frontend smoke evidence.",
        ]

    payload = {
        "artifact": "P235 soft boundary mask frontend",
        "created": now(),
        "status": status,
        "claim_boundary": "Bounded frontend smoke/story-seed evidence only; no full benchmark, navigation, independent-label, learned map-admission, or manuscript-body claim. P195 remains BLOCKED.",
        "inputs_checked": {
            "p228_tool": "tools/apply_confidence_gated_mask_module_p228.py",
            "p233_tool": "tools/run_gated_mask_multi_window_p233.py",
            "p234_tool": "tools/sweep_gated_mask_failure_p234.py",
            "p233_json": rel(P233_JSON),
            "p234_json": rel(P234_JSON),
            "p233_output_root": "outputs/gated_mask_multi_window_p233",
        },
        "selected_variant": selected["variant_id"],
        "evaluations": all_results,
        "decision": decision,
        "next_plan": next_plan,
        "commands": [command_line],
        "outputs": {
            "json": rel(EVIDENCE_JSON),
            "csv": rel(EVIDENCE_CSV),
            "markdown": rel(EXPORT_MD),
            "output_root": rel(args.output_root),
        },
    }
    write_json(EVIDENCE_JSON, payload)
    write_csv(EVIDENCE_CSV, payload)
    write_markdown(EXPORT_MD, payload)
    print(json.dumps({"status": status, "selected_variant": selected["variant_id"], "json": rel(EVIDENCE_JSON)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
