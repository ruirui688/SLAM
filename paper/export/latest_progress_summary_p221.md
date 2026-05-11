# P221 Latest Research Progress Sync

**Status:** P221_PROGRESS_SYNC_COMPLETE  
**Date:** 2026-05-11  
**Latest completed experimental phase:** P220 (`8af9ef8 exp: audit P220 front-end masking smoke`)  
**Scope:** documentation/export synchronization only. No new training, no downloads, no raw-data edits, no human-label creation, and no long experiments.

## Executive Summary

The project has a valid no-manual front-end training route in P216-P220, but learned persistent-map admission control remains blocked.

- **Blocked route:** P193/P195 learned admission control. P193 CUDA training ran, but its weak-label target has proxy leakage risk. P195 correctly blocks claim-worthy training because independent labels are absent.
- **Governance route:** P206-P215 built a no-label evidence governance and appendix bundle. This is useful for audit/reviewer support, but it is not real model training.
- **Active valid training route:** P216 redirected to dataset-provided TorWIC/AnnotatedSemanticSet semantic masks and binary dynamic/non-static masks. P217-P220 then built the dataset, trained a compact mask front-end, packaged held-out masking examples, and audited ORB feature-level effects.
- **Latest scientific boundary:** We can claim dataset-mask-supervised semantic/dynamic front-end masking evidence. We cannot claim learned admission control, learned same-object association, or SLAM trajectory improvement.

## Code Artifacts, P193-P220

### Admission-Control Line, P193-P198

- `tools/train_admission_scorer_frame_gpu_p193.py` and P193 evidence/export artifacts completed a weak-label CUDA admission scorer, but the target was not independent ground truth.
- `paper/evidence/admission_frame_dataset_p193.csv` / `.json` are retained as historical evidence, not as claim-worthy admission training data.
- `tools/prepare_independent_supervision_p195.py` remains the decisive gate for learned admission control.
- `paper/evidence/independent_supervision_gate_p195.json` reports `BLOCKED`: boundary labels are `32` total / `32` blank / `0` valid; pair labels are `160` total / `160` blank / `0` valid.
- `tools/sync_review_labels_p198.py` validates the review-label sync path but performs dry-run validation only unless independent labels exist.

### No-Label Evidence Governance, P199-P215

- P199-P205 explored semantic-stability and raw-evidence audit support without manual labels.
- P206-P215 converted that work into evidence governance: diverse packet, quality-note protocol, safety tests, ingestion audit, cross-phase index, release governance, release bundle, and appendix index.
- Key outputs include:
  - `paper/export/evidence_only_release_bundle_p214.md`
  - `paper/export/evidence_only_appendix_index_p215.md`
  - `paper/evidence/evidence_only_release_bundle_p214.json`
- Boundary: these artifacts support evidence audit and paper appendix traceability only. They do not create labels and do not train admission control.

### Valid No-Manual Dynamic-Mask Route, P216-P220

- **P216 redirect:** `tools/prepare_no_manual_training_redirect_p216.py` documents the shift from no-label governance to valid dataset-mask-supervised training.
- **P217 dataset:** `tools/build_dynamic_mask_dataset_p217.py` builds a deterministic binary dynamic/non-static mask dataset from dataset-provided semantic/indexed masks.
- **P218 training:** `tools/train_dynamic_mask_p218.py` trains a compact binary segmentation model in the `tram` CUDA environment.
- **P219 package:** `tools/prepare_frontend_masking_eval_p219.py` exports six held-out raw/mask/masked-image samples and mask-quality proxy metrics.
- **P220 audit:** `tools/audit_frontend_masking_slam_p220.py` checks runtime availability and ORB keypoint proxy behavior without forcing invalid trajectory claims.

## Evidence and Export Artifacts

Latest front-end route artifacts:

- `paper/evidence/no_manual_training_redirect_p216.json`
- `paper/export/no_manual_training_redirect_p216.md`
- `paper/evidence/dynamic_mask_dataset_p217.json`
- `paper/evidence/dynamic_mask_dataset_p217.csv`
- `paper/export/dynamic_mask_dataset_p217.md`
- `paper/evidence/dynamic_mask_training_p218.json`
- `paper/export/dynamic_mask_training_p218.md`
- `paper/evidence/frontend_masking_eval_p219.json`
- `paper/evidence/frontend_masking_eval_p219.csv`
- `paper/export/frontend_masking_eval_p219.md`
- `paper/evidence/frontend_masking_slam_smoke_p220.json`
- `paper/evidence/frontend_masking_slam_smoke_p220.csv`
- `paper/export/frontend_masking_slam_smoke_p220.md`

