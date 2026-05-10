#!/usr/bin/env python3
"""Build P194 independent-supervision preparation artifacts.

This script does not create labels. It creates review-ready sheets from P193
model errors, near-threshold cases, proxy-sensitive cases, and candidate
cross-session association pairs so a human can provide independent supervision.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
from pathlib import Path
from typing import Any

BOUNDARY_COLUMNS = [
    "review_id",
    "sample_id",
    "source",
    "split",
    "session_id",
    "frame_id",
    "frame_index",
    "object_name",
    "tracklet_id",
    "canonical_label",
    "resolved_label",
    "current_weak_label",
    "model_prediction",
    "model_probability",
    "rule_proxy_fields",
    "reason_for_review",
    "risk_tags",
    "image_or_artifact_reference",
    "recommended_review_question",
    "human_admit_label",
    "human_label_confidence",
    "human_notes",
]

PAIR_COLUMNS = [
    "pair_id",
    "source",
    "split_pair",
    "canonical_label",
    "sample_id_a",
    "sample_id_b",
    "session_id_a",
    "session_id_b",
    "frame_id_a",
    "frame_id_b",
    "weak_label_a",
    "weak_label_b",
    "model_probability_a",
    "model_probability_b",
    "centroid_distance",
    "size_distance",
    "same_weak_label",
    "pair_reason",
    "artifact_reference_a",
    "artifact_reference_b",
    "human_same_object_label",
    "human_pair_notes",
]


def fnum(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in columns})


def load_observation_refs(rows: list[dict[str, Any]], repo_root: Path) -> dict[str, dict[str, Any]]:
    refs: dict[str, dict[str, Any]] = {}
    for rel in sorted({row.get("observation_index_path", "") for row in rows if row.get("observation_index_path")}):
        path = repo_root / str(rel)
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        for obs in data.get("observations") or []:
            refs[str(obs.get("observation_id"))] = obs
    return refs


def prediction_map(model_json: dict[str, Any]) -> dict[str, dict[str, Any]]:
    preds = model_json["models"]["mlp"].get("predictions", [])
    return {str(item["sample_id"]): item for item in preds}


def proxy_json(row: dict[str, Any]) -> str:
    return json.dumps({
        "dynamic_ratio": fnum(row.get("dynamic_ratio")),
        "label_purity": fnum(row.get("label_purity")),
        "is_forklift_like": int(fnum(row.get("is_forklift_like"))),
        "is_infrastructure_like": int(fnum(row.get("is_infrastructure_like"))),
        "canonical_label": row.get("canonical_label", ""),
        "resolved_label": row.get("resolved_label", ""),
        "cluster_id": row.get("cluster_id", ""),
    }, ensure_ascii=False)


def reason_for(row: dict[str, Any], pred: dict[str, Any]) -> tuple[list[str], list[str]]:
    reasons: list[str] = []
    tags: list[str] = []
    y = int(fnum(row.get("target_admit")))
    pred_label = int(pred.get("gpu_pred", 0))
    prob = fnum(pred.get("gpu_probability"))
    if y == 0 and pred_label == 1:
        reasons.append("model_false_admit_against_current_weak_label")
        tags.append("false_positive")
    if y == 1 and pred_label == 0:
        reasons.append("model_false_reject_against_current_weak_label")
        tags.append("false_negative")
    if abs(prob - 0.5) <= 0.18:
        reasons.append("near_decision_threshold")
        tags.append("near_threshold")
    if int(fnum(row.get("is_forklift_like"))) == 1 or int(fnum(row.get("is_infrastructure_like"))) == 1:
        reasons.append("category_proxy_sensitive")
        tags.append("proxy_sensitive")
    if row.get("canonical_label") in {"barrier", "work table", "warehouse rack"} and y == 0:
        reasons.append("infrastructure_rejected_boundary_case")
        tags.append("infra_reject_boundary")
    if row.get("canonical_label") == "forklift" and y == 0 and prob >= 0.35:
        reasons.append("dynamic_object_nontrivial_score")
        tags.append("dynamic_boundary")
    return reasons, tags


def review_question(row: dict[str, Any]) -> str:
    label = row.get("resolved_label") or row.get("canonical_label")
    return (
        f"Should this {label} observation be admitted into the persistent map? "
        "Use visual/object evidence, not the current selection_v5 weak label. "
        "If unsure, mark uncertain and explain whether it is stable infrastructure, movable clutter, or dynamic agent."
    )


def build_boundary_sheet(
    rows: list[dict[str, Any]],
    pred_by_id: dict[str, dict[str, Any]],
    obs_refs: dict[str, dict[str, Any]],
    max_near: int,
    max_proxy: int,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    candidates: dict[str, tuple[dict[str, Any], list[str], list[str]]] = {}
    scored_for_near: list[tuple[float, dict[str, Any], list[str], list[str]]] = []
    scored_for_proxy: list[tuple[float, dict[str, Any], list[str], list[str]]] = []
    stats = {"false_positive": 0, "false_negative": 0, "near_threshold_added": 0, "proxy_sensitive_added": 0}
    for row in rows:
        pred = pred_by_id.get(str(row["sample_id"]))
        if not pred:
            continue
        reasons, tags = reason_for(row, pred)
        prob = fnum(pred.get("gpu_probability"))
        if "false_positive" in tags or "false_negative" in tags:
            candidates[str(row["sample_id"])] = (row, reasons, tags)
            stats["false_positive"] += int("false_positive" in tags)
            stats["false_negative"] += int("false_negative" in tags)
        if "near_threshold" in tags:
            scored_for_near.append((abs(prob - 0.5), row, reasons, tags))
        if "proxy_sensitive" in tags or "infra_reject_boundary" in tags or "dynamic_boundary" in tags:
            # Prefer samples whose probabilities are not trivially 0 or 1.
            scored_for_proxy.append((abs(prob - 0.5), row, reasons, tags))
    for _, row, reasons, tags in sorted(scored_for_near, key=lambda x: x[0])[:max_near]:
        if str(row["sample_id"]) not in candidates:
            stats["near_threshold_added"] += 1
        candidates[str(row["sample_id"])] = (row, reasons, tags)
    for _, row, reasons, tags in sorted(scored_for_proxy, key=lambda x: x[0])[:max_proxy]:
        if str(row["sample_id"]) not in candidates:
            stats["proxy_sensitive_added"] += 1
        candidates[str(row["sample_id"])] = (row, reasons, tags)

    out: list[dict[str, Any]] = []
    for idx, (sample_id, (row, reasons, tags)) in enumerate(sorted(candidates.items()), 1):
        pred = pred_by_id[sample_id]
        obs = obs_refs.get(str(row.get("observation_id")), {})
        artifact = obs.get("overlay_path") or obs.get("mask_path") or row.get("observation_index_path", "")
        out.append({
            "review_id": f"p194_review_{idx:04d}",
            "sample_id": sample_id,
            "source": row.get("source", ""),
            "split": row.get("split", ""),
            "session_id": row.get("session_id", ""),
            "frame_id": row.get("frame_id", ""),
            "frame_index": row.get("frame_index", ""),
            "object_name": obs.get("object_name") or str(row.get("observation_id", "")).rsplit("_", 1)[-1],
            "tracklet_id": row.get("tracklet_id", ""),
            "canonical_label": row.get("canonical_label", ""),
            "resolved_label": row.get("resolved_label", ""),
            "current_weak_label": int(fnum(row.get("target_admit"))),
            "model_prediction": int(pred.get("gpu_pred", 0)),
            "model_probability": pred.get("gpu_probability", ""),
            "rule_proxy_fields": proxy_json(row),
            "reason_for_review": ";".join(dict.fromkeys(reasons)),
            "risk_tags": ";".join(dict.fromkeys(tags)),
            "image_or_artifact_reference": artifact,
            "recommended_review_question": review_question(row),
            "human_admit_label": "",
            "human_label_confidence": "",
            "human_notes": "",
        })
    return out, stats


def build_pair_candidates(rows: list[dict[str, Any]], pred_by_id: dict[str, dict[str, Any]], obs_refs: dict[str, dict[str, Any]], max_pairs: int) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault((str(row.get("source")), str(row.get("canonical_label"))), []).append(row)
    pairs: list[tuple[float, dict[str, Any]]] = []
    for (source, label), items in groups.items():
        for a, b in itertools.combinations(items, 2):
            if a.get("session_id") == b.get("session_id"):
                continue
            ax, ay = fnum(a.get("mean_center_x")), fnum(a.get("mean_center_y"))
            bx, by = fnum(b.get("mean_center_x")), fnum(b.get("mean_center_y"))
            asx, asy = fnum(a.get("mean_size_x")), fnum(a.get("mean_size_y"))
            bsx, bsy = fnum(b.get("mean_size_x")), fnum(b.get("mean_size_y"))
            cd = math.hypot(ax - bx, ay - by)
            sd = math.hypot(asx - bsx, asy - bsy)
            same_weak = int(fnum(a.get("target_admit"))) == int(fnum(b.get("target_admit")))
            # Prioritize hard association cases: same label but different weak labels or close geometry.
            score = cd + 0.5 * sd + (0 if not same_weak else 120)
            pred_a = pred_by_id.get(str(a["sample_id"]), {})
            pred_b = pred_by_id.get(str(b["sample_id"]), {})
            obs_a = obs_refs.get(str(a.get("observation_id")), {})
            obs_b = obs_refs.get(str(b.get("observation_id")), {})
            pair = {
                "pair_id": f"p194_pair_{len(pairs)+1:05d}",
                "source": source,
                "split_pair": f"{a.get('split')}|{b.get('split')}",
                "canonical_label": label,
                "sample_id_a": a.get("sample_id", ""),
                "sample_id_b": b.get("sample_id", ""),
                "session_id_a": a.get("session_id", ""),
                "session_id_b": b.get("session_id", ""),
                "frame_id_a": a.get("frame_id", ""),
                "frame_id_b": b.get("frame_id", ""),
                "weak_label_a": int(fnum(a.get("target_admit"))),
                "weak_label_b": int(fnum(b.get("target_admit"))),
                "model_probability_a": pred_a.get("gpu_probability", ""),
                "model_probability_b": pred_b.get("gpu_probability", ""),
                "centroid_distance": round(cd, 6),
                "size_distance": round(sd, 6),
                "same_weak_label": int(same_weak),
                "pair_reason": "same_label_cross_session_human_association_candidate",
                "artifact_reference_a": obs_a.get("overlay_path") or obs_a.get("mask_path") or a.get("observation_index_path", ""),
                "artifact_reference_b": obs_b.get("overlay_path") or obs_b.get("mask_path") or b.get("observation_index_path", ""),
                "human_same_object_label": "",
                "human_pair_notes": "",
            }
            pairs.append((score, pair))
    return [pair for _, pair in sorted(pairs, key=lambda x: x[0])[:max_pairs]]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="paper/evidence/admission_frame_dataset_p193.csv")
    parser.add_argument("--model-json", default="paper/evidence/admission_scorer_frame_gpu_p193.json")
    parser.add_argument("--output-sheet-csv", default="paper/evidence/admission_boundary_label_sheet_p194.csv")
    parser.add_argument("--output-sheet-json", default="paper/evidence/admission_boundary_label_sheet_p194.json")
    parser.add_argument("--output-pairs-csv", default="paper/evidence/association_pair_candidates_p194.csv")
    parser.add_argument("--output-pairs-json", default="paper/evidence/association_pair_candidates_p194.json")
    parser.add_argument("--output-md", default="paper/export/admission_boundary_supervision_p194.md")
    parser.add_argument("--max-near", type=int, default=24)
    parser.add_argument("--max-proxy", type=int, default=32)
    parser.add_argument("--max-pairs", type=int, default=160)
    args = parser.parse_args()

    root = Path(".").resolve()
    rows = read_csv(root / args.dataset)
    model = json.loads((root / args.model_json).read_text())
    pred_by_id = prediction_map(model)
    obs_refs = load_observation_refs(rows, root)
    sheet, sheet_stats = build_boundary_sheet(rows, pred_by_id, obs_refs, args.max_near, args.max_proxy)
    pairs = build_pair_candidates(rows, pred_by_id, obs_refs, args.max_pairs)

    write_csv(root / args.output_sheet_csv, sheet, BOUNDARY_COLUMNS)
    write_csv(root / args.output_pairs_csv, pairs, PAIR_COLUMNS)

    sheet_payload = {
        "phase": "P194-independent-boundary-supervision",
        "environment_basis": "README.md §0.3 tram environment; this script creates review sheets only and does not claim human labels exist.",
        "source_dataset": args.dataset,
        "source_model_json": args.model_json,
        "n_review_samples": len(sheet),
        "selection_stats": sheet_stats,
        "columns": BOUNDARY_COLUMNS,
        "label_status": "unlabeled_human_review_required",
        "samples": sheet,
    }
    pair_payload = {
        "phase": "P194-pairwise-association-candidates",
        "source_dataset": args.dataset,
        "n_pair_candidates": len(pairs),
        "candidate_status": "unlabeled_human_or_rule_review_required",
        "columns": PAIR_COLUMNS,
        "pairs": pairs,
    }
    (root / args.output_sheet_json).write_text(json.dumps(sheet_payload, indent=2, ensure_ascii=False) + "\n")
    (root / args.output_pairs_json).write_text(json.dumps(pair_payload, indent=2, ensure_ascii=False) + "\n")

    lines = [
        "# P194 Independent Boundary Supervision Preparation",
        "",
        "**Status:** review-ready independent-supervision preparation complete. No human labels are claimed yet.",
        "**Environment basis:** README.md §0.3 tram command form.",
        "",
        "## Boundary Label Sheet",
        "",
        f"- Source dataset: `{args.dataset}`",
        f"- Source model: `{args.model_json}`",
        f"- Review rows: {len(sheet)}",
        f"- False positives included: {sheet_stats['false_positive']}",
        f"- False negatives included: {sheet_stats['false_negative']}",
        f"- Near-threshold additions: {sheet_stats['near_threshold_added']}",
        f"- Proxy-sensitive additions: {sheet_stats['proxy_sensitive_added']}",
        f"- CSV: `{args.output_sheet_csv}`",
        f"- JSON: `{args.output_sheet_json}`",
        "",
        "Each row includes `human_admit_label`, `human_label_confidence`, and `human_notes` blank fields. These blanks are intentional: the sheet is ready for review but is not an independent training label set yet.",
        "",
        "## Pairwise Association Candidate Dataset",
        "",
        f"- Candidate pairs: {len(pairs)}",
        f"- CSV: `{args.output_pairs_csv}`",
        f"- JSON: `{args.output_pairs_json}`",
        "- Pair labels are blank (`human_same_object_label`) and must be reviewed before training.",
        "",
        "## Sampling Strategy",
        "",
        "1. Include all P193 MLP false admits / false rejects against the current weak labels.",
        "2. Add near-threshold examples by `abs(probability - 0.5)`.",
        "3. Add category-proxy-sensitive examples where forklift/infrastructure labels may dominate the target.",
        "4. Add cross-session same-label pair candidates for future association supervision, prioritizing close geometry or weak-label disagreement.",
        "",
        "## Risk Coverage",
        "",
        "- Direct model errors are represented for human adjudication.",
        "- Proxy-sensitive forklift/infrastructure cases are explicitly represented.",
        "- Pairwise candidates cover the cross-session object association target that cluster-level weak labels cannot validate.",
        "",
        "## Next Training Protocol",
        "",
        "P195 should not train on this sheet until humans fill the blank label columns. After labels are filled, build a clean independent-supervision dataset that excludes target-proxy fields where appropriate, then rerun tram CUDA training and compare against P193 weak-label metrics plus P194 no-proxy stress.",
        "",
    ]
    (root / args.output_md).write_text("\n".join(lines))
    print(json.dumps({
        "boundary_csv": args.output_sheet_csv,
        "boundary_json": args.output_sheet_json,
        "n_review_samples": len(sheet),
        "selection_stats": sheet_stats,
        "pair_csv": args.output_pairs_csv,
        "pair_json": args.output_pairs_json,
        "n_pair_candidates": len(pairs),
        "report": args.output_md,
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
