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
| P139 first-sixteen real semantic masks | 0.051135 | 0.051182 | 0.032713 | 0.032711 | 16/64 (0.263896%) |
| P140 first-thirty-two real semantic masks | 0.051135 | 0.051189 | 0.032713 | 0.032711 | 32/64 (0.567722%) |
| P141 dynamic SLAM window-selection diagnostic | — | — | — | — | 32/64 (0.567722%) |
| P142 top4 concentrated dynamic masking | 0.051135 | 0.051135 | 0.032713 | 0.032713 | 4/64 (0.082921%) |
| P142 top8 concentrated dynamic masking | 0.051135 | 0.051132 | 0.032713 | 0.032713 | 8/64 (0.162823%) |
| P142 top16 concentrated dynamic masking | 0.051135 | 0.051122 | 0.032713 | 0.032713 | 16/64 (0.316157%) |

P142 tests concentrated masking on the highest-coverage forklift frames rather
than uniformly masking all available frames. The result remains
trajectory-neutral (`|ΔAPE| < 0.06 mm`), while the sign asymmetry between
concentrated and uniform masking suggests that boundary-feature loss in
low-coverage frames is the dominant artifact. The next active research step is
P143: screen other TorWIC windows for dynamic objects covering more than 5% of
the frame before expecting an ATE/RPE gain.

### P143 Cross-Window Dynamic Content Audit

- Artifact: `outputs/torwic_p143_cross_window_dynamic_audit_v1.{json,md}`.
- Key finding: no locally available TorWIC sequence has forklift coverage above
  `1.39%` of the frame; the `1.39% -> 5%` gap would require roughly `1.9x`
  closer camera-target proximity.
- Interpretation: P135-P143 now form a bounded negative-result study showing
  DROID-SLAM trajectory estimates are robust to industrial dynamic objects
  below roughly `2%` frame coverage in these aisle traverses.
- Next paper step: integrate the full P135-P143 chain as a self-contained
  dynamic SLAM backend chapter with explicit boundary conditions.

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
