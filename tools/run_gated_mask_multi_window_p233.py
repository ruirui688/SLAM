#!/usr/bin/env python3
"""Run P233 bounded multi-window validation for the P228 gated mask module."""

from __future__ import annotations

import argparse
import contextlib
import csv
import io
import json
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

import build_temporal_masked_sequence_p225 as p225  # noqa: E402
import apply_confidence_gated_mask_module_p228 as p228  # noqa: E402


DEFAULT_SEQUENCE = ROOT / "data/TorWIC_SLAM_Dataset/Oct. 12, 2022/Aisle_CW"
DEFAULT_CHECKPOINT = ROOT / "outputs/temporal_masked_sequence_p225/model/p225_retrained_p218_smallunet.pt"
OUTPUT_ROOT = ROOT / "outputs/gated_mask_multi_window_p233"
EVIDENCE_JSON = ROOT / "paper/evidence/gated_mask_multi_window_p233.json"
EVIDENCE_CSV = ROOT / "paper/evidence/gated_mask_multi_window_p233.csv"
EXPORT_MD = ROOT / "paper/export/gated_mask_multi_window_p233.md"


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def run_command(command: list[str], timeout_seconds: int) -> dict[str, Any]:
    start = time.time()
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
        "gated": metrics[masked_key],
        "delta_masked_minus_raw": payload.get("delta_masked_minus_raw", {}),
    }


def trajectory_neutral(metrics: dict[str, Any] | None, tolerance: float) -> bool:
    if not metrics:
        return False
    raw = metrics["raw"]
    gated = metrics["gated"]
    return (
        gated["ape_rmse_m"] <= raw["ape_rmse_m"] + tolerance
        and gated["rpe_rmse_m"] <= raw["rpe_rmse_m"] + tolerance
    )


