# SLAM Data Organization

This file documents how the local SLAM workspace should be read by humans and
research agents.

## Source Of Truth

The research source of truth lives in OpenClaw:

- `/home/rui/.openclaw/workspace-research-orchestrator/projects/industrial-semantic-slam/DATASET_REGISTRY.md`
- `/home/rui/.openclaw/workspace-research-orchestrator/projects/industrial-semantic-slam/DATASET_REGISTRY.json`

Use those files before relying on any generated output snapshot in this repo.

## Active Dataset

| Field | Value |
|---|---|
| Dataset | `TorWIC_SLAM_Dataset` |
| Canonical name | `The Toronto Warehouse Incremental Change SLAM Dataset` |
| Data root | `/home/rui/slam/data/TorWIC_SLAM_Dataset` |
| Protocol configs | `/home/rui/slam/config/protocols` |
| Generated outputs | `/home/rui/slam/outputs` |

Current work uses TorWIC only. Other datasets or demo assets in this repository
are not part of the active research robot dataset pipeline.

## Current Protocol Tiers

| Tier | Protocols | Meaning |
|---|---|---|
| `ACTIVE_SOURCE_OF_TRUTH` | `torwic_same_day_aisle_bundle_v1`, `torwic_cross_day_aisle_bundle_v1`, `torwic_cross_month_aisle_bundle_v1` | Current paper-facing richer ladder |
| `FALLBACK_HISTORICAL` | `torwic_same_day_available_v1`, `torwic_cross_day_available_v1` | Earlier available-data fallback |
| `LEGACY_BASELINE` | `torwic_same_day_v1`, `torwic_cross_day_v1`, `torwic_cross_month_v1` | Earlier weak baseline configs |
| `DEFERRED_FUTURE` | `torwic_hallway_benchmark_batch2_v1` | Future Hallway expansion, not current mainline |

## Current Authoritative Results

| Ladder | Sessions | Count |
|---|---:|---|
| same day richer | 4 | `203/11/5` |
| cross day richer | 4 | `240/10/5` |
| cross month richer | 6 | `297/14/7` |

Count format:

`frame-level objects / cross-session clusters / retained stable objects`

Older counts such as `203/12/5`, `240/11/5`, `297/16/7`, and `172/15/5`
are historical or drift-audit values, not current results.

## Local Data Layout

Do not rename or move these data folders during cleanup.

```text
data/TorWIC_SLAM_Dataset/
  Jun. 15, 2022/
    Aisle_CW_Run_1/
    Aisle_CW_Run_2/
    Aisle_CCW_Run_1/
    Aisle_CCW_Run_2/
  Jun. 23, 2022/
    Aisle_CW_Run_1/
    Aisle_CW_Run_2/
    Aisle_CCW_Run_1/
    Aisle_CCW_Run_2/
  Oct. 12, 2022/
    Aisle_CW/
    Aisle_CCW/
```

## Output Reading Rules

Use this order for current paper numbers:

1. OpenClaw `DATASET_REGISTRY.md`.
2. `outputs/torwic_submission_ready_package_index_v1.md`
3. `outputs/torwic_submission_ready_main_table_v6.md`
4. `outputs/torwic_submission_ready_appendix_table_closure_v6.md`
5. The three active summary JSON files:
   - `outputs/torwic_same_day_aisle_bundle_summary.json`
   - `outputs/torwic_cross_day_aisle_bundle_summary.json`
   - `outputs/torwic_cross_month_aisle_bundle_summary.json`

Do not choose a file as authoritative only because its filename looks newer.

