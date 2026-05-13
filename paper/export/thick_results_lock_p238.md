# P238 Thick Manuscript Results Lock

Status: LOCKED for thick manuscripts only.

Active manuscript paths:
- `paper/manuscript_en_thick.md`
- `paper/manuscript_zh_thick.md`

Inactive manuscript paths:
- `paper/manuscript_en.md`
- `paper/manuscript_zh.md`

Claim boundary:
- P217-P237 support a bounded dynamic-mask frontend smoke/story-seed and failure-diagnosis line only.
- P237 expands the selected P235 soft-boundary/mean-fill feather candidate to four additional short windows, including one nearby Aisle_CCW sequence.
- This remains bounded frontend module evidence only.
- Do not claim a full benchmark, navigation result, independent dynamic-label result, or learned persistent-map admission result.
- P195 remains BLOCKED.

## Locked Numbers

| Phase | Locked result | Source evidence |
|---|---|---|
| P236 | Historical lock for P217-P235/P236 integration retained unchanged | `paper/evidence/thick_results_lock_p236.json` |
| P237 | Status `expanded_bounded_support`; selected variant `meanfill035_feather5_thr060_cap012_min256`; ORB proxy down in 4/4 new windows; DROID 16f neutral in 4/4 windows; one representative 60f neutral | `paper/evidence/soft_boundary_multiwindow_p237.json` |
| P237 | Aisle_CW 240-299: coverage 8.624665%; soft alpha 3.400262%; ORB 218 -> 41; total delta 0; 16f dAPE +0.000034/dRPE +0.000020; 60f dAPE +0.000201/dRPE +0.000003 | `paper/evidence/soft_boundary_multiwindow_p237.json` |
| P237 | Aisle_CW 660-719: coverage 8.699826%; soft alpha 3.441886%; ORB 41 -> 0; total delta 0; 16f dAPE -0.000012/dRPE -0.000007 | `paper/evidence/soft_boundary_multiwindow_p237.json` |
| P237 | Aisle_CW 960-1019: coverage 10.053378%; soft alpha 3.973758%; ORB 27 -> 0; total delta 0; 16f dAPE -0.000009/dRPE +0.000000 | `paper/evidence/soft_boundary_multiwindow_p237.json` |
| P237 | Aisle_CCW 240-299: coverage 10.000000%; soft alpha 3.960283%; ORB 81 -> 4; total delta 0; 16f dAPE -0.000003/dRPE -0.000009 | `paper/evidence/soft_boundary_multiwindow_p237.json` |

## Manuscript Lock

The English and Chinese thick drafts now include:
- P237 `expanded_bounded_support` as an added bounded validation step after P235.
- The four P237 short-window ORB metrics and neutral DROID gate summary.
- Explicit wording that P237 uses short windows and one nearby Aisle_CCW sequence, not a full benchmark.
- The unchanged boundary: no navigation, independent-label, learned map-admission, or broad benchmark claim; P195 remains BLOCKED.

The brief manuscripts were not edited.

Machine-readable lock:
- `paper/evidence/thick_results_lock_p238.json`

## Residual Risks

- P237 windows remain short bounded frontend smoke checks.
- Only one nearby different sequence, Aisle_CCW, is included in P237.
- No independent dynamic segmentation labels are introduced.
- No navigation, full-benchmark, or learned map-admission claim is unlocked.
- P195 remains BLOCKED.
