# Thick Manuscript Draft Direction

Status: active direction, 2026-05-09.

## Primary Goal

Build a thick, readable, paper-shaped manuscript for the dynamic industrial
semantic-segmentation-assisted SLAM project. The target is not another closure
audit. The target is a substantial first draft that a human reader can open and
understand as a complete research paper.

## Current Problem

The current repository-visible manuscripts are useful progress drafts, but they
are still too thin:

- the related-work argument is short;
- the method section does not yet fully explain the object-maintenance data
  model;
- the experimental protocol needs a clearer narrative from data source to
  evidence ladder;
- the results need richer table interpretation and failure-case analysis;
- the discussion should connect the evidence back to dynamic SLAM and semantic
  map maintenance;
- limitations and future work should be explicit enough to prevent overclaiming.

## Active Direction

Create a thick first draft with:

- English manuscript: `paper/manuscript_en_thick.md`;
- Chinese manuscript: `paper/manuscript_zh_thick.md`;
- target structure:
  - Abstract;
  - Introduction;
  - Related Work;
  - Problem Formulation;
  - System Overview;
  - Object-Centric Map Maintenance Method;
  - Experimental Protocol;
  - Results;
  - Failure-Case and Rejection Analysis;
  - Discussion;
  - Limitations;
  - Conclusion;
  - Appendix-style evidence notes if needed;
- integrated figures already tracked under `paper/figures/`;
- tables for Aisle ladder, Hallway broader validation, map-admission reduction,
  failure-case mix, and artifact/evidence provenance;
- explicit claim boundaries: no new data, no new experiment protocol, no
  downstream navigation/planning gain claim.

## Evidence To Use

Use only existing local and Git-tracked evidence:

- Aisle primary ladder: `203/11/5 -> 240/10/5 -> 297/14/7`;
- Hallway secondary broader validation: `537/16/9` over `80/80`;
- dynamic-like rejection share: `50.0%-71.4%`;
- rejection taxonomy: `dynamic_contamination 16`, `low_session 13`,
  `label_fragmentation 3`, `low_support 2`;
- P114-P119 closure chain;
- repository figures under `paper/figures/`;
- `RESEARCH_PROGRESS.md` and ignored output paths for provenance references.

## Execution Rules

- Do not download new datasets.
- Do not start larger-window or full-trajectory experiments.
- Do not add unsupported citations.
- Do not claim navigation or planning gains.
- Prefer thick, coherent prose over repeated checklist language.
- Every section should answer why it matters for dynamic industrial semantic
  SLAM.
- After non-trivial manuscript progress, update `RESEARCH_PROGRESS.md`, commit,
  push, and report Telegram progress.

## Done When

P120 is done when:

- `paper/manuscript_en_thick.md` exists and is substantially thicker than the
  current English progress draft;
- `paper/manuscript_zh_thick.md` exists and mirrors the English structure;
- both drafts include the tracked figures and the current key tables;
- the evidence numbers match P119;
- `RESEARCH_PROGRESS.md` records the thick-draft milestone;
- GitHub is pushed.
