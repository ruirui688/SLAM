# Data Sources

This repository does not version raw datasets, generated experiment outputs,
model checkpoints, extracted videos, or temporary processing directories.

## Active Dataset

| Field | Value |
|---|---|
| Dataset | TorWIC SLAM Dataset |
| Full name | The Toronto Warehouse Incremental Change SLAM Dataset |
| Local root | `/home/rui/slam/data/TorWIC_SLAM_Dataset` |
| Current paper role | Primary source for long-term industrial semantic SLAM evidence |
| Git policy | Excluded from Git; use download scripts and registry docs |

## Local Download / Recovery Entrypoints

Use these repository scripts and docs instead of committing data:

- `tools/download_torwic_linux.py`
- `tools/download_torwic_benchmark_batch1.sh`
- `DATA_ORGANIZATION.md`
- `config/protocols/README.md`

The OpenClaw research registry is the current source of truth for data status:

- `/home/rui/.openclaw/workspace-research-orchestrator/projects/industrial-semantic-slam/DATASET_REGISTRY.md`
- `/home/rui/.openclaw/workspace-research-orchestrator/projects/industrial-semantic-slam/DATASET_REGISTRY.json`

## Paper-Facing Evidence

Current authoritative ladder:

```text
same-day      203 frame objects / 11 clusters / 5 retained stable objects
cross-day     240 frame objects / 10 clusters / 5 retained stable objects
cross-month   297 frame objects / 14 clusters / 7 retained stable objects
```

Hallway is secondary broader-validation evidence:

```text
10 sessions / 80 first-eight commands / 537 objects / 16 clusters / 9 selected
```

## What Must Not Be Committed

- `data/`
- `outputs/`
- `tmp/`
- `checkpoints/`
- `gdino_checkpoints/`
- bag files, zips, videos, point clouds, model weights, and generated masks

If a result is paper-facing, commit the code/config that regenerates it and add
a short note here or in `DATA_ORGANIZATION.md`; do not commit the raw output
unless it is explicitly small and intentionally curated.
