#!/usr/bin/env python3
"""Audit the P242 independent dynamic-label reviewer template.

The audit is intentionally conservative. Blank labels are allowed for a packet
that has not yet been reviewed, but they do not unblock P195.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REVIEW_CSV = ROOT / "paper/evidence/independent_dynamic_label_review_template_p242.csv"
DEFAULT_AUDIT_JSON = ROOT / "paper/evidence/independent_dynamic_label_review_audit_p242.json"

LABEL_FIELDS = [
    "dynamic_region_present",
    "dynamic_region_type",
    "boundary_quality",
    "false_positive_region",
    "false_negative_region",
    "label_confidence",
    "reviewer_id",
    "reviewed_at_utc",
    "reviewer_notes",
]

CONTROLLED_VALUES = {
    "dynamic_region_present": {"yes", "no", "unknown"},
    "dynamic_region_type": {
        "person",
        "forklift",
        "cart",
        "pallet_jack",
        "movable_object",
        "other",
        "none",
        "unknown",
    },
    "boundary_quality": {"good", "partial", "poor", "unknown"},
    "false_positive_region": {"yes", "no", "unknown"},
    "false_negative_region": {"yes", "no", "unknown"},
    "label_confidence": {"high", "medium", "low", "unknown"},
}


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def audit_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    missing_fields = [field for field in LABEL_FIELDS if rows and field not in rows[0]]
    label_non_empty_counts: dict[str, int] = {}
    invalid_values: list[dict[str, str]] = []
    reviewed_rows = 0
    complete_review_rows = 0

    for row in rows:
        non_empty_label_fields = [field for field in LABEL_FIELDS if row.get(field, "").strip()]
        if non_empty_label_fields:
            reviewed_rows += 1
        required_non_empty = [
            row.get("dynamic_region_present", "").strip(),
            row.get("boundary_quality", "").strip(),
            row.get("label_confidence", "").strip(),
            row.get("reviewer_id", "").strip(),
            row.get("reviewed_at_utc", "").strip(),
        ]
        if all(required_non_empty):
            complete_review_rows += 1
        for field in LABEL_FIELDS:
            value = row.get(field, "").strip()
            label_non_empty_counts[field] = label_non_empty_counts.get(field, 0) + int(bool(value))
            allowed = CONTROLLED_VALUES.get(field)
            if value and allowed and value.lower() not in allowed:
                invalid_values.append(
                    {
                        "packet_id": row.get("packet_id", ""),
                        "field": field,
                        "value": value,
                        "allowed_values": ",".join(sorted(allowed)),
                    }
                )

    row_count = len(rows)
    image_path_counts = {}
    missing_image_paths = []
    for field in ["raw_image", "probability_overlay", "soft_mask_overlay", "region_crop"]:
        existing = 0
        for row in rows:
            path = ROOT / row.get(field, "")
            if path.exists():
                existing += 1
            else:
                missing_image_paths.append({"packet_id": row.get("packet_id", ""), "field": field, "path": row.get(field, "")})
        image_path_counts[field] = {"existing": existing, "missing": row_count - existing}

    labels_collected = reviewed_rows > 0 and not invalid_values and not missing_fields
    status = "labels_ready_for_audit" if labels_collected else "no_labels_collected"
    return {
        "status": status,
        "row_count": row_count,
        "by_window": dict(Counter(row.get("window_id", "") for row in rows)),
        "missing_required_fields": missing_fields,
        "label_non_empty_counts": label_non_empty_counts,
        "reviewed_rows": reviewed_rows,
        "complete_review_rows": complete_review_rows,
        "invalid_values": invalid_values,
        "image_path_counts": image_path_counts,
        "missing_image_paths": missing_image_paths,
        "labels_collected": labels_collected,
        "p195_status": "BLOCKED",
        "p195_unblock_condition": (
            "P195 remains BLOCKED until non-empty, valid reviewer labels exist and are audited "
            "for coverage, conflicts, and independence."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-csv", type=Path, default=DEFAULT_REVIEW_CSV)
    parser.add_argument("--audit-json", type=Path, default=DEFAULT_AUDIT_JSON)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = read_csv(args.review_csv)
    payload = {
        "phase": "P242-independent-dynamic-label-review-audit",
        "generated_at_utc": now_utc(),
        "inputs": {"review_csv": rel(args.review_csv)},
        "outputs": {"audit_json": rel(args.audit_json)},
        "claim_boundary": (
            "This audit only checks whether reviewer labels are present and syntactically valid. "
            "It does not infer labels or validate the soft-boundary module."
        ),
        **audit_rows(rows),
    }
    write_json(args.audit_json, payload)
    print(f"P242 audit status: {payload['status']}; P195 {payload['p195_status']}; rows={payload['row_count']}")


if __name__ == "__main__":
    main()
