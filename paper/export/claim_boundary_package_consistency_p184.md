# P184 Claim-Boundary / Citation / Package Consistency Artifact

**Date:** 2026-05-10
**Phase:** P184-final-polish-citation-verification
**Scope:** bounded paper/package consistency pass after the P173 ORB-SLAM3 cross-check and P183 hostile-review simulation.

## Sources Read

- `paper/export/orb_slam3_cross_check_p173_metrics.md`
- `paper/evidence/orb_slam3_cross_check_p173_metrics.json`
- `paper/tro_submission/REVIEWER_ATTACKS_P183.md`
- `paper/tro_submission/main.tex`
- `paper/tro_submission/ANONYMIZATION_CHECKLIST.md`
- `outputs/torwic_submission_readiness_checklist_v1.md`
- `outputs/torwic_submission_ready_package_index_v10.md`
- `outputs/torwic_submission_ready_closure_bundle_v36.md`
- `outputs/torwic_submission_ready_appendix_table_closure_v15.md`

## P173 Evidence Boundary

The ORB-SLAM3 evidence is valid only as a low-power backend-risk check:

- ORB-SLAM3 produced sparse `KeyFrameTrajectory.txt` outputs only; no dense per-frame camera trajectory was available.
- Raw/masked matched samples are small: raw 5 keyframes, masked 9 keyframes.
- Coverage is partial: roughly 1.2 seconds of a 64-frame, approximately 7-second TorWIC Aisle window.
- evo APE/RPE are mathematically valid after timestamp matching and SE(3) Umeyama alignment.
- Raw/masked APE RMSE is effectively tied at 0.041/0.043 m, which does **not** support an improvement claim.
- RPE is computed over different sparse transition counts and should not be treated as directly comparable to DROID-SLAM dense per-frame trajectories.

**Allowed claim:** ORB-SLAM3 was built, ran headlessly on TorWIC, and produced numerically valid sparse-keyframe metrics; this lowers backend-specific reviewer risk by showing the pipeline is not DROID-only at the tooling level.

**Disallowed claims:** no ORB-SLAM3 raw-vs-masked improvement claim; no cross-backend trajectory-neutrality generalization; no direct comparison between ORB-SLAM3 sparse keyframe APE/RPE and DROID-SLAM dense per-frame APE/RPE.

## P183 Reviewer-Attack Coverage

This pass addresses the following P183 risks:

1. **C-M2 short-window / backend overclaim:** `main.tex` now states the ORB-SLAM3 result is sparse, underpowered, and non-comparable to DROID-SLAM dense per-frame trajectories.
2. **C-M3 Hallway wording:** remaining "scene-transfer" language in protocol description, figure caption, dynamic-SLAM replication paragraph, Discussion, and Conclusion was replaced with within-site / within-warehouse variation wording.
3. **C-M5 opaque internal terminology:** residual "richer" labels in the B0/B1/B2 baseline comparison were replaced with "Full Admission Control" / "full admission control".
4. **Single-backend limitation:** the former "Single VO backend" limitation was replaced with a bounded backend caveat that incorporates P173 without overstating it.

## `main.tex` Consistency Changes

Applied changes are intentionally wording/claim-boundary only; no experimental number was promoted beyond the source evidence.

- `scene-transfer branch` -> `within-site scene-variation branch`.
- `Hallway Scene-Transfer Branch` -> `Hallway Within-Site Variation Branch`, with the Hallway described as a different floor plan within the same TorWIC warehouse.
- Figure caption and dynamic-SLAM replication paragraph now use `Hallway within-site variation` rather than `Hallway scene-transfer`.
- Discussion subsection heading changed from cross-scene transfer to within-site variation and explicitly states that this is **not** cross-site generalization.
- Baseline labels now use B2 `Full Admission Control`, not B2 `Richer`.
- Limitation item now records the P173 ORB-SLAM3 sparse-keyframe caveat and forbids raw-vs-masked improvement/generalization claims.

## Submission Package Consistency

Current package status after this P184 delta:

- `outputs/torwic_submission_ready_package_index_v10.md` remains the definitive P148 package navigator, but it predates P173/P184 and therefore should not be treated as including the ORB-SLAM3 sparse-keyframe caveat.
- `outputs/torwic_submission_readiness_checklist_v1.md` remains structurally useful, but its CAMERA-READY verdict predates P173/P184; a final checklist refresh is needed before upload.
- `paper/tro_submission/ANONYMIZATION_CHECKLIST.md` still lists human/author-side pending items: figure watermark/path-string review, EXIF stripping, supplementary JSON/CSV path audit, PDF metadata after compilation, and repository-link/anonymization decisions.
- `outputs/torwic_submission_ready_closure_bundle_v36.md` is backend-environment-probe oriented and does not supersede P148 package completeness; P184 should be treated as a post-P148 paper-claim delta.

## Audit Verdict

**PASS with bounded caveat.** The manuscript claim boundary is now safer after P173: ORB-SLAM3 is represented as a sparse, low-power backend-risk check, while DROID-SLAM remains the primary trajectory-perturbation evidence chain. Package navigators/checklists remain mostly consistent but need a final P184-aware checklist refresh and a real LaTeX compile/PDF metadata check before external submission.
