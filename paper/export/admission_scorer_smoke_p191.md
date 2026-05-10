# P191 Admission-Scorer Learned Smoke

**Status:** CPU-only learned model smoke completed; no GPU, no downloads, no SAM2 training.
**Model backend:** `numpy_logistic_regression`.
**Dataset:** `paper/evidence/admission_scorer_dataset_p190.csv` (51 samples).

## Sample Counts

- train: n=21, admit=10, reject=11
- val: n=14, admit=7, reject=7
- test: n=16, admit=9, reject=7

## Primary Model vs Rule Baseline

### train
- Learned all-features scorer: accuracy=1.0000, precision=1.0000, recall=1.0000, F1=1.0000, fp=0, fn=0.
- Rule baseline: accuracy=1.0000, precision=1.0000, recall=1.0000, F1=1.0000, fp=0, fn=0.

### val
- Learned all-features scorer: accuracy=0.8571, precision=1.0000, recall=0.7143, F1=0.8333, fp=0, fn=2.
- Rule baseline: accuracy=1.0000, precision=1.0000, recall=1.0000, F1=1.0000, fp=0, fn=0.

### test
- Learned all-features scorer: accuracy=0.6875, precision=0.7000, recall=0.7778, F1=0.7368, fp=3, fn=2.
- Rule baseline: accuracy=1.0000, precision=1.0000, recall=1.0000, F1=1.0000, fp=0, fn=0.

## Ablation Summary

- `all_features` (11 features): val acc/F1=0.8571/0.8333; test acc/F1=0.6875/0.7368; test fp/fn=3/2.
- `no_dynamic_ratio` (10 features): val acc/F1=0.8571/0.8333; test acc/F1=0.6875/0.7368; test fp/fn=3/2.
- `geometry_only` (4 features): val acc/F1=0.6429/0.5455; test acc/F1=0.7500/0.7143; test fp/fn=0/4.
- `support_only` (3 features): val acc/F1=0.7857/0.7692; test acc/F1=0.6250/0.6667; test fp/fn=3/3.
- `no_label_category_flags` (8 features): val acc/F1=0.8571/0.8333; test acc/F1=0.8125/0.8421; test fp/fn=2/1.

## Largest All-Feature Coefficients

- `session_count`: +2.498824
- `dynamic_ratio`: -2.008970
- `is_forklift_like`: -1.994768
- `is_infrastructure_like`: +1.994768
- `label_purity`: -1.648838
- `mean_size_x`: +1.262075
- `support_count`: +1.193199
- `frame_count`: +1.083902

## Risk / Interpretation

- This is a real trained CPU model, but only a feasibility smoke: the labels are weak labels generated from the current rule gate.
- The transparent rule baseline scores 1.000 by construction, so the learned model is not yet a contribution claim; it validates the dataset/training/evaluation contract and exposes boundary cases.
- Features such as `dynamic_ratio`, `label_purity`, and label/category flags are potential label-leakage or rule-proxy channels; the ablation block is therefore part of the result, not an optional appendix.
- The test split is Hallway within-site variation, not an independent external deployment site; sample size remains small (51 clusters).

## P192 Plan

Mine P191 false admits/false rejects plus near-threshold samples into a human-review boundary-label sheet. The next expansion should add independent admission-boundary labels or pairwise cross-session association labels before claiming a learned component improves on the rule system.
