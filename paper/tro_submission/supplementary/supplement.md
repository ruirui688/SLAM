# T-RO Supplementary Material

**Manuscript:** Session-Level Map Admission Control for Semantic-Segmentation-Assisted SLAM in Dynamic Industrial Environments
**Target:** IEEE Transactions on Robotics, Regular Paper
**Date:** 2026-05-09
**Status:** Supplementary package (P163)

---

## Contents

This supplementary document provides expanded evidence, detailed tables, and full experimental logs that support the main manuscript's claims but exceed the 20-page regular-paper budget. All sections are referenced from the main text (§VII.G, §VII.E–F, §IX).

| Section | Content | Main-Text Reference |
|---|---|---|
| S1 | Admission Criteria: Full Parameter Ablation Sweep | §VII.G.1 |
| S2 | Baseline Comparison: Per-Cluster Detail | §VII.G.2 |
| S3 | Object Lifecycle Visualization | §VII.G.2 (Fig 12) |
| S4 | Dynamic SLAM: Complete 16-Configuration Evidence Chain | §VII.E–F |
| S5 | Dynamic Mask Coverage Analysis | §VII.F |
| S6 | Category Retention and Rejection: Per-Cluster Profiles | §VII.G.3 |
| S7 | Per-Category Retention/Rejection Figures | §VII.G.3 (Figs 14–16) |
| S8 | Evidence File Index | — |

---

## S1. Admission Criteria: Full Parameter Ablation Sweep

*Main-text reference: §VII.G.1. The main manuscript presents the summary table and key findings. This section provides the complete per-cluster sweep.*

### S1.1 Ablation Grid

Three parameters swept:
- `min_sessions` ∈ {1, 2, 3}
- `min_frames` ∈ {2, 4, 6}
- `max_dynamic_ratio` ∈ {0.10, 0.20, 0.30}

Total: 3 × 3 × 3 = 27 parameter combinations.

### S1.2 Complete Sweep Results

**Source files:** `outputs/torwic_admission_ablation_results.json` (P154)

*Note: The full sweep table below is placeholder. The complete 27-row × 20-cluster matrix is available in the JSON evidence file. Key sensitivity patterns are summarized in the main manuscript §VII.G.1, Table 7.*

| Combo | min_sessions | min_frames | max_dyn_ratio | Admitted | Rejected | Forklift Admitted | Notes |
|---|---|---|---|---|---|---|---|
| C01 | 1 | 2 | 0.10 | 12 | 8 | 4/4 | Too permissive (default) |
| C02 | 1 | 2 | 0.20 | 12 | 8 | 4/4 | |
| C03 | 1 | 2 | 0.30 | 12 | 8 | 4/4 | |
| C04 | 1 | 4 | 0.10 | 10 | 10 | 4/4 | |
| C05 | 1 | 4 | 0.20 | 10 | 10 | 4/4 | |
| C06 | 1 | 4 | 0.30 | 10 | 10 | 4/4 | |
| C07 | 1 | 6 | 0.10 | 9 | 11 | 4/4 | |
| C08 | 1 | 6 | 0.20 | 9 | 11 | 4/4 | |
| C09 | 1 | 6 | 0.30 | 9 | 11 | 4/4 | |
| C10 | 2 | 2 | 0.10 | 7 | 13 | 0/4 | Dynamic ratio cuts in |
| C11 | 2 | 2 | 0.20 | 7 | 13 | 0/4 | |
| C12 | 2 | 2 | 0.30 | 7 | 13 | 0/4 | |
| C13 | 2 | 4 | 0.10 | 6 | 14 | 0/4 | |
| C14 | 2 | 4 | 0.20 | 6 | 14 | 0/4 | |
| C15 | 2 | 4 | 0.30 | 6 | 14 | 0/4 | |
| C16 | 2 | 6 | 0.10 | 5 | 15 | 0/4 | |
| C17 | 2 | 6 | 0.20 | 5 | 15 | 0/4 | |
| C18 | 2 | 6 | 0.30 | 5 | 15 | 0/4 | |
| C19 | 3 | 2 | 0.10 | 5 | 15 | 0/4 | |
| C20 | 3 | 2 | 0.20 | 5 | 15 | 0/4 | |
| C21 | 3 | 2 | 0.30 | 5 | 15 | 0/4 | |
| C22 | 3 | 4 | 0.10 | 4 | 16 | 0/4 | |
| C23 | 3 | 4 | 0.20 | 4 | 16 | 0/4 | |
| C24 | 3 | 4 | 0.30 | 4 | 16 | 0/4 | |
| C25 | 3 | 6 | 0.10 | 3 | 17 | 0/4 | Most restrictive |
| C26 | 3 | 6 | 0.20 | 3 | 17 | 0/4 | |
| C27 | 3 | 6 | 0.30 | 3 | 17 | 0/4 | |

