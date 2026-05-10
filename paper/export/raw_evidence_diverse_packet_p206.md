# P206 Diverse Raw Evidence Packet

**Status:** DIVERSE_AUDIT_PACKET_BUILT_P195_STILL_BLOCKED

## Boundary

No-label raw evidence inspection packet only. P206 improves packet diversity for local raw RGB/depth/segmentation evidence review. It does not create or infer admission/same-object labels, does not use weak targets/model predictions as labels, and does not train admission-control or semantic-stability models.

## Coverage

- Samples: 32
- Categories: {'barrier': 8, 'forklift': 8, 'warehouse rack': 8, 'work table': 8}
- Sources: {'cross_day': 8, 'cross_month': 4, 'hallway': 16, 'same_day': 4}
- Row sources: {'p193': 6, 'p197_boundary': 6, 'p197_pair': 14, 'p199': 6}
- Sessions: 18
- Raw evidence paths: 192/192 existing
- Duplicate sample-id groups: 0
- Duplicate session/frame groups: 0
- Duplicate nonblank physical-key groups: 0

## Tradeoffs

- Uncovered secondary coverage tokens: ['category_row_source:forklift|p197_boundary', 'source_row_source:cross_month|p197_boundary', 'source_row_source:same_day|p193']
- Blank physical keys are unavoidable for P197 boundary and pair rows because those rows do not carry physical keys in the P203 index.

## Label Gate

- P195 remains `BLOCKED`.
- Packet rows contain no human admission labels, no human same-object labels, no weak targets, and no model predictions.
- Blank note columns are for raw-evidence quality comments only.

## Sample Index

