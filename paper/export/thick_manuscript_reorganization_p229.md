# P229 Thick Manuscript Reorganization

Date: 2026-05-13

## Scope

Reorganized the thick English and Chinese manuscripts as the active-only paper
target. The brief manuscripts were intentionally left untouched.

## Files Updated

- `paper/manuscript_en_thick.md`
- `paper/manuscript_zh_thick.md`
- `paper/THICK_DRAFT_DIRECTION.md`

## Structural Change

Both thick drafts now follow the same paper-level structure:

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

The English draft is the fuller working manuscript. The Chinese draft mirrors
the section and table structure with concise prose.

## Evidence Integrated

Object-maintenance evidence preserved:

- Same-day Aisle `203/11/5`
- Cross-day Aisle `240/10/5`
- Cross-month Aisle `297/14/7`
- Hallway `537/16/9`
- rejection taxonomy: `dynamic_contamination 16`,
  `single_session_or_low_session_support 13`, `label_fragmentation 3`,
  `low_support 2`
- P154-P157 admission defense summaries

Dynamic-mask evidence integrated:

- P217 dataset: 237 rows, 156/51/30 split, zero frame overlap, positive pixel
  rate 0.374176
- P218 compact UNet: validation IoU/F1 0.671304/0.803329, test IoU/F1
  0.578580/0.733038
- P219 held-out precision/recall/F1/IoU
  0.556007/0.789669/0.604636/0.443210
- P220 GT dynamic-region ORB keypoints 4795 -> 2192, 54.2857% reduction
- P225 60-frame Oct. 12, 2022 Aisle_CW package, source indices 480-539,
  bounded retrained SmallUNet due to unavailable P218 checkpoint
- P227 DROID learned-mask baseline: APE 0.088504 -> 0.084529, RPE
  0.076145 -> 0.076226, ORB predicted-region 21030 -> 18617
- P228 confidence/coverage gate: threshold 0.50, dilation 1 px, min component
  128 px, max/target coverage 0.22/0.18, mean coverage 14.127053%, APE
  0.088496 -> 0.084705, RPE 0.076145 -> 0.076224, ORB gated-region
  8969 -> 5073

## Claim Boundary

The drafts explicitly state that P228 is a bounded frontend smoke and viable
story seed, not a full dynamic-SLAM benchmark, navigation claim, independent
dynamic segmentation ground truth, or learned persistent-map admission result.
P195 remains BLOCKED. DROID trajectory results are treated as neutral; the
supported P228 improvement is stronger ORB predicted/gated-region suppression.

## Lightweight Checks

Recommended checks after this pass:

```bash
rg -n "P228|P227|P225|P217|P195|BLOCKED" paper/manuscript_en_thick.md paper/manuscript_zh_thick.md paper/THICK_DRAFT_DIRECTION.md
rg -n "^## " paper/manuscript_en_thick.md paper/manuscript_zh_thick.md
git status --short paper/manuscript_en_thick.md paper/manuscript_zh_thick.md paper/THICK_DRAFT_DIRECTION.md paper/export/thick_manuscript_reorganization_p229.md
```