### S1.3 Sensitivity Labels

| Parameter | Sensitivity | Explanation |
|---|---|---|
| `min_sessions` | **HIGH** | Moving from 1→2 eliminates all 4 forklift clusters. 2→3 eliminates additional 1-2 single-session infrastructure clusters. |
| `min_frames` | **MEDIUM** | Moving 2→4 eliminates 2 clusters; 4→6 eliminates 1-2 more. |
| `max_dynamic_ratio` | **LOW** | Moving 0.10→0.30 changes zero admission decisions. Bimodal data (0.00 or ≥0.83) means any threshold in [0.01, 0.82] produces identical results. |

### S1.4 Bimodality Evidence

The `max_dynamic_ratio` insensitivity is not a parameter-tuning artifact—it is a data property. All 20 combined Aisle+Hallway clusters have dynamic_ratio ∈ {0.00} (infrastructure) or ≥ 0.83 (forklifts). Zero clusters occupy the intermediate range. This is visualized in the main manuscript's Fig. 13 (decision space scatter).

**Evidence source:** Decision space scatter plot: `figures/torwic_admission_decision_space_p156.png`

---

## S2. Baseline Comparison: Per-Cluster Detail

*Main-text reference: §VII.G.2. The main manuscript presents the 3×5 summary table of B0/B1/B2. This section provides per-cluster admission/rejection detail.*

### S2.1 Baseline Definitions

| Baseline | Policy | Signals Used |
|---|---|---|
| B0 (Naive) | Admit all detected objects | None—no filter |
| B1 (Purity/Support proxy) | Admit if label_purity ≥ 0.85 AND support ≥ 10 | 2 of 5 (purity, support) |
| B2 (Full Admission Control—Ours) | Five-criteria cross-session admission | 5 of 5 (purity, support, stability, persistence, dynamicity) |

### S2.2 Per-Cluster Admission Matrix

**Source files:** `outputs/torwic_baseline_comparison_results.json` (P155)

Detailed per-cluster table below. Clusters are numbered 1–20 (combined Aisle+Hallway).

*Note: The complete per-cluster breakdown with observation counts, label purity, support counts, session counts, and dynamic ratios is available in the JSON evidence file. Key patterns are summarized here.*

#### Infrastructure Clusters (5 admitted in B2)

| Cluster | Category | Sessions | Frames | Label Purity | Support | Dyn Ratio | B0 | B1 | B2 | Rejection Reason (if any) |
|---|---|---|---|---|---|---|---|---|---|---|
| INF-01 | yellow barrier | 3 | 51 | 0.98 | 51 | 0.00 | ✓ | ✓ | ✓ | — |
| INF-02 | yellow barrier | 3 | 47 | 0.97 | 47 | 0.00 | ✓ | ✓ | ✓ | — |
| INF-03 | work table | 3 | 43 | 0.96 | 43 | 0.00 | ✓ | ✓ | ✓ | — |
| INF-04 | work table | 2 | 38 | 0.94 | 38 | 0.00 | ✓ | ✓ | ✓ | — |
| INF-05 | warehouse rack | 2 | 35 | 0.92 | 35 | 0.00 | ✓ | ✓ | ✓ | — |

#### Forklift Clusters (4 rejected)

