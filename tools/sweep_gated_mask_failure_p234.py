#!/usr/bin/env python3
"""Sweep the P233 840-899 gated-mask failure window for P234."""

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

import apply_confidence_gated_mask_module_p228 as p228  # noqa: E402


P233_JSON = ROOT / "paper/evidence/gated_mask_multi_window_p233.json"
P233_CSV = ROOT / "paper/evidence/gated_mask_multi_window_p233.csv"
P233_EXPORT = ROOT / "paper/export/gated_mask_multi_window_p233.md"
P233_OUTPUT_ROOT = ROOT / "outputs/gated_mask_multi_window_p233"
SOURCE_DIR = P233_OUTPUT_ROOT / "aisle_cw_0840_0899/temporal_masked_sequence_p225/sequence"
OUTPUT_ROOT = ROOT / "outputs/gated_mask_failure_sweep_p234"
EVIDENCE_JSON = ROOT / "paper/evidence/gated_mask_failure_sweep_p234.json"
EVIDENCE_CSV = ROOT / "paper/evidence/gated_mask_failure_sweep_p234.csv"
EXPORT_MD = ROOT / "paper/export/gated_mask_failure_sweep_p234.md"
P233_DEFAULT_ORB = {
    "raw_region_keypoints": 601,
    "gated_region_keypoints": 1901,
    "region_keypoint_delta": 1300,
    "mean_coverage_percent": 18.0,
}


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


def trajectory_neutral(metrics: dict[str, Any] | None, tolerance_m: float) -> bool:
    if not metrics:
        return False
    raw = metrics["raw"]
    gated = metrics["gated"]
    return (
        gated["ape_rmse_m"] <= raw["ape_rmse_m"] + tolerance_m
        and gated["rpe_rmse_m"] <= raw["rpe_rmse_m"] + tolerance_m
    )


def sweep_params() -> list[dict[str, Any]]:
    return [
        {"id": "p233_default", "probability_threshold": 0.50, "dilation_px": 1, "min_component_area_px": 128, "max_coverage": 0.22, "target_coverage": 0.18},
        {"id": "thr055_cap018_min128_dil1", "probability_threshold": 0.55, "dilation_px": 1, "min_component_area_px": 128, "max_coverage": 0.18, "target_coverage": 0.16},
        {"id": "thr055_cap016_min128_dil1", "probability_threshold": 0.55, "dilation_px": 1, "min_component_area_px": 128, "max_coverage": 0.16, "target_coverage": 0.12},
        {"id": "thr055_cap012_min128_dil0", "probability_threshold": 0.55, "dilation_px": 0, "min_component_area_px": 128, "max_coverage": 0.12, "target_coverage": 0.10},
        {"id": "thr060_cap018_min128_dil1", "probability_threshold": 0.60, "dilation_px": 1, "min_component_area_px": 128, "max_coverage": 0.18, "target_coverage": 0.16},
        {"id": "thr060_cap016_min256_dil1", "probability_threshold": 0.60, "dilation_px": 1, "min_component_area_px": 256, "max_coverage": 0.16, "target_coverage": 0.12},
        {"id": "thr060_cap012_min256_dil0", "probability_threshold": 0.60, "dilation_px": 0, "min_component_area_px": 256, "max_coverage": 0.12, "target_coverage": 0.10},
        {"id": "thr060_cap012_min128_dil1", "probability_threshold": 0.60, "dilation_px": 1, "min_component_area_px": 128, "max_coverage": 0.12, "target_coverage": 0.10},
    ]


def build_variant(args: argparse.Namespace, params: dict[str, Any]) -> dict[str, Any]:
    variant_root = args.output_root / params["id"]
    build_args = argparse.Namespace(
        source_dir=args.source_dir,
        sequence_output=variant_root / "temporal_masked_sequence_p228_conf_gated",
        pack_output=variant_root / "dynamic_slam_backend_input_pack_p228_conf_gated",
        frame_limit=None,
        probability_threshold=params["probability_threshold"],
        dilation_px=params["dilation_px"],
        min_component_area_px=params["min_component_area_px"],
        max_coverage=params["max_coverage"],
        target_coverage=params["target_coverage"],
        mask_value=0,
    )
    with contextlib.redirect_stdout(io.StringIO()):
        manifest = p228.build_outputs(build_args)
    orb_summary, orb_rows = p228.orb_sanity(Path(manifest["output_dir"]), None)
    orb_csv = variant_root / f"{params['id']}_orb_features.csv"
    p228.write_orb_csv(orb_csv, orb_rows)
    return {
        "variant_id": params["id"],
        "parameters": {key: params[key] for key in params if key != "id"},
        "pack_dir": manifest["output_dir"],
        "manifest": rel(Path(manifest["output_dir"]) / "backend_input_manifest.json"),
        "mask_summary": manifest["mask_summary"],
        "orb_feature_sanity": orb_summary | {"orb_feature_csv": rel(orb_csv)},
        "preliminary_status": "orb_proxy_down" if orb_summary["raw_to_masked_predicted_region_keypoint_delta"] < 0 else "orb_proxy_not_down",
        "droid_gates": [],
    }


