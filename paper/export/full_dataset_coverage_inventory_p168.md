# TorWIC Full Dataset Coverage Inventory — P168

**Phase:** P168-full-dataset-coverage-inventory  
**Date:** 2026-05-09  
**Status:** Complete — local inventory only, no downloads, no long runs

---

## 1. Executive Summary

| Metric | Value |
|---|---|
| **Total sessions downloaded** | 20 |
| **Total RGB frames** | 32,743 |
| **Dates covered** | 3 (Jun 15, Jun 23, Oct 12, 2022) |
| **Aisle sessions** | 10 (1,094–1,238 frames each) |
| **Hallway sessions** | 10 (1,810–2,539 frames each) |
| **GT trajectory available** | 20/20 ✅ |
| **Sessions with semantic frontend** | 18/20 ⚠️ (Jun 23 Aisle CCW Run 1/2 missing) |
| **Sessions with DROID-SLAM backend** | 1/20 🔴 |
| **DROID-SLAM config variations** | 12 (all on same session) |
| **DROID configs with evo ATE/RPE** | 1/12 ⚠️ (P132 only) |

### Critical Claim Boundary

> **P135–P143 dynamic SLAM backend runs are a bounded 64-frame negative-result chain on a SINGLE TorWIC session (Jun 15 Aisle_CW_Run_1). This is NOT a full dataset benchmark. The 10-configuration "all produce |ΔATE| < 0.1 mm" claim in the paper is based on trajectory visual overlay of 11 un-evaluated 64-frame estimate_tum.txt outputs. Only P132 (8-frame) has formal evo ATE/RPE evaluation (raw: 0.0012m, masked: 0.0012m, Δ = 1×10⁻⁶ m).**

---

## 2. Data Sessions

### 2.1 Aisle Sessions (10)

| # | Date | Route | Frames | Direction | Semantic | DROID |
|---|---|---|---|---|---|---|
| 1 | Jun 15 | Aisle_CCW_Run_1 | 1,136 | CCW | ✅ same-day/cross-day/cross-month | ❌ |
| 2 | Jun 15 | Aisle_CCW_Run_2 | 1,238 | CCW | ✅ same-day/cross-day/cross-month | ❌ |
| 3 | Jun 15 | **Aisle_CW_Run_1** | **1,114** | **CW** | ✅ same-day/cross-day/cross-month | **✅ ALL 12 configs** |
| 4 | Jun 15 | Aisle_CW_Run_2 | 1,124 | CW | ✅ same-day/cross-day/cross-month | ❌ |
| 5 | Jun 23 | Aisle_CCW_Run_1 | 1,066 | CCW | ❌ | ❌ |
| 6 | Jun 23 | Aisle_CCW_Run_2 | 1,156 | CCW | ❌ | ❌ |
| 7 | Jun 23 | Aisle_CW_Run_1 | 1,037 | CW | ✅ cross-day/cross-month | ❌ |
| 8 | Jun 23 | Aisle_CW_Run_2 | 1,059 | CW | ✅ cross-day/cross-month | ❌ |
| 9 | Oct 12 | Aisle_CCW | 915 | CCW | ✅ cross-month | ❌ |
| 10 | Oct 12 | Aisle_CW | 1,092 | CW | ✅ cross-month | ❌ |

**Aisle total:** 10,937 frames across 10 sessions.

### 2.2 Hallway Sessions (10)

| # | Date | Route | Frames | Direction | Semantic | DROID |
|---|---|---|---|---|---|---|
| 11 | Jun 15 | Hallway_Full_CCW | 2,539 | CCW | ✅ batch2 | ❌ |
| 12 | Jun 15 | Hallway_Full_CW | 2,511 | CW | ✅ batch2 | ❌ |
| 13 | Jun 15 | Hallway_Straight_CCW | 2,197 | CCW | ✅ batch2 | ❌ |
| 14 | Jun 23 | Hallway_Full_CW | 2,320 | CW | ✅ batch2 | ❌ |
| 15 | Jun 23 | Hallway_Straight_CCW | 1,972 | CCW | ✅ batch2 | ❌ |
| 16 | Jun 23 | Hallway_Straight_CW | 1,936 | CW | ✅ batch2 | ❌ |
| 17 | Oct 12 | Hallway_Full_CW_Run_1 | 2,318 | CW | ✅ batch2 | ❌ |
| 18 | Oct 12 | Hallway_Full_CW_Run_2 | 2,320 | CW | ✅ batch2 | ❌ |
| 19 | Oct 12 | Hallway_Straight_CCW | 1,883 | CCW | ✅ batch2 | ❌ |
| 20 | Oct 12 | Hallway_Straight_CW | 1,810 | CW | ✅ batch2 | ❌ |

**Hallway total:** 21,806 frames across 10 sessions. All 10 have batch2 8/8 frame coverage.

---

## 3. Semantic Frontend Coverage

### Protocol Map

| Protocol | Sessions | Temporal Gap | Purpose |
|---|---|---|---|
| **same-day Aisle** | 4 (Jun 15 CCW+CW) | minutes | Same-condition baseline |
| **cross-day Aisle** | 4 (Jun 15 CW → Jun 23 CW) | 8 days | Short-term revisit stability |
| **cross-month Aisle** | 6 (Jun + Oct CW/CCW) | ~4 months | Long-term map maintenance |
| **Hallway scene-transfer** | 10 (all dates, all Hallway routes) | 0–4 months | Scene-transfer generalization |

### Frontend Output Structure

Each covered session has:
- `frontend_output/` — Grounding DINO + SAM2 detections
- `observation_output/` — Per-frame observation records
- `tracklet_output/` — Track association across frames
- `map_output/` — Map-object candidate generation

