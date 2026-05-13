#!/usr/bin/env python3
"""Build the P239 independent dynamic-label mini packet.

This tool prepares review materials only. It does not infer, synthesize, or
fill independent labels from model masks, admission labels, weak labels, or any
other proxy source.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageEnhance


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "outputs/independent_dynamic_label_packet_p239"
EVIDENCE_CSV = ROOT / "paper/evidence/independent_dynamic_label_packet_p239.csv"
EVIDENCE_JSON = ROOT / "paper/evidence/independent_dynamic_label_packet_p239.json"
PROTOCOL_MD = ROOT / "paper/export/independent_dynamic_label_protocol_p239.md"
REPORT_MD = ROOT / "paper/export/independent_dynamic_label_packet_p239.md"

SELECTED_VARIANT = "meanfill035_feather5_thr060_cap012_min256"

PRIOR_ARTIFACTS = {
    "p195_gate": ROOT / "paper/evidence/independent_supervision_gate_p195.json",
    "p196_packet": ROOT / "paper/evidence/human_labeling_packet_p196.json",
    "p197_packet": ROOT / "paper/evidence/semantic_evidence_packet_p197.json",
    "p196_boundary_review_csv": ROOT / "paper/evidence/admission_boundary_label_sheet_p196_review.csv",
    "p196_pair_review_csv": ROOT / "paper/evidence/association_pair_candidates_p196_review.csv",
    "p217_dataset": ROOT / "paper/evidence/dynamic_mask_dataset_p217.json",
    "p235_soft_boundary": ROOT / "paper/evidence/soft_boundary_mask_p235.json",
    "p237_multiwindow": ROOT / "paper/evidence/soft_boundary_multiwindow_p237.json",
}

LABEL_FIELDS = [
    "dynamic_region_present",
    "boundary_quality",
    "false_positive_region",
    "false_negative_region",
    "independent_label_confidence",
    "reviewer_id",
    "reviewed_at_utc",
    "reviewer_notes",
]

CSV_FIELDS = [
    "packet_id",
    "window_id",
    "source_phase",
    "sequence_label",
    "sequence_family",
    "source_window_start_index",
    "frame_index",
    "source_frame_index",
    "timestamp",
    "selection_reason",
    "raw_image",
    "probability_overlay",
    "soft_mask_overlay",
    "region_crop",
    "source_probability",
    "source_soft_mask",
    "source_masked_rgb",
    "model_context_note",
    "admission_label_visibility",
] + LABEL_FIELDS


WINDOWS = [
    {
        "window_id": "aisle_cw_0240_0299",
        "source_phase": "P237",
        "sequence_label": "Oct. 12, 2022 Aisle_CW",
        "sequence_family": "soft_boundary_success_window",
        "source_window_start_index": 240,
        "pack_dir": ROOT
        / "outputs/soft_boundary_multiwindow_p237/aisle_cw_0240_0299"
        / SELECTED_VARIANT
        / "dynamic_slam_backend_input_pack_p235_soft_boundary",
        "frame_indices": [0, 10, 20, 30, 40, 50],
        "selection_reason": "P237 success window: ORB predicted-region keypoints down and DROID gate neutral.",
    },
    {
        "window_id": "aisle_cw_0840_0899",
        "source_phase": "P235",
        "sequence_label": "Oct. 12, 2022 Aisle_CW",
        "sequence_family": "p233_p234_failure_repair_window",
        "source_window_start_index": 840,
        "pack_dir": ROOT
        / "outputs/soft_boundary_mask_p235/aisle_cw_0840_0899"
        / SELECTED_VARIANT
        / "dynamic_slam_backend_input_pack_p235_soft_boundary",
        "frame_indices": [0, 10, 20, 30, 40, 50],
        "selection_reason": "P235 repair window for the P233/P234 840-899 hard-mask failure boundary.",
    },
    {
        "window_id": "aisle_ccw_0240_0299",
        "source_phase": "P237",
        "sequence_label": "Oct. 12, 2022 Aisle_CCW",
        "sequence_family": "different_sequence_coverage",
        "source_window_start_index": 240,
        "pack_dir": ROOT
        / "outputs/soft_boundary_multiwindow_p237/aisle_ccw_0240_0299"
        / SELECTED_VARIANT
        / "dynamic_slam_backend_input_pack_p235_soft_boundary",
        "frame_indices": [0, 10, 20, 30, 40, 50],
        "selection_reason": "Different sequence coverage from P237: Aisle_CCW with neutral DROID gate.",
    },
]


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def human_label_audit(rows: list[dict[str, str]], columns: list[str]) -> dict[str, dict[str, int]]:
    audit: dict[str, dict[str, int]] = {}
    for column in columns:
        counter = Counter()
        for row in rows:
            value = row.get(column, "").strip()
            if value == "":
                counter["blank"] += 1
            elif value.lower() in {"unknown", "unreviewed"}:
                counter["unknown"] += 1
            else:
                counter["non_empty"] += 1
        audit[column] = dict(counter)
    return audit


def prior_label_status() -> dict[str, Any]:
    boundary_rows = read_csv(PRIOR_ARTIFACTS["p196_boundary_review_csv"])
    pair_rows = read_csv(PRIOR_ARTIFACTS["p196_pair_review_csv"])
    p195 = read_json(PRIOR_ARTIFACTS["p195_gate"])
    p217 = read_json(PRIOR_ARTIFACTS["p217_dataset"])
    p235 = read_json(PRIOR_ARTIFACTS["p235_soft_boundary"])
    p237 = read_json(PRIOR_ARTIFACTS["p237_multiwindow"])
    return {
        "checked_artifacts": {key: rel(path) for key, path in PRIOR_ARTIFACTS.items()},
        "p195_status": p195.get("status"),
        "p195_decision": p195.get("decision"),
        "p196_boundary_human_label_audit": human_label_audit(
            boundary_rows, ["human_admit_label", "human_label_confidence", "human_notes"]
        ),
        "p196_pair_human_label_audit": human_label_audit(
            pair_rows, ["human_same_object_label", "human_pair_notes"]
        ),
        "p217_boundary": p217.get("claim_boundary"),
        "p217_p195_status": p217.get("p195_status"),
        "p235_claim_boundary": p235.get("claim_boundary"),
        "p235_status": p235.get("status"),
        "p237_claim_boundary": p237.get("claim_boundary"),
        "p237_status": p237.get("status"),
        "conclusion": (
            "No completed independent dynamic labels were found in P195/P196/P197/P217/P235/P237. "
            "P239 therefore prepares a packet only and keeps P195 BLOCKED."
        ),
    }


def indexed_frames(manifest: dict[str, Any]) -> dict[int, dict[str, Any]]:
    frames = manifest.get("frames", [])
    return {int(frame["frame_index"]): frame for frame in frames}


def ensure_rgb(image: Image.Image) -> Image.Image:
    if image.mode != "RGB":
        return image.convert("RGB")
    return image


def tint_overlay(base_path: Path, mask_path: Path, out_path: Path, color: tuple[int, int, int]) -> None:
    base = ensure_rgb(Image.open(base_path))
    mask = Image.open(mask_path).convert("L").resize(base.size)
    alpha = mask.point(lambda px: int(px * 0.45))
    tint = Image.new("RGB", base.size, color)
    overlay = Image.composite(tint, base, alpha)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    overlay.save(out_path)


def probability_overlay(base_path: Path, probability_path: Path, out_path: Path) -> None:
    base = ensure_rgb(Image.open(base_path))
    prob = Image.open(probability_path).convert("L").resize(base.size)
    prob = ImageEnhance.Contrast(prob).enhance(1.4)
    heat = Image.new("RGB", base.size)
    heat_pixels = []
    for value in prob.getdata():
        heat_pixels.append((min(255, value * 2), max(0, value - 80), max(0, 180 - value)))
    heat.putdata(heat_pixels)
    alpha = prob.point(lambda px: int(px * 0.35))
    overlay = Image.composite(heat, base, alpha)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    overlay.save(out_path)


def mask_bbox(mask_path: Path, image_size: tuple[int, int], margin: int = 24) -> tuple[int, int, int, int]:
    mask = Image.open(mask_path).convert("L").resize(image_size)
    bbox = mask.point(lambda px: 255 if px > 0 else 0).getbbox()
    width, height = image_size
    if bbox is None:
        crop_w = max(1, width // 3)
        crop_h = max(1, height // 3)
        left = (width - crop_w) // 2
        top = (height - crop_h) // 2
        return (left, top, left + crop_w, top + crop_h)
    left, top, right, bottom = bbox
    return (
        max(0, left - margin),
        max(0, top - margin),
        min(width, right + margin),
        min(height, bottom + margin),
    )


def region_crop(base_path: Path, mask_path: Path, out_path: Path) -> None:
    base = ensure_rgb(Image.open(base_path))
    crop_box = mask_bbox(mask_path, base.size)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    base.crop(crop_box).save(out_path)


def copy_raw(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def build_packet(args: argparse.Namespace) -> dict[str, Any]:
    if args.clean_output and args.output_root.exists():
        shutil.rmtree(args.output_root)
    args.output_root.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    missing_inputs: list[dict[str, Any]] = []

    for window in WINDOWS:
        pack_dir = Path(window["pack_dir"])
        manifest_path = pack_dir / "backend_input_manifest.json"
        if not manifest_path.exists():
            missing_inputs.append({"window_id": window["window_id"], "missing": rel(manifest_path)})
            continue
        manifest = read_json(manifest_path)
        by_frame = indexed_frames(manifest)
        for frame_index in window["frame_indices"]:
            frame = by_frame.get(frame_index)
            if not frame:
                missing_inputs.append({"window_id": window["window_id"], "missing_frame_index": frame_index})
                continue
            packet_id = f"p239_{window['window_id']}_{frame_index:06d}"
            sample_dir = args.output_root / window["window_id"] / f"{frame_index:06d}"
            raw_src = ROOT / frame["raw_rgb"]
            mask_src = ROOT / frame["dynamic_mask"]
            probability_src = ROOT / frame["source_probability"]
            masked_src = ROOT / frame["masked_rgb"]
            required = [raw_src, mask_src, probability_src, masked_src]
            missing = [rel(path) for path in required if not path.exists()]
            if missing:
                missing_inputs.append(
                    {"window_id": window["window_id"], "frame_index": frame_index, "missing": missing}
                )
                continue

            raw_dst = sample_dir / "raw_image.png"
            probability_dst = sample_dir / "probability_overlay.png"
            soft_mask_dst = sample_dir / "soft_mask_overlay.png"
            crop_dst = sample_dir / "region_crop.png"
            copy_raw(raw_src, raw_dst)
            probability_overlay(raw_src, probability_src, probability_dst)
            tint_overlay(raw_src, mask_src, soft_mask_dst, (255, 64, 64))
            region_crop(raw_src, mask_src, crop_dst)

            row = {
                "packet_id": packet_id,
                "window_id": window["window_id"],
                "source_phase": window["source_phase"],
                "sequence_label": window["sequence_label"],
                "sequence_family": window["sequence_family"],
                "source_window_start_index": window["source_window_start_index"],
                "frame_index": frame_index,
                "source_frame_index": int(window["source_window_start_index"]) + frame_index,
                "timestamp": frame.get("timestamp", ""),
                "selection_reason": window["selection_reason"],
                "raw_image": rel(raw_dst),
                "probability_overlay": rel(probability_dst),
                "soft_mask_overlay": rel(soft_mask_dst),
                "region_crop": rel(crop_dst),
                "source_probability": rel(probability_src),
                "source_soft_mask": rel(mask_src),
                "source_masked_rgb": rel(masked_src),
                "model_context_note": (
                    "Model probability and soft-mask overlays are optional context only; "
                    "they are not ground truth and must not be copied into labels."
                ),
                "admission_label_visibility": "not_included_in_packet",
            }
            for field in LABEL_FIELDS:
                row[field] = ""
            rows.append(row)

    write_csv(args.evidence_csv, rows, CSV_FIELDS)

    status = "READY_FOR_INDEPENDENT_REVIEW" if rows and not missing_inputs else "READY_WITH_MISSING_INPUTS"
    payload = {
        "phase": "P239-independent-dynamic-label-mini-packet",
        "status": status,
        "generated_at_utc": now_utc(),
        "claim_boundary": (
            "P239 prepares an independent dynamic-label review packet only. "
            "It does not collect labels, infer labels, validate the soft-boundary module, "
            "or unblock P195."
        ),
        "selected_variant": SELECTED_VARIANT,
        "outputs": {
            "output_root": rel(args.output_root),
            "label_sheet_csv": rel(args.evidence_csv),
            "packet_json": rel(args.evidence_json),
            "protocol_markdown": rel(args.protocol_md),
            "report_markdown": rel(args.report_md),
        },
        "prior_label_status": prior_label_status(),
        "packet_summary": {
            "total_rows": len(rows),
            "by_window": dict(Counter(row["window_id"] for row in rows)),
            "by_sequence_family": dict(Counter(row["sequence_family"] for row in rows)),
            "label_fields": LABEL_FIELDS,
            "label_field_policy": "blank until filled by a human or external independent reviewer",
            "admission_labels_included": False,
            "model_predictions_used_as_ground_truth": False,
            "model_context_exported": True,
        },
        "rows": rows,
        "missing_inputs": missing_inputs,
        "p195_status_after_p239": "BLOCKED",
        "p195_unblock_condition": (
            "P195 remains BLOCKED until non-empty reviewed independent labels are collected, "
            "audited for coverage and conflicts, and then explicitly linked back into the gate."
        ),
    }
    write_json(args.evidence_json, payload)
    write_protocol(args.protocol_md, payload)
    write_report(args.report_md, payload)
    return payload


def write_protocol(path: Path, payload: dict[str, Any]) -> None:
    text = f"""# P239 Independent Dynamic-Label Mini-Packet Protocol

