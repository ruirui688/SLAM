# P236 Thick Manuscript Results Lock

Status: LOCKED for thick manuscripts only.

Active manuscript paths:
- `paper/manuscript_en_thick.md`
- `paper/manuscript_zh_thick.md`

Inactive manuscript paths:
- `paper/manuscript_en.md`
- `paper/manuscript_zh.md`

Claim boundary:
- P217-P235 support a bounded dynamic-mask frontend smoke/story-seed and failure-diagnosis line only.
- P228 remains the original hard-gated 480-539 story seed.
- P233-P234 show mixed hard-gate behavior and a hard black boundary failure mode.
- P235 is a candidate soft-boundary/mean-fill feather frontend that fixes the observed 840-899 ORB regression in bounded smoke.
- Do not claim a full benchmark, navigation result, independent dynamic-label result, or learned persistent-map admission result.
- P195 remains BLOCKED.

## Locked Numbers

| Phase | Locked result | Source evidence |
|---|---|---|
| P231 | Historical lock for P217-P228 values retained unchanged | `paper/evidence/thick_results_lock_p231.json` |
| P233 | 120-179 mean coverage 18.497106%; APE 0.021072 -> 0.020831; RPE 0.102477 -> 0.102523; ORB 5927 -> 4820 | `paper/evidence/gated_mask_multi_window_p233.json` |
| P233 | 840-899 mean coverage 18.000000%; APE 0.027162 -> 0.027473; RPE 0.101863 -> 0.101896; ORB 601 -> 1901 | `paper/evidence/gated_mask_multi_window_p233.json` |
| P234 | No stable hard/post-processing setting found on 840-899; best proxy variant `thr060_cap012_min256_dil0` still ORB 127 -> 1197; 16f dAPE -0.000057 and dRPE -0.000033 | `paper/evidence/gated_mask_failure_sweep_p234.json` |
| P235 | Selected candidate `meanfill035_feather5_thr060_cap012_min256`; 840-899 ORB 127 -> 0, total keypoint delta 0; 16f dAPE -0.000036/dRPE +0.000007; 60f dAPE +0.000158/dRPE -0.000003 | `paper/evidence/soft_boundary_mask_p235.json` |
| P235 | Backtest 480-539 ORB 1382 -> 188, total keypoint delta 0, 16f neutral | `paper/evidence/soft_boundary_mask_p235.json` |
| P235 | Backtest 120-179 ORB 215 -> 20, total keypoint delta 0, 16f neutral | `paper/evidence/soft_boundary_mask_p235.json` |

## Manuscript Lock

The English and Chinese thick drafts now include:
- P233 mixed multi-window hard-gate result.
- P234 failure diagnosis: hard black mask boundaries can create ORB features; post-processing-only confidence/coverage tuning is not enough.
- P235 soft-boundary candidate: mean-fill feathering fixes the observed 840-899 regression window in bounded smoke.

The brief manuscripts were not edited.

Machine-readable lock:
- `paper/evidence/thick_results_lock_p236.json`

## Residual Risks

- P235 is only a candidate frontend module based on short bounded windows.
- No independent dynamic segmentation labels are introduced.
- No navigation, full-benchmark, or learned map-admission claim is unlocked.
- P195 remains BLOCKED.
