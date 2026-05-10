# P206 Diverse Raw Evidence Packet Triage

**Status:** DIVERSE_PACKET_TRIAGE_COMPLETE_P195_STILL_BLOCKED

## Boundary

Raw evidence QA only. P206 validates local file existence, readability, image dimensions, segmentation non-triviality, depth readability/statistics, and packet diversity. It does not create or infer admission/same-object labels, does not use weak targets/model predictions as labels, and does not train admission-control or semantic-stability models.

## Summary

- Samples triaged: 32
- Referenced paths: 192/192 existing
- Readable images: 192/192
- Rows by issue level: {'OK': 32}
- Issue counts: {}
- Warning counts: {}
- Dimension counts: {'1280x720': 32}

## Diversity Flags

- Unique physical keys: 12/12 nonblank rows
- Duplicate physical-key groups: 0
- Unique session/frame pairs: 32/32 rows
- Duplicate session/frame groups: 0
- Duplicate sample-id groups: 0

## Row Triage

| sample | level | dimensions | issue_codes | warning_codes | depth_nonzero_pixels |
| --- | --- | --- | --- | --- | --- |
| p206_001 | OK | 1280x720 |  |  | 326896 |
| p206_002 | OK | 1280x720 |  |  | 326202 |
| p206_003 | OK | 1280x720 |  |  | 315311 |
| p206_004 | OK | 1280x720 |  |  | 449233 |
| p206_005 | OK | 1280x720 |  |  | 326615 |
| p206_006 | OK | 1280x720 |  |  | 292161 |
| p206_007 | OK | 1280x720 |  |  | 329308 |
| p206_008 | OK | 1280x720 |  |  | 329308 |
| p206_009 | OK | 1280x720 |  |  | 332281 |
| p206_010 | OK | 1280x720 |  |  | 464205 |
| p206_011 | OK | 1280x720 |  |  | 455565 |
| p206_012 | OK | 1280x720 |  |  | 294499 |
| p206_013 | OK | 1280x720 |  |  | 333913 |
| p206_014 | OK | 1280x720 |  |  | 471987 |
| p206_015 | OK | 1280x720 |  |  | 470590 |
| p206_016 | OK | 1280x720 |  |  | 303435 |
| p206_017 | OK | 1280x720 |  |  | 293890 |
| p206_018 | OK | 1280x720 |  |  | 463435 |
| p206_019 | OK | 1280x720 |  |  | 329308 |
| p206_020 | OK | 1280x720 |  |  | 329308 |
| p206_021 | OK | 1280x720 |  |  | 326202 |
| p206_022 | OK | 1280x720 |  |  | 471987 |
| p206_023 | OK | 1280x720 |  |  | 333913 |
| p206_024 | OK | 1280x720 |  |  | 326896 |
| p206_025 | OK | 1280x720 |  |  | 326615 |
| p206_026 | OK | 1280x720 |  |  | 292161 |
| p206_027 | OK | 1280x720 |  |  | 294499 |
| p206_028 | OK | 1280x720 |  |  | 449233 |
| p206_029 | OK | 1280x720 |  |  | 303435 |
| p206_030 | OK | 1280x720 |  |  | 455565 |
| p206_031 | OK | 1280x720 |  |  | 463435 |
| p206_032 | OK | 1280x720 |  |  | 464205 |

## Label Gate

- P195 remains `BLOCKED`.
- Human admission and same-object label fields remain blank in the independent-supervision gate.
- This triage records file/readability/shape/non-empty evidence issues only.
