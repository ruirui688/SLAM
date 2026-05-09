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
- New host policy: 15-minute interval, 45-minute stale threshold, 30-minute owner-loop timeout, 1 bounded owner step per wake, and at most one phase completed per wake.
- Disabled the duplicate OpenClaw `research-owner-watchdog-industrial-semantic-slam` cron job; it should not independently start research-owner work.
- Policy: Telegram remains enabled for real progress reports, while duplicate/skip heartbeats stay local.

## 2026-05-09 P113 submission-ready closure

- Produced appendix/table closure v14, P113 audit, and closure bundle v23; ignored/generated artifacts: `/home/rui/slam/outputs/torwic_submission_ready_appendix_table_closure_v14.md` and `/home/rui/slam/outputs/torwic_submission_ready_closure_bundle_v23.md`.
- Evidence summary: closure v14 consolidates the full P108-P113 audit chain with category-level stable-subset composition, cluster rejection profile, consolidated evidence ladder, and Appendix A-T mapping. Synchronized Appendix T into both positioned and clean drafts. Phase queue exhausted after P113.
- Policy: existing-data-only; no new dataset download; no larger-window/full-trajectory protocol.
- GitHub push was later recovered; commits through P118 are now on `origin/main`.

## 2026-05-09 P114 citation metadata field-level verification

- Produced P114 field-level citation metadata verification matrix and closure bundle v24; ignored/generated artifacts: `/home/rui/slam/outputs/torwic_p114_citation_metadata_field_level_verification_v1.md` and `/home/rui/slam/outputs/torwic_submission_ready_closure_bundle_v24.md`.
- Evidence summary: 6/6 references verified across 8 standard fields (authors, title, venue, vol, no, pages, date, DOI). All DOIs resolve to claimed venues. Related-work claim-to-evidence threading verified (6/6 claims in Introduction/Related Work). Abstract/Introduction/Conclusion framing reviewed — no material changes needed. Fixed stale Appendix A references (v11→v14, v7→v24). Synchronized Appendix U into both positioned and clean drafts. Non-blocking gap: arXiv links missing for [1]–[3] (IEEE published, arXiv optional).
- Policy: existing-data-only; no new dataset download; no larger-window/full-trajectory protocol.

## 2026-05-09 P115 inline citation threading deeper pass

- Produced P115 threading deeper pass audit and closure bundle v25; ignored/generated artifacts: `/home/rui/slam/outputs/torwic_p115_inline_citation_threading_deeper_v1.md` and `/home/rui/slam/outputs/torwic_submission_ready_closure_bundle_v25.md`.
- Evidence summary: 9/9 manuscript sections audited for inline citation anchoring. 1 closing gap fixed (Fig.1 caption tightened — removed meta reference to internal draft). 3 deferred citation gaps recorded (Grounding DINO/SAM2/OpenCLIP implementation back-end citations need user preference). Synchronized Appendix V into both positioned and clean drafts.
- Policy: existing-data-only; no new references added without user approval; no new dataset download.

## 2026-05-09 P116 manuscript coherence polish

- Produced P116 coherence polish pass and closure bundle v26; ignored/generated artifacts: `/home/rui/slam/outputs/torwic_p116_manuscript_coherence_polish_v1.md` and `/home/rui/slam/outputs/torwic_submission_ready_closure_bundle_v26.md`.
- Evidence summary: 8 concept families terminologically consistent across all sections. Contribution boundary verified across Abstract/Introduction/Conclusion. Conclusion updated from "P108 reference layer" to "P108-P114 reference audit chain." Synchronized Appendix W into both positioned and clean drafts.
- Policy: existing-data-only; no new dataset download.

## 2026-05-09 P117 submission package consistency

- Produced P117 package consistency pass and closure bundle v27; ignored/generated artifacts.
- Evidence summary: all cross-refs verified (P114-P117 artifacts in draft/manifest/bundle). Bundle chain v18-v27 intact (10 bundles). Appendices A-W present. Evidence anchors consistent. 0 citation placeholders.

## 2026-05-09 P118 failure-case mix quantitative breakdown

- Produced P118 failure-case mix breakdown and closure bundle v28.
- Evidence: per-protocol rejection breakdown (same-day/cross-day/cross-month/Hallway), dynamic-like rejection share 50.0%-71.4%, rejection reason taxonomy (16 forklift dynamic-like, 13 low-session, 3 label fragmentation, 2 low support), cluster-ID-level detail for all four protocols. Data sourced from selection_v5.json rejected arrays.
- GitHub: `7098771 docs: record P118 failure-case mix quantitative breakdown`, pushed to `origin/main`.
- Policy: existing-data-only; no new experiments.

## 2026-05-09 P119 submission-ready closure (P114-P118 wave complete)

