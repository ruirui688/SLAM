#!/usr/bin/env python3
"""CUDA smoke for the P199 semantic-stability auxiliary scorer.

This trains on ``semantic_static_like`` from P199, not on admission labels.
The target is derived from semantic category hints and therefore the strongest
baseline is the category-definition baseline; model metrics are a bounded
pipeline check, not evidence of learned map admission control.
"""
from __future__ import annotations

import argparse
import csv
import json
import platform
import random
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch
from torch import nn


ROOT = Path(__file__).resolve().parents[1]
SPLITS = ["train", "val", "test"]
FEATURE_FIELDS = [
    "mean_center_x",
    "mean_center_y",
    "mean_size_x",
    "mean_size_y",
    "support_count",
    "mask_area_px",
    "bbox_width",
    "bbox_height",
    "semantic_gate_score",
]


class LogisticSemanticStabilityNet(nn.Module):
    def __init__(self, n_features: int) -> None:
        super().__init__()
        self.linear = nn.Linear(n_features, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x).squeeze(-1)


class MLPSemanticStabilityNet(nn.Module):
    def __init__(self, n_features: int, hidden: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_features, hidden),
            nn.ReLU(),
            nn.Dropout(p=0.05),
            nn.Linear(hidden, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


def require_cuda() -> torch.device:
    if not torch.cuda.is_available():
        raise RuntimeError("P199 CUDA smoke requires CUDA; refusing CPU fallback for the smoke run.")
    return torch.device("cuda")


def gpu_memory(device: torch.device) -> dict[str, int]:
    idx = device.index if device.index is not None else torch.cuda.current_device()
    return {
        "allocated_bytes": int(torch.cuda.memory_allocated(idx)),
        "reserved_bytes": int(torch.cuda.memory_reserved(idx)),
        "max_allocated_bytes": int(torch.cuda.max_memory_allocated(idx)),
        "max_reserved_bytes": int(torch.cuda.max_memory_reserved(idx)),
    }


def fnum(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def target_value(row: dict[str, str]) -> int:
    text = str(row.get("semantic_static_like", "")).strip()
    if text not in {"0", "1"}:
        raise ValueError(f"non-binary semantic_static_like for {row.get('p199_sample_id')}: {text!r}")
    return int(text)


def usable_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("semantic_target_status") == "non_ambiguous" and row.get("semantic_static_like") in {"0", "1"}]


def split_rows(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    out = {split: [row for row in rows if row.get("split") == split] for split in SPLITS}
    missing = [split for split, items in out.items() if not items]
    if missing:
        raise ValueError(f"missing required dataset splits: {missing}")
    return out


def matrix(rows: list[dict[str, str]], features: list[str]) -> list[list[float]]:
    return [[fnum(row.get(field)) for field in features] for row in rows]


def labels(rows: list[dict[str, str]]) -> list[float]:
    return [float(target_value(row)) for row in rows]


def standardize(
    rows_by_split: dict[str, list[dict[str, str]]],
    device: torch.device,
    features: list[str],
) -> tuple[dict[str, torch.Tensor], dict[str, torch.Tensor], dict[str, dict[str, float]]]:
    train_x_cpu = torch.tensor(matrix(rows_by_split["train"], features), dtype=torch.float32)
    mean = train_x_cpu.mean(dim=0)
    std = train_x_cpu.std(dim=0, unbiased=False)
    std = torch.where(std == 0, torch.ones_like(std), std)
    stats = {
        field: {"mean": float(mean[i]), "std": float(std[i])}
        for i, field in enumerate(features)
    }
    x_by_split: dict[str, torch.Tensor] = {}
    y_by_split: dict[str, torch.Tensor] = {}
    for split, rows in rows_by_split.items():
        x_cpu = torch.tensor(matrix(rows, features), dtype=torch.float32)
        y_cpu = torch.tensor(labels(rows), dtype=torch.float32)
        x_by_split[split] = ((x_cpu - mean) / std).to(device)
        y_by_split[split] = y_cpu.to(device)
    return x_by_split, y_by_split, stats


def summarize(y_true: list[int], y_pred: list[int], rows: list[dict[str, str]]) -> dict[str, Any]:
    tp = tn = fp = fn = 0
    errors: list[dict[str, str]] = []
    for truth, pred, row in zip(y_true, y_pred, rows):
        if pred == 1 and truth == 1:
            tp += 1
        elif pred == 0 and truth == 0:
            tn += 1
        elif pred == 1 and truth == 0:
            fp += 1
            errors.append({"p199_sample_id": row["p199_sample_id"], "error": "dynamic_predicted_static"})
        else:
            fn += 1
            errors.append({"p199_sample_id": row["p199_sample_id"], "error": "static_predicted_dynamic"})
    n = tp + tn + fp + fn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "n": n,
        "tp_static_like": tp,
        "tn_dynamic_or_non_static_like": tn,
        "fp_dynamic_predicted_static": fp,
        "fn_static_predicted_dynamic": fn,
        "accuracy": round((tp + tn) / n, 4) if n else 0.0,
        "precision_static_like": round(precision, 4),
        "recall_static_like": round(recall, 4),
        "f1_static_like": round(f1, 4),
        "errors": errors,
    }


def evaluate_model(
    model: nn.Module,
    x_by_split: dict[str, torch.Tensor],
    rows_by_split: dict[str, list[dict[str, str]]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    model.eval()
    metrics: dict[str, Any] = {}
    predictions: list[dict[str, Any]] = []
    with torch.no_grad():
        for split in SPLITS:
            probs = torch.sigmoid(model(x_by_split[split])).detach().cpu().tolist()
            y_true = [target_value(row) for row in rows_by_split[split]]
            y_pred = [1 if prob >= 0.5 else 0 for prob in probs]
            metrics[split] = summarize(y_true, y_pred, rows_by_split[split])
            for row, prob, pred in zip(rows_by_split[split], probs, y_pred):
                predictions.append(
                    {
                        "p199_sample_id": row["p199_sample_id"],
                        "split": split,
                        "canonical_label": row["canonical_label"],
                        "semantic_stability_target": row["semantic_stability_target"],
                        "semantic_static_like": target_value(row),
                        "semantic_stability_probability_static_like": round(float(prob), 6),
                        "semantic_stability_pred_static_like": pred,
                    }
                )
    return metrics, predictions


def train_model(
    name: str,
    model: nn.Module,
    x_by_split: dict[str, torch.Tensor],
    y_by_split: dict[str, torch.Tensor],
    rows_by_split: dict[str, list[dict[str, str]]],
    *,
    device: torch.device,
    epochs: int,
    lr: float,
    weight_decay: float,
) -> dict[str, Any]:
    model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    criterion = nn.BCEWithLogitsLoss()
    history: list[dict[str, float | int]] = []
    log_epochs = {1, 10, 50, 100, 200, epochs}
    torch.cuda.synchronize(device)
    t0 = time.perf_counter()
    for epoch in range(1, epochs + 1):
        model.train()
        optimizer.zero_grad(set_to_none=True)
        loss = criterion(model(x_by_split["train"]), y_by_split["train"])
        loss.backward()
        optimizer.step()
        if epoch in log_epochs:
            model.eval()
            with torch.no_grad():
                train_loss = float(criterion(model(x_by_split["train"]), y_by_split["train"]).detach().cpu())
                val_loss = float(criterion(model(x_by_split["val"]), y_by_split["val"]).detach().cpu())
            history.append({"epoch": epoch, "train_loss": round(train_loss, 6), "val_loss": round(val_loss, 6)})
    torch.cuda.synchronize(device)
    elapsed = time.perf_counter() - t0
    metrics, predictions = evaluate_model(model, x_by_split, rows_by_split)
    return {
        "name": name,
        "architecture": repr(model),
        "epochs": epochs,
        "lr": lr,
        "weight_decay": weight_decay,
        "training_time_seconds": round(elapsed, 6),
        "history": history,
        "metrics": metrics,
        "predictions": predictions,
    }


def majority_baseline(rows_by_split: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    train_counts = Counter(target_value(row) for row in rows_by_split["train"])
    majority = 1 if train_counts[1] >= train_counts[0] else 0
    return {
        split: summarize(
            [target_value(row) for row in rows],
            [majority for _ in rows],
            rows,
        )
        for split, rows in rows_by_split.items()
    }


def category_definition_baseline(rows_by_split: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    return {
        split: summarize(
            [target_value(row) for row in rows],
            [target_value(row) for row in rows],
            rows,
        )
        for split, rows in rows_by_split.items()
    }


def geometry_area_baseline(rows_by_split: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    train_rows = rows_by_split["train"]
    static_areas = [fnum(row.get("mask_area_px") or row.get("support_count")) for row in train_rows if target_value(row) == 1]
    dynamic_areas = [fnum(row.get("mask_area_px") or row.get("support_count")) for row in train_rows if target_value(row) == 0]
    threshold = ((sum(static_areas) / len(static_areas)) + (sum(dynamic_areas) / len(dynamic_areas))) / 2.0
    static_larger = (sum(static_areas) / len(static_areas)) >= (sum(dynamic_areas) / len(dynamic_areas))
    out: dict[str, Any] = {"threshold": round(threshold, 6), "static_larger_than_dynamic": static_larger, "metrics": {}}
    for split, rows in rows_by_split.items():
        truth = [target_value(row) for row in rows]
        pred = []
        for row in rows:
            area = fnum(row.get("mask_area_px") or row.get("support_count"))
            pred.append(1 if (area >= threshold) == static_larger else 0)
        out["metrics"][split] = summarize(truth, pred, rows)
    return out


def split_counts(rows_by_split: dict[str, list[dict[str, str]]]) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for split, rows in rows_by_split.items():
        targets = Counter(row["semantic_stability_target"] for row in rows)
        out[split] = {"n": len(rows), **dict(sorted(targets.items()))}
    return out


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    mlp = payload["models"]["mlp"]
    logistic = payload["models"]["logistic"]
    lines = [
        "# P199 Semantic-Stability Scorer CUDA Smoke",
        "",
        "**Status:** CUDA smoke completed for an auxiliary semantic/static-vs-dynamic target.",
        "",
        "## Scientific Boundary",
        "",
        payload["scientific_boundary"],
        "",
        "## Environment",
        "",
        f"- Command: `{payload['actual_training_command']}`",
        f"- Python: `{payload['python_executable']}`",
        f"- Torch: `{payload['gpu']['torch_version']}`; CUDA runtime `{payload['gpu']['torch_cuda_version']}`; GPU `{payload['gpu']['gpu_name']}`",
        "",
        "## Dataset",
        "",
        f"- Dataset: `{payload['dataset']}`",
        f"- Non-ambiguous rows used: {payload['n_training_rows']}",
        f"- Split counts: `{payload['split_counts']}`",
        f"- Features: `{payload['features']}`",
        "",
        "## Metrics",
        "",
    ]
    for split in SPLITS:
        m = mlp["metrics"][split]
        l = logistic["metrics"][split]
        maj = payload["baselines"]["majority_static_like"]["metrics"][split]
        geom = payload["baselines"]["geometry_area_rule"]["metrics"][split]
        cat = payload["baselines"]["category_definition_oracle"]["metrics"][split]
        lines += [
            f"### {split}",
            f"- MLP: accuracy={m['accuracy']:.4f}, F1(static-like)={m['f1_static_like']:.4f}, fp={m['fp_dynamic_predicted_static']}, fn={m['fn_static_predicted_dynamic']}.",
            f"- Logistic: accuracy={l['accuracy']:.4f}, F1(static-like)={l['f1_static_like']:.4f}, fp={l['fp_dynamic_predicted_static']}, fn={l['fn_static_predicted_dynamic']}.",
            f"- Majority baseline: accuracy={maj['accuracy']:.4f}, F1(static-like)={maj['f1_static_like']:.4f}.",
            f"- Geometry area baseline: accuracy={geom['accuracy']:.4f}, F1(static-like)={geom['f1_static_like']:.4f}.",
            f"- Category-definition baseline: accuracy={cat['accuracy']:.4f}, F1(static-like)={cat['f1_static_like']:.4f}.",
            "",
        ]
    lines += [
        "## Limitations",
        "",
        "- The target is category-derived and weak; the category-definition baseline is perfect by construction on non-ambiguous rows.",
        "- Barrier rows are excluded from training because their semantic hint is mixed static/dynamic.",
        "- This is not an admission-control model and does not use independent persistent-map labels.",
        "- P195 remains blocked until real human labels exist.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="paper/evidence/semantic_stability_dataset_p199.csv")
    parser.add_argument("--output-json", default="paper/evidence/semantic_stability_scorer_p199.json")
    parser.add_argument("--output-md", default="paper/export/semantic_stability_scorer_p199.md")
    parser.add_argument("--actual-command", default="")
    parser.add_argument("--epochs", type=int, default=300)
    parser.add_argument("--lr", type=float, default=0.01)
    parser.add_argument("--weight-decay", type=float, default=0.001)
    parser.add_argument("--hidden", type=int, default=12)
    parser.add_argument("--seed", type=int, default=199)
    args = parser.parse_args()

    device = require_cuda()
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    random.seed(args.seed)
    torch.cuda.reset_peak_memory_stats(device)
    memory_before = gpu_memory(device)

    dataset_path = ROOT / args.dataset
    all_rows = read_rows(dataset_path)
    rows = usable_rows(all_rows)
    rows_by_split = split_rows(rows)
    x_by_split, y_by_split, stats = standardize(rows_by_split, device, FEATURE_FIELDS)

    logistic = train_model(
        "logistic_semantic_stability",
        LogisticSemanticStabilityNet(len(FEATURE_FIELDS)),
        x_by_split,
        y_by_split,
        rows_by_split,
        device=device,
        epochs=args.epochs,
        lr=args.lr,
        weight_decay=args.weight_decay,
    )
    mlp = train_model(
        "mlp_semantic_stability",
        MLPSemanticStabilityNet(len(FEATURE_FIELDS), args.hidden),
        x_by_split,
        y_by_split,
        rows_by_split,
        device=device,
        epochs=args.epochs,
        lr=args.lr,
        weight_decay=args.weight_decay,
    )
    torch.cuda.synchronize(device)
    memory_after = gpu_memory(device)
    memory_peak = gpu_memory(device)

    default_command = (
        "LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib: conda run -n tram "
        "python tools/train_semantic_stability_scorer_p199.py"
    )
    payload: dict[str, Any] = {
        "phase": "P199-no-human-semantic-stability-scorer-cuda-smoke",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "CUDA_SMOKE_COMPLETED",
        "scientific_boundary": (
            "P199 is a no-human-label auxiliary semantic stability scorer. It predicts a "
            "semantic/static-vs-dynamic category prior derived from semantic categories, not "
            "persistent-map admission. It does not replace independent labels, does not unblock "
            "P195, and does not support learned admission-control claims."
        ),
        "environment_basis": "README.md §0.3 tram environment; CUDA smoke refuses CPU fallback.",
        "actual_training_command": args.actual_command or default_command,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "dataset": args.dataset,
        "n_total_rows": len(all_rows),
        "n_training_rows": len(rows),
        "excluded_rows": {
            "ambiguous": sum(1 for row in all_rows if row.get("semantic_target_status") == "ambiguous"),
            "unknown": sum(1 for row in all_rows if row.get("semantic_target_status") == "unknown"),
        },
        "target": {
            "field": "semantic_static_like",
            "positive_class": "static_like semantic category",
            "negative_class": "dynamic_or_non_static_like semantic category",
            "not_admission_control": True,
        },
        "split_counts": split_counts(rows_by_split),
        "features": FEATURE_FIELDS,
        "standardization": stats,
        "gpu": {
            "cuda_available": bool(torch.cuda.is_available()),
            "device": str(device),
            "device_count": int(torch.cuda.device_count()),
            "gpu_name": torch.cuda.get_device_name(device),
            "torch_version": torch.__version__,
            "torch_cuda_version": torch.version.cuda,
            "memory_before": memory_before,
            "memory_after": memory_after,
            "memory_peak": memory_peak,
        },
        "models": {"logistic": logistic, "mlp": mlp},
        "baselines": {
            "majority_static_like": {
                "description": "Predict the train-set majority class for every row.",
                "metrics": majority_baseline(rows_by_split),
            },
            "geometry_area_rule": {
                "description": "Threshold mask/support area using train split class means.",
                **geometry_area_baseline(rows_by_split),
            },
            "category_definition_oracle": {
                "description": "Reconstruct the semantic category definition. This is perfect by construction and is not a learned baseline.",
                "metrics": category_definition_baseline(rows_by_split),
            },
        },
        "constraints_observed": {
            "human_admit_label_filled": False,
            "human_same_object_label_filled": False,
            "admission_target_trained": False,
            "p193_target_admit_used": False,
            "selection_v5_or_current_weak_label_used_as_target": False,
            "model_prediction_used_as_target": False,
            "downloads_performed": False,
        },
        "limitations": [
            "Category-derived target, not independent ground truth.",
            "Category-definition baseline is perfect by construction.",
            "Ambiguous barrier rows excluded from training.",
            "No claim of persistent-map admission control is supported.",
        ],
    }

    out_json = ROOT / args.output_json
    out_md = ROOT / args.output_md
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(out_md, payload)
    print(
        json.dumps(
            {
                "output_json": args.output_json,
                "output_md": args.output_md,
                "gpu_name": payload["gpu"]["gpu_name"],
                "n_training_rows": payload["n_training_rows"],
                "mlp_metrics": mlp["metrics"],
                "logistic_metrics": logistic["metrics"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
