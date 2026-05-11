#!/usr/bin/env python3
"""P216 no-manual-training redirect audit.

This script inventories trainable targets that are already present in local
TorWIC assets, without promoting admission proxies or model predictions into
ground truth.  Its only optional training action is a two-sample CUDA smoke
test over dataset-provided semantic masks from AnnotatedSemanticSet.
"""
from __future__ import annotations

import argparse
import csv
import json
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data/TorWIC_SLAM_Dataset"
ANNOTATED_ZIP = DATA_ROOT / "Oct. 12, 2022/AnnotatedSemanticSet_Finetuning.zip"
P195_JSON = ROOT / "paper/evidence/independent_supervision_gate_p195.json"

STATIC_OBJECT_CATEGORIES = {"fixed_machinery", "misc_static_feature", "rack_shelf"}
MOVABLE_OR_DYNAMIC_CATEGORIES = {
    "cart_pallet_jack",
    "fork_truck",
    "goods_material",
    "misc_dynamic_feature",
    "misc_non_static_feature",
    "person",
    "pylon_cone",
}
CONTEXT_CATEGORIES = {"ceiling", "driveable_ground", "ego_vehicle", "text_region", "unlabeled", "wall_fence_pillar"}
PROHIBITED_TARGET_FIELDS = {
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


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def label_mapping_entries(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [value]
    return []


def category_role(category: str) -> str:
    if category in STATIC_OBJECT_CATEGORIES:
        return "static_object_semantic_class"
    if category in MOVABLE_OR_DYNAMIC_CATEGORIES:
        return "movable_or_dynamic_semantic_class"
    if category in CONTEXT_CATEGORIES:
        return "context_semantic_class"
    return "unknown_or_excluded"


def inspect_annotated_zip(zip_path: Path) -> dict[str, Any]:
    if not zip_path.exists():
        return {"status": "missing", "path": rel(zip_path)}
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        raw_json_names = [name for name in names if name.endswith("raw_labels_2d.json")]
        source_names = [name for name in names if name.endswith("source_image.png")]
        indexed_names = [name for name in names if name.endswith("combined_indexedImage.png")]
        combined_names = [name for name in names if name.endswith("combined_image.png")]
        categories: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "image_count": 0,
                "instance_count": 0,
                "positive_pixels_total": 0,
                "indices": set(),
                "colors": set(),
            }
        )
        indexed_pairs = 0
        sample_records: list[dict[str, str]] = []
        for raw_name in raw_json_names:
            prefix = raw_name.rsplit("/", 1)[0]
            source_name = f"{prefix}/source_image.png"
            indexed_name = f"{prefix}/combined_indexedImage.png"
            if source_name in names and indexed_name in names:
                indexed_pairs += 1
                if len(sample_records) < 5:
                    sample_records.append(
                        {
                            "raw_labels": f"{rel(zip_path)}::{raw_name}",
                            "source_image": f"{rel(zip_path)}::{source_name}",
                            "indexed_mask": f"{rel(zip_path)}::{indexed_name}",
                        }
                    )
            try:
                payload = json.loads(archive.read(raw_name))
            except Exception:
                continue
            mapping = payload.get("labelMapping", {})
            if not isinstance(mapping, dict):
                continue
            for category, raw_entries in mapping.items():
                entries = [entry for entry in label_mapping_entries(raw_entries) if int(entry.get("numPixels") or 0) > 0]
                if not entries:
                    continue
                record = categories[category]
                record["image_count"] += 1
                record["instance_count"] += len(entries)
                record["positive_pixels_total"] += sum(int(entry.get("numPixels") or 0) for entry in entries)
                for entry in entries:
                    if entry.get("index") is not None:
                        record["indices"].add(int(entry["index"]))
                    if entry.get("color"):
                        record["colors"].add(str(entry["color"]))
        category_rows = []
        for category, record in sorted(categories.items()):
            category_rows.append(
                {
                    "category": category,
                    "role": category_role(category),
                    "image_count": record["image_count"],
                    "instance_count": record["instance_count"],
                    "positive_pixels_total": record["positive_pixels_total"],
                    "indices": sorted(record["indices"]),
                    "colors": sorted(record["colors"]),
                }
            )
    return {
        "status": "ok",
        "path": rel(zip_path),
        "archive_members": len(names),
        "raw_label_json_count": len(raw_json_names),
        "source_image_count": len(source_names),
        "combined_indexed_mask_count": len(indexed_names),
        "combined_color_mask_count": len(combined_names),
        "paired_source_indexed_mask_count": indexed_pairs,
        "category_count": len(category_rows),
        "categories": category_rows,
        "sample_training_records": sample_records,
    }


