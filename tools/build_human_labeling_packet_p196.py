#!/usr/bin/env python3
"""Build the P196 human-labeling packet from P194/P195 artifacts.

This script prepares review materials only. It never infers or fills human
labels from weak labels, categories, proxy fields, or model outputs.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BOUNDARY_CSV = ROOT / "paper/evidence/admission_boundary_label_sheet_p194.csv"
PAIR_CSV = ROOT / "paper/evidence/association_pair_candidates_p194.csv"
P195_JSON = ROOT / "paper/evidence/independent_supervision_gate_p195.json"

PROTOCOL_MD = ROOT / "paper/export/human_labeling_protocol_p196.md"
PACKET_JSON = ROOT / "paper/evidence/human_labeling_packet_p196.json"
BOUNDARY_REVIEW_CSV = ROOT / "paper/evidence/admission_boundary_label_sheet_p196_review.csv"
PAIR_REVIEW_CSV = ROOT / "paper/evidence/association_pair_candidates_p196_review.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def evidence_status(*paths: str) -> str:
    if all(Path(p).exists() for p in paths if p):
        return "existing"
    return "missing"


def missing_paths(*paths: str) -> list[str]:
    return [p for p in paths if p and not Path(p).exists()]


def split_key(split: str) -> int:
    return {"val": 0, "train": 1, "test": 2}.get(split, 3)


def boundary_priority(row: dict[str, str]) -> tuple[int, str]:
    tags = set(filter(None, row.get("risk_tags", "").split(";")))
    reason = set(filter(None, row.get("reason_for_review", "").split(";")))
    score = 0
    parts: list[str] = []
    if "false_positive" in tags or "model_false_admit_against_current_weak_label" in reason:
        score -= 100
        parts.append("false_positive")
    if "near_threshold" in tags or "near_decision_threshold" in reason:
        score -= 70
        parts.append("near_threshold")
    if "proxy_sensitive" in tags or "category_proxy_sensitive" in reason:
        score -= 40
        parts.append("proxy_sensitive")
    if "infra_reject_boundary" in tags:
        score -= 30
        parts.append("infrastructure_boundary")
    score += split_key(row.get("split", "")) * 4
    score += {"forklift": 0, "barrier": 1, "work table": 2, "warehouse rack": 3}.get(
        row.get("canonical_label", ""), 4
    )
    try:
        score += int(row.get("review_id", "0").rsplit("_", 1)[-1])
    except ValueError:
        pass
    if not parts:
        parts.append("coverage")
    return score, ",".join(parts)


def pair_priority(row: dict[str, str]) -> tuple[int, str]:
    score = 0
    parts: list[str] = []
    if row.get("same_weak_label") == "0":
        score -= 100
        parts.append("weak_label_disagreement")
    if row.get("canonical_label") == "forklift":
        score -= 60
        parts.append("dynamic_category")
    if row.get("split_pair") == "val|val":
        score -= 50
        parts.append("val_coverage")
    elif row.get("split_pair") == "train|train":
        score -= 20
        parts.append("train_coverage")
    try:
        centroid = float(row.get("centroid_distance", "0") or 0)
        size = float(row.get("size_distance", "0") or 0)
    except ValueError:
        centroid = 0.0
        size = 0.0
    if centroid > 0:
        score -= min(int(centroid * 1000), 40)
        parts.append("centroid_separation")
    if size > 0:
        score -= min(int(size * 1000), 40)
        parts.append("size_separation")
    score += {"forklift": 0, "barrier": 1, "work table": 2, "warehouse rack": 3}.get(
        row.get("canonical_label", ""), 4
    )
    try:
        score += int(row.get("pair_id", "0").rsplit("_", 1)[-1])
    except ValueError:
        pass
    if not parts:
        parts.append("cross_session_same_category")
    return score, ",".join(parts)


def audit_human_column(rows: list[dict[str, str]], column: str) -> dict[str, int]:
    valid = {"0", "1"}
    counter = Counter()
    for row in rows:
        value = row.get(column, "").strip()
        if value == "":
            counter["blank"] += 1
        elif value in valid:
            counter["valid"] += 1
        else:
            counter["invalid"] += 1
    return {"blank": counter["blank"], "valid": counter["valid"], "invalid": counter["invalid"]}


def summarize_boundary(rows: list[dict[str, str]]) -> dict[str, Any]:
    missing = [
        {
            "review_id": row["review_id"],
            "sample_id": row["sample_id"],
            "missing_paths": missing_paths(row["image_or_artifact_reference"]),
        }
        for row in rows
        if evidence_status(row["image_or_artifact_reference"]) == "missing"
    ]
    return {
        "total_rows": len(rows),
        "evidence_paths": {
            "existing": len(rows) - len(missing),
            "missing": len(missing),
        },
        "missing_visual_evidence_samples": missing,
        "by_split": dict(Counter(row["split"] for row in rows)),
        "by_category": dict(Counter(row["canonical_label"] for row in rows)),
        "by_risk_tags": dict(Counter(row["risk_tags"] for row in rows)),
        "human_admit_label_audit": audit_human_column(rows, "human_admit_label"),
    }


def summarize_pairs(rows: list[dict[str, str]]) -> dict[str, Any]:
    missing = []
    for row in rows:
        row_missing = missing_paths(row["artifact_reference_a"], row["artifact_reference_b"])
        if row_missing:
            missing.append(
                {
                    "pair_id": row["pair_id"],
                    "sample_id_a": row["sample_id_a"],
                    "sample_id_b": row["sample_id_b"],
                    "missing_paths": row_missing,
                }
            )
    return {
        "total_rows": len(rows),
        "artifact_reference_a": {
            "existing": sum(Path(row["artifact_reference_a"]).exists() for row in rows),
            "missing": sum(not Path(row["artifact_reference_a"]).exists() for row in rows),
        },
        "artifact_reference_b": {
            "existing": sum(Path(row["artifact_reference_b"]).exists() for row in rows),
            "missing": sum(not Path(row["artifact_reference_b"]).exists() for row in rows),
        },
        "pair_rows_with_missing_visual_evidence": len(missing),
        "missing_visual_evidence_pairs": missing,
        "by_split_pair": dict(Counter(row["split_pair"] for row in rows)),
        "by_category": dict(Counter(row["canonical_label"] for row in rows)),
        "human_same_object_label_audit": audit_human_column(rows, "human_same_object_label"),
    }


def build_boundary_review(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[str]]:
    ranked = sorted(rows, key=boundary_priority)
    rank_by_id = {row["review_id"]: index + 1 for index, row in enumerate(ranked)}
    reason_by_id = {row["review_id"]: boundary_priority(row)[1] for row in rows}
    review_rows = []
    for row in rows:
        item = dict(row)
        item["reviewer_priority"] = str(rank_by_id[row["review_id"]])
        item["evidence_status"] = evidence_status(row["image_or_artifact_reference"])
        item["review_hint"] = (
            f"Priority basis: {reason_by_id[row['review_id']]}. Judge visual/object "
            "evidence only; do not copy current_weak_label, category, or rule_proxy_fields."
        )
        review_rows.append(item)
    fields = list(rows[0].keys()) + ["reviewer_priority", "evidence_status", "review_hint"]
    return review_rows, fields


def build_pair_review(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[str]]:
    ranked = sorted(rows, key=pair_priority)
    rank_by_id = {row["pair_id"]: index + 1 for index, row in enumerate(ranked)}
    reason_by_id = {row["pair_id"]: pair_priority(row)[1] for row in rows}
    review_rows = []
    for row in rows:
        item = dict(row)
        item["reviewer_priority"] = str(rank_by_id[row["pair_id"]])
        item["evidence_status"] = evidence_status(
            row["artifact_reference_a"], row["artifact_reference_b"]
        )
        item["review_hint"] = (
            f"Priority basis: {reason_by_id[row['pair_id']]}. Compare the two visual "
            "artifacts for the same physical object; do not copy weak labels or geometry proxies."
        )
        review_rows.append(item)
    fields = list(rows[0].keys()) + ["reviewer_priority", "evidence_status", "review_hint"]
    return review_rows, fields


def minimal_boundary_order(rows: list[dict[str, str]]) -> list[str]:
    ranked = sorted(rows, key=boundary_priority)
    selected: list[dict[str, str]] = []
    by_split: defaultdict[str, int] = defaultdict(int)
    by_proxy_class: defaultdict[str, int] = defaultdict(int)

    def add(row: dict[str, str]) -> None:
        if row not in selected:
            selected.append(row)
            by_split[row["split"]] += 1
            by_proxy_class[row["current_weak_label"]] += 1

    for split in ["val", "train", "test"]:
        for row in ranked:
            if row["split"] == split:
                add(row)
                break
    for proxy_value in ["0", "1"]:
        for row in ranked:
            if row["current_weak_label"] == proxy_value:
                add(row)
                break
    for row in ranked:
        if len(selected) >= 24:
            break
        add(row)
    return [row["review_id"] for row in selected[:24]]


def minimal_pair_order(rows: list[dict[str, str]]) -> list[str]:
    ranked = sorted(rows, key=pair_priority)
    selected: list[dict[str, str]] = []
    categories = ["forklift", "barrier", "work table", "warehouse rack"]
    split_pairs = ["val|val", "train|train", "test|test"]

    def add(row: dict[str, str]) -> None:
        if row not in selected:
            selected.append(row)

    for split_pair in split_pairs:
        for row in ranked:
            if row["split_pair"] == split_pair:
                add(row)
                break
    for category in categories:
        for row in ranked:
            if row["canonical_label"] == category:
                add(row)
                break
    for row in ranked:
        if len(selected) >= 40:
            break
        add(row)
    return [row["pair_id"] for row in selected[:40]]


def write_protocol(boundary_summary: dict[str, Any], pair_summary: dict[str, Any]) -> None:
    text = f"""# P196 Human Labeling Protocol

