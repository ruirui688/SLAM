#!/usr/bin/env python3
"""Summarize P227 P225 learned-mask baseline reproduction evidence."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "outputs" / "dynamic_slam_backend_input_pack_p227_p225_learned_mask"
DEFAULT_OUTPUT = ROOT / "outputs" / "dynamic_slam_backend_smoke_p227_p225_learned_mask"
DEFAULT_EVIDENCE = ROOT / "paper" / "evidence" / "p225_baseline_reproduction_p227.json"
DEFAULT_EXPORT = ROOT / "paper" / "export" / "p225_baseline_reproduction_p227.md"
DEFAULT_CSV = ROOT / "paper" / "evidence" / "p225_baseline_reproduction_p227_orb_features.csv"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_rgb_list(path: Path, frame_limit: int | None) -> list[tuple[float, Path]]:
    rows: list[tuple[float, Path]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        timestamp_s, image_s = line.split(maxsplit=1)
        rows.append((float(timestamp_s), ROOT / image_s))
        if frame_limit is not None and len(rows) >= frame_limit:
            break
    return rows


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
    if mask.shape != image.shape:
        mask = cv2.resize(mask, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)
    region_pixels = int(np.count_nonzero(mask > 0))
    in_region = 0
    for kp in keypoints:
        x = min(max(int(round(kp.pt[0])), 0), mask.shape[1] - 1)
        y = min(max(int(round(kp.pt[1])), 0), mask.shape[0] - 1)
        if mask[y, x] > 0:
            in_region += 1
    return total, in_region, region_pixels


def orb_sanity(input_dir: Path, frame_limit: int | None) -> tuple[dict, list[dict]]:
    raw_rows = read_rgb_list(input_dir / "raw" / "rgb.txt", frame_limit)
    masked_rows = read_rgb_list(input_dir / "masked" / "rgb.txt", frame_limit)
    orb = cv2.ORB_create(nfeatures=1000)
    frame_rows: list[dict] = []
    totals = {
        "frames": 0,
        "raw_total_keypoints": 0,
        "masked_total_keypoints": 0,
        "raw_predicted_mask_region_keypoints": 0,
        "masked_predicted_mask_region_keypoints": 0,
        "predicted_mask_region_pixels": 0,
    }
    for index, ((timestamp, raw_path), (_, masked_path)) in enumerate(zip(raw_rows, masked_rows)):
        mask_path = input_dir / "predicted_masks" / f"{index:06d}_p218_pred_mask.png"
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
    return totals, frame_rows


def write_orb_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "frame_index",
        "timestamp",
        "raw_total_keypoints",
        "masked_total_keypoints",
        "raw_predicted_mask_region_keypoints",
        "masked_predicted_mask_region_keypoints",
        "predicted_mask_region_pixels",
        "predicted_mask_region_keypoint_delta_masked_minus_raw",
        "total_keypoint_delta_masked_minus_raw",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, payload: dict) -> None:
    metrics = payload.get("metrics", {})
    orb = payload["orb_feature_sanity"]
    lines = [
        "# P227 P225 Baseline Reproduction",
        "",
        f"Status: `{payload['status']}`",
        "",
        f"Claim boundary: {payload['claim_boundary']}",
        "",
        "## Trajectory Metrics",
        "",
        "| Run | Frames | APE RMSE (m) | APE mean (m) | RPE RMSE (m) | RPE mean (m) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for label, values in metrics.items():
        lines.append(
            f"| {label} | {payload['frame_count']} | {values['ape_rmse_m']:.6f} | "
            f"{values['ape_mean_m']:.6f} | {values['rpe_rmse_m']:.6f} | {values['rpe_mean_m']:.6f} |"
        )
    delta = payload.get("delta_masked_minus_raw", {})
    if delta:
        lines += [
            "",
            f"Delta masked-minus-raw: APE RMSE `{delta['ape_rmse_m']:.6f} m`, RPE RMSE `{delta['rpe_rmse_m']:.6f} m`.",
        ]
    if payload.get("stability_gate_16_frame"):
        gate = payload["stability_gate_16_frame"]
        gate_delta = gate["delta_masked_minus_raw"]
        lines += [
            "",
            "16-frame stability gate:",
            "",
            f"- Status: `{gate['status']}`.",
            f"- Raw APE/RPE RMSE: `{gate['metrics']['raw RGB']['ape_rmse_m']:.6f}` / `{gate['metrics']['raw RGB']['rpe_rmse_m']:.6f}` m.",
            f"- Masked APE/RPE RMSE: `{gate['metrics']['masked RGB (P225 learned predicted-mask package)']['ape_rmse_m']:.6f}` / `{gate['metrics']['masked RGB (P225 learned predicted-mask package)']['rpe_rmse_m']:.6f}` m.",
            f"- Delta masked-minus-raw APE/RPE RMSE: `{gate_delta['ape_rmse_m']:.6f}` / `{gate_delta['rpe_rmse_m']:.6f}` m.",
        ]
    lines += [
        "",
        "## ORB Feature Sanity",
        "",
        "This is a predicted-mask-region proxy because independent GT dynamic masks are not available for this sequence.",
        "",
        f"- Raw total keypoints: `{orb['raw_total_keypoints']}`.",
        f"- Masked total keypoints: `{orb['masked_total_keypoints']}`.",
        f"- Raw keypoints in predicted-mask regions: `{orb['raw_predicted_mask_region_keypoints']}`.",
        f"- Masked keypoints in predicted-mask regions: `{orb['masked_predicted_mask_region_keypoints']}`.",
        f"- Predicted-region keypoint delta masked-minus-raw: `{orb['raw_to_masked_predicted_region_keypoint_delta']}`.",
        "",
        "## Interpretation",
        "",
        payload["interpretation"],
        "",
        "## Commands",
        "",
        "```bash",
        *payload["commands"],
        "```",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--metrics-prefix", default="p227_p225_learned_mask_metrics")
    parser.add_argument("--frame-limit", type=int, default=None)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--export", type=Path, default=DEFAULT_EXPORT)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--command", action="append", default=[])
    args = parser.parse_args()

    smoke = read_json(args.output_dir / "dynamic_slam_backend_smoke_manifest.json")
    metrics_payload = read_json(args.output_dir / f"{args.metrics_prefix}.json")
    gate_dir = Path(str(args.output_dir) + "_16")
    gate_payload = None
    if gate_dir.exists():
        gate_smoke = read_json(gate_dir / "dynamic_slam_backend_smoke_manifest.json")
        gate_metrics = read_json(gate_dir / f"{args.metrics_prefix}.json")
        gate_payload = {
            "status": gate_smoke.get("status"),
            "frame_count": gate_smoke.get("frame_limit"),
            "runs": gate_smoke.get("runs", []),
            "metrics": gate_metrics.get("metrics", {}),
            "delta_masked_minus_raw": gate_metrics.get("delta_masked_minus_raw", {}),
        }
    orb_summary, orb_rows = orb_sanity(args.input_dir, args.frame_limit)
    write_orb_csv(args.csv, orb_rows)

    metrics = metrics_payload["metrics"]
    raw = metrics["raw RGB"]
    masked_key = next(key for key in metrics if key != "raw RGB")
    masked = metrics[masked_key]
    delta = metrics_payload["delta_masked_minus_raw"]
    passed = all(run["status"] == "ok" for run in smoke["runs"])
    neutral_or_better = (
        delta["ape_rmse_m"] <= max(0.001, raw["ape_rmse_m"] * 0.05)
        and delta["rpe_rmse_m"] <= max(0.001, raw["rpe_rmse_m"] * 0.05)
    )
    interpretation = (
        "The P225 learned-mask raw/masked DROID-SLAM smoke reproduced successfully. "
        "Masked trajectory error is neutral within the bounded smoke tolerance, so this is baseline reproduction evidence, not an improvement claim."
        if passed and neutral_or_better
        else "The run produced metrics, but masked trajectory error is outside the neutral smoke tolerance; treat it as reproduction evidence requiring follow-up, not an improvement."
    )
    payload = {
        "artifact": "P227 P225 learned-mask baseline reproduction",
        "created": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "status": "baseline_reproduction_passed_neutral" if passed and neutral_or_better else "needs_followup",
        "claim_boundary": "Bounded DROID-SLAM trajectory smoke and ORB feature sanity only. No improvement claim unless APE/RPE support it; ORB dynamic-region counts use predicted-mask-region proxy, not GT dynamic masks.",
        "frame_count": smoke["frame_limit"],
        "inputs": {
            "input_pack": rel(args.input_dir),
            "smoke_manifest": rel(args.output_dir / "dynamic_slam_backend_smoke_manifest.json"),
            "metrics_json": rel(args.output_dir / f"{args.metrics_prefix}.json"),
            "orb_feature_csv": rel(args.csv),
        },
        "runtime": smoke.get("runtime", {}),
        "runs": smoke["runs"],
        "stability_gate_16_frame": gate_payload,
        "metrics": {
            "raw RGB": raw,
            masked_key: masked,
        },
        "delta_masked_minus_raw": delta,
        "orb_feature_sanity": orb_summary,
        "orb_feature_csv": rel(args.csv),
        "commands": args.command,
        "interpretation": interpretation,
        "next_network_module_recommendation": (
            "Keep the DROID/evo path fixed and add a small learned-mask module next: confidence/coverage-gated dilation "
            "or boundary refinement on the P218/P225 SmallUNet output, then rerun the same raw-vs-masked smoke and ORB proxy."
        ),
    }
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(args.export, payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
