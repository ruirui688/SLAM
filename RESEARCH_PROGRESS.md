# Research Progress Log

This file is the lightweight GitHub-facing progress log for the autonomous
research robot.

Raw data, generated experiment outputs, model checkpoints, and temporary files
are intentionally excluded from Git. When the research robot produces progress
that lives in ignored paths such as `outputs/`, it should record the evidence
summary and local paths here, then commit and push the repository.

## 2026-05-09

- Initialized GitHub-facing repository metadata for the dynamic industrial
  semantic-segmentation-assisted SLAM project.
- Added data source documentation and confirmed that `data/`, `outputs/`,
  `tmp/`, `checkpoints/`, model weights, videos, point clouds, and local agent
  scratch files are ignored.
- Current paper-facing direction: semantic segmentation / open-vocabulary
  perception for dynamic industrial environments, stable-object retention,
  dynamic-like rejection, and long-term semantic landmark reuse.
- Current primary ladder: `203/11/5 -> 240/10/5 -> 297/14/7`.
- Current secondary Hallway broader-validation evidence: `537/16/9`.
- Latest OpenClaw research closure before repo initialization: closure bundle
  v11 under `/home/rui/slam/outputs/` and research-orchestrator project state
  under `/home/rui/.openclaw/workspace-research-orchestrator/`.
