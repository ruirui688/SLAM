# P236 Soft-Boundary Candidate Integration

Status: integrated into thick manuscripts and P236 lock.

## Scope

- Updated only thick manuscripts:
  - `paper/manuscript_en_thick.md`
  - `paper/manuscript_zh_thick.md`
- Left brief manuscripts untouched:
  - `paper/manuscript_en.md`
  - `paper/manuscript_zh.md`

## Integrated Story

P228 remains the original hard black confidence/coverage-gated story seed on 480-539: APE 0.088496 -> 0.084705, RPE 0.076145 -> 0.076224, and ORB gated-region keypoints 8969 -> 5073.

P233 prevents overclaiming: hard gating is mixed across windows. It reduces ORB on 120-179 (5927 -> 4820) but reverses on 840-899 (601 -> 1901).

P234 explains the failure: no tested threshold/coverage/component/dilation setting fixes 840-899. The best proxy hard/post-processing variant still gives 127 -> 1197, consistent with hard black mask boundary keypoint creation.

P235 provides the candidate frontend fix: `meanfill035_feather5_thr060_cap012_min256` changes 840-899 ORB 127 -> 0 with total keypoint delta 0 and neutral DROID smoke (16f dAPE -0.000036/dRPE +0.000007; 60f dAPE +0.000158/dRPE -0.000003). Backtests remain ORB-positive: 480-539 gives 1382 -> 188 and 120-179 gives 215 -> 20.

## Claim Boundary

Use as bounded frontend module evidence only. Do not claim:
- full benchmark support,
- navigation or planning gain,
- independent dynamic-label validation,
- learned persistent-map admission.

P195 remains BLOCKED.

## Files

- Lock JSON: `paper/evidence/thick_results_lock_p236.json`
- Lock report: `paper/export/thick_results_lock_p236.md`
- Integration summary: `paper/export/soft_boundary_candidate_integration_p236.md`
- Rebuilt exports: `paper/export/manuscript_en_thick.html`, `paper/export/manuscript_en_thick.pdf`, `paper/export/manuscript_zh_thick.html`, `paper/export/manuscript_zh_thick.pdf`