def inspect_sequence_masks(data_root: Path) -> dict[str, Any]:
    sequence_dirs = sorted(path for path in data_root.glob("*/*/*") if path.is_dir())
    by_kind: Counter[str] = Counter()
    by_sequence: dict[str, dict[str, Any]] = {}
    for sequence_dir in sequence_dirs:
        image_left = sequence_dir / "image_left"
        if not image_left.exists():
            continue
        relative = rel(sequence_dir)
        item: dict[str, Any] = {
            "image_left_count": len(list(image_left.glob("*.png"))),
            "segmentation": {},
        }
        for kind in [
            "segmentation_color_left",
            "segmentation_greyscale_left",
            "segmentation_color_right",
            "segmentation_greyscale_right",
        ]:
            count = len(list((sequence_dir / kind).glob("*.png"))) if (sequence_dir / kind).exists() else 0
            item["segmentation"][kind] = count
            by_kind[kind] += count
        by_sequence[relative] = item
    complete_left = sum(
        1
        for item in by_sequence.values()
        if item["image_left_count"] > 0 and item["segmentation"].get("segmentation_greyscale_left") == item["image_left_count"]
    )
    return {
        "data_root": rel(data_root),
        "sequence_count_with_images": len(by_sequence),
        "sequence_count_with_complete_left_greyscale_masks": complete_left,
        "segmentation_png_counts_by_kind": dict(sorted(by_kind.items())),
        "sample_sequences": dict(list(sorted(by_sequence.items()))[:8]),
    }


def inspect_sequence_zips(data_root: Path) -> dict[str, Any]:
    zip_count = 0
    left_pairs = 0
    segmentation_counts: Counter[str] = Counter()
    for zip_path in sorted(data_root.glob("*/*.zip")):
        if zip_path.name == ANNOTATED_ZIP.name:
            continue
        zip_count += 1
        try:
            with zipfile.ZipFile(zip_path) as archive:
                names = archive.namelist()
        except Exception:
            continue
        image_left = {name.rsplit("/", 1)[-1] for name in names if "/image_left/" in name and name.endswith(".png")}
        seg_left = {name.rsplit("/", 1)[-1] for name in names if "/segmentation_greyscale_left/" in name and name.endswith(".png")}
        left_pairs += len(image_left & seg_left)
        for name in names:
            if name.endswith(".png"):
                for part in Path(name).parts:
                    if part.startswith("segmentation_"):
                        segmentation_counts[part] += 1
    return {
        "sequence_zip_count": zip_count,
        "left_rgb_greyscale_mask_pair_count": left_pairs,
        "segmentation_png_counts_by_kind": dict(sorted(segmentation_counts.items())),
    }


