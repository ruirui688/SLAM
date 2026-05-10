# SUPPLEMENT_FIGURE_PLAN.md — T-RO Supplementary Figure Placement

**Target:** IEEE Transactions on Robotics, Supplementary Material  
**Format:** Self-contained PDF or zip archive with figures + captions  
**Date:** 2026-05-09 (P163)

## Figure Inventory

| Suppl. Fig | Source File | Caption | Location in Supplement |
|---|---|---|---|
| S1 | `paper/figures/torwic_object_lifecycle_p156.png` | Object lifecycle: barrier INF-01 (admitted, 3 sessions, 51 frames) vs forklift FL-01 (rejected, 3 sessions, 28 frames, dynamic_ratio=0.89) | §S3 |
| S2 | `paper/figures/torwic_dynamic_mask_coverage_p135.png` | Per-frame dynamic mask coverage distribution (64-frame window, Aisle_CW_Run_1) | §S4.4 |
| S3 | `paper/figures/torwic_dynamic_slam_backend_p134.png` | DROID-SLAM raw-vs-masked trajectory overlay, all 10 configurations | §S4.5 |
| S4 | `paper/figures/torwic_dynamic_mask_first8_real_p138.png` | First-8 real mask diagnostic | §S4.5 |
| S5 | `paper/figures/torwic_dynamic_mask_first16_real_p139.png` | First-16 real mask diagnostic | §S4.5 |
| S6 | `paper/figures/torwic_dynamic_mask_first32_real_p140.png` | First-32 real mask diagnostic | §S4.5 |
| S7 | `paper/figures/torwic_dynamic_mask_temporal_stress_p136.png` | Temporal propagation stress test | §S4.6 |
| S8 | `paper/figures/torwic_dynamic_mask_flow_stress_p137.png` | Optical-flow propagation stress test | §S4.6 |
| S9 | `paper/figures/torwic_per_category_retention_p157.png` | Per-category retention/rejection bar chart | §S7.1 |
| S10 | `paper/figures/torwic_rejection_reason_distribution_p157.png` | Rejection reason stacked distribution | §S7.2 |
| S11 | `paper/figures/torwic_rejection_reason_heatmap_p157.png` | Category × rejection reason heatmap | §S7.3 |

## Table Inventory (All in Supplement)

| Table | Content | Location |
|---|---|---|
| ST1 | Full 27-combination parameter ablation sweep | §S1.2 |
| ST2 | Sensitivity labels | §S1.3 |
| ST3 | Per-cluster admission matrix (infrastructure) | §S2.2 |
| ST4 | Per-cluster admission matrix (forklifts) | §S2.2 |
| ST5 | Per-cluster admission matrix (single-session) | §S2.2 |
| ST6 | Per-cluster admission matrix (low-frame) | §S2.2 |
| ST7 | Baseline comparison summary | §S2.3 |
| ST8 | Complete 16-configuration DROID-SLAM evidence-chain summary | §S4.2 |
| ST9 | Per-cluster rejection profiles | §S6.2 |
| ST10 | Reason co-occurrence matrix | §S6.3 |
| ST11 | Evidence file index | §S8 |

## Build Instructions

### Option A: Convert to PDF (requires pandoc + LaTeX)
```bash
cd paper/tro_submission/supplementary
pandoc supplement.md -o supplement.pdf \
  --pdf-engine=pdflatex \
  --resource-path=../../figures \
  --from markdown+pipe_tables
```

### Option B: Manual assembly (recommended, given LaTeX blocker)
Upload `supplement.md` and all referenced figure files to Overleaf alongside `main.tex`. The supplement can be compiled as a separate document or included via `\include{}`.

### Option C: Portable zip
```bash
cd paper/tro_submission
zip -r supplementary.zip supplementary/ ../../paper/figures/torwic_object_lifecycle_p156.png ../../paper/figures/torwic_dynamic_mask_*.png ../../paper/figures/torwic_per_category_retention_p157.png ../../paper/figures/torwic_rejection_reason_*.png ../../paper/figures/torwic_dynamic_slam_backend_p134.png
```

## TR-O Supplementary Guidelines

- TR-O accepts supplementary material as a separate PDF or zip archive.
- Supplementary material does not count toward the 20-page limit.
- All supplementary figures must be explicitly referenced in the main text (e.g., "see Supplementary Fig. S1").
- The supplementary document should be self-contained and reviewer-facing.
- Large binary files (datasets, videos) can be linked but should not be uploaded as part of the submission package unless required for reproducibility.

## Claim Boundary Compliance

- ⚠️ No claim that masked input improves trajectory accuracy (ATE/RPE).
- ⚠️ Dynamic SLAM results are presented as a quantitative boundary condition, not a performance gain.
- ✅ All supplementary evidence is consistent with main manuscript claims.
- ✅ Negative results are explicitly framed as boundary conditions.
