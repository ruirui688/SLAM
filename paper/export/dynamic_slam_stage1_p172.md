# Dynamic SLAM Stage 1 Replication — P172

**Phase:** P172-stage1-two-session-droid-replication  
**Date:** 2026-05-09  
**Method:** DROID-SLAM 64-frame with global BA, semantic frontend masks (fork/forklift labels), no temporal propagation, no dilation  
**Tool:** evo APE/RPE (translation part, SE(3) Umeyama alignment)  
**Hardware:** NVIDIA GeForce RTX 3060, CUDA 11.8, PyTorch 2.4.0

---

## Result: ✅ Replication Successful — Both Sessions Trajectory-Neutral

| Session | Date | ΔAPE (mm) | ΔRPE (mm) | Masked Frames | Result |
|---|---|---|---|---|---|
| Jun15 Aisle_CW_Run_2 | 2022-06-15 | −0.001 | 0.000 | 4/64 | ✅ Neutral |
| Jun23 Aisle_CW_Run_1 | 2022-06-23 | 0.000 | 0.000 | 4/64 | ✅ Neutral |

---

## Updated Evidence Chain

| Stage | Sessions | Configs | Neutral | Perturbed | Bounds |
|---|---|---|---|---|---|
| **P171** (single-session) | 1 (Jun15 Run1) | 12 | 7 | 5 | Mask selectivity = necessary condition |
| **P172 Stage 1** (+2 sessions) | 3 | 14 | **9** | 5 | Cross-session reproducibility confirmed |
| **P172 Stage 2** (planned) | 5 | 16 | TBD | TBD | Cross-month + Hallway not yet run |

---

## Detailed Metrics

### Jun15 Aisle_CW_Run_2 (same-day)

| Metric | Raw RGB | Masked RGB | Δ |
|---|---|---|---|
| APE RMSE (m) | 0.009537 | 0.009536 | −0.001 mm |
| APE mean (m) | 0.005915 | 0.005915 | 0.000 |
| RPE RMSE (m) | 0.015247 | 0.015247 | 0.000 |
| RPE mean (m) | 0.008301 | 0.008300 | 0.000 |

**Mask coverage:** 4/64 frames (frames 000001, 000005, 000006, 000007), max 1.49%, mean 0.045%

### Jun23 Aisle_CW_Run_1 (cross-day, 2 weeks later)

| Metric | Raw RGB | Masked RGB | Δ |
|---|---|---|---|
| APE RMSE (m) | 0.051135 | 0.051135 | 0.000 mm |
| APE mean (m) | 0.043453 | 0.043452 | 0.000 |
| RPE RMSE (m) | 0.032713 | 0.032713 | 0.000 |
| RPE mean (m) | 0.019346 | 0.019348 | 0.000 |

**Mask coverage:** 4/64 frames (frames 000004, 000005, 000006, 000007), max 1.10%, mean 0.028%

---

## Interpretation

1. **Trajectory-neutrality replicates across sessions.** Both Jun15 Run2 (same-day) and Jun23 Run1 (cross-day, 2 weeks later) produce ΔAPE ≤ 0.001 mm — effectively identical raw vs masked trajectories. The P171 single-session finding now has multi-session confirmation.

2. **Semantic frontend mask quality is consistent.** Both sessions have forklift masks concentrated in frames 1–7 (early in the 64-frame window), with per-frame coverage ≤ 1.5%. The frontend detects forklifts in similar sequence positions across different runs.

3. **Absolute APE varies across sessions.** Jun15 Run1 (P171 baseline): 0.110 m. Jun15 Run2: 0.010 m. Jun23 Run1: 0.051 m. This is expected — DROID-SLAM's absolute accuracy depends on the specific trajectory path, scene geometry, and feature distribution within each 64-frame window. The key metric is the raw-vs-masked Δ, which is consistently 0.000.

4. **Mask selectivity condition confirmed.** P171 established that aggressive mask strategies (propagation, uniform first-N) degrade DROID-SLAM. P172 confirms that our selective semantic frontend masks maintain trajectory-neutrality across sessions. This strengthens the claim that mask selectivity is the operative condition, not just a single-session artifact.

---

## What This Enables (Paper Claim Upgrade)

| Before P172 | After P172 |
|---|---|
| "7/12 configs neutral on single session" | "9/14 configs neutral across 3 sessions (same-day + cross-day)" |
| Single-session evidence only | Multi-session reproducibility confirmed |
| Remaining: all 3 sessions are Aisle_CW | No Hallway scene transfer yet |

---

## Next Steps

1. **P172 Stage 2 (cross-month + Hallway):** Jun15 Aisle_CCW (same-day opposite direction), Oct 12 Aisle session (cross-month), 1 Hallway session. These require additional GPU runs.
2. **ORB-SLAM3 cross-check:** The P171 limitation ("only DROID-SLAM tested") remains. ORB-SLAM3 would require downloading model/vocabulary files.
3. **Full 20-session replication:** Per P168b ladder, this is a separate decision after Stage 1/2 assessment.

---

*Metrics computed 2026-05-09. All data local. JSON source: `paper/evidence/dynamic_slam_stage1_p172.json`.*