**Status:** review packet only. This phase prepares independent human labels for the P195 gate; it does not train a model and does not claim learned admission control.

## Inputs

- Boundary sheet: `paper/evidence/admission_boundary_label_sheet_p194.csv`
- Pair sheet: `paper/evidence/association_pair_candidates_p194.csv`
- P195 gate report: `paper/evidence/independent_supervision_gate_p195.json`
- Review CSVs with priority and evidence status:
  - `paper/evidence/admission_boundary_label_sheet_p196_review.csv`
  - `paper/evidence/association_pair_candidates_p196_review.csv`
- Packet manifest: `paper/evidence/human_labeling_packet_p196.json`

## Non-Negotiable Label Boundary

- Do not infer, guess, or backfill any `human_*` label.
- Do not copy `current_weak_label`, `weak_label_a`, `weak_label_b`, category names, model predictions, model probabilities, `same_weak_label`, centroid/size distances, or `rule_proxy_fields` into a human label.
- Use only the visual/object evidence in the referenced artifacts and the reviewer notes written during inspection.
- If evidence is insufficient, leave the human label blank and explain the uncertainty in `human_notes` or `human_pair_notes`.

## Admission Label: `human_admit_label`

Fill this column only after inspecting `image_or_artifact_reference`.

- `1` = admit: the observation is a persistent-map object candidate. It appears to be stable infrastructure or a durable object that should be eligible for long-term semantic map maintenance.
- `0` = reject: the observation should not enter the persistent map. Typical reasons include dynamic agent, movable/transient clutter, severe segmentation ambiguity, insufficient object evidence, or a visual crop that does not support persistent-object admission.
- blank = uncertain or not reviewable. Use this when the image/artifact does not provide enough evidence for an independent judgment.

