# Dynamic SLAM Full-Dataset Follow-Up Plan — P168b

**Phase:** P168b-inventory-interpretation-and-plan  
**Based on:** `outputs/torwic_full_dataset_coverage_inventory_p168.json` (P168)  
**Date:** 2026-05-09  
**Status:** Plan only — no data downloads, no SLAM runs  
**Hardware:** NVIDIA GeForce RTX 3060 (12 GB VRAM), CUDA 11.8, PyTorch 2.4.0

---

## 1. Current Reality Check

### What We Have

- **1 session with DROID-SLAM runs**: Jun 15 Aisle_CW_Run_1
- **12 config variations**, all on the same single 64-frame window
- **1 evo-evaluated config**: P132 (8-frame, Δ=0.001mm, effectively tied)
- **11 un-evaluated configs**: have `*_estimate_tum.txt` but no ATE/RPE

### What the Paper Claims

> "10 DROID-SLAM configurations all produce trajectory-neutral results (|ΔATE| < 0.1 mm)"

**Gap**: This claim covers 10 mask-mode variations but on ONE session. The paper does NOT claim across-session, across-date, or across-route dynamic SLAM evidence. The claim is honest if scoped to "single-session 10-config negative result" — but the current wording may imply broader coverage.

### What We Need for a Stronger Paper

| Evidence Level | Description | Sessions Needed |
|---|---|---|
| **Minimal defensible** | Same-day replication + cross-day + evo for all configs | 2–3 |
| **Solid T-RO** | Temporal diversity (3 dates) + route diversity (CCW/CW) | 5–7 |
| **Exemplary** | Full Aisle coverage + Hallway negative control | 10–12 |
| **Benchmark-grade** | Full 20-session matrix | 20 |

---

## 2. Session Priority Tiers

### Tier 0: Already Done

| Session | Frames | Why |
|---|---|---|
| Jun 15 Aisle_CW_Run_1 | 1,114 | ✅ 12 configs, 1 evo-evaluated |

### Tier 1 (P0): Minimum Add — 2 Sessions

These are the smallest addition that would make the paper's dynamic SLAM claim credible as **cross-session** rather than single-session.

| # | Session | Frames | Rationale |
|---|---|---|---|
| **T1a** | **Jun 15 Aisle_CW_Run_2** | 1,124 | Same-day, same-route, different run. Closest replication. If Δ≈0 here too, the single-session result replicates. |
| **T1b** | **Jun 23 Aisle_CW_Run_1** | 1,037 | Cross-day (8 days later), same route. Tests temporal stability of the negative result. |

**Why these two**: They form the minimal temporal axis — same-day replication (T1a) and cross-day generalization (T1b) — requiring only 2 additional DROID-SLAM runs.

### Tier 2 (P1): Core Evidence — 5 More Sessions (7 Total)

| # | Session | Frames | Rationale |
|---|---|---|---|
| **T2a** | Jun 23 Aisle_CW_Run_2 | 1,059 | Cross-day CW Run 2 — completes Jun 23 CW pair |
| **T2b** | Oct 12 Aisle_CW | 1,092 | Cross-month (4 months) — tests long-term stability of negative result |
| **T2c** | Jun 15 Aisle_CCW_Run_1 | 1,136 | Opposite direction (CCW) — tests whether forklift prevalence depends on direction |
| **T2d** | Oct 12 Aisle_CCW | 915 | Cross-month CCW — completes temporal + directional matrix |
| **T2e** | Jun 15 Hallway_Full_CW | 2,511 | Hallway negative control (no forklifts) — tests whether DROID-SLAM is trajectory-neutral even where mask is empty |

**Tier 2 design rationale**: Completes a 2×3 matrix (2 directions × 3 dates) plus 1 Hallway negative control. This is what a T-RO reviewer would expect for a "systems and methodology" paper.

### Tier 3 (P2): Full Aisle + Hallway — 10 More Sessions (17 Total)

All remaining sessions. Completes:
- Full 3-date × 2-direction Aisle matrix with both runs where available
- All 10 Hallway sessions as negative controls

