# P197 Semantic Evidence Protocol

**Status:** reviewer evidence enrichment only. P197 does not generate labels, train a model, or unblock P195.

## Boundary

- P195 remains blocked until real human labels are entered.
- `human_admit_label`, `human_same_object_label`, confidence, and notes columns are preserved from P196 and are not inferred by this script.
- Semantic categories are auxiliary evidence only. Reviewers must decide from visual/object evidence and may ignore semantic hints when ambiguous.
- No `selection_v5`, `current_weak_label`, `model_prediction`, or `rule_proxy_fields` values are used to create human labels.

## Raw Evidence Sources

- TorWIC session zips under `data/TorWIC_SLAM_Dataset/<date>/<route>.zip`.
- AnnotatedSemanticSet zip: `data/TorWIC_SLAM_Dataset/Oct. 12, 2022/AnnotatedSemanticSet_Finetuning.zip`.

## Mapping Rules

- A P196 review row is mapped to TorWIC raw segmentation evidence only when its session id gives a supported TorWIC date/route and its frame id/index gives an existing zip member.
- The script records left color and greyscale segmentation masks when both exist; right masks are included when present.
- AnnotatedSemanticSet label mappings are audited as an ontology/source inventory, but row-level mapping is `unmatched` because the zip lacks route/session and object identity fields required for a safe join.
- If any required mapping information is absent, the row is marked `unmatched`; the script does not guess.

## Category Hint Sets

- Static-like hints: `ceiling, fixed_machinery, misc_static_feature, rack_shelf, wall_fence_pillar`.
- Dynamic/non-static-like hints: `cart_pallet_jack, fork_truck, misc_dynamic_feature, misc_non_static_feature, person, pylon_cone`.

## Mapping Summary

- Boundary rows: `{'matched_torwic_segmentation': 32}`.
- Pair rows: `{'matched_torwic_segmentation_pair': 160}`.
- AnnotatedSemanticSet raw label files: `237`.

## Outputs

- `paper/evidence/semantic_evidence_packet_p197.json`
- `paper/evidence/admission_boundary_label_sheet_p197_semantic_review.csv`
- `paper/evidence/association_pair_candidates_p197_semantic_review.csv`

These CSVs append semantic evidence columns only. Human labels remain blank.
