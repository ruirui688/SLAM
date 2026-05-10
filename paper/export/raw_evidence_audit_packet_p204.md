# P204 Raw Evidence Audit Packet

**Status:** AUDIT_PACKET_BUILT_P195_STILL_BLOCKED

## Boundary

No-label raw evidence inspection packet only. It samples P203 raw RGB/depth/segmentation evidence for reviewer inspection and audit coverage. It does not create or infer admission/same-object labels, does not use weak targets/model predictions as labels, and does not train admission-control or semantic-stability models.

## Inputs and Outputs

- Input P203 index: `paper/evidence/raw_segmentation_evidence_index_p203.csv`
- JSON packet: `paper/evidence/raw_evidence_audit_packet_p204.json`
- CSV packet: `paper/evidence/raw_evidence_audit_packet_p204.csv`

## Coverage

- Samples: 32
- Categories: {'barrier': 17, 'forklift': 6, 'warehouse rack': 4, 'work table': 5}
- Sources: {'cross_day': 17, 'cross_month': 4, 'hallway': 7, 'same_day': 4}
- Row sources: {'p193': 13, 'p197_boundary': 6, 'p197_pair': 8, 'p199': 5}
- Sessions: 12
- Raw evidence paths: 192/192 existing
- All referenced paths exist: True
- Non-label inspection note fields blank: True

## Label Gate

- P195 remains `BLOCKED`.
- Packet rows contain no human admission labels, no human same-object labels, no weak targets, and no model predictions.
- Blank note columns are for raw-evidence inspection comments only; they must not be used to record admission or same-object labels.

## Sample Index

