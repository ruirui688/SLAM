# ORB-SLAM3 Cross-Check — P173 Recovery Artifact

**Date:** 2026-05-10  
**Phase:** P173-recovery — ORB-SLAM3 mono_tum on Jun15 Run1 (aisle CCW)  
**Status:** RUNTIME — trajectories produced, tracking fragile, evo absent

## Build Status

- **ORB-SLAM3 binary:** `/tmp/ORB_SLAM3/Examples/Monocular/mono_tum` — built, functional
- **Shared library:** `/tmp/ORB_SLAM3/lib/libORB_SLAM3.so` — present
- **Vocabulary:** `/tmp/ORB_SLAM3/Vocabulary/ORBvoc.txt` — extracted, loads correctly

## Vocabulary

- `ORBvoc.txt` present, loads without errors.
- 290 map points created on initialization (both raw and masked).

## Camera Configuration

Intrinsics sourced from TorWIC calibrations file (`/home/rui/slam/data/TorWIC_SLAM_Dataset/Oct. 12, 2022/calibrations.txt`), left camera:

| Parameter | Value |
|---|---|
| fx | 621.397 |
| fy | 620.649 |
| cx | 649.644 |
| cy | 367.908 |
| k1 | 0.07547 |
| k2 | -0.03149 |
| p1 | 0.00102 |
| p2 | 0.00210 |
| k3 | 0.000935 (discarded — ORB-SLAM3 uses k1,k2,p1,p2 only) |
| Resolution | 1280×720 |

Config written to: `/home/rui/slam/outputs/orb_slam3_p173_recovery/TorWIC_mono_left.yaml`

## Run Commands

### Raw (unmasked) mono_tum

```bash
cd /tmp/ORB_SLAM3
export LD_LIBRARY_PATH=/home/rui/.local/lib:/tmp/ORB_SLAM3/lib:/tmp/ORB_SLAM3/Thirdparty/DBoW2/lib:/tmp/ORB_SLAM3/Thirdparty/g2o/lib:$LD_LIBRARY_PATH
export PANGOLIN_WINDOW_URI=headless:/tmp/orbslam3_pangolin_raw
timeout 120 ./Examples/Monocular/mono_tum \
  Vocabulary/ORBvoc.txt \
  /home/rui/slam/outputs/orb_slam3_p173_recovery/TorWIC_mono_left.yaml \
  /home/rui/slam/outputs/orb_slam3_p173_recovery/raw_run
```

- 61 images processed (3 skipped — ORB-SLAM3 header skip on TUM-format rgb.txt without comment header)
- **Initialization succeeded:** 290 map points, "New Map created"
- **Tracking failure:** "Fail to track local map!" → "Relocalized!!" → killed by 120s timeout
- Median tracking time: 0.022 s/frame
- 10 keyframes written

### Masked mono_tum

Same as above, replacing `raw_run` with `masked_run`.

- 61 images processed
- **Initialization succeeded:** 290 map points
- **No explicit tracking failure printed** before timeout
- Median tracking time: 0.021 s/frame
- 12 keyframes written

## Trajectory Status

| Variant | Keyframes | First KF timestamp | Last KF timestamp | Initialization |
|---|---|---|---|---|
| Raw | 10 | 5.158 s | 6.355 s | ✓ (290 pts) |
| Masked | 12 | 5.158 s | 6.355 s | ✓ (290 pts) |

Both trajectories cover only ~1.2 s of the sequence (5.16–6.35 s). The full sequence is 64 frames at ~0.11 s intervals ≈ 7.0 s total. ORB-SLAM3 initialization + tracking covered roughly the first 17–20% of the sequence before tracking failed.

The last valid poses differ slightly between raw and masked, as expected with different feature sets:
- Raw final position: (−0.029, 0.0004, −0.019) m
- Masked final position: (−0.031, 0.0003, −0.020) m

## Metrics

- **evo not installed.** No APE/RPE computed. Install blocked by recovery-step constraint ("do not install if absent").
- Manual trajectory inspection shows both variants produce the same initialization frame (timestamp 5.158 s) and similar pose progression through 10–12 keyframes.

## Blocker Analysis

1. **Short sequence (64 frames):** ORB-SLAM3 monocular requires sufficient baseline for initialization. With only 64 frames (~7 s), initialization may barely complete before the sequence ends.
2. **Feature matching on 1280×720:** The corridor aisle scene may be texture-poor, causing rapid tracking loss after initialization.
3. **Tracking failure:** The raw run explicitly reports "Fail to track local map!" after ~10 keyframes. The masked run shows no explicit failure message but was killed by the same 120s timeout.
4. **No CameraTrajectory.txt:** Only KeyFrameTrajectory.txt was saved (sparse keyframe poses, not per-frame camera poses).
5. **No evo for metric comparison.**

## Next Commands

1. **Install evo** and compute APE/RPE on the existing KeyFrameTrajectory files against groundtruth (first frame alignment).
2. **Try ORB-SLAM3 with more features** (e.g., `ORBextractor.nFeatures: 2000`) and/or lower FAST thresholds to improve tracking robustness.
3. **Consider stereo or RGB-D mode** if depth maps are available from TorWIC (Azure Kinect provides depth).
4. **Longer timeout** (300s) or allow run to complete naturally — the 120s timeout may kill before relocalization finishes.
5. **Test on a longer sequence** (e.g., a full Jun15 session with 300+ frames) to give ORB-SLAM3 more baseline for robust initialization and tracking.
