# P195 Independent-Label Gate

**Status:** BLOCKED
**Decision:** do not train or claim learned admission control until human labels are collected

## Label Availability

- Boundary review rows: 32
- `human_admit_label`: blank=32, valid=0, invalid=0
- Pair candidates: 160
- `human_same_object_label`: blank=160, valid=0, invalid=0

## Gate Result

P195 is blocked because independent human labels are not yet available in sufficient quantity. Current artifacts are review sheets, not training labels.

**Current claim boundary:** the project cannot claim learned admission control from P193/P194 weak labels. It can only claim review-ready supervision preparation plus leakage/proxy stress evidence.

Blocking reasons:
- only 0 valid human_admit_label values; need at least 24
- only 0 valid human_same_object_label values; need at least 40
- human_admit_label does not cover both admit and reject classes
- human_same_object_label does not cover both same-object and different-object classes
- human_admit_label missing required split coverage: ['test', 'train', 'val']

## Leakage / Proxy Audit

- P193 dataset proxy columns present: {'dynamic_ratio': True, 'is_forklift_like': True, 'is_infrastructure_like': True, 'label_purity': True}
- Boundary rows carrying `rule_proxy_fields`: 32 / 32
- Reference model proxy features used: ['dynamic_ratio', 'is_forklift_like', 'is_infrastructure_like', 'label_purity']
- P195 training policy: do not train on `rule_proxy_fields`; drop `dynamic_ratio, is_forklift_like, is_infrastructure_like, label_purity` for no-proxy/anti-proxy runs.
- Split overlap after P193 dedup: {'physical_key_overlap_by_split_pair': {'test|train': 0, 'test|val': 0, 'train|val': 0}, 'sample_id_overlap_by_split_pair': {'test|train': 0, 'test|val': 0, 'train|val': 0}}

## Counts

P193 weak-label dataset:

```json
{
  "total": 110,
  "by_split": {
    "test": {
      "n": 60,
      "reject": 23,
      "admit": 37
    },
    "train": {
      "n": 42,
      "reject": 14,
      "admit": 28
    },
    "val": {
      "n": 8,
      "reject": 4,
      "admit": 4
    }
  },
  "by_label": {
    "admit": {
      "n": 69
    },
    "reject": {
      "n": 41
    }
  },
  "by_category": {
    "barrier": {
      "n": 35,
      "admit": 34,
      "reject": 1
    },
    "forklift": {
      "n": 36,
      "reject": 36
    },
    "warehouse rack": {
      "n": 16,
      "reject": 3,
      "admit": 13
    },
    "work table": {
      "n": 23,
      "admit": 22,
      "reject": 1
    }
  }
}
```

P194 boundary review sheet:

```json
{
  "by_split": {
    "test": {
      "n": 17
    },
    "train": {
      "n": 13
    },
    "val": {
      "n": 2
    }
  },
  "by_split_label": {
    "test": {
      "unlabeled": 17
    },
    "train": {
      "unlabeled": 13
    },
    "val": {
      "unlabeled": 2
    }
  },
  "by_category": {
    "barrier": {
      "n": 11
    },
    "forklift": {
      "n": 2
    },
    "warehouse rack": {
      "n": 8
    },
    "work table": {
      "n": 11
    }
  },
  "by_category_label": {
    "barrier": {
      "unlabeled": 11
    },
    "forklift": {
      "unlabeled": 2
    },
    "warehouse rack": {
      "unlabeled": 8
    },
    "work table": {
      "unlabeled": 11
    }
  }
}
```

## Executable Human Labeling Instructions

1. Open `paper/evidence/admission_boundary_label_sheet_p194.csv` and review each image/artifact path in `image_or_artifact_reference`.
2. Fill `human_admit_label` with only `1` for persistent-map admit or `0` for reject. Leave genuinely undecidable rows blank and explain in `human_notes`.
3. Fill `human_label_confidence` with a compact confidence value such as `high`, `medium`, or `low`.
4. Open `paper/evidence/association_pair_candidates_p194.csv` and fill `human_same_object_label` with `1` for same physical object or `0` for different objects.
5. Do not copy `current_weak_label`, category names, or `rule_proxy_fields` into the human columns. The label must come from visual/object evidence.
6. Rerun this gate. If it passes, then run the recorded no-proxy/anti-proxy CUDA training command.
