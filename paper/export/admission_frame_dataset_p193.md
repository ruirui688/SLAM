# P193 Frame-Level Admission Dataset

**Environment basis:** README.md §0.3 tram environment. Build command recorded as:

```bash
LD_LIBRARY_PATH=/home/rui/miniconda3/envs/tram/lib: conda run -n tram python tools/build_admission_frame_dataset_p193.py --outputs-root outputs --cluster-labels paper/evidence/admission_scorer_dataset_p190.csv --output-json paper/evidence/admission_frame_dataset_p193.json --output-csv paper/evidence/admission_frame_dataset_p193.csv
```

## Inventory

- Observation index files scanned: 83
- Backend input manifests inventoried: 20
- Protocol source files retained: 24
- Observations seen in target protocols: 163
- Joined observations: 154
- Skipped no cluster match: 9

## Dataset Size

- Raw joined samples: 154
- Deduplicated training/eval samples: 110
- Removed duplicate physical keys: 44
- Dedup key: `physical_session(session_id)::frame_index::object_name`
- Cross-split overlap after dedup: 0

## Deduplicated Split / Label Distribution

- train: 42 samples = 28 admit / 14 reject
- val: 8 samples = 4 admit / 4 reject
- test: 60 samples = 37 admit / 23 reject

By source:

- cross_day: 31 = 21 admit / 10 reject
- same_day: 11 = 7 admit / 4 reject
- cross_month: 8 = 4 admit / 4 reject
- hallway: 60 = 37 admit / 23 reject

By label:

- barrier: 35 = 34 admit / 1 reject
- work table: 23 = 22 admit / 1 reject
- warehouse rack: 16 = 13 admit / 3 reject
- forklift: 36 = 0 admit / 36 reject

## Join Strategy

For each observation, the builder selects a same-protocol, same-session, same-label `selection_v5` cluster with nearest image-plane centroid/size. The target label is inherited from that cluster's selected/rejected status.

## Risks / Blockers

- Labels are still weak labels inherited from the rule-based `selection_v5` gate, not independent frame-level human labels.
- `dynamic_ratio` is represented by forklift-like label at observation level, so it is a strong label proxy; high GPU metrics cannot be claimed as learned scientific contribution.
- Validation is small after split-exclusive de-duplication (`n=8`), so validation accuracy is not reliable.
- Same physical scene content remains correlated across protocols even after direct duplicate physical keys are removed.
- P194 should create independent boundary labels and pairwise association labels before any claim that a learned scorer improves over rules.
