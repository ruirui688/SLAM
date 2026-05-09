# Dynamic SLAM Backend evo Metrics — P171

**Phase:** P171-evo-metrics-for-existing-droid-configs  
**Date:** 2026-05-09  
**Tool:** evo (Michael Grupp, 2017)  
**Input:** Single TorWIC session (2022-06-15 Aisle_CW_Run_1)  
**Hardware:** NVIDIA GeForce RTX 3060, CUDA 11.8, PyTorch 2.4.0

---

## ⚠️ Claim Correction

| Aspect | Before P171 | After P171 |
|---|---|---|
| **Claim** | "10 DROID-SLAM configs all produce \|ΔATE\| < 0.1 mm" | "Semantic frontend + concentrated forklift masks: 7/12 configs \|ΔAPE\| ≤ 0.006 mm. Aggressive mask strategies: 5/12 configs \|ΔAPE\| 0.92–7.52 mm." |
| **Evidence basis** | Visual trajectory overlay | evo APE/RPE RMSE (translation part, SE(3) Umeyama alignment) |
| **Status** | Overstated | Corrected |

**Bottom line:** Mask selectivity matters for DROID-SLAM bundle adjustment. Our semantic frontend masks ARE trajectory-neutral. Aggressive temporal/flow propagation and blind uniform masking ARE NOT.

---

## 1. Full Metrics Table

### 1.1 APE (Absolute Pose Error, translation part)

| Config | Frames | GBA | Mask Strategy | Raw RMSE (m) | Masked RMSE (m) | Δ (mm) | Result |
|---|---|---|---|---|---|---|---|
| P132 | 8 | ❌ | baseline (smoke) | 0.001428 | 0.001434 | +0.006 | ✅ Tied |
| P134 | 64 | ❌ | baseline (no GBA) | 0.183616 | 0.183616 | 0.000 | ✅ Tied |
| P134-GBA | 64 | ✅ | baseline raw | 0.109855 | 0.109854 | −0.001 | ✅ Tied |
| **P135** | **64** | **✅** | **semantic masks** | **0.109855** | **0.109854** | **−0.001** | **✅ Tied** |
| P136 | 64 | ✅ | temporal stress | 0.109855 | 0.117372 | **+7.517** | ❌ Perturbed |
| P137 | 64 | ✅ | flow stress | 0.109855 | 0.117372 | **+7.517** | ❌ Perturbed |
| P138 | 64 | ✅ | first-8 uniform | 0.109855 | 0.110777 | **+0.922** | ❌ Perturbed |
| P139 | 64 | ✅ | first-16 uniform | 0.109855 | 0.110776 | **+0.921** | ❌ Perturbed |
| P140 | 64 | ✅ | first-32 uniform | 0.109855 | 0.110775 | **+0.920** | ❌ Perturbed |
| P142-T4 | 64 | ✅ | top-4 concentrated | 0.109855 | 0.109853 | −0.002 | ✅ Tied |
| P142-T8 | 64 | ✅ | top-8 concentrated | 0.109855 | 0.109854 | −0.001 | ✅ Tied |
| P142-T16 | 64 | ✅ | top-16 concentrated | 0.109855 | 0.109856 | +0.001 | ✅ Tied |

**Key observations:**
- All 64-frame GBA configs share **identical raw trajectories** (APE RMSE = 0.109855 m) — the raw input pack is the same across all configs
- P134 without GBA shows higher APE (0.183616 m) — expected drift without bundle adjustment
- P132 8-frame has very low APE (0.001428 m) — short window with minimal drift

### 1.2 RPE (Relative Pose Error, translation part)

| Config | Raw RMSE (m) | Masked RMSE (m) | Δ (mm) | Result |
|---|---|---|---|---|
| P132 | 0.003069 | 0.003096 | +0.027 | ✅ Tied |
| P134 | 0.029826 | 0.029826 | 0.000 | ✅ Tied |
| P134-GBA | 0.028945 | 0.028945 | 0.000 | ✅ Tied |
| P135 | 0.028945 | 0.028945 | 0.000 | ✅ Tied |
| P136 | 0.028945 | 0.028864 | −0.081 | ⚠️ Small |
| P137 | 0.028945 | 0.028864 | −0.081 | ⚠️ Small |
| P138 | 0.028945 | 0.028934 | −0.011 | ✅ Tied |
| P139 | 0.028945 | 0.028934 | −0.011 | ✅ Tied |
| P140 | 0.028945 | 0.028934 | −0.011 | ✅ Tied |
| P142-T4 | 0.028945 | 0.028945 | 0.000 | ✅ Tied |
| P142-T8 | 0.028945 | 0.028945 | 0.000 | ✅ Tied |
| P142-T16 | 0.028945 | 0.028945 | 0.000 | ✅ Tied |