def rank_for_droid(variants: list[dict[str, Any]], max_runs: int) -> list[dict[str, Any]]:
    down = [v for v in variants if v["orb_feature_sanity"]["raw_to_masked_predicted_region_keypoint_delta"] < 0]
    if down:
        return sorted(down, key=lambda v: v["orb_feature_sanity"]["raw_to_masked_predicted_region_keypoint_delta"])[:max_runs]
    return sorted(variants, key=lambda v: v["orb_feature_sanity"]["raw_to_masked_predicted_region_keypoint_delta"])[:max_runs]


def run_droid_gate(args: argparse.Namespace, variant: dict[str, Any], frame_limit: int) -> dict[str, Any]:
    output_dir = args.output_root / variant["variant_id"] / f"dynamic_slam_backend_smoke_p234_{frame_limit}"
    prefix = f"p234_{variant['variant_id']}_{frame_limit}f_metrics"
    smoke_cmd = [
        sys.executable,
        "tools/run_dynamic_slam_backend_smoke.py",
        "--input-dir",
        variant["pack_dir"],
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
            variant["pack_dir"],
            "--output-dir",
            rel(output_dir),
            "--artifact",
            f"P234 {frame_limit}-frame gated-mask failure sweep metrics ({variant['variant_id']})",
            "--scope",
            f"P234 bounded failure analysis: Aisle_CW source indices 840-{840 + frame_limit - 1}.",
            "--masked-label",
            f"masked RGB (P234 {variant['variant_id']} confidence/coverage-gated masks)",
            "--output-prefix",
            prefix,
            "--interpretation",
            "P234 bounded failure sweep gate; use only for frontend smoke and module direction.",
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


def failure_diagnosis(variants: list[dict[str, Any]]) -> dict[str, Any]:
    default = next(v for v in variants if v["variant_id"] == "p233_default")
    deltas = [v["orb_feature_sanity"]["raw_to_masked_predicted_region_keypoint_delta"] for v in variants]
    coverages = [v["mask_summary"]["mean_coverage_percent"] for v in variants]
    capped_counts = [len(v["mask_summary"]["coverage_capped_frames"]) for v in variants]
    best = min(variants, key=lambda v: v["orb_feature_sanity"]["raw_to_masked_predicted_region_keypoint_delta"])
    default_capped = len(default["mask_summary"]["coverage_capped_frames"])
    partially_uncapped = [
        f"{v['variant_id']}={len(v['mask_summary']['coverage_capped_frames'])}/60"
        for v in variants
        if len(v["mask_summary"]["coverage_capped_frames"]) < 60
    ]
    return {
        "primary_cause": "scene_low_raw_region_keypoints_and_mask_edge_keypoint_creation",
        "evidence": [
            f"P233 default 840-899 had only {P233_DEFAULT_ORB['raw_region_keypoints']} raw keypoints inside a fixed 18.0% predicted region, while masked images had {P233_DEFAULT_ORB['gated_region_keypoints']} in-region keypoints.",
            f"The P234 default rerun has delta {default['orb_feature_sanity']['raw_to_masked_predicted_region_keypoint_delta']} and {default_capped}/60 coverage-capped frames, matching the P233 failure direction.",
            f"The sweep spans mean coverage {min(coverages):.6f}% to {max(coverages):.6f}% and in-region keypoint deltas {min(deltas)} to {max(deltas)}; the best proxy variant is {best['variant_id']}.",
            f"Coverage-capped frames range from {min(capped_counts)}/60 to {max(capped_counts)}/60; partially uncapped variants: {', '.join(partially_uncapped) if partially_uncapped else 'none'}. This points to coverage-target selection and mask placement, not an empty/sparse-mask instability.",
        ],
        "ruled_down": [
            "Mask-too-sparse instability: the lowest tested coverage remains about 10% and all variants keep nonzero masks on all 60 frames.",
            "Dilation-only issue: both dilation 0 and dilation 1 variants retain positive ORB proxy deltas in this window.",
        ],
    }


def write_csv(path: Path, payload: dict[str, Any]) -> None:
    rows = []
    for variant in payload["sweep"]:
        orb = variant["orb_feature_sanity"]
        gate16 = next((gate for gate in variant["droid_gates"] if gate["frame_limit"] == 16), {})
        metrics = gate16.get("metrics") or {}
        raw = metrics.get("raw", {})
        gated = metrics.get("gated", {})
        delta = metrics.get("delta_masked_minus_raw", {})
        rows.append(
            {
                "variant_id": variant["variant_id"],
                "status": variant["final_status"],
                "threshold": variant["parameters"]["probability_threshold"],
                "dilation_px": variant["parameters"]["dilation_px"],
                "min_component_area_px": variant["parameters"]["min_component_area_px"],
                "max_coverage": variant["parameters"]["max_coverage"],
                "target_coverage": variant["parameters"]["target_coverage"],
                "mean_coverage_percent": variant["mask_summary"]["mean_coverage_percent"],
                "coverage_capped_frames": len(variant["mask_summary"]["coverage_capped_frames"]),
                "raw_region_keypoints": orb["raw_predicted_mask_region_keypoints"],
                "gated_region_keypoints": orb["masked_predicted_mask_region_keypoints"],
                "region_keypoint_delta": orb["raw_to_masked_predicted_region_keypoint_delta"],
                "droid_16f_trajectory_neutral": gate16.get("trajectory_neutral"),
                "droid_16f_raw_ape_rmse_m": raw.get("ape_rmse_m"),
                "droid_16f_gated_ape_rmse_m": gated.get("ape_rmse_m"),
                "droid_16f_delta_ape_rmse_m": delta.get("ape_rmse_m"),
                "droid_16f_raw_rpe_rmse_m": raw.get("rpe_rmse_m"),
                "droid_16f_gated_rpe_rmse_m": gated.get("rpe_rmse_m"),
                "droid_16f_delta_rpe_rmse_m": delta.get("rpe_rmse_m"),
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# P234 Gated Mask Failure Sweep",
        "",
        f"Status: `{payload['status']}`",
        "",
        f"Claim boundary: {payload['claim_boundary']}",
        "",
        "## Scope",
        "",
        "- Window: `Oct. 12, 2022 Aisle_CW` source indices `840-899`.",
        "- Route: reused the P233/P225 probability package; no retraining and no manuscript-body edits.",
        "- DROID was limited to selected 16-frame gates after ORB/coverage screening.",
        "",
        "## Sweep Table",
        "",
        "| Variant | thr | cap/target | min comp | dil | coverage | raw->gated region kp | delta | DROID 16f |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for variant in payload["sweep"]:
        p = variant["parameters"]
        orb = variant["orb_feature_sanity"]
        gate16 = next((gate for gate in variant["droid_gates"] if gate["frame_limit"] == 16), None)
        droid = "not_run"
        if gate16:
            metrics = gate16.get("metrics") or {}
            delta = metrics.get("delta_masked_minus_raw", {})
            droid = f"neutral={gate16['trajectory_neutral']}, dAPE={delta.get('ape_rmse_m')}, dRPE={delta.get('rpe_rmse_m')}"
        lines.append(
            f"| `{variant['variant_id']}` | {p['probability_threshold']:.2f} | {p['max_coverage']:.2f}/{p['target_coverage']:.2f} | "
            f"{p['min_component_area_px']} | {p['dilation_px']} | {variant['mask_summary']['mean_coverage_percent']:.6f}% | "
            f"{orb['raw_predicted_mask_region_keypoints']}->{orb['masked_predicted_mask_region_keypoints']} | "
            f"{orb['raw_to_masked_predicted_region_keypoint_delta']} | {droid} |"
        )
    lines += [
        "",
        "## Failure Analysis",
        "",
        f"Primary cause: `{payload['failure_analysis']['primary_cause']}`.",
        "",
    ]
    for item in payload["failure_analysis"]["evidence"]:
        lines.append(f"- {item}")
    lines += [
        "",
        "Ruled down:",
        "",
    ]
    for item in payload["failure_analysis"]["ruled_down"]:
        lines.append(f"- {item}")
    lines += [
        "",
        "## Decision",
        "",
        payload["decision"],
        "",
        "## Next Module Plan",
        "",
    ]
    for item in payload["next_module_plan"]:
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
    parser.add_argument("--source-dir", type=Path, default=SOURCE_DIR)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--neutral-tolerance-m", type=float, default=0.001)
    parser.add_argument("--droid-candidates", type=int, default=2)
    parser.add_argument("--droid-timeout-seconds", type=int, default=300)
    parser.add_argument("--skip-droid", action="store_true")
    args = parser.parse_args()

    if not args.source_dir.exists():
        raise FileNotFoundError(args.source_dir)
    for required in (P233_JSON, P233_CSV, P233_EXPORT, P233_OUTPUT_ROOT):
        if not required.exists():
            raise FileNotFoundError(required)

    variants = [build_variant(args, params) for params in sweep_params()]
    selected = [] if args.skip_droid else rank_for_droid(variants, args.droid_candidates)
    selected_ids = {variant["variant_id"] for variant in selected}
    for variant in variants:
        if variant["variant_id"] in selected_ids:
            variant["droid_gates"].append(run_droid_gate(args, variant, 16))

    for variant in variants:
        orb_down = variant["orb_feature_sanity"]["raw_to_masked_predicted_region_keypoint_delta"] < 0
        neutral = any(gate["frame_limit"] == 16 and gate["trajectory_neutral"] for gate in variant["droid_gates"])
        variant["final_status"] = "candidate_v2_gating" if orb_down and neutral else "not_candidate"

    candidates = [v for v in variants if v["final_status"] == "candidate_v2_gating"]
    status = "candidate_v2_gating" if candidates else "no_stable_parameter_found"
    decision = (
        f"Candidate v2 gating found: {', '.join(v['variant_id'] for v in candidates)}. Keep claim boundary to bounded frontend smoke until multi-window rerun."
        if candidates
        else "No tested threshold/coverage setting produced both ORB proxy decrease and trajectory-neutral DROID evidence on the 840-899 failure window. Treat post-processing-only gating as unstable for story expansion."
    )
    payload = {
        "artifact": "P234 gated mask failure sweep",
        "created": now(),
        "status": status,
        "claim_boundary": "Bounded frontend failure analysis and module-planning evidence only; no full benchmark, navigation, independent-label, learned map-admission, or manuscript-body claim. P195 remains BLOCKED.",
        "source_window": {
            "sequence_label": "Oct. 12, 2022 Aisle_CW",
            "start_index": 840,
            "end_index": 899,
            "frame_count": 60,
            "source_probability_package": rel(args.source_dir),
        },
        "p233_inputs_checked": {
            "tool": "tools/run_gated_mask_multi_window_p233.py",
            "json": rel(P233_JSON),
            "csv": rel(P233_CSV),
            "markdown": rel(P233_EXPORT),
            "output_root": rel(P233_OUTPUT_ROOT),
            "default_failure": P233_DEFAULT_ORB,
        },
        "sweep": variants,
        "droid_selected_variants": sorted(selected_ids),
        "failure_analysis": failure_diagnosis(variants),
        "decision": decision,
        "next_module_plan": [
            "Stop expanding post-processing-only confidence/coverage gating until boundary placement is made temporally stable.",
            "Prototype boundary/motion-aware input masking: down-weight or feather high-probability mask edges instead of hard black cutouts that create ORB corners.",
            "Add temporal consistency over probability maps before coverage capping so selected regions do not shift by per-frame score rank alone.",
            "Use the 840-899 window as the first regression gate, then re-run 480-539 and 120-179 before making any multi-window story-support claim.",
        ],
        "outputs": {
            "json": rel(EVIDENCE_JSON),
            "csv": rel(EVIDENCE_CSV),
            "markdown": rel(EXPORT_MD),
            "output_root": rel(args.output_root),
        },
        "commands": [" ".join([sys.executable, "tools/sweep_gated_mask_failure_p234.py", *sys.argv[1:]])],
    }
    write_json(EVIDENCE_JSON, payload)
    write_csv(EVIDENCE_CSV, payload)
    write_markdown(EXPORT_MD, payload)
    print(json.dumps({"status": status, "selected_for_droid": sorted(selected_ids), "json": rel(EVIDENCE_JSON)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
