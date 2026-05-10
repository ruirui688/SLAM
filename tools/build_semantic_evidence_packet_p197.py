#!/usr/bin/env python3
"""Build P197 semantic evidence enrichment for the P196 review packet.

P197 is reviewer evidence enrichment only.  It links P196 review rows to raw
TorWIC semantic mask files when the session/date/route/frame mapping is
unambiguous, and it records the separate AnnotatedSemanticSet ontology audit.
It never fills or infers human labels.
"""

from __future__ import annotations

import csv
import json
import re
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data/TorWIC_SLAM_Dataset"

BOUNDARY_REVIEW_CSV = ROOT / "paper/evidence/admission_boundary_label_sheet_p196_review.csv"
PAIR_REVIEW_CSV = ROOT / "paper/evidence/association_pair_candidates_p196_review.csv"
PACKET_JSON = ROOT / "paper/evidence/semantic_evidence_packet_p197.json"
PROTOCOL_MD = ROOT / "paper/export/semantic_evidence_protocol_p197.md"
BOUNDARY_SEMANTIC_CSV = ROOT / "paper/evidence/admission_boundary_label_sheet_p197_semantic_review.csv"
PAIR_SEMANTIC_CSV = ROOT / "paper/evidence/association_pair_candidates_p197_semantic_review.csv"

ANNOTATED_ZIP = DATA_ROOT / "Oct. 12, 2022/AnnotatedSemanticSet_Finetuning.zip"

STATIC_LIKE_CATEGORIES = {
    "wall_fence_pillar",
    "rack_shelf",
    "fixed_machinery",
    "misc_static_feature",
    "ceiling",
}
DYNAMIC_OR_NON_STATIC_LIKE_CATEGORIES = {
    "fork_truck",
    "person",
    "cart_pallet_jack",
    "pylon_cone",
    "misc_dynamic_feature",
    "misc_non_static_feature",
}

CANONICAL_TO_SEMANTIC_HINTS = {
    "forklift": ["fork_truck"],
    "fork": ["fork_truck"],
    "rack forklift": ["fork_truck", "rack_shelf"],
    "warehouse rack": ["rack_shelf"],
    "rack": ["rack_shelf"],
    "barrier": ["misc_static_feature", "pylon_cone"],
    "work table": ["misc_static_feature", "fixed_machinery"],
    "work": ["misc_static_feature", "fixed_machinery"],
}

DATE_BY_TOKEN = {
    "2022-06-15": "Jun. 15, 2022",
    "2022-06-23": "Jun. 23, 2022",
    "2022-10-12": "Oct. 12, 2022",
}


@dataclass(frozen=True)
class TorwicZipIndex:
    zip_path: Path
    internal_names: frozenset[str]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def session_to_date_route(session_id: str) -> tuple[str | None, str | None]:
    date_match = re.search(r"2022-\d\d-\d\d", session_id)
    if not date_match:
        return None, None
    date_token = date_match.group(0)
    date_dir = DATE_BY_TOKEN.get(date_token)
    if not date_dir:
        return None, None
    route = session_id.split(date_token + "__", 1)[-1]
    return date_dir, route


def build_torwic_zip_index() -> dict[tuple[str, str], TorwicZipIndex]:
    index: dict[tuple[str, str], TorwicZipIndex] = {}
    for zip_path in sorted(DATA_ROOT.glob("*/*.zip")):
        if zip_path.name == ANNOTATED_ZIP.name:
            continue
        date_dir = zip_path.parent.name
        route = zip_path.stem
        with zipfile.ZipFile(zip_path) as archive:
            index[(date_dir, route)] = TorwicZipIndex(
                zip_path=zip_path,
                internal_names=frozenset(archive.namelist()),
            )
    return index


def add_zip_member(paths: list[str], index: TorwicZipIndex, member: str) -> None:
    if member in index.internal_names:
        paths.append(f"{index.zip_path.relative_to(ROOT)}::{member}")


