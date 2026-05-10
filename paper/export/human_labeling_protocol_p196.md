# P196 Human Labeling Protocol

**Status:** review packet only. This phase prepares independent human labels for the P195 gate; it does not train a model and does not claim learned admission control.

## Inputs

- Boundary sheet: `paper/evidence/admission_boundary_label_sheet_p194.csv`
- Pair sheet: `paper/evidence/association_pair_candidates_p194.csv`
- P195 gate report: `paper/evidence/independent_supervision_gate_p195.json`
- Review CSVs with priority and evidence status:
  - `paper/evidence/admission_boundary_label_sheet_p196_review.csv`
  - `paper/evidence/association_pair_candidates_p196_review.csv`
- Packet manifest: `paper/evidence/human_labeling_packet_p196.json`

## Non-Negotiable Label Boundary

- Do not infer, guess, or backfill any `human_*` label.
- Do not copy `current_weak_label`, `weak_label_a`, `weak_label_b`, category names, model predictions, model probabilities, `same_weak_label`, centroid/size distances, or `rule_proxy_fields` into a human label.
- Use only the visual/object evidence in the referenced artifacts and the reviewer notes written during inspection.
- If evidence is insufficient, leave the human label blank and explain the uncertainty in `human_notes` or `human_pair_notes`.

## Admission Label: `human_admit_label`

Fill this column only after inspecting `image_or_artifact_reference`.

- `1` = admit: the observation is a persistent-map object candidate. It appears to be stable infrastructure or a durable object that should be eligible for long-term semantic map maintenance.
- `0` = reject: the observation should not enter the persistent map. Typical reasons include dynamic agent, movable/transient clutter, severe segmentation ambiguity, insufficient object evidence, or a visual crop that does not support persistent-object admission.
- blank = uncertain or not reviewable. Use this when the image/artifact does not provide enough evidence for an independent judgment.

Also fill:

- `human_label_confidence`: use `high`, `medium`, or `low`.
- `human_notes`: short visual rationale, especially for low-confidence or blank cases.

## Pair Label: `human_same_object_label`

Fill this column only after comparing `artifact_reference_a` and `artifact_reference_b`.

- `1` = same physical object: both artifacts show the same persistent object instance across frames/sessions.
- `0` = different object: artifacts show different physical objects, object identity is inconsistent, or the visual evidence contradicts a same-object association.
- blank = uncertain or not reviewable. Use this when the two artifacts do not contain enough identity evidence.

Also fill:

- `human_pair_notes`: short rationale, including visual features used for identity or the reason the pair remains undecidable.

## Minimum Order For Rerunning P195

P195 currently requires at least 24 valid boundary labels and 40 valid pair labels, with both label classes covered. The recommended review order is encoded by `reviewer_priority`.

1. Boundary labels: label the first 24 rows by `reviewer_priority`, while ensuring train/val/test are all represented and both human classes (`0` and `1`) appear. Prioritize false-positive, near-threshold, proxy-sensitive, and infrastructure-boundary cases.
2. Pair labels: label the first 40 rows by `reviewer_priority`, while ensuring both same-object (`1`) and different-object (`0`) examples appear. If the first 40 visually all belong to one class, continue down the priority list until both classes are represented.
3. Keep uncertain rows blank. More total reviewed rows are better than forcing labels on weak evidence.

## Evidence Availability

- Boundary rows: 32 total, 32 existing visual references, 0 missing.
- Pair rows: 160 total, `artifact_reference_a` existing/missing = 160/0, `artifact_reference_b` existing/missing = 160/0.

Rows with missing evidence should not receive a forced label. In the current packet, the missing-evidence lists are recorded in `human_labeling_packet_p196.json`.

## Rerun Gate After Human Review

After real human labels are entered in the P194 or P196 review CSVs and copied into the P194 source columns expected by P195, rerun:

```bash
python3 tools/prepare_independent_supervision_p195.py
```

Until real `human_*` labels exist, P195 must remain `BLOCKED`.
