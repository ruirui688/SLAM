# P207 Raw Evidence Quality Notes Protocol

**Status:** evidence-quality notes only; P195 remains `BLOCKED`.

## Scope

This protocol is for reviewing the P206 diversity-first raw evidence packet for visual evidence quality only. It may record whether the RGB/depth/segmentation evidence is clear enough for later inspection, but it must not record object-admission decisions or same-object association decisions.

## Allowed Note Fields

| column | allowed values | meaning |
| --- | --- | --- |
| `visibility_quality` | `blank`, `clear`, `partial`, `poor`, `not_assessable` | Whether the object evidence is visually inspectable in the image. |
| `mask_alignment_quality` | `blank`, `good`, `minor_issue`, `major_issue`, `not_assessable` | Whether the segmentation mask appears aligned enough for evidence review. |
| `depth_quality` | `blank`, `usable`, `limited`, `unusable`, `not_assessable` | Whether the depth image appears usable for evidence inspection. |
| `occlusion_level` | `blank`, `none`, `low`, `medium`, `high`, `not_assessable` | Apparent visual occlusion level only. |
| `blur_level` | `blank`, `none`, `low`, `medium`, `high`, `not_assessable` | Apparent motion/focus blur level only. |
| `reviewer_note` | free text, <=500 chars | Short evidence-quality note. Do not write label decisions here. |
| `quality_blocker` | `blank`, `no`, `yes` | `yes` only when evidence quality prevents reliable evidence inspection. |

Blank values are valid. The generated P207 notes template intentionally leaves all note fields blank.

## Forbidden Content

- Do not fill, infer, or store `human_admit_label`.
- Do not fill, infer, or store `human_same_object_label`.
- Do not write admit/reject, accept/reject, same-object/different-object, or equivalent decisions in any P207 note field.
- Do not copy `target_admit`, `current_weak_label`, `selection_v5`, model predictions, model probabilities, or weak labels into P207.
- Do not turn `canonical_label`, category names, row source, source, mask quality, depth quality, occlusion, blur, or reviewer notes into admission labels or same-object labels.
- Do not train models or tune admission-control thresholds from P207 notes.
- Do not edit raw images, depth, segmentation files, the P206 packet, or upstream evidence data while using this protocol.

## Validation

Run:

```bash
python3 tools/build_evidence_quality_notes_p207.py validate
```

Validation checks allowed value domains, evidence path existence, duplicate/blank sample IDs, prohibited label/proxy columns, and possible label-decision text in `reviewer_note`.

## Current Template Summary

- Notes CSV: `paper/evidence/raw_evidence_quality_notes_p207.csv`
- Notes JSON: `paper/evidence/raw_evidence_quality_notes_p207.json`
- Rows: 32
- Raw evidence paths: 192/192 existing
- All note fields blank: True

## Scientific Boundary

P207 records evidence quality only. It creates no labels, performs no training, and does not support learned admission-control claims. P195 remains blocked until independent human admission and same-object labels exist.
