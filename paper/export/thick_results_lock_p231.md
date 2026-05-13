# P231 Thick Manuscript Results Lock

Status: LOCKED for thick manuscripts only.

Active manuscript path:
- `paper/manuscript_en_thick.md`
- `paper/manuscript_zh_thick.md`

Inactive manuscript path:
- `paper/manuscript_en.md`
- `paper/manuscript_zh.md`

Claim boundary:
- P217-P228 support a bounded dynamic-mask frontend smoke/story seed only.
- P228 is trajectory-neutral DROID smoke plus ORB predicted/gated-region proxy evidence.
- Do not claim a full benchmark, navigation result, independent dynamic-label result, or learned persistent-map admission result.
- P195 remains BLOCKED.

## Locked Numbers

| Phase | Locked result | Source evidence |
|---|---|---|
| P217 | 237 rows; 156/51/30 split; zero frame-group overlap; positive pixel rate 0.374176 | `paper/evidence/dynamic_mask_dataset_p217.json` |
| P218 | validation IoU/F1 0.671304/0.803329; test IoU/F1 0.578580/0.733038; selected threshold 0.40 | `paper/evidence/dynamic_mask_training_p218.json` |
| P219 | held-out precision/recall/F1/IoU 0.556007/0.789669/0.604636/0.443210 | `paper/evidence/frontend_masking_eval_p219.json` |
| P220 | ORB GT dynamic-region keypoints 4795 -> 2192; 54.2857% reduction | `paper/evidence/frontend_masking_slam_smoke_p220.json` |
| P225 | 60 frames; Oct. 12, 2022 Aisle_CW; indices 480-539; trajectory-ready input only; bounded retrained SmallUNet because prior P218 checkpoint was unavailable | `paper/evidence/temporal_masked_sequence_p225.json` |
| P226 | recommended main baseline: DROID-SLAM raw vs masked temporal/dynamic frontend; secondary network baseline: P218 compact binary dynamic-mask segmentation; 8-frame reproduction raw/masked APE 0.001242/0.001243 and RPE 0.002250/0.002255 | `paper/evidence/baseline_reproduction_plan_p226.json` |
| P227 | 60-frame DROID raw/masked APE 0.088504/0.084529; RPE 0.076145/0.076226; ORB predicted-region keypoints 21030 -> 18617; neutral | `paper/evidence/p225_baseline_reproduction_p227.json` |
| P228 | threshold 0.50; dilation 1 px; min component 128 px; max/target coverage 0.22/0.18; mean coverage 14.127053%; 60-frame DROID raw/masked APE 0.088496/0.084705; RPE 0.076145/0.076224; ORB gated-region keypoints 8969 -> 5073; viable frontend story seed | `paper/evidence/confidence_gated_mask_module_p228.json` |

## Manuscript Lock

The English and Chinese thick drafts consistently include the P217-P228 numbers above and keep P228 language bounded as frontend smoke/story seed evidence. The brief manuscripts were not edited for this lock.

P230 quality gate report:
- `paper/export/thick_manuscript_quality_gate_p230.md`

Machine-readable lock:
- `paper/evidence/thick_results_lock_p231.json`

## Residual Risks

- Citation style remains venue-deferred.
- Raw/semantic evidence JSON timestamp-only modifications predate this lock and are not required for P231.
- Untracked `thirdparty/` and ORB wrapper/headless files are not part of this documentation lock.
