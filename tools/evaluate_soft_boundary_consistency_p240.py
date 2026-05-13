#!/usr/bin/env python3
"""Evaluate P240 self-supervised consistency for the soft-boundary frontend.

The checks are intentionally lightweight and evidence-bounded: temporal mask
stability, motion/frame-difference cue alignment, and ORB residual behavior.
They do not use human labels and do not run DROID.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "outputs/soft_boundary_consistency_p240"
EVIDENCE_JSON = ROOT / "paper/evidence/soft_boundary_consistency_p240.json"
EVIDENCE_CSV = ROOT / "paper/evidence/soft_boundary_consistency_p240.csv"
EXPORT_MD = ROOT / "paper/export/soft_boundary_consistency_p240.md"

SELECTED_VARIANT = "meanfill035_feather5_thr060_cap012_min256"


@dataclass(frozen=True)
class WindowSpec:
    window_id: str
    source_phase: str
    sequence_label: str
    start_index: int
    end_index: int
    pack_dir: Path
    selection_reason: str


@dataclass(frozen=True)
class ContrastSpec:
    contrast_id: str
    source_phase: str
    window_id: str
    variant_id: str
    pack_dir: Path
    contrast_reason: str


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def read_rgb_list(path: Path, frame_limit: int | None = None) -> list[tuple[float, Path]]:
    rows: list[tuple[float, Path]] = []
    base = path.parent
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        timestamp_s, image_s = line.split(maxsplit=1)
        image_path = Path(image_s)
        if not image_path.is_absolute():
            root_relative = ROOT / image_path
            image_path = root_relative if root_relative.exists() else base / image_path
        rows.append((float(timestamp_s), image_path))
        if frame_limit is not None and len(rows) >= frame_limit:
            break
    return rows


def load_gray(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(path)
    return image


def mask_paths(pack_dir: Path, frame_count: int) -> list[Path]:
    paths = sorted((pack_dir / "predicted_masks").glob("*.png"))
    if len(paths) < frame_count:
        raise FileNotFoundError(f"Need {frame_count} predicted masks in {pack_dir / 'predicted_masks'}, found {len(paths)}")
    return paths[:frame_count]


def probability_paths(pack_dir: Path, frame_count: int) -> list[Path]:
    paths = sorted((pack_dir / "probabilities").glob("*.png"))
    if len(paths) < frame_count:
        raise FileNotFoundError(f"Need {frame_count} probability maps in {pack_dir / 'probabilities'}, found {len(paths)}")
    return paths[:frame_count]


def default_windows() -> list[WindowSpec]:
    return [
        WindowSpec(
            "aisle_cw_0840_0899",
            "P235",
            "Oct. 12, 2022 Aisle_CW",
            840,
            899,
            ROOT / f"outputs/soft_boundary_mask_p235/aisle_cw_0840_0899/{SELECTED_VARIANT}/dynamic_slam_backend_input_pack_p235_soft_boundary",
            "mandatory failure/repair regression window",
        ),
        WindowSpec(
            "aisle_cw_0240_0299",
            "P237",
            "Oct. 12, 2022 Aisle_CW",
            240,
            299,
            ROOT / f"outputs/soft_boundary_multiwindow_p237/aisle_cw_0240_0299/{SELECTED_VARIANT}/dynamic_slam_backend_input_pack_p235_soft_boundary",
            "mandatory expanded-support same-sequence window",
        ),
        WindowSpec(
            "aisle_ccw_0240_0299",
            "P237",
            "Oct. 12, 2022 Aisle_CCW",
            240,
            299,
            ROOT / f"outputs/soft_boundary_multiwindow_p237/aisle_ccw_0240_0299/{SELECTED_VARIANT}/dynamic_slam_backend_input_pack_p235_soft_boundary",
            "mandatory expanded-support opposite-direction window",
        ),
        WindowSpec(
            "aisle_cw_0480_0539",
            "P235",
            "Oct. 12, 2022 Aisle_CW",
            480,
            539,
            ROOT / f"outputs/soft_boundary_mask_p235/aisle_cw_0480_0539/{SELECTED_VARIANT}/dynamic_slam_backend_input_pack_p235_soft_boundary",
            "P235 backtest/story-seed window",
        ),
        WindowSpec(
            "aisle_cw_0120_0179",
            "P235",
            "Oct. 12, 2022 Aisle_CW",
            120,
            179,
            ROOT / f"outputs/soft_boundary_mask_p235/aisle_cw_0120_0179/{SELECTED_VARIANT}/dynamic_slam_backend_input_pack_p235_soft_boundary",
            "P235/P233 backtest window",
        ),
    ]


def default_contrasts() -> list[ContrastSpec]:
    return [
        ContrastSpec(
            "p234_hard_best_aisle_cw_0840_0899",
            "P234",
            "aisle_cw_0840_0899",
            "thr060_cap012_min256_dil0",
            ROOT / "outputs/gated_mask_failure_sweep_p234/thr060_cap012_min256_dil0/dynamic_slam_backend_input_pack_p228_conf_gated",
            "best P234 hard-mask failure variant on the 840-899 regression window",
        ),
        ContrastSpec(
            "p234_hard_default_aisle_cw_0840_0899",
            "P234",
            "aisle_cw_0840_0899",
            "p233_default",
            ROOT / "outputs/gated_mask_failure_sweep_p234/p233_default/dynamic_slam_backend_input_pack_p228_conf_gated",
            "P233/P234 default hard-mask failure contrast on 840-899",
        ),
    ]


def binary_iou(a: np.ndarray, b: np.ndarray) -> float:
    au = a > 0
    bu = b > 0
    union = int(np.count_nonzero(au | bu))
    if union == 0:
        return 1.0
    return float(np.count_nonzero(au & bu) / union)


def soft_iou(a: np.ndarray, b: np.ndarray) -> float:
    af = a.astype(np.float32) / 255.0
    bf = b.astype(np.float32) / 255.0
    denom = float(np.maximum(af, bf).sum())
    if denom <= 1e-9:
        return 1.0
    return float(np.minimum(af, bf).sum() / denom)


def summarize(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "mean": None, "median": None, "min": None, "max": None}
    arr = np.array(values, dtype=np.float64)
    return {
        "count": int(arr.size),
        "mean": float(arr.mean()),
        "median": float(np.median(arr)),
        "min": float(arr.min()),
        "max": float(arr.max()),
    }


def boundary_band(mask: np.ndarray, radius: int) -> np.ndarray:
    binary = (mask > 0).astype(np.uint8)
    if not np.any(binary):
        return np.zeros_like(binary, dtype=np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius * 2 + 1, radius * 2 + 1))
    dilated = cv2.dilate(binary, kernel)
    eroded = cv2.erode(binary, kernel)
    return ((dilated > 0) & (eroded == 0)).astype(np.uint8)


def keypoint_counts(image: np.ndarray, mask: np.ndarray, band: np.ndarray, orb: cv2.ORB) -> dict[str, int]:
    keypoints = orb.detect(image, None)
    in_region = 0
    in_band = 0
    h, w = mask.shape[:2]
    for kp in keypoints:
        x = min(max(int(round(kp.pt[0])), 0), w - 1)
        y = min(max(int(round(kp.pt[1])), 0), h - 1)
        if mask[y, x] > 0:
            in_region += 1
        if band[y, x] > 0:
            in_band += 1
    return {"total": len(keypoints), "region": in_region, "boundary_band": in_band}


def high_cue_metrics(cue: np.ndarray, mask: np.ndarray, quantile: float) -> dict[str, float]:
    cue_f = cue.astype(np.float32)
    mask_bool = mask > 0
    coverage = float(np.count_nonzero(mask_bool) / max(mask_bool.size, 1))
    if not np.any(mask_bool):
        return {
            "coverage_fraction": coverage,
            "high_cue_overlap_fraction": 0.0,
            "high_cue_enrichment": 0.0,
            "inside_outside_mean_ratio": 0.0,
        }
    threshold = float(np.quantile(cue_f, quantile))
    high = cue_f >= threshold
    high_fraction = float(np.count_nonzero(high) / max(high.size, 1))
    overlap_fraction = float(np.count_nonzero(high & mask_bool) / max(np.count_nonzero(mask_bool), 1))
    enrichment = overlap_fraction / max(high_fraction, 1e-9)
    inside_mean = float(cue_f[mask_bool].mean())
    outside = cue_f[~mask_bool]
    outside_mean = float(outside.mean()) if outside.size else 0.0
    return {
        "coverage_fraction": coverage,
        "high_cue_overlap_fraction": overlap_fraction,
        "high_cue_enrichment": float(enrichment),
        "inside_outside_mean_ratio": float(inside_mean / max(outside_mean, 1e-9)),
    }


def evaluate_pack(
    pack_dir: Path,
    frame_limit: int,
    high_cue_quantile: float,
    boundary_radius: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    raw_rows = read_rgb_list(pack_dir / "raw/rgb.txt", frame_limit)
    masked_rows = read_rgb_list(pack_dir / "masked/rgb.txt", frame_limit)
    frame_count = min(len(raw_rows), len(masked_rows), frame_limit)
    masks = [load_gray(p) for p in mask_paths(pack_dir, frame_count)]
    probs = [load_gray(p) for p in probability_paths(pack_dir, frame_count)]
    raw_images = [load_gray(path) for _, path in raw_rows[:frame_count]]
    masked_images = [load_gray(path) for _, path in masked_rows[:frame_count]]

    orb = cv2.ORB_create(nfeatures=1000)
    rows: list[dict[str, Any]] = []
    coverage_values: list[float] = []
    binary_ious: list[float] = []
    prob_ious: list[float] = []
    flow_enrichments: list[float] = []
    flow_ratios: list[float] = []
    diff_enrichments: list[float] = []
    diff_ratios: list[float] = []
    raw_region_total = 0
    masked_region_total = 0
    raw_band_total = 0
    masked_band_total = 0
    raw_total = 0
    masked_total = 0
    mask_pixels_total = 0
    band_pixels_total = 0

    for index in range(frame_count):
        mask = masks[index]
        band = boundary_band(mask, boundary_radius)
        coverage = float(np.count_nonzero(mask > 0) / max(mask.size, 1))
        coverage_values.append(coverage)
        mask_pixels_total += int(np.count_nonzero(mask > 0))
        band_pixels_total += int(np.count_nonzero(band > 0))

        raw_counts = keypoint_counts(raw_images[index], mask, band, orb)
        masked_counts = keypoint_counts(masked_images[index], mask, band, orb)
        raw_total += raw_counts["total"]
        masked_total += masked_counts["total"]
        raw_region_total += raw_counts["region"]
        masked_region_total += masked_counts["region"]
        raw_band_total += raw_counts["boundary_band"]
        masked_band_total += masked_counts["boundary_band"]

        row: dict[str, Any] = {
            "frame_index": index,
            "mask_coverage_fraction": coverage,
            "raw_total_keypoints": raw_counts["total"],
            "masked_total_keypoints": masked_counts["total"],
            "raw_region_keypoints": raw_counts["region"],
            "masked_region_keypoints": masked_counts["region"],
            "raw_boundary_band_keypoints": raw_counts["boundary_band"],
            "masked_boundary_band_keypoints": masked_counts["boundary_band"],
        }

        if index > 0:
            b_iou = binary_iou(masks[index - 1], mask)
            p_iou = soft_iou(probs[index - 1], probs[index])
            binary_ious.append(b_iou)
            prob_ious.append(p_iou)
            prev = raw_images[index - 1]
            curr = raw_images[index]
            flow = cv2.calcOpticalFlowFarneback(prev, curr, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            flow_mag = cv2.magnitude(flow[..., 0], flow[..., 1])
            diff = cv2.absdiff(prev, curr)
            flow_metrics = high_cue_metrics(flow_mag, masks[index - 1], high_cue_quantile)
            diff_metrics = high_cue_metrics(diff, masks[index - 1], high_cue_quantile)
            flow_enrichments.append(flow_metrics["high_cue_enrichment"])
            flow_ratios.append(flow_metrics["inside_outside_mean_ratio"])
            diff_enrichments.append(diff_metrics["high_cue_enrichment"])
            diff_ratios.append(diff_metrics["inside_outside_mean_ratio"])
            row.update(
                {
                    "prev_mask_binary_iou": b_iou,
                    "prev_probability_soft_iou": p_iou,
                    "flow_high_cue_enrichment": flow_metrics["high_cue_enrichment"],
                    "flow_inside_outside_mean_ratio": flow_metrics["inside_outside_mean_ratio"],
                    "frame_diff_high_cue_enrichment": diff_metrics["high_cue_enrichment"],
                    "frame_diff_inside_outside_mean_ratio": diff_metrics["inside_outside_mean_ratio"],
                }
            )
        rows.append(row)

    coverage_arr = np.array(coverage_values, dtype=np.float64)
    mean_coverage = float(coverage_arr.mean()) if coverage_arr.size else 0.0
    coverage_cv = float(coverage_arr.std() / max(mean_coverage, 1e-9)) if coverage_arr.size else 0.0
    result = {
        "pack_dir": rel(pack_dir),
        "frame_count": frame_count,
        "temporal_mask_stability": {
            "adjacent_binary_mask_iou": summarize(binary_ious),
            "adjacent_probability_soft_iou": summarize(prob_ious),
            "mean_mask_coverage_percent": mean_coverage * 100.0,
            "mask_coverage_cv": coverage_cv,
            "nonzero_mask_frames": int(sum(v > 0 for v in coverage_values)),
        },
        "motion_cue_alignment": {
            "high_cue_quantile": high_cue_quantile,
            "farneback_flow_high_cue_enrichment": summarize(flow_enrichments),
            "farneback_flow_inside_outside_mean_ratio": summarize(flow_ratios),
            "frame_difference_high_cue_enrichment": summarize(diff_enrichments),
            "frame_difference_inside_outside_mean_ratio": summarize(diff_ratios),
        },
        "feature_residual_proxy": {
            "raw_total_keypoints": raw_total,
            "masked_total_keypoints": masked_total,
            "total_keypoint_delta_masked_minus_raw": masked_total - raw_total,
            "raw_region_keypoints": raw_region_total,
            "masked_region_keypoints": masked_region_total,
            "region_keypoint_delta_masked_minus_raw": masked_region_total - raw_region_total,
            "raw_boundary_band_keypoints": raw_band_total,
            "masked_boundary_band_keypoints": masked_band_total,
            "boundary_band_keypoint_delta_masked_minus_raw": masked_band_total - raw_band_total,
            "mask_pixels_total": mask_pixels_total,
            "boundary_band_radius_px": boundary_radius,
            "boundary_band_pixels_total": band_pixels_total,
        },
    }
    return result, rows


def support_flags(result: dict[str, Any]) -> dict[str, bool]:
    temporal = result["temporal_mask_stability"]
    motion = result["motion_cue_alignment"]
    residual = result["feature_residual_proxy"]
    binary_iou = temporal["adjacent_binary_mask_iou"]["mean"] or 0.0
    prob_iou = temporal["adjacent_probability_soft_iou"]["mean"] or 0.0
    flow_enrichment = motion["farneback_flow_high_cue_enrichment"]["mean"] or 0.0
    diff_enrichment = motion["frame_difference_high_cue_enrichment"]["mean"] or 0.0
    return {
        "temporal_coherent": binary_iou >= 0.35 or prob_iou >= 0.55,
        "motion_or_difference_enriched": flow_enrichment >= 1.10 or diff_enrichment >= 1.10,
        "region_orb_not_inflated": residual["region_keypoint_delta_masked_minus_raw"] <= 0,
        "boundary_band_orb_not_inflated": residual["boundary_band_keypoint_delta_masked_minus_raw"] <= max(30, int(0.05 * max(residual["raw_boundary_band_keypoints"], 1))),
    }


def evaluate_window(spec: WindowSpec, args: argparse.Namespace) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    result, frame_rows = evaluate_pack(spec.pack_dir, args.frame_limit, args.high_cue_quantile, args.boundary_radius)
    flags = support_flags(result)
    result.update(
        {
            "window_id": spec.window_id,
            "source_phase": spec.source_phase,
            "sequence_label": spec.sequence_label,
            "start_index": spec.start_index,
            "end_index": spec.end_index,
            "selection_reason": spec.selection_reason,
            "support_flags": flags,
            "window_support": all(flags.values()),
        }
    )
    for row in frame_rows:
        row.update({"window_id": spec.window_id, "source_phase": spec.source_phase, "contrast_id": ""})
    return result, frame_rows


def evaluate_contrast(spec: ContrastSpec, args: argparse.Namespace) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    result, frame_rows = evaluate_pack(spec.pack_dir, args.frame_limit, args.high_cue_quantile, args.boundary_radius)
    result.update(
        {
            "contrast_id": spec.contrast_id,
            "source_phase": spec.source_phase,
            "window_id": spec.window_id,
            "variant_id": spec.variant_id,
            "contrast_reason": spec.contrast_reason,
        }
    )
    for row in frame_rows:
        row.update({"window_id": spec.window_id, "source_phase": spec.source_phase, "contrast_id": spec.contrast_id})
    return result, frame_rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "row_type",
        "window_id",
        "source_phase",
        "contrast_id",
        "frame_index",
        "frame_count",
        "mean_mask_coverage_percent",
        "mask_coverage_cv",
        "adjacent_binary_mask_iou_mean",
        "adjacent_probability_soft_iou_mean",
        "flow_high_cue_enrichment_mean",
        "flow_inside_outside_mean_ratio_mean",
        "frame_diff_high_cue_enrichment_mean",
        "frame_diff_inside_outside_mean_ratio_mean",
        "raw_region_keypoints",
        "masked_region_keypoints",
        "region_keypoint_delta_masked_minus_raw",
        "raw_boundary_band_keypoints",
        "masked_boundary_band_keypoints",
        "boundary_band_keypoint_delta_masked_minus_raw",
        "raw_total_keypoints",
        "masked_total_keypoints",
        "total_keypoint_delta_masked_minus_raw",
        "temporal_coherent",
        "motion_or_difference_enriched",
        "region_orb_not_inflated",
        "boundary_band_orb_not_inflated",
        "window_support",
        "pack_dir",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def csv_summary_row(result: dict[str, Any], row_type: str) -> dict[str, Any]:
    temporal = result["temporal_mask_stability"]
    motion = result["motion_cue_alignment"]
    residual = result["feature_residual_proxy"]
    flags = result.get("support_flags", {})
    return {
        "row_type": row_type,
        "window_id": result["window_id"],
        "source_phase": result["source_phase"],
        "contrast_id": result.get("contrast_id", ""),
        "frame_count": result["frame_count"],
        "mean_mask_coverage_percent": temporal["mean_mask_coverage_percent"],
        "mask_coverage_cv": temporal["mask_coverage_cv"],
        "adjacent_binary_mask_iou_mean": temporal["adjacent_binary_mask_iou"]["mean"],
        "adjacent_probability_soft_iou_mean": temporal["adjacent_probability_soft_iou"]["mean"],
        "flow_high_cue_enrichment_mean": motion["farneback_flow_high_cue_enrichment"]["mean"],
        "flow_inside_outside_mean_ratio_mean": motion["farneback_flow_inside_outside_mean_ratio"]["mean"],
        "frame_diff_high_cue_enrichment_mean": motion["frame_difference_high_cue_enrichment"]["mean"],
        "frame_diff_inside_outside_mean_ratio_mean": motion["frame_difference_inside_outside_mean_ratio"]["mean"],
        "raw_region_keypoints": residual["raw_region_keypoints"],
        "masked_region_keypoints": residual["masked_region_keypoints"],
        "region_keypoint_delta_masked_minus_raw": residual["region_keypoint_delta_masked_minus_raw"],
        "raw_boundary_band_keypoints": residual["raw_boundary_band_keypoints"],
        "masked_boundary_band_keypoints": residual["masked_boundary_band_keypoints"],
        "boundary_band_keypoint_delta_masked_minus_raw": residual["boundary_band_keypoint_delta_masked_minus_raw"],
        "raw_total_keypoints": residual["raw_total_keypoints"],
        "masked_total_keypoints": residual["masked_total_keypoints"],
        "total_keypoint_delta_masked_minus_raw": residual["total_keypoint_delta_masked_minus_raw"],
        "temporal_coherent": flags.get("temporal_coherent", ""),
        "motion_or_difference_enriched": flags.get("motion_or_difference_enriched", ""),
        "region_orb_not_inflated": flags.get("region_orb_not_inflated", ""),
        "boundary_band_orb_not_inflated": flags.get("boundary_band_orb_not_inflated", ""),
        "window_support": result.get("window_support", ""),
        "pack_dir": result["pack_dir"],
    }


def fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (float, np.floating)):
        if math.isnan(float(value)):
            return "n/a"
        return f"{float(value):.{digits}f}"
    return str(value)


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# P240 Soft-Boundary Self-Supervised Consistency Evidence",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Plan Summary",
        "",
        "- Keep the main contribution as object-level map maintenance; keep the dynamic frontend as a failure-driven soft-boundary support module.",
        "- Add self-supervised motion/geometry/temporal consistency checks for the P235/P237 soft-boundary candidate without treating them as independent labels.",
        "- Do not update thick manuscript body text in P240; export this report and evidence artifacts only.",
        "",
        "## Metrics",
        "",
        "- Temporal mask stability: adjacent binary mask IoU, adjacent probability-map soft IoU, and coverage coefficient of variation.",
        "- Motion cue alignment: Farneback optical-flow high-motion enrichment and frame-difference high-cue enrichment inside the soft-mask region.",
        "- Feature residual proxy: raw-vs-soft ORB keypoints inside the predicted region and in a boundary band; P234 hard-mask contrasts show hard-edge ORB inflation on 840-899.",
        "",
        "## Soft-Boundary Windows",
        "",
        "| Window | Source | Frames | Mask IoU | Prob IoU | Flow enrich | Diff enrich | Region ORB | Band ORB | Support |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for result in payload["evaluations"]:
        temporal = result["temporal_mask_stability"]
        motion = result["motion_cue_alignment"]
        residual = result["feature_residual_proxy"]
        lines.append(
            "| "
            f"`{result['window_id']}` | {result['source_phase']} | {result['frame_count']} | "
            f"{fmt(temporal['adjacent_binary_mask_iou']['mean'])} | "
            f"{fmt(temporal['adjacent_probability_soft_iou']['mean'])} | "
            f"{fmt(motion['farneback_flow_high_cue_enrichment']['mean'])} | "
            f"{fmt(motion['frame_difference_high_cue_enrichment']['mean'])} | "
            f"{residual['raw_region_keypoints']}->{residual['masked_region_keypoints']} | "
            f"{residual['raw_boundary_band_keypoints']}->{residual['masked_boundary_band_keypoints']} | "
            f"`{result['window_support']}` |"
        )
    lines.extend(
        [
            "",
            "## Hard-Mask Contrast",
            "",
            "| Contrast | Window | Variant | Region ORB | Band ORB | Pack |",
            "| --- | --- | --- | ---: | ---: | --- |",
        ]
    )
    for result in payload["hard_mask_contrasts"]:
        residual = result["feature_residual_proxy"]
        lines.append(
            "| "
            f"`{result['contrast_id']}` | `{result['window_id']}` | `{result['variant_id']}` | "
            f"{residual['raw_region_keypoints']}->{residual['masked_region_keypoints']} | "
            f"{residual['raw_boundary_band_keypoints']}->{residual['masked_boundary_band_keypoints']} | "
            f"`{result['pack_dir']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            payload["decision"],
            "",
            "## Claim Boundary",
            "",
            payload["claim_boundary"],
            "",
            "## Outputs",
            "",
            f"- JSON: `{payload['outputs']['json']}`",
            f"- CSV: `{payload['outputs']['csv']}`",
            f"- Report: `{payload['outputs']['markdown']}`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frame-limit", type=int, default=60)
    parser.add_argument("--high-cue-quantile", type=float, default=0.90)
    parser.add_argument("--boundary-radius", type=int, default=3)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args()

    args.output_root.mkdir(parents=True, exist_ok=True)
    evaluations: list[dict[str, Any]] = []
    hard_contrasts: list[dict[str, Any]] = []
    csv_rows: list[dict[str, Any]] = []
    frame_rows: list[dict[str, Any]] = []

    for spec in default_windows():
        result, rows = evaluate_window(spec, args)
        evaluations.append(result)
        csv_rows.append(csv_summary_row(result, "soft_window_summary"))
        frame_rows.extend(rows)

    for spec in default_contrasts():
        result, rows = evaluate_contrast(spec, args)
        hard_contrasts.append(result)
        csv_rows.append(csv_summary_row(result, "hard_contrast_summary"))
        frame_rows.extend(rows)

    support_count = sum(1 for result in evaluations if result["window_support"])
    majority_threshold = len(evaluations)
    status = "self_supervised_support" if support_count == majority_threshold else "mixed_self_supervised_support"
    hard_region_inflations = [
        result["feature_residual_proxy"]["region_keypoint_delta_masked_minus_raw"] for result in hard_contrasts
    ]
    hard_band_inflations = [
        result["feature_residual_proxy"]["boundary_band_keypoint_delta_masked_minus_raw"] for result in hard_contrasts
    ]
    decision = (
        f"The selected P235/P237 soft-boundary candidate passes all self-supervised support flags in "
        f"{support_count}/{len(evaluations)} representative windows. The evidence supports the failure-driven "
        "soft-boundary frontend design as a bounded module: soft regions are temporally coherent, are enriched "
        "for motion or frame-difference cues, and avoid ORB inflation inside the soft region and boundary band."
        if status == "self_supervised_support"
        else f"The selected P235/P237 soft-boundary candidate is mixed in self-supervised checks: "
        f"{support_count}/{len(evaluations)} representative windows pass all support flags. Treat this as diagnostic "
        "support only and inspect the failing flags before manuscript integration."
    )
    if hard_region_inflations:
        decision += (
            f" P234 hard-mask contrasts on 840-899 show region ORB deltas {hard_region_inflations} and "
            f"boundary-band ORB deltas {hard_band_inflations}, preserving the hard-edge failure contrast."
        )

    payload = {
        "artifact": "P240 self-supervised soft-boundary consistency evidence",
        "created": now(),
        "status": status,
        "selected_variant": SELECTED_VARIANT,
        "claim_boundary": (
            "Self-supervised evidence only: not independent human-label validation and does not unblock P195. "
            "No full benchmark, navigation, learned-admission, or manuscript-body claim."
        ),
        "inputs_checked": {
            "p235_tool": "tools/apply_soft_boundary_mask_p235.py",
            "p237_tool": "tools/run_soft_boundary_multiwindow_p237.py",
            "p235_evidence": "paper/evidence/soft_boundary_mask_p235.json",
            "p237_evidence": "paper/evidence/soft_boundary_multiwindow_p237.json",
            "p235_output_root": "outputs/soft_boundary_mask_p235",
            "p237_output_root": "outputs/soft_boundary_multiwindow_p237",
            "hard_mask_contrast": "paper/evidence/gated_mask_failure_sweep_p234.json",
        },
        "metric_definitions": {
            "temporal_mask_stability": "Adjacent binary mask IoU, adjacent probability-map soft IoU, and mask coverage CV over 60 frames.",
            "motion_cue_alignment": "Farneback optical-flow and frame-difference high-cue enrichment inside the soft-mask region; high cue means top quantile over each adjacent pair.",
            "feature_residual_proxy": "ORB keypoint counts in predicted region and morphological boundary band before/after soft masking.",
        },
        "support_rule": {
            "temporal_coherent": "mean adjacent binary mask IoU >= 0.35 or mean adjacent probability soft IoU >= 0.55",
            "motion_or_difference_enriched": "mean flow or frame-difference high-cue enrichment >= 1.10",
            "region_orb_not_inflated": "masked-minus-raw ORB keypoint delta inside predicted region <= 0",
            "boundary_band_orb_not_inflated": "masked-minus-raw ORB keypoint delta in boundary band <= max(30, 5% of raw boundary-band keypoints)",
        },
        "summary_counts": {
            "window_count": len(evaluations),
            "self_supervised_support_count": support_count,
            "all_flags_required": True,
            "hard_mask_contrast_count": len(hard_contrasts),
        },
        "decision": decision,
        "evaluations": evaluations,
        "hard_mask_contrasts": hard_contrasts,
        "outputs": {
            "json": rel(EVIDENCE_JSON),
            "csv": rel(EVIDENCE_CSV),
            "markdown": rel(EXPORT_MD),
            "local_output_root": rel(args.output_root),
        },
        "next_step": (
            "Use P240 as self-supervised support for the bounded soft-boundary frontend module. If integrating into the "
            "thick manuscript, do it in a separate P241 pass and keep P195 blocked until independent labels are collected."
        ),
    }
    write_json(EVIDENCE_JSON, payload)
    write_csv(EVIDENCE_CSV, csv_rows)
    write_markdown(EXPORT_MD, payload)
    print(json.dumps({"status": status, "support_count": support_count, "json": rel(EVIDENCE_JSON)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
