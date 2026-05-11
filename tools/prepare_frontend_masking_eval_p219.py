#!/usr/bin/env python3
"""Prepare the P219 front-end masking evaluation package.

This consumes P218 predicted dynamic masks and P217 dataset-provided binary
dynamic masks. It prepares raw-vs-masked image pairs plus non-SLAM proxy
metrics for a bounded SLAM front-end masking evaluation. It does not use or
create admission-control labels.
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import io
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
P217_CSV = ROOT / "paper/evidence/dynamic_mask_dataset_p217.csv"
P218_JSON = ROOT / "paper/evidence/dynamic_mask_training_p218.json"
P195_JSON = ROOT / "paper/evidence/independent_supervision_gate_p195.json"
OUTPUT_ROOT = ROOT / "outputs/frontend_masking_eval_p219"
EVIDENCE_JSON = ROOT / "paper/evidence/frontend_masking_eval_p219.json"
EVIDENCE_CSV = ROOT / "paper/evidence/frontend_masking_eval_p219.csv"
EXPORT_MD = ROOT / "paper/export/frontend_masking_eval_p219.md"
PROHIBITED_FIELDS = {
    "target_admit",
    "current_weak_label",
    "selection_v5",
    "model_prediction",
    "model_pred",
    "model_probability",
    "model_prob",
    "admit_probability",
    "human_admit_label",
    "human_same_object_label",
}


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_p217_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if rows:
        prohibited = sorted(set(rows[0]) & PROHIBITED_FIELDS)
        if prohibited:
            raise ValueError(f"P217 manifest contains prohibited target/proxy columns: {prohibited}")
    missing: list[str] = []
    for row in rows:
        for key in ("image_path", "binary_mask_path"):
            if not (ROOT / row[key]).exists():
                missing.append(f"{row.get('sample_id', '<missing>')}:{key}")
    if missing:
        raise FileNotFoundError(f"P217 local image/mask paths are missing: {missing[:8]}")
    return rows


def metrics_from_masks(pred: np.ndarray, truth: np.ndarray) -> dict[str, Any]:
    pred_b = pred.astype(bool)
    truth_b = truth.astype(bool)
    tp = int(np.logical_and(pred_b, truth_b).sum())
    tn = int(np.logical_and(~pred_b, ~truth_b).sum())
    fp = int(np.logical_and(pred_b, ~truth_b).sum())
    fn = int(np.logical_and(~pred_b, truth_b).sum())
    total = tp + tn + fp + fn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    iou = tp / (tp + fp + fn) if tp + fp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "pixels": total,
        "predicted_masked_pixel_rate": round((tp + fp) / total, 8) if total else 0.0,
        "gt_dynamic_pixel_rate": round((tp + fn) / total, 8) if total else 0.0,
        "mask_precision": round(precision, 6),
        "mask_recall": round(recall, 6),
        "mask_f1": round(f1, 6),
        "mask_iou": round(iou, 6),
    }


def load_cv2() -> tuple[Any | None, str | None]:
    capture = io.StringIO()
    try:
        with contextlib.redirect_stderr(capture):
            import cv2  # type: ignore

        return cv2, None
    except Exception as exc:
        detail = capture.getvalue().strip()
        error = f"{type(exc).__name__}: {exc}"
        if detail:
            error = f"{error}; stderr={detail.splitlines()[-1]}"
        return None, error


def orb_counts(cv2: Any | None, image_path: Path, masked_path: Path, gt_mask: np.ndarray) -> dict[str, Any]:
    if cv2 is None:
        return {
            "orb_available": False,
            "orb_raw_keypoints_total": None,
            "orb_masked_keypoints_total": None,
            "orb_raw_keypoints_in_gt_dynamic": None,
            "orb_masked_keypoints_in_gt_dynamic": None,
            "orb_gt_dynamic_keypoint_reduction": None,
        }
    raw = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    masked = cv2.imread(str(masked_path), cv2.IMREAD_GRAYSCALE)
    if raw is None or masked is None:
        return {
            "orb_available": True,
            "orb_error": "cv2 could not read raw or masked image",
        }
    orb = cv2.ORB_create(nfeatures=2000)
    raw_kp = orb.detect(raw, None) or []
    masked_kp = orb.detect(masked, None) or []

    def in_dynamic(keypoints: list[Any]) -> int:
        count = 0
        h, w = gt_mask.shape
        for kp in keypoints:
            x = int(round(kp.pt[0]))
            y = int(round(kp.pt[1]))
            if 0 <= x < w and 0 <= y < h and gt_mask[y, x]:
                count += 1
        return count

    raw_dyn = in_dynamic(raw_kp)
    masked_dyn = in_dynamic(masked_kp)
    reduction = (raw_dyn - masked_dyn) / raw_dyn if raw_dyn else 0.0
    return {
        "orb_available": True,
        "orb_raw_keypoints_total": len(raw_kp),
        "orb_masked_keypoints_total": len(masked_kp),
        "orb_raw_keypoints_in_gt_dynamic": raw_dyn,
        "orb_masked_keypoints_in_gt_dynamic": masked_dyn,
        "orb_gt_dynamic_keypoint_reduction": round(reduction, 6),
    }


def suppress_dynamic_pixels(rgb: Image.Image, pred_mask: Image.Image, mode: str) -> Image.Image:
    masked = rgb.copy()
    mask_l = pred_mask.convert("L")
    if mode == "color":
        color = Image.new("RGB", rgb.size, (220, 38, 38))
        masked = Image.blend(masked, color, 0.35)
        out = rgb.copy()
        out.paste(masked, (0, 0), mask_l)
        return out
    gray = Image.new("RGB", rgb.size, (118, 118, 118))
    masked.paste(gray, (0, 0), mask_l)
    return masked


def select_predictions(p218: dict[str, Any], limit_per_split: int) -> list[dict[str, Any]]:
    artifacts = list(p218.get("prediction_artifacts", []))
    selected: list[dict[str, Any]] = []
    for split in ("val", "test"):
        split_items = [item for item in artifacts if item.get("split") == split]
        selected.extend(split_items[:limit_per_split])
    return selected


def p195_status() -> dict[str, Any]:
    payload = read_json(P195_JSON)
    label_audit = payload.get("label_audit", {}) if isinstance(payload, dict) else {}
    boundary = label_audit.get("boundary_review") or label_audit.get("boundary") or {}
    pairs = label_audit.get("association_pairs") or label_audit.get("pairs") or {}
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


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = [
        "sample_id",
        "split",
        "raw_image_path",
        "gt_binary_mask_path",
        "predicted_mask_path",
        "predicted_probability_path",
        "masked_image_path",
        "overlay_path",
        "width",
        "height",
        "predicted_masked_pixel_rate",
        "gt_dynamic_pixel_rate",
        "mask_precision",
        "mask_recall",
        "mask_f1",
        "mask_iou",
        "orb_available",
        "orb_raw_keypoints_total",
        "orb_masked_keypoints_total",
        "orb_raw_keypoints_in_gt_dynamic",
        "orb_masked_keypoints_in_gt_dynamic",
        "orb_gt_dynamic_keypoint_reduction",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    p195 = payload["p195_status"]
    orb_note = payload["orb"]["status"]
    lines = [
        "# P219 Front-End Masking Evaluation Package",
        "",
        f"**Status:** {payload['status']}",
        "",
        "## Boundary",
        "",
        payload["claim_boundary"],
        "",
        "## Package",
        "",
        f"- Samples: `{summary['sample_count']}` (`val={summary['split_counts'].get('val', 0)}`, `test={summary['split_counts'].get('test', 0)}`)",
        f"- Masking mode: `{payload['config']['mask_mode']}`",
        f"- Selected P218 threshold: `{payload['p218_selected_threshold']}`",
        f"- Local package root: `{payload['outputs']['package_root']}`",
        "",
        "## Proxy Metrics",
        "",
        f"- Mean predicted masked pixel rate: `{summary['mean_predicted_masked_pixel_rate']}`",
        f"- Mean GT dynamic pixel rate: `{summary['mean_gt_dynamic_pixel_rate']}`",
        f"- Mean mask precision/recall/F1/IoU: `{summary['mean_mask_precision']}` / `{summary['mean_mask_recall']}` / `{summary['mean_mask_f1']}` / `{summary['mean_mask_iou']}`",
        f"- ORB proxy: `{orb_note}`",
        "",
        "## Samples",
        "",
        "| split | sample | pred rate | GT rate | precision | recall | IoU | masked image |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["samples"]:
        lines.append(
            "| {split} | `{sample_id}` | `{predicted_masked_pixel_rate}` | `{gt_dynamic_pixel_rate}` | "
            "`{mask_precision}` | `{mask_recall}` | `{mask_iou}` | `{masked_image_path}` |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Evaluation Protocol",
            "",
            "1. Use these six held-out P218 prediction samples as a deterministic raw-vs-masked input sanity package.",
            "2. For each row, compare raw image front-end features against the masked image where P218 predicted dynamic pixels are suppressed.",
            "3. Report mask pixel coverage and GT-mask precision/recall/IoU as front-end input quality checks, not SLAM trajectory metrics.",
            "4. If OpenCV ORB is available, report total keypoints and keypoints in the GT dynamic region before/after masking as a feature-masking proxy.",
            "5. Run actual ORB/DROID trajectory smoke only in P220 on a tiny existing local raw-vs-masked backend pack; use ATE/RPE only when trajectories and ground truth align.",
            "",
            "## P195 Gate",
            "",
            f"- Status: `{p195['status']}`",
            f"- Human labels blank: `{p195['human_labels_blank']}`",
            f"- Valid `human_admit_label`: `{p195['boundary_valid_human_admit_label_count']}`",
            f"- Valid `human_same_object_label`: `{p195['pair_valid_human_same_object_label_count']}`",
            "",
            "## P220 Recommendation",
            "",
            "Run a tiny raw-vs-masked trajectory smoke using an existing local ORB-SLAM3 or DROID-SLAM helper on a short held-out sequence/package only after confirming the runtime is already available. Keep the comparison bounded: raw RGB vs P218-masked RGB, record feature/trajectory availability, ATE/RPE if valid ground truth exists, and do not claim learned admission control.",
            "",
            "## Outputs",
            "",
            f"- JSON evidence: `{payload['outputs']['evidence_json']}`",
            f"- CSV evidence: `{payload['outputs']['evidence_csv']}`",
            f"- Markdown report: `{payload['outputs']['export_markdown']}`",
            f"- Ignored local images/manifests: `{payload['outputs']['package_root']}`",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def mean(key: str) -> float:
        values = [float(row[key]) for row in rows if row.get(key) not in (None, "")]
        return round(sum(values) / len(values), 6) if values else 0.0

    split_counts = Counter(row["split"] for row in rows)
    return {
        "sample_count": len(rows),
        "split_counts": dict(sorted(split_counts.items())),
        "mean_predicted_masked_pixel_rate": mean("predicted_masked_pixel_rate"),
        "mean_gt_dynamic_pixel_rate": mean("gt_dynamic_pixel_rate"),
        "mean_mask_precision": mean("mask_precision"),
        "mean_mask_recall": mean("mask_recall"),
        "mean_mask_f1": mean("mask_f1"),
        "mean_mask_iou": mean("mask_iou"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p217-csv", type=Path, default=P217_CSV)
    parser.add_argument("--p218-json", type=Path, default=P218_JSON)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--evidence-json", type=Path, default=EVIDENCE_JSON)
    parser.add_argument("--evidence-csv", type=Path, default=EVIDENCE_CSV)
    parser.add_argument("--export-md", type=Path, default=EXPORT_MD)
    parser.add_argument("--limit-per-split", type=int, default=3)
    parser.add_argument("--mask-mode", choices=("suppress", "color"), default="suppress")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows_by_sample = {row["sample_id"]: row for row in read_p217_rows(args.p217_csv)}
    p218 = read_json(args.p218_json)
    predictions = select_predictions(p218, args.limit_per_split)
    if not predictions:
        raise RuntimeError("No P218 prediction artifacts found; rerun P218 before P219.")

    cv2, cv2_error = load_cv2()
    masked_dir = args.output_root / "masked_images"
    overlay_dir = args.output_root / "overlays"
    manifest_path = args.output_root / "frontend_masking_eval_manifest.json"
    masked_dir.mkdir(parents=True, exist_ok=True)
    overlay_dir.mkdir(parents=True, exist_ok=True)

    sample_rows: list[dict[str, Any]] = []
    for item in predictions:
        sample_id = item["sample_id"]
        if sample_id not in rows_by_sample:
            raise KeyError(f"P218 prediction sample {sample_id} missing from P217 manifest")
        row = rows_by_sample[sample_id]
        raw_path = ROOT / row["image_path"]
        gt_path = ROOT / row["binary_mask_path"]
        pred_path = ROOT / item["prediction_mask_png"]
        prob_path = ROOT / item["probability_png"]
        overlay_source_path = ROOT / item["overlay_png"]
        for path in (pred_path, prob_path):
            if not path.exists():
                raise FileNotFoundError(path)

        raw = Image.open(raw_path).convert("RGB")
        gt = Image.open(gt_path).convert("L")
        if gt.size != raw.size:
            gt = gt.resize(raw.size, Image.Resampling.NEAREST)
        pred_small = Image.open(pred_path).convert("L")
        prob_small = Image.open(prob_path).convert("L")
        pred = pred_small.resize(raw.size, Image.Resampling.NEAREST)
        prob = prob_small.resize(raw.size, Image.Resampling.BILINEAR)

        stem = f"{item['split']}_{sample_id}"
        masked_path = masked_dir / f"{stem}_masked.png"
        pred_full_path = args.output_root / "predicted_masks_fullres" / f"{stem}_pred_mask_fullres.png"
        prob_full_path = args.output_root / "probabilities_fullres" / f"{stem}_prob_fullres.png"
        pred_full_path.parent.mkdir(parents=True, exist_ok=True)
        prob_full_path.parent.mkdir(parents=True, exist_ok=True)
        masked = suppress_dynamic_pixels(raw, pred, args.mask_mode)
        masked.save(masked_path)
        pred.save(pred_full_path)
        prob.save(prob_full_path)

        gt_np = np.asarray(gt) >= 127
        pred_np = np.asarray(pred) >= 127
        metrics = metrics_from_masks(pred_np, gt_np)
        orb = orb_counts(cv2, raw_path, masked_path, gt_np)

        sample_rows.append(
            {
                "sample_id": sample_id,
                "split": item["split"],
                "frame_id": row.get("frame_id", ""),
                "view_id": row.get("view_id", ""),
                "raw_image_path": rel(raw_path),
                "gt_binary_mask_path": rel(gt_path),
                "predicted_mask_path": rel(pred_path),
                "predicted_probability_path": rel(prob_path),
                "predicted_mask_fullres_path": rel(pred_full_path),
                "predicted_probability_fullres_path": rel(prob_full_path),
                "masked_image_path": rel(masked_path),
                "overlay_path": rel(overlay_source_path),
                "width": raw.width,
                "height": raw.height,
                "p218_resized_width": item.get("resized_size", [None, None])[0],
                "p218_resized_height": item.get("resized_size", [None, None])[1],
                **metrics,
                **orb,
            }
        )

    summary = summarize(sample_rows)
    orb_status = "available" if cv2 is not None else f"unavailable ({cv2_error})"
    payload: dict[str, Any] = {
        "status": "P219_FRONTEND_MASKING_EVAL_PACKAGE_READY",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "claim_boundary": (
            "P219 evaluates P218 semantic dynamic-mask front-end inputs and non-SLAM proxy metrics only. "
            "It does not train or claim learned persistent-map admission control."
        ),
        "config": {
            "p217_csv": rel(args.p217_csv),
            "p218_json": rel(args.p218_json),
            "limit_per_split": args.limit_per_split,
            "mask_mode": args.mask_mode,
            "uses_admission_labels": False,
            "uses_weak_or_selection_labels": False,
            "runs_slam": False,
        },
        "p218_selected_threshold": p218.get("selected_threshold"),
        "p218_source_commit": "4bbf1be",
        "summary": summary,
        "samples": sample_rows,
        "orb": {
            "status": orb_status,
            "error": cv2_error,
        },
        "p195_status": p195_status(),
        "p220_plan": [
            "Confirm an existing local tiny ORB-SLAM3 or DROID-SLAM smoke helper can run without downloads.",
            "Build raw and P218-masked RGB lists for a short held-out sequence/window with aligned timestamps and ground truth.",
            "Run raw vs masked with identical backend settings and record trajectory availability, ATE/RPE only if valid, plus front-end feature counts.",
            "Keep P195 blocked and make no learned admission-control claim.",
        ],
        "outputs": {
            "package_root": rel(args.output_root),
            "manifest": rel(manifest_path),
            "evidence_json": rel(args.evidence_json),
            "evidence_csv": rel(args.evidence_csv),
            "export_markdown": rel(args.export_md),
        },
        "verification": {
            "script_runs": True,
            "p218_prediction_artifacts_used": len(predictions),
            "held_out_rows_generated": len(sample_rows),
            "p195_remains_blocked": p195_status().get("status") == "BLOCKED",
            "human_labels_blank": p195_status().get("human_labels_blank") is True,
            "no_admission_or_weak_labels_used": True,
            "raw_data_modified": False,
            "slam_run": False,
        },
    }

    write_json(manifest_path, payload)
    write_json(args.evidence_json, payload)
    write_csv(args.evidence_csv, sample_rows)
    write_markdown(args.export_md, payload)
    print(json.dumps({"status": payload["status"], "summary": summary, "outputs": payload["outputs"]}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
