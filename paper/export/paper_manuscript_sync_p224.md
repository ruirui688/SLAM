# P224 Paper Manuscript Synchronization

**Status:** complete
**Scope:** documentation-only manuscript synchronization. No experiments,
training, label creation, downloads, or raw-data edits were performed.

## Audit Finding

Before P224, `paper/manuscript_en.md` already contained a P217-P220
dynamic/non-static mask front-end section, but the T-RO paper path still read
primarily as the older session-level admission-control manuscript. In
particular, `paper/tro_submission/abstract.tex` did not surface the current
dataset-mask-supervised training route, and `paper/tro_submission/main.tex`
needed a results-facing table/prose plus discussion/limitation/conclusion
threading.

## Manuscript Sections Changed

- `paper/manuscript_en.md`
  - Abstract: added compact P217-P220 metric summary and boundary statement.
  - Introduction: clarified that the learned route is pixel-mask front-end
    supervision, not object-admission supervision.
  - Results: added a P217-P220 metrics table and ORB proxy interpretation.
  - Discussion: added boundary language separating front-end mask learning from
    learned admission and same-object association.

- `paper/tro_submission/abstract.tex`
  - Added the P217 dataset size/split, P218 validation/test IoU-F1, P219
    held-out mask metrics, P220 ORB dynamic-region keypoint reduction, and the
    explicit boundary that the learned component is not learned persistent-map
    admission control and not an ATE/RPE improvement claim.

- `paper/tro_submission/main.tex`
  - Method: retained the dataset-mask-supervised front-end section from P222.
  - Results: added `Dataset-Mask-Supervised Front-End Training` with a table
    covering P217 dataset policy, P218 model/training metrics, P219 held-out
    metrics, and P220 ORB proxy.
  - Discussion: added `Separation Between Front-End Masking and Map Admission`.
  - Limitations: added a learned front-end boundary item.
  - Conclusion: added a final boundary paragraph.

- `paper/README.md`
  - Added current manuscript status and linked this P224 sync note.

## Required Current Values Threaded Into Manuscripts

- P217 dataset: 237 rows from 79 frame groups.
- Split: 156 train, 51 validation, 30 test; zero frame overlap.
- Positive dynamic/non-static pixel rate: 0.374176.
- P218 validation IoU/F1: 0.671304/0.803329.
- P218 test IoU/F1: 0.578580/0.733038.
- P219 held-out mean precision/recall/F1/IoU:
  0.556007/0.789669/0.604636/0.443210.
- P220 ORB proxy: raw keypoints 10059, masked keypoints 9972, GT
  dynamic-region keypoints 4795 -> 2192, reduction 54.2857%.

## Claim Boundary

- P195 learned persistent-map admission control remains blocked because
  independent `human_admit_label` and `human_same_object_label` values are
  absent (`0/32` and `0/160` valid).
- P217-P220 support dataset-mask-supervised dynamic/non-static front-end masking
  and feature-level dynamic-region suppression.
- P217-P220 do not support learned admission control, learned same-object
  association, same-object learning, trajectory ATE/RPE improvement, map-quality
  improvement, or downstream navigation gain.

## Verification

- Required metric scan passed across `paper/manuscript_en.md`,
  `paper/tro_submission/abstract.tex`, `paper/tro_submission/main.tex`,
  `paper/README.md`, `paper/tro_submission/README.md`, this sync note, and
  `RESEARCH_PROGRESS.md`.
- Claim-boundary scan found only negative/boundary mentions of learned
  admission control, same-object association, ATE/RPE improvement, trajectory
  improvement, map-quality improvement, and navigation gain in the changed
  manuscript surfaces.
- `git diff --check` passed for the changed docs.
- `python3 tools/prepare_independent_supervision_p195.py` returned `BLOCKED`
  with `0/32` valid `human_admit_label` and `0/160` valid
  `human_same_object_label`.