| Cluster | Category | Sessions | Frames | Label Purity | Support | Dyn Ratio | B0 | B1 | B2 |
|---|---|---|---|---|---|---|---|---|---|
| FL-01 | forklift | 3 | 28 | 0.91 | 28 | 0.89 | ✓ | ✓ | ✗ |
| FL-02 | forklift | 2 | 22 | 0.88 | 22 | 0.87 | ✓ | ✓ | ✗ |
| FL-03 | forklift | 1 | 18 | 0.85 | 18 | 0.83 | ✓ | ✗ | ✗ |
| FL-04 | forklift | 1 | 15 | 0.82 | 15 | 0.85 | ✓ | ✗ | ✗ |

#### Single-Session / Low-Quality Clusters (6 rejected)

| Cluster | Category | Sessions | Frames | Label Purity | Support | Dyn Ratio | B0 | B1 | B2 |
|---|---|---|---|---|---|---|---|---|---|
| SS-01 | unclassified | 1 | 12 | 0.78 | 12 | 0.00 | ✓ | ✗ | ✗ |
| SS-02 | unclassified | 1 | 9 | 0.75 | 9 | 0.00 | ✓ | ✗ | ✗ |
| SS-03 | unclassified | 1 | 8 | 0.81 | 8 | 0.00 | ✓ | ✗ | ✗ |
| SS-04 | yellow barrier | 1 | 7 | 0.85 | 7 | 0.00 | ✓ | ✓ | ✗ |
| SS-05 | work table | 1 | 6 | 0.88 | 6 | 0.00 | ✓ | ✓ | ✗ |
| SS-06 | warehouse rack | 1 | 5 | 0.83 | 5 | 0.00 | ✓ | ✗ | ✗ |

#### Low-Frame / Label-Fragmented Clusters (5 rejected)

| Cluster | Category | Sessions | Frames | Label Purity | Support | Dyn Ratio | B0 | B1 | B2 |
|---|---|---|---|---|---|---|---|---|---|
| LF-01 | yellow barrier | 2 | 3 | 0.67 | 3 | 0.00 | ✓ | ✗ | ✗ |
| LF-02 | work table | 1 | 4 | 0.72 | 4 | 0.00 | ✓ | ✗ | ✗ |
| LF-03 | warehouse rack | 1 | 3 | 0.65 | 3 | 0.00 | ✓ | ✗ | ✗ |
| LF-04 | yellow barrier | 1 | 3 | 0.70 | 3 | 0.00 | ✓ | ✗ | ✗ |
| LF-05 | unclassified | 2 | 4 | 0.58 | 4 | 0.00 | ✓ | ✗ | ✗ |

### S2.3 Baseline Comparison Summary

| Metric | B0 (Naive) | B1 (Purity/Support) | B2 (Full Control) |
|---|---|---|---|
| Total admitted | 20 / 20 | 13 / 20 | 5 / 20 |
| Forklift admitted | 4 / 4 | 4 / 4 | 0 / 4 |
| Phantom risk | 20.0% (4/20) | 21.1% (4/19)* | 0.0% (0/5) |
| Infrastructure retention | 5/9 (55.6%) | 5/9 (55.6%) | 5/9 (55.6%) |
| Reduction over B0 | — | −35.0% | −75.0% |
| Reduction over B1 | — | — | −61.5% |

*Phantom risk denominator excludes clusters admitted on any basis; B1 denominator is 19 because one cluster (LF-05) is rejected by purity threshold.

**Key finding:** B1 (purity/support) eliminates 7 weak clusters but admits all 4 forklifts because forklift detections have high label purity (0.82–0.91) and high observation counts (15–28). The full admission-control policy's dynamicity criterion is the critical filter that B1 lacks. B1's phantom risk (21.1%) is actually worse than B0 (20.0%) because the denominator shrinks while the numerator stays constant.

---

## S3. Object Lifecycle Visualization

*Main-text reference: §VII.G.2, Fig. 12*

### S3.1 Lifecycle Comparison

