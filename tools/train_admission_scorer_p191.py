#!/usr/bin/env python3
"""P191 CPU-only learned admission-scorer smoke.

Trains an auditable logistic admission scorer on the P190 cluster-level dataset,
compares it with the transparent rule baseline, and runs feature ablations to
avoid presenting rule imitation as a false contribution.

No downloads, no GPU, no SAM2 training.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:  # Prefer local numpy when present; keep a pure-Python fallback below.
    import numpy as np
except Exception:  # pragma: no cover - fallback path is retained for portability.
    np = None  # type: ignore[assignment]

try:  # Use sklearn only if already installed locally; never install/download it here.
    from sklearn.linear_model import LogisticRegression  # type: ignore
    from sklearn.preprocessing import StandardScaler  # type: ignore
except Exception:  # pragma: no cover - expected on the current host.
    LogisticRegression = None  # type: ignore[assignment]
    StandardScaler = None  # type: ignore[assignment]

ALL_FEATURES = [
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

ABLATIONS: dict[str, list[str]] = {
    "all_features": ALL_FEATURES,
    "no_dynamic_ratio": [f for f in ALL_FEATURES if f != "dynamic_ratio"],
    "geometry_only": ["mean_center_x", "mean_center_y", "mean_size_x", "mean_size_y"],
    "support_only": ["session_count", "frame_count", "support_count"],
    "no_label_category_flags": [
        f for f in ALL_FEATURES if f not in {"label_purity", "is_forklift_like", "is_infrastructure_like"}
    ],
}

SPLITS = ["train", "val", "test"]


@dataclass
class TrainedModel:
    name: str
    backend: str
    features: list[str]
    means: list[float]
    stds: list[float]
    coefficients: list[float]
    bias: float
    training_history: list[dict[str, float | int]]


def fnum(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def sigmoid_scalar(z: float) -> float:
    if z < -60:
        return 0.0
    if z > 60:
        return 1.0
    return 1.0 / (1.0 + math.exp(-z))


def read_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def matrix(rows: list[dict[str, Any]], features: list[str]) -> list[list[float]]:
    return [[fnum(row[feature]) for feature in features] for row in rows]


def labels(rows: list[dict[str, Any]]) -> list[int]:
    return [int(float(row["target_admit"])) for row in rows]


def standard_stats(train_x: list[list[float]]) -> tuple[list[float], list[float]]:
    n = len(train_x)
    p = len(train_x[0]) if n else 0
    means: list[float] = []
    stds: list[float] = []
    for j in range(p):
        vals = [row[j] for row in train_x]
        mean = sum(vals) / len(vals)
        var = sum((v - mean) ** 2 for v in vals) / len(vals)
        std = math.sqrt(var) or 1.0
        means.append(mean)
        stds.append(std)
    return means, stds


def apply_standard(x: list[list[float]], means: list[float], stds: list[float]) -> list[list[float]]:
    return [[(value - means[j]) / stds[j] for j, value in enumerate(row)] for row in x]


def train_numpy_logreg(
    x_train: list[list[float]],
    y_train: list[int],
    *,
    epochs: int,
    lr: float,
    l2: float,
) -> tuple[list[float], float, list[dict[str, float | int]]]:
    assert np is not None
    x = np.asarray(x_train, dtype=float)
    y = np.asarray(y_train, dtype=float)
    w = np.zeros(x.shape[1], dtype=float)
    b = 0.0
    history: list[dict[str, float | int]] = []
    log_epochs = {1, 10, 100, 500, 1000, epochs}
    for epoch in range(1, epochs + 1):
        logits = x @ w + b
        logits = np.clip(logits, -60, 60)
        prob = 1.0 / (1.0 + np.exp(-logits))
        err = prob - y
        grad_w = (x.T @ err) / len(y) + l2 * w
        grad_b = float(np.mean(err))
        w -= lr * grad_w
        b -= lr * grad_b
        if epoch in log_epochs:
            p = np.clip(prob, 1e-8, 1 - 1e-8)
            loss = float(np.mean(-(y * np.log(p) + (1 - y) * np.log(1 - p))) + 0.5 * l2 * np.sum(w * w))
            history.append({"epoch": epoch, "loss": round(loss, 6)})
    return [float(v) for v in w], float(b), history


def train_python_logreg(
    x_train: list[list[float]],
    y_train: list[int],
    *,
    epochs: int,
    lr: float,
    l2: float,
) -> tuple[list[float], float, list[dict[str, float | int]]]:
    nfeat = len(x_train[0])
    w = [0.0] * nfeat
    b = 0.0
    history: list[dict[str, float | int]] = []
    log_epochs = {1, 10, 100, 500, 1000, epochs}
    for epoch in range(1, epochs + 1):
        gw = [0.0] * nfeat
        gb = 0.0
        loss = 0.0
        for x, y in zip(x_train, y_train):
            prob = sigmoid_scalar(sum(wi * xi for wi, xi in zip(w, x)) + b)
            p = min(max(prob, 1e-8), 1 - 1e-8)
            loss += -(y * math.log(p) + (1 - y) * math.log(1 - p))
            err = prob - y
            for i, xi in enumerate(x):
                gw[i] += err * xi
            gb += err
        m = len(x_train)
        for i in range(nfeat):
            gw[i] = gw[i] / m + l2 * w[i]
            w[i] -= lr * gw[i]
        b -= lr * (gb / m)
        if epoch in log_epochs:
            reg = 0.5 * l2 * sum(v * v for v in w)
            history.append({"epoch": epoch, "loss": round(loss / m + reg, 6)})
    return w, b, history


def train_model(
    rows_by_split: dict[str, list[dict[str, Any]]],
    name: str,
    features: list[str],
    *,
    epochs: int,
    lr: float,
    l2: float,
) -> TrainedModel:
    train_rows = rows_by_split["train"]
    train_x_raw = matrix(train_rows, features)
    train_y = labels(train_rows)
    means, stds = standard_stats(train_x_raw)

    train_x = apply_standard(train_x_raw, means, stds)
    history: list[dict[str, float | int]]

    if LogisticRegression is not None and StandardScaler is not None:
        # sklearn path is intentionally deterministic and local-only.
        scaler = StandardScaler()
        x_np = scaler.fit_transform(matrix(train_rows, features))
        clf = LogisticRegression(random_state=0, solver="liblinear", penalty="l2", C=1.0 / max(l2, 1e-9))
        clf.fit(x_np, train_y)
        means = [float(v) for v in scaler.mean_]
        stds = [float(v) if float(v) != 0 else 1.0 for v in scaler.scale_]
        w = [float(v) for v in clf.coef_[0]]
        b = float(clf.intercept_[0])
        history = [{"epoch": 1, "loss": -1.0}]
        backend = "sklearn_logistic_regression"
    elif np is not None:
        w, b, history = train_numpy_logreg(train_x, train_y, epochs=epochs, lr=lr, l2=l2)
        backend = "numpy_logistic_regression"
    else:
        w, b, history = train_python_logreg(train_x, train_y, epochs=epochs, lr=lr, l2=l2)
        backend = "pure_python_logistic_regression"

    return TrainedModel(
        name=name,
        backend=backend,
        features=features,
        means=means,
        stds=stds,
        coefficients=w,
        bias=b,
        training_history=history,
    )


def predict_probability(model: TrainedModel, row: dict[str, Any]) -> float:
    x = [(fnum(row[feature]) - model.means[j]) / model.stds[j] for j, feature in enumerate(model.features)]
    return sigmoid_scalar(sum(wi * xi for wi, xi in zip(model.coefficients, x)) + model.bias)


def rule_predict(row: dict[str, Any]) -> int:
    return int(
        fnum(row["session_count"]) >= 2
        and fnum(row["frame_count"]) >= 4
        and fnum(row["support_count"]) >= 6
        and fnum(row["dynamic_ratio"]) <= 0.2
        and fnum(row["label_purity"]) >= 0.7
    )


def summarize(scored_rows: list[dict[str, Any]], pred_key: str) -> dict[str, Any]:
    tp = tn = fp = fn = 0
    false_admit_forklift: list[str] = []
    false_reject_infra: list[str] = []
    false_admit: list[str] = []
    false_reject: list[str] = []
    for row in scored_rows:
        y = int(row["target_admit"])
        pred = int(row[pred_key])
        if pred == 1 and y == 1:
            tp += 1
        elif pred == 0 and y == 0:
            tn += 1
        elif pred == 1 and y == 0:
            fp += 1
            false_admit.append(row["sample_id"])
            if int(float(row.get("is_forklift_like", 0))) == 1:
                false_admit_forklift.append(row["sample_id"])
        else:
            fn += 1
            false_reject.append(row["sample_id"])
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
        "false_admits": false_admit,
        "false_rejects": false_reject,
        "false_admit_forklift_like": false_admit_forklift,
        "false_reject_infrastructure_like": false_reject_infra,
    }


def score_model(model: TrainedModel, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    for row in rows:
        p = predict_probability(model, row)
        out = dict(row)
        out["learned_probability"] = p
        out["learned_pred"] = 1 if p >= 0.5 else 0
        out["rule_pred"] = rule_predict(row)
        scored.append(out)
    return scored


def ablation_report(models: dict[str, TrainedModel], rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    report: dict[str, Any] = {}
    for name, model in models.items():
        report[name] = {
            "backend": model.backend,
            "features": model.features,
            "n_features": len(model.features),
            "metrics": {},
            "coefficients": sorted(
                [
                    {"feature": feat, "coefficient": round(coef, 6)}
                    for feat, coef in zip(model.features, model.coefficients)
                ],
                key=lambda d: abs(float(d["coefficient"])),
                reverse=True,
            ),
        }
        for split in SPLITS:
            scored = score_model(model, rows_by_split[split])
            report[name]["metrics"][split] = summarize(scored, "learned_pred")
    return report


def split_counts(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for split, rows in rows_by_split.items():
        out[split] = {
            "n": len(rows),
            "admit": sum(int(float(r["target_admit"])) for r in rows),
            "reject": sum(1 - int(float(r["target_admit"])) for r in rows),
        }
    return out


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    primary = payload["primary_model"]
    metrics = payload["metrics"]
    ablations = payload["ablation"]
    lines = [
        "# P191 Admission-Scorer Learned Smoke",
        "",
        "**Status:** CPU-only learned model smoke completed; no GPU, no downloads, no SAM2 training.",
        f"**Model backend:** `{primary['backend']}`.",
        f"**Dataset:** `{payload['dataset']}` ({payload['n_samples']} samples).",
        "",
        "## Sample Counts",
        "",
    ]
    for split, counts in payload["split_counts"].items():
        lines.append(f"- {split}: n={counts['n']}, admit={counts['admit']}, reject={counts['reject']}")
    lines += ["", "## Primary Model vs Rule Baseline", ""]
    for split in SPLITS:
        learned = metrics[split]["learned"]
        rule = metrics[split]["rule_baseline"]
        lines += [
            f"### {split}",
            f"- Learned all-features scorer: accuracy={learned['accuracy']:.4f}, precision={learned['precision_admit']:.4f}, recall={learned['recall_admit']:.4f}, F1={learned['f1_admit']:.4f}, fp={learned['fp']}, fn={learned['fn']}.",
            f"- Rule baseline: accuracy={rule['accuracy']:.4f}, precision={rule['precision_admit']:.4f}, recall={rule['recall_admit']:.4f}, F1={rule['f1_admit']:.4f}, fp={rule['fp']}, fn={rule['fn']}.",
            "",
        ]
    lines += ["## Ablation Summary", ""]
    for name, report in ablations.items():
        t = report["metrics"]["test"]
        v = report["metrics"]["val"]
        lines.append(
            f"- `{name}` ({report['n_features']} features): val acc/F1={v['accuracy']:.4f}/{v['f1_admit']:.4f}; test acc/F1={t['accuracy']:.4f}/{t['f1_admit']:.4f}; test fp/fn={t['fp']}/{t['fn']}."
        )
    lines += ["", "## Largest All-Feature Coefficients", ""]
    for c in primary["coefficients"][:8]:
        lines.append(f"- `{c['feature']}`: {c['coefficient']:+.6f}")
    lines += [
        "",
        "## Risk / Interpretation",
        "",
        "- This is a real trained CPU model, but only a feasibility smoke: the labels are weak labels generated from the current rule gate.",
        "- The transparent rule baseline scores 1.000 by construction, so the learned model is not yet a contribution claim; it validates the dataset/training/evaluation contract and exposes boundary cases.",
        "- Features such as `dynamic_ratio`, `label_purity`, and label/category flags are potential label-leakage or rule-proxy channels; the ablation block is therefore part of the result, not an optional appendix.",
        "- The test split is Hallway within-site variation, not an independent external deployment site; sample size remains small (51 clusters).",
        "",
        "## P192 Plan",
        "",
        "Mine P191 false admits/false rejects plus near-threshold samples into a human-review boundary-label sheet. The next expansion should add independent admission-boundary labels or pairwise cross-session association labels before claiming a learned component improves on the rule system.",
        "",
    ]
    path.write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="paper/evidence/admission_scorer_dataset_p190.csv")
    parser.add_argument("--output-json", default="paper/evidence/admission_scorer_smoke_p191.json")
    parser.add_argument("--output-md", default="paper/export/admission_scorer_smoke_p191.md")
    parser.add_argument("--epochs", type=int, default=4000)
    parser.add_argument("--lr", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.001)
    args = parser.parse_args()

    dataset = Path(args.dataset)
    rows = read_rows(dataset)
    rows_by_split = {split: [row for row in rows if row.get("split") == split] for split in SPLITS}
    missing = [split for split, split_rows in rows_by_split.items() if not split_rows]
    if missing:
        raise SystemExit(f"missing split rows: {missing}")

    models = {
        name: train_model(rows_by_split, name, features, epochs=args.epochs, lr=args.lr, l2=args.l2)
        for name, features in ABLATIONS.items()
    }
    primary_model = models["all_features"]
    primary_scored = {split: score_model(primary_model, rows_by_split[split]) for split in SPLITS}
    metrics = {
        split: {
            "learned": summarize(scored_rows, "learned_pred"),
            "rule_baseline": summarize(scored_rows, "rule_pred"),
        }
        for split, scored_rows in primary_scored.items()
    }
    primary_coefficients = sorted(
        [
            {"feature": feat, "coefficient": round(coef, 6)}
            for feat, coef in zip(primary_model.features, primary_model.coefficients)
        ],
        key=lambda d: abs(float(d["coefficient"])),
        reverse=True,
    )
    predictions = [
        {
            "sample_id": row["sample_id"],
            "split": split,
            "canonical_label": row["canonical_label"],
            "target_admit": int(row["target_admit"]),
            "learned_probability": round(float(row["learned_probability"]), 6),
            "learned_pred": int(row["learned_pred"]),
            "rule_pred": int(row["rule_pred"]),
        }
        for split in SPLITS
        for row in primary_scored[split]
    ]
    near_threshold = sorted(
        predictions,
        key=lambda row: abs(float(row["learned_probability"]) - 0.5),
    )[:12]

    payload: dict[str, Any] = {
        "phase": "P191-admission-scorer-smoke",
        "dataset": str(dataset),
        "n_samples": len(rows),
        "split_counts": split_counts(rows_by_split),
        "primary_model": {
            "name": "all_features",
            "backend": primary_model.backend,
            "features": primary_model.features,
            "epochs": args.epochs,
            "lr": args.lr,
            "l2": args.l2,
            "bias": round(primary_model.bias, 6),
            "coefficients": primary_coefficients,
            "training_history": primary_model.training_history,
        },
        "rule_baseline": {
            "definition": "session_count>=2 and frame_count>=4 and support_count>=6 and dynamic_ratio<=0.2 and label_purity>=0.7",
            "warning": "This baseline is expected to score 1.000 because P190 labels are weak labels from this rule gate.",
        },
        "metrics": metrics,
        "ablation": ablation_report(models, rows_by_split),
        "predictions": predictions,
        "near_threshold_samples": near_threshold,
        "risk_interpretation": [
            "This is a real trained logistic model but only a feasibility smoke, not a publication-grade learned component.",
            "The labels are weak labels generated by the current rule gate, so dynamic_ratio/label_purity/category features can act as rule proxies.",
            "The rule baseline scoring 1.000 is by construction and must not be used as evidence that a learned model improves the system.",
            "The 51-cluster sample size and within-site Hallway test split limit generalization claims.",
        ],
        "next_expansion_plan_p192": [
            "Export P191 false admits/false rejects and near-threshold samples into a compact human-review sheet.",
            "Add independent admission-boundary labels that are not generated from the current rule gate.",
            "Materialize pairwise cross-session association labels as a second supervised target if the goal shifts from admission to association.",
            "Only after independent labels exist, compare learned models against the transparent rule gate as a potential method contribution.",
        ],
        "constraints_observed": ["CPU-only", "no downloads", "no GPU", "no SAM2 training", "protocol split preserved"],
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
        "backend": primary_model.backend,
        "n_samples": len(rows),
        "primary_metrics": metrics,
        "ablation_test_accuracy_f1": {
            name: {
                "accuracy": report["metrics"]["test"]["accuracy"],
                "f1_admit": report["metrics"]["test"]["f1_admit"],
                "fp": report["metrics"]["test"]["fp"],
                "fn": report["metrics"]["test"]["fn"],
            }
            for name, report in payload["ablation"].items()
        },
    }
    print(json.dumps(stdout_summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
