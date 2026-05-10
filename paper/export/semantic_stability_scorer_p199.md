# P199 Semantic-Stability Scorer CUDA Smoke

**Status:** CUDA smoke completed for an auxiliary semantic/static-vs-dynamic target.

## Scientific Boundary

P199 is a no-human-label auxiliary semantic stability scorer. It predicts a semantic/static-vs-dynamic category prior derived from semantic categories, not persistent-map admission. It does not replace independent labels, does not unblock P195, and does not support learned admission-control claims.

## Environment

- Command: `LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib:$LD_LIBRARY_PATH /home/rui/miniconda3/bin/conda run -n tram python tools/train_semantic_stability_scorer_p199.py`
- Python: `/home/rui/miniconda3/envs/tram/bin/python`
- Torch: `2.4.0+cu118`; CUDA runtime `11.8`; GPU `NVIDIA GeForce RTX 3060`

## Dataset

- Dataset: `paper/evidence/semantic_stability_dataset_p199.csv`
- Non-ambiguous rows used: 75
- Split counts: `{'train': {'n': 27, 'dynamic_or_non_static_like': 12, 'static_like': 15}, 'val': {'n': 6, 'dynamic_or_non_static_like': 4, 'static_like': 2}, 'test': {'n': 42, 'dynamic_or_non_static_like': 20, 'static_like': 22}}`
- Features: `['mean_center_x', 'mean_center_y', 'mean_size_x', 'mean_size_y', 'support_count', 'mask_area_px', 'bbox_width', 'bbox_height', 'semantic_gate_score']`

## Metrics

### train
- MLP: accuracy=1.0000, F1(static-like)=1.0000, fp=0, fn=0.
- Logistic: accuracy=0.8889, F1(static-like)=0.9032, fp=2, fn=1.
- Majority baseline: accuracy=0.5556, F1(static-like)=0.7143.
- Geometry area baseline: accuracy=0.5185, F1(static-like)=0.6486.
- Category-definition baseline: accuracy=1.0000, F1(static-like)=1.0000.

### val
- MLP: accuracy=0.5000, F1(static-like)=0.4000, fp=2, fn=1.
- Logistic: accuracy=0.5000, F1(static-like)=0.4000, fp=2, fn=1.
- Majority baseline: accuracy=0.3333, F1(static-like)=0.5000.
- Geometry area baseline: accuracy=0.6667, F1(static-like)=0.6667.
- Category-definition baseline: accuracy=1.0000, F1(static-like)=1.0000.

### test
- MLP: accuracy=0.8333, F1(static-like)=0.8571, fp=6, fn=1.
- Logistic: accuracy=0.8333, F1(static-like)=0.8571, fp=6, fn=1.
- Majority baseline: accuracy=0.5238, F1(static-like)=0.6875.
- Geometry area baseline: accuracy=0.4762, F1(static-like)=0.6071.
- Category-definition baseline: accuracy=1.0000, F1(static-like)=1.0000.

## Limitations

- The target is category-derived and weak; the category-definition baseline is perfect by construction on non-ambiguous rows.
- Barrier rows are excluded from training because their semantic hint is mixed static/dynamic.
- This is not an admission-control model and does not use independent persistent-map labels.
- P195 remains blocked until real human labels exist.