| # | Session | Frames | Category |
|---|---|---|---|
| T3a | Jun 15 Aisle_CCW_Run_2 | 1,238 | Aisle CCW |
| T3b | Jun 23 Aisle_CCW_Run_1 | 1,066 | Aisle CCW (no frontend yet) |
| T3c | Jun 23 Aisle_CCW_Run_2 | 1,156 | Aisle CCW (no frontend yet) |
| T3d | Jun 15 Hallway_Full_CCW | 2,539 | Hallway |
| T3e | Jun 15 Hallway_Straight_CCW | 2,197 | Hallway |
| T3f | Jun 23 Hallway_Straight_CCW | 1,972 | Hallway |
| T3g | Jun 23 Hallway_Straight_CW | 1,936 | Hallway |
| T3h | Oct 12 Hallway_Full_CW_Run_1 | 2,318 | Hallway |
| T3i | Oct 12 Hallway_Full_CW_Run_2 | 2,320 | Hallway |
| T3j | Oct 12 Hallway_Straight_CCW | 1,883 | Hallway |
| T3k | Oct 12 Hallway_Straight_CW | 1,810 | Hallway |

Note: Jun 23 Hallway_Full_CW (2,320f) already counted as Hallway negative control in T2e; if replaced by a different Hallway session, adjust.

### Tier 4 (P3): Full 20-Session Benchmark

All remaining sessions without exception. Adds the last 2 Hallway sessions not covered above.

---

## 3. Mask Coverage Scan Strategy

### Purpose

Before running DROID-SLAM on a new session, we should know:
1. How many frames contain dynamic objects (forklifts)?
2. What percentage of frame area is dynamic?
3. Which frames have the highest dynamic coverage?

This determines whether a session is "forklift-rich" (high coverage, worth running many mask configs on) or "forklift-poor" (useful as a negative replication).

### Method

**For Aisle sessions** (expected to have forklifts):
1. Scan `frontend_output/` for `state == "dynamic_agent"` detections
2. For each frame with dynamic detections, compute mask pixel count ÷ total frame pixels
3. Output: per-frame dynamic coverage list + summary statistics

**For Hallway sessions** (expected forklift-free):
1. Quick verification scan only — confirm 0 dynamic_agent detections
2. No detailed coverage analysis needed if confirmed

### Mask Scan Batch (Pre-DROID)

| Priority | Sessions | Effort | Purpose |
|---|---|---|---|
| **Before T1** | T1a, T1b | ~5 min | Confirm forklift presence in repl/cross-day sessions |
| **Before T2** | T2a–T2e | ~15 min | Full coverage analysis across temporal + directional axes |
| **Before T3** | T3a–T3k | ~30 min | Complete matrix |

### Quick-Check Heuristic

Instead of running full mask coverage on all 20 sessions upfront, we can use a cheap proxy: scan the existing frontend `observation_output/` for `state == "dynamic_agent"` labels. This is already computed during frontend processing and merely needs aggregation.

---

## 4. DROID-SLAM Batch Run Plan

### Runtime Estimate per Session

Based on P132/P134 experience on RTX 3060:

| Component | 64-frame | 128-frame | Full session (~1000f) |
|---|---|---|---|
| RGB → DROID trajectory (raw) | ~3 min | ~6 min | ~45 min (windowed) |
| RGB → DROID trajectory (masked) | ~3 min | ~6 min | ~45 min (windowed) |
| evo APE + RPE | <1 min | <1 min | <1 min |
| **Total per session (raw+masked pair)** | **~7 min** | **~13 min** | **~90 min** |

**Windowing strategy for full sessions**: DROID-SLAM can process continuous sequences natively. For a 1000-frame session, we should:
1. Run the full sequence (not just 64-frame window)
2. Extract the same window for direct comparison with existing 64-frame results
3. Report both full-trajectory and window-matched ATE/RPE

### Minimal Batch Plan (Tier 1: 2 Sessions)