Also fill:

- `human_label_confidence`: use `high`, `medium`, or `low`.
- `human_notes`: short visual rationale, especially for low-confidence or blank cases.

## Pair Label: `human_same_object_label`

Fill this column only after comparing `artifact_reference_a` and `artifact_reference_b`.

- `1` = same physical object: both artifacts show the same persistent object instance across frames/sessions.
- `0` = different object: artifacts show different physical objects, object identity is inconsistent, or the visual evidence contradicts a same-object association.
- blank = uncertain or not reviewable. Use this when the two artifacts do not contain enough identity evidence.

Also fill:

- `human_pair_notes`: short rationale, including visual features used for identity or the reason the pair remains undecidable.

## Minimum Order For Rerunning P195

P195 currently requires at least 24 valid boundary labels and 40 valid pair labels, with both label classes covered. The recommended review order is encoded by `reviewer_priority`.

1. Boundary labels: label the first 24 rows by `reviewer_priority`, while ensuring train/val/test are all represented and both human classes (`0` and `1`) appear. Prioritize false-positive, near-threshold, proxy-sensitive, and infrastructure-boundary cases.
2. Pair labels: label the first 40 rows by `reviewer_priority`, while ensuring both same-object (`1`) and different-object (`0`) examples appear. If the first 40 visually all belong to one class, continue down the priority list until both classes are represented.
3. Keep uncertain rows blank. More total reviewed rows are better than forcing labels on weak evidence.

## Evidence Availability

