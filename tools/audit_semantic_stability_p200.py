#!/usr/bin/env python3
"""P200 no-label audit for the P199 semantic-stability auxiliary branch.

This script deliberately audits the P199 category-derived semantic/static-like
target without using human labels or admission-control targets.  Learned stress
tests use only geometry, area, support, session/source, and semantic gate score
numeric fields.  Category labels are used only for explicit degeneracy audits
and the category-definition oracle baseline.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]

ALL_NUMERIC_FEATURES = [
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

FEATURE_SETS = {
    "geometry_only": [
        "mean_center_x",
        "mean_center_y",
        "mean_size_x",
        "mean_size_y",
        "bbox_width",
        "bbox_height",
    ],
    "area_only": ["mask_area_px"],
    "support_only": ["support_count"],
    "no_semantic_gate_score": [
        "mean_center_x",
        "mean_center_y",
        "mean_size_x",
        "mean_size_y",
        "support_count",
        "mask_area_px",
        "bbox_width",
        "bbox_height",
    ],
    "all_numeric": ALL_NUMERIC_FEATURES,
}

TARGET_FIELD = "semantic_static_like"
HUMAN_LABEL_FILES = {
    "boundary_p194": ("paper/evidence/admission_boundary_label_sheet_p194.csv", "human_admit_label"),
    "boundary_p197": ("paper/evidence/admission_boundary_label_sheet_p197_semantic_review.csv", "human_admit_label"),
    "pairs_p194": ("paper/evidence/association_pair_candidates_p194.csv", "human_same_object_label"),
    "pairs_p197": ("paper/evidence/association_pair_candidates_p197_semantic_review.csv", "human_same_object_label"),
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def fnum(value: Any) -> float:
    try:
        out = float(value)
    except Exception:
        return 0.0
    if math.isfinite(out):
        return out
    return 0.0


def target(row: dict[str, str]) -> int:
    text = str(row.get(TARGET_FIELD, "")).strip()
    if text not in {"0", "1"}:
        raise ValueError(f"non-binary {TARGET_FIELD} for {row.get('p199_sample_id')}: {text!r}")
    return int(text)


def usable_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("semantic_target_status") == "non_ambiguous" and row.get(TARGET_FIELD) in {"0", "1"}]


def split_by(rows: list[dict[str, str]], field: str) -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        out[row.get(field, "")].append(row)
    return dict(sorted(out.items()))


def class_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    counts = Counter(target(row) for row in rows)
    return {"dynamic_or_non_static_like": counts[0], "static_like": counts[1]}


def count_by(rows: list[dict[str, str]], *fields: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        key = "|".join(row.get(field, "") for field in fields)
        counts[key] += 1
    return dict(sorted(counts.items()))


def matrix(rows: list[dict[str, str]], features: list[str]) -> np.ndarray:
    return np.array([[fnum(row.get(feature)) for feature in features] for row in rows], dtype=np.float64)


def labels(rows: list[dict[str, str]]) -> np.ndarray:
    return np.array([target(row) for row in rows], dtype=np.float64)


def standardize(train_x: np.ndarray, test_x: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict[str, list[float]]]:
    mean = train_x.mean(axis=0)
    std = train_x.std(axis=0)
    std[std == 0.0] = 1.0
    return (train_x - mean) / std, (test_x - mean) / std, {
        "mean": [round(float(v), 6) for v in mean],
        "std": [round(float(v), 6) for v in std],
    }


def summarize(y_true: list[int] | np.ndarray, y_pred: list[int] | np.ndarray) -> dict[str, Any]:
    truth = [int(v) for v in y_true]
    pred = [int(v) for v in y_pred]
    tp = sum(1 for t, p in zip(truth, pred) if t == 1 and p == 1)
    tn = sum(1 for t, p in zip(truth, pred) if t == 0 and p == 0)
    fp = sum(1 for t, p in zip(truth, pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(truth, pred) if t == 1 and p == 0)
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
    }


def train_logistic(
    train_rows: list[dict[str, str]],
    eval_rows: list[dict[str, str]],
    features: list[str],
    *,
    epochs: int,
    lr: float,
    l2: float,
) -> dict[str, Any]:
    train_counts = Counter(target(row) for row in train_rows)
    eval_counts = Counter(target(row) for row in eval_rows)
    if len(train_counts) < 2:
        return {
            "status": "infeasible_single_class_train",
            "train_class_counts": {"0": train_counts[0], "1": train_counts[1]},
            "eval_class_counts": {"0": eval_counts[0], "1": eval_counts[1]},
        }
    train_x = matrix(train_rows, features)
    eval_x = matrix(eval_rows, features)
    train_y = labels(train_rows)
    eval_y = labels(eval_rows)
    train_z, eval_z, stats = standardize(train_x, eval_x)
    train_z = np.c_[np.ones(train_z.shape[0]), train_z]
    eval_z = np.c_[np.ones(eval_z.shape[0]), eval_z]
    weights = np.zeros(train_z.shape[1], dtype=np.float64)
    for _ in range(epochs):
        logits = np.clip(train_z @ weights, -35.0, 35.0)
        probs = 1.0 / (1.0 + np.exp(-logits))
        grad = (train_z.T @ (probs - train_y)) / len(train_y)
        grad[1:] += l2 * weights[1:]
        weights -= lr * grad
    eval_probs = 1.0 / (1.0 + np.exp(-np.clip(eval_z @ weights, -35.0, 35.0)))
    eval_pred = (eval_probs >= 0.5).astype(int)
    train_probs = 1.0 / (1.0 + np.exp(-np.clip(train_z @ weights, -35.0, 35.0)))
    train_pred = (train_probs >= 0.5).astype(int)
    return {
        "status": "fit",
        "features": features,
        "train_class_counts": {"0": train_counts[0], "1": train_counts[1]},
        "eval_class_counts": {"0": eval_counts[0], "1": eval_counts[1]},
        "standardization": stats,
        "metrics": {
            "train": summarize(train_y, train_pred),
            "eval": summarize(eval_y, eval_pred),
        },
        "weights": [round(float(v), 6) for v in weights],
    }


def majority_baseline(train_rows: list[dict[str, str]], eval_rows: list[dict[str, str]]) -> dict[str, Any]:
    counts = Counter(target(row) for row in train_rows)
    pred_value = 1 if counts[1] >= counts[0] else 0
    return {
        "prediction": pred_value,
        "train_class_counts": {"0": counts[0], "1": counts[1]},
        "metrics": summarize([target(row) for row in eval_rows], [pred_value] * len(eval_rows)),
    }


def category_definition_baseline(eval_rows: list[dict[str, str]]) -> dict[str, Any]:
    truth = [target(row) for row in eval_rows]
    return {
        "description": "Uses the target-defining semantic category mapping; perfect by construction, not learned.",
        "metrics": summarize(truth, truth),
    }


def geometry_threshold_baseline(train_rows: list[dict[str, str]], eval_rows: list[dict[str, str]]) -> dict[str, Any]:
    static_area = [fnum(row.get("mask_area_px") or row.get("support_count")) for row in train_rows if target(row) == 1]
    dynamic_area = [fnum(row.get("mask_area_px") or row.get("support_count")) for row in train_rows if target(row) == 0]
    if not static_area or not dynamic_area:
        return {"status": "infeasible_single_class_train"}
    static_mean = sum(static_area) / len(static_area)
    dynamic_mean = sum(dynamic_area) / len(dynamic_area)
    threshold = (static_mean + dynamic_mean) / 2.0
    static_larger = static_mean >= dynamic_mean
    preds = []
    for row in eval_rows:
        area = fnum(row.get("mask_area_px") or row.get("support_count"))
        preds.append(1 if (area >= threshold) == static_larger else 0)
    return {
        "status": "fit",
        "threshold": round(threshold, 6),
        "static_mean": round(static_mean, 6),
        "dynamic_mean": round(dynamic_mean, 6),
        "static_larger_than_dynamic": static_larger,
        "metrics": summarize([target(row) for row in eval_rows], preds),
    }


def original_split_ablation(rows: list[dict[str, str]], args: argparse.Namespace) -> dict[str, Any]:
    by_split = split_by(rows, "split")
    train_rows = by_split.get("train", [])
    out: dict[str, Any] = {}
    for name, features in FEATURE_SETS.items():
        out[name] = {}
        for split in ["train", "val", "test"]:
            eval_rows = by_split.get(split, [])
            out[name][split] = train_logistic(
                train_rows,
                eval_rows,
                features,
                epochs=args.epochs,
                lr=args.lr,
                l2=args.l2,
            )
    return out


def original_split_baselines(rows: list[dict[str, str]]) -> dict[str, Any]:
    by_split = split_by(rows, "split")
    train_rows = by_split.get("train", [])
    out: dict[str, Any] = {}
    for split in ["train", "val", "test"]:
        eval_rows = by_split.get(split, [])
        out[split] = {
            "majority": majority_baseline(train_rows, eval_rows),
            "geometry_threshold": geometry_threshold_baseline(train_rows, eval_rows),
            "category_definition": category_definition_baseline(eval_rows),
        }
    return out


def leave_group_out(
    rows: list[dict[str, str]],
    group_field: str,
    features: list[str],
    args: argparse.Namespace,
) -> dict[str, Any]:
    groups = split_by(rows, group_field)
    out: dict[str, Any] = {}
    for group, eval_rows in groups.items():
        train_rows = [row for row in rows if row.get(group_field, "") != group]
        eval_class_counts = Counter(target(row) for row in eval_rows)
        train_class_counts = Counter(target(row) for row in train_rows)
        status_notes = []
        if len(train_class_counts) < 2:
            status_notes.append("train split is single-class")
        if len(eval_class_counts) < 2:
            status_notes.append("held-out split is single-class; binary generalization metric is degenerate")
        out[group] = {
            "n_train": len(train_rows),
            "n_eval": len(eval_rows),
            "train_class_counts": {"0": train_class_counts[0], "1": train_class_counts[1]},
            "eval_class_counts": {"0": eval_class_counts[0], "1": eval_class_counts[1]},
            "status_notes": status_notes,
            "model": train_logistic(train_rows, eval_rows, features, epochs=args.epochs, lr=args.lr, l2=args.l2),
            "baselines": {
                "majority": majority_baseline(train_rows, eval_rows),
                "geometry_threshold": geometry_threshold_baseline(train_rows, eval_rows),
                "category_definition": category_definition_baseline(eval_rows),
            },
        }
    return out


def train_on_one_category(rows: list[dict[str, str]], args: argparse.Namespace) -> dict[str, Any]:
    groups = split_by(rows, "canonical_label")
    out: dict[str, Any] = {}
    for train_category, train_rows in groups.items():
        train_counts = Counter(target(row) for row in train_rows)
        out[train_category] = {
            "n_train": len(train_rows),
            "train_class_counts": {"0": train_counts[0], "1": train_counts[1]},
            "status": "infeasible_single_class_train",
            "reason": "Each non-ambiguous canonical category has only one target class, so a one-category supervised binary train split cannot estimate both classes.",
        }
    return out


def category_coupling(rows: list[dict[str, str]]) -> dict[str, Any]:
    groups = split_by(rows, "canonical_label")
    per_category: dict[str, Any] = {}
    deterministic = True
    for category, category_rows in groups.items():
        counts = Counter(target(row) for row in category_rows)
        if counts[0] and counts[1]:
            deterministic = False
        per_category[category] = {
            "n": len(category_rows),
            "class_counts": {"0": counts[0], "1": counts[1]},
            "single_class": not (counts[0] and counts[1]),
        }
    return {
        "target_is_deterministic_given_canonical_label_on_non_ambiguous_rows": deterministic,
        "per_category": per_category,
        "interpretation": (
            "The P199 target is a semantic category definition: forklift maps to dynamic/non-static-like, "
            "while warehouse rack and work table map to static-like. Category labels are therefore not used "
            "as learned-model inputs in P200 stress tests."
        ),
    }


def source_family(row: dict[str, str]) -> str:
    source = row.get("source", "")
    if source in {"same_day", "cross_day", "cross_month"}:
        return "aisle"
    return source or "unknown"


def add_source_family(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out = []
    for row in rows:
        copied = dict(row)
        copied["source_family"] = source_family(row)
        out.append(copied)
    return out


def read_p199_report(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "missing", "path": rel(path)}
    payload = json.loads(path.read_text(encoding="utf-8"))
    models = payload.get("models", {})
    return {
        "status": payload.get("status", "present"),
        "path": rel(path),
        "mlp_metrics": models.get("mlp", {}).get("metrics", {}),
        "logistic_metrics": models.get("logistic", {}).get("metrics", {}),
        "category_definition_baseline": payload.get("baselines", {}).get("category_definition_oracle", {}).get("metrics", {}),
    }


def human_label_audit() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, (relative, column) in HUMAN_LABEL_FILES.items():
        path = ROOT / relative
        if not path.exists():
            out[name] = {"status": "missing", "path": relative, "column": column}
            continue
        rows = read_csv(path)
        blank = sum(1 for row in rows if str(row.get(column, "")).strip() == "")
        nonblank = len(rows) - blank
        out[name] = {
            "status": "checked",
            "path": relative,
            "column": column,
            "total": len(rows),
            "blank": blank,
            "nonblank": nonblank,
        }
    return out


def p195_status() -> dict[str, Any]:
    path = ROOT / "paper/evidence/independent_supervision_gate_p195.json"
    if not path.exists():
        return {"status": "missing", "path": rel(path)}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "status": payload.get("status"),
        "path": rel(path),
        "decision": payload.get("decision"),
        "block_reasons": payload.get("block_reasons", []),
        "label_audit": payload.get("label_audit", {}),
    }


def compact_metrics(entry: dict[str, Any]) -> str:
    metrics = entry.get("metrics", entry)
    return f"acc={metrics.get('accuracy', 0):.4f}, f1={metrics.get('f1_static_like', 0):.4f}"


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    test_ablation = payload["stress_tests"]["original_split_feature_ablations"]
    test_baselines = payload["baselines"]["original_split"]["test"]
    source_out = payload["stress_tests"]["leave_source_out"]
    source_family_out = payload["stress_tests"]["leave_source_family_out"]
    lines = [
        "# P200 Semantic-Stability Audit",
        "",
        f"**Status:** {payload['status']}",
        "",
        "## Scientific Boundary",
        "",
        payload["scientific_boundary"],
        "",
        "## Main Finding",
        "",
        payload["interpretation"],
        "",
        "## Dataset",
        "",
        f"- Input: `{payload['dataset']['path']}`",
        f"- Total rows: {payload['dataset']['total_rows']}",
        f"- Non-ambiguous audited rows: {payload['dataset']['non_ambiguous_rows']}",
        f"- Ambiguous barrier rows excluded from learned stress tests: {payload['dataset']['ambiguous_rows']}",
        f"- Category/target counts: `{payload['dataset']['by_category_and_target']}`",
        f"- Source/target counts: `{payload['dataset']['by_source_and_target']}`",
        "",
        "## Feature Ablations",
        "",
        "Original P199 train/val/test split; learned models use only numeric geometry/area/support/gate features.",
        "",
        "| Feature set | Val acc/F1 | Test acc/F1 |",
        "|---|---:|---:|",
    ]
    for name in FEATURE_SETS:
        val_metrics = test_ablation[name]["val"]["metrics"]["eval"]
        test_metrics = test_ablation[name]["test"]["metrics"]["eval"]
        lines.append(
            f"| `{name}` | {val_metrics['accuracy']:.4f}/{val_metrics['f1_static_like']:.4f} | "
            f"{test_metrics['accuracy']:.4f}/{test_metrics['f1_static_like']:.4f} |"
        )
    lines += [
        "",
        "## Baselines",
        "",
        f"- Majority on P199 test: {compact_metrics(test_baselines['majority'])}",
        f"- Geometry threshold on P199 test: {compact_metrics(test_baselines['geometry_threshold'])}",
        f"- Category-definition oracle on P199 test: {compact_metrics(test_baselines['category_definition'])} (perfect by construction).",
        f"- P199 reported MLP/logistic test: {compact_metrics(payload['p199_reported_model']['mlp_metrics']['test'])} / {compact_metrics(payload['p199_reported_model']['logistic_metrics']['test'])}.",
        "",
        "## Leave-Group-Out Stress Tests",
        "",
        "Leave-category-out is degenerate: every non-ambiguous category is single-class, so there is no held-out category with both target classes. Training on one category is also single-class and infeasible for supervised binary learning.",
        "",
        "| Held-out source | n | class counts 0/1 | Logistic acc/F1 | Majority acc/F1 | Geometry threshold acc/F1 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for source, result in source_out.items():
        counts = result["eval_class_counts"]
        model_metrics = result["model"]["metrics"]["eval"]
        maj_metrics = result["baselines"]["majority"]["metrics"]
        geom_metrics = result["baselines"]["geometry_threshold"]["metrics"]
        lines.append(
            f"| `{source}` | {result['n_eval']} | {counts['0']}/{counts['1']} | "
            f"{model_metrics['accuracy']:.4f}/{model_metrics['f1_static_like']:.4f} | "
            f"{maj_metrics['accuracy']:.4f}/{maj_metrics['f1_static_like']:.4f} | "
            f"{geom_metrics['accuracy']:.4f}/{geom_metrics['f1_static_like']:.4f} |"
        )
    lines += [
        "",
        "| Held-out source family | n | class counts 0/1 | Logistic acc/F1 | Majority acc/F1 | Geometry threshold acc/F1 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for family, result in source_family_out.items():
        counts = result["eval_class_counts"]
        model_metrics = result["model"]["metrics"]["eval"]
        maj_metrics = result["baselines"]["majority"]["metrics"]
        geom_metrics = result["baselines"]["geometry_threshold"]["metrics"]
        lines.append(
            f"| `{family}` | {result['n_eval']} | {counts['0']}/{counts['1']} | "
            f"{model_metrics['accuracy']:.4f}/{model_metrics['f1_static_like']:.4f} | "
            f"{maj_metrics['accuracy']:.4f}/{maj_metrics['f1_static_like']:.4f} | "
            f"{geom_metrics['accuracy']:.4f}/{geom_metrics['f1_static_like']:.4f} |"
        )
    lines += [
        "",
        "## P195 and Label Boundary",
        "",
        f"- P195 status: `{payload['p195_status']['status']}`.",
        "- Human label audit remains blank/non-admission; no labels were fabricated or filled.",
        "- P200 does not train on `selection_v5`, `current_weak_label`, P193 `target_admit`, or human-label columns.",
        "",
        "## Recommendation",
        "",
        payload["p201_recommendation"],
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    dataset_path = ROOT / args.dataset
    all_rows = read_csv(dataset_path)
    usable = add_source_family(usable_rows(all_rows))
    by_split = split_by(usable, "split")
    source_out = leave_group_out(usable, "source", ALL_NUMERIC_FEATURES, args)
    source_family_out = leave_group_out(usable, "source_family", ALL_NUMERIC_FEATURES, args)
    payload: dict[str, Any] = {
        "phase": "P200-semantic-stability-no-label-audit",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "AUDIT_COMPLETED",
        "scientific_boundary": (
            "P200 audits the no-human-label P199 semantic-stability branch only. "
            "The target is semantic/static-like category evidence, not admission control. "
            "P200 does not create human labels, does not train admit/reject from P193/P194/P195 labels, "
            "and does not unblock P195."
        ),
        "dataset": {
            "path": args.dataset,
            "total_rows": len(all_rows),
            "non_ambiguous_rows": len(usable),
            "ambiguous_rows": sum(1 for row in all_rows if row.get("semantic_target_status") == "ambiguous"),
            "by_split_and_target": {
                split: class_counts(rows)
                for split, rows in by_split.items()
            },
            "by_category_and_target": count_by(usable, "canonical_label", TARGET_FIELD),
            "by_source_and_target": count_by(usable, "source", TARGET_FIELD),
            "by_source_family_and_target": count_by(usable, "source_family", TARGET_FIELD),
        },
        "target_coupling": category_coupling(usable),
        "stress_tests": {
            "original_split_feature_ablations": original_split_ablation(usable, args),
            "leave_category_out": leave_group_out(usable, "canonical_label", ALL_NUMERIC_FEATURES, args),
            "train_on_one_category": train_on_one_category(usable, args),
            "leave_source_out": source_out,
            "leave_source_family_out": source_family_out,
        },
        "baselines": {
            "original_split": original_split_baselines(usable),
        },
        "p199_reported_model": read_p199_report(ROOT / "paper/evidence/semantic_stability_scorer_p199.json"),
        "p195_status": p195_status(),
        "human_label_audit": human_label_audit(),
        "constraints_observed": {
            "downloads_performed": False,
            "human_admit_label_filled": False,
            "human_same_object_label_filled": False,
            "admission_target_trained": False,
            "p193_target_admit_used": False,
            "selection_v5_or_current_weak_label_used_as_target": False,
            "current_weak_label_used_as_target": False,
            "category_labels_used_as_learned_features": False,
        },
        "interpretation": (
            "The audit supports a skeptical reading: the P199 target is deterministic from non-ambiguous "
            "semantic category labels, while geometry/area/session-only stress tests are unstable and do not "
            "establish category-independent semantic-stability learning. The P199 CUDA result remains a bounded "
            "pipeline smoke/evidence artifact, not an admission-control result."
        ),
        "limitations": [
            "No independent human labels are present.",
            "Category-definition baseline is perfect by construction.",
            "Leave-category-out is degenerate because each non-ambiguous category has one target class.",
            "Small split sizes, especially validation and cross-month/same-day source subsets, make learned metrics low power.",
            "No CUDA rerun is included; the audit is deterministic NumPy stress evaluation only.",
        ],
        "p201_recommendation": (
            "For P201, prioritize collecting or importing independent human admission/same-object labels and rerun "
            "the P195 gate. If staying no-label, treat semantic stability only as an ontology/category prior and "
            "add new non-ambiguous categories where each semantic category is represented across multiple geometry "
            "and source regimes before claiming learned generalization."
        ),
        "hyperparameters": {
            "epochs": args.epochs,
            "lr": args.lr,
            "l2": args.l2,
        },
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="paper/evidence/semantic_stability_dataset_p199.csv")
    parser.add_argument("--output-json", default="paper/evidence/semantic_stability_audit_p200.json")
    parser.add_argument("--output-md", default="paper/export/semantic_stability_audit_p200.md")
    parser.add_argument("--epochs", type=int, default=1200)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--l2", type=float, default=0.001)
    args = parser.parse_args()

    payload = build_payload(args)
    out_json = ROOT / args.output_json
    out_md = ROOT / args.output_md
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(out_md, payload)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "output_json": args.output_json,
                "output_md": args.output_md,
                "non_ambiguous_rows": payload["dataset"]["non_ambiguous_rows"],
                "p195_status": payload["p195_status"]["status"],
                "all_numeric_test": payload["stress_tests"]["original_split_feature_ablations"]["all_numeric"]["test"]["metrics"]["eval"],
                "category_deterministic": payload["target_coupling"]["target_is_deterministic_given_canonical_label_on_non_ambiguous_rows"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
