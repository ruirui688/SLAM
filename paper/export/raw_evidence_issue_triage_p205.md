# P205 Raw Evidence Issue Triage

**Status:** ISSUE_TRIAGE_COMPLETE_P195_STILL_BLOCKED

## Boundary

Raw evidence QA only. P205 validates local file existence, readability, image dimensions, segmentation non-triviality, depth readability/statistics, and packet diversity. It does not create or infer admission/same-object labels, does not use weak targets/model predictions as labels, and does not train admission-control or semantic-stability models.

## Inputs and Outputs

- P204 packet: `paper/evidence/raw_evidence_audit_packet_p204.json`
- P203 index: `paper/evidence/raw_segmentation_evidence_index_p203.json`
- JSON triage: `paper/evidence/raw_evidence_issue_triage_p205.json`
- CSV triage: `paper/evidence/raw_evidence_issue_triage_p205.csv`

## Summary

- Samples triaged: 32
- Referenced paths: 192/192 existing
- Readable images: 192/192
- Rows by issue level: {'OK': 5, 'WARN': 27}
- Issue counts: {}
- Warning counts: {'duplicate_sample_id': 15, 'duplicate_session_frame': 23}
- Dimension counts: {'1280x720': 32}

## Diversity Flags

- Unique physical keys: 18/18 nonblank rows
- Duplicate physical keys: 0
- Unique session/frame pairs: 18/32 rows
- Duplicate session/frame pairs: 9
- Duplicate sample IDs: 7

## Row Triage

| sample | level | dimensions | issue_codes | warning_codes | depth_nonzero_pixels |
| --- | --- | --- | --- | --- | --- |
| p204_001 | WARN | 1280x720 |  | duplicate_sample_id;duplicate_session_frame | 326896 |
| p204_002 | OK | 1280x720 |  |  | 326202 |
| p204_003 | WARN | 1280x720 |  | duplicate_session_frame | 464205 |
| p204_004 | WARN | 1280x720 |  | duplicate_session_frame | 333913 |
| p204_005 | WARN | 1280x720 |  | duplicate_sample_id;duplicate_session_frame | 333913 |
| p204_006 | WARN | 1280x720 |  | duplicate_sample_id;duplicate_session_frame | 464205 |
| p204_007 | WARN | 1280x720 |  | duplicate_session_frame | 449233 |
| p204_008 | WARN | 1280x720 |  | duplicate_session_frame | 449233 |
| p204_009 | WARN | 1280x720 |  | duplicate_session_frame | 326615 |
| p204_010 | WARN | 1280x720 |  | duplicate_sample_id;duplicate_session_frame | 449233 |
| p204_011 | WARN | 1280x720 |  | duplicate_session_frame | 326615 |
| p204_012 | OK | 1280x720 |  |  | 455565 |
| p204_013 | WARN | 1280x720 |  | duplicate_session_frame | 294499 |
| p204_014 | OK | 1280x720 |  |  | 471987 |
| p204_015 | WARN | 1280x720 |  | duplicate_sample_id | 329308 |
| p204_016 | WARN | 1280x720 |  | duplicate_sample_id;duplicate_session_frame | 464205 |
| p204_017 | WARN | 1280x720 |  | duplicate_session_frame | 463435 |
| p204_018 | WARN | 1280x720 |  | duplicate_session_frame | 294499 |
| p204_019 | WARN | 1280x720 |  | duplicate_sample_id;duplicate_session_frame | 464205 |
| p204_020 | WARN | 1280x720 |  | duplicate_sample_id;duplicate_session_frame | 449233 |
| p204_021 | WARN | 1280x720 |  | duplicate_session_frame | 333913 |
| p204_022 | OK | 1280x720 |  |  | 292161 |
| p204_023 | WARN | 1280x720 |  | duplicate_sample_id;duplicate_session_frame | 326896 |
| p204_024 | WARN | 1280x720 |  | duplicate_sample_id;duplicate_session_frame | 463435 |
| p204_025 | WARN | 1280x720 |  | duplicate_sample_id;duplicate_session_frame | 329308 |
| p204_026 | WARN | 1280x720 |  | duplicate_session_frame | 329308 |
| p204_027 | WARN | 1280x720 |  | duplicate_session_frame | 333913 |
| p204_028 | WARN | 1280x720 |  | duplicate_sample_id | 464205 |
| p204_029 | WARN | 1280x720 |  | duplicate_sample_id | 449233 |
| p204_030 | WARN | 1280x720 |  | duplicate_sample_id;duplicate_session_frame | 333913 |
| p204_031 | OK | 1280x720 |  |  | 292161 |
| p204_032 | WARN | 1280x720 |  | duplicate_sample_id | 463435 |

## Label Gate

- P195 remains `BLOCKED`.
- Human admission and same-object label fields remain blank in the independent-supervision gate.
- This triage records file/readability/shape/non-empty evidence issues only; it does not support admission-control claims.

## P206 Recommendation

Use P205 as the raw-evidence QA baseline. If a future review step is needed, create a separate no-training visual inspection protocol that records evidence quality notes only, while keeping admission/same-object labels behind the independent human-label workflow.