Latest progress-sync artifact:

- `paper/export/latest_progress_summary_p221.md`

## Data and Training Status

### P217 Dataset

- Source: local TorWIC/AnnotatedSemanticSet dataset-provided semantic/indexed masks.
- Total rows: `237`
- Frame groups: `79`
- Split: train `156`, validation `51`, test `30`
- Frame overlap across splits: `0`
- Overall positive dynamic/non-static pixel rate: `0.374176`
- No `target_admit`, `current_weak_label`, `selection_v5`, model-prediction target, or human-label column is used as a training label.

### P218 Dynamic-Mask Training

- Environment: `tram`, NVIDIA GeForce RTX 3060, PyTorch CUDA.
- Model: compact UNet-style binary dynamic/non-static mask front-end.
- Resize: `320x180`
- Epochs: `5`
- Batch size: `8`
- Selected threshold: `0.40` from validation F1.
- Validation metrics: IoU `0.671304`, F1 `0.803329`, precision `0.716614`, recall `0.913920`, balanced accuracy `0.842796`.
- Test metrics: IoU `0.578580`, F1 `0.733038`, precision `0.601953`, recall `0.937109`, balanced accuracy `0.815713`.
- Baseline: all-background dynamic IoU/F1 is `0.0/0.0` on validation and test.

### P219 Front-End Masking Package

- Held-out samples: `6` (`3` validation, `3` test)
- Mean predicted masked pixel rate: `0.208691`
- Mean GT dynamic pixel rate: `0.137248`
- Mean mask precision/recall/F1/IoU: `0.556007` / `0.789669` / `0.604636` / `0.443210`
- Boundary: mask quality and front-end package only; no SLAM trajectory metrics.

### P220 ORB Feature Proxy

- `tram` OpenCV is available (`4.12.0`); default Python OpenCV remains unavailable due NumPy ABI mismatch.
- ORB-SLAM3 wrapper/headless/vocabulary/camera assets are locally available.
- P219 package is six held-out frames, not a temporal SLAM sequence; it lacks timestamps, calibration, and trajectory GT.
- ORB feature proxy:
  - Raw keypoints total: `10059`
  - Masked keypoints total: `9972`
  - GT dynamic-region raw keypoints: `4795`
  - GT dynamic-region masked keypoints: `2192`
  - GT dynamic-region keypoint reduction: `54.2857%`
- Boundary: this is a feature-level proxy showing dynamic-region feature suppression. It is not an ATE/RPE or trajectory claim.

## README Status

The root README now includes a concise **Current Research Status** section that points readers to this P221 summary, identifies P216-P220 as the active valid training route, and warns that P195 learned admission control remains blocked.

The README's final current-status section has also been updated from the older 2026-05-09 snapshot to the P220/P221 state.

## Claim Boundaries

Allowed:

- Dataset-mask-supervised dynamic/non-static semantic front-end training.
- Held-out front-end masking package metrics.
- ORB feature proxy showing reduced GT dynamic-region keypoints after P218 masking.
- Evidence governance and appendix readiness for no-label audit artifacts.

Not allowed yet:

- Learned persistent-map admission control.
- Learned cross-session same-object association.
- Claims that P193 weak-label admission training is claim-worthy.
- Claims that P206-P215 evidence governance is real training.
- Raw-vs-masked SLAM trajectory improvement, ATE/RPE improvement, map-quality improvement, or navigation benefit from P218 masks.

## Blockers

- **P195 remains blocked:** no independent `human_admit_label` or `human_same_object_label` values exist.
- **P219/P220 trajectory blocker:** the held-out P219 package is frame-level, not a timestamped SLAM sequence with calibration and aligned trajectory ground truth.
- **OpenCV environment split:** default Python OpenCV import fails locally, while `tram` OpenCV works. Future ORB/DROID checks should use the documented `tram` environment.

## Recommended Next Steps

1. Build a small temporally aligned held-out raw-vs-P218-masked sequence package from existing local data.
2. Include timestamps, calibration, and GT trajectory alignment before running ORB-SLAM3 or DROID-SLAM.
3. Report trajectory availability first, then ATE/RPE only if alignment is valid.
4. Keep P195 blocked until independent human labels are collected/imported through the existing review protocol.
5. Do not revisit P193 weak-label admission as a claim path unless the target is replaced with independent supervision.

## Verification Snapshot

- P195 evidence exists and reports `BLOCKED`.
- P217, P218, P219, and P220 evidence JSON files exist and report their completed statuses.
- No new scripts were added in P221, so no new `py_compile` check is required.
- P221 made documentation/export changes only.
