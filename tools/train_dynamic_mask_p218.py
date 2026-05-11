#!/usr/bin/env python3
"""Train the P218 compact binary dynamic-mask CUDA smoke.

This script reads only the P217 manifest image/mask paths. Targets are
dataset-provided AnnotatedSemanticSet-derived binary dynamic/non-static masks,
not admission labels, weak labels, or model predictions.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import random
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset


ROOT = Path(__file__).resolve().parents[1]
P217_CSV = ROOT / "paper/evidence/dynamic_mask_dataset_p217.csv"
P217_JSON = ROOT / "paper/evidence/dynamic_mask_dataset_p217.json"
P195_JSON = ROOT / "paper/evidence/independent_supervision_gate_p195.json"
EVIDENCE_JSON = ROOT / "paper/evidence/dynamic_mask_training_p218.json"
EXPORT_MD = ROOT / "paper/export/dynamic_mask_training_p218.md"
OUTPUT_ROOT = ROOT / "outputs/dynamic_mask_training_p218"
SPLITS = ("train", "val", "test")
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


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    missing = [row.get("sample_id", "<missing>") for row in rows if not (ROOT / row.get("image_path", "")).exists()]
    missing += [row.get("sample_id", "<missing>") for row in rows if not (ROOT / row.get("binary_mask_path", "")).exists()]
    if missing:
        raise FileNotFoundError(f"P217 manifest has missing local image/mask paths: {missing[:8]}")
    prohibited = sorted(set(rows[0].keys()) & PROHIBITED_FIELDS) if rows else []
    if prohibited:
        raise ValueError(f"P217 manifest contains prohibited target/proxy columns: {prohibited}")
    return rows


def split_rows(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    out = {split: [row for row in rows if row.get("split") == split] for split in SPLITS}
    missing = [split for split, items in out.items() if not items]
    if missing:
        raise ValueError(f"missing required splits in P217 manifest: {missing}")
    return out


def set_determinism(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True


def stable_flip(sample_id: str, seed: int) -> bool:
    text = f"{sample_id}:{seed}:p218_horizontal_flip"
    return int(hashlib.sha1(text.encode("utf-8")).hexdigest()[:8], 16) % 2 == 0


class DynamicMaskDataset(Dataset[tuple[torch.Tensor, torch.Tensor, str]]):
    def __init__(self, rows: list[dict[str, str]], *, size: tuple[int, int], augment: bool, seed: int) -> None:
        self.rows = rows
        self.size = size
        self.augment = augment
        self.seed = seed

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor, str]:
        row = self.rows[idx]
        width, height = self.size
        image = Image.open(ROOT / row["image_path"]).convert("RGB").resize((width, height), Image.Resampling.BILINEAR)
        mask = Image.open(ROOT / row["binary_mask_path"]).convert("L").resize((width, height), Image.Resampling.NEAREST)
        if self.augment and stable_flip(row["sample_id"], self.seed):
            image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            mask = mask.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        image_np = np.asarray(image, dtype=np.float32) / 255.0
        mask_np = (np.asarray(mask, dtype=np.float32) >= 127.0).astype(np.float32)
        image_t = torch.from_numpy(image_np.transpose(2, 0, 1))
        mask_t = torch.from_numpy(mask_np[None, :, :])
        return image_t, mask_t, row["sample_id"]


class ConvBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class SmallUNet(nn.Module):
    def __init__(self, base_channels: int = 12) -> None:
        super().__init__()
        c = base_channels
        self.enc1 = ConvBlock(3, c)
        self.enc2 = ConvBlock(c, c * 2)
        self.bottleneck = ConvBlock(c * 2, c * 4)
        self.up2 = nn.ConvTranspose2d(c * 4, c * 2, 2, stride=2)
        self.dec2 = ConvBlock(c * 4, c * 2)
        self.up1 = nn.ConvTranspose2d(c * 2, c, 2, stride=2)
        self.dec1 = ConvBlock(c * 2, c)
        self.head = nn.Conv2d(c, 1, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        e1 = self.enc1(x)
        e2 = self.enc2(F.max_pool2d(e1, 2))
        b = self.bottleneck(F.max_pool2d(e2, 2))
        d2 = self.up2(b)
        if d2.shape[-2:] != e2.shape[-2:]:
            d2 = F.interpolate(d2, size=e2.shape[-2:], mode="bilinear", align_corners=False)
        d2 = self.dec2(torch.cat([d2, e2], dim=1))
        d1 = self.up1(d2)
        if d1.shape[-2:] != e1.shape[-2:]:
            d1 = F.interpolate(d1, size=e1.shape[-2:], mode="bilinear", align_corners=False)
        return self.head(self.dec1(torch.cat([d1, e1], dim=1)))


def dice_loss_from_logits(logits: torch.Tensor, target: torch.Tensor, eps: float = 1e-6) -> torch.Tensor:
    probs = torch.sigmoid(logits)
    dims = (1, 2, 3)
    intersection = (probs * target).sum(dim=dims)
    union = probs.sum(dim=dims) + target.sum(dim=dims)
    dice = (2 * intersection + eps) / (union + eps)
    return 1.0 - dice.mean()


def confusion_from_probs(probs: torch.Tensor, target: torch.Tensor, threshold: float) -> dict[str, int]:
    pred = probs >= threshold
    truth = target >= 0.5
    tp = int((pred & truth).sum().item())
    tn = int((~pred & ~truth).sum().item())
    fp = int((pred & ~truth).sum().item())
    fn = int((~pred & truth).sum().item())
    return {"tp": tp, "tn": tn, "fp": fp, "fn": fn}


def metrics_from_confusion(conf: dict[str, int]) -> dict[str, Any]:
    tp, tn, fp, fn = conf["tp"], conf["tn"], conf["fp"], conf["fn"]
    total = tp + tn + fp + fn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    iou = tp / (tp + fp + fn) if tp + fp + fn else 0.0
    return {
        **conf,
        "pixels": total,
        "pixel_accuracy": round((tp + tn) / total, 6) if total else 0.0,
        "precision_dynamic": round(precision, 6),
        "recall_dynamic": round(recall, 6),
        "f1_dynamic": round(f1, 6),
        "dynamic_iou": round(iou, 6),
        "balanced_accuracy": round((recall + specificity) / 2, 6),
        "positive_pixel_rate": round((tp + fn) / total, 6) if total else 0.0,
        "predicted_positive_rate": round((tp + fp) / total, 6) if total else 0.0,
    }


def add_conf(a: dict[str, int], b: dict[str, int]) -> dict[str, int]:
    return {key: a.get(key, 0) + b.get(key, 0) for key in ("tp", "tn", "fp", "fn")}


def evaluate_model(
    model: nn.Module,
    loader: DataLoader[tuple[torch.Tensor, torch.Tensor, str]],
    device: torch.device,
    thresholds: list[float],
) -> dict[str, Any]:
    model.eval()
    conf_by_threshold = {threshold: {"tp": 0, "tn": 0, "fp": 0, "fn": 0} for threshold in thresholds}
    loss_sum = 0.0
    batches = 0
    with torch.no_grad():
        for image, mask, _sample_ids in loader:
            image = image.to(device, non_blocking=True)
            mask = mask.to(device, non_blocking=True)
            logits = model(image)
            probs = torch.sigmoid(logits)
            loss = F.binary_cross_entropy_with_logits(logits, mask) + 0.5 * dice_loss_from_logits(logits, mask)
            loss_sum += float(loss.item())
            batches += 1
            for threshold in thresholds:
                conf_by_threshold[threshold] = add_conf(conf_by_threshold[threshold], confusion_from_probs(probs, mask, threshold))
    return {
        "loss": round(loss_sum / batches, 6) if batches else math.nan,
        "threshold_metrics": {f"{threshold:.2f}": metrics_from_confusion(conf) for threshold, conf in conf_by_threshold.items()},
    }


def compute_pos_weight(loader: DataLoader[tuple[torch.Tensor, torch.Tensor, str]], max_weight: float) -> tuple[torch.Tensor, dict[str, Any]]:
    positives = 0.0
    total = 0.0
    for _image, mask, _sample_ids in loader:
        positives += float(mask.sum().item())
        total += float(mask.numel())
    negatives = max(0.0, total - positives)
    raw = negatives / positives if positives else max_weight
    weight = min(max_weight, max(1.0, raw))
    return torch.tensor([weight], dtype=torch.float32), {
        "train_resized_positive_pixels": int(positives),
        "train_resized_total_pixels": int(total),
        "train_resized_positive_pixel_rate": round(positives / total, 6) if total else 0.0,
        "raw_neg_pos_ratio": round(raw, 6),
        "pos_weight_used": round(weight, 6),
    }


def baseline_metrics(rows_by_split: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    train_pos = sum(int(row["dynamic_positive_pixels"]) for row in rows_by_split["train"])
    train_total = sum(int(row["total_pixels"]) for row in rows_by_split["train"])
    train_prior = train_pos / train_total if train_total else 0.0
    for split, rows in rows_by_split.items():
        pos = sum(int(row["dynamic_positive_pixels"]) for row in rows)
        total = sum(int(row["total_pixels"]) for row in rows)
        neg = total - pos
        all_background = {"tp": 0, "tn": neg, "fp": 0, "fn": pos}
        all_dynamic = {"tp": pos, "tn": 0, "fp": neg, "fn": 0}
        prior_pred_dynamic = train_prior >= 0.5
        prior_conf = all_dynamic if prior_pred_dynamic else all_background
        out[split] = {
            "all_background": metrics_from_confusion(all_background),
            "all_dynamic": metrics_from_confusion(all_dynamic),
            "train_prior_threshold_0_5": {
                "train_positive_prior": round(train_prior, 6),
                "predicted_dynamic": prior_pred_dynamic,
                **metrics_from_confusion(prior_conf),
            },
        }
    return out


def export_predictions(
    model: nn.Module,
    rows: list[dict[str, str]],
    *,
    size: tuple[int, int],
    device: torch.device,
    threshold: float,
    output_dir: Path,
    limit: int,
) -> list[dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    selected: list[dict[str, str]] = []
    for split in ("val", "test"):
        selected.extend([row for row in rows if row["split"] == split][: max(1, limit // 2)])
    selected = selected[:limit]
    model.eval()
    exported: list[dict[str, Any]] = []
    width, height = size
    with torch.no_grad():
        for row in selected:
            image = Image.open(ROOT / row["image_path"]).convert("RGB")
            mask = Image.open(ROOT / row["binary_mask_path"]).convert("L")
            image_small = image.resize((width, height), Image.Resampling.BILINEAR)
            mask_small = mask.resize((width, height), Image.Resampling.NEAREST)
            image_np = np.asarray(image_small, dtype=np.float32) / 255.0
            image_t = torch.from_numpy(image_np.transpose(2, 0, 1))[None].to(device)
            probs = torch.sigmoid(model(image_t))[0, 0].detach().cpu().numpy()
            pred = (probs >= threshold).astype(np.uint8) * 255
            prob_img = Image.fromarray(np.clip(probs * 255.0, 0, 255).astype(np.uint8), mode="L")
            pred_img = Image.fromarray(pred, mode="L")
            overlay = image_small.copy()
            red = Image.new("RGB", image_small.size, (255, 0, 0))
            blue = Image.new("RGB", image_small.size, (0, 96, 255))
            pred_alpha = pred_img.point(lambda value: 110 if value > 0 else 0, mode="L")
            truth_alpha = mask_small.point(lambda value: 80 if value > 0 else 0, mode="L")
            overlay.paste(blue, (0, 0), truth_alpha)
            overlay.paste(red, (0, 0), pred_alpha)
            stem = f"{row['split']}_{row['sample_id']}"
            pred_path = output_dir / f"{stem}_pred_mask.png"
            prob_path = output_dir / f"{stem}_prob.png"
            overlay_path = output_dir / f"{stem}_overlay.png"
            pred_img.save(pred_path)
            prob_img.save(prob_path)
            overlay.save(overlay_path)
            conf = confusion_from_probs(torch.from_numpy(probs[None, None]), torch.from_numpy((np.asarray(mask_small) >= 127)[None, None]), threshold)
            exported.append(
                {
                    "sample_id": row["sample_id"],
                    "split": row["split"],
                    "threshold": threshold,
                    "resized_size": [width, height],
                    "prediction_mask_png": rel(pred_path),
                    "probability_png": rel(prob_path),
                    "overlay_png": rel(overlay_path),
                    "metrics": metrics_from_confusion(conf),
                }
            )
    return exported


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


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    metrics = payload["metrics"]
    best = payload["selected_threshold"]
    lines = [
        "# P218 Dynamic-Mask Training Smoke",
        "",
        f"**Status:** {payload['status']}",
        "",
        "## Boundary",
        "",
        payload["claim_boundary"],
        "",
        "## Training Config",
        "",
        f"- Device: `{payload['environment']['device']}`",
        f"- CUDA available: `{payload['environment']['cuda_available']}`",
        f"- Resize: `{payload['config']['resize_width']}x{payload['config']['resize_height']}`",
        f"- Epochs: `{payload['config']['epochs']}`",
        f"- Batch size: `{payload['config']['batch_size']}`",
        f"- Loss: `BCEWithLogitsLoss(pos_weight={payload['class_balance']['pos_weight_used']}) + 0.5 * DiceLoss`",
        f"- Deterministic horizontal augmentation: `{payload['config']['augment_horizontal_flip']}`",
        "",
        "## Metrics",
        "",
        f"- Selected threshold: `{best}` from validation F1.",
        f"- Validation: pixel accuracy `{metrics['val']['selected_threshold']['pixel_accuracy']}`, precision `{metrics['val']['selected_threshold']['precision_dynamic']}`, recall `{metrics['val']['selected_threshold']['recall_dynamic']}`, F1 `{metrics['val']['selected_threshold']['f1_dynamic']}`, dynamic IoU `{metrics['val']['selected_threshold']['dynamic_iou']}`, balanced accuracy `{metrics['val']['selected_threshold']['balanced_accuracy']}`.",
        f"- Test: pixel accuracy `{metrics['test']['selected_threshold']['pixel_accuracy']}`, precision `{metrics['test']['selected_threshold']['precision_dynamic']}`, recall `{metrics['test']['selected_threshold']['recall_dynamic']}`, F1 `{metrics['test']['selected_threshold']['f1_dynamic']}`, dynamic IoU `{metrics['test']['selected_threshold']['dynamic_iou']}`, balanced accuracy `{metrics['test']['selected_threshold']['balanced_accuracy']}`.",
        "",
        "## Baselines",
        "",
        f"- Val all-background dynamic IoU/F1: `{payload['baselines']['val']['all_background']['dynamic_iou']}` / `{payload['baselines']['val']['all_background']['f1_dynamic']}`.",
        f"- Test all-background dynamic IoU/F1: `{payload['baselines']['test']['all_background']['dynamic_iou']}` / `{payload['baselines']['test']['all_background']['f1_dynamic']}`.",
        f"- Train-prior threshold baseline predicts dynamic: `{payload['baselines']['test']['train_prior_threshold_0_5']['predicted_dynamic']}` with train prior `{payload['baselines']['test']['train_prior_threshold_0_5']['train_positive_prior']}`.",
        "",
        "## Prediction Artifacts",
        "",
    ]
    for item in payload["prediction_artifacts"]:
        lines.append(f"- `{item['split']}` `{item['sample_id']}`: `{item['prediction_mask_png']}`, `{item['probability_png']}`, `{item['overlay_png']}`")
    lines.extend(
        [
            "",
            "## P195",
            "",
            f"- Status: `{payload['p195_status'].get('status', 'unknown')}`",
            f"- Human labels remain blank: `{payload['p195_status'].get('human_labels_blank', 'unknown')}`",
            "",
            "## Outputs",
            "",
            f"- JSON evidence: `{payload['outputs']['json']}`",
            f"- Markdown report: `{payload['outputs']['markdown']}`",
            f"- Prediction artifact directory: `{payload['outputs']['prediction_dir']}`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=P217_CSV)
    parser.add_argument("--p217-json", type=Path, default=P217_JSON)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--resize-width", type=int, default=320)
    parser.add_argument("--resize-height", type=int, default=180)
    parser.add_argument("--base-channels", type=int, default=12)
    parser.add_argument("--lr", type=float, default=2e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=218)
    parser.add_argument("--max-pos-weight", type=float, default=4.0)
    parser.add_argument("--require-cuda", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--augment-horizontal-flip", action="store_true")
    parser.add_argument("--prediction-limit", type=int, default=6)
    args = parser.parse_args()

    if args.epochs < 1 or args.epochs > 20:
        raise ValueError("--epochs must be in [1, 20] for the bounded P218 smoke")
    set_determinism(args.seed)
    cuda_available = torch.cuda.is_available()
    if args.require_cuda and not cuda_available:
        raise RuntimeError("P218 smoke requires CUDA by default; pass --no-require-cuda only for compile/debug checks.")
    device = torch.device("cuda" if cuda_available else "cpu")

    rows = read_manifest(args.manifest)
    rows_by_split = split_rows(rows)
    size = (args.resize_width, args.resize_height)
    train_ds = DynamicMaskDataset(rows_by_split["train"], size=size, augment=args.augment_horizontal_flip, seed=args.seed)
    eval_ds = {split: DynamicMaskDataset(items, size=size, augment=False, seed=args.seed) for split, items in rows_by_split.items()}
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0, pin_memory=cuda_available)
    class_loader = DataLoader(DynamicMaskDataset(rows_by_split["train"], size=size, augment=False, seed=args.seed), batch_size=args.batch_size, shuffle=False, num_workers=0)
    eval_loaders = {
        split: DataLoader(ds, batch_size=args.batch_size, shuffle=False, num_workers=0, pin_memory=cuda_available)
        for split, ds in eval_ds.items()
    }
    pos_weight, class_balance = compute_pos_weight(class_loader, args.max_pos_weight)
    pos_weight = pos_weight.to(device)

    model = SmallUNet(base_channels=args.base_channels).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    bce = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    thresholds = [0.30, 0.40, 0.50, 0.60, 0.70]
    history: list[dict[str, Any]] = []
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
            loss = bce(logits, mask) + 0.5 * dice_loss_from_logits(logits, mask)
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
    val_threshold_metrics = raw_eval["val"]["threshold_metrics"]
    selected_threshold = max(
        thresholds,
        key=lambda threshold: (
            val_threshold_metrics[f"{threshold:.2f}"]["f1_dynamic"],
            val_threshold_metrics[f"{threshold:.2f}"]["dynamic_iou"],
            -abs(threshold - 0.5),
        ),
    )
    selected_key = f"{selected_threshold:.2f}"
    metrics = {
        split: {
            "loss": raw_eval[split]["loss"],
            "threshold_metrics": raw_eval[split]["threshold_metrics"],
            "selected_threshold": raw_eval[split]["threshold_metrics"][selected_key],
        }
        for split in SPLITS
    }
    prediction_artifacts = export_predictions(
        model,
        rows,
        size=size,
        device=device,
        threshold=selected_threshold,
        output_dir=args.output_root / "predictions",
        limit=args.prediction_limit,
    )
    p217 = read_json(args.p217_json)
    p195 = p195_status()
    manifest_columns = sorted(rows[0].keys()) if rows else []
    payload = {
        "status": "P218_DYNAMIC_MASK_TRAINING_SMOKE_COMPLETE",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": "P218 trains a compact binary dynamic/non-static mask front-end from P217 dataset-provided semantic masks only. It does not train or claim persistent-map admission control.",
        "source": {
            "p217_csv_manifest": rel(args.manifest),
            "p217_json_manifest": rel(args.p217_json),
            "p217_status": p217.get("status", "unknown"),
            "raw_data_touched": False,
            "labels_from": "P217 binary_mask_path derived from AnnotatedSemanticSet raw_labels_2d + combined_indexedImage",
            "uses_target_admit": False,
            "uses_current_weak_label": False,
            "uses_selection_v5": False,
            "uses_model_predictions_as_labels": False,
            "uses_human_labels": False,
        },
        "leakage_guard": {
            "manifest_columns": manifest_columns,
            "manifest_prohibited_columns": sorted(set(manifest_columns) & PROHIBITED_FIELDS),
            "prohibited_fields": sorted(PROHIBITED_FIELDS),
            "pass": not (set(manifest_columns) & PROHIBITED_FIELDS),
        },
        "dataset": {
            "rows": len(rows),
            "split_counts": dict(sorted(Counter(row["split"] for row in rows).items())),
            "frame_group_counts_by_split": {
                split: len({row["frame_id"] for row in items}) for split, items in sorted(rows_by_split.items())
            },
            "p217_positive_pixel_rate_by_split": p217.get("summary", {}).get("positive_pixel_rate_by_split", {}),
            "p217_overall_positive_pixel_rate": p217.get("summary", {}).get("overall_positive_pixel_rate"),
            "positive_categories": p217.get("target_policy", {}).get("positive_categories", []),
        },
        "config": {
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "resize_width": args.resize_width,
            "resize_height": args.resize_height,
            "base_channels": args.base_channels,
            "lr": args.lr,
            "weight_decay": args.weight_decay,
            "seed": args.seed,
            "augment_horizontal_flip": args.augment_horizontal_flip,
            "thresholds": thresholds,
        },
        "class_balance": class_balance,
        "history": history,
        "selected_threshold": selected_key,
        "metrics": metrics,
        "baselines": baseline_metrics(rows_by_split),
        "prediction_artifacts": prediction_artifacts,
        "p195_status": p195,
        "verification": {
            "cuda_required": args.require_cuda,
            "cuda_available": cuda_available,
            "ran_on_cuda": device.type == "cuda",
            "val_metrics_generated": "val" in metrics,
            "test_metrics_generated": "test" in metrics,
            "p195_remains_blocked": p195.get("status") == "BLOCKED",
            "human_labels_blank": bool(p195.get("human_labels_blank")),
            "label_leakage_guard_pass": not (set(manifest_columns) & PROHIBITED_FIELDS),
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "torch": torch.__version__,
            "cuda_available": cuda_available,
            "device": torch.cuda.get_device_name(0) if cuda_available else "cpu",
            "cuda_version": torch.version.cuda,
            "duration_seconds": round(time.time() - start, 3),
        },
        "outputs": {
            "json": rel(EVIDENCE_JSON),
            "markdown": rel(EXPORT_MD),
            "prediction_dir": rel(args.output_root / "predictions"),
        },
    }
    if not payload["leakage_guard"]["pass"]:
        payload["status"] = "FAILED_LABEL_LEAKAGE_GUARD"
    write_json(EVIDENCE_JSON, payload)
    write_markdown(EXPORT_MD, payload)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "device": payload["environment"]["device"],
                "selected_threshold": selected_key,
                "val": metrics["val"]["selected_threshold"],
                "test": metrics["test"]["selected_threshold"],
                "json": rel(EVIDENCE_JSON),
                "markdown": rel(EXPORT_MD),
                "prediction_artifacts": len(prediction_artifacts),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if payload["status"] == "P218_DYNAMIC_MASK_TRAINING_SMOKE_COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