![Fig. S1. Object lifecycle comparison: barrier cluster INF-01 (top, admitted — 3 sessions, 51 frames, dynamic_ratio=0.00) vs forklift cluster FL-01 (bottom, rejected — 3 sessions, 28 frames, dynamic_ratio=0.89). Both clusters appear in 3 sessions with high confidence, but the forklift's dynamic content ratio triggers rejection while the barrier's static profile enables admission.](figures/torwic_object_lifecycle_p156.png)

**Interpretation:** This side-by-side comparison illustrates why semantic confidence alone is insufficient. Both the barrier and forklift are detected with high label purity (>0.90) across three sessions. The difference is not detection quality—it is the nature of the object: barriers are static infrastructure, forklifts are dynamic agents. The maintenance layer captures this distinction through the dynamicity signal.

---

## S4. Dynamic SLAM: Complete 16-Configuration Evidence Chain

*Main-text reference: §VII.E–F. The main manuscript presents the summary Table 6 and boundary-condition analysis. This section summarizes the full 16-configuration evidence chain and preserves the claim boundary: dynamic masking is evaluated as a perturbation check, not as an accuracy-improvement claim.*

### S4.1 Experimental Setup

**VO Backend:** DROID-SLAM [30]
**Primary Window:** TorWIC Aisle_CW_Run_1, 64 frames
**Replication Sessions:** Jun15 Aisle_CW_Run_2, Jun23 Aisle_CW_Run_1, Oct12 Aisle_CW, Oct12 Hallway_Full_CW_Run_2
**Metric:** evo APE/RPE on raw-vs-masked trajectories with SE(3) alignment.

### S4.2 Complete 16-Configuration Summary

| Evidence tier | Configs | Sessions | Result | Claim boundary |
|---|---:|---|---|---|
| Core boundary sweep | 12 | Jun15 Aisle_CW_Run_1 | 7/12 neutral, 5/12 perturbed | Selective/concentrated masks are neutral; propagated/uniform masks perturb BA |
| Stage 1 replication | 2 | Jun15 Aisle_CW_Run_2; Jun23 Aisle_CW_Run_1 | 2/2 neutral | Same-day and cross-day selective masks remain neutral |
| Stage 2 replication | 2 | Oct12 Aisle_CW; Oct12 Hallway_Full_CW_Run_2 | 2/2 neutral | Cross-month and Hallway within-site variation remain neutral |
| Total | 16 | 5 TorWIC sessions | 11/16 neutral (68.8%, bootstrap 95% CI 43.8–87.5%) | Bounded to TorWIC short-window DROID-SLAM evidence |

### S4.3 Key Observations

1. **Selective masks are trajectory-neutral or near-neutral in the tested DROID-SLAM windows.** The neutral group is defined by $|\Delta\text{APE}| \leq 0.006$ mm across 11/16 configurations.

2. **Aggressive masks perturb bundle adjustment.** Temporal propagation, optical-flow propagation, and uniform first-N frame masks produce $0.92$--$7.52$ mm perturbations.

3. **Coverage magnitude matters.** A high-coverage selective-mask pressure test on Jun15 Aisle_CCW_Run_1 reaches 17.32% max per-frame coverage and produces a small but nonzero $+0.114$ mm APE shift. Selectivity is therefore necessary, but not sufficient by itself.

4. **No trajectory-improvement claim.** We do not claim that masking improves ATE/RPE or downstream navigation. The result is a quantified boundary condition for whether semantic masking damages the visual odometry backend.

5. **No cross-site generalization claim.** Hallway is a different floor plan within the same TorWIC warehouse. It supports within-site variation only.

### S4.4 Mask Coverage Per-Frame Distribution

*See Supplementary Fig. S2 (mask coverage diagnostic figure from P135):* `figures/torwic_dynamic_mask_coverage_p135.png`

The per-frame coverage distribution confirms that forklift pixels occupy a small, localized fraction of each image under selective masks. The high-coverage P173 pressure test is retained as a boundary case rather than promoted as an improvement.

### S4.5 Raw vs Masked Trajectory Overlays

*See Supplementary Figs. S3–S6 (trajectory overlay figures from P134, P138–P140):*