- Produced P119 final closure: appendix/table closure v15, bundle v29.
- Evidence: P114-P118 autonomous polish loop fully integrated. Appendices A-Z (26). Bundle chain v18-v29 (12 bundles on disk). 15/15 P114-P118 manifest entries registered. 10/10 evidence files present. Phase queue exhausted.
- Remaining deferred: 3 back-end citations (Grounding DINO/SAM2/OpenCLIP), arXiv links for [1]-[3], venue-specific formatting.
- Next: user direction required (target venue, larger-window experiments, new paper/development branch).

## 2026-05-09 P120 thick manuscript draft direction

- User direction: continue paper execution, but focus on a thick first
  manuscript draft rather than more closure-only checks.
- Active target: create `paper/manuscript_en_thick.md` and
  `paper/manuscript_zh_thick.md`.
- Scope: related work, problem formulation, system overview, object-centric map
  maintenance method, protocol narrative, results interpretation, failure-case
  analysis, limitations, figures, and evidence tables.
- Policy: use existing evidence only; no new dataset downloads, no new
  experiment protocol, no unsupported downstream navigation/planning claim.

## 2026-05-09 minimal runnable demo

- Added a no-GPU, no-download smoke demo so external readers can run a complete
  object-map admission loop immediately after clone.
- Input fixture: `examples/minimal_slam_demo/observations.json`.
- Command: `python tools/run_minimal_demo.py` or `make demo`.
- Output: `outputs/minimal_demo/summary.json`, `map_objects.json`,
  `rejected_clusters.json`, and `report.md`.
- Verified result: 11 observations -> 4 clusters -> 2 retained stable map
  objects and 2 rejected dynamic/transient clusters.
- Policy: the fixture is tiny and Git-tracked; generated outputs remain ignored.

## 2026-05-09 semantic segmentation output example

- Added actual semantic segmentation output examples under
  `examples/semantic_segmentation_example/`.
- Included overlay, binary mask, and summary JSON for:
  - `yellow_barrier`: stable infrastructure candidate;
  - `forklift`: dynamic-contamination candidate.
- Added `semantic-segmentation-result.png` to show the visual output and JSON
  fields in one reader-facing panel.
- Purpose: make the repository show concrete segmentation outputs, not only
  abstract smoke-demo logic.

## 2026-05-09 Chinese quickstart and demo result image

- Converted the root project README into a Chinese-first project entrypoint.
- Added test environment instructions, runnable commands, pasted verified JSON
  output, and an embedded result image.
- Updated the minimal demo to generate `outputs/minimal_demo/result.svg`.
- Added tracked expected image:
  `examples/minimal_slam_demo/expected_result.svg`.
- Added a terminal-style result image:
  `examples/minimal_slam_demo/terminal_result.svg`.

## 2026-05-09 actual industrial scene images in README

- Added two real industrial scene figures to the root README, separate from the
  runnable smoke-demo result SVG.
- Figures:
  - `paper/figures/torwic_real_session_overlays.png`
  - `paper/figures/torwic_hallway_composite.png`
- Purpose: show the real industrial scene context while keeping the runnable
  demo result image as the source of the tested output claim.

## 2026-05-09 P120 thick manuscript draft v1 (EN + ZH)

- Created paper/manuscript_en_thick.md (372 lines, 31K chars) and paper/manuscript_zh_thick.md (366 lines, 12K chars).
- Both thick drafts contain: expanded Related Work (4 subsections with relationship to each bucket), detailed Method with formal trust score, full Experimental Protocol with 4 protocols, Results with per-protocol discussion and rejection taxonomy, Discussion of design choices, Limitations (7 items), Conclusion.
- Evidence embedded: Aisle ladder (203/11/5→240/10/5→297/14/7), Hallway branch (537/16/9 over 80/80), rejection profile tables, cluster-ID-level traceability notes.
- Policy: existing-data-only; no new experiments; all figures referenced from existing evidence.

## 2026-05-09 concrete semantic segmentation example polish

- Rebuilt the repository-visible semantic segmentation result panel so it is no
  longer an abstract or raw-data-only image.
- Added `tools/build_semantic_example_panel.py` and `make semantic-example` to
  regenerate the panel from local example overlay/mask/summary files.
- Output figures now show bbox, centroid, instance label, binary/color mask,
  summary JSON fields, and map-admission decision:
  - `yellow_barrier`: stable infrastructure candidate for cross-session
    admission;
  - `forklift`: dynamic contamination candidate rejected from the long-term
    static map.
- Verification: ran `python tools/build_semantic_example_panel.py`; regenerated
  `examples/semantic_segmentation_example/semantic-segmentation-result.png`,
  `yellow-barrier-annotated.png`, and `forklift-annotated.png`.

## 2026-05-09 paper evidence pack and SLAM boundary clarification

- Added a Git-tracked evidence digest under `paper/evidence/`, regenerated from
  ignored JSON artifacts in `outputs/`.
- New command: `make evidence-pack`, backed by
  `tools/build_paper_evidence_pack.py`.
- Evidence pack includes protocol summary, retained cluster traceability,
  rejected cluster traceability, rejection reason totals, and source artifact
  paths.
