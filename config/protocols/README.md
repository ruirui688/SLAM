# TorWIC Protocol Configs

This directory contains protocol JSON files for TorWIC experiments.

## Current Mainline

Use these as the current source-of-truth protocol family:

- `torwic_same_day_aisle_bundle_v1.json`
- `torwic_cross_day_aisle_bundle_v1.json`
- `torwic_cross_month_aisle_bundle_v1.json`

These correspond to the current authoritative richer ladder:

`203/11/5 -> 240/10/5 -> 297/14/7`

## Historical / Fallback

These are retained for reproducibility and historical explanation:

- `torwic_same_day_available_v1.json`
- `torwic_cross_day_available_v1.json`
- `torwic_same_day_v1.json`
- `torwic_cross_day_v1.json`
- `torwic_cross_month_v1.json`

Do not use them as current paper-facing protocol configs unless the task
explicitly asks for historical or fallback results.

## Deferred

- `torwic_hallway_benchmark_batch2_v1.json`

This is a future Hallway expansion skeleton. It is not part of the current
mainline until Hallway data import/download is explicitly restored.

## Registry

The authoritative registry is maintained at:

`/home/rui/.openclaw/workspace-research-orchestrator/projects/industrial-semantic-slam/DATASET_REGISTRY.md`

