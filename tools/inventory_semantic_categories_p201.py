#!/usr/bin/env python3
"""Inventory P201 no-label semantic categories from local TorWIC assets.

P201 is deliberately an inventory/feasibility artifact.  It reads only local
raw TorWIC segmentation assets and existing generated manifests.  It does not
create human labels, does not use P193/P197 weak admission targets as labels,
and does not train admission control.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

STATIC_LIKE_OBJECT_CATEGORIES = {
    "rack_shelf",
    "fixed_machinery",
    "misc_static_feature",
}
STATIC_CONTEXT_CATEGORIES = {
    "wall_fence_pillar",
    "ceiling",
    "driveable_ground",
}
DYNAMIC_OR_NON_STATIC_OBJECT_CATEGORIES = {
    "fork_truck",
    "person",
    "cart_pallet_jack",
    "pylon_cone",
    "misc_dynamic_feature",
    "misc_non_static_feature",
    "goods_material",
}
CONTEXT_ONLY_CATEGORIES = {
    "wall_fence_pillar",
    "ceiling",
    "driveable_ground",
    "ego_vehicle",
    "text_region",
    "unlabeled",
}

OPEN_VOCAB_TO_TORWIC = {
    "forklift": ["fork_truck"],
    "fork": ["fork_truck"],
    "rack forklift": ["fork_truck", "rack_shelf"],
    "##lift": ["fork_truck"],
    "warehouse rack": ["rack_shelf"],
    "rack": ["rack_shelf"],
    "barrier": ["misc_static_feature", "pylon_cone"],
    "yellow barrier": ["misc_static_feature", "pylon_cone"],
    "work table": ["misc_static_feature", "fixed_machinery"],
    "work": ["misc_static_feature", "fixed_machinery"],
    "table": ["misc_static_feature", "fixed_machinery"],
}

CSV_COLUMNS = [
    "semantic_category",
    "stability_policy",
    "map_object_role",
    "raw_annotated_image_count",
    "raw_annotated_instance_count",
    "raw_positive_pixels_total",
    "raw_positive_pixels_median_per_image",
    "raw_positive_pixels_max_per_image",
    "raw_label_indices",
    "raw_label_colors",
    "existing_manifest_instance_count",
    "existing_observation_count",
    "candidate_for_auxiliary_expansion",
    "expansion_blocker",
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in CSV_COLUMNS})


def norm_label(value: Any) -> str:
    text = str(value or "").strip().lower().replace("_", " ").replace("-", " ")
    return re.sub(r"\s+", " ", text)


def semantic_policy(category: str) -> tuple[str, str, bool]:
    if category in STATIC_LIKE_OBJECT_CATEGORIES:
        return "static_like", "map_object_candidate", True
    if category in DYNAMIC_OR_NON_STATIC_OBJECT_CATEGORIES:
        if category == "goods_material":
            return "dynamic_or_non_static_like", "movable_clutter_candidate", True
        return "dynamic_or_non_static_like", "map_object_candidate", True
    if category in STATIC_CONTEXT_CATEGORIES:
        return "static_context_only", "context_only_not_admission_object", False
    return "exclude_or_unknown", "context_only_not_admission_object", False


def label_mapping_entries(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [value]
    return []


def inventory_annotated_zip(zip_path: Path) -> dict[str, Any]:
    categories: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "image_count": 0,
            "instance_count": 0,
            "positive_pixels_total": 0,
            "positive_pixels_by_image": [],
            "indices": set(),
            "colors": set(),
        }
    )
    raw_json_count = 0
    archive_members = 0
    labeled_roots: Counter[str] = Counter()
    if not zip_path.exists():
        return {
            "status": "missing",
            "path": rel(zip_path),
            "raw_json_count": 0,
            "archive_members": 0,
            "categories": {},
            "labeled_roots": {},
        }
    with zipfile.ZipFile(zip_path) as handle:
        names = handle.namelist()
        archive_members = len(names)
        raw_names = [name for name in names if name.endswith("raw_labels_2d.json")]
        raw_json_count = len(raw_names)
        for name in raw_names:
            parts = Path(name).parts
            if len(parts) >= 2:
                labeled_roots[parts[1]] += 1
            try:
                payload = json.loads(handle.read(name))
            except Exception:
                continue
            mapping = payload.get("labelMapping", {})
            if not isinstance(mapping, dict):
                continue
            for category, raw_entries in mapping.items():
                entries = label_mapping_entries(raw_entries)
                positive_entries = [entry for entry in entries if int(entry.get("numPixels") or 0) > 0]
                if not positive_entries:
                    continue
                image_pixels = sum(int(entry.get("numPixels") or 0) for entry in positive_entries)
                record = categories[category]
                record["image_count"] += 1
                record["instance_count"] += len(positive_entries)
                record["positive_pixels_total"] += image_pixels
                record["positive_pixels_by_image"].append(image_pixels)
                for entry in positive_entries:
                    if entry.get("index") is not None:
                        record["indices"].add(int(entry["index"]))
                    if entry.get("color"):
                        record["colors"].add(str(entry["color"]))
    out_categories: dict[str, Any] = {}
    for category, record in sorted(categories.items()):
        pixels = record["positive_pixels_by_image"]
        out_categories[category] = {
            "image_count": record["image_count"],
            "instance_count": record["instance_count"],
            "positive_pixels_total": record["positive_pixels_total"],
            "positive_pixels_median_per_image": int(statistics.median(pixels)) if pixels else 0,
            "positive_pixels_max_per_image": max(pixels) if pixels else 0,
            "indices": sorted(record["indices"]),
            "colors": sorted(record["colors"]),
        }
    return {
        "status": "ok",
        "path": rel(zip_path),
        "raw_json_count": raw_json_count,
        "archive_members": archive_members,
        "labeled_roots": dict(sorted(labeled_roots.items())),
        "categories": out_categories,
    }


def sequence_from_seg_dir(path: Path) -> tuple[str, str, str]:
    parts = path.parts
    try:
        index = parts.index("TorWIC_SLAM_Dataset")
        date = parts[index + 1]
        sequence = parts[index + 2]
    except (ValueError, IndexError):
        date = ""
        sequence = ""
    return date, sequence, path.name


def inventory_extracted_segmentation(data_root: Path) -> dict[str, Any]:
    dirs = [
        path
        for path in data_root.glob("*/*/**")
        if path.is_dir() and path.name.startswith("segmentation_")
    ]
    per_dir = []
    by_sequence: dict[str, dict[str, Any]] = defaultdict(lambda: {"png_count": 0, "directories": []})
    by_kind: Counter[str] = Counter()
    for path in sorted(dirs):
        date, sequence, kind = sequence_from_seg_dir(path)
        png_count = sum(1 for _ in path.glob("*.png"))
        key = f"{date}/{sequence}"
        per_dir.append({"path": rel(path), "date": date, "sequence": sequence, "kind": kind, "png_count": png_count})
        by_sequence[key]["png_count"] += png_count
        by_sequence[key]["directories"].append(rel(path))
        by_kind[kind] += png_count
    return {
        "directory_count": len(dirs),
        "png_count": sum(item["png_count"] for item in per_dir),
        "by_kind": dict(sorted(by_kind.items())),
        "by_sequence": dict(sorted(by_sequence.items())),
        "directories": per_dir,
        "category_mapping_status": "blocked: extracted sequence masks have color/greyscale pixels but no per-frame raw_labels_2d.json metadata in the extracted directories; category counts require either zip-side metadata or a trusted color/index map.",
    }


def inventory_sequence_zips(data_root: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for zip_path in sorted(data_root.glob("*/*.zip")):
        if zip_path.name == "AnnotatedSemanticSet_Finetuning.zip":
            continue
        try:
            with zipfile.ZipFile(zip_path) as handle:
                names = handle.namelist()
        except Exception as exc:
            out[rel(zip_path)] = {"status": "error", "error": str(exc)}
            continue
        counts = Counter()
        for name in names:
            parts = Path(name).parts
            for part in parts:
                if part.startswith("segmentation_") and name.endswith(".png"):
                    counts[part] += 1
        out[rel(zip_path)] = {"status": "ok", "segmentation_png_counts": dict(sorted(counts.items()))}
    return out


def iter_json_files(*roots: Path) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        files.extend(root.glob("**/*.json"))
    return sorted(set(files))


def inventory_existing_manifests() -> dict[str, Any]:
    manifest_counts: Counter[str] = Counter()
    observation_counts: Counter[str] = Counter()
    target_label_counts: Counter[str] = Counter()
    manifest_files = 0
    observation_index_files = 0
    all_manifest_paths: list[str] = []
    all_observation_index_paths: list[str] = []
    for path in iter_json_files(ROOT / "outputs", ROOT / "tmp", ROOT / "examples"):
        if "thirdparty" in path.parts:
            continue
        if path.name == "all_instances_manifest.json":
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            manifest_files += 1
            all_manifest_paths.append(rel(path))
            for label in payload.get("target_labels") or []:
                target_label_counts[norm_label(label)] += 1
            for instance in payload.get("instances") or []:
                label = norm_label(instance.get("resolved_label") or instance.get("grounding_label"))
                if label:
                    manifest_counts[label] += 1
        elif path.name == "observations_index.json":
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            observation_index_files += 1
            all_observation_index_paths.append(rel(path))
            for observation in payload.get("observations") or []:
                label = norm_label(observation.get("resolved_label") or observation.get("grounding_label"))
                if label:
                    observation_counts[label] += 1
    torwic_semantic_counts: Counter[str] = Counter()
    for label, count in manifest_counts.items():
        for category in OPEN_VOCAB_TO_TORWIC.get(label, []):
            torwic_semantic_counts[category] += count
    return {
        "manifest_file_count": manifest_files,
        "observation_index_file_count": observation_index_files,
        "instance_label_counts": dict(sorted(manifest_counts.items())),
        "observation_label_counts": dict(sorted(observation_counts.items())),
        "target_label_counts": dict(sorted(target_label_counts.items())),
        "mapped_torwic_semantic_instance_counts": dict(sorted(torwic_semantic_counts.items())),
        "manifest_paths_sample": all_manifest_paths[:20],
        "observation_index_paths_sample": all_observation_index_paths[:20],
    }


def human_label_blank_audit() -> dict[str, Any]:
    files = {
        "boundary_p194": (ROOT / "paper/evidence/admission_boundary_label_sheet_p194.csv", "human_admit_label"),
        "boundary_p197": (ROOT / "paper/evidence/admission_boundary_label_sheet_p197_semantic_review.csv", "human_admit_label"),
        "pairs_p194": (ROOT / "paper/evidence/association_pair_candidates_p194.csv", "human_same_object_label"),
        "pairs_p197": (ROOT / "paper/evidence/association_pair_candidates_p197_semantic_review.csv", "human_same_object_label"),
    }
    audit: dict[str, Any] = {}
    for name, (path, column) in files.items():
        rows = read_csv(path)
        nonblank = sum(1 for row in rows if str(row.get(column, "")).strip())
        audit[name] = {"path": rel(path), "column": column, "rows": len(rows), "blank": len(rows) - nonblank, "nonblank": nonblank}
    return audit


def build_category_rows(annotated: dict[str, Any], manifests: dict[str, Any]) -> list[dict[str, Any]]:
    raw_categories = annotated.get("categories", {})
    manifest_semantic = manifests.get("mapped_torwic_semantic_instance_counts", {})
    observation_by_label = manifests.get("observation_label_counts", {})
    rows: list[dict[str, Any]] = []
    categories = set(raw_categories) | set(manifest_semantic)
    for category in sorted(categories):
        raw = raw_categories.get(category, {})
        policy, role, candidate = semantic_policy(category)
        mapped_observation_count = 0
        for label, mapped_categories in OPEN_VOCAB_TO_TORWIC.items():
            if category in mapped_categories:
                mapped_observation_count += int(observation_by_label.get(label, 0))
        blocker = ""
        if category in CONTEXT_ONLY_CATEGORIES:
            blocker = "context-only category; useful as environment context but not an object admission sample"
        elif mapped_observation_count == 0:
            blocker = "present in raw annotation inventory but absent from existing object observation manifests"
        elif category in {"misc_static_feature", "pylon_cone"}:
            blocker = "currently appears through barrier/yellow-barrier labels that map to both static and non-static categories"
        rows.append(
            {
                "semantic_category": category,
                "stability_policy": policy,
                "map_object_role": role,
                "raw_annotated_image_count": raw.get("image_count", 0),
                "raw_annotated_instance_count": raw.get("instance_count", 0),
                "raw_positive_pixels_total": raw.get("positive_pixels_total", 0),
                "raw_positive_pixels_median_per_image": raw.get("positive_pixels_median_per_image", 0),
                "raw_positive_pixels_max_per_image": raw.get("positive_pixels_max_per_image", 0),
                "raw_label_indices": ";".join(str(v) for v in raw.get("indices", [])),
                "raw_label_colors": ";".join(raw.get("colors", [])),
                "existing_manifest_instance_count": manifest_semantic.get(category, 0),
                "existing_observation_count": mapped_observation_count,
                "candidate_for_auxiliary_expansion": "yes" if candidate and mapped_observation_count > 0 and not blocker else "inventory_only",
                "expansion_blocker": blocker,
            }
        )
    return rows


def feasibility(category_rows: list[dict[str, Any]], annotated: dict[str, Any], manifests: dict[str, Any]) -> dict[str, Any]:
    raw_candidate_rows = [
        row
        for row in category_rows
        if row["map_object_role"] in {"map_object_candidate", "movable_clutter_candidate"}
        and int(row["raw_annotated_image_count"]) > 0
    ]
    manifest_candidate_rows = [
        row
        for row in category_rows
        if int(row["existing_observation_count"]) > 0
        and row["semantic_category"] not in {"misc_static_feature", "pylon_cone"}
        and row["map_object_role"] in {"map_object_candidate", "movable_clutter_candidate"}
    ]
    raw_candidate_categories = {row["semantic_category"] for row in raw_candidate_rows}
    manifest_candidate_categories = {row["semantic_category"] for row in manifest_candidate_rows}
    p199_categories = {"fork_truck", "rack_shelf", "fixed_machinery", "misc_static_feature", "pylon_cone"}
    additional_raw = sorted(raw_candidate_categories - p199_categories)
    additional_manifest_safe = sorted(manifest_candidate_categories - p199_categories)
    can_break = bool(additional_manifest_safe)
    blockers = [
        "Existing object observations/front-end manifests are still prompt-limited mostly to forklift, rack, work table, and barrier/yellow barrier.",
        "The richer AnnotatedSemanticSet_Finetuning.zip categories have frame/image IDs and mask pixels, but no local join to observation_id, tracklet_id, physical_key, or cross-session object clusters.",
        "Extracted sequence segmentation_color/greyscale directories do not include per-frame raw_labels_2d.json metadata in the extracted folders, and raw category masks are not connected to current observation manifests.",
        "Using P193 target_admit/current_weak_label/selection_v5/model predictions would create prohibited target leakage, so those fields are not used.",
    ]
    return {
        "can_break_category_target_degeneracy_with_current_local_data": can_break,
        "answer": "no" if not can_break else "yes_but_inventory_only",
        "raw_candidate_category_count": len(raw_candidate_categories),
        "raw_candidate_categories": sorted(raw_candidate_categories),
        "additional_raw_candidate_categories_beyond_p199": additional_raw,
        "safe_manifest_join_candidate_category_count": len(manifest_candidate_categories),
        "safe_manifest_join_candidate_categories": sorted(manifest_candidate_categories),
        "additional_safe_manifest_categories_beyond_p199": additional_manifest_safe,
        "target_policy_if_future_join_exists": "category-derived static_like versus dynamic_or_non_static_like auxiliary target only; context-only categories excluded from object admission rows; no admit/reject labels.",
        "current_blockers": blockers,
        "decision": (
            "Do not materialize an expanded semantic-stability training dataset from current local assets. "
            "The raw ontology is broader, but the missing raw-mask-to-observation/tracklet/physical-key join would force guessing labels."
        ),
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    counts = payload["counts"]
    feasibility_report = payload["feasibility"]
    raw = payload["annotated_semantic_zip"]
    lines = [
        "# P201 No-Label Semantic Category Inventory",
        "",
        f"**Status:** {payload['status']}",
        "",
        "## Boundary",
        "",
        payload["scientific_boundary"],
        "",
        "## Inventory Counts",
        "",
        f"- Annotated raw label JSON files: {raw.get('raw_json_count', 0)}",
        f"- Annotated semantic categories with positive pixels: {counts['raw_categories_with_positive_pixels']}",
        f"- Candidate raw map-object/movable-clutter categories: {counts['raw_candidate_category_count']}",
        f"- Existing all-instances manifests: {counts['manifest_file_count']}",
        f"- Existing observation indexes: {counts['observation_index_file_count']}",
        f"- Extracted segmentation directories: {counts['extracted_segmentation_directory_count']}",
        f"- Extracted segmentation PNGs: {counts['extracted_segmentation_png_count']}",
        "",
        "## Candidate Categories",
        "",
        f"- Static-like object candidates: `{payload['category_policy']['static_like_object_categories']}`",
        f"- Static context only: `{payload['category_policy']['static_context_categories']}`",
        f"- Dynamic/non-static object or clutter candidates: `{payload['category_policy']['dynamic_or_non_static_object_categories']}`",
        f"- Context-only/excluded categories: `{payload['category_policy']['context_only_categories']}`",
        "",
        "## Feasibility Answer",
        "",
        f"- Can current local data break the P199/P200 category=target degeneracy? **{feasibility_report['answer'].upper()}**",
        f"- Additional raw candidate categories beyond P199: `{feasibility_report['additional_raw_candidate_categories_beyond_p199']}`",
        f"- Additional safely joined manifest categories beyond P199: `{feasibility_report['additional_safe_manifest_categories_beyond_p199']}`",
        f"- Target policy if a safe join is added later: {feasibility_report['target_policy_if_future_join_exists']}",
        "",
        "## Missing Joins",
        "",
    ]
    lines.extend(f"- {item}" for item in feasibility_report["current_blockers"])
    lines.extend(
        [
            "",
            "## Label Audit",
            "",
            f"- P195 status remains: `{payload['p195_status']}`",
            "- No `human_admit_label` or `human_same_object_label` values were created or filled.",
            "",
            "## Outputs",
            "",
            f"- JSON: `{payload['outputs']['json']}`",
            f"- CSV: `{payload['outputs']['csv']}`",
            "",
            f"**P202 recommendation:** {payload['p202_recommendation']}",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", default="data/TorWIC_SLAM_Dataset")
    parser.add_argument("--annotated-zip", default="data/TorWIC_SLAM_Dataset/Oct. 12, 2022/AnnotatedSemanticSet_Finetuning.zip")
    parser.add_argument("--output-json", default="paper/evidence/semantic_category_inventory_p201.json")
    parser.add_argument("--output-csv", default="paper/evidence/semantic_category_inventory_p201.csv")
    parser.add_argument("--output-md", default="paper/export/semantic_category_inventory_p201.md")
    args = parser.parse_args()

    data_root = ROOT / args.data_root
    annotated = inventory_annotated_zip(ROOT / args.annotated_zip)
    extracted = inventory_extracted_segmentation(data_root)
    sequence_zips = inventory_sequence_zips(data_root)
    manifests = inventory_existing_manifests()
    label_audit = human_label_blank_audit()
    category_rows = build_category_rows(annotated, manifests)
    feasibility_report = feasibility(category_rows, annotated, manifests)

    p195_status = "BLOCKED" if all(item["nonblank"] == 0 for item in label_audit.values()) else "RECHECK_REQUIRED"
    payload = {
        "status": "INVENTORY_COMPLETE_EXPANSION_BLOCKED_BY_MISSING_SAFE_JOIN",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scientific_boundary": (
            "P201 inventories no-human-label semantic assets only. It does not create human labels, "
            "does not use P193/P197 weak admission targets/model predictions as target labels, "
            "and does not claim admission control."
        ),
        "inputs": {
            "data_root": rel(data_root),
            "annotated_zip": args.annotated_zip,
            "p199_report": "paper/export/semantic_stability_dataset_p199.md",
            "p200_report": "paper/export/semantic_stability_audit_p200.md",
        },
        "annotated_semantic_zip": annotated,
        "extracted_sequence_segmentation": extracted,
        "sequence_zip_segmentation_counts": sequence_zips,
        "existing_outputs_and_manifests": manifests,
        "category_policy": {
            "static_like_object_categories": sorted(STATIC_LIKE_OBJECT_CATEGORIES),
            "static_context_categories": sorted(STATIC_CONTEXT_CATEGORIES),
            "dynamic_or_non_static_object_categories": sorted(DYNAMIC_OR_NON_STATIC_OBJECT_CATEGORIES),
            "context_only_categories": sorted(CONTEXT_ONLY_CATEGORIES),
            "open_vocab_to_torwic_mapping": OPEN_VOCAB_TO_TORWIC,
        },
        "category_rows": category_rows,
        "feasibility": feasibility_report,
        "p195_status": p195_status,
        "human_label_blank_audit": label_audit,
        "counts": {
            "raw_categories_with_positive_pixels": len(annotated.get("categories", {})),
            "raw_candidate_category_count": feasibility_report["raw_candidate_category_count"],
            "manifest_file_count": manifests["manifest_file_count"],
            "observation_index_file_count": manifests["observation_index_file_count"],
            "extracted_segmentation_directory_count": extracted["directory_count"],
            "extracted_segmentation_png_count": extracted["png_count"],
        },
        "outputs": {
            "json": args.output_json,
            "csv": args.output_csv,
            "markdown": args.output_md,
        },
        "p202_recommendation": (
            "Build a safe raw-segmentation-to-observation join first: map raw sequence/date/frame/camera/category "
            "masks to observation_id/tracklet/physical_key and then rerun a no-label auxiliary dataset build. "
            "Keep P195 blocked until independent human labels exist."
        ),
    }
    write_json(ROOT / args.output_json, payload)
    write_csv(ROOT / args.output_csv, category_rows)
    write_markdown(ROOT / args.output_md, payload)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_csv}")
    print(f"wrote {args.output_md}")
    print(f"feasibility={feasibility_report['answer']} p195={p195_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