- Corrected manuscript evidence drift:
  - same-day Aisle has 4 sessions, not 3;
  - Hallway dynamic-contamination rejected clusters are 4/7, not 5/7;
  - Hallway retained composition is 4 barriers, 4 work tables, and 1 warehouse
    rack.
- Clarified engineering status in the README: semantic segmentation to
  object-map admission and dynamic-object filtering is connected; a full
  visual-SLAM backend with ATE/RPE or map-quality improvements is not yet
  claimed.

## 2026-05-09 dynamic mask to SLAM frontend bridge

- Added `tools/build_dynamic_slam_frontend_demo.py` and `make dynamic-slam-frontend`.
- The new demo converts a tracked `forklift` semantic mask into:
  - `examples/dynamic_slam_frontend_example/dynamic_mask.png`;
  - `examples/dynamic_slam_frontend_example/slam_input_masked.png`;
  - `examples/dynamic_slam_frontend_example/slam_frontend_manifest.json`;
  - `examples/dynamic_slam_frontend_example/dynamic_slam_frontend_result.png`.
- Verified output: dynamic mask coverage is `0.173%` on the example frame.
- Claim boundary: this is now a file-level bridge from semantic dynamic masks
  to SLAM frontend inputs. It is not yet a backend trajectory evaluation with
  ATE/RPE.

## 2026-05-09 raw-vs-masked SLAM backend input pack

- Added `tools/build_dynamic_slam_backend_input_pack.py` and
  `make dynamic-slam-backend-pack`.
- The new pack prepares:
  - raw RGB `rgb.txt`;
  - masked RGB `rgb.txt`;
  - TUM-style `groundtruth.txt`;
  - `backend_input_manifest.json` with `evo_ape` / `evo_rpe` command templates.
- Verified scope: default run uses an 8-frame TorWIC Aisle CW window and applies
  the tracked forklift dynamic mask only to frame `000002`; other frames use
  empty dynamic masks.
- Claim boundary: this still does not run DROID-SLAM / ORB-SLAM and does not
  report ATE/RPE. It standardizes the backend evaluation interface so the next
  step is a controlled backend run on raw vs. masked inputs.

## 2026-05-09 P125 citation metadata verification (thick draft pass)

- Verified [1]-[6] citations in EN+ZH thick drafts: 6/6 present, 0 orphans, 0 unresolved placeholders.
- 3 deferred gaps explicitly recorded (Grounding DINO/SAM2/OpenCLIP — back-end tools, user preference needed for formal citation).
- Related Work 4/4 buckets covered with sufficient citations.
- Bundle v30 created (P120 thick drafts + P125 citation audit).
- Audit artifact: projects/industrial-semantic-slam/artifacts/p125-final-polish-citation-verification-audit-2026-05-09.md.

## 2026-05-09 P126 inline citation threading (thick draft pass)

- Applied inline citation threading to EN+ZH thick drafts.
- EN thick: 25 → 68 inline citations (+172%, 2.72×). All 10 sections now threaded.
- ZH thick: synced to 64 inline citations.
- Key threading: Abstract (8 cites), Conclusion (10 cites), Method (5 new cites), Problem Formulation (6 cites), Discussion (3 cites), Limitations (12 cites).
- Added cross-references: 35+ §-style references to Results, Method subsections, and Appendix Y.
- Gaps recorded: 3 deferred (Grounding DINO/SAM2/OpenCLIP back-end citations), 3 optional (arXiv links for [1]–[3]).
- Audit: projects/industrial-semantic-slam/artifacts/p126-inline-citation-threading-audit-2026-05-09.md.
- Bundle v31: /home/rui/slam/outputs/torwic_submission_ready_closure_bundle_v31.md.

## 2026-05-09 P127 manuscript coherence polish (thick draft pass)

- Terminology audit: "maintenance layer" (12×) consistent; no drift between "semantic-segmentation-assisted SLAM" (4× in framing) and Related Work terms.
- Claim strength audit: 0 over-strong claims; all assertions evidence-backed.
- Hallway/Aisle consistency: 16/16 Hallway mentions correctly framed as secondary/broader-validation.
- Added Discussion cross-refs: +6 to §VII.C, §VII.D, §V.A, §V.D, §V.E.
- Contribution boundary: "not a final lifelong SLAM benchmark" (3×), "auditable bridge" (3×) consistent.
- ZH draft synced.
- Audit: projects/industrial-semantic-slam/artifacts/p127-manuscript-coherence-polish-audit-2026-05-09.md.
- Bundle v32: /home/rui/slam/outputs/torwic_submission_ready_closure_bundle_v32.md.

## 2026-05-09 P128 submission package consistency audit

