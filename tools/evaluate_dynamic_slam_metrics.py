#!/usr/bin/env python3
"""Evaluate raw-vs-masked DROID-SLAM trajectories with evo."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "outputs" / "dynamic_slam_backend_input_pack_64"
DEFAULT_OUTPUT = ROOT / "outputs" / "dynamic_slam_backend_smoke_p134_64_global_ba"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def parse_evo_stats(stdout: str) -> dict[str, float]:
    stats: dict[str, float] = {}
    for line in stdout.splitlines():
        match = re.match(r"\s*(max|mean|median|min|rmse|sse|std)\s+([0-9.eE+-]+)\s*$", line)
        if match:
            stats[match.group(1)] = float(match.group(2))
    missing = {"rmse", "mean"} - stats.keys()
    if missing:
        raise RuntimeError(f"Could not parse evo statistics {sorted(missing)} from:\n{stdout}")
    return stats


def run_evo(kind: str, gt: Path, estimate: Path) -> dict[str, float]:
    command = [f"evo_{kind}", "tum", str(gt), str(estimate), "--align", "--correct_scale"]
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=True)
    return parse_evo_stats(completed.stdout)


def mask_coverage(manifest_path: Path) -> dict:
    if not manifest_path.exists():
        return {}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    frames = manifest.get("frames", [])
    nonzero = [frame for frame in frames if frame.get("mask_pixels", 0) > 0]
    total = max(len(frames), 1)
    return {
        "masked_frames": [frame["frame_index"] for frame in nonzero],
        "masked_frame_count": len(nonzero),
        "total_frames": len(frames),
        "nonzero_frame_coverage_percent": {
            f"{frame['frame_index']:06d}": round(frame["coverage_ratio"] * 100.0, 6)
            for frame in nonzero
        },
        "mean_coverage_percent": round(
            sum(frame.get("coverage_ratio", 0.0) for frame in frames) * 100.0 / total,
            6,
        ),
        "policy": manifest.get("dynamic_mask_policy"),
        "temporal_propagation_radius": manifest.get("temporal_propagation_radius"),
        "dynamic_mask_dilation_px": manifest.get("dynamic_mask_dilation_px"),
    }


def write_markdown(path: Path, payload: dict) -> None:
    metrics = payload["metrics"]
    coverage = payload["mask_coverage"]
    lines = [
        f"# {payload['artifact']}",
        "",
        f"Scope: {payload['scope']}",
        "",
        "| Input | APE RMSE (m) | APE mean (m) | RPE RMSE (m) | RPE mean (m) |",
        "|---|---:|---:|---:|---:|",
    ]
    for label, values in metrics.items():
        lines.append(
            f"| {label} | {values['ape_rmse_m']:.6f} | {values['ape_mean_m']:.6f} | "
            f"{values['rpe_rmse_m']:.6f} | {values['rpe_mean_m']:.6f} |"
        )
    if "delta_masked_minus_raw" in payload:
        delta = payload["delta_masked_minus_raw"]
        lines += [
            "",
            f"Delta masked-minus-raw: APE RMSE `{delta['ape_rmse_m']:.6f} m`, "
            f"RPE RMSE `{delta['rpe_rmse_m']:.6f} m`.",
        ]
    if coverage:
        lines += [
            "",
            "Mask coverage:",
            "",
            f"- Masked frames: `{coverage['masked_frame_count']}/{coverage['total_frames']}`.",
            f"- Mean coverage: `{coverage['mean_coverage_percent']:.6f}%`.",
            f"- Temporal propagation radius: `{coverage.get('temporal_propagation_radius')}`.",
            f"- Mask dilation: `{coverage.get('dynamic_mask_dilation_px')}` px.",
        ]
    lines += ["", f"Interpretation: {payload['interpretation']}", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--artifact", default="Dynamic SLAM raw-vs-masked metrics")
    parser.add_argument("--scope", default="Bounded TorWIC DROID-SLAM raw-vs-masked run.")
    parser.add_argument("--masked-label", default="masked RGB")
    parser.add_argument("--output-prefix", default="dynamic_slam_metrics")
    parser.add_argument(
        "--interpretation",
        default="Raw and masked trajectories should be interpreted with the declared mask coverage and claim boundary.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    gt = args.input_dir / "groundtruth.txt"
    raw = args.output_dir / "raw_estimate_tum.txt"
    masked = args.output_dir / "masked_estimate_tum.txt"
    raw_ape = run_evo("ape", gt, raw)
    raw_rpe = run_evo("rpe", gt, raw)
    masked_ape = run_evo("ape", gt, masked)
    masked_rpe = run_evo("rpe", gt, masked)
    payload = {
        "artifact": args.artifact,
        "created": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "scope": args.scope,
        "claim_boundary": "Metrics report bounded backend behavior only; they do not by themselves prove navigation benefit or full-map quality improvement.",
        "inputs": {
            "groundtruth": rel(gt),
            "raw_estimate": rel(raw),
            "masked_estimate": rel(masked),
        },
        "mask_coverage": mask_coverage(args.input_dir / "backend_input_manifest.json"),
        "metrics": {
            "raw RGB": {
                "ape_rmse_m": raw_ape["rmse"],
                "ape_mean_m": raw_ape["mean"],
                "rpe_rmse_m": raw_rpe["rmse"],
                "rpe_mean_m": raw_rpe["mean"],
            },
            args.masked_label: {
                "ape_rmse_m": masked_ape["rmse"],
                "ape_mean_m": masked_ape["mean"],
                "rpe_rmse_m": masked_rpe["rmse"],
                "rpe_mean_m": masked_rpe["mean"],
            },
        },
        "delta_masked_minus_raw": {
            "ape_rmse_m": masked_ape["rmse"] - raw_ape["rmse"],
            "rpe_rmse_m": masked_rpe["rmse"] - raw_rpe["rmse"],
        },
        "interpretation": args.interpretation,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / f"{args.output_prefix}.json"
    md_path = args.output_dir / f"{args.output_prefix}.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(md_path, payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
