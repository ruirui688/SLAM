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

## Dynamic SLAM Backend Metrics

| Experiment | Raw APE | Masked APE | Raw RPE | Masked RPE | Mask coverage |
|---|---:|---:|---:|---:|---:|
| P132/P133 8-frame DROID-SLAM smoke | 0.001242 | 0.001243 | 0.00225 | 0.002255 |  |
| P134 64-frame DROID-SLAM global BA | 0.051135 | 0.051136 | 0.032713 | 0.032713 |  |
| P135 existing semantic masks | 0.051135 | 0.051135 | 0.032713 | 0.032713 | 3/64 (0.025750%) |
| P136 temporal mask stress test | 0.051135 | 0.051222 | 0.032713 | 0.03271 | 16/64 (0.267154%) |
| P137 optical-flow mask stress test | 0.051135 | 0.051222 | 0.032713 | 0.03271 | 16/64 (0.267154%) |
| P138 first-eight real semantic masks | 0.051135 | 0.051177 | 0.032713 | 0.032712 | 8/64 (0.118100%) |

## Tracked Files

- `protocol_summary.csv`: compact table for paper/result table reuse.
- `retained_clusters.csv`: retained cluster-level traceability.
- `rejected_clusters.csv`: rejected cluster-level traceability.
- `evidence_summary.json`: full digest with source artifact paths.
- `dynamic_slam_backend_metrics.csv`: compact APE/RPE backend table.
- `dynamic_slam_backend_metrics.json`: full backend metric digest.

## Source Artifact Policy

The source JSON and markdown artifacts remain under ignored `outputs/` paths.
This pack records their relative paths in `evidence_summary.json` and should
be refreshed whenever the underlying protocol outputs change.