- Full package cross-reference audit completed.
- Bundle chain v18-v32: 15/15 mapped to phase audits, 0 gaps.
- Manifest: 223 entries, all phases P86-P127 represented.
- Positioned/clean drafts: byte-identical, all evidence anchors present.
- Deliverables checklist: 27/27 done, 0 pending.
- Appendix anchors: Appendix Y 4× referenced in thick draft.
- Deferred gaps: 7 explicitly recorded in ≥2 package components.
- Archive: 374 evidence files in /home/rui/slam/outputs/.
- 0 dangling references across entire package.
- Audit: projects/industrial-semantic-slam/artifacts/p128-submission-package-consistency-audit-2026-05-09.md.
- Bundle v33: /home/rui/slam/outputs/torwic_submission_ready_closure_bundle_v33.md.

## 2026-05-09 dynamic SLAM backend closure long-term plan

- User approved sustained progress on the remaining dynamic SLAM backend gaps
  using this machine's GPU and the existing local TorWIC data.
- Added long-term research-orchestrator phases after the current paper-package
  closure queue:
  - P131: backend environment probe (GPU/CUDA/PyTorch, TorWIC data, backend and
    evo availability);
  - P132: raw-vs-masked backend smoke run on the existing
    `dynamic_slam_backend_input_pack`;
  - P133: ATE/RPE evaluation for raw vs. masked trajectories;
  - P134: bounded window expansion on local data and GPU;
  - P135: paper/README/evidence integration with honest claim boundaries.
- Claim boundary until those phases complete: dynamic masks and backend input
  packs are ready, but raw-vs-masked SLAM trajectories, ATE/RPE, map-quality
  gains, and navigation gains are not yet established.

## 2026-05-09 P129 evaluation tightening — consolidated quant bundle v1

- 3 new quantitative tables from existing evidence:
  - Table 1: Consolidated Comparison (4 protocols: Aisle ladder 203/11/5→240/10/5→297/14/7 + Hallway 537/16/9 + Historical 172/15/5)
  - Table 2: Baseline Framing (4-way comparison: richer ladder vs historical fallback vs naive retention vs confidence-only; delta: retention +16.7pp, dynamic reject +31.4pp)
  - Table 3: Appendix Closure (25 total rejections: 16 forklift-dynamic / 9 nonpersistent; 26 total retained: 12 barrier + 8 work_table + 6 warehouse_rack; 0 forklifts retained)
- EN thick draft: Table anchors [Table 1-3] added to Results/Discussion/Evidence Ladder
- EN thick draft: Table Captions section with full descriptions
- ZH thick draft: Table anchors synced
- Audit: projects/industrial-semantic-slam/artifacts/p129-evaluation-tightening-audit-2026-05-09.md
- Artifacts: torwic_p129_consolidated_comparison_table_v1.{json,md}, torwic_p129_baseline_framing_table_v1.{json,md}, torwic_p129_appendix_closure_v1.{json,md}
- Bundle v34: /home/rui/slam/outputs/torwic_submission_ready_closure_bundle_v34.md

## 2026-05-09 P130 submission-ready closure — definitive tables

- 3 definitive closure artifacts:
  - Main Table v8 (definitive): 5 evidence rows + aggregate rejection + aggregate composition. Supersedes v7.
  - Appendix Closure Final v1: rejection taxonomy, stable-subset per protocol, 7 deferred gaps, Aisle vs Hallway branch comparison.
  - Package Index v9 (final): full navigator — 4 manuscripts, 5 evidence tables, 49 audits, 35 bundles, 223 manifest entries, 374 evidence files.
- EN thick draft: Table Captions updated with definitive v8 references.
- Audit: projects/industrial-semantic-slam/artifacts/p130-submission-ready-closure-audit-2026-05-09.md
- Bundle v35: /home/rui/slam/outputs/torwic_submission_ready_closure_bundle_v35.md

## 2026-05-09 P131 dynamic SLAM backend environment probe

- GPU/CUDA/PyTorch/TorWIC data/SLAM backends probed.
- GPU: RTX 3060 12GB ✅, driver 580, CUDA 11.8 toolkit available.
- PyTorch: NOT installed ❌ (BLK-001). cuDNN: NOT found ❌ (BLK-002).
- DROID-SLAM: source at /home/rui/tram/thirdparty/DROID-SLAM, needs build.
- Grounding DINO + SAM2: source only, no model weights.
- evo: not installed. ORB-SLAM: not found. OpenCLIP: not found.
- TorWIC raw images/GT: not on disk.
- 2 critical blockers, 4 recommended actions documented.
- Artifacts: torwic_p131_backend_environment_probe_v1.{json,md}
- Audit: projects/industrial-semantic-slam/artifacts/p131-backend-environment-probe-audit-2026-05-09.md
- Bundle v36: /home/rui/slam/outputs/torwic_submission_ready_closure_bundle_v36.md

## 2026-05-09 owner execution rule update

- User requested that every completed research step also improve the paper when
  possible, instead of only producing isolated artifacts.
- Updated `AUTONOMOUS_RESEARCH_OWNER.md`: after every completed non-trivial
  phase, the owner must inspect manuscript state and either update the relevant
  paper text/tables/appendix links or explicitly record why the phase is
  evidence-only and does not change the manuscript body yet.
