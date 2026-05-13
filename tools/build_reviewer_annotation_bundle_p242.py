#!/usr/bin/env python3
"""Build the P242 reviewer-friendly annotation bundle from P239 rows."""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
P239_CSV = ROOT / "paper/evidence/independent_dynamic_label_packet_p239.csv"
P239_JSON = ROOT / "paper/evidence/independent_dynamic_label_packet_p239.json"
REVIEW_TEMPLATE_CSV = ROOT / "paper/evidence/independent_dynamic_label_review_template_p242.csv"
REVIEW_SHEET_HTML = ROOT / "paper/export/independent_dynamic_label_review_sheet_p242.html"
REVIEW_BUNDLE_MD = ROOT / "paper/export/independent_dynamic_label_review_bundle_p242.md"
AUDIT_JSON = ROOT / "paper/evidence/independent_dynamic_label_review_audit_p242.json"
AUDIT_TOOL = ROOT / "tools/audit_independent_dynamic_labels_p242.py"

REVIEW_FIELDS = [
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
    "model_context_note",
    "admission_label_visibility",
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

EMPTY_REVIEW_FIELDS = [
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


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def rel_from_export(path_text: str) -> str:
    path = ROOT / path_text
    return os.path.relpath(path, ROOT / "paper/export")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_p239(rows: list[dict[str, str]], p239: dict[str, Any]) -> None:
    if len(rows) != 18:
        raise ValueError(f"expected 18 P239 rows, found {len(rows)}")
    if p239.get("p195_status_after_p239") != "BLOCKED":
        raise ValueError("P239 evidence does not report P195 as BLOCKED")
    label_fields = p239.get("packet_summary", {}).get("label_fields", [])
    for field in label_fields:
        non_empty = [row["packet_id"] for row in rows if row.get(field, "").strip()]
        if non_empty:
            raise ValueError(f"P239 label field {field} is already non-empty for {non_empty[:3]}")
    for row in rows:
        for field in ["raw_image", "probability_overlay", "soft_mask_overlay", "region_crop"]:
            if not (ROOT / row[field]).exists():
                raise FileNotFoundError(f"{row['packet_id']} missing {field}: {row[field]}")


def build_review_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    review_rows = []
    for row in rows:
        item = {field: row.get(field, "") for field in REVIEW_FIELDS}
        for field in EMPTY_REVIEW_FIELDS:
            item[field] = ""
        item["label_confidence"] = ""
        review_rows.append(item)
    return review_rows


def write_html(path: Path, rows: list[dict[str, str]]) -> None:
    cards = []
    for row in rows:
        fields = {
            "packet_id": row["packet_id"],
            "window": row["window_id"],
            "source_frame_index": row["source_frame_index"],
            "sequence": row["sequence_label"],
            "selection": row["selection_reason"],
        }
        image_cells = []
        for label, field in [
            ("Raw", "raw_image"),
            ("Probability context", "probability_overlay"),
            ("Soft-mask context", "soft_mask_overlay"),
            ("Region crop", "region_crop"),
        ]:
            src = html.escape(rel_from_export(row[field]))
            image_cells.append(f"<figure><img src=\"{src}\" alt=\"{html.escape(label)}\"><figcaption>{html.escape(label)}</figcaption></figure>")
        empty_fields = "".join(
            f"<li><code>{html.escape(field)}</code>: __________</li>" for field in EMPTY_REVIEW_FIELDS
        )
        meta = "".join(f"<dt>{html.escape(k)}</dt><dd>{html.escape(str(v))}</dd>" for k, v in fields.items())
        cards.append(
            "<section class=\"sample\">"
            f"<h2>{html.escape(row['packet_id'])}</h2>"
            f"<dl>{meta}</dl>"
            f"<div class=\"images\">{''.join(image_cells)}</div>"
            "<div class=\"fields\"><h3>Reviewer fields</h3>"
            f"<ul>{empty_fields}</ul></div>"
            "</section>"
        )
    text = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>P242 Independent Dynamic-Label Review Sheet</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 24px; color: #1f2933; background: #f7f8fa; }}
    header {{ max-width: 1100px; margin: 0 auto 24px; }}
    h1 {{ margin-bottom: 8px; }}
    .note {{ background: #fff; border-left: 4px solid #b42318; padding: 12px 16px; }}
    .sample {{ max-width: 1100px; margin: 0 auto 24px; background: #fff; border: 1px solid #d8dee4; padding: 16px; }}
    .sample h2 {{ margin-top: 0; font-size: 18px; }}
    dl {{ display: grid; grid-template-columns: 180px 1fr; gap: 6px 12px; }}
    dt {{ font-weight: 700; }}
    dd {{ margin: 0; }}
    .images {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 14px; }}
    figure {{ margin: 0; border: 1px solid #d8dee4; background: #fdfdfd; padding: 8px; }}
    img {{ width: 100%; height: auto; display: block; }}
    figcaption {{ margin-top: 6px; font-size: 13px; color: #4b5563; }}
    .fields {{ margin-top: 12px; }}
    code {{ background: #eef2f7; padding: 1px 4px; }}
    @media (max-width: 900px) {{ .images {{ grid-template-columns: repeat(2, 1fr); }} dl {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <header>
    <h1>P242 Independent Dynamic-Label Review Sheet</h1>
    <p class="note">Use raw images as primary evidence. Probability and soft-mask images are optional context only, not ground truth. Do not consult admission labels. This sheet has no independent labels until a reviewer fills the CSV.</p>
  </header>
  {''.join(cards)}
</body>
</html>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_markdown(path: Path, rows: list[dict[str, str]], p239: dict[str, Any]) -> None:
    by_window = Counter(row["window_id"] for row in rows)
    text = f"""# P242 Independent Dynamic-Label Review Bundle

## Purpose

P242 converts the P239 mini packet into a reviewer-friendly offline annotation bundle. It reduces the manual review cost, but it does not collect labels, infer labels, validate the soft-boundary module, or unblock P195.

## Files

- Reviewer CSV template: `{rel(REVIEW_TEMPLATE_CSV)}`
- Offline HTML review sheet: `{rel(REVIEW_SHEET_HTML)}`
- Current audit JSON: `{rel(AUDIT_JSON)}`
- Source P239 CSV: `{rel(P239_CSV)}`
- Source P239 JSON: `{rel(P239_JSON)}`

## Current Status

- Rows: {len(rows)}
- Windows: {", ".join(f"{key}={value}" for key, value in sorted(by_window.items()))}
- P239 status after packet creation: `{p239.get("p195_status_after_p239")}`
- P242 audit status: `no_labels_collected`
- P195 status: `BLOCKED`

## How To Fill The CSV

Fill only the reviewer columns in `{rel(REVIEW_TEMPLATE_CSV)}`:

- `dynamic_region_present`: `yes`, `no`, or `unknown`.
- `dynamic_region_type`: `person`, `forklift`, `cart`, `pallet_jack`, `movable_object`, `other`, `none`, or `unknown`.
- `boundary_quality`: `good`, `partial`, `poor`, or `unknown`.
- `false_positive_region`: `yes`, `no`, or `unknown`.
- `false_negative_region`: `yes`, `no`, or `unknown`.
- `label_confidence`: `high`, `medium`, `low`, or `unknown`.
- `reviewer_id`, `reviewed_at_utc`, and `reviewer_notes`: reviewer provenance and comments.

Use the raw image as primary evidence. The probability overlay, soft-mask overlay, and crop are reviewer context only. They must not be copied as labels or treated as ground truth.

## Independence Rules

Do not inspect admission labels, weak labels, P196/P197 review labels, model probabilities, or model masks as a source of truth. The HTML and overlays are meant to make the visual task easier, not to define the answer.

Labels become independent only after a human or external reviewer fills non-empty fields and the completed CSV passes a follow-up audit. Until then, P195 remains BLOCKED and this bundle must not be cited as independent validation.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_audit(review_csv: Path, audit_json: Path) -> None:
    subprocess.run(
        [sys.executable, str(AUDIT_TOOL), "--review-csv", str(review_csv), "--audit-json", str(audit_json)],
        cwd=ROOT,
        check=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p239-csv", type=Path, default=P239_CSV)
    parser.add_argument("--p239-json", type=Path, default=P239_JSON)
    parser.add_argument("--review-template-csv", type=Path, default=REVIEW_TEMPLATE_CSV)
    parser.add_argument("--review-sheet-html", type=Path, default=REVIEW_SHEET_HTML)
    parser.add_argument("--review-bundle-md", type=Path, default=REVIEW_BUNDLE_MD)
    parser.add_argument("--audit-json", type=Path, default=AUDIT_JSON)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = read_csv(args.p239_csv)
    p239 = read_json(args.p239_json)
    validate_p239(rows, p239)
    review_rows = build_review_rows(rows)
    write_csv(args.review_template_csv, review_rows, REVIEW_FIELDS)
    write_html(args.review_sheet_html, review_rows)
    run_audit(args.review_template_csv, args.audit_json)
    write_markdown(args.review_bundle_md, review_rows, p239)
    print(
        "Built P242 reviewer annotation bundle: "
        f"{len(review_rows)} rows, labels blank, P195 BLOCKED at {now_utc()}."
    )


if __name__ == "__main__":
    main()