def torwic_segmentation_evidence(
    session_id: str,
    frame_index: str,
    zip_index: dict[tuple[str, str], TorwicZipIndex],
) -> dict[str, Any]:
    date_dir, route = session_to_date_route(session_id)
    if not date_dir or not route:
        return {
            "mapping_status": "unmatched",
            "mapping_reason": "session_id_does_not_contain_supported_torwic_date_route",
        }
    index = zip_index.get((date_dir, route))
    if index is None:
        return {
            "mapping_status": "unmatched",
            "mapping_reason": "torwic_session_zip_not_found",
            "date_dir": date_dir,
            "route": route,
        }
    try:
        frame = f"{int(frame_index):06d}"
    except (TypeError, ValueError):
        return {
            "mapping_status": "unmatched",
            "mapping_reason": "invalid_or_missing_frame_index",
            "date_dir": date_dir,
            "route": route,
        }

    source_paths: list[str] = []
    for subdir in (
        "segmentation_color_left",
        "segmentation_greyscale_left",
        "segmentation_color_right",
        "segmentation_greyscale_right",
    ):
        add_zip_member(source_paths, index, f"{route}/{subdir}/{frame}.png")

    if not source_paths:
        return {
            "mapping_status": "unmatched",
            "mapping_reason": "frame_segmentation_members_not_found_in_torwic_zip",
            "date_dir": date_dir,
            "route": route,
            "frame": frame,
        }

    reliable = any("/segmentation_color_left/" in p for p in source_paths) and any(
        "/segmentation_greyscale_left/" in p for p in source_paths
    )
    return {
        "mapping_status": "matched_torwic_segmentation" if reliable else "partial_torwic_segmentation",
        "mapping_reason": "session_date_route_frame_member_match",
        "date_dir": date_dir,
        "route": route,
        "frame": frame,
        "source_semantic_paths": source_paths,
    }


def flatten_label_mapping(mapping: Any) -> list[dict[str, Any]]:
    if mapping is None:
        return []
    if isinstance(mapping, list):
        return [item for item in mapping if isinstance(item, dict)]
    if isinstance(mapping, dict):
        return [mapping]
    return []


def audit_annotated_semantic_set() -> dict[str, Any]:
    if not ANNOTATED_ZIP.exists():
        return {
            "zip_path": str(ANNOTATED_ZIP.relative_to(ROOT)),
            "available": False,
            "mapping_status_for_p196_rows": "unmatched",
            "mapping_reason": "zip_not_found",
        }

    category_counter: Counter[str] = Counter()
    static_counter: Counter[str] = Counter()
    dynamic_counter: Counter[str] = Counter()
    raw_label_files = 0
    frame_dirs: set[str] = set()
    sample_entries: list[dict[str, Any]] = []

    with zipfile.ZipFile(ANNOTATED_ZIP) as archive:
        names = archive.namelist()
        raw_names = sorted(name for name in names if name.endswith("/raw_labels_2d.json"))
        raw_label_files = len(raw_names)
        for name in raw_names:
            parts = name.split("/")
            if len(parts) >= 3:
                frame_dirs.add(parts[1])
            payload = json.loads(archive.read(name))
            label_mapping = payload.get("labelMapping", {})
            present_categories = []
            for category, mapping in label_mapping.items():
                entries = flatten_label_mapping(mapping)
                pixels = sum(int(entry.get("numPixels") or 0) for entry in entries)
                if pixels <= 0:
                    continue
                category_counter[category] += 1
                present_categories.append(category)
                if category in STATIC_LIKE_CATEGORIES:
                    static_counter[category] += 1
                if category in DYNAMIC_OR_NON_STATIC_LIKE_CATEGORIES:
                    dynamic_counter[category] += 1
            if len(sample_entries) < 5:
                sample_entries.append(
                    {
                        "raw_label_path": name,
                        "present_categories": sorted(present_categories),
                    }
                )

    return {
        "zip_path": str(ANNOTATED_ZIP.relative_to(ROOT)),
        "available": True,
        "raw_labels_2d_files": raw_label_files,
        "labelled_frame_directories": len(frame_dirs),
        "categories_with_positive_pixels": dict(sorted(category_counter.items())),
        "static_like_categories": dict(sorted(static_counter.items())),
        "dynamic_or_non_static_like_categories": dict(sorted(dynamic_counter.items())),
        "sample_entries": sample_entries,
        "mapping_status_for_p196_rows": "unmatched",
        "mapping_reason": (
            "AnnotatedSemanticSet entries expose frame-directory ids and image_N raw label folders, "
            "but no route/session identity or reviewed-object identity that can be joined safely to P196 rows."
        ),
    }