def read_csv_columns(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return set(reader.fieldnames or [])


def leakage_guard() -> dict[str, Any]:
    target_artifacts = {
        "p216_json": ROOT / "paper/evidence/no_manual_training_redirect_p216.json",
        "p216_markdown": ROOT / "paper/export/no_manual_training_redirect_p216.md",
    }
    source_columns = {
        "p193_dataset": read_csv_columns(ROOT / "paper/evidence/admission_frame_dataset_p193.csv"),
        "p194_boundary": read_csv_columns(ROOT / "paper/evidence/admission_boundary_label_sheet_p194.csv"),
        "p194_pairs": read_csv_columns(ROOT / "paper/evidence/association_pair_candidates_p194.csv"),
    }
    return {
        "prohibited_target_fields": sorted(PROHIBITED_TARGET_FIELDS),
        "p193_contains_prohibited_fields": sorted(source_columns["p193_dataset"] & PROHIBITED_TARGET_FIELDS),
        "p216_uses_prohibited_fields_as_targets": False,
        "p216_target_artifacts": {name: rel(path) for name, path in target_artifacts.items()},
        "note": "P216 reads P195 status and local semantic mask inventories only; it does not read P193 weak targets as labels.",
    }


def cuda_smoke(zip_path: Path, max_samples: int) -> dict[str, Any]:
    try:
        import numpy as np
        import torch
        import torch.nn as nn
        import torch.nn.functional as F
        from PIL import Image
    except Exception as exc:
        return {"requested": True, "status": "skipped_import_error", "error": repr(exc)}
    if not torch.cuda.is_available():
        return {"requested": True, "status": "skipped_cuda_unavailable", "torch_version": torch.__version__}
    x_tensors = []
    y_tensors = []
    with zipfile.ZipFile(zip_path) as archive:
        raw_names = [name for name in archive.namelist() if name.endswith("raw_labels_2d.json")]
        for raw_name in raw_names:
            if len(x_tensors) >= max_samples:
                break
            prefix = raw_name.rsplit("/", 1)[0]
            source_name = f"{prefix}/source_image.png"
            indexed_name = f"{prefix}/combined_indexedImage.png"
            if source_name not in archive.namelist() or indexed_name not in archive.namelist():
                continue
            payload = json.loads(archive.read(raw_name))
            dynamic_indices = set()
            for category, raw_entries in (payload.get("labelMapping") or {}).items():
                if category not in MOVABLE_OR_DYNAMIC_CATEGORIES:
                    continue
                for entry in label_mapping_entries(raw_entries):
                    if int(entry.get("numPixels") or 0) > 0 and entry.get("index") is not None:
                        dynamic_indices.add(int(entry["index"]))
            if not dynamic_indices:
                continue
            source = Image.open(BytesIO(archive.read(source_name))).convert("RGB").resize((160, 96))
            indexed = Image.open(BytesIO(archive.read(indexed_name))).convert("L").resize((160, 96), resample=Image.Resampling.NEAREST)
            x = torch.from_numpy(np.array(source)).permute(2, 0, 1).float() / 255.0
            mask_array = np.array(indexed)
            y = torch.from_numpy(np.isin(mask_array, sorted(dynamic_indices)).astype("int64"))
            x_tensors.append(x)
            y_tensors.append(y)
    if not x_tensors:
        return {"requested": True, "status": "failed_no_dynamic_samples"}
    device = torch.device("cuda")
    x_batch = torch.stack(x_tensors).to(device)
    y_batch = torch.stack(y_tensors).to(device)
    model = nn.Sequential(nn.Conv2d(3, 8, 3, padding=1), nn.ReLU(), nn.Conv2d(8, 2, 1)).to(device)
    logits = model(x_batch)
    loss = F.cross_entropy(logits, y_batch)
    loss.backward()
    return {
        "requested": True,
        "status": "pass",
        "torch_version": torch.__version__,
        "cuda_device": torch.cuda.get_device_name(0),
        "sample_count": len(x_tensors),
        "input_shape": list(x_batch.shape),
        "target_shape": list(y_batch.shape),
        "loss": float(loss.detach().cpu().item()),
    }


def build_recommendations(annotated: dict[str, Any], sequence_masks: dict[str, Any], sequence_zips: dict[str, Any]) -> list[dict[str, Any]]:
    paired = int(annotated.get("paired_source_indexed_mask_count") or 0)
    sequence_pairs = int(sequence_zips.get("left_rgb_greyscale_mask_pair_count") or 0)
    return [
        {
            "rank": 1,
            "route": "P216A dataset-provided semantic segmentation and binary dynamic/static mask training",
            "status": "immediately_executable_cuda_smoke" if paired else "blocked_missing_pairs",
            "target": "pixel-level semantic category masks from AnnotatedSemanticSet; optional binary movable/dynamic mask derived from TorWIC semantic categories",
            "why_valid": "The labels are dataset-provided segmentation masks and raw_labels_2d categories, not persistent-map admission or same-object labels.",
            "claim_allowed": "learned semantic segmentation or dynamic-object masking front-end for SLAM preprocessing",
            "claim_blocked": "learned persistent-map admission control or cross-session same-object association",
            "evidence": {
                "annotated_paired_source_indexed_masks": paired,
                "semantic_categories": annotated.get("category_count", 0),
            },
        },
        {
            "rank": 2,
            "route": "P216B SLAM front-end dynamic object masking from dataset masks",
            "status": "executable_preprocessing_path",
            "target": "mask RGB/depth features for movable categories before DROID/ORB front-end evaluation",
            "why_valid": "Uses local segmentation masks as masks, not as admission ground truth.",
            "claim_allowed": "front-end masking ablation using semantic masks and downstream ATE/RPE/feature metrics",
            "claim_blocked": "admission-control learning",
            "evidence": {"sequence_left_rgb_greyscale_mask_pairs": sequence_pairs},
        },
        {
            "rank": 3,
            "route": "P216C self-supervised temporal consistency representation learning",
            "status": "valid_but_second_order",
            "target": "photometric/depth/semantic consistency over adjacent frames, evaluated as representation or mask-consistency pretraining",
            "why_valid": "No human admission labels are required, but it still needs a clean downstream evaluation protocol.",
            "claim_allowed": "self-supervised pretraining or consistency regularization",
            "claim_blocked": "admission decisions without independent labels",
            "evidence": {"complete_extracted_left_mask_sequences": sequence_masks.get("sequence_count_with_complete_left_greyscale_masks", 0)},
        },
        {
            "rank": 4,
            "route": "P216D object-level persistent-map admission learning",
            "status": "blocked",
            "target": "human_admit_label and human_same_object_label",
            "why_valid": "Requires independent labels that do not exist locally yet.",
            "claim_allowed": "none until P195 unblocks",
            "claim_blocked": "learned admission control",
            "evidence": {"p195_required": "human labels remain blank"},
        },
    ]


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# P216 No-Manual Training Redirect",
        "",
        f"**Status:** {payload['status']}",
        f"**Recommendation:** {payload['recommendation']}",
        "",
        "## Direct Answer",
        "",
        "The P206-P215 path drifted away from model training. It is useful evidence governance, but it cannot by itself train a model. Manual labels were requested because P195 correctly requires independent admission and same-object ground truth before any learned admission-control claim. Those labels remain absent, so P195 must stay blocked.",
        "",
        "The next scientifically valid no-manual route is not admission learning. It is dataset-mask-supervised semantic segmentation or binary dynamic/static mask training from TorWIC/AnnotatedSemanticSet masks, followed by SLAM front-end dynamic masking evaluation.",
        "",
        "## What Can Be Trained Now",
        "",
    ]
    for item in payload["recommendation_ranking"]:
        lines.extend(
            [
                f"### Rank {item['rank']}: {item['route']}",
                "",
                f"- Status: `{item['status']}`",
                f"- Target: {item['target']}",
                f"- Validity: {item['why_valid']}",
                f"- Claim allowed: {item['claim_allowed']}",
                f"- Claim blocked: {item['claim_blocked']}",
                "",
            ]
        )
    annotated = payload["local_data_inventory"]["annotated_semantic_set"]
    sequence = payload["local_data_inventory"]["sequence_zips"]
    lines.extend(
        [
            "## Local Evidence",
            "",
            f"- AnnotatedSemanticSet raw label JSON files: {annotated.get('raw_label_json_count', 0)}",
            f"- Paired source image and indexed mask samples: {annotated.get('paired_source_indexed_mask_count', 0)}",
            f"- Semantic categories with positive pixels: {annotated.get('category_count', 0)}",
            f"- Sequence zip left RGB/greyscale mask pairs: {sequence.get('left_rgb_greyscale_mask_pair_count', 0)}",
            f"- CUDA smoke: `{payload['cuda_smoke'].get('status')}`",
            "",
            "## P216 Implementation Plan",
            "",
            "1. Build `TorchDataset` loaders for `AnnotatedSemanticSet_Finetuning.zip` source images and `combined_indexedImage.png` masks.",
            "2. Train a compact segmentation baseline with class weights and leave-root/frame-id splits; report mIoU, dynamic-binary IoU, per-category IoU, and mask coverage.",
            "3. Collapse movable categories into a binary dynamic/non-static mask head for SLAM front-end masking.",
            "4. Export masks into the existing raw-vs-masked DROID/ORB evaluation path and report only front-end masking/trajectory effects.",
            "5. Keep P195 admission/same-object learning blocked until independent labels exist.",
            "",
            "## Leakage Guard",
            "",
            f"- P195 status: `{payload['p195']['status']}`",
            f"- Human labels blank: `{payload['p195']['labels_blank']}`",
            "- P216 does not use `target_admit`, `current_weak_label`, `selection_v5`, P193 labels, or model predictions as targets.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cuda-smoke", action="store_true", help="Run a two-sample CUDA segmentation smoke test.")
    parser.add_argument("--smoke-samples", type=int, default=2)
    parser.add_argument("--output-json", default="paper/evidence/no_manual_training_redirect_p216.json")
    parser.add_argument("--output-md", default="paper/export/no_manual_training_redirect_p216.md")
    args = parser.parse_args()

    annotated = inspect_annotated_zip(ANNOTATED_ZIP)
    sequence_masks = inspect_sequence_masks(DATA_ROOT)
    sequence_zips = inspect_sequence_zips(DATA_ROOT)
    p195_raw = load_json(P195_JSON)
    p195 = {
        "status": p195_raw.get("status", "UNKNOWN"),
        "labels_blank": (
            p195_raw.get("label_audit", {}).get("boundary", {}).get("valid") == 0
            and p195_raw.get("label_audit", {}).get("pairs", {}).get("valid") == 0
        ),
        "label_audit": p195_raw.get("label_audit", {}),
        "decision": p195_raw.get("decision", ""),
    }
    smoke = cuda_smoke(ANNOTATED_ZIP, max(1, args.smoke_samples)) if args.cuda_smoke else {"requested": False, "status": "not_run"}
    recommendations = build_recommendations(annotated, sequence_masks, sequence_zips)
    payload = {
        "status": "REDIRECT_READY_NO_MANUAL_MASK_TRAINING_P195_BLOCKED",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "recommendation": "Start P216A: train semantic segmentation / binary dynamic-mask front-end from dataset-provided TorWIC masks; do not train admission control.",
        "previous_path_assessment": {
            "p206_p215_drifted_from_training": True,
            "why": "P206-P215 built evidence packets, QA, notes governance, release checks, and appendix packaging. That is valuable governance but it does not create a supervised training target.",
            "why_manual_labels_were_requested": "P195 admission-control learning needs independent human_admit_label and human_same_object_label because existing P193 weak/proxy/model fields are not ground truth.",
        },
        "local_data_inventory": {
            "annotated_semantic_set": annotated,
            "extracted_sequence_masks": sequence_masks,
            "sequence_zips": sequence_zips,
        },
        "recommendation_ranking": recommendations,
        "p216_plan": {
            "phase_id": "P216",
            "primary_deliverable": "CUDA semantic segmentation and binary dynamic-mask training smoke using AnnotatedSemanticSet masks",
            "allowed_targets": [
                "semantic class pixels from raw_labels_2d/combined_indexedImage",
                "binary movable/dynamic mask derived from dataset semantic categories",
                "SLAM front-end raw-vs-masked evaluation metrics",
            ],
            "blocked_targets": [
                "persistent-map admission labels",
                "cross-session same-object labels",
                "P193 target_admit/current_weak_label/selection_v5/model predictions as ground truth",
            ],
        },
        "claim_boundary": "P216 may claim dataset-mask-supervised semantic/dynamic mask training and SLAM front-end masking evaluation only. It must not claim learned admission control while P195 is BLOCKED.",
        "leakage_guard": leakage_guard(),
        "p195": p195,
        "cuda_smoke": smoke,
        "outputs": {"json": args.output_json, "markdown": args.output_md},
        "verification": {
            "p195_remains_blocked": p195["status"] == "BLOCKED",
            "human_labels_remain_blank": bool(p195["labels_blank"]),
            "no_prohibited_targets_used": True,
            "cuda_smoke_status": smoke.get("status"),
        },
    }
    write_json(ROOT / args.output_json, payload)
    write_markdown(ROOT / args.output_md, payload)
    print(json.dumps({"status": payload["status"], "cuda_smoke": smoke.get("status"), "p195": p195["status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
