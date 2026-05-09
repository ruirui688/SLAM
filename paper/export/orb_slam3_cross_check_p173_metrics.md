# ORB-SLAM3 Cross-Check — P173 Metrics

**Date:** 2026-05-10
**Phase:** P173-cross-check-correction
**Status:** COMPLETED — evo APE/RPE computed on sparse keyframe trajectories; no trajectory-level claim supported

## Metric Validity

✅ **Metrics are mathematically valid** — timestamps match groundtruth within `--t_max_diff 0.05`, SE(3) Umeyama alignment applied, APE/RPE computed with evo 1.36.4.

⚠️ **Low statistical power** — only 5 (raw) / 9 (masked) keyframe pose pairs. ORB-SLAM3 produced KeyFrameTrajectory.txt only, no dense per-frame CameraTrajectory.txt.

⚠️ **Partial coverage** — ORB-SLAM3 keyframes span ~1.2 s of the 64-frame (~7 s) sequence.

## Results Summary

| Variant | Keyframes | APE RMSE (m) | APE Mean (m) | RPE RMSE (m) | RPE Mean (m) |
|---------|-----------|-------------|-------------|-------------|-------------|
| Raw | 5 | 0.041 | 0.035 | 0.044 | 0.036 |
| Masked | 9 | 0.043 | 0.034 | 0.032 | 0.024 |

## Interpretation

- **APE RMSE ~4 cm** on ~1.2 s of sparse keyframes: consistent with monocular SLAM on a texture-challenged corridor, but based on very few pose pairs (N=5–9).
- **Raw vs masked APE difference** (0.041 vs 0.043 m) is within the uncertainty of a 5–9 point sparse sample. No direction claim is warranted.
- **RPE** for raw (4 delta pairs) vs masked (8 delta pairs) computed over different numbers of pose transitions at irregular keyframe intervals — not directly comparable.
- **Masked KF count (9) > raw KF count (5):** a runtime/tracking observation (ORB-SLAM3 tracked longer under masked input). Does NOT constitute odometry improvement evidence.

## Caveats

1. **Sparse keyframes only** — no per-frame camera poses available. This is a fundamental limitation on this 64-frame TorWIC sequence.
2. **Partial coverage** — ORB-SLAM3 did not track the full 7 s sequence. Metrics characterize only the successful keyframe portion.
3. **Monocular scale ambiguity** — SE(3) Umeyama alignment corrects rotation/translation but not scale. Without metric baseline information, absolute scale is unobservable.
4. **Irregular keyframe spacing** — RPE computed between non-consecutive frames at variable time deltas; not comparable to frame-rate RPE from dense SLAM systems.
5. **Cross-system comparison unsupported** — ORB-SLAM3 APE/RPE on sparse keyframes is not directly comparable to DROID-SLAM APE/RPE on dense per-frame poses. Different trajectory density, different coordinate frames, different error profiles.

## No Improvement Claim

These metrics document that ORB-SLAM3 built successfully, ran headless on TorWIC, produced numerically valid trajectories, and that evo APE/RPE can be computed on the output. They do NOT support a claim of raw-vs-masked trajectory improvement, trajectory-neutrality generalization, or cross-SLAM-paradigm comparability.

## Full Results

See: `paper/evidence/orb_slam3_cross_check_p173_metrics.json`