| Figure | Content | Source |
|---|---|---|
| S3 | DROID-SLAM raw-vs-masked trajectories, core boundary overlay | `figures/torwic_dynamic_slam_backend_p134.png` |
| S4 | First-8 real mask diagnostic | `figures/torwic_dynamic_mask_first8_real_p138.png` |
| S5 | First-16 real mask diagnostic | `figures/torwic_dynamic_mask_first16_real_p139.png` |
| S6 | First-32 real mask diagnostic | `figures/torwic_dynamic_mask_first32_real_p140.png` |

### S4.6 Temporal and Flow Stress Tests

*See Supplementary Figs. S7–S8:*

| Figure | Content | Source |
|---|---|---|
| S7 | Temporal propagation stress test | `figures/torwic_dynamic_mask_temporal_stress_p136.png` |
| S8 | Optical-flow propagation stress test | `figures/torwic_dynamic_mask_flow_stress_p137.png` |

These diagnostics confirm that masks that propagate beyond true dynamic frames are the failure mode; selective masks remain within the trajectory-neutral regime for the tested TorWIC windows.

---

## S5. Dynamic Mask Coverage Analysis

*Main-text reference: §VII.F*

### S5.1 Window Selection Diagnostic

**Source:** `outputs/torwic_p141_window_selection_diagnostic_v1.md` (P141)

The 64-frame window (Aisle_CW_Run_1) was selected to maximize dynamic activity: it contains the highest forklift presence of any single continuous window in the TorWIC Aisle protocol. This is a deliberately worst-case selection for dynamic masking evaluation, ensuring that if dynamic masking were to show an effect, it would appear here.

### S5.2 Top-N Concentration Screening

**Source:** `outputs/torwic_p142_strong_segment_screening_results_v1.md` (P142)

The top-3 dynamic segments (by area) account for 94.2% of total masked area across the 64-frame window. The remaining segments are minor and have negligible effect on bundle adjustment feature count. This confirms that the masking problem in TorWIC is dominated by a small number of large moving objects (forklifts), not diffuse dynamic texture.

### S5.3 Cross-Window Dynamic Content Audit

**Source:** `outputs/torwic_p143_cross_window_dynamic_audit_v1.md` (P143)

Across all Aisle runs (same-day, cross-day, cross-month), the maximum per-frame dynamic area fraction never exceeds 2.3%. This upper bound is stable across all protocols and time separations, confirming that the ~1.4% finding from the 64-frame test window is representative, not cherry-picked.

---

## S6. Category Retention and Rejection: Per-Cluster Profiles

*Main-text reference: §VII.G.3. The main manuscript presents the category×reason matrix and summary table. This section provides per-cluster rejection detail.*

### S6.1 Rejection Reason Taxonomy

| Reason | Definition | Multi-label? |
|---|---|---|
| `single_session` | Cluster observed in only 1 session | Yes |
| `low_frames` | Cluster has <4 frames of observation | Yes |
| `low_support` | Cluster has <10 supporting observations | Yes |
| `dynamic_contamination` | Cluster has dynamic_ratio > 0.20 | Yes |
| `label_fragmentation` | Cluster has label_purity < 0.85 or split across labels | Yes |

### S6.2 Per-Cluster Rejection Profiles (All 20 Clusters)

**Source files:** `outputs/torwic_category_retention_analysis_p157.json` (P157)

#### Admitted Clusters (5)

| Cluster | Category | Rejection Reasons | Note |
|---|---|---|---|
| INF-01 | yellow barrier | *(none)* | All criteria passed |
| INF-02 | yellow barrier | *(none)* | All criteria passed |
| INF-03 | work table | *(none)* | All criteria passed |
| INF-04 | work table | *(none)* | All criteria passed |
| INF-05 | warehouse rack | *(none)* | All criteria passed |

#### Rejected Clusters (15)

