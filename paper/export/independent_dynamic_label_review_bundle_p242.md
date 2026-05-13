# P242 Independent Dynamic-Label Review Bundle

## Purpose

P242 converts the P239 mini packet into a reviewer-friendly offline annotation bundle. It reduces the manual review cost, but it does not collect labels, infer labels, validate the soft-boundary module, or unblock P195.

## Files

- Reviewer CSV template: `paper/evidence/independent_dynamic_label_review_template_p242.csv`
- Offline HTML review sheet: `paper/export/independent_dynamic_label_review_sheet_p242.html`
- Current audit JSON: `paper/evidence/independent_dynamic_label_review_audit_p242.json`
- Source P239 CSV: `paper/evidence/independent_dynamic_label_packet_p239.csv`
- Source P239 JSON: `paper/evidence/independent_dynamic_label_packet_p239.json`

## Current Status

- Rows: 18
- Windows: aisle_ccw_0240_0299=6, aisle_cw_0240_0299=6, aisle_cw_0840_0899=6
- P239 status after packet creation: `BLOCKED`
- P242 audit status: `no_labels_collected`
- P195 status: `BLOCKED`

## How To Fill The CSV

Fill only the reviewer columns in `paper/evidence/independent_dynamic_label_review_template_p242.csv`:

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