def build_p225_window(args: argparse.Namespace, window: dict[str, Any]) -> dict[str, Any]:
    out_root = args.output_root / window["id"] / "temporal_masked_sequence_p225"
    p225.EVIDENCE_JSON = out_root / "evidence" / f"{window['id']}_temporal_masked_sequence_p225.json"
    p225.EVIDENCE_CSV = out_root / "evidence" / f"{window['id']}_temporal_masked_sequence_p225.csv"
    p225.EXPORT_MD = out_root / "evidence" / f"{window['id']}_temporal_masked_sequence_p225.md"
    p225.EVIDENCE_CSV.parent.mkdir(parents=True, exist_ok=True)
    p225_args = argparse.Namespace(
        sequence_dir=args.sequence_dir,
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
    return p225.build_sequence(p225_args)


def build_gated_pack(args: argparse.Namespace, window: dict[str, Any], p225_payload: dict[str, Any]) -> dict[str, Any]:
    win_root = args.output_root / window["id"]
    build_args = argparse.Namespace(
        source_dir=Path(p225_payload["outputs"]["package_root"]),
        sequence_output=win_root / "temporal_masked_sequence_p228_conf_gated",
        pack_output=win_root / "dynamic_slam_backend_input_pack_p228_conf_gated",
        frame_limit=None,
        probability_threshold=args.probability_threshold,
        dilation_px=args.dilation_px,
        min_component_area_px=args.min_component_area_px,
        max_coverage=args.max_coverage,
        target_coverage=args.target_coverage,
        mask_value=0,
    )
    with contextlib.redirect_stdout(io.StringIO()):
        return p228.build_outputs(build_args)


def run_smoke_and_metrics(args: argparse.Namespace, window: dict[str, Any], frame_limit: int, timeout_seconds: int) -> dict[str, Any]:
    win_root = args.output_root / window["id"]
    input_dir = win_root / "dynamic_slam_backend_input_pack_p228_conf_gated"
    output_dir = win_root / f"dynamic_slam_backend_smoke_p228_conf_gated_{frame_limit}"
    prefix = f"p233_{window['id']}_conf_gated_metrics"
    smoke_cmd = [
        sys.executable,
        "tools/run_dynamic_slam_backend_smoke.py",
        "--input-dir",
        rel(input_dir),
        "--output-dir",
        rel(output_dir),
        "--frame-limit",
        str(frame_limit),
    ]
    smoke_result = run_command(smoke_cmd, timeout_seconds)
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
            rel(input_dir),
            "--output-dir",
            rel(output_dir),
            "--artifact",
            f"P233 {frame_limit}-frame confidence-gated multi-window smoke metrics ({window['id']})",
            "--scope",
            f"P233 bounded multi-window validation: {frame_limit} frames from {window['sequence_label']} source indices {window['start_index']}-{window['start_index'] + frame_limit - 1}.",
            "--masked-label",
            "masked RGB (P228 confidence/coverage-gated P225 probability masks)",
            "--output-prefix",
            prefix,
            "--interpretation",
            "P233 bounded multi-window module validation; use only as frontend smoke/story support.",
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


def summarize_window(args: argparse.Namespace, window: dict[str, Any]) -> dict[str, Any]:
    p225_payload = build_p225_window(args, window)
    gated_manifest = build_gated_pack(args, window, p225_payload)
    orb_summary, orb_rows = p228.orb_sanity(Path(gated_manifest["output_dir"]), None)
    orb_csv = args.output_root / window["id"] / f"{window['id']}_orb_features.csv"
    p228.write_orb_csv(orb_csv, orb_rows)
    gate_16 = run_smoke_and_metrics(args, window, 16, 240)
    full = None
    if gate_16["smoke_status"] == "ok":
        full = run_smoke_and_metrics(args, window, window["frame_count"], 600)
    orb_drop = orb_summary["masked_predicted_mask_region_keypoints"] < orb_summary["raw_predicted_mask_region_keypoints"]
    status = "trajectory_neutral_orb_proxy_down" if full and full["trajectory_neutral"] and orb_drop else "mixed_or_neutral"
    return {
        "window_id": window["id"],
        "sequence_label": window["sequence_label"],
        "source_sequence_dir": rel(args.sequence_dir),
        "start_index": window["start_index"],
        "end_index": window["start_index"] + window["frame_count"] - 1,
        "frame_count": window["frame_count"],
        "selection_reason": window["selection_reason"],
        "status": status,
        "p225": {
            "json": p225_payload["outputs"]["json"],
            "csv": p225_payload["outputs"]["csv"],
            "markdown": p225_payload["outputs"]["markdown"],
            "package_root": p225_payload["outputs"]["package_root"],
            "mask_model": p225_payload["mask_model"],
            "mask_statistics": p225_payload["mask_statistics"],
        },
        "gated_pack": {
            "manifest": rel(Path(gated_manifest["output_dir"]) / "backend_input_manifest.json"),
            "output_dir": gated_manifest["output_dir"],
            "sequence_output": gated_manifest["sequence_output"],
            "module_parameters": gated_manifest["module_parameters"],
            "mask_summary": gated_manifest["mask_summary"],
        },
        "orb_feature_sanity": orb_summary | {"orb_feature_csv": rel(orb_csv)},
        "stability_gate_16_frame": gate_16,
        "full_window": full,
    }


def write_csv(path: Path, payload: dict[str, Any]) -> None:
    rows = []
    for win in payload["windows"]:
        full = win.get("full_window") or {}
        metrics = full.get("metrics") or {}
        raw = metrics.get("raw", {})
        gated = metrics.get("gated", {})
        delta = metrics.get("delta_masked_minus_raw", {})
        orb = win["orb_feature_sanity"]
        mask = win["gated_pack"]["mask_summary"]
        rows.append(
            {
                "window_id": win["window_id"],
                "sequence_label": win["sequence_label"],
                "start_index": win["start_index"],
                "end_index": win["end_index"],
                "frame_count": win["frame_count"],
                "status": win["status"],
                "mean_gated_coverage_percent": mask["mean_coverage_percent"],
                "raw_ape_rmse_m": raw.get("ape_rmse_m"),
                "gated_ape_rmse_m": gated.get("ape_rmse_m"),
                "delta_ape_rmse_m": delta.get("ape_rmse_m"),
                "raw_rpe_rmse_m": raw.get("rpe_rmse_m"),
                "gated_rpe_rmse_m": gated.get("rpe_rmse_m"),
                "delta_rpe_rmse_m": delta.get("rpe_rmse_m"),
                "raw_region_keypoints": orb["raw_predicted_mask_region_keypoints"],
                "gated_region_keypoints": orb["masked_predicted_mask_region_keypoints"],
                "region_keypoint_delta": orb["raw_to_masked_predicted_region_keypoint_delta"],
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# P233 Gated Mask Multi-Window Validation",
        "",
        f"Status: `{payload['status']}`",
        "",
        f"Claim boundary: {payload['claim_boundary']}",
        "",
        "## Window Selection",
        "",
    ]
    for win in payload["windows"]:
        lines.append(
            f"- `{win['window_id']}`: {win['sequence_label']} indices `{win['start_index']}-{win['end_index']}` "
            f"({win['frame_count']} frames), reason: {win['selection_reason']}."
        )
    lines += [
        "",
        "## Metrics",
        "",
        "| Window | Mean gated coverage | Raw APE | Gated APE | Delta APE | Raw RPE | Gated RPE | Delta RPE | Region keypoints raw->gated |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for win in payload["windows"]:
        full = win.get("full_window") or {}
        metrics = full.get("metrics") or {}
        raw = metrics.get("raw", {})
        gated = metrics.get("gated", {})
        delta = metrics.get("delta_masked_minus_raw", {})
        mask = win["gated_pack"]["mask_summary"]
        orb = win["orb_feature_sanity"]
        lines.append(
            f"| {win['window_id']} | {mask['mean_coverage_percent']:.6f}% | "
            f"{raw.get('ape_rmse_m', float('nan')):.6f} | {gated.get('ape_rmse_m', float('nan')):.6f} | {delta.get('ape_rmse_m', float('nan')):.6f} | "
            f"{raw.get('rpe_rmse_m', float('nan')):.6f} | {gated.get('rpe_rmse_m', float('nan')):.6f} | {delta.get('rpe_rmse_m', float('nan')):.6f} | "
            f"{orb['raw_predicted_mask_region_keypoints']}->{orb['masked_predicted_mask_region_keypoints']} |"
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
        "- Windows remain short bounded smokes, not a full benchmark.",
        "- Gated masks are model predictions post-processed from P225 probability maps; no independent dynamic-label claim is made.",
        "- P195 remains blocked until independent human labels exist.",
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
    parser.add_argument("--sequence-dir", type=Path, default=DEFAULT_SEQUENCE)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--require-cuda", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--neutral-tolerance-m", type=float, default=0.001)
    parser.add_argument("--probability-threshold", type=float, default=0.50)
    parser.add_argument("--dilation-px", type=int, default=1)
    parser.add_argument("--min-component-area-px", type=int, default=128)
    parser.add_argument("--max-coverage", type=float, default=0.22)
    parser.add_argument("--target-coverage", type=float, default=0.18)
    parser.add_argument("--single-window", action="store_true")
    args = parser.parse_args()

    windows = [
        {
            "id": "aisle_cw_0120_0179",
            "sequence_label": "Oct. 12, 2022 Aisle_CW",
            "start_index": 120,
            "frame_count": 60,
            "selection_reason": "same sequence as P225/P228, before and non-overlapping with source indices 480-539",
        },
        {
            "id": "aisle_cw_0840_0899",
            "sequence_label": "Oct. 12, 2022 Aisle_CW",
            "start_index": 840,
            "frame_count": 60,
            "selection_reason": "same sequence as P225/P228, after and non-overlapping with source indices 480-539",
        },
    ]
    if args.single_window:
        windows = windows[:1]

    command_line = " ".join([sys.executable, "tools/run_gated_mask_multi_window_p233.py", *sys.argv[1:]])
    results = [summarize_window(args, window) for window in windows]
    all_support = all(win["status"] == "trajectory_neutral_orb_proxy_down" for win in results)
    status = "multi_window_story_support" if all_support and len(results) > 1 else "mixed_or_neutral"
    interpretation = (
        "Across the new non-overlapping windows, the P228 confidence/coverage gate stayed within the bounded trajectory-neutral tolerance and reduced ORB keypoints inside predicted gated regions. "
        "This supports only a multi-window frontend story seed, not a full SLAM benchmark or navigation claim."
        if status == "multi_window_story_support"
        else "The multi-window evidence is mixed or incomplete. Treat P228 as bounded neutral smoke evidence and tune probability/coverage parameters before expanding claims."
    )
    payload = {
        "artifact": "P233 gated mask multi-window validation",
        "created": now(),
        "status": status,
        "claim_boundary": "Bounded multi-window frontend smoke/story support only; no full benchmark, navigation, independent-label, or learned map-admission claim. P195 remains BLOCKED.",
        "source_checkpoint": rel(args.checkpoint),
        "training_route": "Reused P225/P218 SmallUNet checkpoint; no retraining was performed.",
        "module_parameters": {
            "probability_threshold": args.probability_threshold,
            "dilation_px": args.dilation_px,
            "min_component_area_px": args.min_component_area_px,
            "max_coverage": args.max_coverage,
            "target_coverage": args.target_coverage,
        },
        "windows": results,
        "commands": [command_line],
        "interpretation": interpretation,
        "next_step": "If expanding beyond story support, add more TorWIC sequences and parameter sweeps while keeping independent-label and map-admission claims out of scope until P195 is unblocked.",
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
    print(json.dumps({"status": status, "windows": [w["window_id"] for w in results], "json": rel(EVIDENCE_JSON)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
