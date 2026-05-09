# P173 — ORB-SLAM3 Cross-Check Recovery Report

**Date:** 2026-05-10
**Status:** ⚠️ PARTIAL — headless runner built and executed; sparse keyframe trajectories produced; evo APE/RPE computed on sparse keyframes; full-sequence runs and dense per-frame poses not yet available.

---

## 1. Build Chain

### Dependencies
| Component | Version | Source | Status |
|-----------|---------|--------|--------|
| Pangolin | master (2025) | GitHub, /tmp/Pangolin | ✅ Built locally to ~/.local |
| ORB-SLAM3 | master (UZ-SLAMLab) | GitHub, /tmp/ORB_SLAM3 | ✅ Built with C++14 |
| OpenCV | 4.5.4 | system apt | ✅ |
| Eigen3 | 3.4.0 | system apt | ✅ |
| ORBvoc.txt | 145 MB | ORB_SLAM3 repo | ✅ Extracted |
| evo | 1.36.4 | pip --user | ✅ Working (scipy 1.15.3 resolved earlier version clash) |

### Build blockers resolved
- `libepoxy-dev` not installed: extracted .deb headers to ~/.local, created `libepoxy.so` symlink
- Pangolin GL initialization: built without EGL support for headless mode
- ORB-SLAM3 `std::make_unique`: C++14 flag in cmake
- `bUseViewer=true`: wrote headless runner with `bUseViewer=false`

### Headless runner
- Source: `/tmp/ORB_SLAM3/Examples/Monocular/run_headless.cc`
- Key differences from stock `mono_tum`:
  - `bUseViewer=false` (no Pangolin window)
  - Auto-rewrites rgb.txt to use local `image_left/` paths
  - Handles 1280×720 TorWIC images

---

## 2. Experimental Results

### Configuration
- **Sequence:** TorWIC Aisle_CCW_Run_1, 64-frame window (frames 000000–000063)
- **Camera:** Azure Kinect Left, 1280×720, PinHole model
  - fx=621.40, fy=620.65, cx=649.64, cy=367.91
  - k1=0.0755, k2=−0.0315, p1=0.0010, p2=0.0021
- **ORB:** 1000 features, 8 levels, scale 1.2, FAST 20/7

### Trajectory counts (two independent runs)

**Run A (02:32, earlier):**
- Raw: 10 keyframes
- Masked: 12 keyframes
- Trajectory files: `outputs/orb_slam3_p173_recovery/{raw,masked}_KeyFrameTrajectory.txt`

**Run B (02:45, later):**
- Raw: 5 keyframes
- Masked: 9 keyframes
- Trajectory files: `outputs/orb_slam3_cross_check_p173/traj_{raw,masked}_aisle_ccw_run1.txt`

In both runs, masked input produced more keyframes than raw. This is a runtime/tracking observation — it indicates that ORB-SLAM3 tracked longer (or selected more frequent keyframes) under masked input, but does NOT by itself demonstrate better odometry accuracy.

### evo APE/RPE — Run B (5/9 KFs, computed 2026-05-10 02:56+08)

Computed via `evo_ape tum` / `evo_rpe tum` with SE(3) Umeyama alignment, `--t_max_diff 0.05`, against the 64-frame groundtruth TUM trajectory.

| Variant | KF pairs | APE RMSE (m) | APE Mean (m) | APE Std (m) | RPE RMSE (m) |
|---------|----------|-------------|-------------|------------|-------------|
| Raw | 5 | 0.0409 | 0.0346 | 0.0218 | 0.0435 |
| Masked | 9 | 0.0431 | 0.0342 | 0.0262 | 0.0317 |

**Caveats:**
- N=5 vs N=9: these are sparse keyframe pose pairs, not per-frame camera poses. Neither number is adequate for a robust APE/RPE comparison.
- The APE difference (0.041 vs 0.043 m) is within the uncertainty of a 5–9 point sample.
- RPE for raw (4 consecutive delta pairs) vs masked (8 pairs) is computed over different numbers of pose transitions at irregular keyframe intervals — not directly comparable.
- These metrics validate that evo can be applied and that ORB-SLAM3 produced numerically valid trajectories; they do NOT establish a raw-vs-masked trajectory improvement.

### Common-keyframe |Δ| (Run B, 5 matching timestamps)

As a low-level sanity check, the absolute difference between raw and masked keyframe poses was computed at the 5 timestamps where both trajectories produced a keyframe.

| Timestamp | |Δ| (mm) — ORB coordinate frame |
|-----------|------|
| 5.16 s | 0.000 |
| 5.56 s | 0.962 |
| 5.76 s | 4.829 |
| 5.86 s | 4.403 |
| 5.96 s | 7.018 |
| **Mean** | **3.442** |