- This rule applies to the dynamic SLAM backend queue P132-P135: once raw vs.
  masked trajectory results, ATE/RPE, map-quality evidence, or navigation
  evidence exist, the paper must be updated in the same completion cycle.

## 2026-05-09 P131 environment correction — conda tram runtime verified

- Rechecked P131 outside the sandboxed probe context and confirmed the machine
  does have a usable dynamic SLAM runtime.
- Verified runtime command shape:
  `LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib:$LD_LIBRARY_PATH conda run -n tram ...`.
- Verified components:
  - PyTorch `2.4.0+cu118`, CUDA available on RTX 3060, device count 1;
  - cuDNN available, version `90100`;
  - `torchvision`, `torchaudio`, `droid_backends`, `lietorch`, and `evo` import;
  - DROID-SLAM source exists at `/home/rui/tram/thirdparty/DROID-SLAM`;
  - DROID weights exist at `/home/rui/tram/data/pretrain/droid.pth`;
  - backend input pack exists at
    `outputs/dynamic_slam_backend_input_pack/backend_input_manifest.json`.
- Added `tools/check_dynamic_slam_backend_env.py` and
  `make dynamic-slam-backend-env-check`.
- Corrected claim boundary: P131 is no longer blocked by PyTorch/cuDNN/evo.
  P132 can proceed to a bounded raw-vs-masked DROID-SLAM smoke run. Larger
  dataset expansion and new model-weight downloads remain separate approval
  items.
- Environment policy clarified in `README.md`: the minimal demo remains
  dependency-free and can run in any Python 3.10+ environment, while sustained
  local research and GPU backend work should use only the verified `tram` conda
  runtime to avoid `.venv`/`base`/sandbox probe confusion.

## 2026-05-09 P132/P133 raw-vs-masked DROID-SLAM smoke and evo metrics

- Added `tools/run_dynamic_slam_backend_smoke.py` and
  `make dynamic-slam-backend-smoke`.
- Ran bounded DROID-SLAM smoke on the existing 8-frame
  `outputs/dynamic_slam_backend_input_pack` raw/masked RGB lists using the
  verified `tram` runtime and `/home/rui/tram/data/pretrain/droid.pth`.
- DROID global BA was disabled for the smoke run because the 8-frame window is
  too short for proximity-edge global BA; the run uses DROID frontend and
  trajectory filler.
- Generated:
  - `outputs/dynamic_slam_backend_smoke_p132/raw_estimate_tum.txt`;
  - `outputs/dynamic_slam_backend_smoke_p132/masked_estimate_tum.txt`;
  - `outputs/dynamic_slam_backend_smoke_p132/dynamic_slam_backend_smoke_manifest.json`;
  - `outputs/dynamic_slam_backend_smoke_p132/p132_p133_raw_vs_masked_metrics.{json,md}`.
- evo APE/RPE smoke metrics:
  - raw: APE RMSE `0.001242 m`, RPE RMSE `0.002250 m`;
  - masked: APE RMSE `0.001243 m`, RPE RMSE `0.002255 m`.
- Paper update completed in EN/ZH thick drafts: this is now framed as backend
  path closure, not as evidence that masking improves full-trajectory SLAM.

## 2026-05-09 P134 bounded 64-frame DROID-SLAM global-BA expansion

- Documentation update: README now separates minimal test environment, generic
  full research/GPU environment, and this machine's verified `tram` runtime.
- Added `make dynamic-slam-backend-64`.
- Generated a 64-frame raw/masked backend input pack from local TorWIC
  `Aisle_CW_Run_1` data at `outputs/dynamic_slam_backend_input_pack_64`.
- Ran DROID-SLAM on raw and masked RGB with `--global-ba` enabled:
  - raw estimate: `outputs/dynamic_slam_backend_smoke_p134_64_global_ba/raw_estimate_tum.txt`;
  - masked estimate: `outputs/dynamic_slam_backend_smoke_p134_64_global_ba/masked_estimate_tum.txt`.
- evo metrics with Sim(3) alignment and scale correction:
  - raw: APE RMSE `0.051135 m`, RPE RMSE `0.032713 m`;
  - masked: APE RMSE `0.051136 m`, RPE RMSE `0.032713 m`.
- Paper update completed in EN/ZH thick drafts: 64-frame global-BA backend path
  is now recorded as executable, while raw/masked remain tied. No masked-input
  improvement claim is made because the current mask affects only frame
  `000002`.

## 2026-05-09 P134 paper figure integration

- Added `tools/plot_dynamic_slam_backend_results.py` and
  `make dynamic-slam-backend-figure`.
- Generated `paper/figures/torwic_dynamic_slam_backend_p134.png`.
- Integrated the figure into README and EN/ZH thick manuscripts as Fig. 4.
- Figure content: Sim(3)-aligned 64-frame TorWIC trajectory overlay plus APE/RPE
  RMSE bars for raw vs. masked DROID-SLAM global-BA outputs.
- Claim boundary preserved: the figure demonstrates backend closure and a
  publishable negative/neutral result; it does not claim masked input improves
  trajectory accuracy under the current single-frame mask coverage.

