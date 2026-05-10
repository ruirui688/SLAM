# P200 Semantic-Stability Audit

**Status:** AUDIT_COMPLETED

## Scientific Boundary

P200 audits the no-human-label P199 semantic-stability branch only. The target is semantic/static-like category evidence, not admission control. P200 does not create human labels, does not train admit/reject from P193/P194/P195 labels, and does not unblock P195.

## Main Finding

The audit supports a skeptical reading: the P199 target is deterministic from non-ambiguous semantic category labels, while geometry/area/session-only stress tests are unstable and do not establish category-independent semantic-stability learning. The P199 CUDA result remains a bounded pipeline smoke/evidence artifact, not an admission-control result.

## Dataset

- Input: `paper/evidence/semantic_stability_dataset_p199.csv`
- Total rows: 110
- Non-ambiguous audited rows: 75
- Ambiguous barrier rows excluded from learned stress tests: 35
- Category/target counts: `{'forklift|0': 36, 'warehouse rack|1': 16, 'work table|1': 23}`
- Source/target counts: `{'cross_day|0': 9, 'cross_day|1': 13, 'cross_month|0': 4, 'cross_month|1': 2, 'hallway|0': 20, 'hallway|1': 22, 'same_day|0': 3, 'same_day|1': 2}`

## Feature Ablations

Original P199 train/val/test split; learned models use only numeric geometry/area/support/gate features.

| Feature set | Val acc/F1 | Test acc/F1 |
|---|---:|---:|
| `geometry_only` | 0.1667/0.2857 | 0.7857/0.8235 |
| `area_only` | 0.3333/0.5000 | 0.5238/0.6875 |
| `support_only` | 0.3333/0.5000 | 0.5238/0.6875 |
| `no_semantic_gate_score` | 0.1667/0.2857 | 0.7857/0.8235 |
| `all_numeric` | 0.1667/0.2857 | 0.7857/0.8235 |

## Baselines

- Majority on P199 test: acc=0.5238, f1=0.6875
- Geometry threshold on P199 test: acc=0.4762, f1=0.6071
- Category-definition oracle on P199 test: acc=1.0000, f1=1.0000 (perfect by construction).
- P199 reported MLP/logistic test: acc=0.8333, f1=0.8571 / acc=0.8333, f1=0.8571.

## Leave-Group-Out Stress Tests

Leave-category-out is degenerate: every non-ambiguous category is single-class, so there is no held-out category with both target classes. Training on one category is also single-class and infeasible for supervised binary learning.

| Held-out source | n | class counts 0/1 | Logistic acc/F1 | Majority acc/F1 | Geometry threshold acc/F1 |
|---|---:|---:|---:|---:|---:|
| `cross_day` | 22 | 9/13 | 0.8182/0.8462 | 0.4091/0.0000 | 0.4091/0.5806 |
| `cross_month` | 6 | 4/2 | 0.5000/0.4000 | 0.3333/0.5000 | 0.6667/0.6667 |
| `hallway` | 42 | 20/22 | 0.8095/0.8333 | 0.5238/0.6875 | 0.4762/0.6071 |
| `same_day` | 5 | 3/2 | 0.4000/0.4000 | 0.4000/0.5714 | 0.2000/0.0000 |

| Held-out source family | n | class counts 0/1 | Logistic acc/F1 | Majority acc/F1 | Geometry threshold acc/F1 |
|---|---:|---:|---:|---:|---:|
| `aisle` | 33 | 16/17 | 0.8182/0.8125 | 0.5152/0.6800 | 0.4242/0.2963 |
| `hallway` | 42 | 20/22 | 0.8095/0.8333 | 0.5238/0.6875 | 0.4762/0.6071 |

## P195 and Label Boundary

- P195 status: `BLOCKED`.
- Human label audit remains blank/non-admission; no labels were fabricated or filled.
- P200 does not train on `selection_v5`, `current_weak_label`, P193 `target_admit`, or human-label columns.

## Recommendation

For P201, prioritize collecting or importing independent human admission/same-object labels and rerun the P195 gate. If staying no-label, treat semantic stability only as an ontology/category prior and add new non-ambiguous categories where each semantic category is represented across multiple geometry and source regimes before claiming learned generalization.
