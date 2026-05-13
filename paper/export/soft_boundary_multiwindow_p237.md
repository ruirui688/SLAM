# P237 Soft Boundary Multi-Window Validation

Status: `expanded_bounded_support`

Claim boundary: Bounded frontend module evidence only; no full benchmark, navigation, independent-label, learned map-admission, or manuscript-body claim. P195 remains BLOCKED.

## Window Selection

- `aisle_cw_0240_0299`: Oct. 12, 2022 Aisle_CW indices `240-299` (60 frames), reason: same sequence as P225/P228, non-overlapping with 120-179, 480-539, and 840-899.
- `aisle_cw_0660_0719`: Oct. 12, 2022 Aisle_CW indices `660-719` (60 frames), reason: same sequence as P225/P228, non-overlapping mid-late window.
- `aisle_cw_0960_1019`: Oct. 12, 2022 Aisle_CW indices `960-1019` (60 frames), reason: same sequence as P225/P228, non-overlapping late window within available frame range.
- `aisle_ccw_0240_0299`: Oct. 12, 2022 Aisle_CCW indices `240-299` (60 frames), reason: nearby different sequence with image_left, frame_times, traj_gt, and shared Oct. 12 calibration.

## Metrics

| Window | Family | Coverage | Soft alpha | Region kp raw->soft | Delta | Total delta | DROID 16f | DROID 60f | Status |
|---|---|---:|---:|---:|---:|---:|---|---|---|
| `aisle_cw_0240_0299` | same_sequence_new_window | 8.624665% | 3.400262% | 218->41 | -177 | 0 | neutral=True, dAPE=3.399999999999931e-05, dRPE=2.0000000000006124e-05 | neutral=True, dAPE=0.0002009999999999998, dRPE=2.9999999999891225e-06 | `orb_proxy_down_droid16_neutral_droid60_checked` |
| `aisle_cw_0660_0719` | same_sequence_new_window | 8.699826% | 3.441886% | 41->0 | -41 | 0 | neutral=True, dAPE=-1.2000000000012001e-05, dRPE=-7.000000000007001e-06 | not_run | `orb_proxy_down_droid16_neutral` |
| `aisle_cw_0960_1019` | same_sequence_new_window | 10.053378% | 3.973758% | 27->0 | -27 | 0 | neutral=True, dAPE=-8.999999999998592e-06, dRPE=0.0 | not_run | `orb_proxy_down_droid16_neutral` |
| `aisle_ccw_0240_0299` | nearby_different_sequence | 10.000000% | 3.960283% | 81->4 | -77 | 0 | neutral=True, dAPE=-3.0000000000030003e-06, dRPE=-9.000000000002062e-06 | not_run | `orb_proxy_down_droid16_neutral` |

## Interpretation

The selected P235 soft-boundary candidate reduced the ORB predicted-region proxy in 4/4 new windows, with DROID 16-frame neutral gates in 4/4 windows. Treat this as expanded bounded frontend-module support only.

## Commands

```bash
/home/rui/miniconda3/envs/tram/bin/python tools/run_soft_boundary_multiwindow_p237.py
```

## Files

- JSON: `paper/evidence/soft_boundary_multiwindow_p237.json`
- CSV: `paper/evidence/soft_boundary_multiwindow_p237.csv`
- Markdown: `paper/export/soft_boundary_multiwindow_p237.md`
- Output root: `outputs/soft_boundary_multiwindow_p237`

## Residual Risk

- Windows remain short bounded smoke checks, not a full benchmark.
- Probability maps are P225/P218 model predictions; no independent dynamic labels are introduced.
- No navigation, planning, or learned persistent-map admission claim is made.
- P195 remains BLOCKED.

## Next Step

Add more sequences and independent dynamic labels before considering any claim-boundary change; keep P195 BLOCKED.