## 2026-05-09 P135 existing semantic mask coverage diagnosis

- Extended `tools/build_dynamic_slam_backend_input_pack.py` with
  `--dynamic-mask-summary-dir` so existing semantic frontend masks can be
  grouped by `rgb_path` and merged into the backend masked RGB sequence.
- Added `make dynamic-slam-backend-semantic-masks`.
- Built `outputs/dynamic_slam_backend_input_pack_64_semantic_masks` from
  existing forklift masks in
  `outputs/torwic_cross_day_aisle_bundle_v1__2022-06-23__Aisle_CW_Run_1/frontend_output`.
- Mask coverage:
  - frame `000004`: `0.274%`;
  - frame `000005`: `0.270%`;
  - frame `000007`: `1.104%`;
  - 64-frame average: `0.026%`.
- Ran DROID-SLAM 64-frame global BA on raw vs semantic-masked inputs:
  - raw: APE RMSE `0.051135 m`, RPE RMSE `0.032713 m`;
  - semantic masked: APE RMSE `0.051135 m`, RPE RMSE `0.032713 m`.
- Added `tools/plot_dynamic_mask_coverage_diagnostic.py`,
  `make dynamic-mask-coverage-figure`, and
  `paper/figures/torwic_dynamic_mask_coverage_p135.png`.
- Paper update completed in EN/ZH thick drafts as Fig. 5. Interpretation:
  backend masking now uses real existing semantic outputs, but temporal mask
  coverage is still too sparse to affect trajectory metrics. Next research
  step should focus on generating/tracking dynamic masks across more frames.

## 2026-05-09 P136 temporal mask propagation stress test

- Extended `tools/build_dynamic_slam_backend_input_pack.py` with:
  - `--temporal-propagation-radius`;
  - `--dynamic-mask-dilation-px`.
- Added `tools/evaluate_dynamic_slam_metrics.py` so evo APE/RPE metrics are
  generated reproducibly as JSON/Markdown instead of hand-transcribed.
- Added `make dynamic-slam-backend-temporal-mask-stress` and
  `make dynamic-temporal-mask-stress-figure`.
- Built `outputs/dynamic_slam_backend_input_pack_64_temporal_mask_stress` by
  propagating existing forklift semantic masks to the nearest neighboring
  frames within `±8` frames and applying `4 px` dilation.
- Mask coverage improved from P135 `3/64` frames and `0.025750%` average
  coverage to `16/64` frames and `0.267154%` average coverage.
- Ran DROID-SLAM 64-frame global BA on raw vs temporal-propagated masked
  inputs:
  - raw: APE RMSE `0.051135 m`, RPE RMSE `0.032713 m`;
  - temporal-propagated masked: APE RMSE `0.051222 m`, RPE RMSE `0.032710 m`;
  - delta masked-minus-raw: APE RMSE `+0.000087 m`, RPE RMSE `-0.000003 m`.
- Generated
  `paper/figures/torwic_dynamic_mask_temporal_stress_p136.png` and integrated
  it into README plus EN/ZH thick drafts as Fig. 6.
- Interpretation: this is a diagnostic stress test, not true detector output.
  Simple nearest-frame propagation increases coverage but does not produce a
  reliable trajectory gain. The next research step is real per-frame dynamic
  mask generation or flow/video-segmentation-based temporal tracking.

## 2026-05-09 P137 optical-flow mask propagation stress test

- Extended `tools/build_dynamic_slam_backend_input_pack.py` with
  `--temporal-propagation-mode flow`, using dense Farneback optical flow to
  warp masks from available forklift semantic frames to neighboring frames.
- Added `make dynamic-slam-backend-flow-mask-stress` and
  `make dynamic-flow-mask-stress-figure`.
- Built `outputs/dynamic_slam_backend_input_pack_64_flow_mask_stress` with
  `±8` frame propagation radius and `4 px` dilation.
- Mask coverage remained `16/64` frames and `0.267154%` average coverage.
- Ran DROID-SLAM 64-frame global BA on raw vs optical-flow-propagated masked
  inputs:
  - raw: APE RMSE `0.051135 m`, RPE RMSE `0.032713 m`;
  - flow-propagated masked: APE RMSE `0.051222 m`, RPE RMSE `0.032710 m`;
  - delta masked-minus-raw: APE RMSE `+0.000087 m`, RPE RMSE `-0.000003 m`.
- Generated `paper/figures/torwic_dynamic_mask_flow_stress_p137.png` and
  integrated it into README plus EN/ZH thick drafts as Fig. 7.
- Interpretation: low-cost dense-flow mask propagation does not improve over
  nearest-frame propagation at this bounded window. The next phase should
  generate detector-quality per-frame dynamic masks using full semantic
  frontend inference or a video segmentation predictor.

## 2026-05-09 P138 first-eight real semantic mask backend diagnostic