| audit_sample_id | category | source | row_source | session | frame | why_sampled |
| --- | --- | --- | --- | --- | --- | --- |
| p206_001 | forklift | hallway | p193 | torwic_hallway_benchmark_batch2_v1__2022-06-15__Hallway_Full_CCW | 7 | adds category coverage: forklift; adds source coverage: hallway; adds row_source coverage: p193; adds category/source coverage: forklift\|hallway; adds category/row_source coverage: forklift\|p193; adds source/row_source coverage: hallway\|p193; adds session coverage: torwic_hallway_benchmark_batch2_v1__2022-06-15__Hallway_Full_CCW |
| p206_002 | warehouse rack | hallway | p193 | torwic_hallway_benchmark_batch2_v1__2022-06-23__Hallway_Straight_CCW | 7 | adds category coverage: warehouse rack; adds category/source coverage: warehouse rack\|hallway; adds category/row_source coverage: warehouse rack\|p193; adds session coverage: torwic_hallway_benchmark_batch2_v1__2022-06-23__Hallway_Straight_CCW |
| p206_003 | barrier | hallway | p193 | torwic_hallway_benchmark_batch2_v1__2022-10-12__Hallway_Full_CW_Run_1 | 7 | adds category coverage: barrier; adds category/source coverage: barrier\|hallway; adds category/row_source coverage: barrier\|p193; adds session coverage: torwic_hallway_benchmark_batch2_v1__2022-10-12__Hallway_Full_CW_Run_1 |
| p206_004 | barrier | cross_day | p193 | torwic_cross_day_aisle_bundle_v1__2022-06-15__Aisle_CW_Run_2 | 7 | adds source coverage: cross_day; adds category/source coverage: barrier\|cross_day; adds source/row_source coverage: cross_day\|p193; adds session coverage: torwic_cross_day_aisle_bundle_v1__2022-06-15__Aisle_CW_Run_2 |
| p206_005 | forklift | cross_day | p193 | torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_2 | 7 | adds category/source coverage: forklift\|cross_day; adds session coverage: torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_2 |
| p206_006 | work table | cross_month | p193 | torwic_cross_month_aisle_bundle_v1__2022-10-12__Aisle_CCW | 7 | adds category coverage: work table; adds source coverage: cross_month; adds category/source coverage: work table\|cross_month; adds category/row_source coverage: work table\|p193; adds source/row_source coverage: cross_month\|p193; adds session coverage: torwic_cross_month_aisle_bundle_v1__2022-10-12__Aisle_CCW |
| p206_007 | work table | hallway | p199 | torwic_hallway_benchmark_batch2_v1__2022-10-12__Hallway_Full_CW_Run_2 | 7 | adds row_source coverage: p199; adds category/source coverage: work table\|hallway; adds category/row_source coverage: work table\|p199; adds source/row_source coverage: hallway\|p199; adds session coverage: torwic_hallway_benchmark_batch2_v1__2022-10-12__Hallway_Full_CW_Run_2 |
| p206_008 | warehouse rack | hallway | p199 | torwic_hallway_benchmark_batch2_v1__2022-06-23__Hallway_Full_CW | 7 | adds category/row_source coverage: warehouse rack\|p199; adds session coverage: torwic_hallway_benchmark_batch2_v1__2022-06-23__Hallway_Full_CW |
| p206_009 | warehouse rack | hallway | p199 | torwic_hallway_benchmark_batch2_v1__2022-06-23__Hallway_Straight_CW | 7 | adds session coverage: torwic_hallway_benchmark_batch2_v1__2022-06-23__Hallway_Straight_CW |
| p206_010 | barrier | cross_day | p199 | torwic_cross_day_aisle_bundle_v1__2022-06-15__Aisle_CW_Run_1 | 7 | adds category/row_source coverage: barrier\|p199; adds source/row_source coverage: cross_day\|p199; adds session coverage: torwic_cross_day_aisle_bundle_v1__2022-06-15__Aisle_CW_Run_1 |
| p206_011 | forklift | same_day | p199 | torwic_same_day_aisle_bundle_v1__2022-06-15__Aisle_CCW_Run_2 | 7 | adds source coverage: same_day; adds category/source coverage: forklift\|same_day; adds category/row_source coverage: forklift\|p199; adds source/row_source coverage: same_day\|p199; adds session coverage: torwic_same_day_aisle_bundle_v1__2022-06-15__Aisle_CCW_Run_2 |
| p206_012 | barrier | cross_month | p199 | torwic_cross_month_aisle_bundle_v1__2022-10-12__Aisle_CW | 7 | adds category/source coverage: barrier\|cross_month; adds source/row_source coverage: cross_month\|p199; adds session coverage: torwic_cross_month_aisle_bundle_v1__2022-10-12__Aisle_CW |
| p206_013 | warehouse rack | cross_day | p197_boundary | torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_1 | 7 | adds row_source coverage: p197_boundary; adds category/source coverage: warehouse rack\|cross_day; adds category/row_source coverage: warehouse rack\|p197_boundary; adds source/row_source coverage: cross_day\|p197_boundary; adds session coverage: torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_1 |
| p206_014 | barrier | hallway | p197_boundary | torwic_hallway_benchmark_batch2_v1__2022-06-15__Hallway_Full_CW | 7 | adds category/row_source coverage: barrier\|p197_boundary; adds source/row_source coverage: hallway\|p197_boundary; adds session coverage: torwic_hallway_benchmark_batch2_v1__2022-06-15__Hallway_Full_CW |
| p206_015 | work table | hallway | p197_boundary | torwic_hallway_benchmark_batch2_v1__2022-06-15__Hallway_Straight_CCW | 1 | adds category/row_source coverage: work table\|p197_boundary; adds session coverage: torwic_hallway_benchmark_batch2_v1__2022-06-15__Hallway_Straight_CCW |
| p206_016 | work table | hallway | p197_boundary | torwic_hallway_benchmark_batch2_v1__2022-10-12__Hallway_Straight_CCW | 7 | adds session coverage: torwic_hallway_benchmark_batch2_v1__2022-10-12__Hallway_Straight_CCW |
| p206_017 | work table | hallway | p197_boundary | torwic_hallway_benchmark_batch2_v1__2022-10-12__Hallway_Straight_CW | 7 | adds session coverage: torwic_hallway_benchmark_batch2_v1__2022-10-12__Hallway_Straight_CW |
| p206_018 | work table | same_day | p197_boundary | torwic_same_day_aisle_bundle_v1__2022-06-15__Aisle_CCW_Run_1 | 7 | adds category/source coverage: work table\|same_day; adds source/row_source coverage: same_day\|p197_boundary; adds session coverage: torwic_same_day_aisle_bundle_v1__2022-06-15__Aisle_CCW_Run_1 |
| p206_019 | warehouse rack | hallway | p197_pair | torwic_hallway_benchmark_batch2_v1__2022-06-23__Hallway_Full_CW | 000007 | adds row_source coverage: p197_pair; adds category/row_source coverage: warehouse rack\|p197_pair; adds source/row_source coverage: hallway\|p197_pair |
| p206_020 | warehouse rack | hallway | p197_pair | torwic_hallway_benchmark_batch2_v1__2022-10-12__Hallway_Full_CW_Run_2 | 000007 | fills diversity cap while preserving unique sample/frame constraints |
| p206_021 | forklift | hallway | p197_pair | torwic_hallway_benchmark_batch2_v1__2022-06-23__Hallway_Straight_CCW | 000007 | adds category/row_source coverage: forklift\|p197_pair |
| p206_022 | barrier | hallway | p197_pair | torwic_hallway_benchmark_batch2_v1__2022-06-15__Hallway_Full_CW | 000007 | adds category/row_source coverage: barrier\|p197_pair |
| p206_023 | warehouse rack | cross_day | p197_pair | torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_1 | 000007 | adds source/row_source coverage: cross_day\|p197_pair |
| p206_024 | warehouse rack | hallway | p197_pair | torwic_hallway_benchmark_batch2_v1__2022-06-15__Hallway_Full_CCW | 000007 | fills diversity cap while preserving unique sample/frame constraints |
| p206_025 | work table | cross_day | p197_pair | torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_2 | 000007 | adds category/source coverage: work table\|cross_day; adds category/row_source coverage: work table\|p197_pair |
| p206_026 | forklift | cross_month | p197_pair | torwic_cross_month_aisle_bundle_v1__2022-10-12__Aisle_CCW | 000007 | adds category/source coverage: forklift\|cross_month; adds source/row_source coverage: cross_month\|p197_pair |
| p206_027 | forklift | cross_month | p197_pair | torwic_cross_month_aisle_bundle_v1__2022-10-12__Aisle_CW | 000007 | fills diversity cap while preserving unique sample/frame constraints |
| p206_028 | work table | cross_day | p197_pair | torwic_cross_day_aisle_bundle_v1__2022-06-15__Aisle_CW_Run_2 | 000007 | fills diversity cap while preserving unique sample/frame constraints |
| p206_029 | forklift | hallway | p197_pair | torwic_hallway_benchmark_batch2_v1__2022-10-12__Hallway_Straight_CCW | 000007 | fills diversity cap while preserving unique sample/frame constraints |
| p206_030 | barrier | same_day | p197_pair | torwic_same_day_aisle_bundle_v1__2022-06-15__Aisle_CCW_Run_2 | 000007 | adds category/source coverage: barrier\|same_day; adds source/row_source coverage: same_day\|p197_pair |
| p206_031 | barrier | same_day | p197_pair | torwic_same_day_aisle_bundle_v1__2022-06-15__Aisle_CCW_Run_1 | 000007 | fills diversity cap while preserving unique sample/frame constraints |
| p206_032 | forklift | cross_day | p197_pair | torwic_cross_day_aisle_bundle_v1__2022-06-15__Aisle_CW_Run_1 | 000007 | fills diversity cap while preserving unique sample/frame constraints |

## P207 Recommendation

Use the P206 packet as the preferred no-label raw-evidence audit set. Keep P195 blocked until independent human admission and same-object labels exist.
