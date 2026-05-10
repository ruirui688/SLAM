# P208 Evidence-Quality Notes Summary

**Status:** `PASS`; P195 remains `BLOCKED`.

## Scope

P208 summarizes P207 evidence-quality notes only. It reports blank counts, allowed-value distributions, and quality-blocker rates. It does not create admission labels, same-object labels, training data, or admission-control claims.

## Current Results

- Rows: 32
- All note fields blank: True
- Quality blockers: 0 yes / 32 rows
- Validation: PASS (0 issues, 0 warnings)
- Prohibited label/proxy columns present: none
- Reviewer notes with admission/same-object-like text: 0

## Note Field Distributions

- `visibility_quality`: blank=32, clear=0, partial=0, poor=0, not_assessable=0
- `mask_alignment_quality`: blank=32, good=0, minor_issue=0, major_issue=0, not_assessable=0
- `depth_quality`: blank=32, usable=0, limited=0, unusable=0, not_assessable=0
- `occlusion_level`: blank=32, none=0, low=0, medium=0, high=0, not_assessable=0
- `blur_level`: blank=32, none=0, low=0, medium=0, high=0, not_assessable=0
- `reviewer_note`: blank=32, nonblank=0
- `quality_blocker`: blank=32, no=0, yes=0

## Quality Blocker Rates

### By `canonical_label`
- barrier: 0/8 yes (rate=0.000000, blank=8)
- forklift: 0/8 yes (rate=0.000000, blank=8)
- warehouse rack: 0/8 yes (rate=0.000000, blank=8)
- work table: 0/8 yes (rate=0.000000, blank=8)

### By `source`
- cross_day: 0/8 yes (rate=0.000000, blank=8)
- cross_month: 0/4 yes (rate=0.000000, blank=4)
- hallway: 0/16 yes (rate=0.000000, blank=16)
- same_day: 0/4 yes (rate=0.000000, blank=4)

### By `row_source`
- p193: 0/6 yes (rate=0.000000, blank=6)
- p197_boundary: 0/6 yes (rate=0.000000, blank=6)
- p197_pair: 0/14 yes (rate=0.000000, blank=14)
- p199: 0/6 yes (rate=0.000000, blank=6)

### By `session_id`
- torwic_cross_day_aisle_bundle_v1__2022-06-15__Aisle_CW_Run_1: 0/2 yes (rate=0.000000, blank=2)
- torwic_cross_day_aisle_bundle_v1__2022-06-15__Aisle_CW_Run_2: 0/2 yes (rate=0.000000, blank=2)
- torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_1: 0/2 yes (rate=0.000000, blank=2)
- torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_2: 0/2 yes (rate=0.000000, blank=2)
- torwic_cross_month_aisle_bundle_v1__2022-10-12__Aisle_CCW: 0/2 yes (rate=0.000000, blank=2)
- torwic_cross_month_aisle_bundle_v1__2022-10-12__Aisle_CW: 0/2 yes (rate=0.000000, blank=2)
- torwic_hallway_benchmark_batch2_v1__2022-06-15__Hallway_Full_CCW: 0/2 yes (rate=0.000000, blank=2)
- torwic_hallway_benchmark_batch2_v1__2022-06-15__Hallway_Full_CW: 0/2 yes (rate=0.000000, blank=2)
- torwic_hallway_benchmark_batch2_v1__2022-06-15__Hallway_Straight_CCW: 0/1 yes (rate=0.000000, blank=1)
- torwic_hallway_benchmark_batch2_v1__2022-06-23__Hallway_Full_CW: 0/2 yes (rate=0.000000, blank=2)
- torwic_hallway_benchmark_batch2_v1__2022-06-23__Hallway_Straight_CCW: 0/2 yes (rate=0.000000, blank=2)
- torwic_hallway_benchmark_batch2_v1__2022-06-23__Hallway_Straight_CW: 0/1 yes (rate=0.000000, blank=1)
- torwic_hallway_benchmark_batch2_v1__2022-10-12__Hallway_Full_CW_Run_1: 0/1 yes (rate=0.000000, blank=1)
- torwic_hallway_benchmark_batch2_v1__2022-10-12__Hallway_Full_CW_Run_2: 0/2 yes (rate=0.000000, blank=2)
- torwic_hallway_benchmark_batch2_v1__2022-10-12__Hallway_Straight_CCW: 0/2 yes (rate=0.000000, blank=2)
- torwic_hallway_benchmark_batch2_v1__2022-10-12__Hallway_Straight_CW: 0/1 yes (rate=0.000000, blank=1)
- torwic_same_day_aisle_bundle_v1__2022-06-15__Aisle_CCW_Run_1: 0/2 yes (rate=0.000000, blank=2)
- torwic_same_day_aisle_bundle_v1__2022-06-15__Aisle_CCW_Run_2: 0/2 yes (rate=0.000000, blank=2)

## Rows Requiring Attention

- Rows with `quality_blocker=yes`: 0
- Rows with invalid allowed values: 0
- Rows with possible label-decision text in `reviewer_note`: 0

## Scientific Boundary

P208 is read-only evidence-quality QA. It does not fill or infer `human_admit_label` or `human_same_object_label`, does not use weak/model/selection fields as labels, does not train, and does not alter raw images or data.