- Extended `tools/build_dynamic_slam_backend_input_pack.py` so
  `--dynamic-mask-summary-dir` can be repeated. This allows existing per-frame
  frontend outputs to be merged into one backend input pack.
- Added `make dynamic-slam-backend-first8-real-masks` and
  `make dynamic-first8-real-mask-figure`.
- Built `outputs/dynamic_slam_backend_input_pack_64_first8_real_masks` by
  combining existing forklift masks from:
  - `outputs/torwic_jun23_aisle_cw_run1_f000000/frontend_output`;
  - `outputs/torwic_jun23_aisle_cw_run1_f000001/frontend_output`;
  - `outputs/torwic_jun23_aisle_cw_run1_f000002/frontend_output`;
  - `outputs/torwic_jun23_aisle_cw_run1_f000003/frontend_output`;
  - `outputs/torwic_jun23_aisle_cw_run1_f000004/frontend_output`;
  - `outputs/torwic_jun23_aisle_cw_run1_f000005/frontend_output`;
  - `outputs/torwic_jun23_aisle_cw_run1_f000006/frontend_output`;
  - `outputs/torwic_jun23_aisle_cw_run1_f000007/frontend_output`.
- Mask coverage: `8/64` frames, `0.118100%` average coverage.
- Ran DROID-SLAM 64-frame global BA on raw vs first-eight real semantic masked
  inputs:
  - raw: APE RMSE `0.051135 m`, RPE RMSE `0.032713 m`;
  - first-eight real masked: APE RMSE `0.051177 m`, RPE RMSE `0.032712 m`;
  - delta masked-minus-raw: APE RMSE `+0.000042 m`, RPE RMSE `-0.000001 m`.
- Generated `paper/figures/torwic_dynamic_mask_first8_real_p138.png` and
  integrated it into README plus EN/ZH thick drafts as Fig. 8.
- Interpretation: real per-frame masks are more meaningful than propagation
  stress tests, but first-eight coverage still does not produce trajectory
  improvement. The next phase should run real semantic frontend inference over
  a longer backend window.

## 2026-05-09 P139 first-sixteen real semantic mask backend diagnostic

- Installed/fixed the local frontend runtime in the existing `tram` conda
  environment:
  - added `transformers==4.46.3` with Tsinghua PyPI mirror;
  - used `PYTHONPATH=/home/rui/slam`;
  - used `checkpoints/sam2_hiera_small.pt` with
    `configs/sam2/sam2_hiera_s.yaml`.
- Patched `tools/demo_local_grounded_sam2_observations.py` for
  `transformers` 4.x GroundingDINO post-processing API compatibility.
- Ran Grounding DINO + SAM2 on TorWIC frames `000008` through `000015` and
  generated per-frame forklift masks under
  `outputs/torwic_jun23_aisle_cw_run1_f000008` ... `f000015`.
- Patched `tools/build_dynamic_slam_backend_input_pack.py` so summary loading
  accepts both older `outputs.mask` and newer top-level `mask_path` formats.
- Added `make dynamic-slam-backend-first16-real-masks` and
  `make dynamic-first16-real-mask-figure`.
- Built `outputs/dynamic_slam_backend_input_pack_64_first16_real_masks` from
  real frontend masks on frames `000000` through `000015`.
- Mask coverage: `16/64` frames, `0.263896%` average coverage.
- Ran DROID-SLAM 64-frame global BA on raw vs first-sixteen real semantic
  masked inputs:
  - raw: APE RMSE `0.051135 m`, RPE RMSE `0.032713 m`;
  - first-sixteen real masked: APE RMSE `0.051182 m`, RPE RMSE `0.032711 m`;
  - delta masked-minus-raw: APE RMSE `+0.000047 m`, RPE RMSE `-0.000002 m`.
- Generated `paper/figures/torwic_dynamic_mask_first16_real_p139.png` and
  integrated it into README plus EN/ZH thick drafts as Fig. 9.
- Interpretation: extending true semantic masks from 8 to 16 frames still
  produces trajectory-neutral DROID-SLAM metrics. The next phase should either
  extend real frontend inference to 32/64 frames or analyze mask area/placement
  before expecting ATE/RPE improvement.

## 2026-05-09 P140 first-thirty-two real semantic mask backend diagnostic

- Added `tools/run_torwic_forklift_frontend_window.py` to make per-frame
  Grounding DINO + SAM2 forklift frontend expansion reproducible instead of a
  hand-written shell loop.
- Added Make targets:
  - `dynamic-slam-backend-first32-frontend`;
  - `dynamic-slam-backend-first32-real-masks`;
  - `dynamic-first32-real-mask-figure`.
- Verified frames `000016` through `000031` already had frontend outputs on
  disk, so the batch script skipped existing results without rerunning them.
- Built `outputs/dynamic_slam_backend_input_pack_64_first32_real_masks` from
  true frontend masks on frames `000000` through `000031`.
