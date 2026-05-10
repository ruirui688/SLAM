# Cover Letter — T-RO Submission

**Target:** IEEE Transactions on Robotics, Regular Paper  
**Template:** T-RO cover letter (initial submission, double-anonymous)  
**Date:** [TO BE FILLED AT SUBMISSION TIME]  
**Status:** DRAFT — pending author information and advisor review

---

Dear Editor-in-Chief,

We submit the manuscript titled **"Session-Level Map Admission Control for Semantic-Segmentation-Assisted SLAM in Dynamic Industrial Environments"** for consideration as a regular paper in *IEEE Transactions on Robotics*.

**Contribution type:** This is a systems and methodology paper in the area of semantic SLAM and long-term map maintenance. It addresses a gap in current object-level SLAM architectures: the absence of an explicit admission-control policy that decides which detected objects merit permanent representation in a semantic map, as distinct from transient or dynamic contamination.

**Why T-RO:** The paper does not propose a new detection network or a new visual odometry algorithm. Its contribution is methodological: an explicit, auditable, multi-layer map maintenance architecture that transforms open-vocabulary detection output into durable semantic landmarks. IEEE T-RO has a well-established tradition of publishing systems contributions of this kind [cf. Cadena et al., T-RO 2016; Campos et al., T-RO 2021; Yang & Scherer, T-RO 2019], and the multi-component experimental validation—parameter ablation, baseline comparison, per-category rejection analysis, and a systematic dynamic-SLAM boundary-condition study—is designed to meet T-RO's thorough-evidence expectations.

**Key evidence:** The framework is evaluated on the TorWIC industrial dataset (POV-SLAM, RSS 2023) across three Aisle revisits (same-day, cross-day, cross-month) and a Hallway within-site variation protocol. Supporting evidence includes: (i) a 27-combination parameter ablation confirming natural data bimodality; (ii) a 3-baseline comparison (naive-all-admit, purity/support heuristic, and our cross-session policy) demonstrating that simpler heuristics cannot reject dynamic contamination; (iii) per-category retention and rejection analysis with a 5-reason taxonomy; and (iv) a 16-configuration DROID-SLAM boundary-condition study showing that selective masking is trajectory-neutral or near-neutral across five TorWIC sessions, while aggressive masking perturbs bundle adjustment.

**Honest limitations (explicitly disclosed):** (1) The dynamic SLAM backend evaluation is a negative result: masked input does not improve ATE/RPE in TorWIC warehouse aisles because forklift coverage is bounded below ~1.4% of frame area. We do not claim trajectory improvement. (2) Per-detection confidence scores were not preserved during observation extraction. (3) The maintenance layer is evaluated on one dataset (TorWIC), which is currently the only public multi-session industrial SLAM dataset with object-level annotations. (4) Only DROID-SLAM was tested as the visual odometry backend.

**Prior publication:** None of this material has been previously published or is under review elsewhere. The TorWIC dataset is publicly available from POV-SLAM (Barath et al., RSS 2023).

**Suggested reviewers:**

1. **[Reviewer 1]:** Expert in semantic SLAM and object-level mapping (e.g., a CubeSLAM or MaskFusion author / group member)
2. **[Reviewer 2]:** Expert in dynamic SLAM and long-term mapping (e.g., a DynaSLAM or RTAB-Map author / group member)
3. **[Reviewer 3]:** Expert in open-vocabulary perception / foundation models for robotics (e.g., an OpenScene or ConceptFusion author / group member)
4. **[Reviewer 4]:** Expert in SLAM evaluation methodology and industrial robotics
5. **[Reviewer 5]:** Expert in map maintenance and long-term autonomy

*Note: Suggested reviewers will be finalized after advisor review and conflict-of-interest checks. Placeholder descriptions indicate the expertise areas targeted.*

**ORCID and PaperCept:** All authors will register ORCID identifiers and the submission will be made through IEEE PaperCept (https://ras.papercept.net/) per T-RO guidelines.

**Manuscript statistics:** Approximately 14–16 pages in IEEEtran two-column format, 12 figures in main body, 6 tables, 35 references, with supplementary material (11 additional figures, 11 additional tables) provided as a separate document.

We confirm that this manuscript has been prepared in compliance with IEEE's double-anonymous review policy: the author block is empty, self-citations use third-person language, and the acknowledgments section has been removed.

Thank you for your consideration.

Sincerely,

[Author names to be filled]

---

## Notes for Author Before Submission

### Mandatory fields to complete:
- [ ] Author names and affiliations
- [ ] Corresponding author email
- [ ] ORCID IDs for all authors
- [ ] Date
- [ ] Finalize suggested reviewer list with specific names after conflict-of-interest check

### Double-anonymous verification:
- [ ] No author names in PDF metadata
- [ ] No acknowledgments section
- [ ] No funding disclosure in manuscript
- [ ] Self-citations anonymized (third-person: "Cadena et al. [1] presented...")
- [ ] No institutional identifiers in figures (logos, watermarks)
- [ ] No GitHub repo links that reveal author identity

### Page count:
- Estimated: 14–16 pages in IEEEtran. Within 20-page limit. Pages 13–20 incur mandatory overlength charges.