## Purpose

This protocol supports a small independent review pass over dynamic regions in P235/P237 soft-boundary windows. The packet is designed to reduce reviewer cost while preserving the claim boundary: it prepares review material only and does not create independent labels by itself.

## Packet Scope

- Packet CSV: `{payload["outputs"]["label_sheet_csv"]}`
- Local visual packet root: `{payload["outputs"]["output_root"]}`
- Samples: {payload["packet_summary"]["total_rows"]}
- Windows: {", ".join(sorted(payload["packet_summary"]["by_window"]))}
- Selected soft-boundary context variant: `{SELECTED_VARIANT}`

## Reviewer Rules

1. Use the raw image as the primary evidence.
2. Treat probability overlays and soft-mask overlays as optional context only.
3. Do not copy model masks, probabilities, weak labels, admission labels, or prior P196/P197 fields into the label columns.
4. Do not consult admission labels while filling this sheet. The P239 packet intentionally does not include them.
5. Mark uncertainty in `reviewer_notes` instead of forcing a label.
6. Leave a field blank if the packet does not contain enough visual evidence for that field.

## Label Fields

- `dynamic_region_present`: reviewer judgment on whether an independently visible dynamic/movable region is present in the reviewed area.
- `boundary_quality`: reviewer judgment of the contextual mask boundary quality, for example good, partial, poor, or unknown.
- `false_positive_region`: reviewer notes or flag for mask/context regions that appear static/background.
- `false_negative_region`: reviewer notes or flag for visible dynamic/movable regions missed by the context overlay.
- `independent_label_confidence`: reviewer confidence, for example high, medium, low, or unknown.
- `reviewer_id`, `reviewed_at_utc`, `reviewer_notes`: reviewer provenance and comments.

