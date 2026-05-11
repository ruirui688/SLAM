# P222 Manuscript Section: Dynamic-Mask Training and Front-End Masking

**Status:** manuscript-ready documentation update  
**Scope:** P217-P220 dynamic/non-static mask front-end training and masking
evaluation. This section is not an admission-control training claim.

## Suggested Manuscript Text

### Dataset-Mask-Supervised Dynamic/Non-Static Front End

The current learned component is a semantic dynamic/non-static mask front end,
not the persistent-map admission gate. It is trained from dataset-provided
TorWIC/AnnotatedSemanticSet semantic/indexed masks and is used only to suppress
dynamic/non-static pixels before SLAM feature extraction.

P217 constructs the dataset from local `source_image.png`,
`combined_indexedImage.png`, and `raw_labels_2d.json` entries. Positive pixels
are semantic indices for `cart_pallet_jack`, `fork_truck`, `goods_material`,
`misc_dynamic_feature`, `misc_non_static_feature`, `person`, and `pylon_cone`.
Static object, context, and background pixels are encoded as zero.
`goods_material` is included as movable clutter for SLAM front-end masking; it
is not persistent-map admission ground truth.

The P217 manifest contains 237 rows from 79 frame groups. The split is
deterministic by frame group: 156 train rows, 51 validation rows, and 30 test
rows, with zero frame overlap across train/validation/test. The overall
dynamic/non-static positive pixel rate is 0.374176.

P218 trains a compact UNet-style binary model in the `tram` CUDA environment on
an NVIDIA RTX 3060. The smoke configuration resizes inputs to `320x180`, runs
for 5 epochs with batch size 8, and optimizes
`BCEWithLogitsLoss(pos_weight=1.489919) + 0.5 * DiceLoss`. The selected
operating threshold is 0.40 from validation F1. Validation IoU/F1 are
0.671304/0.803329; test IoU/F1 are 0.578580/0.733038.

P219 packages six held-out validation/test samples with raw images, predicted
masks, ground-truth dynamic masks, and masked images. Mean mask
precision/recall/F1/IoU are 0.556007/0.789669/0.604636/0.443210. P220 evaluates
feature-level effects using ORB in the `tram` OpenCV environment: raw keypoints
total 10059 and masked keypoints total 9972, while ground-truth dynamic-region
keypoints drop from 4795 to 2192, a 54.2857% reduction.

This evidence supports a front-end dynamic-region suppression claim only. The
P219 package is six held-out frames, not a timestamped SLAM sequence with
calibration and aligned trajectory ground truth. Therefore P220 reports no
trajectory ATE/RPE and does not support a raw-vs-masked SLAM trajectory
improvement claim.

### Admission-Control Boundary

The dynamic-mask model must be separated from learned persistent-map admission
control. P195 remains `BLOCKED` because independent `human_admit_label` and
`human_same_object_label` supervision is absent: `0/32` valid admission labels
and `0/160` valid same-object labels. P193 weak-label admission training and
rule-derived proxy fields remain historical evidence only and cannot support a
learned admission-control claim.

## Evidence Anchors

- Dataset: `paper/export/dynamic_mask_dataset_p217.md`
- Training: `paper/export/dynamic_mask_training_p218.md`
- Held-out masking package: `paper/export/frontend_masking_eval_p219.md`
- ORB feature proxy: `paper/export/frontend_masking_slam_smoke_p220.md`
- Admission-control gate: `paper/export/independent_supervision_gate_p195.md`
