#!/usr/bin/env python3
"""Prepare a lightweight cluster-level admission-scorer dataset for P190.

This script does not train a model. It materializes a deterministic feature table
from existing TorWIC selection artifacts and runs a rule-baseline smoke check so
that the first real-model training step can start from a fixed dataset contract.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

DEFAULT_SOURCES = [
    ("same_day", "outputs/torwic_same_day_aisle_bundle_selection_v5.json", "train"),
    ("cross_day", "outputs/torwic_cross_day_aisle_bundle_selection_v5.json", "train"),
    ("cross_month", "outputs/torwic_cross_month_aisle_bundle_selection_v5.json", "val"),
    ("hallway", "outputs/torwic_hallway_protocol_current_selection_v5.json", "test"),
]

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

INFRA_LABELS = {"yellow barrier", "work table", "warehouse rack", "barrier"}


def num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_samples(root: Path) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for source_name, rel_path, split in DEFAULT_SOURCES:
        path = root / rel_path
        data = json.loads(path.read_text())
        for label_name, target in [("selected", 1), ("rejected", 0)]:
            for item in data.get(label_name, []):
                canonical = str(item.get("canonical_label", "")).strip().lower()
                mean_center = item.get("mean_center_xyz") or [0, 0, 0]
                mean_size = item.get("mean_size_xyz") or [0, 0, 0]
                sample = {
                    "sample_id": f"{source_name}:{item.get('cluster_id')}",
                    "source": source_name,
                    "split": split,
                    "cluster_id": item.get("cluster_id", ""),
                    "canonical_label": canonical,
                    "dominant_state": item.get("dominant_state", ""),
                    "target_admit": target,
                    "session_count": num(item.get("session_count")),
                    "frame_count": num(item.get("frame_count")),
                    "support_count": num(item.get("support_count")),
                    "dynamic_ratio": num(item.get("dynamic_ratio")),
                    "label_purity": num(item.get("label_purity")),
                    "mean_center_x": num(mean_center[0] if len(mean_center) > 0 else 0),
                    "mean_center_y": num(mean_center[1] if len(mean_center) > 1 else 0),
                    "mean_size_x": num(mean_size[0] if len(mean_size) > 0 else 0),
                    "mean_size_y": num(mean_size[1] if len(mean_size) > 1 else 0),
                    "is_forklift_like": 1 if "fork" in canonical or "lift" in canonical else 0,
                    "is_infrastructure_like": 1 if canonical in INFRA_LABELS else 0,
                }
                samples.append(sample)
    return samples


def rule_predict(sample: dict[str, Any]) -> int:
    return int(
        sample["session_count"] >= 2
        and sample["frame_count"] >= 4
        and sample["support_count"] >= 6
        and sample["dynamic_ratio"] <= 0.2
        and sample["label_purity"] >= 0.7
    )


def metrics(samples: list[dict[str, Any]]) -> dict[str, Any]:
    by_split: dict[str, dict[str, int]] = {}
    for sample in samples:
        split = sample["split"]
        pred = rule_predict(sample)
        truth = int(sample["target_admit"])
        bucket = by_split.setdefault(split, {"n": 0, "correct": 0, "tp": 0, "tn": 0, "fp": 0, "fn": 0})
        bucket["n"] += 1
        bucket["correct"] += int(pred == truth)
        if pred == 1 and truth == 1:
            bucket["tp"] += 1
        elif pred == 0 and truth == 0:
            bucket["tn"] += 1
        elif pred == 1 and truth == 0:
            bucket["fp"] += 1
        else:
            bucket["fn"] += 1
    for bucket in by_split.values():
        bucket["accuracy"] = round(bucket["correct"] / bucket["n"], 4) if bucket["n"] else 0.0
    return by_split


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-json", default="paper/evidence/admission_scorer_dataset_p190.json")
    parser.add_argument("--output-csv", default="paper/evidence/admission_scorer_dataset_p190.csv")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    samples = load_samples(root)
    split_counts: dict[str, int] = {}
    label_counts: dict[str, dict[str, int]] = {}
    for s in samples:
        split_counts[s["split"]] = split_counts.get(s["split"], 0) + 1
        label_counts.setdefault(s["split"], {"admit": 0, "reject": 0})["admit" if s["target_admit"] else "reject"] += 1

    out_json = root / args.output_json
    out_csv = root / args.output_csv
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "phase": "P190-real-model-training-readiness",
        "task": "cluster_level_admission_scorer_dataset",
        "sources": [
            {"name": name, "path": rel, "split": split} for name, rel, split in DEFAULT_SOURCES
        ],
        "target": "target_admit (1=selected stable map object, 0=rejected)",
        "features": FEATURE_FIELDS,
        "split_strategy": "train=same_day+cross_day Aisle, val=cross_month Aisle, test=Hallway within-site variation",
        "n_samples": len(samples),
        "split_counts": split_counts,
        "label_counts": label_counts,
        "rule_baseline_metrics": metrics(samples),
        "samples": samples,
    }
    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

    columns = ["sample_id", "source", "split", "cluster_id", "canonical_label", "dominant_state", "target_admit"] + FEATURE_FIELDS
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows({k: s.get(k, "") for k in columns} for s in samples)

    print(json.dumps({
        "output_json": str(out_json.relative_to(root)),
        "output_csv": str(out_csv.relative_to(root)),
        "n_samples": len(samples),
        "split_counts": split_counts,
        "label_counts": label_counts,
        "rule_baseline_metrics": payload["rule_baseline_metrics"],
    }, indent=2))


if __name__ == "__main__":
    main()