def semantic_hint_for_row(canonical_label: str) -> tuple[str, str]:
    hints = CANONICAL_TO_SEMANTIC_HINTS.get(canonical_label.strip().lower(), [])
    if not hints:
        return "no_direct_ontology_hint", ""
    classes = []
    for hint in hints:
        if hint in STATIC_LIKE_CATEGORIES:
            classes.append("static_like")
        elif hint in DYNAMIC_OR_NON_STATIC_LIKE_CATEGORIES:
            classes.append("dynamic_or_non_static_like")
        else:
            classes.append("other")
    unique_classes = sorted(set(classes))
    return "+".join(unique_classes), ";".join(hints)


def blank_human_audit(rows: list[dict[str, str]], columns: list[str]) -> dict[str, dict[str, int]]:
    audit: dict[str, dict[str, int]] = {}
    for column in columns:
        counts = Counter("blank" if str(row.get(column, "")).strip() == "" else "nonblank" for row in rows)
        audit[column] = {"blank": counts["blank"], "nonblank": counts["nonblank"]}
    return audit


def enrich_boundary_rows(
    rows: list[dict[str, str]],
    zip_index: dict[tuple[str, str], TorwicZipIndex],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    enriched: list[dict[str, Any]] = []
    evidence_records: list[dict[str, Any]] = []
    for row in rows:
        evidence = torwic_segmentation_evidence(row.get("session_id", ""), row.get("frame_index", ""), zip_index)
        hint_class, hint_categories = semantic_hint_for_row(row.get("canonical_label", ""))
        source_paths = evidence.get("source_semantic_paths", [])
        item = dict(row)
        item.update(
            {
                "semantic_evidence_status": evidence["mapping_status"],
                "semantic_mapping_reason": evidence["mapping_reason"],
                "semantic_hint": hint_class,
                "semantic_hint_categories": hint_categories,
                "source_semantic_path": ";".join(source_paths),
                "semantic_review_note": (
                    "Auxiliary reviewer evidence only; do not copy semantic hints into human labels."
                ),
            }
        )
        enriched.append(item)
        evidence_records.append(
            {
                "row_type": "boundary",
                "review_id": row.get("review_id", ""),
                "sample_id": row.get("sample_id", ""),
                "session_id": row.get("session_id", ""),
                "frame_index": row.get("frame_index", ""),
                "canonical_label": row.get("canonical_label", ""),
                "mapping": evidence,
                "semantic_hint": hint_class,
                "semantic_hint_categories": hint_categories.split(";") if hint_categories else [],
            }
        )
    return enriched, evidence_records


def enrich_pair_rows(
    rows: list[dict[str, str]],
    zip_index: dict[tuple[str, str], TorwicZipIndex],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    enriched: list[dict[str, Any]] = []
    evidence_records: list[dict[str, Any]] = []
    for row in rows:
        frame_a = row.get("frame_id_a", "").rsplit("_", 1)[-1]
        frame_b = row.get("frame_id_b", "").rsplit("_", 1)[-1]
        evidence_a = torwic_segmentation_evidence(row.get("session_id_a", ""), frame_a, zip_index)
        evidence_b = torwic_segmentation_evidence(row.get("session_id_b", ""), frame_b, zip_index)
        hint_class, hint_categories = semantic_hint_for_row(row.get("canonical_label", ""))
        paths_a = evidence_a.get("source_semantic_paths", [])
        paths_b = evidence_b.get("source_semantic_paths", [])
        if evidence_a["mapping_status"].startswith("matched") and evidence_b["mapping_status"].startswith("matched"):
            status = "matched_torwic_segmentation_pair"
        elif evidence_a["mapping_status"] == "unmatched" or evidence_b["mapping_status"] == "unmatched":
            status = "unmatched"
        else:
            status = "partial_torwic_segmentation_pair"

        item = dict(row)
        item.update(
            {
                "semantic_evidence_status": status,
                "semantic_mapping_reason_a": evidence_a["mapping_reason"],
                "semantic_mapping_reason_b": evidence_b["mapping_reason"],
                "semantic_hint": hint_class,
                "semantic_hint_categories": hint_categories,
                "source_semantic_path_a": ";".join(paths_a),
                "source_semantic_path_b": ";".join(paths_b),
                "semantic_review_note": (
                    "Auxiliary reviewer evidence only; compare visual evidence and leave human labels blank until review."
                ),
            }
        )
        enriched.append(item)
        evidence_records.append(
            {
                "row_type": "pair",
                "pair_id": row.get("pair_id", ""),
                "sample_id_a": row.get("sample_id_a", ""),
                "sample_id_b": row.get("sample_id_b", ""),
                "canonical_label": row.get("canonical_label", ""),
                "mapping_a": evidence_a,
                "mapping_b": evidence_b,
                "pair_mapping_status": status,
                "semantic_hint": hint_class,
                "semantic_hint_categories": hint_categories.split(";") if hint_categories else [],
            }
        )
    return enriched, evidence_records


def status_counts(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts = Counter(str(record.get(key, "")) for record in records)
    return dict(sorted(counts.items()))


def make_protocol(packet: dict[str, Any]) -> str:
    boundary_counts = packet["summary"]["boundary_mapping_status_counts"]
    pair_counts = packet["summary"]["pair_mapping_status_counts"]
    annotated = packet["annotated_semantic_set_audit"]
    return f"""# P197 Semantic Evidence Protocol

**Status:** reviewer evidence enrichment only. P197 does not generate labels, train a model, or unblock P195.

## Boundary

- P195 remains blocked until real human labels are entered.
- `human_admit_label`, `human_same_object_label`, confidence, and notes columns are preserved from P196 and are not inferred by this script.
- Semantic categories are auxiliary evidence only. Reviewers must decide from visual/object evidence and may ignore semantic hints when ambiguous.
- No `selection_v5`, `current_weak_label`, `model_prediction`, or `rule_proxy_fields` values are used to create human labels.

## Raw Evidence Sources

- TorWIC session zips under `data/TorWIC_SLAM_Dataset/<date>/<route>.zip`.
- AnnotatedSemanticSet zip: `{annotated['zip_path']}`.

## Mapping Rules

- A P196 review row is mapped to TorWIC raw segmentation evidence only when its session id gives a supported TorWIC date/route and its frame id/index gives an existing zip member.
- The script records left color and greyscale segmentation masks when both exist; right masks are included when present.
- AnnotatedSemanticSet label mappings are audited as an ontology/source inventory, but row-level mapping is `unmatched` because the zip lacks route/session and object identity fields required for a safe join.
- If any required mapping information is absent, the row is marked `unmatched`; the script does not guess.

## Category Hint Sets

- Static-like hints: `{', '.join(sorted(STATIC_LIKE_CATEGORIES))}`.
- Dynamic/non-static-like hints: `{', '.join(sorted(DYNAMIC_OR_NON_STATIC_LIKE_CATEGORIES))}`.

## Mapping Summary

- Boundary rows: `{boundary_counts}`.
- Pair rows: `{pair_counts}`.
- AnnotatedSemanticSet raw label files: `{annotated.get('raw_labels_2d_files', 0)}`.

## Outputs

- `paper/evidence/semantic_evidence_packet_p197.json`
- `paper/evidence/admission_boundary_label_sheet_p197_semantic_review.csv`
- `paper/evidence/association_pair_candidates_p197_semantic_review.csv`

These CSVs append semantic evidence columns only. Human labels remain blank.
"""


def main() -> int:
    boundary_rows = read_csv(BOUNDARY_REVIEW_CSV)
    pair_rows = read_csv(PAIR_REVIEW_CSV)
    zip_index = build_torwic_zip_index()
    annotated_audit = audit_annotated_semantic_set()

    boundary_enriched, boundary_records = enrich_boundary_rows(boundary_rows, zip_index)
    pair_enriched, pair_records = enrich_pair_rows(pair_rows, zip_index)

    boundary_fields = list(boundary_rows[0].keys()) + [
        "semantic_evidence_status",
        "semantic_mapping_reason",
        "semantic_hint",
        "semantic_hint_categories",
        "source_semantic_path",
        "semantic_review_note",
    ]
    pair_fields = list(pair_rows[0].keys()) + [
        "semantic_evidence_status",
        "semantic_mapping_reason_a",
        "semantic_mapping_reason_b",
        "semantic_hint",
        "semantic_hint_categories",
        "source_semantic_path_a",
        "source_semantic_path_b",
        "semantic_review_note",
    ]

    write_csv(BOUNDARY_SEMANTIC_CSV, boundary_enriched, boundary_fields)
    write_csv(PAIR_SEMANTIC_CSV, pair_enriched, pair_fields)

    pair_status_records = [
        {"pair_mapping_status": record["pair_mapping_status"]} for record in pair_records
    ]
    packet = {
        "phase": "P197-semantic-evidence-reviewer-enrichment",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scientific_boundary": (
            "P197 links raw semantic evidence into the P196 review packet for reviewer convenience only. "
            "It does not infer human labels and does not release the P195 gate."
        ),
        "inputs": {
            "boundary_review_csv": str(BOUNDARY_REVIEW_CSV.relative_to(ROOT)),
            "pair_review_csv": str(PAIR_REVIEW_CSV.relative_to(ROOT)),
            "torwic_data_root": str(DATA_ROOT.relative_to(ROOT)),
            "annotated_semantic_zip": str(ANNOTATED_ZIP.relative_to(ROOT)),
        },
        "outputs": {
            "boundary_semantic_review_csv": str(BOUNDARY_SEMANTIC_CSV.relative_to(ROOT)),
            "pair_semantic_review_csv": str(PAIR_SEMANTIC_CSV.relative_to(ROOT)),
            "protocol_md": str(PROTOCOL_MD.relative_to(ROOT)),
        },
        "constraints": {
            "human_admit_label_inferred": False,
            "human_same_object_label_inferred": False,
            "semantic_category_converted_to_admission_label": False,
            "weak_label_or_model_proxy_used_for_human_labels": False,
            "training_or_download_performed": False,
        },
        "semantic_hint_sets": {
            "static_like": sorted(STATIC_LIKE_CATEGORIES),
            "dynamic_or_non_static_like": sorted(DYNAMIC_OR_NON_STATIC_LIKE_CATEGORIES),
        },
        "summary": {
            "boundary_rows": len(boundary_rows),
            "pair_rows": len(pair_rows),
            "boundary_mapping_status_counts": status_counts(
                [record["mapping"] for record in boundary_records], "mapping_status"
            ),
            "pair_mapping_status_counts": status_counts(pair_status_records, "pair_mapping_status"),
            "boundary_human_label_audit": blank_human_audit(
                boundary_enriched,
                ["human_admit_label", "human_label_confidence", "human_notes"],
            ),
            "pair_human_label_audit": blank_human_audit(
                pair_enriched,
                ["human_same_object_label", "human_pair_notes"],
            ),
        },
        "annotated_semantic_set_audit": annotated_audit,
        "boundary_evidence_records": boundary_records,
        "pair_evidence_records": pair_records,
    }

    write_json(PACKET_JSON, packet)
    PROTOCOL_MD.parent.mkdir(parents=True, exist_ok=True)
    PROTOCOL_MD.write_text(make_protocol(packet), encoding="utf-8")

    print(json.dumps(packet["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
