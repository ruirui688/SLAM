# P235 Soft Boundary Mask Frontend

Status: `candidate_soft_boundary_v1`

Claim boundary: Bounded frontend smoke/story-seed evidence only; no full benchmark, navigation, independent-label, learned map-admission, or manuscript-body claim. P195 remains BLOCKED.

## Scope

- First regression window: `aisle_cw_0840_0899`.
- Backtest windows: `aisle_cw_0480_0539` and `aisle_cw_0120_0179` for the selected variant.
- No manuscript-body edits; evidence is export-only.

## Metrics

| Window | Variant | Method | Coverage | Soft alpha | Region kp raw->soft | Delta | Total delta | DROID 16f | DROID 60f | Status |
|---|---|---|---:|---:|---:|---:|---:|---|---|---|
| `aisle_cw_0840_0899` | `alpha035_thr060_cap012_min256` | alpha_attenuation | 10.000000% | 3.500000% | 127->25 | -102 | 0 | not_run | not_run | `backtest_orb_proxy_down` |
| `aisle_cw_0840_0899` | `alpha050_thr060_cap012_min256` | alpha_attenuation | 10.000000% | 5.000000% | 127->74 | -53 | 0 | not_run | not_run | `backtest_orb_proxy_down` |
| `aisle_cw_0840_0899` | `feather035_sigma5_thr060_cap012_min256` | feathered_boundary | 10.000000% | 4.038715% | 127->3 | -124 | 0 | not_run | not_run | `backtest_orb_proxy_down` |
| `aisle_cw_0840_0899` | `feather050_sigma7_thr060_cap012_min256` | feathered_boundary | 10.000000% | 5.939528% | 127->4 | -123 | 0 | not_run | not_run | `backtest_orb_proxy_down` |
| `aisle_cw_0840_0899` | `meanfill035_feather5_thr060_cap012_min256` | mean_color_feather | 10.000000% | 4.038715% | 127->0 | -127 | 0 | neutral=True | neutral=True | `candidate_soft_boundary_v1` |
| `aisle_cw_0480_0539` | `meanfill035_feather5_thr060_cap012_min256` | mean_color_feather | 5.469591% | 2.193039% | 1382->188 | -1194 | 0 | neutral=True | not_run | `backtest_orb_proxy_down` |
| `aisle_cw_0120_0179` | `meanfill035_feather5_thr060_cap012_min256` | mean_color_feather | 9.843802% | 3.991233% | 215->20 | -195 | 0 | neutral=True | not_run | `backtest_orb_proxy_down` |

## Decision

`meanfill035_feather5_thr060_cap012_min256` avoids the strong 840-899 ORB proxy reversal and is DROID-neutral in the bounded gate. Treat it only as a candidate frontend smoke module pending more windows and independent labels.

## Next Plan

- Keep the soft-boundary candidate as a bounded frontend v1, not a paper-level benchmark claim.
- Add temporal/motion consistency before expanding beyond these three short windows.
- Retain P195 BLOCKED until independent human labels are available.

## Files

- JSON: `paper/evidence/soft_boundary_mask_p235.json`
- CSV: `paper/evidence/soft_boundary_mask_p235.csv`
- Markdown: `paper/export/soft_boundary_mask_p235.md`
- Output root: `outputs/soft_boundary_mask_p235`
