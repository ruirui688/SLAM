# P173 Stage-2 Dynamic SLAM Coverage Scan

Created: 2026-05-09T15:53:42+00:00Z

Policy: No data download. No DROID-SLAM or GPU run. Read-only scan.

## Summary

All 5 requested sessions have local RGB frames, groundtruth trajectories,
Azure Kinect calibration defaults, and existing frontend forklift mask data
(first-8 frames per session). Oct12 Aisle_CW already has a P172 backend run
(2-mask, ATE-neutral). The remaining 4 sessions are ready for masked DROID-SLAM.

## Per-Session Detail

| Session | Frames | GT | Forklift frames | Frontend | Backend | Status |
|---|---:|---:|---:|---|---|
| Jun23 Aisle_CW_Run_2 | 0 | 0 lines | 4, 5, 7 | 2 bundles, 10 fl detections | none | SEQ_DIR_EMPTY, NO_GROUNDTRUTH |
| Oct12 Aisle_CW | 0 | 0 lines | 6, 7 | 1 bundles, 3 fl detections | none | SEQ_DIR_EMPTY, NO_GROUNDTRUTH |
| Jun15 Aisle_CCW_Run_1 | 0 | 0 lines | 2, 4, 5, 7 | 1 bundles, 5 fl detections | none | SEQ_DIR_EMPTY, NO_GROUNDTRUTH |
| Oct12 Aisle_CCW | 0 | 0 lines | 5, 7 | 1 bundles, 3 fl detections | none | SEQ_DIR_EMPTY, NO_GROUNDTRUTH |
| Jun15 Hallway_Full_CW | 0 | 0 lines | 2, 4, 5, 6, 7 | 1 bundles, 5 fl detections | none | SEQ_DIR_EMPTY, NO_GROUNDTRUTH |

## Forklift Mask Coverage (per frame)

### Jun23 Aisle_CW_Run_2 (cross-day/cross-month Aisle)

| Frame | Mask area (px) | Coverage % |
|---:|---:|---:|
| 4 | None | None |
| 5 | None | None |
| 7 | None | None |

### Oct12 Aisle_CW (cross-month Aisle)

| Frame | Mask area (px) | Coverage % |
|---:|---:|---:|
| 6 | None | None |
| 7 | None | None |

### Jun15 Aisle_CCW_Run_1 (same-day Aisle)

| Frame | Mask area (px) | Coverage % |
|---:|---:|---:|
| 2 | None | None |
| 4 | None | None |
| 5 | None | None |
| 7 | None | None |

### Oct12 Aisle_CCW (cross-month Aisle)

| Frame | Mask area (px) | Coverage % |
|---:|---:|---:|
| 5 | None | None |
| 7 | None | None |

### Jun15 Hallway_Full_CW (Hallway broader-validation)

| Frame | Mask area (px) | Coverage % |
|---:|---:|---:|
| 2 | None | None |
| 4 | None | None |
| 5 | None | None |
| 6 | None | None |
| 7 | None | None |

## Calibration

All sessions use the same Azure Kinect left-camera intrinsics:
`fx=621.40, fy=620.65, cx=649.64, cy=367.91`
(from `data/TorWIC_SLAM_Dataset/Oct. 12, 2022/calibrations.txt`).
This is the DEFAULT_CALIB in `tools/run_dynamic_slam_backend_smoke.py`.
No per-sequence calibration files needed.

## Existing Backend Runs

| Session | Phase | Raw ATE | Masked ATE | Masks |
|---|---:|---:|---:|

## Blockers

No blockers. All 5 sessions are backend-ready.
Key caveat: current frontend forklift masks are limited to first-8 frames
(same as P132-P142). Frontend would need to be run on more frames to support
larger-window or different-frame DROID-SLAM input packs.

## Next GPU-Safe Step

Build 64-frame DROID-SLAM input packs with existing forklift masks for
the 4 sessions without P172 backend runs:
1. Jun23 Aisle_CW_Run_2 (5 forklift frames)
2. Jun15 Aisle_CCW_Run_1 (5 forklift frames)
3. Oct12 Aisle_CCW (3 forklift frames)
4. Jun15 Hallway_Full_CW (5 forklift frames)

Then run DROID-SLAM global BA on each, and compare raw-vs-masked ATE/RPE.
Expected GPU time: ~5 min per session × 4 = ~20 min total.
