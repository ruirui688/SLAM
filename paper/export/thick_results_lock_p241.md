# P241 Thick Manuscript Results Lock

Status: LOCKED for thick manuscripts only.

Active manuscript paths:
- `paper/manuscript_en_thick.md`
- `paper/manuscript_zh_thick.md`

Inactive manuscript paths:
- `paper/manuscript_en.md`
- `paper/manuscript_zh.md`

Claim boundary:
- P217-P240 support a bounded dynamic-mask frontend smoke/diagnostic and failure-diagnosis line only.
- P240 is mixed self-supervised consistency evidence, not independent human-label validation.
- P239 prepared an independent-label packet but collected no labels.
- Do not claim a full benchmark, navigation result, independent dynamic-label validation, or learned persistent-map admission result.
- P195 remains BLOCKED.

## Locked Numbers

| Phase | Locked result | Source evidence |
|---|---|---|
| P238 | Historical lock for P217-P237/P238 integration retained unchanged | `paper/evidence/thick_results_lock_p238.json` |
| P239 | Independent dynamic-label packet status `READY_FOR_INDEPENDENT_REVIEW`; no labels collected; P195 remains blocked | `paper/evidence/independent_dynamic_label_packet_p239.json` |
| P240 | Status `mixed_self_supervised_support`; selected variant `meanfill035_feather5_thr060_cap012_min256`; 3/5 windows pass all support flags | `paper/evidence/soft_boundary_consistency_p240.json` |
| P240 | `aisle_cw_0840_0899`: support `False`; mask IoU 0.785; prob IoU 0.966; flow enrich 0.339; diff enrich 0.257; region ORB 127 -> 0; boundary-band ORB 400 -> 169 | `paper/evidence/soft_boundary_consistency_p240.json` |
| P240 | `aisle_cw_0240_0299`: support `True`; mask IoU 0.738; prob IoU 0.961; flow enrich 1.574; diff enrich 0.461; region ORB 218 -> 41; boundary-band ORB 837 -> 497 | `paper/evidence/soft_boundary_consistency_p240.json` |
| P240 | `aisle_ccw_0240_0299`: support `True`; mask IoU 0.705; prob IoU 0.956; flow enrich 1.346; diff enrich 0.474; region ORB 81 -> 4; boundary-band ORB 227 -> 127 | `paper/evidence/soft_boundary_consistency_p240.json` |
| P240 | `aisle_cw_0480_0539`: support `True`; mask IoU 0.385; prob IoU 0.929; flow enrich 1.799; diff enrich 1.802; region ORB 1382 -> 188; boundary-band ORB 2226 -> 1157 | `paper/evidence/soft_boundary_consistency_p240.json` |
| P240 | `aisle_cw_0120_0179`: support `False`; mask IoU 0.720; prob IoU 0.961; flow enrich 0.393; diff enrich 0.579; region ORB 215 -> 20; boundary-band ORB 1360 -> 773 | `paper/evidence/soft_boundary_consistency_p240.json` |
| P240 | Hard-mask contrasts on 840-899: region ORB deltas [1070, 1300], boundary-band ORB deltas [2912, 5377] | `paper/evidence/soft_boundary_consistency_p240.json` |

## Manuscript Lock

The English and Chinese thick drafts now include:
- P240 `mixed_self_supervised_support` as diagnostic self-supervised support after the P235/P237 soft-boundary candidate.
- The 3/5 support count and the passing windows: `aisle_cw_0240_0299`, `aisle_ccw_0240_0299`, and `aisle_cw_0480_0539`.
- The two mixed windows: 840-899 and 120-179 remain temporal/ORB-supportive but fail the motion/frame-difference enrichment threshold.
- The P234 hard-mask contrast numbers preserving the hard-edge failure diagnosis.
- The unchanged boundary: no full benchmark, navigation, independent-label validation, learned map-admission claim, or P195 unblock.

The brief manuscripts were not edited.

Machine-readable lock:
- `paper/evidence/thick_results_lock_p241.json`

## Residual Risks
- P240 is self-supervised diagnostic evidence only, not independent human-label validation.
- Only 3/5 representative soft-boundary windows pass all P240 support flags.
- The 840-899 and 120-179 windows do not meet the motion/frame-difference enrichment threshold.
- P239 has no collected labels and does not unblock P195.
- No navigation, full-benchmark, or learned map-admission claim is unlocked.
- P195 remains BLOCKED.
