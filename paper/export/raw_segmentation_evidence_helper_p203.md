# P203 Raw Segmentation Evidence Helper

**Status:** EVIDENCE_INDEX_BUILT_P195_STILL_BLOCKED

## Boundary

Reusable no-label evidence lookup only. This index contains raw frame evidence paths and provenance from P202 exact joins; it does not contain generated human/admission/same-object labels and does not train or materialize expanded AnnotatedSemanticSet training rows.

## Index Counts

- Rows: 572
- Join status counts: {'exact': 572}
- Row source counts: {'p193': 110, 'p197_boundary': 32, 'p197_pair': 320, 'p199': 110}
- Raw evidence paths: 3432/3432 existing
- All paths exist: True

## CLI

```bash
python3 tools/raw_segmentation_evidence_helper_p203.py build
python3 tools/raw_segmentation_evidence_helper_p203.py lookup --sample-id SAMPLE_ID
python3 tools/raw_segmentation_evidence_helper_p203.py lookup --observation-id OBSERVATION_ID
python3 tools/raw_segmentation_evidence_helper_p203.py summarize
python3 tools/raw_segmentation_evidence_helper_p203.py validate
```

## Outputs

- JSON index: `paper/evidence/raw_segmentation_evidence_index_p203.json`
- CSV index: `paper/evidence/raw_segmentation_evidence_index_p203.csv`

## Label Gate

- P195 remains `BLOCKED`.
- Human label columns remain blank; this helper does not write or infer them.

## P204 Recommendation

Use this helper for reviewer/audit sampling and raw evidence packet inspection. Do not expand AnnotatedSemanticSet categories into object-level training rows until route/session/object identity is available for a safe join.
