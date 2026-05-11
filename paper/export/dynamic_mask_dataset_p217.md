# P217 Dynamic-Mask Dataset

**Status:** READY_NO_MANUAL_DYNAMIC_MASK_DATASET

## Boundary

P217 creates a no-manual semantic/dynamic-mask front-end dataset from dataset-provided TorWIC AnnotatedSemanticSet labels only. It does not create admission labels, same-object labels, or learned admission-control evidence.

## Dataset

- Rows: `237`
- Split counts: `{'test': 30, 'train': 156, 'val': 51}`
- Frame-group counts by split: `{'test': 10, 'train': 52, 'val': 17}`
- Overall dynamic/non-static positive pixel rate: `0.374176`
- Frame-group overlap: `{'train_val': 0, 'train_test': 0, 'val_test': 0}`

## Target Policy

- Positive categories: `cart_pallet_jack`, `fork_truck`, `goods_material`, `misc_dynamic_feature`, `misc_non_static_feature`, `person`, `pylon_cone`.
- `goods_material` is included as movable clutter because the dataset category denotes material/goods that can be rearranged in industrial scenes; this is a front-end non-static mask target, not persistent-map admission ground truth.
- Static object, context, and background pixels are encoded as binary 0.
- No P193 weak labels, admission targets, model predictions, or human-label placeholders are used.

## Outputs

- CSV manifest: `paper/evidence/dynamic_mask_dataset_p217.csv`
- JSON manifest: `paper/evidence/dynamic_mask_dataset_p217.json`
- Sanity contact sheet: `outputs/dynamic_mask_dataset_p217/sanity/p217_dynamic_mask_sanity.png`

## P195

- Status: `BLOCKED`
- Human labels remain blank: `True`