```
Batch: T1-minimal
Sessions: 2 (Jun 15 Aisle_CW_Run_2 + Jun 23 Aisle_CW_Run_1)
Configs per session: raw + masked (baseline only)
Total DROID runs: 4 (2 sessions × 2 modes)
Estimated GPU time: ~30 min
Disk output: ~2 MB per session (trajectory + evo reports)

Pre-requisites:
  - Mask coverage scan on both sessions (5 min)
  - Input pack creation: raw/masked RGB for 64-frame window + groundtruth (10 min)
```

### Core Batch Plan (Tier 2: 5 Sessions)

```
Batch: T2-core
Sessions: 5 (T2a–T2e)
Configs per session: raw + masked (baseline) + semantic mask (3 modes)
Total DROID runs: 15 (5 sessions × 3 modes)
Estimated GPU time: ~2 hours
Disk output: ~10 MB

Include: mask coverage scan + input pack creation for all 5 sessions
```

### Full Batch Plan (Tier 3+: 12 Sessions)

```
Batch: T3-full
Sessions: 12 (T3a–T3k minus overlaps)
Configs per session: raw + masked (2 modes, Hallway may be raw-only)
Total DROID runs: ~18 (Aisle: 3 modes × N; Hallway: 1 mode × N)
Estimated GPU time: ~3 hours
Disk output: ~20 MB
```

### Recommended Staged Execution

| Stage | Sessions | Configs/Session | Runs | Time | Paper Upgrade |
|---|---|---|---|---|---|
| **Stage 0** | 0 (already done) | 12 on T0 | — | — | Single-session negative result |
| **Stage 1** | T1a, T1b (2) | raw + masked | 4 | ~30 min | Same-day repl + cross-day → "cross-session negative result" |
| **Stage 2** | T2a–T2e (5) | raw + masked | 10 | ~1.5 hr | Temporal + directional + Hallway ctrl → "multi-condition negative result" |
| **Stage 3** | Remaining Aisle (3) | raw + masked | 6 | ~45 min | Full Aisle matrix → "systematic negative-result study" |
| **Stage 4** | Remaining Hallway (9) | raw only | 9 | ~1 hr | Full Hallway → "scene-transfer negative control" |

**Total to full coverage**: ~4 hours GPU time, 29 additional DROID-SLAM runs.

---

## 5. GPU / Time / Failure Risk

### GPU Constraints

| Factor | Details |
|---|---|
| **GPU** | NVIDIA GeForce RTX 3060, 12 GB VRAM |
| **DROID-SLAM VRAM** | ~4–6 GB for 64-frame window; ~10 GB for full session |
| **Concurrent runs** | NOT possible — DROID-SLAM uses full GPU |
| **Cooling** | Consumer GPU — sustained multi-hour runs need monitoring |
| **Power** | ~170W under DROID-SLAM load |

### Time Budget

| Plan | Sessions | GPU Hours | Wall Clock |
|---|---|---|---|
| **Stage 1 only** | 2 | 0.5 hr | ~1 hr (with prep) |
| **Stages 1+2** | 7 | 2 hr | ~3 hr |
| **Stages 1+2+3** | 10 | 3 hr | ~4 hr |
| **Full (all 4 stages)** | 19 | 4 hr | ~6 hr |

### Failure Modes and Mitigations

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| **DROID-SLAM OOM on full session** | Medium | Cannot process long sequences | Fall back to 64/128-frame window extraction; document full-session limit |
| **GT trajectory format mismatch** | Low | evo cannot compute ATE | Pre-validate TUM format; have format converter ready |
| **Mask coverage = 0% for some Aisle sessions** | Low–Medium | Session has no forklifts → not useful for mask-mode study but useful as negative replication | If 0%, run raw-only as additional negative control |
| **CUDA/cuDNN version conflict** | Low | DROID-SLAM won't run | Current env (tram, torch 2.4.0+cu118) is verified working |
| **Disk space** | Low | 20 sessions × 2MB = 40MB total output | Negligible |
| **Session-specific DROID failure** | Low-Medium | Individual session produces NaN/garbage trajectory | Skip session; document as DROID-SLAM failure, not our method failure |

---

## 6. Claim Upgrade Roadmap

### Current Paper Claim