## Independence Boundary

Labels are independent only after a human or external reviewer fills non-empty label fields using this protocol. The generated packet, CSV, JSON, and overlays are not independent validation.

P195 remains BLOCKED until non-empty reviewed labels exist and are audited. This packet alone must not be cited as independent dynamic-label evidence.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_report(path: Path, payload: dict[str, Any]) -> None:
    prior = payload["prior_label_status"]
    summary = payload["packet_summary"]
    text = f"""# P239 Independent Dynamic-Label Mini Packet

## Result

P239 prepared a mini packet for future independent dynamic-region review. No independent labels were collected or inferred.

## Prior Label Status

- P195 status before and after P239: `{prior["p195_status"]}` / `BLOCKED`
- P195 decision: {prior["p195_decision"]}
- P196 boundary rows remain blank for `human_admit_label`: {prior["p196_boundary_human_label_audit"]["human_admit_label"].get("blank", 0)}
- P196 pair rows remain blank for `human_same_object_label`: {prior["p196_pair_human_label_audit"]["human_same_object_label"].get("blank", 0)}
- P217/P235/P237 remain bounded context or frontend evidence, not independent labels.

## Packet Contents

- Label sheet CSV: `{payload["outputs"]["label_sheet_csv"]}`
- Packet JSON: `{payload["outputs"]["packet_json"]}`
- Protocol: `{payload["outputs"]["protocol_markdown"]}`
- Local image packet root: `{payload["outputs"]["output_root"]}`
- Rows: {summary["total_rows"]}
- Windows: {", ".join(f"{key}={value}" for key, value in sorted(summary["by_window"].items()))}
- Sequence families: {", ".join(f"{key}={value}" for key, value in sorted(summary["by_sequence_family"].items()))}

Each row references raw image, probability overlay, soft-mask overlay, and region crop. The overlays are annotator context only and are not ground truth.

## Conservative Conclusion

The packet is ready for an independent reviewer, but P195 remains BLOCKED. The claim boundary does not change until reviewed, non-empty labels are added and audited.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--evidence-csv", type=Path, default=EVIDENCE_CSV)
    parser.add_argument("--evidence-json", type=Path, default=EVIDENCE_JSON)
    parser.add_argument("--protocol-md", type=Path, default=PROTOCOL_MD)
    parser.add_argument("--report-md", type=Path, default=REPORT_MD)
    parser.add_argument("--clean-output", action="store_true", help="remove the local output packet before rebuilding")
    return parser.parse_args()


def main() -> None:
    payload = build_packet(parse_args())
    print(
        "Built P239 independent dynamic-label mini packet: "
        f"{payload['packet_summary']['total_rows']} rows, "
        f"P195 {payload['p195_status_after_p239']}."
    )


if __name__ == "__main__":
    main()