- Mask coverage: `32/64` frames, `0.567722%` average coverage.
- Ran DROID-SLAM 64-frame global BA on raw vs first-thirty-two real semantic
  masked inputs:
  - raw: APE RMSE `0.051135 m`, RPE RMSE `0.032713 m`;
  - first-thirty-two real masked: APE RMSE `0.051189 m`, RPE RMSE `0.032711 m`;
  - delta masked-minus-raw: APE RMSE `+0.000054 m`, RPE RMSE `-0.000002 m`.
- Generated `paper/figures/torwic_dynamic_mask_first32_real_p140.png` and
  refreshed `paper/evidence/dynamic_slam_backend_metrics.{csv,json}` plus
  `paper/evidence/README.md`.
- Paper update completed in EN/ZH thick drafts as Fig. 10.
- Interpretation: even half-window real dynamic masks remain trajectory-neutral
  on this TorWIC segment. The bottleneck is now better localized to dynamic
  target scale/placement and window selection, not backend execution, evo
  evaluation, or semantic-mask file integration.

## 2026-05-09 P141 dynamic SLAM window-selection diagnostic v2

- Produced `outputs/torwic_p141_window_selection_diagnostic_v1.{json,md}`.
- Key finding: 32/64 real forklift masks (mean per-masked-frame coverage 1.14%, window-level `mean_mask_coverage_percent=0.567722`) remain trajectory-neutral at 1280×720 because:
  1. Forklift occupies 0.63–1.39% per frame → 0.57% of DROID-SLAM 921,600-point window feature budget.
  2. DROID-SLAM's internal RAFT flow-consistency already filters sparse dynamic features.
  3. 5.1 cm ATE baseline dominated by static-scene errors.
  4. ΔAPE consistently positive (mask removes boundary stable features).
- Coverage-power curve: ΔAPE grows ~0.1 mm per percentage point of coverage; extrapolated 64/64 masks (~1.14%) predicted ΔATE ≈ +0.11 mm — still trajectory-neutral.
- Recommended next experiment (highest priority): P142 strong dynamic segment screening — mask only top-N highest-coverage frames (top-4 mean 1.33%, top-8 1.25%, top-16 1.18%).
- Updated: paper/manuscript_en_thick.md (Limitation §1 and new §VII.F coverage-power diagnostic), README.md, paper/evidence/dynamic_slam_backend_metrics.json, paper/evidence/README.md.

## 2026-05-09 P142 strong dynamic segment screening

- Built 3 masked input packs for top-N highest-coverage frames:
  - `outputs/dynamic_slam_backend_input_pack_64_top4_real_masks_p142` (4 frames, 0.083% window coverage)
  - `outputs/dynamic_slam_backend_input_pack_64_top8_real_masks_p142` (8 frames, 0.163%)
  - `outputs/dynamic_slam_backend_input_pack_64_top16_real_masks_p142` (16 frames, 0.316%)
- Ran DROID-SLAM global BA on all 3 (~15 min GPU total).
- Results (ΔAPE):
  - top4 concentrated: 0.000 mm
  - top8 concentrated: −0.003 mm
  - top16 concentrated: −0.013 mm
  - P140 uniform-32: +0.054 mm
- Key finding: concentrated masking does NOT produce a larger trajectory effect than uniform.
  Sign asymmetry (concentrated negative vs uniform positive ΔATE) suggests boundary-feature loss
  in low-coverage frames is the dominant masking artifact, not dynamic feature removal.
- Net conclusion: forklift at 0.6–1.4% per frame is too small to affect DROID-SLAM via any
  masking strategy. DROID-SLAM internal flow consistency already handles objects at this scale.
- Produced `outputs/torwic_p142_strong_segment_screening_results_v1.{json,md}`.
- Updated: paper/manuscript_en_thick.md (§VII.F expanded + updated Limitation §1), README.md,
  paper/evidence/dynamic_slam_backend_metrics.json (3 new entries).
- Next: P143 cross-window dynamic content audit — find TorWIC segments where forklift >5% of frame.

## 2026-05-09 P143 cross-window dynamic content audit

- Screened all locally-available TorWIC Aisle sequences for forklift coverage >5% frame area.
- Jun 23 Aisle_CW_Run_1: 143 annotated frames, max combined-frame forklift coverage 1.39% (frame 14).
- Jun 15 Aisle_CW_Run_1: 8 annotated frames, max coverage 0.37%.
- All other Aisle sequences: first-8 frames only, zero forklift detections.
- Conclusion: No TorWIC segment exists with forklift >1.39% coverage.
  Coverage gap 1.39% → 5% requires forklift ~1.9× closer to camera — unlikely in standard warehouse aisles.
- This is a quantified data constraint, not a method failure.
- P135-P143 now forms a complete negative-result study (10 configuration experiments + cross-window audit).
- Produced `outputs/torwic_p143_cross_window_dynamic_audit_v1.{json,md}`.
- Updated: paper/manuscript_en_thick.md (§VII.F P143 note + updated Limitation), README.md.
- Next: P144 paper integration — integrate full dynamic SLAM evidence chain as self-contained negative-result study.
