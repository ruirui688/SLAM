# P233 Gated Mask Multi-Window Validation

Status: `mixed_or_neutral`

Claim boundary: Bounded multi-window frontend smoke/story support only; no full benchmark, navigation, independent-label, or learned map-admission claim. P195 remains BLOCKED.

## Window Selection

- `aisle_cw_0120_0179`: Oct. 12, 2022 Aisle_CW indices `120-179` (60 frames), reason: same sequence as P225/P228, before and non-overlapping with source indices 480-539.
- `aisle_cw_0840_0899`: Oct. 12, 2022 Aisle_CW indices `840-899` (60 frames), reason: same sequence as P225/P228, after and non-overlapping with source indices 480-539.

## Metrics

| Window | Mean gated coverage | Raw APE | Gated APE | Delta APE | Raw RPE | Gated RPE | Delta RPE | Region keypoints raw->gated |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| aisle_cw_0120_0179 | 18.497106% | 0.021072 | 0.020831 | -0.000241 | 0.102477 | 0.102523 | 0.000046 | 5927->4820 |
| aisle_cw_0840_0899 | 18.000000% | 0.027162 | 0.027473 | 0.000311 | 0.101863 | 0.101896 | 0.000033 | 601->1901 |

## Interpretation

The multi-window evidence is mixed or incomplete. Treat P228 as bounded neutral smoke evidence and tune probability/coverage parameters before expanding claims.

## Commands

```bash
/home/rui/miniconda3/envs/tram/bin/python tools/run_gated_mask_multi_window_p233.py
```

## Files

- JSON: `paper/evidence/gated_mask_multi_window_p233.json`
- CSV: `paper/evidence/gated_mask_multi_window_p233.csv`
- Markdown: `paper/export/gated_mask_multi_window_p233.md`
- Output root: `outputs/gated_mask_multi_window_p233`

## Residual Risk

- Windows remain short bounded smokes, not a full benchmark.
- Gated masks are model predictions post-processed from P225 probability maps; no independent dynamic-label claim is made.
- P195 remains blocked until independent human labels exist.

## Next Step

If expanding beyond story support, add more TorWIC sequences and parameter sweeps while keeping independent-label and map-admission claims out of scope until P195 is unblocked.