- Boundary rows: {boundary_summary['total_rows']} total, {boundary_summary['evidence_paths']['existing']} existing visual references, {boundary_summary['evidence_paths']['missing']} missing.
- Pair rows: {pair_summary['total_rows']} total, `artifact_reference_a` existing/missing = {pair_summary['artifact_reference_a']['existing']}/{pair_summary['artifact_reference_a']['missing']}, `artifact_reference_b` existing/missing = {pair_summary['artifact_reference_b']['existing']}/{pair_summary['artifact_reference_b']['missing']}.

Rows with missing evidence should not receive a forced label. In the current packet, the missing-evidence lists are recorded in `human_labeling_packet_p196.json`.

## Rerun Gate After Human Review

After real human labels are entered in the P194 or P196 review CSVs and copied into the P194 source columns expected by P195, rerun:

```bash
python3 tools/prepare_independent_supervision_p195.py
```

Until real `human_*` labels exist, P195 must remain `BLOCKED`.
"""
    PROTOCOL_MD.write_text(text, encoding="utf-8")


def main() -> None:
    boundary_rows = read_csv(BOUNDARY_CSV)
    pair_rows = read_csv(PAIR_CSV)
    p195 = json.loads(P195_JSON.read_text(encoding="utf-8"))

    boundary_review, boundary_fields = build_boundary_review(boundary_rows)
    pair_review, pair_fields = build_pair_review(pair_rows)
    write_csv(BOUNDARY_REVIEW_CSV, boundary_review, boundary_fields)
    write_csv(PAIR_REVIEW_CSV, pair_review, pair_fields)

    boundary_summary = summarize_boundary(boundary_rows)
    pair_summary = summarize_pairs(pair_rows)

    packet = {
        "phase": "P196-human-labeling-closed-loop-packet",
        "status": "READY_FOR_HUMAN_REVIEW",
        "scientific_boundary": (
            "P196 prepares human labeling materials only. It does not train, does not "
            "infer human labels, and does not unblock P195 without real human input."
        ),
        "inputs": {
            "boundary_sheet_p194": str(BOUNDARY_CSV.relative_to(ROOT)),
            "pair_candidates_p194": str(PAIR_CSV.relative_to(ROOT)),
            "p195_gate": str(P195_JSON.relative_to(ROOT)),
        },
        "outputs": {
            "protocol": str(PROTOCOL_MD.relative_to(ROOT)),
            "packet": str(PACKET_JSON.relative_to(ROOT)),
            "boundary_review_csv": str(BOUNDARY_REVIEW_CSV.relative_to(ROOT)),
            "pair_review_csv": str(PAIR_REVIEW_CSV.relative_to(ROOT)),
        },
        "p195_gate_requirements": p195.get("gate", {}),
        "label_audit": p195.get("label_audit", {}),
        "evidence_availability": {
            "boundary": boundary_summary,
            "pairs": pair_summary,
        },
        "recommended_minimum_labeling_strategy": {
            "boundary_first": {
                "target_valid_labels": 24,
                "must_cover_splits": ["train", "val", "test"],
                "must_cover_human_classes": ["0 reject", "1 admit"],
                "priority_basis": [
                    "false_positive",
                    "near_threshold",
                    "proxy_sensitive",
                    "infrastructure_boundary",
                    "split/category balance",
                ],
                "ordered_review_ids": minimal_boundary_order(boundary_rows),
            },
            "pairs_second": {
                "target_valid_labels": 40,
                "must_cover_human_classes": ["0 different object", "1 same physical object"],
                "priority_basis": [
                    "weak_label_disagreement",
                    "dynamic_category",
                    "val/train/test coverage",
                    "geometry-separation review risk",
                    "category balance",
                ],
                "ordered_pair_ids": minimal_pair_order(pair_rows),
                "class_balance_note": (
                    "The order is a review recommendation only. If the first 40 visually "
                    "do not include both same and different object labels, continue reviewing "
                    "lower-priority rows until both human classes are real and documented."
                ),
            },
        },
        "forbidden_shortcuts": [
            "do not fill human labels from current_weak_label",
            "do not fill human labels from category names",
            "do not fill human labels from rule_proxy_fields",
            "do not fill human labels from model predictions or probabilities",
            "do not force labels for missing or ambiguous visual evidence",
        ],
    }

    PACKET_JSON.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_protocol(boundary_summary, pair_summary)

    print(json.dumps({"status": "ok", "outputs": packet["outputs"]}, indent=2))


if __name__ == "__main__":
    main()
