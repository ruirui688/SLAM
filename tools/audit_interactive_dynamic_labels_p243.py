#!/usr/bin/env python3
"""Audit CSV exports from the P243 interactive annotation web tool."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "paper/evidence/independent_dynamic_label_review_template_p242.csv"

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
    "dynamic_region_present": {"yes", "no", "uncertain"},
    "dynamic_region_type": {
        "moving_object",
        "static_structure",
        "reflection",
        "shadow",
        "unknown",
        "not_applicable",
    },
    "boundary_quality": {"good", "acceptable", "poor", "not_applicable"},
    "false_positive_region": {"yes", "no", "uncertain"},
    "false_negative_region": {"yes", "no", "uncertain"},
    "label_confidence": {"high", "medium", "low"},
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def audit(rows: list[dict[str, str]], input_csv: Path) -> dict[str, Any]:
    missing_fields = [field for field in LABEL_FIELDS if rows and field not in rows[0]]
    invalid_values = []
    non_empty_counts = Counter()
    reviewed_rows = 0
    complete_rows = 0
    for row in rows:
        has_any_label = False
        for field in LABEL_FIELDS:
            value = row.get(field, "").strip()
            if value:
                has_any_label = True
                non_empty_counts[field] += 1
            allowed = CONTROLLED_VALUES.get(field)
            if value and allowed and value not in allowed:
                invalid_values.append(
                    {
                        "packet_id": row.get("packet_id", ""),
                        "field": field,
                        "value": value,
                        "allowed_values": sorted(allowed),
                    }
                )
        if has_any_label:
            reviewed_rows += 1
        required = ["dynamic_region_present", "boundary_quality", "label_confidence", "reviewer_id", "reviewed_at_utc"]
        if all(row.get(field, "").strip() for field in required):
            complete_rows += 1
    status = "labels_ready_for_independence_audit" if complete_rows and not invalid_values and not missing_fields else "no_auditable_labels"
    if reviewed_rows == 0:
        status = "no_labels_collected"
    return {
        "phase": "P243-interactive-dynamic-label-export-audit",
        "generated_at_utc": now_utc(),
        "input_csv": str(input_csv),
        "status": status,
        "row_count": len(rows),
        "by_window": dict(Counter(row.get("window_id", "") for row in rows)),
        "reviewed_rows": reviewed_rows,
        "complete_rows": complete_rows,
        "label_non_empty_counts": dict(non_empty_counts),
        "missing_fields": missing_fields,
        "invalid_values": invalid_values,
        "p195_status": "BLOCKED",
        "claim_boundary": (
            "This audit checks exported reviewer labels for presence and syntax only. "
            "It does not infer labels or provide independent validation; P195 remains BLOCKED "
            "until non-empty labels pass coverage, conflict, and independence review."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv", nargs="?", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--json", type=Path, help="optional output JSON path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = audit(read_csv(args.input_csv), args.input_csv)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