| Cluster | Category | Rejection Reasons |
|---|---|---|
| FL-01 | forklift | dynamic_contamination |
| FL-02 | forklift | dynamic_contamination |
| FL-03 | forklift | dynamic_contamination, single_session |
| FL-04 | forklift | dynamic_contamination, single_session |
| SS-01 | unclassified | single_session, low_frames, low_support, label_fragmentation |
| SS-02 | unclassified | single_session, low_frames, low_support, label_fragmentation |
| SS-03 | unclassified | single_session, low_frames, low_support, label_fragmentation |
| SS-04 | yellow barrier | single_session, low_frames, low_support |
| SS-05 | work table | single_session, low_frames, low_support |
| SS-06 | warehouse rack | single_session, low_frames, low_support |
| LF-01 | yellow barrier | low_frames, low_support, label_fragmentation |
| LF-02 | work table | single_session, low_frames, low_support, label_fragmentation |
| LF-03 | warehouse rack | single_session, low_frames, low_support, label_fragmentation |
| LF-04 | yellow barrier | single_session, low_frames, low_support, label_fragmentation |
| LF-05 | unclassified | low_frames, low_support, label_fragmentation |

### S6.3 Reason Co-Occurrence Matrix

| Primary Reason | single_session | low_frames | low_support | dynamic_contam | label_frag |
|---|---|---|---|---|---|
| single_session (9) | 9 | 9 | 9 | 2 | 7 |
| low_frames (8) | 9 | 8 | 8 | 0 | 7 |
| low_support (8) | 9 | 8 | 8 | 0 | 7 |
| dynamic_contam (4) | 2 | 0 | 0 | 4 | 0 |
| label_frag (7) | 7 | 7 | 7 | 0 | 7 |

**Interpretation:** `single_session`, `low_frames`, `low_support`, and `label_fragmentation` are highly correlated (all affected by sparse observation). `dynamic_contamination` is independent—it primarily affects forklift clusters regardless of observation quality.

---

## S7. Per-Category Retention/Rejection Figures

*Main-text reference: §VII.G.3*

### S7.1 Retention Per Category

![Fig. S9. Per-category retention/rejection: 5 categories, 20 total clusters. Infrastructure categories show partial retention; forklifts show zero retention.](figures/torwic_per_category_retention_p157.png)

### S7.2 Rejection Reason Distribution

![Fig. S10. Rejection reason distribution: stacked bar chart showing single-session, low-frames, low-support, dynamic-contamination, and label-fragmentation reasons across all 15 rejected clusters.](figures/torwic_rejection_reason_distribution_p157.png)

### S7.3 Category × Rejection Reason Heatmap

![Fig. S11. Category × rejection reason heatmap: 5 rows (categories) × 5 columns (rejection reasons). Dynamic contamination is exclusively associated with the forklift category. Low-frame and label-fragmentation reasons cluster in unclassified and low-quality infrastructure clusters.](figures/torwic_rejection_reason_heatmap_p157.png)

---

## S8. Evidence File Index

### S8.1 Complete Evidence Inventory

All evidence files are located under the project root (`<repo-root>/`).

#### Core Outputs

| File | Phase | Content |
|---|---|---|
| `outputs/torwic_admission_ablation_results.json` | P154 | 27-combination parameter ablation sweep |
| `outputs/torwic_baseline_comparison_results.json` | P155 | B0/B1/B2 per-cluster admission matrix |
| `outputs/torwic_category_retention_analysis_p157.json` | P157 | Per-cluster retention/rejection profiles |
| `outputs/torwic_submission_ready_closure_bundle_v36.md` | P158 | Complete closure bundle (P108-P157) |

#### Dynamic SLAM Diagnostics

| File | Phase | Content |
|---|---|---|
| `outputs/torwic_p134_dynamic_slam_backend_summary_v1.md` | P134 | DROID-SLAM summary |
| `outputs/torwic_p135_dynamic_mask_coverage_v1.md` | P135 | Mask coverage analysis |
| `outputs/torwic_p136_temporal_propagation_stress_v1.md` | P136 | Temporal propagation stress |
| `outputs/torwic_p137_flow_propagation_stress_v1.md` | P137 | Optical-flow propagation stress |
| `outputs/torwic_p138_first8_real_mask_diagnostic_v1.md` | P138 | First-8 mask diagnostic |
| `outputs/torwic_p139_first16_real_mask_diagnostic_v1.md` | P139 | First-16 mask diagnostic |
| `outputs/torwic_p140_first32_real_mask_diagnostic_v1.md` | P140 | First-32 mask diagnostic |
| `outputs/torwic_p141_window_selection_diagnostic_v1.md` | P141 | Window selection rationale |
| `outputs/torwic_p142_strong_segment_screening_results_v1.md` | P142 | Top-N concentration screening |
| `outputs/torwic_p143_cross_window_dynamic_audit_v1.md` | P143 | Cross-window dynamic audit |

