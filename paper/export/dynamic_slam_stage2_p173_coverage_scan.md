# Dynamic SLAM Stage 2 Coverage Scan — P173

**Scope:** local data/frontend availability and 64-frame mask coverage only. No DROID-SLAM or ATE/RPE is run here.

## Summary

- Sessions scanned: 5
- Ready for DROID input packs: 5/5
- Hallway negative control has empty dynamic mask: no
- Strongest dynamic session: Jun15 Aisle_CCW_Run_1 (max 17.324544% coverage)

## Coverage Table

| Session | Category | Masked Frames | Max Coverage | Mean Coverage | Status |
|---|---|---:|---:|---:|---|
| Jun23 Aisle_CW_Run_2 | cross-day CW pair | 4/64 | 0.88954% | 0.030908% | ready_for_droid |
| Oct12 Aisle_CW | cross-month CW | 2/64 | 4.8852% | 0.125658% | ready_for_droid |
| Jun15 Aisle_CCW_Run_1 | opposite direction | 5/64 | 17.324544% | 0.567534% | ready_for_droid |
| Oct12 Aisle_CCW | cross-month CCW | 3/64 | 5.377713% | 0.212719% | ready_for_droid |
| Jun15 Hallway_Full_CW | Hallway negative control | 7/64 | 0.895182% | 0.037001% | ready_for_droid |

## Notable Finding

Jun15 Aisle_CCW_Run_1 is the first P173 candidate with strong dynamic-mask coverage in the first 64 frames: max 17.324544% and mean 0.567722%. This is substantially stronger than P172 Stage 1 (<1.5% max, <0.05% mean) and should be the first GPU run because it can stress-test the P171/P172 selectivity claim.

## Top Dynamic Frames

### Jun23 Aisle_CW_Run_2
| Frame | Coverage | Mask Inputs |
|---:|---:|---|
| 000007 | 0.88954% | `outputs/torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_2/frontend_output/fork_007_mask.png`<br>`outputs/torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_2/frontend_output/forklift_005_mask.png`<br>`outputs/torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_2/frontend_output/forklift_006_mask.png` |
| 000005 | 0.524197% | `outputs/torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_2/frontend_output/forklift_004_mask.png`<br>`outputs/torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_2/frontend_output/forklift_007_mask.png` |
| 000003 | 0.505642% | `outputs/torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_2/frontend_output/fork_005_mask.png` |
| 000004 | 0.058702% | `outputs/torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_2/frontend_output/forklift_009_mask.png` |

### Oct12 Aisle_CW
| Frame | Coverage | Mask Inputs |
|---:|---:|---|
| 000007 | 4.8852% | `outputs/torwic_cross_month_aisle_bundle_v1__2022-10-12__Aisle_CW/frontend_output/forklift_001_mask.png`<br>`outputs/torwic_cross_month_aisle_bundle_v1__2022-10-12__Aisle_CW/frontend_output/forklift_003_mask.png` |
| 000006 | 3.156901% | `outputs/torwic_cross_month_aisle_bundle_v1__2022-10-12__Aisle_CW/frontend_output/forklift_004_mask.png` |

### Jun15 Aisle_CCW_Run_1
| Frame | Coverage | Mask Inputs |
|---:|---:|---|
| 000005 | 17.324544% | `outputs/torwic_same_day_aisle_bundle_v1__2022-06-15__Aisle_CCW_Run_1/frontend_output/forklift_004_mask.png`<br>`outputs/torwic_same_day_aisle_bundle_v1__2022-06-15__Aisle_CCW_Run_1/frontend_output/forklift_007_mask.png` |
| 000007 | 16.511827% | `outputs/torwic_same_day_aisle_bundle_v1__2022-06-15__Aisle_CCW_Run_1/frontend_output/forklift_005_mask.png` |
| 000006 | 0.900716% | `outputs/torwic_same_day_aisle_bundle_v1__2022-06-15__Aisle_CCW_Run_1/frontend_output/fork_006_mask.png`<br>`outputs/torwic_same_day_aisle_bundle_v1__2022-06-15__Aisle_CCW_Run_1/frontend_output/fork_007_mask.png` |
| 000002 | 0.798611% | `outputs/torwic_same_day_aisle_bundle_v1__2022-06-15__Aisle_CCW_Run_1/frontend_output/forklift_008_mask.png` |
| 000004 | 0.786458% | `outputs/torwic_same_day_aisle_bundle_v1__2022-06-15__Aisle_CCW_Run_1/frontend_output/forklift_006_mask.png` |

### Oct12 Aisle_CCW
| Frame | Coverage | Mask Inputs |
|---:|---:|---|
| 000007 | 5.377713% | `outputs/torwic_cross_month_aisle_bundle_v1__2022-10-12__Aisle_CCW/frontend_output/forklift_003_mask.png`<br>`outputs/torwic_cross_month_aisle_bundle_v1__2022-10-12__Aisle_CCW/frontend_output/forklift_004_mask.png` |
| 000005 | 4.299479% | `outputs/torwic_cross_month_aisle_bundle_v1__2022-10-12__Aisle_CCW/frontend_output/fork_004_mask.png`<br>`outputs/torwic_cross_month_aisle_bundle_v1__2022-10-12__Aisle_CCW/frontend_output/forklift_002_mask.png` |
| 000001 | 3.936849% | `outputs/torwic_cross_month_aisle_bundle_v1__2022-10-12__Aisle_CCW/frontend_output/fork_003_mask.png` |

### Jun15 Hallway_Full_CW
| Frame | Coverage | Mask Inputs |
|---:|---:|---|
| 000000 | 0.895182% | `outputs/torwic_hallway_benchmark_batch2_v1__2022-06-15__Hallway_Full_CW/frontend_output/fork_007_mask.png` |
| 000003 | 0.69911% | `outputs/torwic_hallway_benchmark_batch2_v1__2022-06-15__Hallway_Full_CW/frontend_output/fork_006_mask.png` |
| 000002 | 0.161133% | `outputs/torwic_hallway_benchmark_batch2_v1__2022-06-15__Hallway_Full_CW/frontend_output/forklift_009_mask.png` |
| 000007 | 0.160265% | `outputs/torwic_hallway_benchmark_batch2_v1__2022-06-15__Hallway_Full_CW/frontend_output/forklift_005_mask.png` |
| 000006 | 0.153863% | `outputs/torwic_hallway_benchmark_batch2_v1__2022-06-15__Hallway_Full_CW/frontend_output/forklift_008_mask.png` |

## Next GPU Step

Run tools/run_dynamic_slam_backend_smoke.py --frame-limit 64 --buffer 256 --global-ba for each p173 input pack, then tools/evaluate_dynamic_slam_metrics.py for evo APE/RPE. Start with p173_jun15_aisle_ccw_run1 because it has the strongest dynamic coverage.

## Input Packs

- Jun23 Aisle_CW_Run_2: `outputs/dynamic_slam_backend_input_pack_p173_jun23_aisle_cw_run2`
- Oct12 Aisle_CW: `outputs/dynamic_slam_backend_input_pack_p173_oct12_aisle_cw`
- Jun15 Aisle_CCW_Run_1: `outputs/dynamic_slam_backend_input_pack_p173_jun15_aisle_ccw_run1`
- Oct12 Aisle_CCW: `outputs/dynamic_slam_backend_input_pack_p173_oct12_aisle_ccw`
- Jun15 Hallway_Full_CW: `outputs/dynamic_slam_backend_input_pack_p173_jun15_hallway_full_cw`
