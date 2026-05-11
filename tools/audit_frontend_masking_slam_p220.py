#!/usr/bin/env python3
"""P220 bounded front-end masking SLAM feasibility audit.

This script audits the local P219 raw-vs-P218-masked sample package, probes
local OpenCV/SLAM runtime availability, and computes a deterministic ORB
feature proxy when OpenCV is available. It does not train, download data, touch
raw data, or use admission-control labels.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
P219_MANIFEST = ROOT / "outputs/frontend_masking_eval_p219/frontend_masking_eval_manifest.json"
P219_JSON = ROOT / "paper/evidence/frontend_masking_eval_p219.json"
P218_JSON = ROOT / "paper/evidence/dynamic_mask_training_p218.json"
P195_JSON = ROOT / "paper/evidence/independent_supervision_gate_p195.json"
EVIDENCE_JSON = ROOT / "paper/evidence/frontend_masking_slam_smoke_p220.json"
EVIDENCE_CSV = ROOT / "paper/evidence/frontend_masking_slam_smoke_p220.csv"
EXPORT_MD = ROOT / "paper/export/frontend_masking_slam_smoke_p220.md"

TRAM_PYTHON = Path("/home/rui/miniconda3/envs/tram/bin/python")
TRAM_LD = "/home/rui/miniconda3/envs/tram/lib"
DROID_ROOT = Path("/home/rui/tram/thirdparty/DROID-SLAM")
DROID_WEIGHTS = Path("/home/rui/tram/data/pretrain/droid.pth")
ORB_WRAPPER = ROOT / "tools/orb_slam3_wrapper.sh"
ORB_HEADLESS = ROOT / "tools/orb_slam3_headless"
ORB_SOURCE = ROOT / "tools/orb_slam3_headless_runner.cc"
ORB_VOCAB = ROOT / "thirdparty/ORB_SLAM3/Vocabulary/ORBvoc.txt"
ORB_CAMERA_YAML = ROOT / "outputs/orb_slam3_p173_recovery/TorWIC_mono_left.yaml"

PROHIBITED_LABEL_TOKENS = (
    "target_admit",
    "current_weak_label",
    "selection_v5",
    "model_prediction",
    "model_pred",
    "model_probability",
    "model_prob",
    "human_admit_label",
    "human_same_object_label",
)


def rel(path: Path | str | None) -> str | None:
    if path is None:
        return None
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_probe(command: list[str], timeout: int = 10, env: dict[str, str] | None = None) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "status": "ok" if proc.returncode == 0 else "error",
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "timeout",
            "returncode": None,
            "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "").strip() if isinstance(exc.stderr, str) else "",
            "error": f"timeout after {timeout}s",
        }
    except Exception as exc:
        return {"status": "error", "returncode": None, "stdout": "", "stderr": "", "error": f"{type(exc).__name__}: {exc}"}


def cv2_probe(python_exe: Path | str, env: dict[str, str] | None = None) -> dict[str, Any]:
    code = (
        "import json, sys\n"
        "try:\n"
        " import cv2\n"
        " print(json.dumps({'available': True, 'python': sys.executable, 'version': cv2.__version__, "
        "'has_orb_create': hasattr(cv2, 'ORB_create')}))\n"
        "except Exception as exc:\n"
        " print(json.dumps({'available': False, 'python': sys.executable, 'error': type(exc).__name__ + ': ' + str(exc)}))\n"
        " raise\n"
    )
    probe = run_probe([str(python_exe), "-c", code], timeout=10, env=env)
    parsed: dict[str, Any] = {}
    if probe.get("stdout"):
        for line in reversed(probe["stdout"].splitlines()):
            try:
                parsed = json.loads(line)
                break
            except json.JSONDecodeError:
                continue
    if not parsed:
        parsed = {"available": False, "python": str(python_exe)}
    if probe["status"] != "ok":
        stderr_tail = probe.get("stderr", "").splitlines()[-1:] or []
        error = parsed.get("error") or probe.get("error") or (stderr_tail[0] if stderr_tail else "opencv probe failed")
        parsed["available"] = False
        parsed["error"] = error
        if probe.get("stderr"):
            parsed["stderr_tail"] = probe["stderr"].splitlines()[-3:]
    parsed["probe_status"] = probe["status"]
    parsed["returncode"] = probe["returncode"]
    return parsed


def p195_status() -> dict[str, Any]:
    payload = read_json(P195_JSON) if P195_JSON.exists() else {}
    audit = payload.get("label_audit", {}) if isinstance(payload, dict) else {}
    boundary = audit.get("boundary_review") or audit.get("boundary") or {}
    pairs = audit.get("association_pairs") or audit.get("pairs") or {}
    boundary_valid = int(boundary.get("valid_human_admit_label_count", boundary.get("valid", 0)) or 0)
    pair_valid = int(pairs.get("valid_human_same_object_label_count", pairs.get("valid", 0)) or 0)
    return {
        "status": payload.get("status", "unknown") if isinstance(payload, dict) else "unknown",
        "human_labels_blank": boundary_valid == 0 and pair_valid == 0,
        "boundary_total": boundary.get("total"),
        "boundary_blank": boundary.get("blank"),
        "boundary_valid_human_admit_label_count": boundary_valid,
        "pair_total": pairs.get("total"),
        "pair_blank": pairs.get("blank"),
        "pair_valid_human_same_object_label_count": pair_valid,
    }


def sample_input_audit(samples: list[dict[str, Any]]) -> dict[str, Any]:
    required = ("raw_image_path", "masked_image_path", "gt_binary_mask_path", "predicted_mask_fullres_path")
    rows = []
    for sample in samples:
        row = {"sample_id": sample["sample_id"]}
        for key in required:
            value = sample.get(key)
            row[f"{key}_exists"] = bool(value and (ROOT / value).exists())
        raw = ROOT / sample["raw_image_path"]
        with Image.open(raw) as img:
            row["width"], row["height"] = img.size
        rows.append(row)
    return {
        "sample_count": len(samples),
        "all_required_images_and_masks_present": all(
            all(row[f"{key}_exists"] for key in required) for row in rows
        ),
        "per_sample": rows,
        "trajectory_inputs_for_p219_samples": {
            "calibration": "absent_in_p219_package",
            "timestamps": "absent_in_p219_package",
            "trajectory_groundtruth": "absent_in_p219_package",
            "note": "P219 contains held-out frame/mask samples, not a temporally aligned SLAM sequence.",
        },
    }


def count_orb_with_current_python(manifest_path: Path) -> dict[str, Any]:
    import cv2  # type: ignore
    import numpy as np

    manifest = read_json(manifest_path)
    rows = []
    for sample in manifest["samples"]:
        raw_path = ROOT / sample["raw_image_path"]
        masked_path = ROOT / sample["masked_image_path"]
        gt_path = ROOT / sample["gt_binary_mask_path"]
        raw = cv2.imread(str(raw_path), cv2.IMREAD_GRAYSCALE)
        masked = cv2.imread(str(masked_path), cv2.IMREAD_GRAYSCALE)
        gt = cv2.imread(str(gt_path), cv2.IMREAD_GRAYSCALE)
        if raw is None or masked is None or gt is None:
            raise FileNotFoundError(f"Could not read raw/masked/gt for {sample['sample_id']}")
        gt_bool = gt > 0
        orb = cv2.ORB_create(nfeatures=2000)
        raw_kp = orb.detect(raw, None) or []
        masked_kp = orb.detect(masked, None) or []

        def in_mask(keypoints: list[Any]) -> int:
            h, w = gt_bool.shape
            count = 0
            for kp in keypoints:
                x = int(round(kp.pt[0]))
                y = int(round(kp.pt[1]))
                if 0 <= x < w and 0 <= y < h and bool(gt_bool[y, x]):
                    count += 1
            return count

        raw_dyn = in_mask(raw_kp)
        masked_dyn = in_mask(masked_kp)
        rows.append(
            {
                "sample_id": sample["sample_id"],
                "split": sample["split"],
                "raw_keypoints_total": len(raw_kp),
                "masked_keypoints_total": len(masked_kp),
                "raw_keypoints_in_gt_dynamic": raw_dyn,
                "masked_keypoints_in_gt_dynamic": masked_dyn,
                "total_keypoint_delta": len(masked_kp) - len(raw_kp),
                "total_keypoint_reduction_rate": (len(raw_kp) - len(masked_kp)) / len(raw_kp) if raw_kp else 0.0,
                "gt_dynamic_keypoint_reduction_rate": (raw_dyn - masked_dyn) / raw_dyn if raw_dyn else 0.0,
            }
        )
    return {
        "status": "ok",
        "python": sys.executable,
        "cv2_version": cv2.__version__,
        "samples": rows,
        "summary": summarize_orb(rows),
    }


def summarize_orb(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    raw_total = sum(int(r["raw_keypoints_total"]) for r in rows)
    masked_total = sum(int(r["masked_keypoints_total"]) for r in rows)
    raw_dyn = sum(int(r["raw_keypoints_in_gt_dynamic"]) for r in rows)
    masked_dyn = sum(int(r["masked_keypoints_in_gt_dynamic"]) for r in rows)
    return {
        "sample_count": len(rows),
        "raw_keypoints_total": raw_total,
        "masked_keypoints_total": masked_total,
        "total_keypoint_delta": masked_total - raw_total,
        "total_keypoint_reduction_rate": round((raw_total - masked_total) / raw_total, 6) if raw_total else 0.0,
        "raw_keypoints_in_gt_dynamic": raw_dyn,
        "masked_keypoints_in_gt_dynamic": masked_dyn,
        "gt_dynamic_keypoint_delta": masked_dyn - raw_dyn,
        "gt_dynamic_keypoint_reduction_rate": round((raw_dyn - masked_dyn) / raw_dyn, 6) if raw_dyn else 0.0,
    }


def run_orb_proxy(default_cv2: dict[str, Any], tram_cv2: dict[str, Any]) -> dict[str, Any]:
    if default_cv2.get("available") and default_cv2.get("has_orb_create"):
        return count_orb_with_current_python(P219_MANIFEST)
    if tram_cv2.get("available") and tram_cv2.get("has_orb_create") and TRAM_PYTHON.exists():
        env = os.environ.copy()
        env["LD_LIBRARY_PATH"] = f"{TRAM_LD}:{env.get('LD_LIBRARY_PATH', '')}"
        proc = run_probe(
            [str(TRAM_PYTHON), str(Path(__file__).resolve()), "--orb-worker", str(P219_MANIFEST)],
            timeout=20,
            env=env,
        )
        if proc["status"] == "ok":
            try:
                return json.loads(proc["stdout"].splitlines()[-1])
            except Exception as exc:
                return {"status": "failed", "error": f"could not parse tram ORB worker output: {type(exc).__name__}: {exc}", "probe": proc}
        return {"status": "failed", "error": "tram ORB worker failed", "probe": proc}
    return {
        "status": "blocked",
        "error": "OpenCV ORB unavailable in default Python and tram Python",
        "default_opencv_error": default_cv2.get("error"),
        "tram_opencv_error": tram_cv2.get("error"),
    }


def backend_audit() -> dict[str, Any]:
    backend_packs = []
    for manifest_path in sorted((ROOT / "outputs").glob("dynamic_slam_backend_input_pack*/backend_input_manifest.json")):
        pack_dir = manifest_path.parent
        raw_rgb = pack_dir / "raw/rgb.txt"
        masked_rgb = pack_dir / "masked/rgb.txt"
        gt = pack_dir / "groundtruth.txt"
        frame_count = 0
        if raw_rgb.exists():
            frame_count = len([line for line in raw_rgb.read_text(encoding="utf-8").splitlines() if line.strip()])
        backend_packs.append(
            {
                "manifest": rel(manifest_path),
                "frame_count": frame_count,
                "raw_rgb": raw_rgb.exists(),
                "masked_rgb": masked_rgb.exists(),
                "groundtruth": gt.exists(),
            }
        )
    smallest = min(backend_packs, key=lambda item: item["frame_count"]) if backend_packs else None
    return {
        "orb_slam3": {
            "wrapper_exists": ORB_WRAPPER.exists(),
            "wrapper_readable": os.access(ORB_WRAPPER, os.R_OK),
            "headless_exists": ORB_HEADLESS.exists(),
            "headless_executable": os.access(ORB_HEADLESS, os.X_OK),
            "headless_source_exists": ORB_SOURCE.exists(),
            "vocabulary_exists": ORB_VOCAB.exists(),
            "camera_yaml_exists": ORB_CAMERA_YAML.exists(),
            "smoke_status": "not_run",
            "smoke_reason": "Existing wrapper expects a temporal sequence directory and writes inside the input session; P219 is a six-frame held-out package without timestamps/trajectory, so P220 did not force an ORB-SLAM3 trajectory run.",
        },
        "droid": {
            "root_exists": DROID_ROOT.exists(),
            "weights_exists": DROID_WEIGHTS.exists(),
            "backend_packs_found": len(backend_packs),
            "smallest_backend_pack": smallest,
            "smoke_status": "not_run",
            "smoke_reason": "DROID runtime and prior backend packs exist, but P219 samples are not a SLAM sequence and running DROID even on prior packs would not be raw-vs-P218-masked; bounded P220 records availability only.",
        },
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = [
        "sample_id",
        "split",
        "raw_keypoints_total",
        "masked_keypoints_total",
        "total_keypoint_delta",
        "total_keypoint_reduction_rate",
        "raw_keypoints_in_gt_dynamic",
        "masked_keypoints_in_gt_dynamic",
        "gt_dynamic_keypoint_delta",
        "gt_dynamic_keypoint_reduction_rate",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["gt_dynamic_keypoint_delta"] = int(row["masked_keypoints_in_gt_dynamic"]) - int(row["raw_keypoints_in_gt_dynamic"])
            writer.writerow({key: out.get(key, "") for key in columns})


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    orb = payload["orb_proxy"]
    orb_summary = orb.get("summary", {})
    p195 = payload["p195_status"]
    lines = [
        "# P220 Front-End Masking SLAM Feasibility Smoke",
        "",
        f"**Status:** {payload['status']}",
        "",
        "## Boundary",
        "",
        payload["claim_boundary"],
        "",
        "## Availability",
        "",
        f"- Default Python OpenCV: `{payload['availability']['opencv_default'].get('available')}`"
        f" (`{payload['availability']['opencv_default'].get('error', payload['availability']['opencv_default'].get('version', ''))}`)",
        f"- tram OpenCV: `{payload['availability']['opencv_tram'].get('available')}`"
        f" (`{payload['availability']['opencv_tram'].get('error', payload['availability']['opencv_tram'].get('version', ''))}`)",
        f"- ORB-SLAM3 wrapper/headless/vocab/camera: `{payload['availability']['backend']['orb_slam3']['wrapper_exists']}` / "
        f"`{payload['availability']['backend']['orb_slam3']['headless_exists']}` / "
        f"`{payload['availability']['backend']['orb_slam3']['vocabulary_exists']}` / "
        f"`{payload['availability']['backend']['orb_slam3']['camera_yaml_exists']}`",
        f"- DROID root/weights: `{payload['availability']['backend']['droid']['root_exists']}` / "
        f"`{payload['availability']['backend']['droid']['weights_exists']}`",
        "",
        "## P219 Input Audit",
        "",
        f"- Samples: `{payload['p219_input_audit']['sample_count']}`",
        f"- Required images/masks present: `{payload['p219_input_audit']['all_required_images_and_masks_present']}`",
        "- SLAM timestamps/calibration/trajectory for P219 samples: absent; P219 is a held-out frame/mask package, not a sequence.",
        "",
        "## ORB Feature Proxy",
        "",
        f"- Status: `{orb.get('status')}`",
    ]
    if orb_summary:
        lines.extend(
            [
                f"- Raw keypoints total: `{orb_summary['raw_keypoints_total']}`",
                f"- Masked keypoints total: `{orb_summary['masked_keypoints_total']}`",
                f"- Total keypoint reduction: `{orb_summary['total_keypoint_reduction_rate']}`",
                f"- Raw keypoints in GT dynamic regions: `{orb_summary['raw_keypoints_in_gt_dynamic']}`",
                f"- Masked keypoints in GT dynamic regions: `{orb_summary['masked_keypoints_in_gt_dynamic']}`",
                f"- GT-dynamic keypoint reduction: `{orb_summary['gt_dynamic_keypoint_reduction_rate']}`",
                "",
                "| sample | raw kp | masked kp | raw dyn kp | masked dyn kp | dyn reduction |",
                "| --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in orb.get("samples", []):
            lines.append(
                f"| `{row['sample_id']}` | `{row['raw_keypoints_total']}` | `{row['masked_keypoints_total']}` | "
                f"`{row['raw_keypoints_in_gt_dynamic']}` | `{row['masked_keypoints_in_gt_dynamic']}` | "
                f"`{row['gt_dynamic_keypoint_reduction_rate']:.6f}` |"
            )
    else:
        lines.append(f"- Blocker: `{orb.get('error')}`")
    lines.extend(
        [
            "",
            "## SLAM Smoke",
            "",
            f"- ORB-SLAM3: `{payload['availability']['backend']['orb_slam3']['smoke_status']}` — "
            f"{payload['availability']['backend']['orb_slam3']['smoke_reason']}",
            f"- DROID: `{payload['availability']['backend']['droid']['smoke_status']}` — "
            f"{payload['availability']['backend']['droid']['smoke_reason']}",
            "",
            "## P195 Gate",
            "",
            f"- Status: `{p195['status']}`",
            f"- Human labels blank: `{p195['human_labels_blank']}`",
            f"- Valid human admission labels: `{p195['boundary_valid_human_admit_label_count']}`",
            f"- Valid human same-object labels: `{p195['pair_valid_human_same_object_label_count']}`",
            "",
            "## Recommendation",
            "",
            payload["p221_recommendation"],
            "",
            "## Outputs",
            "",
            f"- JSON evidence: `{rel(EVIDENCE_JSON)}`",
            f"- CSV evidence: `{rel(EVIDENCE_CSV)}`",
            f"- Markdown report: `{rel(EXPORT_MD)}`",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--orb-worker", type=Path, default=None, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.orb_worker:
        print(json.dumps(count_orb_with_current_python(args.orb_worker), sort_keys=True))
        return

    p219 = read_json(P219_MANIFEST)
    samples = list(p219["samples"])
    default_cv2 = cv2_probe(sys.executable)
    tram_env = os.environ.copy()
    tram_env["LD_LIBRARY_PATH"] = f"{TRAM_LD}:{tram_env.get('LD_LIBRARY_PATH', '')}"
    tram_cv2 = cv2_probe(TRAM_PYTHON, env=tram_env) if TRAM_PYTHON.exists() else {"available": False, "error": "tram python missing"}
    orb = run_orb_proxy(default_cv2, tram_cv2)
    backend = backend_audit()
    input_audit = sample_input_audit(samples)
    p195 = p195_status()

    payload = {
        "status": "P220_FRONTEND_MASKING_SLAM_FEASIBILITY_SMOKE_COMPLETE",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "claim_boundary": "P220 audits/evaluates semantic dynamic-mask front-end effects only. It does not train or claim learned admission control, and it does not use weak/admission labels.",
        "source_reports": {
            "p218": rel(P218_JSON),
            "p219": rel(P219_JSON),
            "p219_manifest": rel(P219_MANIFEST),
        },
        "guardrails": {
            "uses_admission_labels": False,
            "uses_weak_or_selection_labels": False,
            "prohibited_label_tokens_not_used": list(PROHIBITED_LABEL_TOKENS),
            "touches_raw_data": False,
            "downloads": False,
            "long_experiments": False,
        },
        "availability": {
            "opencv_default": default_cv2,
            "opencv_tram": tram_cv2,
            "backend": backend,
        },
        "p219_input_audit": input_audit,
        "orb_proxy": orb,
        "p195_status": p195,
        "p221_recommendation": "P221 should build a small temporally aligned raw-vs-P218-masked sequence package from local held-out frames before any trajectory claim. Keep P195 blocked until independent human admission/same-object labels exist.",
    }

    EVIDENCE_JSON.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(EVIDENCE_CSV, orb.get("samples", []) if orb.get("status") == "ok" else [])
    write_markdown(EXPORT_MD, payload)
    print(json.dumps({"status": payload["status"], "json": rel(EVIDENCE_JSON), "csv": rel(EVIDENCE_CSV), "md": rel(EXPORT_MD)}, indent=2))


if __name__ == "__main__":
    main()
