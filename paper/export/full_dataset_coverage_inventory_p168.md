# P168 Full Dataset Coverage Inventory

Generated from local filesystem inventory. No data/model downloads and no new SLAM runs were performed.

## Executive Summary

- Local TorWIC sessions found: **20** across **3** dates.
- Estimated RGB frames: **32,743**.
- Aisle / Hallway sessions: **10 / 10**.
- Sessions with GT trajectory: **20/20**.
- Sessions with existing semantic frontend artifacts: **16/20**.
- Sessions with DROID-SLAM raw/masked backend artifacts: **1/20**.
- DROID-SLAM backend configs in the bounded chain: **12**, with **11** metrics-bearing configs.

## Claim Boundary

P135-P143 dynamic SLAM backend runs are bounded 64-frame negative-result chain on a SINGLE TorWIC session (Jun 15 Aisle_CW_Run_1). This is NOT a full dataset benchmark. No multi-session DROID-SLAM comparisons exist.

**Interpretation:** the project has broad local TorWIC data and broad semantic-map evidence, but dynamic SLAM backend evidence is currently concentrated on one 64-frame Aisle_CW_Run_1 window. This is enough for a bounded negative-result/boundary-condition study; it is not enough for a full-dataset dynamic SLAM benchmark claim.

## Session Coverage Matrix

| Session | Route type | RGB frames | GT traj | Semantic frontend | DROID backend | ATE/RPE computed | Dynamic-SLAM suitability | Blockers |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `2022-06-15__Aisle_CCW_Run_1` | aisle | 1136 | yes | yes | no | no | yes | No DROID-SLAM backend run, No DROID-SLAM input pack created |
| `2022-06-15__Aisle_CCW_Run_2` | aisle | 1238 | yes | yes | no | no | yes | No DROID-SLAM backend run, No DROID-SLAM input pack created |
| `2022-06-15__Aisle_CW_Run_1` | aisle | 1114 | yes | yes | yes | yes | yes | - |
| `2022-06-15__Aisle_CW_Run_2` | aisle | 1124 | yes | yes | no | no | yes | No DROID-SLAM backend run, No DROID-SLAM input pack created |
| `2022-06-15__Hallway_Full_CCW` | hallway | 2539 | yes | yes | no | no | no | No DROID-SLAM input pack created |
| `2022-06-15__Hallway_Full_CW` | hallway | 2511 | yes | yes | no | no | no | No DROID-SLAM input pack created |
| `2022-06-15__Hallway_Straight_CCW` | hallway | 2197 | yes | yes | no | no | no | No DROID-SLAM input pack created |
| `2022-06-23__Aisle_CCW_Run_1` | aisle | 1066 | yes | no | no | no | yes | No DROID-SLAM backend run, No DROID-SLAM input pack created |
| `2022-06-23__Aisle_CCW_Run_2` | aisle | 1156 | yes | no | no | no | yes | No DROID-SLAM backend run, No DROID-SLAM input pack created |
| `2022-06-23__Aisle_CW_Run_1` | aisle | 1037 | yes | yes | no | no | yes | No DROID-SLAM backend run, No DROID-SLAM input pack created |
| `2022-06-23__Aisle_CW_Run_2` | aisle | 1059 | yes | yes | no | no | yes | No DROID-SLAM backend run, No DROID-SLAM input pack created |
| `2022-06-23__Hallway_Full_CW` | hallway | 2320 | yes | yes | no | no | no | No DROID-SLAM input pack created |
| `2022-06-23__Hallway_Straight_CCW` | hallway | 1972 | yes | yes | no | no | no | No DROID-SLAM input pack created |
| `2022-06-23__Hallway_Straight_CW` | hallway | 1936 | yes | yes | no | no | no | No DROID-SLAM input pack created |
| `2022-10-12__Aisle_CCW` | aisle | 915 | yes | yes | no | no | yes | No DROID-SLAM backend run, No DROID-SLAM input pack created |
| `2022-10-12__Aisle_CW` | aisle | 1092 | yes | yes | no | no | yes | No DROID-SLAM backend run, No DROID-SLAM input pack created |
| `2022-10-12__Hallway_Full_CW_Run_1` | hallway | 2318 | yes | yes | no | no | no | No DROID-SLAM input pack created |
| `2022-10-12__Hallway_Full_CW_Run_2` | hallway | 2320 | yes | yes | no | no | no | No DROID-SLAM input pack created |
| `2022-10-12__Hallway_Straight_CCW` | hallway | 1883 | yes | yes | no | no | no | No DROID-SLAM input pack created |
| `2022-10-12__Hallway_Straight_CW` | hallway | 1810 | yes | yes | no | no | no | No DROID-SLAM input pack created |

