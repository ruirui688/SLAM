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

## 2026-05-09 P106 evaluation tightening delta matrix

- Produced ignored/generated evidence artifact: `/home/rui/slam/outputs/torwic_p106_evaluation_delta_matrix_v1.md` and `.json`.
- Evidence summary: compared historical `current172` fallback rows `6/6/0`, `14/7/0`, `172/15/5` against the authoritative richer Aisle ladder `203/11/5 -> 240/10/5 -> 297/14/7`; retained Hallway as current secondary broader validation at `537/16/9` over `80/80` executed first-eight frames.
- Paper-facing sync: synchronized Appendix M into both OpenClaw paper drafts and refreshed closure bundle v16 under `/home/rui/slam/outputs/torwic_submission_ready_closure_bundle_v16.md`.
- Policy: existing-data-only; no new dataset download; no larger-window/full-trajectory protocol; no generated `outputs/` artifacts committed to Git.

## 2026-05-09 P107 submission-ready closure

- Produced ignored/generated closure artifacts: `/home/rui/slam/outputs/torwic_submission_ready_appendix_table_closure_v13.md`, `/home/rui/slam/outputs/torwic_submission_ready_package_index_v8.md`, and `/home/rui/slam/outputs/torwic_submission_ready_closure_bundle_v17.md`.
- Evidence summary: final package closure links the primary Aisle ladder `203/11/5 -> 240/10/5 -> 297/14/7`, historical `current172` fallback `172/15/5`, P106 delta matrix, current Hallway secondary branch `537/16/9` over `80/80`, synced paper drafts with Appendix N, and the P107 final audit.
- Policy: existing-data-only; no new dataset download; no larger-window/full-trajectory protocol; generated `outputs/` artifacts remain ignored and are not committed.

## 2026-05-09 P108 final polish citation verification

- Produced ignored/generated citation and package artifacts: `/home/rui/slam/outputs/torwic_citation_verified_batch3_v1.md` and `/home/rui/slam/outputs/torwic_submission_ready_closure_bundle_v18.md`.
- Evidence summary: synchronized Appendix O into both OpenClaw paper drafts, confirmed references used equal bibliography entries `[1]--[6]`, placeholder count remains zero, and mapped related-work buckets to long-term SLAM [1], dynamic SLAM [2], semantic/object-level SLAM [3], open-vocabulary mapping [4]/[5], and TorWIC/POV-SLAM provenance [6].
- Policy: existing-data-only; no new dataset download; no larger-window/full-trajectory protocol; no generated `outputs/` artifacts committed to Git.
