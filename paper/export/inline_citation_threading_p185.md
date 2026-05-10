# P185 Inline-Citation Threading — ORB-SLAM3 Caveat Verification

Date: 2026-05-10
Project: industrial-semantic-slam
Scope: low-cost DeepSeek worker verification, persisted by OpenClaw maintainer owner loop.

## Verdict

PASS. The ORB-SLAM3 sparse-keyframe caveat is consistently represented across the P173 metrics note, P184 claim-boundary package consistency artifact, and `paper/tro_submission/main.tex`.

## Evidence checked

- `paper/export/claim_boundary_package_consistency_p184.md`
- `paper/export/orb_slam3_cross_check_p173_metrics.md`
- `paper/tro_submission/main.tex`
- `paper/tro_submission/references.bib`
- `paper/tro_submission/ANONYMIZATION_CHECKLIST.md`

## Main finding

`main.tex` Limitations item 8 correctly states that the ORB-SLAM3 mono cross-check on Jun 15 Aisle_CCW produced sparse keyframe trajectories only:

- raw: 5 keyframes
- masked: 9 keyframes
- approximately 1.2 s covered from a 64-frame / approximately 7 s window
- evo APE/RPE are mathematically valid on matched keyframes
- raw/masked APE RMSE: 0.041 / 0.043 m
- not directly comparable to DROID-SLAM dense per-frame trajectories
- no raw-vs-masked improvement claim
- no trajectory-neutrality generalization claim
- no cross-backend performance claim

## Citation-anchor check

ORB-SLAM3 is cited in related work / comparison contexts through `campos2021orb3`. The limitations item describes the local P173 experimental cross-check rather than a claim from the ORB-SLAM3 paper itself, so adding another `\cite{campos2021orb3}` to that caveat is not required.

## Over-claim check

No ORB-SLAM3 over-claim was found in the checked surfaces. Current wording is bounded to a low-power backend-risk check.

## Next owner-loop step

Do not spend another Codex edit pass on ORB-SLAM3 wording unless a later audit finds drift. Continue with broader pre-submission cleanup from P184 / anonymization scope:

1. EXIF / embedded metadata stripping or verification.
2. PDF metadata verification.
3. path-string audit for local absolute paths.
4. supplementary JSON / package navigator freshness check.

## Status

P185 ORB-SLAM3 citation-threading sub-scope is complete. Recommended next active phase: pre-submission anonymization and metadata/package consistency cleanup.
