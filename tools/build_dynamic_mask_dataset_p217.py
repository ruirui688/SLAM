#!/usr/bin/env python3
"""Build the P217 no-manual dynamic-mask dataset.

P217 materializes a CUDA-ready binary dynamic/non-static mask dataset from
TorWIC AnnotatedSemanticSet labels only.  It deliberately does not use weak
admission labels, model predictions, or human-label placeholders as targets.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data/TorWIC_SLAM_Dataset"
ANNOTATED_ZIP = DATA_ROOT / "Oct. 12, 2022/AnnotatedSemanticSet_Finetuning.zip"
OUTPUT_ROOT = ROOT / "outputs/dynamic_mask_dataset_p217"
EVIDENCE_DIR = ROOT / "paper/evidence"
EXPORT_DIR = ROOT / "paper/export"
P195_JSON = EVIDENCE_DIR / "independent_supervision_gate_p195.json"

DYNAMIC_POSITIVE_CATEGORIES = {
    "cart_pallet_jack",
    "fork_truck",
    "goods_material",
    "misc_dynamic_feature",
    "misc_non_static_feature",
    "person",
    "pylon_cone",
}
STATIC_NEGATIVE_CATEGORIES = {"fixed_machinery", "misc_static_feature", "rack_shelf"}
CONTEXT_NEGATIVE_CATEGORIES = {
    "ceiling",
    "driveable_ground",
    "ego_vehicle",
    "text_region",
    "unlabeled",
    "wall_fence_pillar",
}
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def label_entries(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [value]
    return []


def parse_sample_id(raw_name: str) -> tuple[str, str]:
    match = re.search(r"Labelled_Test_Data/([^/]+)/(image_[0-9]+)\.png_raw_labels_2d/", raw_name)
    if not match:
        digest = hashlib.sha1(raw_name.encode("utf-8")).hexdigest()[:12]
        return digest, "unknown_view"
    return match.group(1), match.group(2)


def split_for_frame(frame_id: str) -> str:
    bucket = int(hashlib.sha1(frame_id.encode("utf-8")).hexdigest()[:8], 16) % 10
    if bucket < 7:
        return "train"
    if bucket < 9:
        return "val"
    return "test"


def safe_name(frame_id: str, view_id: str) -> str:
    return f"{frame_id}_{view_id.replace('_', '-')}"


def category_stats_from_mapping(mapping: dict[str, Any]) -> tuple[dict[str, int], dict[str, list[int]], list[int]]:
    pixels: dict[str, int] = {}
    indices_by_category: dict[str, list[int]] = {}
    dynamic_indices: list[int] = []
    for category, raw_value in mapping.items():
        entries = label_entries(raw_value)
        positive_entries = [entry for entry in entries if int(entry.get("numPixels") or 0) > 0]
        if not positive_entries:
            pixels[category] = 0
            indices_by_category[category] = []
            continue
        pixels[category] = sum(int(entry.get("numPixels") or 0) for entry in positive_entries)
        indices = sorted({int(entry["index"]) for entry in positive_entries if entry.get("index") is not None})
        indices_by_category[category] = indices
        if category in DYNAMIC_POSITIVE_CATEGORIES:
            dynamic_indices.extend(indices)
    return pixels, indices_by_category, sorted(set(dynamic_indices))


def binary_mask_from_indexed(indexed: Image.Image, dynamic_indices: list[int]) -> Image.Image:
    src = indexed.convert("L")
    lut = [255 if value in set(dynamic_indices) else 0 for value in range(256)]
    return src.point(lut, mode="L")


def copy_zip_image(archive: zipfile.ZipFile, member: str, destination: Path) -> Image.Image:
    image = Image.open(BytesIO(archive.read(member))).convert("RGB")
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination)
    return image


def write_sanity_contact_sheet(rows: list[dict[str, Any]], out_path: Path, limit: int = 6) -> list[dict[str, Any]]:
    samples = rows[:limit]
    if not samples:
        return []
    tiles: list[Image.Image] = []
    report: list[dict[str, Any]] = []
    for row in samples:
        image = Image.open(ROOT / row["image_path"]).convert("RGB")
        mask = Image.open(ROOT / row["binary_mask_path"]).convert("L")
        overlay = image.copy()
        red = Image.new("RGB", image.size, (255, 0, 0))
        alpha = mask.point(lambda value: 96 if value > 0 else 0, mode="L")
        overlay.paste(red, (0, 0), alpha)
        thumb_w = 320
        thumb_h = max(1, int(image.height * thumb_w / image.width))
        tile = Image.new("RGB", (thumb_w * 2, thumb_h), (0, 0, 0))
        tile.paste(image.resize((thumb_w, thumb_h)), (0, 0))
        tile.paste(overlay.resize((thumb_w, thumb_h)), (thumb_w, 0))
        tiles.append(tile)
        report.append(
            {
                "sample_id": row["sample_id"],
                "split": row["split"],
                "image_size": [image.width, image.height],
                "mask_size": [mask.width, mask.height],
                "positive_pixels": int(row["dynamic_positive_pixels"]),
                "positive_pixel_rate": float(row["dynamic_positive_pixel_rate"]),
            }
        )
    sheet = Image.new("RGB", (tiles[0].width, sum(tile.height for tile in tiles)), (0, 0, 0))
    y = 0
    for tile in tiles:
        sheet.paste(tile, (0, y))
        y += tile.height
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    return report


def build_dataset(zip_path: Path, output_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not zip_path.exists():
        raise FileNotFoundError(zip_path)

    image_out = output_root / "images"
    mask_out = output_root / "binary_masks"
    rows: list[dict[str, Any]] = []
    category_pixel_totals: Counter[str] = Counter()
    category_image_counts: Counter[str] = Counter()
    category_positive_indices: dict[str, set[int]] = defaultdict(set)
    skipped: list[dict[str, str]] = []

    with zipfile.ZipFile(zip_path) as archive:
        members = set(archive.namelist())
        raw_names = sorted(name for name in members if name.endswith("raw_labels_2d.json"))
        for raw_name in raw_names:
            prefix = raw_name.rsplit("/", 1)[0]
            source_member = f"{prefix}/source_image.png"
            indexed_member = f"{prefix}/combined_indexedImage.png"
            if source_member not in members or indexed_member not in members:
                skipped.append({"raw_labels": raw_name, "reason": "missing_source_or_indexed_mask"})
                continue
            payload = json.loads(archive.read(raw_name))
            mapping = payload.get("labelMapping")
            if not isinstance(mapping, dict):
                skipped.append({"raw_labels": raw_name, "reason": "missing_label_mapping"})
                continue
            frame_id, view_id = parse_sample_id(raw_name)
            sample_stem = safe_name(frame_id, view_id)
            image_path = image_out / f"{sample_stem}.png"
            mask_path = mask_out / f"{sample_stem}_dynamic.png"

            source = copy_zip_image(archive, source_member, image_path)
            indexed = Image.open(BytesIO(archive.read(indexed_member)))
            category_pixels, indices_by_category, dynamic_indices = category_stats_from_mapping(mapping)
            binary = binary_mask_from_indexed(indexed, dynamic_indices)
            if source.size != binary.size:
                skipped.append({"raw_labels": raw_name, "reason": f"dimension_mismatch_source_{source.size}_mask_{binary.size}"})
                continue
            mask_path.parent.mkdir(parents=True, exist_ok=True)
            binary.save(mask_path)

            total_pixels = source.width * source.height
            dynamic_positive_pixels = int(binary.histogram()[255])
            dynamic_positive_rate = dynamic_positive_pixels / total_pixels if total_pixels else 0.0
            positive_categories = sorted(category for category, count in category_pixels.items() if count > 0)
            dynamic_positive_categories = sorted(category for category in positive_categories if category in DYNAMIC_POSITIVE_CATEGORIES)
            static_negative_categories = sorted(category for category in positive_categories if category in STATIC_NEGATIVE_CATEGORIES)
            context_negative_categories = sorted(category for category in positive_categories if category in CONTEXT_NEGATIVE_CATEGORIES)
            unknown_categories = sorted(
                category
                for category in positive_categories
                if category not in DYNAMIC_POSITIVE_CATEGORIES
                and category not in STATIC_NEGATIVE_CATEGORIES
                and category not in CONTEXT_NEGATIVE_CATEGORIES
            )
            for category, pixels in category_pixels.items():
                if pixels > 0:
                    category_pixel_totals[category] += pixels
                    category_image_counts[category] += 1
                    category_positive_indices[category].update(indices_by_category.get(category, []))
            rows.append(
                {
                    "sample_id": sample_stem,
                    "frame_id": frame_id,
                    "view_id": view_id,
                    "split": split_for_frame(frame_id),
                    "image_path": rel(image_path),
                    "binary_mask_path": rel(mask_path),
                    "source_image_member": f"{rel(zip_path)}::{source_member}",
                    "indexed_mask_member": f"{rel(zip_path)}::{indexed_member}",
                    "raw_labels_member": f"{rel(zip_path)}::{raw_name}",
                    "source": "TorWIC AnnotatedSemanticSet_Finetuning dataset-provided raw_labels_2d + combined_indexedImage",
                    "target_policy": "binary_dynamic_non_static_from_dataset_semantic_indices; positives=cart_pallet_jack|fork_truck|goods_material|misc_dynamic_feature|misc_non_static_feature|person|pylon_cone; all other indexed/background pixels=0; no admission labels",
                    "width": source.width,
                    "height": source.height,
                    "total_pixels": total_pixels,
                    "dynamic_positive_pixels": dynamic_positive_pixels,
                    "dynamic_positive_pixel_rate": f"{dynamic_positive_rate:.8f}",
                    "dynamic_positive_categories": "|".join(dynamic_positive_categories),
                    "static_negative_categories": "|".join(static_negative_categories),
                    "context_negative_categories": "|".join(context_negative_categories),
                    "unknown_categories": "|".join(unknown_categories),
                    "category_pixel_stats_json": json.dumps(category_pixels, sort_keys=True, separators=(",", ":")),
                    "category_indices_json": json.dumps(indices_by_category, sort_keys=True, separators=(",", ":")),
                }
            )

    rows.sort(key=lambda row: (row["split"], row["frame_id"], row["view_id"]))
    metadata = {
        "skipped": skipped,
        "category_summary": [
            {
                "category": category,
                "role": "dynamic_positive"
                if category in DYNAMIC_POSITIVE_CATEGORIES
                else "static_negative"
                if category in STATIC_NEGATIVE_CATEGORIES
                else "context_negative"
                if category in CONTEXT_NEGATIVE_CATEGORIES
                else "unknown_excluded",
                "image_count": category_image_counts[category],
                "positive_pixels_total": category_pixel_totals[category],
                "positive_indices": sorted(category_positive_indices[category]),
            }
            for category in sorted(category_pixel_totals)
        ],
    }
    return rows, metadata


def validate_rows(rows: list[dict[str, Any]], sample_limit: int = 16) -> dict[str, Any]:
    checked = []
    failures = []
    for row in rows[:sample_limit]:
        image_path = ROOT / row["image_path"]
        mask_path = ROOT / row["binary_mask_path"]
        try:
            image = Image.open(image_path)
            mask = Image.open(mask_path)
            ok = image.size == mask.size
            checked.append({"sample_id": row["sample_id"], "image_size": list(image.size), "mask_size": list(mask.size), "ok": ok})
            if not ok:
                failures.append(row["sample_id"])
        except Exception as exc:  # pragma: no cover - defensive report path
            failures.append(f"{row['sample_id']}: {exc}")
    columns = set(rows[0].keys()) if rows else set()
    prohibited = sorted(columns & PROHIBITED_FIELDS)
    return {
        "sample_limit": sample_limit,
        "checked_count": len(checked),
        "checked": checked,
        "dimension_failures": failures,
        "manifest_prohibited_columns": prohibited,
        "pass": not failures and not prohibited and len(rows) > 0,
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    split_counts: Counter[str] = Counter(row["split"] for row in rows)
    split_positive_pixels: Counter[str] = Counter()
    split_total_pixels: Counter[str] = Counter()
    positive_rows: Counter[str] = Counter()
    frame_ids_by_split: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        split = row["split"]
        pos = int(row["dynamic_positive_pixels"])
        total = int(row["total_pixels"])
        split_positive_pixels[split] += pos
        split_total_pixels[split] += total
        positive_rows[split] += 1 if pos > 0 else 0
        frame_ids_by_split[split].add(row["frame_id"])
    return {
        "total_rows": len(rows),
        "split_counts": dict(sorted(split_counts.items())),
        "positive_row_counts_by_split": dict(sorted(positive_rows.items())),
        "frame_group_counts_by_split": {split: len(ids) for split, ids in sorted(frame_ids_by_split.items())},
        "positive_pixel_rate_by_split": {
            split: (split_positive_pixels[split] / split_total_pixels[split] if split_total_pixels[split] else 0.0)
            for split in sorted(split_total_pixels)
        },
        "overall_positive_pixel_rate": (
            sum(split_positive_pixels.values()) / sum(split_total_pixels.values()) if sum(split_total_pixels.values()) else 0.0
        ),
        "frame_group_overlap": {
            "train_val": len(frame_ids_by_split["train"] & frame_ids_by_split["val"]),
            "train_test": len(frame_ids_by_split["train"] & frame_ids_by_split["test"]),
            "val_test": len(frame_ids_by_split["val"] & frame_ids_by_split["test"]),
        },
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sample_id",
        "frame_id",
        "view_id",
        "split",
        "image_path",
        "binary_mask_path",
        "source_image_member",
        "indexed_mask_member",
        "raw_labels_member",
        "source",
        "target_policy",
        "width",
        "height",
        "total_pixels",
        "dynamic_positive_pixels",
        "dynamic_positive_pixel_rate",
        "dynamic_positive_categories",
        "static_negative_categories",
        "context_negative_categories",
        "unknown_categories",
        "category_pixel_stats_json",
        "category_indices_json",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# P217 Dynamic-Mask Dataset",
        "",
        f"**Status:** {payload['status']}",
        "",
        "## Boundary",
        "",
        payload["claim_boundary"],
        "",
        "## Dataset",
        "",
        f"- Rows: `{summary['total_rows']}`",
        f"- Split counts: `{summary['split_counts']}`",
        f"- Frame-group counts by split: `{summary['frame_group_counts_by_split']}`",
        f"- Overall dynamic/non-static positive pixel rate: `{summary['overall_positive_pixel_rate']:.6f}`",
        f"- Frame-group overlap: `{summary['frame_group_overlap']}`",
        "",
        "## Target Policy",
        "",
        "- Positive categories: `cart_pallet_jack`, `fork_truck`, `goods_material`, `misc_dynamic_feature`, `misc_non_static_feature`, `person`, `pylon_cone`.",
        "- `goods_material` is included as movable clutter because the dataset category denotes material/goods that can be rearranged in industrial scenes; this is a front-end non-static mask target, not persistent-map admission ground truth.",
        "- Static object, context, and background pixels are encoded as binary 0.",
        "- No P193 weak labels, admission targets, model predictions, or human-label placeholders are used.",
        "",
        "## Outputs",
        "",
        f"- CSV manifest: `{payload['outputs']['csv_manifest']}`",
        f"- JSON manifest: `{payload['outputs']['json_manifest']}`",
        f"- Sanity contact sheet: `{payload['sanity']['contact_sheet']}`",
        "",
        "## P195",
        "",
        f"- Status: `{payload['p195_status'].get('status', 'unknown')}`",
        f"- Human labels remain blank: `{payload['p195_status'].get('human_labels_blank', 'unknown')}`",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def p195_status() -> dict[str, Any]:
    payload = load_json(P195_JSON)
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotated-zip", type=Path, default=ANNOTATED_ZIP)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--sample-check-count", type=int, default=16)
    args = parser.parse_args()

    rows, metadata = build_dataset(args.annotated_zip, args.output_root)
    summary = summarize(rows)
    validation = validate_rows(rows, args.sample_check_count)
    sanity_path = args.output_root / "sanity/p217_dynamic_mask_sanity.png"
    sanity_samples = write_sanity_contact_sheet(rows, sanity_path)

    csv_path = EVIDENCE_DIR / "dynamic_mask_dataset_p217.csv"
    json_path = EVIDENCE_DIR / "dynamic_mask_dataset_p217.json"
    md_path = EXPORT_DIR / "dynamic_mask_dataset_p217.md"
    write_csv(csv_path, rows)

    status = "READY_NO_MANUAL_DYNAMIC_MASK_DATASET" if validation["pass"] else "FAILED_VALIDATION"
    payload = {
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": "P217 creates a no-manual semantic/dynamic-mask front-end dataset from dataset-provided TorWIC AnnotatedSemanticSet labels only. It does not create admission labels, same-object labels, or learned admission-control evidence.",
        "source": {
            "annotated_zip": rel(args.annotated_zip),
            "raw_data_touched": False,
            "sequence_greyscale_masks_used": False,
            "sequence_greyscale_note": "Not used because AnnotatedSemanticSet gives explicit per-sample category-to-index mappings; no sequence greyscale IDs were guessed.",
        },
        "target_policy": {
            "name": "binary_dynamic_non_static_from_dataset_semantic_indices",
            "positive_categories": sorted(DYNAMIC_POSITIVE_CATEGORIES),
            "static_negative_categories": sorted(STATIC_NEGATIVE_CATEGORIES),
            "context_negative_categories": sorted(CONTEXT_NEGATIVE_CATEGORIES),
            "goods_material_justification": "Included as movable clutter for SLAM front-end masking because industrial goods/material can be rearranged; this is not an admission-control label.",
            "negative_encoding": "All other indexed/background pixels are binary 0.",
        },
        "summary": summary,
        "category_summary": metadata["category_summary"],
        "skipped": metadata["skipped"],
        "validation": validation,
        "sanity": {
            "contact_sheet": rel(sanity_path),
            "samples": sanity_samples,
        },
        "leakage_guard": {
            "prohibited_fields": sorted(PROHIBITED_FIELDS),
            "manifest_prohibited_columns": validation["manifest_prohibited_columns"],
            "uses_p193_target_admit": False,
            "uses_current_weak_label": False,
            "uses_selection_v5": False,
            "uses_model_predictions_as_labels": False,
            "uses_human_labels": False,
        },
        "p195_status": p195_status(),
        "outputs": {
            "csv_manifest": rel(csv_path),
            "json_manifest": rel(json_path),
            "markdown_report": rel(md_path),
            "derived_image_root": rel(args.output_root / "images"),
            "derived_binary_mask_root": rel(args.output_root / "binary_masks"),
        },
    }
    write_json(json_path, payload)
    write_markdown(md_path, payload)
    print(
        json.dumps(
            {
                "status": status,
                "rows": summary["total_rows"],
                "split_counts": summary["split_counts"],
                "overall_positive_pixel_rate": summary["overall_positive_pixel_rate"],
                "csv": rel(csv_path),
                "json": rel(json_path),
                "sanity": rel(sanity_path),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if status == "READY_NO_MANUAL_DYNAMIC_MASK_DATASET" else 1


if __name__ == "__main__":
    raise SystemExit(main())
