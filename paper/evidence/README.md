# Paper Evidence Pack

This directory is the Git-tracked digest of the current TorWIC evidence.
It is regenerated from ignored experiment outputs under `outputs/` so the
paper tables remain auditable without committing raw data, model outputs,
videos, point clouds, or full generated output directories.

Regenerate from the repository root:

```bash
make evidence-pack
```

## Protocol Summary

| Protocol | Role | Sessions | Frame objects | Clusters | Retained | Rejected | Dynamic rejected |
|---|---|---:|---:|---:|---:|---:|---:|
| Same-day Aisle | Primary Aisle ladder | 4 | 203 | 11 | 5 | 6 | 3 |
| Cross-day Aisle | Primary Aisle ladder | 4 | 240 | 10 | 5 | 5 | 3 |
| Cross-month Aisle | Primary Aisle ladder | 6 | 297 | 14 | 7 | 7 | 5 |
| Hallway broader validation | Secondary scene-transfer validation | 10 | 537 | 16 | 9 | 7 | 4 |

## Rejection Reason Totals

| Reason | Count |
|---|---:|
| `dynamic_contamination` | 15 |
| `insufficient_frame_support` | 6 |
| `label_fragmentation` | 3 |
| `low_support` | 6 |
| `single_session_or_low_session_support` | 12 |

## Tracked Files

- `protocol_summary.csv`: compact table for paper/result table reuse.
- `retained_clusters.csv`: retained cluster-level traceability.
- `rejected_clusters.csv`: rejected cluster-level traceability.
- `evidence_summary.json`: full digest with source artifact paths.

## Source Artifact Policy

The source JSON and markdown artifacts remain under ignored `outputs/` paths.
This pack records their relative paths in `evidence_summary.json` and should
be refreshed whenever the underlying protocol outputs change.
