# P239 Independent Dynamic-Label Mini-Packet Protocol

## Purpose

This protocol supports a small independent review pass over dynamic regions in P235/P237 soft-boundary windows. The packet is designed to reduce reviewer cost while preserving the claim boundary: it prepares review material only and does not create independent labels by itself.

## Packet Scope

- Packet CSV: `paper/evidence/independent_dynamic_label_packet_p239.csv`
- Local visual packet root: `outputs/independent_dynamic_label_packet_p239`
- Samples: 18
- Windows: aisle_ccw_0240_0299, aisle_cw_0240_0299, aisle_cw_0840_0899
- Selected soft-boundary context variant: `meanfill035_feather5_thr060_cap012_min256`

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
