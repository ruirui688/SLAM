# Dynamic Industrial Semantic-Segmentation-Assisted SLAM

This repository tracks the paper-facing code, protocol configuration, and
documentation for a research project on **semantic-segmentation-assisted SLAM
in dynamic industrial environments**.

The current paper direction is clear:

- use open-vocabulary semantic segmentation as an RGB-D object evidence source;
- convert detections into auditable object-map maintenance records;
- retain stable semantic landmarks across industrial revisits;
- reject dynamic or transient object evidence before it pollutes the persistent
  SLAM map;
- present the contribution as a bounded systems paper, not as a final lifelong
  SLAM benchmark or downstream navigation-gain claim.

Raw datasets, generated experiment outputs, videos, point clouds, model weights,
and temporary files are intentionally excluded from Git. Dataset provenance and
download entrypoints are documented in [`DATA_SOURCES.md`](./DATA_SOURCES.md)
and [`DATA_ORGANIZATION.md`](./DATA_ORGANIZATION.md).

## Paper Drafts

The repository now contains visible manuscript drafts:

| Draft | Path | Purpose |
|---|---|---|
| English manuscript | [`paper/manuscript_en.md`](./paper/manuscript_en.md) | Current English paper draft for direct GitHub review |
| Chinese manuscript | [`paper/manuscript_zh.md`](./paper/manuscript_zh.md) | Chinese companion draft for project tracking and discussion |

These Markdown drafts are Git-tracked progress artifacts. They summarize the
current submission-ready argument and point back to ignored local evidence under
`outputs/` when needed.

## Current Evidence Stack

The primary evidence family is the TorWIC Aisle revisit ladder:

| Setting | Sessions | Frame-Level Objects | Cross-Session Clusters | Retained Stable Objects |
|---|---:|---:|---:|---:|
| Same-day Aisle | 4 | 203 | 11 | 5 |
| Cross-day Aisle | 4 | 240 | 10 | 5 |
| Cross-month Aisle | 6 | 297 | 14 | 7 |

The secondary broader-validation branch is TorWIC Hallway:

| Branch | Sessions | Executed Frames | Frame-Level Objects | Cross-Session Clusters | Retained Stable Objects |
|---|---:|---:|---:|---:|---:|
| Hallway broader validation | 10 | 80/80 first-eight-frame commands | 537 | 16 | 9 |

Important interpretation rules:

- Aisle is the primary controlled ladder.
- Hallway is current broader validation, not missing or deferred.
- Hallway must not be merged into the primary Aisle ladder.
- The historical `172/15/5` cross-month family is fallback chronology only.
- Larger-window or full-trajectory experiments require explicit approval.

## Repository Layout

| Path | Role |
|---|---|
| [`paper/`](./paper/) | Git-tracked Chinese and English manuscript drafts |
| [`RESEARCH_PROGRESS.md`](./RESEARCH_PROGRESS.md) | Lightweight progress log for commits and robot updates |
| [`DATA_SOURCES.md`](./DATA_SOURCES.md) | Dataset source, local root, and Git exclusion policy |
| [`DATA_ORGANIZATION.md`](./DATA_ORGANIZATION.md) | Data organization notes and recovery guidance |
| [`config/protocols/`](./config/protocols/) | TorWIC protocol configs used by the paper-facing evidence stack |
| [`tools/`](./tools/) | Dataset, protocol, object-observation, and reporting utilities |
| [`sam2/`](./sam2/) | SAM2 model code inherited from the Grounded-SAM-2 base |
| [`grounding_dino/`](./grounding_dino/) | Grounding DINO code inherited from the Grounded-SAM-2 base |

## Core Pipeline

The current system is organized around an auditable object-maintenance chain:

```text
RGB-D frames
  -> text-guided detection
  -> SAM2 masks
  -> OpenCLIP label/reranking checks
  -> 2D-to-3D object initialization
  -> ObjectObservation
  -> TrackletRecord
  -> cross-session MapObject
  -> retained stable landmark or rejected transient/dynamic evidence
```

This is the central scientific point of the paper: segmentation outputs are not
inserted directly into the persistent SLAM map. They become candidate evidence
and must pass cross-session admission rules.

## Dataset Policy

Active dataset:

- Dataset: TorWIC SLAM Dataset / Toronto Warehouse Incremental Change SLAM
  Dataset
- Local root: `/home/rui/slam/data/TorWIC_SLAM_Dataset`
- Git policy: excluded from Git
- Download/recovery entrypoints:
  - [`tools/download_torwic_linux.py`](./tools/download_torwic_linux.py)
  - [`tools/download_torwic_benchmark_batch1.sh`](./tools/download_torwic_benchmark_batch1.sh)
  - [`DATA_SOURCES.md`](./DATA_SOURCES.md)
  - [`config/protocols/README.md`](./config/protocols/README.md)

Do not commit:

- `data/`
- `outputs/`
- `tmp/`
- `checkpoints/`
- `gdino_checkpoints/`
- `.bag`, `.zip`, videos, point clouds, masks, model weights, and generated
  large artifacts

When the research robot produces ignored artifacts, it should record the result
summary in [`RESEARCH_PROGRESS.md`](./RESEARCH_PROGRESS.md), update the paper
drafts or package index when appropriate, then commit and push the tracked
metadata.

## Current Submission Status

As of 2026-05-09, the current manuscript state is P109:

- inline citation and evidence threading is complete for the bounded systems
  claim;
- the six venue-neutral citation buckets are mapped to long-term SLAM, dynamic
  SLAM, object-level SLAM, open-vocabulary 3D mapping, and TorWIC/POV-SLAM
  provenance;
- no new dataset download or new experiment protocol is active;
- remaining work is venue-specific polish, final figure/table packaging, and
  any explicitly approved larger-window experiments.

## Upstream Base

This project started from Grounded-SAM-2 and still includes its model/demo code.
The upstream-oriented README has been preserved as
[`SAM2_README.md`](./SAM2_README.md). This root README describes the current
SLAM research repository rather than the original upstream demo package.
