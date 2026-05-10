#!/usr/bin/env python3
"""P195 independent-label gate for admission-control supervision.

This script is intentionally conservative. It refuses to treat blank
``human_*`` columns as labels, and it refuses to claim learned admission control
unless enough independent human labels are present to build a split-aware
supervision set. When the gate is blocked, it writes a report and JSON evidence
with concrete labeling instructions.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROXY_FEATURES = {
    "dynamic_ratio",
    "label_purity",
    "is_forklift_like",
    "is_infrastructure_like",
}
ANTI_PROXY_DROP_FEATURES = sorted(PROXY_FEATURES)
TRAINER_FEATURE_FIELDS = [
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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in columns})


def parse_binary(value: Any) -> int | None:
    text = str(value if value is not None else "").strip().lower()
    if text in {"1", "admit", "yes", "y", "true", "stable", "keep"}:
        return 1
    if text in {"0", "reject", "no", "n", "false", "dynamic", "drop"}:
        return 0
    return None


def count_blank_and_valid(rows: list[dict[str, str]], column: str) -> dict[str, int]:
    blank = valid = invalid = 0
    for row in rows:
        value = str(row.get(column, "")).strip()
        if value == "":
            blank += 1
        elif parse_binary(value) is None:
            invalid += 1
        else:
            valid += 1
    return {"total": len(rows), "blank": blank, "valid": valid, "invalid": invalid}


def split_label_category_counts(rows: list[dict[str, Any]], label_field: str) -> dict[str, Any]:
    by_split: dict[str, Counter[str]] = defaultdict(Counter)
    by_split_label: dict[str, Counter[str]] = defaultdict(Counter)
    by_category: dict[str, Counter[str]] = defaultdict(Counter)
    by_category_label: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        split = str(row.get("split", ""))
        category = str(row.get("canonical_label", ""))
        label = parse_binary(row.get(label_field))
        label_text = "unlabeled" if label is None else ("admit" if label == 1 else "reject")
        by_split[split]["n"] += 1
        by_split_label[split][label_text] += 1
        by_category[category]["n"] += 1
        by_category_label[category][label_text] += 1
    return {
        "by_split": {k: dict(v) for k, v in sorted(by_split.items())},
        "by_split_label": {k: dict(v) for k, v in sorted(by_split_label.items())},
        "by_category": {k: dict(v) for k, v in sorted(by_category.items())},
        "by_category_label": {k: dict(v) for k, v in sorted(by_category_label.items())},
    }


def dataset_counts(rows: list[dict[str, str]]) -> dict[str, Any]:
    by_split: dict[str, Counter[str]] = defaultdict(Counter)
    by_label: dict[str, Counter[str]] = defaultdict(Counter)
    by_category: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        split = row.get("split", "")
        category = row.get("canonical_label", "")
        label = "admit" if parse_binary(row.get("target_admit")) == 1 else "reject"
        by_split[split]["n"] += 1
        by_split[split][label] += 1
        by_label[label]["n"] += 1
        by_category[category]["n"] += 1
        by_category[category][label] += 1
    return {
        "total": len(rows),
        "by_split": {k: dict(v) for k, v in sorted(by_split.items())},
        "by_label": {k: dict(v) for k, v in sorted(by_label.items())},
        "by_category": {k: dict(v) for k, v in sorted(by_category.items())},
    }


def split_overlap(rows: list[dict[str, str]]) -> dict[str, Any]:
    keys_by_split: dict[str, set[str]] = defaultdict(set)
    samples_by_split: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        split = row.get("split", "")
        if row.get("physical_key"):
            keys_by_split[split].add(row["physical_key"])
        if row.get("sample_id"):
            samples_by_split[split].add(row["sample_id"])
    overlaps: dict[str, int] = {}
    splits = sorted(keys_by_split)
    for i, a in enumerate(splits):
        for b in splits[i + 1 :]:
            overlaps[f"{a}|{b}"] = len(keys_by_split[a] & keys_by_split[b])
    sample_overlaps: dict[str, int] = {}
    splits = sorted(samples_by_split)
    for i, a in enumerate(splits):
        for b in splits[i + 1 :]:
            sample_overlaps[f"{a}|{b}"] = len(samples_by_split[a] & samples_by_split[b])
    return {
        "physical_key_overlap_by_split_pair": overlaps,
        "sample_id_overlap_by_split_pair": sample_overlaps,
    }


def proxy_audit(dataset_rows: list[dict[str, str]], boundary_rows: list[dict[str, str]], model_json: dict[str, Any] | None) -> dict[str, Any]:
    dataset_columns = set(dataset_rows[0]) if dataset_rows else set()
    proxy_presence = {field: field in dataset_columns for field in sorted(PROXY_FEATURES)}
    rule_proxy_field_rows = sum(1 for row in boundary_rows if str(row.get("rule_proxy_fields", "")).strip())
    p193_features = set((model_json or {}).get("features", []))
    p193_trained_proxy_features = sorted(p193_features & PROXY_FEATURES)
    p194_dropped = sorted(set((model_json or {}).get("dropped_features", [])) & PROXY_FEATURES)
    return {
        "proxy_feature_presence_in_p193_dataset": proxy_presence,
        "boundary_rows_with_rule_proxy_fields": rule_proxy_field_rows,
        "boundary_rows_total": len(boundary_rows),
        "p193_or_reference_model_features": sorted(p193_features),
        "proxy_features_used_by_reference_model": p193_trained_proxy_features,
        "proxy_features_dropped_by_reference_model": p194_dropped,
        "p195_training_policy": {
            "rule_proxy_fields_used_for_training": False,
            "category_flags_used_for_training": False,
            "drop_features_for_no_proxy_training": ANTI_PROXY_DROP_FEATURES,
        },
    }


def enough_labels(
    boundary_rows: list[dict[str, str]],
    pair_rows: list[dict[str, str]],
    *,
    min_boundary_labels: int,
    min_pair_labels: int,
    require_both_classes: bool,
    require_all_splits: bool,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    boundary_labels = [parse_binary(row.get("human_admit_label")) for row in boundary_rows]
    pair_labels = [parse_binary(row.get("human_same_object_label")) for row in pair_rows]
    valid_boundary = [label for label in boundary_labels if label is not None]
    valid_pairs = [label for label in pair_labels if label is not None]
    if len(valid_boundary) < min_boundary_labels:
        reasons.append(f"only {len(valid_boundary)} valid human_admit_label values; need at least {min_boundary_labels}")
    if len(valid_pairs) < min_pair_labels:
        reasons.append(f"only {len(valid_pairs)} valid human_same_object_label values; need at least {min_pair_labels}")
    if require_both_classes and len(set(valid_boundary)) < 2:
        reasons.append("human_admit_label does not cover both admit and reject classes")
    if require_both_classes and min_pair_labels > 0 and len(set(valid_pairs)) < 2:
        reasons.append("human_same_object_label does not cover both same-object and different-object classes")
    if require_all_splits:
        splits = {row.get("split", "") for row in boundary_rows if parse_binary(row.get("human_admit_label")) is not None}
        missing = {"train", "val", "test"} - splits
        if missing:
            reasons.append(f"human_admit_label missing required split coverage: {sorted(missing)}")
    return not reasons, reasons


def build_independent_dataset(
    dataset_rows: list[dict[str, str]],
    boundary_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    by_id = {row["sample_id"]: row for row in dataset_rows}
    out: list[dict[str, Any]] = []
    for review in boundary_rows:
        human_label = parse_binary(review.get("human_admit_label"))
        if human_label is None:
            continue
        sample_id = review.get("sample_id", "")
        source = by_id.get(sample_id)
        if not source:
            continue
        row = dict(source)
        row["target_admit"] = human_label
        row["label_source"] = "p195_independent_human_admit_label"
        row["human_review_id"] = review.get("review_id", "")
        row["human_label_confidence"] = review.get("human_label_confidence", "")
        row["human_notes"] = review.get("human_notes", "")
        out.append(row)
    return out


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    status = payload["status"]
    gate = payload["gate"]
    label = payload["label_audit"]
    risk = payload["leakage_audit"]
    lines = [
        "# P195 Independent-Label Gate",
        "",
        f"**Status:** {status}",
        f"**Decision:** {payload['decision']}",
        "",
        "## Label Availability",
        "",
        f"- Boundary review rows: {label['boundary']['total']}",
        f"- `human_admit_label`: blank={label['boundary']['blank']}, valid={label['boundary']['valid']}, invalid={label['boundary']['invalid']}",
        f"- Pair candidates: {label['pairs']['total']}",
        f"- `human_same_object_label`: blank={label['pairs']['blank']}, valid={label['pairs']['valid']}, invalid={label['pairs']['invalid']}",
        "",
        "## Gate Result",
        "",
    ]
    if status == "BLOCKED":
        lines += [
            "P195 is blocked because independent human labels are not yet available in sufficient quantity. Current artifacts are review sheets, not training labels.",
            "",
            "**Current claim boundary:** the project cannot claim learned admission control from P193/P194 weak labels. It can only claim review-ready supervision preparation plus leakage/proxy stress evidence.",
            "",
            "Blocking reasons:",
        ]
        lines += [f"- {reason}" for reason in gate["block_reasons"]]
    else:
        lines += [
            "The gate passed and an independent-supervision dataset was built from human labels.",
            f"- Dataset: `{payload['outputs'].get('independent_dataset_csv', '')}`",
        ]
    lines += [
        "",
        "## Leakage / Proxy Audit",
        "",
        f"- P193 dataset proxy columns present: {risk['proxy_feature_presence_in_p193_dataset']}",
        f"- Boundary rows carrying `rule_proxy_fields`: {risk['boundary_rows_with_rule_proxy_fields']} / {risk['boundary_rows_total']}",
        f"- Reference model proxy features used: {risk['proxy_features_used_by_reference_model']}",
        f"- P195 training policy: do not train on `rule_proxy_fields`; drop `{', '.join(ANTI_PROXY_DROP_FEATURES)}` for no-proxy/anti-proxy runs.",
        f"- Split overlap after P193 dedup: {payload['split_overlap']}",
        "",
        "## Counts",
        "",
        "P193 weak-label dataset:",
        "",
        "```json",
        json.dumps(payload["p193_dataset_counts"], indent=2, ensure_ascii=False),
        "```",
        "",
        "P194 boundary review sheet:",
        "",
        "```json",
        json.dumps(payload["boundary_review_counts"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## Executable Human Labeling Instructions",
        "",
        "1. Open `paper/evidence/admission_boundary_label_sheet_p194.csv` and review each image/artifact path in `image_or_artifact_reference`.",
        "2. Fill `human_admit_label` with only `1` for persistent-map admit or `0` for reject. Leave genuinely undecidable rows blank and explain in `human_notes`.",
        "3. Fill `human_label_confidence` with a compact confidence value such as `high`, `medium`, or `low`.",
        "4. Open `paper/evidence/association_pair_candidates_p194.csv` and fill `human_same_object_label` with `1` for same physical object or `0` for different objects.",
        "5. Do not copy `current_weak_label`, category names, or `rule_proxy_fields` into the human columns. The label must come from visual/object evidence.",
        "6. Rerun this gate. If it passes, then run the recorded no-proxy/anti-proxy CUDA training command.",
        "",
    ]
    if payload.get("training_commands"):
        lines += ["## Training Commands", ""]
        lines += [f"- `{cmd}`" for cmd in payload["training_commands"]]
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_training(command: list[str], cwd: Path) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return {
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--p193-dataset", default="paper/evidence/admission_frame_dataset_p193.csv")
    parser.add_argument("--boundary-sheet", default="paper/evidence/admission_boundary_label_sheet_p194.csv")
    parser.add_argument("--pair-candidates", default="paper/evidence/association_pair_candidates_p194.csv")
    parser.add_argument("--reference-model-json", default="paper/evidence/admission_scorer_frame_gpu_p193.json")
    parser.add_argument("--output-json", default="paper/evidence/independent_supervision_gate_p195.json")
    parser.add_argument("--output-md", default="paper/export/independent_supervision_gate_p195.md")
    parser.add_argument("--output-dataset", default="paper/evidence/independent_supervision_dataset_p195.csv")
    parser.add_argument("--output-train-json", default="paper/evidence/admission_scorer_independent_no_proxy_p195.json")
    parser.add_argument("--output-train-md", default="paper/export/admission_scorer_independent_no_proxy_p195.md")
    parser.add_argument("--min-boundary-labels", type=int, default=24)
    parser.add_argument("--min-pair-labels", type=int, default=40)
    parser.add_argument("--require-both-classes", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--require-all-splits", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--train-if-ready", action="store_true")
    args = parser.parse_args()

    root = Path(".").resolve()
    p193_dataset = root / args.p193_dataset
    boundary_sheet = root / args.boundary_sheet
    pair_candidates = root / args.pair_candidates
    model_path = root / args.reference_model_json

    dataset_rows = read_csv(p193_dataset)
    boundary_rows = read_csv(boundary_sheet)
    pair_rows = read_csv(pair_candidates)
    model_json = json.loads(model_path.read_text()) if model_path.exists() else None

    ready, block_reasons = enough_labels(
        boundary_rows,
        pair_rows,
        min_boundary_labels=args.min_boundary_labels,
        min_pair_labels=args.min_pair_labels,
        require_both_classes=args.require_both_classes,
        require_all_splits=args.require_all_splits,
    )

    outputs: dict[str, str] = {
        "gate_json": args.output_json,
        "gate_markdown": args.output_md,
    }
    training_commands: list[str] = []
    training_result: dict[str, Any] | None = None
    independent_rows: list[dict[str, Any]] = []
    if ready:
        independent_rows = build_independent_dataset(dataset_rows, boundary_rows)
        output_dataset = root / args.output_dataset
        columns = list(dataset_rows[0].keys()) + ["human_review_id", "human_label_confidence", "human_notes"]
        write_csv(output_dataset, independent_rows, columns)
        outputs["independent_dataset_csv"] = args.output_dataset
        drop_arg = ",".join(ANTI_PROXY_DROP_FEATURES)
        cmd = [
            "conda",
            "run",
            "-n",
            "tram",
            "python",
            "tools/train_admission_scorer_gpu_p192.py",
            "--dataset",
            args.output_dataset,
            "--dataset-kind",
            "p195-independent-human-no-proxy",
            "--drop-features",
            drop_arg,
            "--p191-json",
            "paper/evidence/admission_scorer_smoke_p191.json",
            "--p192-json",
            "paper/evidence/admission_scorer_no_proxy_p194.json",
            "--comparison-label",
            "P194 no-proxy weak-label stress",
            "--output-json",
            args.output_train_json,
            "--output-md",
            args.output_train_md,
            "--phase",
            "P195-independent-human-no-proxy-training",
            "--report-title",
            "P195 Independent Human No-Proxy Admission Scorer",
        ]
        training_commands.append("LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib:$LD_LIBRARY_PATH " + " ".join(cmd))
        if args.train_if_ready:
            env_cmd = ["bash", "-lc", "LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib:$LD_LIBRARY_PATH " + " ".join(cmd)]
            training_result = run_training(env_cmd, root)
            if training_result["returncode"] != 0:
                block_reasons.append("independent labels passed, but CUDA training command failed")
                ready = False

    payload: dict[str, Any] = {
        "phase": "P195-independent-label-gate",
        "status": "READY" if ready else "BLOCKED",
        "decision": (
            "independent labels sufficient; independent no-proxy training may proceed"
            if ready
            else "do not train or claim learned admission control until human labels are collected"
        ),
        "inputs": {
            "p193_dataset": args.p193_dataset,
            "boundary_sheet": args.boundary_sheet,
            "pair_candidates": args.pair_candidates,
            "reference_model_json": args.reference_model_json,
        },
        "gate": {
            "min_boundary_labels": args.min_boundary_labels,
            "min_pair_labels": args.min_pair_labels,
            "require_both_classes": args.require_both_classes,
            "require_all_splits": args.require_all_splits,
            "block_reasons": block_reasons,
        },
        "label_audit": {
            "boundary": count_blank_and_valid(boundary_rows, "human_admit_label"),
            "pairs": count_blank_and_valid(pair_rows, "human_same_object_label"),
        },
        "p193_dataset_counts": dataset_counts(dataset_rows),
        "boundary_review_counts": split_label_category_counts(boundary_rows, "human_admit_label"),
        "pair_label_counts": count_blank_and_valid(pair_rows, "human_same_object_label"),
        "split_overlap": split_overlap(dataset_rows),
        "leakage_audit": proxy_audit(dataset_rows, boundary_rows, model_json),
        "independent_dataset_counts": dataset_counts(independent_rows) if independent_rows else None,
        "outputs": outputs,
        "training_commands": training_commands,
        "training_result": training_result,
        "constraints_observed": [
            "no fabricated human labels",
            "blank human_* columns are not labels",
            "no downloads",
            "no submission/PDF tuning",
            "no SAM2 full training",
        ],
    }

    out_json = root / args.output_json
    out_md = root / args.output_md
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    write_markdown(out_md, payload)
    print(json.dumps({
        "status": payload["status"],
        "decision": payload["decision"],
        "block_reasons": block_reasons,
        "label_audit": payload["label_audit"],
        "outputs": outputs,
    }, indent=2, ensure_ascii=False))
    return 0 if ready or payload["status"] == "BLOCKED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
