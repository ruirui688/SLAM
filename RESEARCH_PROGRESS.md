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

## 2026-05-09 P109 inline citation evidence threading

- Produced ignored/generated threading artifacts: `/home/rui/slam/outputs/torwic_p109_inline_citation_threading_matrix_v1.md` and `/home/rui/slam/outputs/torwic_submission_ready_closure_bundle_v19.md`.
- Evidence summary: synchronized Appendix P into both OpenClaw paper drafts, tying Abstract/Introduction/Related Work/Method/Results/Hallway/Discussion/Conclusion claims to verified refs `[1]--[6]`, internal Table/Appendix/package anchors, or explicit future-work boundaries.
- Policy: existing-data-only; no new dataset download; no larger-window/full-trajectory protocol; no generated `outputs/` artifacts committed to Git.

## 2026-05-09 repository-visible manuscript drafts

- Replaced the root README with the current dynamic industrial semantic-segmentation-assisted SLAM project view, including evidence tables, dataset policy, and robot commit expectations.
- Added Git-tracked manuscript drafts under `/home/rui/slam/paper/`: English draft `paper/manuscript_en.md`, Chinese draft `paper/manuscript_zh.md`, and `paper/README.md`.
- Evidence summary: repository readers can now inspect the current paper direction directly from GitHub without opening ignored `outputs/` artifacts.
- Policy: no raw dataset, generated output, model weight, video, point cloud, or temporary artifact was added to Git.

## 2026-05-09 P110 manuscript coherence polish

- Produced P110 audit and closure bundle v20; ignored/generated artifacts: `/home/rui/slam/outputs/torwic_submission_ready_closure_bundle_v20.md`.
- Evidence summary: synchronized Appendix Q into both OpenClaw paper drafts. Fixed Section III.A narrative redundancy (merged near-duplicate "candidate evidence" sentences). Tightened Section II item 4, Section VI, and Fig. A1 caption to explicitly block Hallway-to-Aisle promotion or merge. Verified terminology consistency, contribution boundary, Aisle/Hallway roles, and figure captions remain bounded.
- Policy: existing-data-only; no new dataset download; no larger-window/full-trajectory protocol; no generated `outputs/` artifacts committed to Git.

## 2026-05-09 autonomous owner Telegram reporting

- Operational fix: host-side research owner delivery is enabled by default and points to the research Telegram topic.
- Owner-loop policy: future non-trivial progress reports must include changed artifacts, verification, Git commit hash, commit subject, push status, and next active phase/step.
- Added repository-visible operating note: `AUTONOMOUS_RESEARCH_OWNER.md`.
- Policy: pure hosted autonomy remains bounded by approval gates for new data downloads, larger-window/full-trajectory protocols, downstream navigation/planning claims, destructive Git actions, credential/delivery-target changes, and venue-specific house style decisions.

## 2026-05-09 P111 submission package consistency

- Produced P111 audit and closure bundle v21; ignored/generated artifacts: `/home/rui/slam/outputs/torwic_submission_ready_closure_bundle_v21.md`.
- Evidence summary: verified all primary evidence artifacts exist on disk and are mutually cross-referenced. Bundle v20 correctly references all primary artifacts. Manifest records 6 P108-P110 entries. Deliverables checklist covers P108-P111. Manually checked 10 key files for cross-reference integrity; no dangling artifact paths found. Anchors `203/11/5 -> 240/10/5 -> 297/14/7` and `537/16/9`, `80/80` traceable through all package layers.
- Policy: existing-data-only; no new dataset download; no larger-window/full-trajectory protocol; no generated `outputs/` artifacts committed to Git.

## 2026-05-09 P112 evaluation tightening

- Produced P112 stable-subset composition table and closure bundle v22; ignored/generated artifacts: `/home/rui/slam/outputs/torwic_p112_evaluation_tightening_stable_subset_composition_v1.md` and `/home/rui/slam/outputs/torwic_submission_ready_closure_bundle_v22.md`.
- Evidence summary: derived category-level stable-subset composition from actual aisle/hallway subset JSON data. Barriers (42.9%), work tables (28.6%), and warehouse racks (28.6%) consistently dominate the cross-month Aisle retained set. Forklift-like clusters are never retained. Dynamic-like rejection share increases from 50.0% same-day to 71.4% cross-month and Hallway. Synchronized Appendix S into both positioned and clean drafts.
- Policy: existing-data-only; no new dataset download; no larger-window/full-trajectory protocol; no generated `outputs/` artifacts committed to Git.