## Dynamic SLAM Backend Coverage

- Unique backend input session/window: **1** (`2022-06-15 Aisle_CW_Run_1 (1,114 frames)`).
- Backend configs: **12**.
- Configs with metrics: **11**.
- Configs pending metrics: **1**.

| Config | Mask policy | Frames | Global BA | Metrics |
|---|---|---:|---:|---:|
| `p132` | baseline_raw | 8 | no | yes |
| `p134_64` | baseline_raw | 64 | no | no |
| `p134_64_gba` | baseline_raw | 64 | yes | yes |
| `p135_sem` | semantic | 64 | yes | yes |
| `p136_temporal` | temporal_stress | 64 | yes | yes |
| `p137_flow` | flow_stress | 64 | yes | yes |
| `p138_first8` | first8_real | 64 | yes | yes |
| `p139_first16` | first16_real | 64 | yes | yes |
| `p140_first32` | first32_real | 64 | yes | yes |
| `p142_top4` | top4_concentrated | 64 | yes | yes |
| `p142_top8` | top8_concentrated | 64 | yes | yes |
| `p142_top16` | top16_concentrated | 64 | yes | yes |

## Gaps And Blockers

| ID | Severity | Description | Impact |
|---|---|---|---|
| `GAP-DROID-001` | HIGH | 12 DROID-SLAM config runs on 1/20 sessions. No other session has backend runs. | Cannot claim multi-session dynamic SLAM. Paper claim: single-window negative-result. |
| `GAP-DROID-002` | MEDIUM | 11/12 DROID-SLAM configs have metrics; one non-global-BA intermediate config lacks metrics. The real gap is not metrics within P135-P143, but lack of multi-session backend coverage. | Paper may report the bounded 10-config negative-result chain, but must not imply full-dataset dynamic SLAM evaluation. |
| `GAP-DROID-003` | MEDIUM | No DROID-SLAM runs on Hallway sessions (0/10). | Cannot extrapolate dynamic SLAM to Hallway. |
| `GAP-DROID-004` | MEDIUM | No comparison against published SLAM systems. | Documented in Limitations item #5. |
| `GAP-FRONTEND-001` | LOW | 36 output dirs contain version drift (v1, available_v1, bundle_v1). | Metadata clarity only; bundle_v1+richer recomputed are canonical. |
| `GAP-DATA-001` | LOW | Single-site dataset. No public multi-site industrial SLAM dataset exists. | Documented in Limitations item #2. |

## Next-Step Matrix

| Priority | Action | Why |
|---:|---|---|
| 1 | Run dynamic-SLAM backend on 2-3 additional sessions selected from this matrix. | Converts the current single-window result into multi-session evidence. |
| 2 | Scan mask coverage across all RGB sessions before running expensive backend jobs. | Avoids spending GPU time on low-dynamic windows. |
| 3 | Add bootstrap CI / small-sample tests for current object-admission results. | Addresses Round-1 reviewer risk about 20 clusters. |
| 4 | Keep P135-P143 framed as bounded negative-result evidence until multi-session backend runs exist. | Prevents overclaiming. |
