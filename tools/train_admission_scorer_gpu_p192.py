#!/usr/bin/env python3
"""P192 CUDA-only admission-scorer training smoke.

This is intentionally a GPU pipeline validation step for the real-model branch.
It trains small PyTorch CUDA logistic/MLP baselines on the P190 cluster dataset,
compares with P191 CPU baseline outputs, and writes a concrete P193 data
expansion plan. It must fail if CUDA is unavailable; there is no CPU fallback.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import platform
import random
import sys
import time
from pathlib import Path
from typing import Any

import torch
from torch import nn

FEATURE_FIELDS = [
    "session_count",
    "frame_count",
    "support_count",
    "dynamic_ratio",
    "label_purity",
    "mean_center_x",
    "mean_center_y",
    "mean_size_x",
    "mean_size_y",
    "is_forklift_like",
    "is_infrastructure_like",
]
SPLITS = ["train", "val", "test"]


class LogisticAdmissionNet(nn.Module):
    def __init__(self, n_features: int) -> None:
        super().__init__()
        self.linear = nn.Linear(n_features, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x).squeeze(-1)


class MLPAdmissionNet(nn.Module):
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
        raise RuntimeError("P192 requires CUDA. torch.cuda.is_available() is False; refusing CPU fallback.")
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


def read_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def split_rows(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out = {split: [row for row in rows if row.get("split") == split] for split in SPLITS}
    missing = [split for split, items in out.items() if not items]
    if missing:
        raise ValueError(f"missing required dataset splits: {missing}")
    return out


def matrix(rows: list[dict[str, Any]]) -> list[list[float]]:
    return [[fnum(row[field]) for field in FEATURE_FIELDS] for row in rows]


def labels(rows: list[dict[str, Any]]) -> list[float]:
    return [float(row["target_admit"]) for row in rows]


def standardize(
    rows_by_split: dict[str, list[dict[str, Any]]],
    device: torch.device,
) -> tuple[dict[str, torch.Tensor], dict[str, torch.Tensor], dict[str, dict[str, float]]]:
    train_x_cpu = torch.tensor(matrix(rows_by_split["train"]), dtype=torch.float32)
    mean = train_x_cpu.mean(dim=0)
    std = train_x_cpu.std(dim=0, unbiased=False)
    std = torch.where(std == 0, torch.ones_like(std), std)
    stats = {
        field: {"mean": float(mean[i]), "std": float(std[i])}
        for i, field in enumerate(FEATURE_FIELDS)
    }
    x_by_split: dict[str, torch.Tensor] = {}
    y_by_split: dict[str, torch.Tensor] = {}
    for split, rows in rows_by_split.items():
        x_cpu = torch.tensor(matrix(rows), dtype=torch.float32)
        y_cpu = torch.tensor(labels(rows), dtype=torch.float32)
        x_by_split[split] = ((x_cpu - mean) / std).to(device)
        y_by_split[split] = y_cpu.to(device)
    return x_by_split, y_by_split, stats


def rule_predict(row: dict[str, Any]) -> int:
    return int(
        fnum(row["session_count"]) >= 2
        and fnum(row["frame_count"]) >= 4
        and fnum(row["support_count"]) >= 6
        and fnum(row["dynamic_ratio"]) <= 0.2
        and fnum(row["label_purity"]) >= 0.7
    )


def summarize(y_true: list[int], y_pred: list[int], rows: list[dict[str, Any]]) -> dict[str, Any]:
    tp = tn = fp = fn = 0
    false_admits: list[str] = []
    false_rejects: list[str] = []
    false_admit_forklift: list[str] = []
    false_reject_infra: list[str] = []
    for truth, pred, row in zip(y_true, y_pred, rows):
        if pred == 1 and truth == 1:
            tp += 1
        elif pred == 0 and truth == 0:
            tn += 1
        elif pred == 1 and truth == 0:
            fp += 1
            false_admits.append(row["sample_id"])
            if int(float(row.get("is_forklift_like", 0))) == 1:
                false_admit_forklift.append(row["sample_id"])
        else:
            fn += 1
            false_rejects.append(row["sample_id"])
            if int(float(row.get("is_infrastructure_like", 0))) == 1:
                false_reject_infra.append(row["sample_id"])
    n = tp + tn + fp + fn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "n": n,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "accuracy": round((tp + tn) / n, 4) if n else 0.0,
        "precision_admit": round(precision, 4),
        "recall_admit": round(recall, 4),
        "f1_admit": round(f1, 4),
        "false_admits": false_admits,
        "false_rejects": false_rejects,
        "false_admit_forklift_like": false_admit_forklift,
        "false_reject_infrastructure_like": false_reject_infra,
    }


def evaluate_model(
    model: nn.Module,
    x_by_split: dict[str, torch.Tensor],
    rows_by_split: dict[str, list[dict[str, Any]]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    model.eval()
    metrics: dict[str, Any] = {}
    predictions: list[dict[str, Any]] = []
    with torch.no_grad():
        for split in SPLITS:
            logits = model(x_by_split[split])
            probs = torch.sigmoid(logits).detach().cpu().tolist()
            y_true = [int(float(row["target_admit"])) for row in rows_by_split[split]]
            y_pred = [1 if prob >= 0.5 else 0 for prob in probs]
            metrics[split] = summarize(y_true, y_pred, rows_by_split[split])
            for row, prob, pred in zip(rows_by_split[split], probs, y_pred):
                predictions.append(
                    {
                        "sample_id": row["sample_id"],
                        "split": split,
                        "canonical_label": row["canonical_label"],
                        "target_admit": int(float(row["target_admit"])),
                        "gpu_probability": round(float(prob), 6),
                        "gpu_pred": pred,
                        "rule_pred": rule_predict(row),
                    }
                )
    return metrics, predictions


def train_model(
    name: str,
    model: nn.Module,
    x_by_split: dict[str, torch.Tensor],
    y_by_split: dict[str, torch.Tensor],
    rows_by_split: dict[str, list[dict[str, Any]]],
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
    log_epochs = {1, 10, 50, 100, 250, 500, epochs}
    torch.cuda.synchronize(device)
    t0 = time.perf_counter()
    for epoch in range(1, epochs + 1):
        model.train()
        optimizer.zero_grad(set_to_none=True)
        logits = model(x_by_split["train"])
        loss = criterion(logits, y_by_split["train"])
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


def rule_baseline_metrics(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for split, rows in rows_by_split.items():
        truth = [int(float(row["target_admit"])) for row in rows]
        pred = [rule_predict(row) for row in rows]
        out[split] = summarize(truth, pred, rows)
    return out


def load_p191(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def p193_plan() -> dict[str, Any]:
    return {
        "objective": "Stop treating the 51 cluster table as the training universe; build larger supervision from existing TorWIC outputs without downloads.",
        "frame_level_expansion": {
            "source_globs": [
                "outputs/torwic_*/frontend_output/all_instances_manifest.json",
                "outputs/torwic_*/observation_output/observations_index.json",
            ],
            "unit": "one detected/segmented object instance per frame",
            "candidate_features": [
                "bbox geometry and area ratio",
                "mask area / coverage",
                "open-vocabulary label and score fields where present",
                "session id, frame id, protocol, scene branch",
                "projection/support counts from observation_output",
                "dynamic-agent proxy labels from forklift-like categories and state_histogram links",
            ],
            "label_strategy": "inherit weak labels by joining frame instances to selected/rejected cluster ids when available; separate uncertain/unmatched examples for review rather than training as negatives",
            "expected_scale": "hundreds to low-thousands of frame/object examples from already materialized TorWIC outputs, depending on join strictness",
            "p193_command": "/home/rui/miniconda3/envs/openvla/bin/python tools/build_admission_frame_dataset_p193.py --outputs-root outputs --cluster-labels paper/evidence/admission_scorer_dataset_p190.csv --output-json paper/evidence/admission_frame_dataset_p193.json --output-csv paper/evidence/admission_frame_dataset_p193.csv",
        },
        "pairwise_association_expansion": {
            "source_globs": [
                "outputs/torwic_*/tracklet_output/tracklets_index.json",
                "outputs/torwic_*/map_output/map_objects.json",
                "outputs/torwic_*selection_v5.json",
            ],
            "unit": "pair of object tracklets/clusters across sessions",
            "candidate_features": [
                "centroid distance and size-ratio differences",
                "canonical label match / label purity",
                "session gap and protocol branch",
                "support/frame-count compatibility",
                "dynamic-ratio compatibility",
            ],
            "label_strategy": "positive if pair belongs to the same retained map-object/cluster lineage; hard negative if same semantic label but rejected or spatially incompatible; keep ambiguous pairs for human review",
            "expected_scale": "O(n^2) pair candidates per protocol before pruning; likely more useful than 51 cluster labels for a learned association scorer",
            "p193_command": "/home/rui/miniconda3/envs/openvla/bin/python tools/build_association_pair_dataset_p193.py --outputs-root outputs --selection-glob 'outputs/torwic_*selection_v5.json' --output-json paper/evidence/association_pair_dataset_p193.json --output-csv paper/evidence/association_pair_dataset_p193.csv",
        },
        "recommended_p193_first_step": "Implement the frame-level dataset builder first because manifests already exist and it expands admission supervision without changing the model target; then build pairwise association labels as P194 if admission still underfits.",
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    gpu = payload["gpu"]
    mlp = payload["models"]["mlp"]
    logistic = payload["models"]["logistic"]
    p191 = payload.get("p191_comparison") or {}
    lines = [
        "# P192 GPU Admission-Scorer Training Smoke",
        "",
        "**Status:** CUDA-only PyTorch smoke completed. This run used GPU and would fail rather than falling back to CPU if CUDA were unavailable.",
        f"**Python:** `{payload['python_executable']}`",
        f"**Torch:** `{gpu['torch_version']}`; CUDA runtime `{gpu['torch_cuda_version']}`; device `{gpu['device']}`; GPU `{gpu['gpu_name']}`.",
        f"**Dataset:** `{payload['dataset']}` ({payload['n_samples']} cluster samples).",
        "",
        "## GPU Evidence",
        "",
        f"- cuda_available: `{gpu['cuda_available']}`",
        f"- device_count: `{gpu['device_count']}`",
        f"- memory_before: allocated={gpu['memory_before']['allocated_bytes']} bytes, reserved={gpu['memory_before']['reserved_bytes']} bytes",
        f"- memory_after: allocated={gpu['memory_after']['allocated_bytes']} bytes, reserved={gpu['memory_after']['reserved_bytes']} bytes",
        f"- memory_peak: allocated={gpu['memory_peak']['max_allocated_bytes']} bytes, reserved={gpu['memory_peak']['max_reserved_bytes']} bytes",
        "",
        "## Metrics: GPU MLP vs GPU Logistic vs Rule Baseline",
        "",
    ]
    for split in SPLITS:
        m = mlp["metrics"][split]
        l = logistic["metrics"][split]
        r = payload["rule_baseline_metrics"][split]
        lines += [
            f"### {split}",
            f"- GPU MLP: accuracy={m['accuracy']:.4f}, precision={m['precision_admit']:.4f}, recall={m['recall_admit']:.4f}, F1={m['f1_admit']:.4f}, fp={m['fp']}, fn={m['fn']}.",
            f"- GPU logistic: accuracy={l['accuracy']:.4f}, precision={l['precision_admit']:.4f}, recall={l['recall_admit']:.4f}, F1={l['f1_admit']:.4f}, fp={l['fp']}, fn={l['fn']}.",
            f"- Rule baseline: accuracy={r['accuracy']:.4f}, precision={r['precision_admit']:.4f}, recall={r['recall_admit']:.4f}, F1={r['f1_admit']:.4f}, fp={r['fp']}, fn={r['fn']}.",
            "",
        ]
    lines += [
        "## P191 CPU Baseline Comparison",
        "",
    ]
    if p191:
        for split in SPLITS:
            cpu = p191["metrics"][split]["learned"]
            m = mlp["metrics"][split]
            lines.append(
                f"- {split}: P191 CPU all-features acc/F1={cpu['accuracy']:.4f}/{cpu['f1_admit']:.4f}; P192 GPU MLP acc/F1={m['accuracy']:.4f}/{m['f1_admit']:.4f}."
            )
    else:
        lines.append("- P191 JSON not found; comparison skipped.")
    lines += [
        "",
        "## Training Runtime",
        "",
        f"- GPU MLP training time: {mlp['training_time_seconds']:.6f} s",
        f"- GPU logistic training time: {logistic['training_time_seconds']:.6f} s",
        "",
        "## Risk / Interpretation",
        "",
        "- This really used CUDA, but it remains a pipeline validation step: 51 cluster samples are too few for a publishable GPU model claim.",
        "- Rule baseline remains artificially strong because P190 labels are weak labels derived from the same rule gate.",
        "- Dynamic ratio, label purity, and label/category flags may leak the rule decision; do not claim learned superiority until independent labels exist.",
        "- The right next step is larger real-data dataset construction from existing TorWIC manifests/tracklets/map objects, not more epochs on 51 clusters.",
        "",
        "## P193 Real-Data Expansion Plan",
        "",
        "### Frame-level admission dataset",
        f"- Source globs: `{', '.join(payload['p193_real_data_expansion_plan']['frame_level_expansion']['source_globs'])}`",
        f"- Command: `{payload['p193_real_data_expansion_plan']['frame_level_expansion']['p193_command']}`",
        "",
        "### Pairwise cross-session association dataset",
        f"- Source globs: `{', '.join(payload['p193_real_data_expansion_plan']['pairwise_association_expansion']['source_globs'])}`",
        f"- Command: `{payload['p193_real_data_expansion_plan']['pairwise_association_expansion']['p193_command']}`",
        "",
        f"**Recommendation:** {payload['p193_real_data_expansion_plan']['recommended_p193_first_step']}",
        "",
    ]
    path.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="paper/evidence/admission_scorer_dataset_p190.csv")
    parser.add_argument("--p191-json", default="paper/evidence/admission_scorer_smoke_p191.json")
    parser.add_argument("--output-json", default="paper/evidence/admission_scorer_gpu_p192.json")
    parser.add_argument("--output-md", default="paper/export/admission_scorer_gpu_p192.md")
    parser.add_argument("--epochs", type=int, default=800)
    parser.add_argument("--lr", type=float, default=0.01)
    parser.add_argument("--weight-decay", type=float, default=0.001)
    parser.add_argument("--hidden", type=int, default=16)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    device = require_cuda()
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    random.seed(args.seed)
    torch.cuda.reset_peak_memory_stats(device)
    memory_before = gpu_memory(device)

    dataset_path = Path(args.dataset)
    rows = read_rows(dataset_path)
    rows_by_split = split_rows(rows)
    x_by_split, y_by_split, stats = standardize(rows_by_split, device)

    logistic_result = train_model(
        "logistic",
        LogisticAdmissionNet(len(FEATURE_FIELDS)),
        x_by_split,
        y_by_split,
        rows_by_split,
        device=device,
        epochs=args.epochs,
        lr=args.lr,
        weight_decay=args.weight_decay,
    )
    mlp_result = train_model(
        "mlp",
        MLPAdmissionNet(len(FEATURE_FIELDS), args.hidden),
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

    p191 = load_p191(Path(args.p191_json))
    payload: dict[str, Any] = {
        "phase": "P192-gpu-admission-scorer-training",
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "dataset": str(dataset_path),
        "n_samples": len(rows),
        "split_counts": {
            split: {
                "n": len(split_rows_),
                "admit": sum(int(float(row["target_admit"])) for row in split_rows_),
                "reject": sum(1 - int(float(row["target_admit"])) for row in split_rows_),
            }
            for split, split_rows_ in rows_by_split.items()
        },
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
        "models": {
            "logistic": logistic_result,
            "mlp": mlp_result,
        },
        "rule_baseline_metrics": rule_baseline_metrics(rows_by_split),
        "p191_comparison": p191,
        "interpretation": [
            "P192 corrects P191 by validating the real-model path on CUDA; there is no CPU fallback in this script.",
            "Because the dataset has only 51 rule-derived cluster labels, the GPU model is a pipeline check and not the terminal research result.",
            "P193 must expand supervision from existing TorWIC outputs to frame-level or pairwise association samples before model quality claims are meaningful.",
        ],
        "p193_real_data_expansion_plan": p193_plan(),
        "constraints_observed": ["cuda-only", "no CPU fallback", "no downloads", "no SAM2 full training", "existing P190 dataset only for smoke"],
    }

    out_json = Path(args.output_json)
    out_md = Path(args.output_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    write_markdown(out_md, payload)

    stdout_summary = {
        "output_json": str(out_json),
        "output_md": str(out_md),
        "cuda_available": payload["gpu"]["cuda_available"],
        "device": payload["gpu"]["device"],
        "gpu_name": payload["gpu"]["gpu_name"],
        "torch_version": payload["gpu"]["torch_version"],
        "torch_cuda_version": payload["gpu"]["torch_cuda_version"],
        "memory_before": memory_before,
        "memory_after": memory_after,
        "memory_peak": memory_peak,
        "mlp_training_time_seconds": mlp_result["training_time_seconds"],
        "logistic_training_time_seconds": logistic_result["training_time_seconds"],
        "mlp_metrics": mlp_result["metrics"],
        "logistic_metrics": logistic_result["metrics"],
        "p193_first_command": payload["p193_real_data_expansion_plan"]["frame_level_expansion"]["p193_command"],
    }
    print(json.dumps(stdout_summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