> "10 DROID-SLAM configurations on one session → all trajectory-neutral (|ΔATE| < 0.1 mm)"

**Truth value**: True for the single session tested.  
**Weakness**: Reviewer will ask "what about other sessions/dates/routes?"

### Claim Upgrade Ladder

| Stage | Evidence Added | Upgraded Claim |
|---|---|---|
| **Stage 0** (current) | 1 session, 12 configs | "Single-session 10-config negative result: |ΔATE| < 0.1 mm on Jun 15 Aisle_CW_Run_1" |
| **Stage 1** | +2 sessions (same-day repl + cross-day) | "Cross-session negative result: replicated on same-day different-run (Δ < 0.1 mm) and cross-day (8 days, Δ < 0.1 mm)" |
| **Stage 2** | +5 sessions (temporal + directional + Hallway) | "Multi-condition negative-result study: trajectory-neutral across 3 dates, 2 directions, and 1 Hallway negative control" |
| **Stage 3** | Full Aisle (10 sessions) | "Systematic Aisle negative-result study: 10 sessions × 3 dates × 2 directions — all trajectory-neutral" |
| **Stage 4** | Full 20 sessions | "Complete 20-session TorWIC dynamic SLAM evaluation: forklift masking is trajectory-neutral in warehouse environment (<2% frame coverage)" |

### What Claim Does NOT Upgrade

Regardless of how many sessions we run:

> **We never claim dynamic masking IMPROVES ATE/RPE.** The claim is always "the effect is below measurement noise" — i.e., trajectory-neutral, not trajectory-improving. More sessions strengthen the negative-result confidence; they never convert it into a positive-result claim.

---

## 7. Batch Manifest Draft (Stage 1)

### Input Pack Structure (reuse from P132/P134)

Each session needs:

```
outputs/dynamic_slam_backend_input_pack_{session_id}/
├── raw/
│   └── rgb.txt          ← TUM-format RGB associations
├── masked/
│   └── rgb.txt          ← TUM-format RGB associations (with mask overlay)
├── groundtruth.txt       ← TUM-format ground truth poses
└── input_manifest.json   ← metadata
```

### Stage 1 Execution Script Outline

```bash
# For each session in T1a, T1b:
# 1. Mask coverage scan (5 min prep)
python tools/scan_mask_coverage.py \
  --session-root data/TorWIC_SLAM_Dataset/{date}/{route} \
  --frontend-output outputs/torwic_*__{date}__{route}/frontend_output \
  --output outputs/mask_coverage_{session_id}.json

# 2. Select 64-frame window with highest dynamic coverage
python tools/select_dynamic_window.py \
  --coverage outputs/mask_coverage_{session_id}.json \
  --window-size 64 \
  --output outputs/window_{session_id}_64.json

# 3. Create input pack (raw + masked + gt)
python tools/create_droid_input_pack.py \
  --session-root data/TorWIC_SLAM_Dataset/{date}/{route} \
  --window outputs/window_{session_id}_64.json \
  --output outputs/dynamic_slam_backend_input_pack_{session_id}

# 4. Run DROID-SLAM raw and masked
python tools/run_droid_slam.py \
  --input outputs/dynamic_slam_backend_input_pack_{session_id}/raw/rgb.txt \
  --output outputs/droid_backend_{session_id}_raw/ \
  --global-ba

python tools/run_droid_slam.py \
  --input outputs/dynamic_slam_backend_input_pack_{session_id}/masked/rgb.txt \
  --output outputs/droid_backend_{session_id}_masked/ \
  --global-ba

# 5. evo evaluation
evo_ape tum \
  outputs/dynamic_slam_backend_input_pack_{session_id}/groundtruth.txt \
  outputs/droid_backend_{session_id}_raw/raw_estimate_tum.txt \
  --save_results outputs/droid_backend_{session_id}_raw/

evo_ape tum \
  outputs/dynamic_slam_backend_input_pack_{session_id}/groundtruth.txt \
  outputs/droid_backend_{session_id}_masked/masked_estimate_tum.txt \
  --save_results outputs/droid_backend_{session_id}_masked/
```

