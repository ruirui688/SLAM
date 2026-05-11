# P216 No-Manual Training Redirect

**Status:** REDIRECT_READY_NO_MANUAL_MASK_TRAINING_P195_BLOCKED
**Recommendation:** Start P216A: train semantic segmentation / binary dynamic-mask front-end from dataset-provided TorWIC masks; do not train admission control.

## Direct Answer

The P206-P215 path drifted away from model training. It is useful evidence governance, but it cannot by itself train a model. Manual labels were requested because P195 correctly requires independent admission and same-object ground truth before any learned admission-control claim. Those labels remain absent, so P195 must stay blocked.

The next scientifically valid no-manual route is not admission learning. It is dataset-mask-supervised semantic segmentation or binary dynamic/static mask training from TorWIC/AnnotatedSemanticSet masks, followed by SLAM front-end dynamic masking evaluation.

## What Can Be Trained Now

### Rank 1: P216A dataset-provided semantic segmentation and binary dynamic/static mask training

- Status: `immediately_executable_cuda_smoke`
- Target: pixel-level semantic category masks from AnnotatedSemanticSet; optional binary movable/dynamic mask derived from TorWIC semantic categories
- Validity: The labels are dataset-provided segmentation masks and raw_labels_2d categories, not persistent-map admission or same-object labels.
- Claim allowed: learned semantic segmentation or dynamic-object masking front-end for SLAM preprocessing
- Claim blocked: learned persistent-map admission control or cross-session same-object association

### Rank 2: P216B SLAM front-end dynamic object masking from dataset masks

- Status: `executable_preprocessing_path`
- Target: mask RGB/depth features for movable categories before DROID/ORB front-end evaluation
- Validity: Uses local segmentation masks as masks, not as admission ground truth.
- Claim allowed: front-end masking ablation using semantic masks and downstream ATE/RPE/feature metrics
- Claim blocked: admission-control learning

### Rank 3: P216C self-supervised temporal consistency representation learning

- Status: `valid_but_second_order`
- Target: photometric/depth/semantic consistency over adjacent frames, evaluated as representation or mask-consistency pretraining
- Validity: No human admission labels are required, but it still needs a clean downstream evaluation protocol.
- Claim allowed: self-supervised pretraining or consistency regularization
- Claim blocked: admission decisions without independent labels

### Rank 4: P216D object-level persistent-map admission learning

- Status: `blocked`
- Target: human_admit_label and human_same_object_label
- Validity: Requires independent labels that do not exist locally yet.
- Claim allowed: none until P195 unblocks
- Claim blocked: learned admission control

## Local Evidence

- AnnotatedSemanticSet raw label JSON files: 237
- Paired source image and indexed mask samples: 237
- Semantic categories with positive pixels: 15
- Sequence zip left RGB/greyscale mask pairs: 32743
- CUDA smoke: `pass`

## P216 Implementation Plan

1. Build `TorchDataset` loaders for `AnnotatedSemanticSet_Finetuning.zip` source images and `combined_indexedImage.png` masks.
2. Train a compact segmentation baseline with class weights and leave-root/frame-id splits; report mIoU, dynamic-binary IoU, per-category IoU, and mask coverage.
3. Collapse movable categories into a binary dynamic/non-static mask head for SLAM front-end masking.
4. Export masks into the existing raw-vs-masked DROID/ORB evaluation path and report only front-end masking/trajectory effects.
5. Keep P195 admission/same-object learning blocked until independent labels exist.

## Leakage Guard

- P195 status: `BLOCKED`
- Human labels blank: `True`
- P216 does not use `target_admit`, `current_weak_label`, `selection_v5`, P193 labels, or model predictions as targets.
