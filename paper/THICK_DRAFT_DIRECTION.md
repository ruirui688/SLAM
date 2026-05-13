# Thick Manuscript Draft Direction

Status: active-only manuscript target, 2026-05-13.

## Primary Goal

The thick draft is now the active manuscript target for the dynamic industrial
semantic-segmentation-assisted SLAM project. Do not maintain the brief English
or Chinese drafts unless the user explicitly asks for them. Future paper
editing should prioritize:

- `paper/manuscript_en_thick.md`;
- `paper/manuscript_zh_thick.md`;
- supporting export summaries under `paper/export/`.

## Current Problem

The older thick-draft direction was centered on the P112/P120-era object
maintenance manuscript. That is no longer sufficient. The manuscript must now
preserve the object-maintenance evidence while integrating the later
dynamic-mask frontend evidence from P217-P228, especially the P225-P228
learned-mask/gated-mask story.

## Active Structure

Use the following paper-shaped structure in both thick drafts:

1. Abstract
2. Introduction
3. Related Work
4. Problem Formulation
5. System Overview
6. Object-Centric Maintenance
7. Dynamic-Mask Frontend
8. Experimental Protocol
9. Results
10. Failure/Boundary Analysis
11. Discussion
12. Limitations
13. Conclusion

Appendix-style evidence notes, references, figure captions, and table captions
may follow the main paper body.

## Evidence To Preserve

Object-maintenance evidence:

- Same-day Aisle: `203/11/5`;
- Cross-day Aisle: `240/10/5`;
- Cross-month Aisle: `297/14/7`;
- Hallway secondary branch: `537/16/9`;
- dynamic-like rejection share: `50.0%-71.4%`;
- rejection taxonomy: `dynamic_contamination 16`, `single_session_or_low_session_support 13`, `label_fragmentation 3`, `low_support 2`;
- P154-P157 admission defense: parameter ablation, baseline comparison, visualization, per-category analysis;
- tracked figures under `paper/figures/`.

Dynamic-mask frontend evidence:

- P217 dataset: 237 rows, 156/51/30 split, zero frame overlap, positive pixel rate 0.374176;
- P218 compact UNet: validation IoU/F1 0.671304/0.803329, test IoU/F1 0.578580/0.733038;
- P219 held-out precision/recall/F1/IoU 0.556007/0.789669/0.604636/0.443210;
- P220 GT dynamic-region ORB keypoints 4795 -> 2192, 54.2857% reduction;
- P225 60-frame Oct. 12, 2022 Aisle_CW sequence, source indices 480-539, bounded retrained SmallUNet because the P218 checkpoint was unavailable;
- P227 DROID 60f raw/masked APE 0.088504/0.084529, RPE 0.076145/0.076226, ORB predicted-region 21030 -> 18617, status neutral;
- P228 gated module: threshold 0.50, dilation 1 px, min component 128 px, max/target coverage 0.22/0.18, mean coverage 14.127053%, DROID 60f raw/masked APE 0.088496/0.084705, RPE 0.076145/0.076224, ORB gated-region 8969 -> 5073.

## Claim Boundaries

Keep the claims conservative:

- P228 is a bounded frontend smoke and viable story seed.
- Do not claim a full dynamic-SLAM benchmark.
- Do not claim navigation or planning gain.
- Do not claim independent dynamic segmentation ground truth.
- Do not claim learned persistent-map admission.
- P195 remains BLOCKED.
- DROID trajectory results are neutral; the supported P228 improvement is the
  stronger ORB predicted/gated-region suppression proxy.

## Execution Rules

- Do not download new datasets for manuscript cleanup.
- Do not start long experiments while editing the thick draft.
- Do not add unsupported citations.
- Do not touch `paper/manuscript_en.md` or `paper/manuscript_zh.md` unless
  explicitly asked.
- Do not touch unrelated dirty evidence files or untracked third-party/ORB
  files during manuscript-only work.
- Prefer coherent thick prose over checklist fragments.
- When updating dynamic-mask claims, cite the relevant export summaries:
  `paper/export/p228_paper_story_results.md`,
  `paper/export/p225_baseline_reproduction_p227.md`, and
  `paper/export/confidence_gated_mask_module_p228.md`.

## Done When

A thick-draft reorganization pass is complete when:

- English and Chinese thick drafts share the same section/table-level structure;
- P225-P228 appear in Dynamic-Mask Frontend, Results, and Limitations/Boundary sections;
- object-maintenance evidence and citations remain present;
- brief drafts are left untouched;
- a short export summary records what changed;
- lightweight checks confirm P227/P228 appear in both thick drafts.
