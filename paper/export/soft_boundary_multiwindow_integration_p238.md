# P238 Soft-Boundary Multi-Window Integration

Status: integrated into thick manuscripts and P238 lock.

## Scope

- Updated only thick manuscripts:
  - `paper/manuscript_en_thick.md`
  - `paper/manuscript_zh_thick.md`
- Left brief manuscripts untouched:
  - `paper/manuscript_en.md`
  - `paper/manuscript_zh.md`

## Integrated Story

P236 integrated the P235 candidate `meanfill035_feather5_thr060_cap012_min256` as a bounded soft-boundary frontend module that fixes the 840-899 hard-boundary ORB regression in smoke evidence.

P237 extends that candidate to four new short windows:

| Window | Sequence | ORB raw->soft | Total delta | DROID gate |
|---|---|---:|---:|---|
| `aisle_cw_0240_0299` | Oct. 12, 2022 Aisle_CW | 218 -> 41 | 0 | 16f neutral; 60f neutral |
| `aisle_cw_0660_0719` | Oct. 12, 2022 Aisle_CW | 41 -> 0 | 0 | 16f neutral |
| `aisle_cw_0960_1019` | Oct. 12, 2022 Aisle_CW | 27 -> 0 | 0 | 16f neutral |
| `aisle_ccw_0240_0299` | Oct. 12, 2022 Aisle_CCW | 81 -> 4 | 0 | 16f neutral |

Result status: `expanded_bounded_support`.

## Claim Boundary

Use as bounded frontend module evidence only. Do not claim:
- full benchmark support,
- navigation or planning gain,
- independent dynamic-label validation,
- learned persistent-map admission.

P195 remains BLOCKED.

## Files

- Lock JSON: `paper/evidence/thick_results_lock_p238.json`
- Lock report: `paper/export/thick_results_lock_p238.md`
- Integration summary: `paper/export/soft_boundary_multiwindow_integration_p238.md`
- P237 evidence: `paper/evidence/soft_boundary_multiwindow_p237.json`
- Rebuilt exports: `paper/export/manuscript_en_thick.html`, `paper/export/manuscript_en_thick.pdf`, `paper/export/manuscript_zh_thick.html`, `paper/export/manuscript_zh_thick.pdf`
