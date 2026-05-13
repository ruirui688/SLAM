#!/usr/bin/env python3
"""Build and summarize the P228 confidence-gated mask module.

The build step reads the P225 raw frames and probability maps, applies a
bounded confidence/coverage gate, writes a new masked sequence, and prepares a
DROID-compatible raw-vs-masked backend pack. The summarize step consumes the
existing DROID/evo outputs and writes the P228 paper evidence files.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "outputs" / "temporal_masked_sequence_p225" / "sequence"
DEFAULT_SEQUENCE_OUTPUT = ROOT / "outputs" / "temporal_masked_sequence_p228_conf_gated"
DEFAULT_PACK_OUTPUT = ROOT / "outputs" / "dynamic_slam_backend_input_pack_p228_conf_gated"
DEFAULT_SMOKE_OUTPUT = ROOT / "outputs" / "dynamic_slam_backend_smoke_p228_conf_gated"
DEFAULT_EVIDENCE = ROOT / "paper" / "evidence" / "confidence_gated_mask_module_p228.json"
DEFAULT_EXPORT = ROOT / "paper" / "export" / "confidence_gated_mask_module_p228.md"
DEFAULT_CSV = ROOT / "paper" / "evidence" / "confidence_gated_mask_module_p228_orb_features.csv"
DEFAULT_BASELINE = ROOT / "paper" / "evidence" / "p225_baseline_reproduction_p227.json"

P227_16_RAW_APE = 0.025810
P227_16_RAW_RPE = 0.092888
P227_16_MASKED_APE = 0.025066
P227_16_MASKED_RPE = 0.092770
P227_60_RAW_APE = 0.088504
P227_60_RAW_RPE = 0.076145
P227_60_MASKED_APE = 0.084529
P227_60_MASKED_RPE = 0.076226


@dataclass(frozen=True)
class GateParams:
    probability_threshold: float
    dilation_px: int
    min_component_area_px: int
    max_coverage: float
    target_coverage: float
    mask_value: int


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


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
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{timestamp:.9f} {rel(image_path)}" for timestamp, image_path in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def connected_component_filter(mask: np.ndarray, min_area: int) -> np.ndarray:
    if min_area <= 1 or not np.any(mask):
        return mask
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
    keep = np.zeros(mask.shape, dtype=bool)
    for label in range(1, count):
        if int(stats[label, cv2.CC_STAT_AREA]) >= min_area:
            keep |= labels == label
    return keep


def dilate_mask(mask: np.ndarray, dilation_px: int) -> np.ndarray:
    if dilation_px <= 0 or not np.any(mask):
        return mask
    size = dilation_px * 2 + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))
    return cv2.dilate(mask.astype(np.uint8), kernel, iterations=1).astype(bool)


def cap_by_probability(mask: np.ndarray, probability: np.ndarray, max_coverage: float, target_coverage: float) -> tuple[np.ndarray, bool]:
    pixels = mask.size
    coverage = float(np.count_nonzero(mask)) / max(pixels, 1)
    if coverage <= max_coverage:
        return mask, False
    target_pixels = max(1, int(round(target_coverage * pixels)))
    candidate_scores = probability[mask]
    if candidate_scores.size <= target_pixels:
        return mask, False
    cutoff = np.partition(candidate_scores, -target_pixels)[-target_pixels]
    capped = mask & (probability >= cutoff)
    if int(np.count_nonzero(capped)) > target_pixels:
        coords = np.flatnonzero(capped.ravel())
        scores = probability.ravel()[coords]
        keep_order = np.argsort(scores, kind="mergesort")[-target_pixels:]
        exact = np.zeros(mask.size, dtype=bool)
        exact[coords[keep_order]] = True
        capped = exact.reshape(mask.shape)
    return capped, True


def build_mask(probability: np.ndarray, params: GateParams) -> tuple[np.ndarray, dict]:
    candidate = probability >= params.probability_threshold
    after_components = connected_component_filter(candidate, params.min_component_area_px)
    after_dilation = dilate_mask(after_components, params.dilation_px)
    gated, capped = cap_by_probability(
        after_dilation,
        probability,
        params.max_coverage,
        min(params.target_coverage, params.max_coverage),
    )
    total = gated.size
    stats = {
        "candidate_pixels": int(np.count_nonzero(candidate)),
        "component_filtered_pixels": int(np.count_nonzero(after_components)),
        "dilated_pixels": int(np.count_nonzero(after_dilation)),
        "mask_pixels": int(np.count_nonzero(gated)),
        "coverage_ratio": float(np.count_nonzero(gated)) / max(total, 1),
        "coverage_capped": capped,
    }
    return gated, stats


def mask_rgb(raw: np.ndarray, mask: np.ndarray, mask_value: int) -> np.ndarray:
    output = raw.copy()
    output[mask] = mask_value
    return output


def copy_sequence_sidecars(source_dir: Path, sequence_dir: Path) -> None:
    for variant in ("raw", "masked"):
        for name in ("TorWIC_mono_left.yaml", "calibrations.txt", "frame_times.txt", "groundtruth.txt", "traj_gt.txt"):
            src = source_dir / "raw" / name
            if src.exists():
                shutil.copy2(src, sequence_dir / variant / name)


def copy_pack_sidecars(source_dir: Path, pack_dir: Path, frame_limit: int | None) -> None:
    gt_rows = read_gt_rows(source_dir / "raw" / "groundtruth.txt", frame_limit)
    (pack_dir / "groundtruth.txt").write_text(
        "# timestamp tx ty tz qx qy qz qw\n" + "\n".join(gt_rows) + "\n",
        encoding="utf-8",
    )
    for name in ("frame_times.txt", "calibrations.txt", "TorWIC_mono_left.yaml"):
        shutil.copy2(source_dir / "raw" / name, pack_dir / name)


def build_outputs(args: argparse.Namespace) -> dict:
    params = GateParams(
        probability_threshold=args.probability_threshold,
        dilation_px=args.dilation_px,
        min_component_area_px=args.min_component_area_px,
        max_coverage=args.max_coverage,
        target_coverage=args.target_coverage,
        mask_value=args.mask_value,
    )
    source_dir = args.source_dir
    sequence_dir = args.sequence_output
    pack_dir = args.pack_output

    rows = read_rgb_rows(source_dir / "raw" / "rgb.txt", args.frame_limit)
    for path in (
        sequence_dir / "sequence" / "raw" / "image_left",
        sequence_dir / "sequence" / "masked" / "image_left",
        sequence_dir / "sequence" / "predicted_masks",
        sequence_dir / "sequence" / "probabilities",
        pack_dir / "raw" / "image_left",
        pack_dir / "masked" / "image_left",
        pack_dir / "predicted_masks",
        pack_dir / "probabilities",
    ):
        path.mkdir(parents=True, exist_ok=True)

    sequence_raw_rows: list[tuple[float, Path]] = []
    sequence_masked_rows: list[tuple[float, Path]] = []
    pack_raw_rows: list[tuple[float, Path]] = []
    pack_masked_rows: list[tuple[float, Path]] = []
    frames: list[dict] = []

    for index, (timestamp, image_rel) in enumerate(rows):
        raw_src = source_dir / "raw" / image_rel
        prob_src = source_dir / "probabilities" / f"{index:06d}_p218_prob.png"
        if not raw_src.exists():
            raise FileNotFoundError(raw_src)
        if not prob_src.exists():
            raise FileNotFoundError(prob_src)

        raw = np.array(Image.open(raw_src).convert("RGB"))
        probability_u8 = np.array(Image.open(prob_src).convert("L"))
        probability = probability_u8.astype(np.float32) / 255.0
        mask, stats = build_mask(probability, params)
        masked = mask_rgb(raw, mask, params.mask_value)

        raw_name = f"{index:06d}.png"
        mask_name = f"{index:06d}_p228_conf_gated_mask.png"
        prob_name = f"{index:06d}_p218_prob.png"

        seq_raw = sequence_dir / "sequence" / "raw" / "image_left" / raw_name
        seq_masked = sequence_dir / "sequence" / "masked" / "image_left" / raw_name
        seq_mask = sequence_dir / "sequence" / "predicted_masks" / mask_name
        seq_prob = sequence_dir / "sequence" / "probabilities" / prob_name
        pack_raw = pack_dir / "raw" / "image_left" / raw_name
        pack_masked = pack_dir / "masked" / "image_left" / raw_name
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

        sequence_raw_rows.append((timestamp, seq_raw))
        sequence_masked_rows.append((timestamp, seq_masked))
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
                **stats,
            }
        )

    write_rgb_list(sequence_dir / "sequence" / "raw" / "rgb.txt", sequence_raw_rows)
    write_rgb_list(sequence_dir / "sequence" / "masked" / "rgb.txt", sequence_masked_rows)
    write_rgb_list(pack_dir / "raw" / "rgb.txt", pack_raw_rows)
    write_rgb_list(pack_dir / "masked" / "rgb.txt", pack_masked_rows)
    copy_sequence_sidecars(source_dir, sequence_dir / "sequence")
    copy_pack_sidecars(source_dir, pack_dir, args.frame_limit)

    total_pixels = sum(frame["mask_pixels"] for frame in frames)
    total_candidate = sum(frame["candidate_pixels"] for frame in frames)
    total_area = len(frames) * raw.shape[0] * raw.shape[1] if frames else 0
    manifest = {
        "artifact": "P228 confidence-gated P225 probability-mask module",
        "created": now(),
        "status": "backend_input_pack_ready",
        "claim_boundary": "Mask post-processing and DROID input pack only; trajectory and ORB claims require separate smoke/evo evaluation.",
        "source_dir": rel(source_dir),
        "sequence_output": rel(sequence_dir),
        "output_dir": rel(pack_dir),
        "frame_count": len(frames),
        "raw_rgb_list": rel(pack_dir / "raw" / "rgb.txt"),
        "masked_rgb_list": rel(pack_dir / "masked" / "rgb.txt"),
        "groundtruth_tum": rel(pack_dir / "groundtruth.txt"),
        "dynamic_mask_policy": "P228 confidence/coverage-gated post-processing of P225 P218 probability maps.",
        "module_parameters": asdict(params),
        "predicted_mask_region_proxy": True,
        "mask_summary": {
            "total_candidate_pixels": int(total_candidate),
            "total_mask_pixels": int(total_pixels),
            "mean_coverage_percent": round((total_pixels / max(total_area, 1)) * 100.0, 6),
            "coverage_capped_frames": [frame["frame_index"] for frame in frames if frame["coverage_capped"]],
            "nonzero_mask_frames": sum(1 for frame in frames if frame["mask_pixels"] > 0),
        },
        "frames": frames,
    }
    for output in (pack_dir / "backend_input_manifest.json", sequence_dir / "backend_input_manifest.json"):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return manifest


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_backend_rgb_list(path: Path, frame_limit: int | None) -> list[tuple[float, Path]]:
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
    raw_rows = read_backend_rgb_list(input_dir / "raw" / "rgb.txt", frame_limit)
    masked_rows = read_backend_rgb_list(input_dir / "masked" / "rgb.txt", frame_limit)
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
        mask_path = input_dir / "predicted_masks" / f"{index:06d}_p228_conf_gated_mask.png"
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
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def compact_metrics(metrics_payload: dict) -> dict:
    metrics = metrics_payload["metrics"]
    masked_key = next(key for key in metrics if key != "raw RGB")
    return {
        "raw RGB": metrics["raw RGB"],
        masked_key: metrics[masked_key],
        "delta_masked_minus_raw": metrics_payload.get("delta_masked_minus_raw", {}),
    }


def metric_status(raw: dict, masked: dict, tolerance: float = 0.001) -> bool:
    return (
        masked["ape_rmse_m"] <= raw["ape_rmse_m"] + tolerance
        and masked["rpe_rmse_m"] <= raw["rpe_rmse_m"] + tolerance
    )


def write_markdown(path: Path, payload: dict) -> None:
    gate = payload["stability_gate_16_frame"]
    full = payload["full_60_frame"]
    orb = payload["orb_feature_sanity"]
    params = payload["module_parameters"]
    lines = [
        "# P228 Confidence-Gated Mask Module",
        "",
        f"Status: `{payload['status']}`",
        "",
        f"Claim boundary: {payload['claim_boundary']}",
        "",
        "## Module",
        "",
        f"- Probability threshold: `{params['probability_threshold']}`.",
        f"- Dilation: `{params['dilation_px']}` px.",
        f"- Min connected component area: `{params['min_component_area_px']}` px.",
        f"- Coverage cap / target: `{params['max_coverage']}` / `{params['target_coverage']}`.",
        f"- Mean gated mask coverage: `{payload['mask_summary']['mean_coverage_percent']:.6f}%`.",
        "",
        "## Trajectory Metrics",
        "",
        "| Run | Frames | Raw APE | Masked APE | Raw RPE | Masked RPE | Delta APE | Delta RPE |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label, block in (("P228 gate", gate), ("P228 full", full)):
        metrics = block["metrics"]
        masked_key = next(key for key in metrics if key != "raw RGB")
        raw = metrics["raw RGB"]
        masked = metrics[masked_key]
        delta = block["delta_masked_minus_raw"]
        lines.append(
            f"| {label} | {block['frame_count']} | {raw['ape_rmse_m']:.6f} | {masked['ape_rmse_m']:.6f} | "
            f"{raw['rpe_rmse_m']:.6f} | {masked['rpe_rmse_m']:.6f} | {delta['ape_rmse_m']:.6f} | {delta['rpe_rmse_m']:.6f} |"
        )
    lines += [
        "",
        "## P227 Comparison",
        "",
        f"- P227 16f raw/masked APE: `{P227_16_RAW_APE:.6f}` / `{P227_16_MASKED_APE:.6f}`; RPE: `{P227_16_RAW_RPE:.6f}` / `{P227_16_MASKED_RPE:.6f}`.",
        f"- P227 60f raw/masked APE: `{P227_60_RAW_APE:.6f}` / `{P227_60_MASKED_APE:.6f}`; RPE: `{P227_60_RAW_RPE:.6f}` / `{P227_60_MASKED_RPE:.6f}`.",
        "",
        "## ORB Feature Proxy",
        "",
        "This uses the P228 predicted-mask region, not independent dynamic GT.",
        "",
        f"- Raw total keypoints: `{orb['raw_total_keypoints']}`.",
        f"- Masked total keypoints: `{orb['masked_total_keypoints']}`.",
        f"- Raw keypoints in gated regions: `{orb['raw_predicted_mask_region_keypoints']}`.",
        f"- Masked keypoints in gated regions: `{orb['masked_predicted_mask_region_keypoints']}`.",
        f"- Region keypoint delta masked-minus-raw: `{orb['raw_to_masked_predicted_region_keypoint_delta']}`.",
        f"- P227 predicted-region delta baseline: `{payload['p227_orb_feature_sanity']['raw_to_masked_predicted_region_keypoint_delta']}`.",
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


def summarize_outputs(args: argparse.Namespace) -> dict:
    manifest = read_json(args.pack_output / "backend_input_manifest.json")
    smoke = read_json(args.smoke_output / "dynamic_slam_backend_smoke_manifest.json")
    metrics_payload = read_json(args.smoke_output / f"{args.metrics_prefix}.json")
    gate_dir = Path(str(args.smoke_output) + "_16")
    gate_smoke = read_json(gate_dir / "dynamic_slam_backend_smoke_manifest.json")
    gate_metrics_payload = read_json(gate_dir / f"{args.metrics_prefix}.json")
    baseline = read_json(args.baseline_evidence) if args.baseline_evidence.exists() else {}
    baseline_orb = baseline.get("orb_feature_sanity", {})

    orb_summary, orb_rows = orb_sanity(args.pack_output, args.frame_limit)
    write_orb_csv(args.csv, orb_rows)

    full_metrics = compact_metrics(metrics_payload)
    gate_metrics = compact_metrics(gate_metrics_payload)
    full_masked_key = next(key for key in full_metrics if key not in {"raw RGB", "delta_masked_minus_raw"})
    gate_masked_key = next(key for key in gate_metrics if key not in {"raw RGB", "delta_masked_minus_raw"})

    runs_ok = all(run["status"] == "ok" for run in smoke["runs"]) and all(
        run["status"] == "ok" for run in gate_smoke["runs"]
    )
    gate_ok = metric_status(gate_metrics["raw RGB"], gate_metrics[gate_masked_key])
    full_ok = metric_status(full_metrics["raw RGB"], full_metrics[full_masked_key])
    p227_orb_delta = baseline_orb.get("raw_to_masked_predicted_region_keypoint_delta")
    orb_remains_or_improves = (
        p227_orb_delta is not None
        and orb_summary["raw_to_masked_predicted_region_keypoint_delta"] <= int(p227_orb_delta)
    )

    if runs_ok and gate_ok and full_ok and orb_remains_or_improves:
        status = "viable_story_seed"
        interpretation = (
            "The confidence-gated module stayed within the bounded trajectory smoke tolerance and preserved/improved the P227 ORB predicted-region suppression proxy. "
            "This is only a small frontend mask-module smoke, but it is a viable story seed."
        )
    elif runs_ok and gate_ok and full_ok:
        status = "trajectory_neutral_or_better_orb_weaker"
        interpretation = (
            "The confidence-gated module stayed within the bounded trajectory smoke tolerance, but the ORB predicted-region suppression proxy did not match P227. "
            "Treat this as a neutral module seed and tune coverage/threshold before making a story claim."
        )
    else:
        status = "failed_or_neutral_requires_tuning"
        interpretation = (
            "The confidence-gated module produced bounded smoke evidence, but trajectory metrics exceeded the tiny tolerance or a run failed. "
            "Do not claim improvement; tune threshold, dilation, or coverage cap and rerun."
        )

    payload = {
        "artifact": "P228 confidence-gated mask module smoke",
        "created": now(),
        "status": status,
        "claim_boundary": "Small frontend mask post-processing smoke on the P225 sequence only; not a full benchmark, navigation claim, or independent dynamic segmentation claim. P195 remains BLOCKED.",
        "inputs": {
            "input_pack": rel(args.pack_output),
            "sequence_output": rel(args.sequence_output),
            "smoke_manifest_16": rel(gate_dir / "dynamic_slam_backend_smoke_manifest.json"),
            "metrics_json_16": rel(gate_dir / f"{args.metrics_prefix}.json"),
            "smoke_manifest_60": rel(args.smoke_output / "dynamic_slam_backend_smoke_manifest.json"),
            "metrics_json_60": rel(args.smoke_output / f"{args.metrics_prefix}.json"),
            "orb_feature_csv": rel(args.csv),
            "baseline_p227": rel(args.baseline_evidence),
        },
        "module_parameters": manifest["module_parameters"],
        "mask_summary": manifest["mask_summary"],
        "runtime": smoke.get("runtime", {}),
        "stability_gate_16_frame": {
            "status": gate_smoke.get("status"),
            "frame_count": gate_smoke.get("frame_limit"),
            "runs": gate_smoke.get("runs", []),
            "metrics": {key: value for key, value in gate_metrics.items() if key != "delta_masked_minus_raw"},
            "delta_masked_minus_raw": gate_metrics["delta_masked_minus_raw"],
        },
        "full_60_frame": {
            "status": smoke.get("status"),
            "frame_count": smoke.get("frame_limit"),
            "runs": smoke.get("runs", []),
            "metrics": {key: value for key, value in full_metrics.items() if key != "delta_masked_minus_raw"},
            "delta_masked_minus_raw": full_metrics["delta_masked_minus_raw"],
        },
        "p227_baseline_metrics": {
            "16_frame": {
                "raw_ape_rmse_m": P227_16_RAW_APE,
                "raw_rpe_rmse_m": P227_16_RAW_RPE,
                "masked_ape_rmse_m": P227_16_MASKED_APE,
                "masked_rpe_rmse_m": P227_16_MASKED_RPE,
            },
            "60_frame": {
                "raw_ape_rmse_m": P227_60_RAW_APE,
                "raw_rpe_rmse_m": P227_60_RAW_RPE,
                "masked_ape_rmse_m": P227_60_MASKED_APE,
                "masked_rpe_rmse_m": P227_60_MASKED_RPE,
            },
        },
        "orb_feature_sanity": orb_summary,
        "p227_orb_feature_sanity": baseline_orb,
        "orb_proxy_remains_or_improves_vs_p227": orb_remains_or_improves,
        "commands": args.command,
        "interpretation": interpretation,
        "next_adjustment_if_needed": "If ORB suppression is too weak, lower probability_threshold below the current value or raise max_coverage/target_coverage modestly; if trajectory degrades, reduce dilation_px or max_coverage.",
    }
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(args.export, payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command_name", required=True)

    build = subparsers.add_parser("build", help="Build P228 sequence and DROID backend input pack.")
    build.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    build.add_argument("--sequence-output", type=Path, default=DEFAULT_SEQUENCE_OUTPUT)
    build.add_argument("--pack-output", type=Path, default=DEFAULT_PACK_OUTPUT)
    build.add_argument("--frame-limit", type=int, default=None)
    build.add_argument("--probability-threshold", type=float, default=0.60)
    build.add_argument("--dilation-px", type=int, default=1)
    build.add_argument("--min-component-area-px", type=int, default=128)
    build.add_argument("--max-coverage", type=float, default=0.18)
    build.add_argument("--target-coverage", type=float, default=0.12)
    build.add_argument("--mask-value", type=int, default=0)
    build.set_defaults(func=build_outputs)

    summarize = subparsers.add_parser("summarize", help="Summarize DROID/evo outputs into P228 evidence.")
    summarize.add_argument("--sequence-output", type=Path, default=DEFAULT_SEQUENCE_OUTPUT)
    summarize.add_argument("--pack-output", type=Path, default=DEFAULT_PACK_OUTPUT)
    summarize.add_argument("--smoke-output", type=Path, default=DEFAULT_SMOKE_OUTPUT)
    summarize.add_argument("--metrics-prefix", default="p228_conf_gated_metrics")
    summarize.add_argument("--frame-limit", type=int, default=None)
    summarize.add_argument("--baseline-evidence", type=Path, default=DEFAULT_BASELINE)
    summarize.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    summarize.add_argument("--export", type=Path, default=DEFAULT_EXPORT)
    summarize.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    summarize.add_argument("--command", action="append", default=[])
    summarize.set_defaults(func=summarize_outputs)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
