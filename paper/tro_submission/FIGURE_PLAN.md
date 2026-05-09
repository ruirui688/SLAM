# T-RO Figure Plan — Main vs. Supplementary

Total figures: 16. T-RO main text target: 10–12 figures.
Supplementary material: 4–6 figures (submitted as a separate PDF).

## Main Text Figures (10)

| Main # | Original # | File | Description | Width |
|---|---|---|---|---|
| 1 | Fig. 1 | `../figures/torwic_paper_result_overview.png` | Pipeline overview: observation→tracklet→map-object→revision | column |
| 2 | Fig. 2 | `../figures/torwic_real_session_overlays.png` | Primary Aisle evidence ladder (203/11/5, 240/10/5, 297/14/7) | wide |
| 3 | Fig. 3 | `../figures/torwic_stable_object_selection_v5.png` | Map-admission selectivity across four protocols | wide |
| 4 | Fig. 4 | `../figures/torwic_dynamic_slam_backend_p134.png` | Bounded DROID-SLAM backend closure (64-frame) | column |
| 5 | Fig. 11 | `../figures/torwic_before_after_map_composition_p156.png` | Before/after map composition: B0 vs B2 | column |
| 6 | Fig. 12 | `../figures/torwic_object_lifecycle_p156.png` | Object lifecycle: stable barrier vs forklift rejection | wide |
| 7 | Fig. 13 | `../figures/torwic_admission_decision_space_p156.png` | Admission decision space: dynamic_ratio × session_count | wide |
| 8 | Fig. 14 | `../figures/torwic_per_category_retention_p157.png` | Per-category retention/rejection bar chart | column |
| 9 | Fig. 10 | `../figures/torwic_dynamic_mask_first32_real_p140.png` | Representative dynamic-mask diagnostic (strongest: 32 real frames) | column |
| 10 | Fig. 4 (Hallway) | `../figures/torwic_hallway_composite.png` | Hallway broader-validation composite | wide |

## Supplementary Figures (6)

### S1. Consolidated Dynamic-SLAM Mask Coverage Panel (Figs 5–9 merged)

Merge Figs 5–9 into a single multi-panel figure:

| Panel | Original | File |
|---|---|---|
| (a) | Fig. 5 | `../figures/torwic_dynamic_mask_coverage_p135.png` |
| (b) | Fig. 6 | `../figures/torwic_dynamic_mask_temporal_stress_p136.png` |
| (c) | Fig. 7 | `../figures/torwic_dynamic_mask_flow_stress_p137.png` |
| (d) | Fig. 8 | `../figures/torwic_dynamic_mask_first8_real_p138.png` |
| (e) | Fig. 9 | `../figures/torwic_dynamic_mask_first16_real_p139.png` |

Caption: "Dynamic-SLAM mask coverage diagnostics (P135–P139).
(a) Existing semantic-mask coverage: 3/64 frames, 0.026% mean.
(b) Temporal nearest-frame propagation stress test: 16/64 frames, 0.267%.
(c) Optical-flow warped propagation stress test: same coverage.
(d) First-eight real frontend masks: 8/64 frames, 0.118%.
(e) First-sixteen real frontend masks: 16/64 frames, 0.264%.
All five configurations produce effectively tied ATE/RPE
(|Δ| < 0.1 mm), confirming that the bounding constraint is
dynamic-mask area, not propagation method."

### S2. Rejection-Reason Derivative Figures (Figs 15–16)

| Panel | Original | File |
|---|---|---|
| (a) | Fig. 15 | `../figures/torwic_rejection_reason_distribution_p157.png` |
| (b) | Fig. 16 | `../figures/torwic_rejection_reason_heatmap_p157.png` |

Caption: "Rejection reason analysis (P157).
(a) Distribution across 15 rejected clusters (multi-label).
(b) Per-category × rejection reason heatmap."

## Consolidation Rationale

- **Figs 5–9 → S1 multi-panel**: These are diagnostic variants of the same
  core experiment (dynamic-mask coverage vs ATE). Showing all five as separate
  main-text figures would inflate the page count without adding independent
  evidence. A merged multi-panel figure preserves traceability while saving 4
  figure slots.

- **Figs 15–16 → S2 multi-panel**: These are supporting analytics for the
  per-category retention result (Fig. 14 in main text). The main narrative is
  adequately served by the bar chart; the distribution and heatmap provide
  reviewer-facing detail.

- **Fig. 10 (first-32 real masks, P140)** is selected as the single
  representative dynamic-mask figure in the main text because it is the
  strongest configuration (32/64 frames, 0.568% coverage) and shows the
  asymptote of the real-mask scaling experiment.

## Page Budget Accounting

| What | Pages (est.) |
|---|---|
| Text body (~9,400 words) | ~10.5 |
| 10 main-text figures | ~3.5 |
| 5 tables | ~2.0 |
| References (11 entries) | ~0.8 |
| **Total** | **~16.8** |

Within IEEE T-RO 20-page limit with ~3 pages margin for layout variance.
If a reviewer or editor requests cuts, Figs 3 and 10 are the first candidates
for supplementary relocation.