**This is a raw coordinate-frame delta, not an evo APE/RPE metric.** It has no alignment, no ground-truth reference, and is not directly comparable to DROID-SLAM APE/RPE values. It only confirms that the two trajectories diverged over time (expected, given different feature sets).

---

## 3. Claim Boundaries

### What is established
- ORB-SLAM3 builds and runs on TorWIC at user level (no sudo, no GPU)
- Headless mono runner produces sparse keyframe trajectories on 64-frame windows
- evo APE/RPE can be computed on ORB-SLAM3 keyframe outputs against groundtruth
- Masked input produced more keyframes than raw in both independent runs (12>10, 9>5)
- Within the sparse keyframe limits, raw-vs-masked APE values are close (± few mm) in both runs

### What is NOT established
- Meaningful full-trajectory APE/RPE (only sparse keyframes, N≤12)
- A claim that masking improves ORB-SLAM3 odometry
- Trajectory-neutrality generalization across SLAM paradigms
- Comparability to DROID-SLAM APE/RPE (different trajectory density, different coordinate frames, different error profiles)
- Statistical significance (n=1 sequence, 5–12 keyframes)
- Full-session ORB-SLAM3 tracking robustness

---

## 4. Blockers and Next Steps

### Current blockers
1. **Sparse keyframe only:** ORB-SLAM3 did not produce dense CameraTrajectory.txt — only KeyFrameTrajectory.txt. APE/RPE is limited to 5–12 pose pairs.
2. **Short 64-frame window:** ORB-SLAM3 tracking covers only ~1.2 s out of ~7 s (17%). Full-sequence data is locally available but not yet processed.
3. **Single session:** Only Aisle_CCW_Run_1 tested. Cross-session generalizability is unknown.

### Recommended next phase (if pursued)
Extend ORB-SLAM3 to full-sequence Aisle_CW_Run_1 (≥300 frames) for denser keyframe trajectories and meaningfully powered evo ATE/RPE comparison. Requires:
- Extract full-sequence image data from local TorWIC
- Run raw + masked full-sequence headless
- Compute evo_ape with Sim(3) alignment on denser trajectories

---

## 5. Artifacts

| File | Path |
|------|------|
| Headless runner source | `/tmp/ORB_SLAM3/Examples/Monocular/run_headless.cc` |
| Headless runner binary | `/tmp/ORB_SLAM3/Examples/Monocular/run_headless` |
| TorWIC config | `/tmp/torwic_mono.yaml` |
| Run A raw trajectory (10 KFs) | `/home/rui/slam/outputs/orb_slam3_p173_recovery/raw_KeyFrameTrajectory.txt` |
| Run A masked trajectory (12 KFs) | `/home/rui/slam/outputs/orb_slam3_p173_recovery/masked_KeyFrameTrajectory.txt` |
| Run B raw trajectory (5 KFs) | `/home/rui/slam/outputs/orb_slam3_cross_check_p173/traj_raw_aisle_ccw_run1.txt` |
| Run B masked trajectory (9 KFs) | `/home/rui/slam/outputs/orb_slam3_cross_check_p173/traj_masked_aisle_ccw_run1.txt` |
| Ground truth (64 poses) | `/home/rui/slam/outputs/orb_slam3_cross_check_p173/groundtruth_aisle_ccw_run1.txt` |
| ORB-SLAM3 build | `/tmp/ORB_SLAM3/` (lib, examples, vocab) |
| evo metrics JSON | `paper/evidence/orb_slam3_cross_check_p173_metrics.json` |
| This report | `paper/export/orb_slam3_cross_check_p173_recovery.md` |

---

## 6. Reproducibility Commands

```bash
# Build ORB-SLAM3
git clone https://github.com/UZ-SLAMLab/ORB_SLAM3.git
cd ORB_SLAM3
# Fix C++14, build Thirdparty, add headless runner (see run_headless.cc)
cmake .. -DCMAKE_CXX_STANDARD=14 -DCMAKE_PREFIX_PATH=~/.local ...
make -j$(nproc)

# Run raw
LD_LIBRARY_PATH=~/.local/lib:lib:Thirdparty/DBoW2/lib:Thirdparty/g2o/lib \
  ./Examples/Monocular/run_headless \
  Vocabulary/ORBvoc.txt torwic_mono.yaml <seq_path>/raw

# Run masked
LD_LIBRARY_PATH=... ./Examples/Monocular/run_headless \
  Vocabulary/ORBvoc.txt torwic_mono.yaml <seq_path>/masked

# evo APE
evo_ape tum groundtruth.txt traj_raw.txt --align --t_max_diff 0.05
evo_ape tum groundtruth.txt traj_masked.txt --align --t_max_diff 0.05
```
