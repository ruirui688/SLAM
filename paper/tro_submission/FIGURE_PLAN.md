# FIGURE_PLAN.md — T-RO Figure Placement Plan

**Template:** IEEEtran, two-column  
**Figure width target:** \columnwidth (3.5 in / 89 mm) for single-column, \textwidth (7.16 in / 182 mm) for double-column (spanning) floats  
**Resolution:** 300 dpi recommended for TR-O (current figures at 150 dpi — acceptable, but regenerate at 300 dpi for final submission)

## Main-Body Figures (12 figures)

| Fig | File | Width | Section | Caption Summary |
|-----|------|-------|---------|-----------------|
| 1 | `figures/torwic_paper_result_overview.png` | double-col | §VII.A | Full pipeline: perception → maintenance → map |
| 2 | `figures/torwic_real_session_overlays.png` | double-col | §VII.D | Four-protocol rejection-ratio overview |
| 3 | `figures/torwic_hallway_composite.png` | double-col | §VII.C | Hallway scene-transfer evidence |
| 4 | `figures/torwic_dynamic_slam_backend_p134.png` | single-col | §VII.E | DROID-SLAM raw-vs-masked trajectories |
| 5 | `figures/torwic_dynamic_mask_coverage_p135.png` | single-col | §VII.F | Dynamic mask coverage per config |
| 6 | `figures/torwic_dynamic_mask_temporal_stress_p136.png` | single-col | §VII.F | Temporal propagation stress test |
| 7 | `figures/torwic_dynamic_mask_flow_stress_p137.png` | single-col | §VII.F | Optical-flow propagation stress test |
| 8 | `figures/torwic_dynamic_mask_first8_real_p138.png` | single-col | §VII.F | First-8 real mask diagnostic |
| 9 | `figures/torwic_dynamic_mask_first16_real_p139.png` | single-col | §VII.F | First-16 real mask diagnostic |
| 10 | `figures/torwic_dynamic_mask_first32_real_p140.png` | single-col | §VII.F | First-32 real mask diagnostic |
| 11 | `figures/torwic_before_after_map_composition_p156.png` | single-col | §VII.G.2 | B0 vs B2 map composition |
| 13 | `figures/torwic_admission_decision_space_p156.png` | double-col | §VII.G.1 | Dynamic_ratio × session_count scatter |

## Supplementary Figures (4 figures, P163)

| Fig | File | Caption Summary |
|-----|------|-----------------|
| S1 (12) | `figures/torwic_object_lifecycle_p156.png` | Object lifecycle: barrier admission vs forklift rejection |
| S2 (14) | `figures/torwic_per_category_retention_p157.png` | Per-category retention/rejection bar chart |
| S3 (15) | `figures/torwic_rejection_reason_distribution_p157.png` | Rejection reason distribution |
| S4 (16) | `figures/torwic_rejection_reason_heatmap_p157.png` | Category × rejection reason heatmap |

## Figure Sizing Notes

- **Double-column figures (1,2,3,13):** Use `\begin{figure*}`. Consider reducing size to fit within page margins while preserving readability.
- **Single-column figures (4-11):** Use `\begin{figure}`. Current PNGs are ~1200-1600px wide; at 150dpi they render at ~8-10 inches. They will need to be scaled via `\includegraphics[width=\columnwidth]{...}`.
- **Resolution:** Current figures at 150 dpi are readable but slightly below the 300 dpi TR-O recommendation. For final submission, regenerate all figures at `dpi=300` and update in this plan.

## Table Placement

| Table | Content | Section |
|-------|---------|---------|
| 1 | Evidence Ladder Summary (Aisle protocols) | §VII.A |
| 2 | Same-Day Aisle Selection Analysis | §VII.B |
| 3 | Cross-Day Aisle Selection Analysis | §VII.B |
| 4 | Hallway Selection Analysis | §VII.C |
| 5 | DROID-SLAM Backend Configuration Survey | §VII.E |
| 6 | Complete Dynamic Masking Evidence Chain | §VII.F |
| 7 | Parameter Ablation Summary (P154) | §VII.G.1 |
| 8 | Baseline Comparison (P155) | §VII.G.2 |
| 9 | Per-Category Retention Matrix (P157) | §VII.G.3 |

Tables 7-9 are new (P154-P157). Tables 1-6 are existing.

## Overlength Risk Assessment

- All 12 main-body figures: ~3 pages of figure floats
- 9 tables: ~3 pages of table floats
- Text body: ~8 pages
- References: ~2 pages
- **Estimated total: ~16 pages** (within 20-page limit, but >12-page free tier)

The 16-page estimate is within TR-O's regular-paper budget. If the page count exceeds 20 after full content insertion, move Tables 4 and/or 9 to supplementary.
