# P234 Gated Mask Failure Sweep

Status: `no_stable_parameter_found`

Claim boundary: Bounded frontend failure analysis and module-planning evidence only; no full benchmark, navigation, independent-label, learned map-admission, or manuscript-body claim. P195 remains BLOCKED.

## Scope

- Window: `Oct. 12, 2022 Aisle_CW` source indices `840-899`.
- Route: reused the P233/P225 probability package; no retraining and no manuscript-body edits.
- DROID was limited to selected 16-frame gates after ORB/coverage screening.

## Sweep Table

| Variant | thr | cap/target | min comp | dil | coverage | raw->gated region kp | delta | DROID 16f |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `p233_default` | 0.50 | 0.22/0.18 | 128 | 1 | 18.000000% | 601->1901 | 1300 | not_run |
| `thr055_cap018_min128_dil1` | 0.55 | 0.18/0.16 | 128 | 1 | 16.000000% | 449->1757 | 1308 | not_run |
| `thr055_cap016_min128_dil1` | 0.55 | 0.16/0.12 | 128 | 1 | 12.000000% | 227->1352 | 1125 | not_run |
| `thr055_cap012_min128_dil0` | 0.55 | 0.12/0.10 | 128 | 0 | 10.000000% | 127->1207 | 1080 | neutral=True, dAPE=-5.7000000000001494e-05, dRPE=-3.300000000000525e-05 |
| `thr060_cap018_min128_dil1` | 0.60 | 0.18/0.16 | 128 | 1 | 16.432901% | 504->1728 | 1224 | not_run |
| `thr060_cap016_min256_dil1` | 0.60 | 0.16/0.12 | 256 | 1 | 12.248381% | 248->1349 | 1101 | not_run |
| `thr060_cap012_min256_dil0` | 0.60 | 0.12/0.10 | 256 | 0 | 10.000000% | 127->1197 | 1070 | neutral=True, dAPE=-5.7000000000001494e-05, dRPE=-3.300000000000525e-05 |
| `thr060_cap012_min128_dil1` | 0.60 | 0.12/0.10 | 128 | 1 | 10.000000% | 127->1207 | 1080 | not_run |

## Failure Analysis

Primary cause: `scene_low_raw_region_keypoints_and_mask_edge_keypoint_creation`.

- P233 default 840-899 had only 601 raw keypoints inside a fixed 18.0% predicted region, while masked images had 1901 in-region keypoints.
- The P234 default rerun has delta 1300 and 60/60 coverage-capped frames, matching the P233 failure direction.
- The sweep spans mean coverage 10.000000% to 18.000000% and in-region keypoint deltas 1070 to 1308; the best proxy variant is thr060_cap012_min256_dil0.
- Coverage-capped frames range from 31/60 to 60/60; partially uncapped variants: thr060_cap018_min128_dil1=31/60, thr060_cap016_min256_dil1=56/60. This points to coverage-target selection and mask placement, not an empty/sparse-mask instability.

Ruled down:

- Mask-too-sparse instability: the lowest tested coverage remains about 10% and all variants keep nonzero masks on all 60 frames.
- Dilation-only issue: both dilation 0 and dilation 1 variants retain positive ORB proxy deltas in this window.

## Decision

No tested threshold/coverage setting produced both ORB proxy decrease and trajectory-neutral DROID evidence on the 840-899 failure window. Treat post-processing-only gating as unstable for story expansion.

## Next Module Plan

- Stop expanding post-processing-only confidence/coverage gating until boundary placement is made temporally stable.
- Prototype boundary/motion-aware input masking: down-weight or feather high-probability mask edges instead of hard black cutouts that create ORB corners.
- Add temporal consistency over probability maps before coverage capping so selected regions do not shift by per-frame score rank alone.
- Use the 840-899 window as the first regression gate, then re-run 480-539 and 120-179 before making any multi-window story-support claim.

## Files

- JSON: `paper/evidence/gated_mask_failure_sweep_p234.json`
- CSV: `paper/evidence/gated_mask_failure_sweep_p234.csv`
- Markdown: `paper/export/gated_mask_failure_sweep_p234.md`
- Output root: `outputs/gated_mask_failure_sweep_p234`