### Stage 1 Deliverable

```
outputs/
├── mask_coverage_T1a_T1b_summary.json
├── dynamic_slam_backend_input_pack_2022-06-15__Aisle_CW_Run_2/
├── dynamic_slam_backend_input_pack_2022-06-23__Aisle_CW_Run_1/
├── droid_backend_2022-06-15__Aisle_CW_Run_2_raw/
├── droid_backend_2022-06-15__Aisle_CW_Run_2_masked/
├── droid_backend_2022-06-23__Aisle_CW_Run_1_raw/
├── droid_backend_2022-06-23__Aisle_CW_Run_1_masked/
└── stage1_cross_session_summary.json  ← ΔATE comparison table
```

---

## 8. Recommended Execution Order

### Immediate Next (this wake cycle or next)

**Priority 1: Fix the known gap — evo evaluation for 11 pending configs**
- Already have `*_estimate_tum.txt` files — just need to run `evo_ape`
- Effort: ~5 min, no GPU needed
- Upgrades the 10-config claim from "visual" to "metric"

### Then: Stage 1 (2 new sessions)

| Step | Effort | Dependency |
|---|---|---|
| 1. Mask coverage scan T1a+T1b | 5 min | Frontend outputs exist |
| 2. Input pack creation | 10 min | Step 1 (window selection) |
| 3. DROID-SLAM raw+masked (4 runs) | 30 min GPU | Step 2 |
| 4. evo evaluation (4 reports) | 2 min | Step 3 |
| 5. Summary table | 5 min | Step 4 |
| **Total Stage 1** | **~1 hr** | |

### Then: Decision Point

After Stage 1:
- If ΔATE ≈ 0 on both new sessions → proceed to Stage 2 (strong evidence)
- If ΔATE >> 0 on either session → investigate; potential blocker; do not proceed blindly

---

## 9. Paper Integration Plan

### Where Results Go

| Evidence | Paper Section | Figure/Table |
|---|---|---|
| Single-session 10-config (current) | §VII.F | Fig 4 (summary) + Table 6 |
| Stage 1 cross-session | §VII.F addendum | Table 7 (cross-session ΔATE matrix) |
| Stage 2 multi-condition | §VII.F expanded | Fig 5 (temporal+directional ΔATE heatmap) |
| Stage 3+ full coverage | §VII.F or Appendix | Supplementary §S4 expanded |

### When to Update the Manuscript

| Milestone | Manuscript Action |
|---|---|
| After Priority 1 (evo for 11 configs) | Update main.tex §VII.F: replace "visual overlay" with "evo ATE/RPE" |
| After Stage 1 (2 new sessions) | Add cross-session paragraph + table to §VII.F |
| After Stage 2 (7 total sessions) | Rewrite §VII.F as multi-condition study; move single-session detail to supplement |

---

## 10. Decision Matrix

### What to Run and When

| Option | Sessions | GPU Time | Paper Impact | Risk |
|---|---|---|---|---|
| **A: Priority 1 only** (evo existing) | 0 new | 0 min | Low — fills small gap | None |
| **B: A + Stage 1** (minimal) | 2 new | 30 min | Medium — cross-session evidence | Low |
| **C: A + B + Stage 2** (T-RO ready) | 7 new | 2 hr | High — multi-condition evidence | Medium (GPU time) |
| **D: Full 20-session** | 19 new | 4 hr | Maximum — benchmark-grade | Medium (power/cooling) |

### Recommendation

**Start with A (Priority 1: evo for 11 configs), then proceed to B (Stage 1: 2 sessions).** Stop and assess after Stage 1. If Δ≈0 on both new sessions, the cross-session claim is solid enough to submit with "Stage 2 deferred to revision." If Δ≠0, investigate before expanding.

The faster path to submission-ready is A+B, which takes ~1 hour and gives cross-session evidence. C and D can be deferred to the revision cycle if reviewers ask.

---

*Plan generated 2026-05-09. No SLAM runs, no data downloads performed. All estimates based on P132/P134 DROID-SLAM runtime data on RTX 3060.*
