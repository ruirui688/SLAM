# P219 Front-End Masking Evaluation Package

**Status:** P219_FRONTEND_MASKING_EVAL_PACKAGE_READY

## Boundary

P219 evaluates P218 semantic dynamic-mask front-end inputs and non-SLAM proxy metrics only. It does not train or claim learned persistent-map admission control.

## Package

- Samples: `6` (`val=3`, `test=3`)
- Masking mode: `suppress`
- Selected P218 threshold: `0.40`
- Local package root: `outputs/frontend_masking_eval_p219`

## Proxy Metrics

- Mean predicted masked pixel rate: `0.208691`
- Mean GT dynamic pixel rate: `0.137248`
- Mean mask precision/recall/F1/IoU: `0.556007` / `0.789669` / `0.604636` / `0.44321`
- ORB proxy: `unavailable (ImportError: numpy.core.multiarray failed to import; stderr=AttributeError: _ARRAY_API not found)`

## Samples

| split | sample | pred rate | GT rate | precision | recall | IoU | masked image |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| val | `000000904_image-0` | `0.21856083` | `0.18932046` | `0.639018` | `0.737714` | `0.520714` | `outputs/frontend_masking_eval_p219/masked_images/val_000000904_image-0_masked.png` |
| val | `000000904_image-1` | `0.25661458` | `0.09260959` | `0.351845` | `0.974938` | `0.348692` | `outputs/frontend_masking_eval_p219/masked_images/val_000000904_image-1_masked.png` |
| val | `000000904_image-2` | `0.11434503` | `0.15781004` | `0.832477` | `0.603191` | `0.5379` | `outputs/frontend_masking_eval_p219/masked_images/val_000000904_image-2_masked.png` |
| test | `000000900_image-0` | `0.27833137` | `0.1674774` | `0.50354` | `0.836834` | `0.458522` | `outputs/frontend_masking_eval_p219/masked_images/test_000000900_image-0_masked.png` |
| test | `000000900_image-1` | `0.25390625` | `0.06692491` | `0.241128` | `0.914816` | `0.235833` | `outputs/frontend_masking_eval_p219/masked_images/test_000000900_image-1_masked.png` |
| test | `000000900_image-2` | `0.13038522` | `0.1493465` | `0.768032` | `0.670521` | `0.557598` | `outputs/frontend_masking_eval_p219/masked_images/test_000000900_image-2_masked.png` |

## Evaluation Protocol

1. Use these six held-out P218 prediction samples as a deterministic raw-vs-masked input sanity package.
2. For each row, compare raw image front-end features against the masked image where P218 predicted dynamic pixels are suppressed.
3. Report mask pixel coverage and GT-mask precision/recall/IoU as front-end input quality checks, not SLAM trajectory metrics.
4. If OpenCV ORB is available, report total keypoints and keypoints in the GT dynamic region before/after masking as a feature-masking proxy.
5. Run actual ORB/DROID trajectory smoke only in P220 on a tiny existing local raw-vs-masked backend pack; use ATE/RPE only when trajectories and ground truth align.

## P195 Gate

- Status: `BLOCKED`
- Human labels blank: `True`
- Valid `human_admit_label`: `0`
- Valid `human_same_object_label`: `0`

## P220 Recommendation

Run a tiny raw-vs-masked trajectory smoke using an existing local ORB-SLAM3 or DROID-SLAM helper on a short held-out sequence/package only after confirming the runtime is already available. Keep the comparison bounded: raw RGB vs P218-masked RGB, record feature/trajectory availability, ATE/RPE if valid ground truth exists, and do not claim learned admission control.

## Outputs

- JSON evidence: `paper/evidence/frontend_masking_eval_p219.json`
- CSV evidence: `paper/evidence/frontend_masking_eval_p219.csv`
- Markdown report: `paper/export/frontend_masking_eval_p219.md`
- Ignored local images/manifests: `outputs/frontend_masking_eval_p219`
