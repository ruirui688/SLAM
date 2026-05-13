#!/usr/bin/env python3
"""Build a bounded P225 temporal raw-vs-P218-masked TorWIC sequence package.

The mask route intentionally reuses the P218 compact dynamic-mask model code.
If no checkpoint is supplied, this script performs a bounded retraining smoke
from P217 dataset-provided semantic binary masks only, then runs inference on a
small temporally aligned TorWIC window. It does not use target sequence semantic
masks, weak labels, selection labels, model predictions, or human labels as
training targets.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import shutil
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

from train_dynamic_mask_p218 import (  # noqa: E402
    PROHIBITED_FIELDS,
    DynamicMaskDataset,
    SmallUNet,
    compute_pos_weight,
    evaluate_model,
    read_json,
    read_manifest,
    set_determinism,
    split_rows,
)


DATA_ROOT = ROOT / "data/TorWIC_SLAM_Dataset"
DEFAULT_SEQUENCE = DATA_ROOT / "Oct. 12, 2022/Aisle_CW"
P217_CSV = ROOT / "paper/evidence/dynamic_mask_dataset_p217.csv"
P217_JSON = ROOT / "paper/evidence/dynamic_mask_dataset_p217.json"
P218_JSON = ROOT / "paper/evidence/dynamic_mask_training_p218.json"
P195_JSON = ROOT / "paper/evidence/independent_supervision_gate_p195.json"
EVIDENCE_JSON = ROOT / "paper/evidence/temporal_masked_sequence_p225.json"
EVIDENCE_CSV = ROOT / "paper/evidence/temporal_masked_sequence_p225.csv"
EXPORT_MD = ROOT / "paper/export/temporal_masked_sequence_p225.md"
OUTPUT_ROOT = ROOT / "outputs/temporal_masked_sequence_p225"
SPLITS = ("train", "val", "test")


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_times(path: Path) -> list[float]:
    return [float(line.strip().split()[0]) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_pose_lines(path: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        rows.append(line.strip().split())
    return rows


def find_sequence_dir(requested: Path) -> Path:
    candidates = [requested, requested / requested.name]
    for candidate in candidates:
        if (
            (candidate / "image_left").is_dir()
            and (candidate / "frame_times.txt").is_file()
            and (candidate / "traj_gt.txt").is_file()
        ):
            return candidate
    raise FileNotFoundError(f"no TorWIC sequence with image_left/frame_times.txt/traj_gt.txt under {requested}")


def sorted_images(image_dir: Path) -> list[Path]:
    images = sorted(image_dir.glob("*.png"), key=lambda p: int(p.stem) if p.stem.isdigit() else p.stem)
    if not images:
        raise FileNotFoundError(f"no PNG images in {image_dir}")
    return images


def p195_status() -> dict[str, Any]:
    payload = read_json(P195_JSON)
    label_audit = payload.get("label_audit", {}) if isinstance(payload, dict) else {}
    boundary = label_audit.get("boundary_review") or label_audit.get("boundary") or {}
    pairs = label_audit.get("association_pairs") or label_audit.get("pairs") or {}
    boundary_valid = boundary.get("valid_human_admit_label_count", boundary.get("valid", 0))
    pair_valid = pairs.get("valid_human_same_object_label_count", pairs.get("valid", 0))
    return {
        "status": payload.get("status", "unknown") if isinstance(payload, dict) else "unknown",
        "human_labels_blank": boundary_valid == 0 and pair_valid == 0,
        "boundary_valid_human_admit_label_count": boundary_valid,
        "pair_valid_human_same_object_label_count": pair_valid,
    }


def train_or_load_model(args: argparse.Namespace, device: torch.device) -> tuple[SmallUNet, dict[str, Any]]:
    model = SmallUNet(base_channels=args.base_channels).to(device)
    if args.checkpoint:
        checkpoint = torch.load(args.checkpoint, map_location=device)
        model.load_state_dict(checkpoint["model_state_dict"])
        threshold = float(checkpoint.get("selected_threshold", args.threshold))
        return model, {
            "mode": "loaded_checkpoint",
            "checkpoint": rel(args.checkpoint),
            "checkpoint_sha256": sha256_file(args.checkpoint),
            "selected_threshold": threshold,
            "config": checkpoint.get("config", {}),
            "training_metrics": checkpoint.get("metrics", {}),
        }

    rows = read_manifest(args.p217_manifest)
    manifest_columns = sorted(rows[0].keys()) if rows else []
    prohibited = sorted(set(manifest_columns) & PROHIBITED_FIELDS)
    if prohibited:
        raise ValueError(f"P217 manifest contains prohibited target/proxy columns: {prohibited}")

    rows_by_split = split_rows(rows)
    size = (args.resize_width, args.resize_height)
    train_ds = DynamicMaskDataset(rows_by_split["train"], size=size, augment=False, seed=args.seed)
    eval_ds = {split: DynamicMaskDataset(items, size=size, augment=False, seed=args.seed) for split, items in rows_by_split.items()}
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0, pin_memory=device.type == "cuda")
    class_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)
    eval_loaders = {
        split: DataLoader(ds, batch_size=args.batch_size, shuffle=False, num_workers=0, pin_memory=device.type == "cuda")
        for split, ds in eval_ds.items()
    }
    pos_weight, class_balance = compute_pos_weight(class_loader, args.max_pos_weight)
    pos_weight = pos_weight.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    bce = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    history: list[dict[str, Any]] = []
    thresholds = [0.30, 0.40, 0.50, 0.60, 0.70]
    start = time.time()

    for epoch in range(1, args.epochs + 1):
        model.train()
        loss_total = 0.0
        batches = 0
        for image, mask, _sample_ids in train_loader:
            image = image.to(device, non_blocking=True)
            mask = mask.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            logits = model(image)
            loss = bce(logits, mask) + 0.5 * _dice_loss_from_logits(logits, mask)
            loss.backward()
            optimizer.step()
            loss_total += float(loss.item())
            batches += 1
        val_metrics = evaluate_model(model, eval_loaders["val"], device, [0.50])["threshold_metrics"]["0.50"]
        history.append(
            {
                "epoch": epoch,
                "train_loss": round(loss_total / batches, 6) if batches else math.nan,
                "val_f1_dynamic_at_0_50": val_metrics["f1_dynamic"],
                "val_dynamic_iou_at_0_50": val_metrics["dynamic_iou"],
            }
        )

    raw_eval = {split: evaluate_model(model, loader, device, thresholds) for split, loader in eval_loaders.items()}
    selected_threshold = max(
        thresholds,
        key=lambda threshold: (
            raw_eval["val"]["threshold_metrics"][f"{threshold:.2f}"]["f1_dynamic"],
            raw_eval["val"]["threshold_metrics"][f"{threshold:.2f}"]["dynamic_iou"],
            -abs(threshold - 0.5),
        ),
    )
    selected_key = f"{selected_threshold:.2f}"
    metrics = {
        split: {
            "loss": raw_eval[split]["loss"],
            "selected_threshold": raw_eval[split]["threshold_metrics"][selected_key],
        }
        for split in SPLITS
    }
    checkpoint_path = args.output_root / "model" / "p225_retrained_p218_smallunet.pt"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_payload = {
        "model_state_dict": model.state_dict(),
        "selected_threshold": selected_threshold,
        "config": {
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "resize_width": args.resize_width,
            "resize_height": args.resize_height,
            "base_channels": args.base_channels,
            "lr": args.lr,
            "weight_decay": args.weight_decay,
            "seed": args.seed,
        },
        "metrics": metrics,
        "history": history,
        "class_balance": class_balance,
        "label_source": "P217 binary_mask_path derived from dataset-provided TorWIC AnnotatedSemanticSet semantic masks only",
    }
    torch.save(checkpoint_payload, checkpoint_path)
    return model, {
        "mode": "retrained_bounded_smoke_no_prior_p218_checkpoint_found",
        "checkpoint": rel(checkpoint_path),
        "checkpoint_sha256": sha256_file(checkpoint_path),
        "selected_threshold": selected_threshold,
        "duration_seconds": round(time.time() - start, 3),
        "history": history,
        "metrics": metrics,
        "class_balance": class_balance,
        "dataset": {
            "p217_csv": rel(args.p217_manifest),
            "rows": len(rows),
            "split_counts": dict(sorted(Counter(row["split"] for row in rows).items())),
            "manifest_prohibited_columns": prohibited,
        },
    }


def _dice_loss_from_logits(logits: torch.Tensor, target: torch.Tensor, eps: float = 1e-6) -> torch.Tensor:
    probs = torch.sigmoid(logits)
    dims = (1, 2, 3)
    intersection = (probs * target).sum(dim=dims)
    union = probs.sum(dim=dims) + target.sum(dim=dims)
    dice = (2 * intersection + eps) / (union + eps)
    return 1.0 - dice.mean()


def infer_mask(model: SmallUNet, image: Image.Image, args: argparse.Namespace, threshold: float, device: torch.device) -> tuple[Image.Image, Image.Image, dict[str, Any]]:
    model.eval()
    small = image.resize((args.resize_width, args.resize_height), Image.Resampling.BILINEAR)
    image_np = np.asarray(small, dtype=np.float32) / 255.0
    image_t = torch.from_numpy(image_np.transpose(2, 0, 1))[None].to(device)
    with torch.no_grad():
        probs = torch.sigmoid(model(image_t))[0, 0].detach().cpu().numpy()
    pred_small = (probs >= threshold).astype(np.uint8) * 255
    prob_img = Image.fromarray(np.clip(probs * 255.0, 0, 255).astype(np.uint8), mode="L").resize(image.size, Image.Resampling.BILINEAR)
    pred_img = Image.fromarray(pred_small, mode="L").resize(image.size, Image.Resampling.NEAREST)
    pred_np = np.asarray(pred_img, dtype=np.uint8)
    positive_pixels = int((pred_np >= 127).sum())
    total_pixels = int(pred_np.size)
    return pred_img, prob_img, {
        "predicted_dynamic_pixels": positive_pixels,
        "predicted_dynamic_pixel_rate": round(positive_pixels / total_pixels, 6) if total_pixels else 0.0,
        "mean_probability": round(float(probs.mean()), 6),
        "max_probability": round(float(probs.max()), 6),
    }


def mask_image(image: Image.Image, pred_mask: Image.Image) -> Image.Image:
    arr = np.asarray(image.convert("RGB"), dtype=np.uint8).copy()
    mask = np.asarray(pred_mask, dtype=np.uint8) >= 127
    arr[mask] = 0
    return Image.fromarray(arr, mode="RGB")


def write_rgb_txt(path: Path, rows: list[dict[str, Any]], variant: str) -> None:
    lines = [f"{row['timestamp']:.9f} image_left/{Path(row[f'{variant}_image_path']).name}" for row in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_frame_times(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("\n".join(f"{row['timestamp']:.18e}" for row in rows) + "\n", encoding="utf-8")


def write_groundtruth(path: Path, pose_rows: list[list[str]], indices: list[int]) -> None:
    lines = [" ".join(pose_rows[idx]) for idx in indices]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def copy_if_exists(src: Path, dst: Path) -> str | None:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return rel(dst)
    return None


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    seq = payload["sequence"]
    mask = payload["mask_model"]
    stats = payload["mask_statistics"]
    lines = [
        "# P225 Temporal Raw-vs-P218-Masked Sequence Package",
        "",
        f"**Status:** {payload['status']}",
        "",
        "## Claim Boundary",
        "",
        payload["claim_boundary"],
        "",
        "## Sequence",
        "",
        f"- Source: `{seq['source_sequence_dir']}`",
        f"- Window: `{seq['start_index']}` to `{seq['end_index']}` inclusive",
        f"- Frames: `{seq['frame_count']}`",
        f"- Timestamp span seconds: `{seq['timestamp_span_seconds']}`",
        f"- Raw package: `{payload['outputs']['raw_sequence_dir']}`",
        f"- Masked package: `{payload['outputs']['masked_sequence_dir']}`",
        "",
        "## Mask Model Route",
        "",
        f"- Mode: `{mask['mode']}`",
        f"- Checkpoint: `{mask['checkpoint']}`",
        f"- Threshold: `{mask['selected_threshold']}`",
        "- Training labels: P217 dataset-provided semantic binary dynamic/non-static masks only.",
        "- Target sequence semantic masks were not used as labels or copied into masked outputs.",
        "",
        "## Masked Window Stats",
        "",
        f"- Mean predicted dynamic pixel rate: `{stats['mean_predicted_dynamic_pixel_rate']}`",
        f"- Min/max predicted dynamic pixel rate: `{stats['min_predicted_dynamic_pixel_rate']}` / `{stats['max_predicted_dynamic_pixel_rate']}`",
        f"- Mean probability: `{stats['mean_probability']}`",
        "",
        "## Trajectory Readiness",
        "",
        f"- `rgb.txt`: `{payload['trajectory_readiness']['rgb_txt']}`",
        f"- `frame_times.txt`: `{payload['trajectory_readiness']['frame_times_txt']}`",
        f"- `groundtruth.txt`: `{payload['trajectory_readiness']['groundtruth_txt']}`",
        f"- `calibrations.txt`: `{payload['trajectory_readiness']['calibrations_txt']}`",
        f"- ORB YAML reference: `{payload['trajectory_readiness']['orb_yaml_reference']}`",
        "",
        "## Outputs",
        "",
        f"- JSON: `{payload['outputs']['json']}`",
        f"- CSV: `{payload['outputs']['csv']}`",
        f"- Markdown: `{payload['outputs']['markdown']}`",
        "",
        "## Boundary Notes",
        "",
        "- This is a trajectory-ready packaging/feasibility step, not an ATE/RPE result.",
        f"- P195 status remains `{payload['p195_status'].get('status', 'unknown')}`.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_sequence(args: argparse.Namespace) -> dict[str, Any]:
    set_determinism(args.seed)
    cuda_available = torch.cuda.is_available()
    if args.require_cuda and not cuda_available:
        raise RuntimeError("P225 requires CUDA by default for bounded retraining/inference; pass --no-require-cuda for CPU smoke")
    device = torch.device("cuda" if cuda_available else "cpu")
    start_time = time.time()

    sequence_dir = find_sequence_dir(args.sequence_dir)
    image_paths = sorted_images(sequence_dir / "image_left")
    frame_times = parse_times(sequence_dir / "frame_times.txt")
    pose_rows = parse_pose_lines(sequence_dir / "traj_gt.txt")
    if len(image_paths) != len(frame_times) or len(frame_times) != len(pose_rows):
        raise ValueError(
            f"unaligned source lengths images={len(image_paths)} frame_times={len(frame_times)} traj_gt={len(pose_rows)}"
        )
    if args.start_index < 0 or args.start_index >= len(image_paths):
        raise ValueError("--start-index out of range")
    end_index = min(args.start_index + args.frame_count, len(image_paths))
    indices = list(range(args.start_index, end_index))
    if len(indices) < 2:
        raise ValueError("window must contain at least 2 frames")

    model, mask_info = train_or_load_model(args, device)
    threshold = float(mask_info["selected_threshold"])

    package_root = args.output_root / "sequence"
    raw_dir = package_root / "raw"
    masked_dir = package_root / "masked"
    for variant_dir in (raw_dir, masked_dir):
        (variant_dir / "image_left").mkdir(parents=True, exist_ok=True)
    (package_root / "predicted_masks").mkdir(parents=True, exist_ok=True)
    (package_root / "probabilities").mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for out_idx, src_idx in enumerate(indices):
        source = image_paths[src_idx]
        stem = f"{out_idx:06d}"
        image = Image.open(source).convert("RGB")
        pred_mask, prob_img, mask_stats = infer_mask(model, image, args, threshold, device)
        masked = mask_image(image, pred_mask)
        raw_path = raw_dir / "image_left" / f"{stem}.png"
        masked_path = masked_dir / "image_left" / f"{stem}.png"
        mask_path = package_root / "predicted_masks" / f"{stem}_p218_pred_mask.png"
        prob_path = package_root / "probabilities" / f"{stem}_p218_prob.png"
        image.save(raw_path)
        masked.save(masked_path)
        pred_mask.save(mask_path)
        prob_img.save(prob_path)
        pose = pose_rows[src_idx]
        row = {
            "package_frame_id": stem,
            "source_index": src_idx,
            "source_image_path": rel(source),
            "timestamp": frame_times[src_idx],
            "raw_image_path": rel(raw_path),
            "masked_image_path": rel(masked_path),
            "p218_pred_mask_path": rel(mask_path),
            "p218_probability_path": rel(prob_path),
            "gt_tx": pose[1],
            "gt_ty": pose[2],
            "gt_tz": pose[3],
            "gt_qx": pose[4],
            "gt_qy": pose[5],
            "gt_qz": pose[6],
            "gt_qw": pose[7],
            **mask_stats,
        }
        rows.append(row)

    for variant, variant_dir in (("raw", raw_dir), ("masked", masked_dir)):
        write_rgb_txt(variant_dir / "rgb.txt", rows, variant)
        write_frame_times(variant_dir / "frame_times.txt", rows)
        write_groundtruth(variant_dir / "groundtruth.txt", pose_rows, indices)
        write_groundtruth(variant_dir / "traj_gt.txt", pose_rows, indices)
        copy_if_exists(sequence_dir.parent / "calibrations.txt", variant_dir / "calibrations.txt")
        copy_if_exists(ROOT / "outputs/orb_slam3_p173_recovery/TorWIC_mono_left.yaml", variant_dir / "TorWIC_mono_left.yaml")

    with EVIDENCE_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    rates = [float(row["predicted_dynamic_pixel_rate"]) for row in rows]
    probs = [float(row["mean_probability"]) for row in rows]
    p217 = read_json(args.p217_json)
    p218 = read_json(P218_JSON)
    timestamp_span = rows[-1]["timestamp"] - rows[0]["timestamp"]
    payload = {
        "status": "P225_TEMPORAL_RAW_VS_P218_MASKED_SEQUENCE_PACKAGE_COMPLETE",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": "This package is trajectory-ready input material for raw-vs-P218-masked feasibility testing. It does not claim ORB-SLAM3/DROID ATE/RPE improvement.",
        "sequence": {
            "source_sequence_dir": rel(sequence_dir),
            "preferred_oct_12_aisle_cw_used": "Oct. 12, 2022/Aisle_CW" in rel(sequence_dir),
            "start_index": indices[0],
            "end_index": indices[-1],
            "frame_count": len(indices),
            "timestamp_start": rows[0]["timestamp"],
            "timestamp_end": rows[-1]["timestamp"],
            "timestamp_span_seconds": round(timestamp_span, 6),
            "image_size": list(Image.open(image_paths[indices[0]]).size),
        },
        "mask_model": mask_info,
        "source_evidence": {
            "p217_json": rel(args.p217_json),
            "p217_status": p217.get("status", "unknown"),
            "p218_json": rel(P218_JSON),
            "p218_status": p218.get("status", "unknown"),
            "p218_existing_checkpoint_found": bool(args.checkpoint),
            "target_sequence_semantic_masks_used_as_training_labels": False,
            "uses_target_admit": False,
            "uses_current_weak_label": False,
            "uses_selection_v5": False,
            "uses_model_predictions_as_training_labels": False,
            "uses_human_labels": False,
        },
        "mask_statistics": {
            "mean_predicted_dynamic_pixel_rate": round(float(np.mean(rates)), 6),
            "min_predicted_dynamic_pixel_rate": round(float(np.min(rates)), 6),
            "max_predicted_dynamic_pixel_rate": round(float(np.max(rates)), 6),
            "mean_probability": round(float(np.mean(probs)), 6),
        },
        "trajectory_readiness": {
            "raw_frame_count": len(list((raw_dir / "image_left").glob("*.png"))),
            "masked_frame_count": len(list((masked_dir / "image_left").glob("*.png"))),
            "rgb_txt": [rel(raw_dir / "rgb.txt"), rel(masked_dir / "rgb.txt")],
            "frame_times_txt": [rel(raw_dir / "frame_times.txt"), rel(masked_dir / "frame_times.txt")],
            "groundtruth_txt": [rel(raw_dir / "groundtruth.txt"), rel(masked_dir / "groundtruth.txt")],
            "calibrations_txt": [rel(raw_dir / "calibrations.txt"), rel(masked_dir / "calibrations.txt")],
            "orb_yaml_reference": [rel(raw_dir / "TorWIC_mono_left.yaml"), rel(masked_dir / "TorWIC_mono_left.yaml")],
            "slam_not_run": True,
        },
        "p195_status": p195_status(),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "torch": torch.__version__,
            "cuda_available": cuda_available,
            "device": torch.cuda.get_device_name(0) if cuda_available else "cpu",
            "cuda_version": torch.version.cuda,
            "duration_seconds": round(time.time() - start_time, 3),
        },
        "outputs": {
            "json": rel(EVIDENCE_JSON),
            "csv": rel(EVIDENCE_CSV),
            "markdown": rel(EXPORT_MD),
            "package_root": rel(package_root),
            "raw_sequence_dir": rel(raw_dir),
            "masked_sequence_dir": rel(masked_dir),
            "predicted_mask_dir": rel(package_root / "predicted_masks"),
            "probability_dir": rel(package_root / "probabilities"),
        },
    }
    write_json(EVIDENCE_JSON, payload)
    write_markdown(EXPORT_MD, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sequence-dir", type=Path, default=DEFAULT_SEQUENCE)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--p217-manifest", type=Path, default=P217_CSV)
    parser.add_argument("--p217-json", type=Path, default=P217_JSON)
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--start-index", type=int, default=480)
    parser.add_argument("--frame-count", type=int, default=60)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--resize-width", type=int, default=320)
    parser.add_argument("--resize-height", type=int, default=180)
    parser.add_argument("--base-channels", type=int, default=12)
    parser.add_argument("--lr", type=float, default=2e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--max-pos-weight", type=float, default=4.0)
    parser.add_argument("--seed", type=int, default=225)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--require-cuda", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()
    if args.frame_count < 2 or args.frame_count > 120:
        raise ValueError("--frame-count must be in [2, 120] for bounded P225 packaging")
    if args.epochs < 1 or args.epochs > 5:
        raise ValueError("--epochs must be in [1, 5] for bounded P225 retraining smoke")
    payload = build_sequence(args)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "frames": payload["sequence"]["frame_count"],
                "source": payload["sequence"]["source_sequence_dir"],
                "mask_mode": payload["mask_model"]["mode"],
                "threshold": payload["mask_model"]["selected_threshold"],
                "mean_predicted_dynamic_pixel_rate": payload["mask_statistics"]["mean_predicted_dynamic_pixel_rate"],
                "raw_sequence_dir": payload["outputs"]["raw_sequence_dir"],
                "masked_sequence_dir": payload["outputs"]["masked_sequence_dir"],
                "json": payload["outputs"]["json"],
                "csv": payload["outputs"]["csv"],
                "markdown": payload["outputs"]["markdown"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