| audit_sample_id | category | source | row_source | session | frame | why_sampled |
| --- | --- | --- | --- | --- | --- | --- |
| p204_001 | forklift | hallway | p193 | torwic_hallway_benchmark_batch2_v1__2022-06-15__Hallway_Full_CCW | 7 | adds category coverage: forklift; adds source coverage: hallway; adds row_source coverage: p193; adds category/source coverage: forklift\|hallway; adds category/row_source coverage: forklift\|p193; adds source/row_source coverage: hallway\|p193; adds session coverage: torwic_hallway_benchmark_batch2_v1__2022-06-15__Hallway_Full_CCW |
| p204_002 | warehouse rack | hallway | p193 | torwic_hallway_benchmark_batch2_v1__2022-06-23__Hallway_Straight_CCW | 7 | adds category coverage: warehouse rack; adds category/source coverage: warehouse rack\|hallway; adds category/row_source coverage: warehouse rack\|p193; adds session coverage: torwic_hallway_benchmark_batch2_v1__2022-06-23__Hallway_Straight_CCW |
| p204_003 | barrier | cross_day | p193 | torwic_cross_day_aisle_bundle_v1__2022-06-15__Aisle_CW_Run_1 | 7 | adds category coverage: barrier; adds source coverage: cross_day; adds category/source coverage: barrier\|cross_day; adds category/row_source coverage: barrier\|p193; adds source/row_source coverage: cross_day\|p193; adds session coverage: torwic_cross_day_aisle_bundle_v1__2022-06-15__Aisle_CW_Run_1 |
| p204_004 | barrier | cross_day | p193 | torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_1 | 7 | adds session coverage: torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_1 |
| p204_005 | barrier | cross_day | p193 | torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_1 | 7 | fills deterministic packet cap with additional unique physical evidence |
| p204_006 | barrier | cross_day | p193 | torwic_cross_day_aisle_bundle_v1__2022-06-15__Aisle_CW_Run_1 | 7 | fills deterministic packet cap with additional unique physical evidence |
| p204_007 | work table | cross_day | p193 | torwic_cross_day_aisle_bundle_v1__2022-06-15__Aisle_CW_Run_2 | 7 | adds category coverage: work table; adds category/source coverage: work table\|cross_day; adds category/row_source coverage: work table\|p193; adds session coverage: torwic_cross_day_aisle_bundle_v1__2022-06-15__Aisle_CW_Run_2 |
| p204_008 | barrier | cross_day | p193 | torwic_cross_day_aisle_bundle_v1__2022-06-15__Aisle_CW_Run_2 | 7 | fills deterministic packet cap with additional unique physical evidence |
| p204_009 | barrier | cross_day | p193 | torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_2 | 7 | adds session coverage: torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_2 |
| p204_010 | barrier | cross_day | p193 | torwic_cross_day_aisle_bundle_v1__2022-06-15__Aisle_CW_Run_2 | 7 | fills deterministic packet cap with additional unique physical evidence |
| p204_011 | barrier | cross_day | p193 | torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_2 | 7 | fills deterministic packet cap with additional unique physical evidence |
| p204_012 | barrier | same_day | p193 | torwic_same_day_aisle_bundle_v1__2022-06-15__Aisle_CCW_Run_2 | 7 | adds source coverage: same_day; adds category/source coverage: barrier\|same_day; adds source/row_source coverage: same_day\|p193; adds session coverage: torwic_same_day_aisle_bundle_v1__2022-06-15__Aisle_CCW_Run_2 |
| p204_013 | work table | cross_month | p193 | torwic_cross_month_aisle_bundle_v1__2022-10-12__Aisle_CW | 7 | adds source coverage: cross_month; adds category/source coverage: work table\|cross_month; adds source/row_source coverage: cross_month\|p193; adds session coverage: torwic_cross_month_aisle_bundle_v1__2022-10-12__Aisle_CW |
| p204_014 | work table | hallway | p199 | torwic_hallway_benchmark_batch2_v1__2022-06-15__Hallway_Full_CW | 7 | adds row_source coverage: p199; adds category/source coverage: work table\|hallway; adds category/row_source coverage: work table\|p199; adds source/row_source coverage: hallway\|p199; adds session coverage: torwic_hallway_benchmark_batch2_v1__2022-06-15__Hallway_Full_CW |
| p204_015 | warehouse rack | hallway | p199 | torwic_hallway_benchmark_batch2_v1__2022-06-23__Hallway_Full_CW | 7 | adds category/row_source coverage: warehouse rack\|p199; adds session coverage: torwic_hallway_benchmark_batch2_v1__2022-06-23__Hallway_Full_CW |
| p204_016 | barrier | cross_day | p199 | torwic_cross_day_aisle_bundle_v1__2022-06-15__Aisle_CW_Run_1 | 7 | adds category/row_source coverage: barrier\|p199; adds source/row_source coverage: cross_day\|p199 |
| p204_017 | forklift | same_day | p199 | torwic_same_day_aisle_bundle_v1__2022-06-15__Aisle_CCW_Run_1 | 7 | adds category/source coverage: forklift\|same_day; adds category/row_source coverage: forklift\|p199; adds source/row_source coverage: same_day\|p199; adds session coverage: torwic_same_day_aisle_bundle_v1__2022-06-15__Aisle_CCW_Run_1 |
| p204_018 | forklift | cross_month | p199 | torwic_cross_month_aisle_bundle_v1__2022-10-12__Aisle_CW | 7 | adds category/source coverage: forklift\|cross_month; adds source/row_source coverage: cross_month\|p199 |
| p204_019 | barrier | cross_day | p197_boundary | torwic_cross_day_aisle_bundle_v1__2022-06-15__Aisle_CW_Run_1 | 7 | adds row_source coverage: p197_boundary; adds category/row_source coverage: barrier\|p197_boundary; adds source/row_source coverage: cross_day\|p197_boundary |
| p204_020 | barrier | cross_day | p197_boundary | torwic_cross_day_aisle_bundle_v1__2022-06-15__Aisle_CW_Run_2 | 7 | fills deterministic packet cap with additional unique physical evidence |
| p204_021 | warehouse rack | cross_day | p197_boundary | torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_1 | 7 | adds category/source coverage: warehouse rack\|cross_day; adds category/row_source coverage: warehouse rack\|p197_boundary |
| p204_022 | barrier | cross_month | p197_boundary | torwic_cross_month_aisle_bundle_v1__2022-10-12__Aisle_CCW | 7 | adds category/source coverage: barrier\|cross_month; adds source/row_source coverage: cross_month\|p197_boundary; adds session coverage: torwic_cross_month_aisle_bundle_v1__2022-10-12__Aisle_CCW |
| p204_023 | forklift | hallway | p197_boundary | torwic_hallway_benchmark_batch2_v1__2022-06-15__Hallway_Full_CCW | 7 | adds category/row_source coverage: forklift\|p197_boundary; adds source/row_source coverage: hallway\|p197_boundary |
| p204_024 | work table | same_day | p197_boundary | torwic_same_day_aisle_bundle_v1__2022-06-15__Aisle_CCW_Run_1 | 7 | adds category/source coverage: work table\|same_day; adds category/row_source coverage: work table\|p197_boundary; adds source/row_source coverage: same_day\|p197_boundary |
| p204_025 | warehouse rack | hallway | p197_pair | torwic_hallway_benchmark_batch2_v1__2022-06-23__Hallway_Full_CW | 000007 | adds row_source coverage: p197_pair; adds category/row_source coverage: warehouse rack\|p197_pair; adds source/row_source coverage: hallway\|p197_pair |
| p204_026 | barrier | hallway | p197_pair | torwic_hallway_benchmark_batch2_v1__2022-06-23__Hallway_Full_CW | 000007 | adds category/source coverage: barrier\|hallway; adds category/row_source coverage: barrier\|p197_pair |
| p204_027 | forklift | cross_day | p197_pair | torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_1 | 000007 | adds category/source coverage: forklift\|cross_day; adds category/row_source coverage: forklift\|p197_pair; adds source/row_source coverage: cross_day\|p197_pair |
| p204_028 | barrier | cross_day | p197_pair | torwic_cross_day_aisle_bundle_v1__2022-06-15__Aisle_CW_Run_1 | 000007 | fills deterministic packet cap with additional unique physical evidence |
| p204_029 | barrier | cross_day | p197_pair | torwic_cross_day_aisle_bundle_v1__2022-06-15__Aisle_CW_Run_2 | 000007 | fills deterministic packet cap with additional unique physical evidence |
| p204_030 | barrier | cross_day | p197_pair | torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_1 | 000007 | fills deterministic packet cap with additional unique physical evidence |
| p204_031 | forklift | cross_month | p197_pair | torwic_cross_month_aisle_bundle_v1__2022-10-12__Aisle_CCW | 000007 | adds source/row_source coverage: cross_month\|p197_pair |
| p204_032 | work table | same_day | p197_pair | torwic_same_day_aisle_bundle_v1__2022-06-15__Aisle_CCW_Run_1 | 000007 | adds category/row_source coverage: work table\|p197_pair; adds source/row_source coverage: same_day\|p197_pair |

## P205 Recommendation

Use this packet for human/agent raw-evidence inspection and to identify missing or ambiguous visual evidence. Keep P195 blocked until independent human admission and same-object labels exist; do not convert inspection notes into labels without a separate reviewed labeling protocol.
