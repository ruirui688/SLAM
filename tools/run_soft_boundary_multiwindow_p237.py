#!/usr/bin/env python3
"""Run P237 bounded multi-window validation for the P235 soft-boundary candidate.

This tool expands the selected P235 variant to additional TorWIC windows while
keeping the claim boundary narrow: predicted-mask frontend smoke only, no full
benchmark, navigation, independent-label, or learned map-admission claim.
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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import apply_soft_boundary_mask_p235 as p235  # noqa: E402
import build_temporal_masked_sequence_p225 as p225  # noqa: E402


DEFAULT_CHECKPOINT = ROOT / "outputs/temporal_masked_sequence_p225/model/p225_retrained_p218_smallunet.pt"
OUTPUT_ROOT = ROOT / "outputs/soft_boundary_multiwindow_p237"
EVIDENCE_JSON = ROOT / "paper/evidence/soft_boundary_multiwindow_p237.json"
EVIDENCE_CSV = ROOT / "paper/evidence/soft_boundary_multiwindow_p237.csv"
EXPORT_MD = ROOT / "paper/export/soft_boundary_multiwindow_p237.md"
SELECTED_VARIANT = p235.SoftVariant(
    "meanfill035_feather5_thr060_cap012_min256",
    "mean_color_feather",
    probability_threshold=0.60,
    dilation_px=0,
    min_component_area_px=256,
    max_coverage=0.12,
    target_coverage=0.10,
    attenuation_alpha=0.35,
    feather_sigma=5.0,
    mean_fill=True,
)


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


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


def default_windows() -> list[dict[str, Any]]:
    return [
        {
            "id": "aisle_cw_0240_0299",
            "sequence_label": "Oct. 12, 2022 Aisle_CW",
            "sequence_dir": ROOT / "data/TorWIC_SLAM_Dataset/Oct. 12, 2022/Aisle_CW",
            "start_index": 240,
            "frame_count": 60,
            "selection_reason": "same sequence as P225/P228, non-overlapping with 120-179, 480-539, and 840-899",
            "sequence_family": "same_sequence_new_window",
        },
        {
            "id": "aisle_cw_0660_0719",
            "sequence_label": "Oct. 12, 2022 Aisle_CW",
            "sequence_dir": ROOT / "data/TorWIC_SLAM_Dataset/Oct. 12, 2022/Aisle_CW",
            "start_index": 660,
            "frame_count": 60,
            "selection_reason": "same sequence as P225/P228, non-overlapping mid-late window",
            "sequence_family": "same_sequence_new_window",
        },
        {
            "id": "aisle_cw_0960_1019",
            "sequence_label": "Oct. 12, 2022 Aisle_CW",
            "sequence_dir": ROOT / "data/TorWIC_SLAM_Dataset/Oct. 12, 2022/Aisle_CW",
            "start_index": 960,
            "frame_count": 60,
            "selection_reason": "same sequence as P225/P228, non-overlapping late window within available frame range",
            "sequence_family": "same_sequence_new_window",
        },
        {
            "id": "aisle_ccw_0240_0299",
            "sequence_label": "Oct. 12, 2022 Aisle_CCW",
            "sequence_dir": ROOT / "data/TorWIC_SLAM_Dataset/Oct. 12, 2022/Aisle_CCW",
            "start_index": 240,
            "frame_count": 60,
            "selection_reason": "nearby different sequence with image_left, frame_times, traj_gt, and shared Oct. 12 calibration",
            "sequence_family": "nearby_different_sequence",
        },
    ]


def ensure_oct12_calibration(sequence_package_root: Path) -> None:
    calibration_src = ROOT / "data/TorWIC_SLAM_Dataset/Oct. 12, 2022/calibrations.txt"
    if not calibration_src.exists():
        return
    for variant in ("raw", "masked"):
        dst = sequence_package_root / variant / "calibrations.txt"
        if not dst.exists():
            shutil.copy2(calibration_src, dst)


def build_p225_window(args: argparse.Namespace, window: dict[str, Any]) -> dict[str, Any]:
    out_root = args.output_root / window["id"] / "temporal_masked_sequence_p225"
    p225.EVIDENCE_JSON = out_root / "evidence" / f"{window['id']}_temporal_masked_sequence_p225.json"
    p225.EVIDENCE_CSV = out_root / "evidence" / f"{window['id']}_temporal_masked_sequence_p225.csv"
    p225.EXPORT_MD = out_root / "evidence" / f"{window['id']}_temporal_masked_sequence_p225.md"
    p225.EVIDENCE_CSV.parent.mkdir(parents=True, exist_ok=True)
    p225_args = argparse.Namespace(
        sequence_dir=window["sequence_dir"],
        output_root=out_root,
        p217_manifest=ROOT / "paper/evidence/dynamic_mask_dataset_p217.csv",
        p217_json=ROOT / "paper/evidence/dynamic_mask_dataset_p217.json",
        checkpoint=args.checkpoint,
        start_index=window["start_index"],
        frame_count=window["frame_count"],
        epochs=1,
        batch_size=8,
        resize_width=320,
        resize_height=180,
        base_channels=12,
        lr=2e-3,
        weight_decay=1e-4,
        max_pos_weight=4.0,
        seed=225,
        threshold=0.5,
        require_cuda=args.require_cuda,
    )
    payload = p225.build_sequence(p225_args)
    ensure_oct12_calibration(Path(payload["outputs"]["package_root"]))
    return payload


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
    output_dir = args.output_root / result["window_id"] / SELECTED_VARIANT.variant_id / f"dynamic_slam_backend_smoke_p237_{frame_limit}"
    prefix = f"p237_{result['window_id']}_{SELECTED_VARIANT.variant_id}_{frame_limit}f_metrics"
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
            f"P237 {frame_limit}-frame soft-boundary multi-window metrics ({result['window_id']})",
            "--scope",
            f"P237 bounded frontend smoke: {frame_limit} frames from {result['sequence_label']} source indices {result['start_index']}-{result['start_index'] + frame_limit - 1}.",
            "--masked-label",
            f"masked RGB (P237 {SELECTED_VARIANT.variant_id} soft-boundary frontend)",
            "--output-prefix",
            prefix,
            "--interpretation",
            "P237 bounded soft-boundary multi-window smoke; no full benchmark or navigation claim.",
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


def evaluate_window(args: argparse.Namespace, window: dict[str, Any]) -> dict[str, Any]:
    p225_payload = build_p225_window(args, window)
    p235_args = argparse.Namespace(
        output_root=args.output_root,
        frame_limit=None,
        neutral_tolerance_m=args.neutral_tolerance_m,
        orb_reverse_tolerance_fraction=args.orb_reverse_tolerance_fraction,
        droid_timeout_seconds=args.droid_timeout_seconds,
        skip_droid=True,
    )
    soft_window = {
        "id": window["id"],
        "sequence_label": window["sequence_label"],
        "start_index": window["start_index"],
        "end_index": window["start_index"] + window["frame_count"] - 1,
        "source_dir": ROOT / p225_payload["outputs"]["package_root"],
        "priority": window["sequence_family"],
    }
    with contextlib.redirect_stdout(io.StringIO()):
        manifest = p235.build_variant_pack(p235_args, soft_window, SELECTED_VARIANT)
    pack_dir = ROOT / manifest["output_dir"]
    orb_summary, orb_rows = p235.orb_sanity(pack_dir, None)
    orb_csv = args.output_root / window["id"] / SELECTED_VARIANT.variant_id / f"{window['id']}_{SELECTED_VARIANT.variant_id}_orb_features.csv"
    p235.write_orb_csv(orb_csv, orb_rows)
    delta = orb_summary["raw_to_masked_predicted_region_keypoint_delta"]
    raw_region = max(orb_summary["raw_predicted_mask_region_keypoints"], 1)
    not_significant_reverse = delta <= max(30, int(round(raw_region * args.orb_reverse_tolerance_fraction)))
    result = {
        "window_id": window["id"],
        "sequence_label": window["sequence_label"],
        "sequence_family": window["sequence_family"],
        "source_sequence_dir": rel(window["sequence_dir"]),
        "start_index": window["start_index"],
        "end_index": window["start_index"] + window["frame_count"] - 1,
        "frame_count": window["frame_count"],
        "selection_reason": window["selection_reason"],
        "variant_id": SELECTED_VARIANT.variant_id,
        "method": SELECTED_VARIANT.method,
        "parameters": SELECTED_VARIANT.__dict__,
        "p225": {
            "json": p225_payload["outputs"]["json"],
            "csv": p225_payload["outputs"]["csv"],
            "markdown": p225_payload["outputs"]["markdown"],
            "package_root": p225_payload["outputs"]["package_root"],
            "mask_model": p225_payload["mask_model"],
            "mask_statistics": p225_payload["mask_statistics"],
        },
        "pack_dir": manifest["output_dir"],
        "manifest": rel(pack_dir / "backend_input_manifest.json"),
        "mask_summary": manifest["mask_summary"],
        "orb_feature_sanity": orb_summary | {"orb_feature_csv": rel(orb_csv)},
        "orb_proxy_down": delta < 0,
        "orb_proxy_not_significant_reverse": not_significant_reverse,
        "droid_gates": [],
    }
    if not args.skip_droid and result["orb_proxy_down"]:
        result["droid_gates"].append(run_droid_gate(args, result, 16))
    return result


def assign_window_status(result: dict[str, Any]) -> str:
    gate16 = next((gate for gate in result["droid_gates"] if gate["frame_limit"] == 16), None)
    gate60 = next((gate for gate in result["droid_gates"] if gate["frame_limit"] == 60), None)
    if result["orb_proxy_down"] and result["orb_feature_sanity"]["total_keypoints_stable"] and gate16 and gate16["trajectory_neutral"]:
        if gate60:
            return "orb_proxy_down_droid16_neutral_droid60_checked" if gate60["trajectory_neutral"] else "orb_proxy_down_droid16_neutral_droid60_mixed"
        return "orb_proxy_down_droid16_neutral"
    if result["orb_proxy_down"]:
        return "orb_proxy_down_droid_not_run_or_mixed"
    if result["orb_proxy_not_significant_reverse"]:
        return "orb_proxy_near_neutral"
    return "orb_proxy_reverse"


def write_csv(path: Path, payload: dict[str, Any]) -> None:
    rows = []
    for result in payload["evaluations"]:
        orb = result["orb_feature_sanity"]
        gate16 = next((gate for gate in result["droid_gates"] if gate["frame_limit"] == 16), {})
        gate60 = next((gate for gate in result["droid_gates"] if gate["frame_limit"] == 60), {})
        rows.append(
            {
                "window_id": result["window_id"],
                "sequence_label": result["sequence_label"],
                "sequence_family": result["sequence_family"],
                "start_index": result["start_index"],
                "end_index": result["end_index"],
                "frame_count": result["frame_count"],
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


def fmt_gate(gate: dict[str, Any] | None) -> str:
    if not gate:
        return "not_run"
    delta = (gate.get("metrics") or {}).get("delta_masked_minus_raw", {})
    if not delta:
        return f"neutral={gate.get('trajectory_neutral')}"
    return f"neutral={gate.get('trajectory_neutral')}, dAPE={delta.get('ape_rmse_m')}, dRPE={delta.get('rpe_rmse_m')}"


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# P237 Soft Boundary Multi-Window Validation",
        "",
        f"Status: `{payload['status']}`",
        "",
        f"Claim boundary: {payload['claim_boundary']}",
        "",
        "## Window Selection",
        "",
    ]
    for result in payload["evaluations"]:
        lines.append(
            f"- `{result['window_id']}`: {result['sequence_label']} indices `{result['start_index']}-{result['end_index']}` "
            f"({result['frame_count']} frames), reason: {result['selection_reason']}."
        )
    lines += [
        "",
        "## Metrics",
        "",
        "| Window | Family | Coverage | Soft alpha | Region kp raw->soft | Delta | Total delta | DROID 16f | DROID 60f | Status |",
        "|---|---|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for result in payload["evaluations"]:
        orb = result["orb_feature_sanity"]
        gate16 = next((gate for gate in result["droid_gates"] if gate["frame_limit"] == 16), None)
        gate60 = next((gate for gate in result["droid_gates"] if gate["frame_limit"] == 60), None)
        lines.append(
            f"| `{result['window_id']}` | {result['sequence_family']} | "
            f"{result['mask_summary']['mean_coverage_percent']:.6f}% | {result['mask_summary']['mean_soft_alpha_percent']:.6f}% | "
            f"{orb['raw_predicted_mask_region_keypoints']}->{orb['masked_predicted_mask_region_keypoints']} | "
            f"{orb['raw_to_masked_predicted_region_keypoint_delta']} | {orb['raw_to_masked_total_keypoint_delta']} | "
            f"{fmt_gate(gate16)} | {fmt_gate(gate60)} | `{result['status']}` |"
        )
    lines += [
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
        "## Files",
        "",
        f"- JSON: `{payload['outputs']['json']}`",
        f"- CSV: `{payload['outputs']['csv']}`",
        f"- Markdown: `{payload['outputs']['markdown']}`",
        f"- Output root: `{payload['outputs']['output_root']}`",
        "",
        "## Residual Risk",
        "",
        "- Windows remain short bounded smoke checks, not a full benchmark.",
        "- Probability maps are P225/P218 model predictions; no independent dynamic labels are introduced.",
        "- No navigation, planning, or learned persistent-map admission claim is made.",
        "- P195 remains BLOCKED.",
        "",
        "## Next Step",
        "",
        payload["next_step"],
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--require-cuda", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--neutral-tolerance-m", type=float, default=0.001)
    parser.add_argument("--orb-reverse-tolerance-fraction", type=float, default=0.05)
    parser.add_argument("--droid-timeout-seconds", type=int, default=300)
    parser.add_argument("--skip-droid", action="store_true")
    parser.add_argument("--single-window", action="store_true")
    args = parser.parse_args()

    if not args.checkpoint.exists():
        raise FileNotFoundError(args.checkpoint)
    windows = default_windows()
    if args.single_window:
        windows = windows[:1]

    command_line = " ".join([sys.executable, "tools/run_soft_boundary_multiwindow_p237.py", *sys.argv[1:]])
    evaluations = [evaluate_window(args, window) for window in windows]
    if not args.skip_droid:
        stable_candidates = [
            result
            for result in evaluations
            if result["orb_proxy_down"]
            and any(gate["frame_limit"] == 16 and gate["trajectory_neutral"] for gate in result["droid_gates"])
        ]
        if stable_candidates:
            representative = max(
                stable_candidates,
                key=lambda result: abs(result["orb_feature_sanity"]["raw_to_masked_predicted_region_keypoint_delta"]),
            )
            representative["droid_gates"].append(run_droid_gate(args, representative, 60))

    for result in evaluations:
        result["status"] = assign_window_status(result)

    orb_down_count = sum(1 for result in evaluations if result["orb_proxy_down"])
    droid_neutral_count = sum(
        1
        for result in evaluations
        if any(gate["frame_limit"] == 16 and gate["trajectory_neutral"] for gate in result["droid_gates"])
    )
    majority = len(evaluations) // 2 + 1
    expanded = orb_down_count >= majority and droid_neutral_count >= majority
    status = "expanded_bounded_support" if expanded else "mixed_bounded_support"
    if expanded:
        interpretation = (
            f"The selected P235 soft-boundary candidate reduced the ORB predicted-region proxy in {orb_down_count}/{len(evaluations)} new windows, "
            f"with DROID 16-frame neutral gates in {droid_neutral_count}/{len(evaluations)} windows. Treat this as expanded bounded frontend-module support only."
        )
        next_step = "Add more sequences and independent dynamic labels before considering any claim-boundary change; keep P195 BLOCKED."
    else:
        interpretation = (
            f"The selected P235 soft-boundary candidate is mixed across the new windows: ORB proxy down in {orb_down_count}/{len(evaluations)} and "
            f"DROID 16-frame neutral in {droid_neutral_count}/{len(evaluations)}. Treat this as bounded diagnostic evidence only."
        )
        next_step = "Diagnose failing windows before expanding the candidate; keep full-benchmark, navigation, independent-label, and map-admission claims out of scope."

    payload = {
        "artifact": "P237 soft boundary multi-window validation",
        "created": now(),
        "status": status,
        "claim_boundary": "Bounded frontend module evidence only; no full benchmark, navigation, independent-label, learned map-admission, or manuscript-body claim. P195 remains BLOCKED.",
        "selected_variant": SELECTED_VARIANT.variant_id,
        "training_route": "Reused P225/P218 SmallUNet checkpoint for probability maps; no retraining and no target-window labels were used.",
        "source_checkpoint": rel(args.checkpoint),
        "evaluations": evaluations,
        "summary_counts": {
            "window_count": len(evaluations),
            "orb_proxy_down_count": orb_down_count,
            "droid_16f_neutral_count": droid_neutral_count,
            "majority_threshold": majority,
        },
        "interpretation": interpretation,
        "next_step": next_step,
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
    print(json.dumps({"status": status, "windows": [r["window_id"] for r in evaluations], "json": rel(EVIDENCE_JSON)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