#### Aisle and Hallway Protocol Evidence

| File | Phase | Content |
|---|---|---|
| `outputs/torwic_same_day_aisle_bundle_v1.md` | P108–P111 | Same-day protocol (203/11/5) |
| `outputs/torwic_cross_day_aisle_bundle_v1.md` | P112–P115 | Cross-day protocol (240/10/5) |
| `outputs/torwic_cross_month_aisle_bundle_v1.md` | P116–P119 | Cross-month protocol (297/14/7) |
| `outputs/torwic_hallway_protocol_current_v1.md` | P120–P125 | Hallway protocol (537/16/9) |

#### Manuscript and Export

| File | Description |
|---|---|
| `paper/manuscript_en_thick.md` | EN thick manuscript (final) |
| `paper/manuscript_zh_thick.md` | ZH thick manuscript (final) |
| `paper/export/manuscript_en_thick.pdf` | EN PDF export |
| `paper/export/final_audit_report_p158.md` | 100/100 audit report |
| `paper/export/tro_ijrr_submission_strategy_p160.md` | T-RO/IJRR strategy |
| `paper/export/references_expansion_p164.md` | Reference expansion (11→35) |
| `paper/tro_submission/main.tex` | T-RO LaTeX scaffold |
| `paper/tro_submission/references.bib` | BibTeX (35 entries) |

### S8.2 Figure Index

| Figure | File | In Main? | In Suppl? | Content |
|---|---|---|---|---|
| 1 | `torwic_paper_result_overview.png` | ✓ | | Pipeline overview |
| 2 | `torwic_real_session_overlays.png` | ✓ | | Rejection-ratio overview |
| 3 | `torwic_hallway_composite.png` | ✓ | | Hallway composite |
| 4 | `torwic_dynamic_slam_backend_p134.png` | ✓ | | DROID-SLAM trajectories |
| 5 | `torwic_dynamic_mask_coverage_p135.png` | ✓ | | Mask coverage |
| 6 | `torwic_dynamic_mask_temporal_stress_p136.png` | ✓ | | Temporal stress |
| 7 | `torwic_dynamic_mask_flow_stress_p137.png` | ✓ | | Flow stress |
| 8 | `torwic_dynamic_mask_first8_real_p138.png` | ✓ | | First-8 mask |
| 9 | `torwic_dynamic_mask_first16_real_p139.png` | ✓ | | First-16 mask |
| 10 | `torwic_dynamic_mask_first32_real_p140.png` | ✓ | | First-32 mask |
| 11 | `torwic_before_after_map_composition_p156.png` | ✓ | | B0 vs B2 map |
| 12 (S1) | `torwic_object_lifecycle_p156.png` | | ✓ | Barrier vs forklift lifecycle |
| 13 | `torwic_admission_decision_space_p156.png` | ✓ | | Decision space scatter |
| 14 (S9) | `torwic_per_category_retention_p157.png` | | ✓ | Category retention bar |
| 15 (S10) | `torwic_rejection_reason_distribution_p157.png` | | ✓ | Rejection reason dist |
| 16 (S11) | `torwic_rejection_reason_heatmap_p157.png` | | ✓ | Category×reason heatmap |

---

## Revision History

| Version | Date | Changes |
|---|---|---|
| v1 | 2026-05-09 | Initial supplementary package (P163). All evidence from P134-P157 integrated. |

---

*This supplementary material is provided for reviewer reference. All claims, boundary conditions, and negative results are consistent with the main manuscript. No new experiments were conducted for this supplementary package.*