## 2026-05-09 repository-visible paper figures

- Added curated paper figures under `paper/figures/` and embedded them in both English and Chinese repository-visible manuscript drafts.
- Figure set: TorWIC real-session overlays, paper result overview, stable-object selection table, and Hallway broader-validation composite.
- Evidence summary: GitHub readers can now inspect the visual story directly from `paper/manuscript_en.md` and `paper/manuscript_zh.md` without opening ignored `outputs/` paths.
- Policy: selected lightweight paper figures are tracked; raw datasets, videos, point clouds, model weights, and full generated output directories remain excluded.

## 2026-05-09 DeepSeek model routing

- Operational configuration: default OpenClaw agent model is set to `deepseek-v4-flash`.
- Exception: `research-orchestrator` keeps explicit `deepseek-v4-pro` routing for planning, owner-loop execution, and long-horizon autonomous research pushing.
- Policy: do not use deprecated `deepseek-chat` or `deepseek-reasoner` aliases for this project.

## 2026-05-09 wake mechanism consolidation

- Consolidated autonomous research wakeups to one active driver: host-side `research-owner-host-watchdog.timer`.
- New host policy: 15-minute interval, 45-minute stale threshold, 30-minute owner-loop timeout, 3 bounded steps per wake, and at most one phase completed per wake.
- Disabled the duplicate OpenClaw `research-owner-watchdog-industrial-semantic-slam` cron job; it should not independently start research-owner work.
- Policy: Telegram remains enabled for real progress reports, while duplicate/skip heartbeats stay local.

## 2026-05-09 P113 submission-ready closure

- Produced appendix/table closure v14, P113 audit, and closure bundle v23; ignored/generated artifacts: `/home/rui/slam/outputs/torwic_submission_ready_appendix_table_closure_v14.md` and `/home/rui/slam/outputs/torwic_submission_ready_closure_bundle_v23.md`.
- Evidence summary: closure v14 consolidates the full P108-P113 audit chain with category-level stable-subset composition, cluster rejection profile, consolidated evidence ladder, and Appendix A-T mapping. Synchronized Appendix T into both positioned and clean drafts. Phase queue exhausted after P113.
- Policy: existing-data-only; no new dataset download; no larger-window/full-trajectory protocol.
- GitHub push blocked by SSH for commits a48e320 (P112) and subsequent; local commits preserved.

## 2026-05-09 P114 citation metadata field-level verification

- Produced P114 field-level citation metadata verification matrix and closure bundle v24; ignored/generated artifacts: `/home/rui/slam/outputs/torwic_p114_citation_metadata_field_level_verification_v1.md` and `/home/rui/slam/outputs/torwic_submission_ready_closure_bundle_v24.md`.
- Evidence summary: 6/6 references verified across 8 standard fields (authors, title, venue, vol, no, pages, date, DOI). All DOIs resolve to claimed venues. Related-work claim-to-evidence threading verified (6/6 claims in Introduction/Related Work). Abstract/Introduction/Conclusion framing reviewed — no material changes needed. Fixed stale Appendix A references (v11→v14, v7→v24). Synchronized Appendix U into both positioned and clean drafts. Non-blocking gap: arXiv links missing for [1]–[3] (IEEE published, arXiv optional).
- Policy: existing-data-only; no new dataset download; no larger-window/full-trajectory protocol.

## 2026-05-09 P115 inline citation threading deeper pass

- Produced P115 threading deeper pass audit and closure bundle v25; ignored/generated artifacts: `/home/rui/slam/outputs/torwic_p115_inline_citation_threading_deeper_v1.md` and `/home/rui/slam/outputs/torwic_submission_ready_closure_bundle_v25.md`.
- Evidence summary: 9/9 manuscript sections audited for inline citation anchoring. 1 closing gap fixed (Fig.1 caption tightened — removed meta reference to internal draft). 3 deferred citation gaps recorded (Grounding DINO/SAM2/OpenCLIP implementation back-end citations need user preference). Synchronized Appendix V into both positioned and clean drafts.
- Policy: existing-data-only; no new references added without user approval; no new dataset download.
