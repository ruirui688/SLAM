# P194 Independent Boundary Supervision Preparation

**Status:** review-ready independent-supervision preparation complete. No human labels are claimed yet.
**Environment basis:** README.md §0.3 tram command form.

## Boundary Label Sheet

- Source dataset: `paper/evidence/admission_frame_dataset_p193.csv`
- Source model: `paper/evidence/admission_scorer_frame_gpu_p193.json`
- Review rows: 32
- False positives included: 3
- False negatives included: 0
- Near-threshold additions: 3
- Proxy-sensitive additions: 26
- CSV: `paper/evidence/admission_boundary_label_sheet_p194.csv`
- JSON: `paper/evidence/admission_boundary_label_sheet_p194.json`

Each row includes `human_admit_label`, `human_label_confidence`, and `human_notes` blank fields. These blanks are intentional: the sheet is ready for review but is not an independent training label set yet.

## Pairwise Association Candidate Dataset

- Candidate pairs: 160
- CSV: `paper/evidence/association_pair_candidates_p194.csv`
- JSON: `paper/evidence/association_pair_candidates_p194.json`
- Pair labels are blank (`human_same_object_label`) and must be reviewed before training.

## Sampling Strategy

1. Include all P193 MLP false admits / false rejects against the current weak labels.
2. Add near-threshold examples by `abs(probability - 0.5)`.
3. Add category-proxy-sensitive examples where forklift/infrastructure labels may dominate the target.
4. Add cross-session same-label pair candidates for future association supervision, prioritizing close geometry or weak-label disagreement.

## Risk Coverage

- Direct model errors are represented for human adjudication.
- Proxy-sensitive forklift/infrastructure cases are explicitly represented.
- Pairwise candidates cover the cross-session object association target that cluster-level weak labels cannot validate.

## Next Training Protocol

P195 should not train on this sheet until humans fill the blank label columns. After labels are filled, build a clean independent-supervision dataset that excludes target-proxy fields where appropriate, then rerun tram CUDA training and compare against P193 weak-label metrics plus P194 no-proxy stress.

## No-Proxy Leakage Stress Result

A tram CUDA stress run was completed with `dynamic_ratio`, `label_purity`, `is_forklift_like`, and `is_infrastructure_like` removed from the feature set.

- Output JSON: `paper/evidence/admission_scorer_no_proxy_p194.json`
- Output report: `paper/export/admission_scorer_no_proxy_p194.md`
- GPU: NVIDIA GeForce RTX 3060, PyTorch `2.4.0+cu118`, CUDA `11.8`
- Full-proxy P193 MLP Hallway test accuracy/F1: `0.9500 / 0.9610`
- No-proxy P194 MLP Hallway test accuracy/F1: `0.8667 / 0.9000`
- No-proxy validation accuracy/F1: `0.5000 / 0.6000` on only 8 validation samples

Interpretation: removing obvious proxy fields reduces performance and exposes additional boundary errors. This supports the blocker/risk that the weak-label model is partially dependent on category/rule proxies. P195 must use human-reviewed independent labels before claiming learned admission control.
