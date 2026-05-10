# P199 Semantic-Stability Auxiliary Dataset

**Status:** BUILT

## Scientific Boundary

P199 is a no-human-label auxiliary semantic stability dataset. It can support semantic/static-vs-dynamic prior experiments, but it does not replace independent admission labels, does not unblock P195, and does not justify learned admission-control claims.

## Dataset Counts

- Total rows: 110
- Non-ambiguous training-eligible rows: 75
- Ambiguous rows kept for audit, excluded from default training: 35
- Unknown rows: 0
- Target counts: `{'ambiguous_static_and_dynamic': 35, 'dynamic_or_non_static_like': 36, 'static_like': 39}`
- Split/target counts: `{'test': {'dynamic_or_non_static_like': 20, 'static_like': 22}, 'train': {'dynamic_or_non_static_like': 12, 'static_like': 15}, 'val': {'dynamic_or_non_static_like': 4, 'static_like': 2}}`
- Category counts: `{'barrier': 35, 'forklift': 36, 'warehouse rack': 16, 'work table': 23}`

## Label Policy

- No `human_admit_label` or `human_same_object_label` values are created.
- P193 `target_admit`, `current_weak_label`, `selection_v5`, and model predictions are not used as P199 targets.
- The binary field `semantic_static_like` means static-like semantic category versus dynamic/non-static-like semantic category. It is not an admit/reject label.
- Barrier rows are marked ambiguous because their P197 ontology hint contains both `misc_static_feature` and `pylon_cone`.

## Outputs

- CSV: `paper/evidence/semantic_stability_dataset_p199.csv`
- JSON: `paper/evidence/semantic_stability_dataset_p199.json`

**Recommendation:** Use the non-ambiguous subset only for a bounded semantic/static-dynamic smoke. Keep P195 blocked until real human admission and same-object labels exist.
