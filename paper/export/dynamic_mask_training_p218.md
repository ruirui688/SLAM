# P218 Dynamic-Mask Training Smoke

**Status:** P218_DYNAMIC_MASK_TRAINING_SMOKE_COMPLETE

## Boundary

P218 trains a compact binary dynamic/non-static mask front-end from P217 dataset-provided semantic masks only. It does not train or claim persistent-map admission control.

## Training Config

- Device: `NVIDIA GeForce RTX 3060`
- CUDA available: `True`
- Resize: `320x180`
- Epochs: `5`
- Batch size: `8`
- Loss: `BCEWithLogitsLoss(pos_weight=1.489919) + 0.5 * DiceLoss`
- Deterministic horizontal augmentation: `False`

## Metrics

- Selected threshold: `0.40` from validation F1.
- Validation: pixel accuracy `0.826746`, precision `0.716614`, recall `0.91392`, F1 `0.803329`, dynamic IoU `0.671304`, balanced accuracy `0.842796`.
- Test: pixel accuracy `0.774521`, precision `0.601953`, recall `0.937109`, F1 `0.733038`, dynamic IoU `0.57858`, balanced accuracy `0.815713`.

## Baselines

- Val all-background dynamic IoU/F1: `0.0` / `0.0`.
- Test all-background dynamic IoU/F1: `0.0` / `0.0`.
- Train-prior threshold baseline predicts dynamic: `False` with train prior `0.387909`.

## Prediction Artifacts

- `val` `000000904_image-0`: `outputs/dynamic_mask_training_p218/predictions/val_000000904_image-0_pred_mask.png`, `outputs/dynamic_mask_training_p218/predictions/val_000000904_image-0_prob.png`, `outputs/dynamic_mask_training_p218/predictions/val_000000904_image-0_overlay.png`
- `val` `000000904_image-1`: `outputs/dynamic_mask_training_p218/predictions/val_000000904_image-1_pred_mask.png`, `outputs/dynamic_mask_training_p218/predictions/val_000000904_image-1_prob.png`, `outputs/dynamic_mask_training_p218/predictions/val_000000904_image-1_overlay.png`
- `val` `000000904_image-2`: `outputs/dynamic_mask_training_p218/predictions/val_000000904_image-2_pred_mask.png`, `outputs/dynamic_mask_training_p218/predictions/val_000000904_image-2_prob.png`, `outputs/dynamic_mask_training_p218/predictions/val_000000904_image-2_overlay.png`
- `test` `000000900_image-0`: `outputs/dynamic_mask_training_p218/predictions/test_000000900_image-0_pred_mask.png`, `outputs/dynamic_mask_training_p218/predictions/test_000000900_image-0_prob.png`, `outputs/dynamic_mask_training_p218/predictions/test_000000900_image-0_overlay.png`
- `test` `000000900_image-1`: `outputs/dynamic_mask_training_p218/predictions/test_000000900_image-1_pred_mask.png`, `outputs/dynamic_mask_training_p218/predictions/test_000000900_image-1_prob.png`, `outputs/dynamic_mask_training_p218/predictions/test_000000900_image-1_overlay.png`
- `test` `000000900_image-2`: `outputs/dynamic_mask_training_p218/predictions/test_000000900_image-2_pred_mask.png`, `outputs/dynamic_mask_training_p218/predictions/test_000000900_image-2_prob.png`, `outputs/dynamic_mask_training_p218/predictions/test_000000900_image-2_overlay.png`

## P195

- Status: `BLOCKED`
- Human labels remain blank: `True`

## Outputs

- JSON evidence: `paper/evidence/dynamic_mask_training_p218.json`
- Markdown report: `paper/export/dynamic_mask_training_p218.md`
- Prediction artifact directory: `outputs/dynamic_mask_training_p218/predictions`
