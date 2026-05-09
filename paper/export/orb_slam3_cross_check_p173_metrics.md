# ORB-SLAM3 Cross-Check — P173 Metrics

**Date:** 2026-05-10  
**Phase:** P173-recovery — metric evaluation  
**Status:** COMPLETED — APE/RPE computed, sparse-only, tracking fragile

## Metric Validity

✅ **Metrics are mathematically valid** — timestamps match groundtruth exactly, SE(3) Umeyama alignment applied, APE/RPE computed with standard evo (`evo 1.36.4`).

⚠️ **Low statistical power** — only 10 (raw) / 12 (masked) keyframes over ~1.2s. ORB-SLAM3 did not produce dense CameraTrajectory.txt.

⚠️ **Partial coverage** — ORB-SLAM3 tracked ~17% of the 64-frame (~7s) sequence before tracking loss.

## Results Summary

| Variant | Keyframes | Duration | APE RMSE (m) | APE Mean (m) | RPE RMSE (m) | RPE Mean (m) |
|---|---|---|---|---|---|---|
| Raw | 10 | 1.196 s | 0.052 | 0.044 | 0.024 | 0.023 |
| Masked | 12 | 1.196 s | 0.048 | 0.041 | 0.020 | 0.018 |

## Interpretation

- **APE ~4–5 cm** on a ~1.2s keyframe window: consistent with monocular SLAM in a texture-challenged corridor, but based on very few poses.
- **Raw vs masked**: The masked variant is numerically lower by ~0.5 cm in this short keyframe subset, but the sample is too small to infer an odometry improvement or a feature-matching mechanism.
- **RPE ~2 cm** per keyframe step: reflects local drift between consecutive keyframes (irregular intervals).
- **Scale**: ORB-SLAM3 monotonic scale was not explicitly corrected; SE(3) alignment includes implicit rotation+translation only.

## Caveats

1. **Sparse keyframes only** — no per-frame camera poses available. This is a fundamental limitation of ORB-SLAM3's KeyFrameTrajectory.txt output on this sequence.
2. **Partial coverage** — ORB-SLAM3 failed to track >80% of the sequence. The computed metrics characterize only the successful portion.
3. **Monocular scale ambiguity** — without additional metric information (e.g., known baseline length), absolute scale is unobservable.
4. **Irregular keyframe spacing** — RPE computed between non-consecutive frames at variable time deltas; not directly comparable to frame-rate RPE from other systems.

## No Improvement Claim

These numbers **do not** constitute a claim of improvement over any baseline SLAM system. They merely document that ORB-SLAM3 initialized and tracked briefly on the TorWIC Jun15 Run1 scene, and that the masked trajectory had slightly lower sparse-keyframe error inside that short window.

## Full Results

See: `paper/evidence/orb_slam3_cross_check_p173_metrics.json`