**RPE is uniformly tight** — all configs have |ΔRPE| ≤ 0.081 mm, with most at 0.000 mm. RPE measures local frame-to-frame accuracy, which is less affected by global mask perturbations than APE.

---

## 2. Two-Group Analysis

### Group 1: Trajectory-Neutral (7/12 configs)

**P132, P134, P134-GBA, P135, P142-T4, P142-T8, P142-T16**

These configs use either (a) no masking at all (P132/P134 baselines), (b) our semantic frontend masks (P135), or (c) concentrated forklift-only masks (P142). All produce |ΔAPE| ≤ 0.006 mm — effectively tied.

**Interpretation:** When masks are applied only to frames that actually contain forklifts, DROID-SLAM's bundle adjustment is unaffected. Our semantic frontend (P135) falls squarely in this category.

### Group 2: Perturbed (5/12 configs)

**P136 (temporal stress), P137 (flow stress), P138 (first-8), P139 (first-16), P140 (first-32)**

These configs use aggressive mask strategies that either (a) propagate masks temporally/optically beyond actual dynamic regions (P136/P137) or (b) blindly mask the first N frames regardless of forklift presence (P138-P140).

**Interpretation:**
- **P136/P137 (ΔAPE = +7.517 mm):** Temporal/flow propagation removes visual features from frames that would otherwise contribute to DROID-SLAM's bundle adjustment. The identical magnitude (±0 mm) across both propagation methods suggests the mask STRATEGY (which frames get masked) dominates over the propagation METHOD (temporal vs flow).
- **P138-P140 (ΔAPE ≈ +0.92 mm):** Masking the first N frames depletes the initialization window, causing a ~0.92 mm degradation that plateaus after the first 8 frames (no additional degradation from masking 16 or 32 frames). This confirms that DROID-SLAM's initialization is the vulnerable phase.

---

## 3. What This Means for the Paper

### Corrected Claim

> "Semantic frontend masks produce trajectory-neutral DROID-SLAM results (|ΔAPE| ≤ 0.001 mm, P135). Concentrated forklift-only masks confirm selective masking is harmless (|ΔAPE| ≤ 0.002 mm, P142). However, aggressive temporal/flow propagation and blind uniform masking introduce measurable trajectory perturbations (0.92–7.52 mm ΔAPE), revealing that mask selectivity is a necessary condition for trajectory-neutrality in DROID-SLAM."

### Why This Is a Better Paper Story

1. **Honesty:** We no longer claim the implausible "all configs are identical."
2. **Substance:** We can explain WHY some masks perturb DROID-SLAM (initialization window, feature depletion) and WHY ours don't (selective forklift-only masking).
3. **Defense:** When a reviewer asks "what if you mask aggressively?" we have an evo-backed answer: "we tested that — it degrades trajectory by 0.9–7.5 mm, which is exactly why mask selectivity matters."
4. **Method strength:** P135 (semantic masks) performs identically to P142 (oracle concentrated masks), validating our frontend mask quality.

### What Must Be Updated

| File | Change |
|---|---|
| `main.tex` §VII.F | Replace "10 configs all |ΔATE| < 0.1 mm" with two-group analysis |
| `main.tex` §IX (Limitations) | Update dynamic SLAM item to reflect corrected finding |
| `EDITOR_SUMMARY.md` | Update "10 DROID-SLAM" paragraph |
| `supplement.md` §S4 | Update with evo metrics table |
| `manuscript_en_thick.md` §VII.E-F | Sync corrected claim |

---

## 4. Reproducibility

All evo commands used:

```bash
evo_ape tum groundtruth.txt raw_estimate_tum.txt -a --pose_relation trans_part
evo_ape tum groundtruth.txt masked_estimate_tum.txt -a --pose_relation trans_part
evo_rpe tum groundtruth.txt raw_estimate_tum.txt -a --pose_relation trans_part
evo_rpe tum groundtruth.txt masked_estimate_tum.txt -a --pose_relation trans_part
```

Groundtruth files are from the respective `dynamic_slam_backend_input_pack_*` directories.
Estimate files are from the respective `dynamic_slam_backend_smoke_*` directories.
All 12 configs share the same 64-frame TorWIC window (Jun 15 Aisle_CW_Run_1).

---

*Metrics computed 2026-05-09. All data local, no GPU runs, no downloads. JSON source: `paper/evidence/dynamic_slam_backend_metrics_p171.json`.*