### Gaps

- **Jun 23 Aisle_CCW_Run_1/2:** No bundle frontend output. These are CCW Aisle runs — the protocol focused on CW pairs for cross-day and cross-month.
- **Version drift:** 36 frontend output directories exist; `bundle_v1` + `richer_recomputed` are canonical.

---

## 4. DROID-SLAM Backend Coverage

### Single-Session Reality

**All 12 DROID-SLAM config runs use the same input: Jun 15 Aisle_CW_Run_1.**

| Config | Frames | GBA | Mask Mode | Has evo |
|---|---|---|---|---|
| p132 | 8 | ❌ | baseline raw | ✅ (Δ=0.001mm) |
| p134_64 | 64 | ❌ | baseline raw | ❌ |
| p134_64_gba | 64 | ✅ | baseline raw | ❌ |
| p135_sem | 64 | ✅ | semantic mask | ❌ |
| p136_temporal | 64 | ✅ | temporal stress | ❌ |
| p137_flow | 64 | ✅ | flow stress | ❌ |
| p138_first8 | 64 | ✅ | first 8 real masks | ❌ |
| p139_first16 | 64 | ✅ | first 16 real masks | ❌ |
| p140_first32 | 64 | ✅ | first 32 real masks | ❌ |
| p142_top4 | 64 | ✅ | top 4 concentrated | ❌ |
| p142_top8 | 64 | ✅ | top 8 concentrated | ❌ |
| p142_top16 | 64 | ✅ | top 16 concentrated | ❌ |

### What's Missing

1. **No evo evaluation for 11/12 configs.** The `*_estimate_tum.txt` files exist but ATE/RPE has not been computed.
2. **No multi-session comparison.** No DROID-SLAM run on any other session — not even Jun 15 Aisle_CW_Run_2 (same day, same route, different run).
3. **No Hallway DROID-SLAM runs.** 0/10 Hallway sessions have backend coverage.
4. **No comparison against published baselines.** ORB-SLAM3, RTAB-Map, and other SLAM backends were not run.

### What's Present

- ✅ P132 8-frame smoke: raw vs masked ATE/RPE evaluated (Δ ≈ 0)
- ✅ 11 64-frame configs: estimate_tum.txt outputs for visual overlay comparison
- ✅ All configs: DROID-SLAM stdout preserved for diagnostic review
- ✅ Input packs: raw/masked RGB frames + groundtruth.txt available

---

## 5. Gaps and Blockers

| ID | Severity | Description | Paper Impact |
|---|---|---|---|
| **GAP-DROID-001** | 🔴 HIGH | 12 configs on 1/20 sessions | Paper claim scoped to single-window negative-result |
| **GAP-DROID-002** | 🔴 HIGH | 1/12 configs have evo eval | Trajectory claims based on visual overlay, not metrics |
| **GAP-DROID-003** | 🟡 MEDIUM | No Hallway DROID-SLAM runs | Dynamic SLAM evidence is Aisle-only |
| **GAP-DROID-004** | 🟡 MEDIUM | No published SLAM baselines | Documented in Limitations item #5 |
| **GAP-FRONTEND-001** | ⚪ LOW | 2/20 Aisle sessions no frontend | Jun 23 CCW runs excluded from object protocols |
| **GAP-DATA-001** | ⚪ LOW | Single-site dataset | Documented in Limitations item #2 |

---

## 6. Readiness Assessment

| Dimension | Status | Score |
|---|---|---|
| Data download completeness | 20/20 sessions, 32,743 frames, all GT | ✅ |
| Semantic frontend coverage | 18/20 sessions (Aisle: 8/10, Hallway: 10/10) | ⚠️ |
| DROID-SLAM backend coverage | 1/20 sessions, 12 config variations | 🔴 |
| ATE/RPE evaluation | 1/12 configs | 🔴 |
| Claim safety (current paper) | Bounded to single-window negative-result | ✅ |
| Multi-session evidence readiness | Not ready | 🔴 |

### Next Actions (Lowest Effort First)

| Priority | Action | Effort | Impact |
|---|---|---|---|
| **1** | Run evo ape/rpe on 11 remaining 64-frame configs | ~5 min | Upgrades all claims from "visual" to "metric" |
| **2** | Run DROID-SLAM on Jun 15 Aisle_CW_Run_2 (same day, different run) | ~15 min | Adds same-day replication |
| **3** | Run DROID-SLAM on 1 Hallway session | ~15 min | Extends dynamic SLAM to scene-transfer |
| **4** | Archive legacy frontend variant directories | ~5 min | Metadata clarity |

---

## 7. Cross-Reference: Paper Claims vs Reality

| Paper Claim | Actual Evidence | Gap |
|---|---|---|
| "10 DROID-SLAM configurations" | 12 configs, all on same input | ✅ Claim accurate |
| "all produce trajectory-neutral results" | 11/12 no evo eval; visual overlay only | ⚠️ Needs evo |
| "|ΔATE| < 0.1 mm" | P132: Δ=0.001mm. Others: unverified | ⚠️ Needs evo |
| "quantified boundary condition <2%" | 1.39% max observed (session-specific) | ✅ Claim accurate |
| "35 TorWIC sessions" | 20 sessions with 36 output variant dirs | ⚠️ 35 is variant-count, not session-count |
| "full parameter ablation across 27 combinations" | ✅ Cross-referenced with supplement.md §S1 | ✅ Claim accurate |
| "per-cluster provenance auditable" | ✅ All bundle_v1 outputs have per-cluster IDs | ✅ Claim accurate |

---

*Inventory generated 2026-05-09. All data is local, no downloads performed. The JSON equivalent is at `outputs/torwic_full_dataset_coverage_inventory_p168.json`.*
