# P240 Soft-Boundary Self-Supervised Consistency Evidence

Status: `mixed_self_supervised_support`

## Plan Summary

- Keep the main contribution as object-level map maintenance; keep the dynamic frontend as a failure-driven soft-boundary support module.
- Add self-supervised motion/geometry/temporal consistency checks for the P235/P237 soft-boundary candidate without treating them as independent labels.
- Do not update thick manuscript body text in P240; export this report and evidence artifacts only.

## Metrics

- Temporal mask stability: adjacent binary mask IoU, adjacent probability-map soft IoU, and coverage coefficient of variation.
- Motion cue alignment: Farneback optical-flow high-motion enrichment and frame-difference high-cue enrichment inside the soft-mask region.
- Feature residual proxy: raw-vs-soft ORB keypoints inside the predicted region and in a boundary band; P234 hard-mask contrasts show hard-edge ORB inflation on 840-899.

## Soft-Boundary Windows

| Window | Source | Frames | Mask IoU | Prob IoU | Flow enrich | Diff enrich | Region ORB | Band ORB | Support |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `aisle_cw_0840_0899` | P235 | 60 | 0.785 | 0.966 | 0.339 | 0.257 | 127->0 | 400->169 | `False` |
| `aisle_cw_0240_0299` | P237 | 60 | 0.738 | 0.961 | 1.574 | 0.461 | 218->41 | 837->497 | `True` |
| `aisle_ccw_0240_0299` | P237 | 60 | 0.705 | 0.956 | 1.346 | 0.474 | 81->4 | 227->127 | `True` |
| `aisle_cw_0480_0539` | P235 | 60 | 0.385 | 0.929 | 1.799 | 1.802 | 1382->188 | 2226->1157 | `True` |
| `aisle_cw_0120_0179` | P235 | 60 | 0.720 | 0.961 | 0.393 | 0.579 | 215->20 | 1360->773 | `False` |

## Hard-Mask Contrast

| Contrast | Window | Variant | Region ORB | Band ORB | Pack |
| --- | --- | --- | ---: | ---: | --- |
| `p234_hard_best_aisle_cw_0840_0899` | `aisle_cw_0840_0899` | `thr060_cap012_min256_dil0` | 127->1197 | 400->3312 | `outputs/gated_mask_failure_sweep_p234/thr060_cap012_min256_dil0/dynamic_slam_backend_input_pack_p228_conf_gated` |
| `p234_hard_default_aisle_cw_0840_0899` | `aisle_cw_0840_0899` | `p233_default` | 601->1901 | 1067->6444 | `outputs/gated_mask_failure_sweep_p234/p233_default/dynamic_slam_backend_input_pack_p228_conf_gated` |

## Decision

The selected P235/P237 soft-boundary candidate is mixed in self-supervised checks: 3/5 representative windows pass all support flags. Treat this as diagnostic support only and inspect the failing flags before manuscript integration. P234 hard-mask contrasts on 840-899 show region ORB deltas [1070, 1300] and boundary-band ORB deltas [2912, 5377], preserving the hard-edge failure contrast.

## Claim Boundary

Self-supervised evidence only: not independent human-label validation and does not unblock P195. No full benchmark, navigation, learned-admission, or manuscript-body claim.

## Outputs

- JSON: `paper/evidence/soft_boundary_consistency_p240.json`
- CSV: `paper/evidence/soft_boundary_consistency_p240.csv`
- Report: `paper/export/soft_boundary_consistency_p240.md`
