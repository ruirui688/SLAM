# P220 Front-End Masking SLAM Feasibility Smoke

**Status:** P220_FRONTEND_MASKING_SLAM_FEASIBILITY_SMOKE_COMPLETE

## Boundary

P220 audits/evaluates semantic dynamic-mask front-end effects only. It does not train or claim learned admission control, and it does not use weak/admission labels.

## Availability

- Default Python OpenCV: `False` (`ImportError: numpy.core.multiarray failed to import`)
- tram OpenCV: `True` (`4.12.0`)
- ORB-SLAM3 wrapper/headless/vocab/camera: `True` / `True` / `True` / `True`
- DROID root/weights: `True` / `True`

## P219 Input Audit

- Samples: `6`
- Required images/masks present: `True`
- SLAM timestamps/calibration/trajectory for P219 samples: absent; P219 is a held-out frame/mask package, not a sequence.

## ORB Feature Proxy

- Status: `ok`
- Raw keypoints total: `10059`
- Masked keypoints total: `9972`
- Total keypoint reduction: `0.008649`
- Raw keypoints in GT dynamic regions: `4795`
- Masked keypoints in GT dynamic regions: `2192`
- GT-dynamic keypoint reduction: `0.542857`

| sample | raw kp | masked kp | raw dyn kp | masked dyn kp | dyn reduction |
| --- | ---: | ---: | ---: | ---: | ---: |
| `000000904_image-0` | `1782` | `1319` | `1203` | `485` | `0.596841` |
| `000000904_image-1` | `2000` | `1989` | `646` | `118` | `0.817337` |
| `000000904_image-2` | `1906` | `1527` | `1275` | `588` | `0.538824` |
| `000000900_image-0` | `1785` | `1484` | `705` | `539` | `0.235461` |
| `000000900_image-1` | `1236` | `2000` | `482` | `4` | `0.991701` |
| `000000900_image-2` | `1350` | `1653` | `484` | `458` | `0.053719` |

## SLAM Smoke

- ORB-SLAM3: `not_run` — Existing wrapper expects a temporal sequence directory and writes inside the input session; P219 is a six-frame held-out package without timestamps/trajectory, so P220 did not force an ORB-SLAM3 trajectory run.
- DROID: `not_run` — DROID runtime and prior backend packs exist, but P219 samples are not a SLAM sequence and running DROID even on prior packs would not be raw-vs-P218-masked; bounded P220 records availability only.

## P195 Gate

- Status: `BLOCKED`
- Human labels blank: `True`
- Valid human admission labels: `0`
- Valid human same-object labels: `0`

## Recommendation

P221 should build a small temporally aligned raw-vs-P218-masked sequence package from local held-out frames before any trajectory claim. Keep P195 blocked until independent human admission/same-object labels exist.

## Outputs

- JSON evidence: `paper/evidence/frontend_masking_slam_smoke_p220.json`
- CSV evidence: `paper/evidence/frontend_masking_slam_smoke_p220.csv`
- Markdown report: `paper/export/frontend_masking_slam_smoke_p220.md`
