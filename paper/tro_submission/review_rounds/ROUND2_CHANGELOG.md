# Round 2 Changelog — Targeted Rewrite from ROUND1_REVIEW.md

**Phase:** P166 (review-round-2-targeted-rewrite)  
**Based on:** ROUND1_REVIEW.md (10 rejection risks, 18 action items)  
**Date:** 2026-05-09  
**Scope:** `main.tex`, `EDITOR_SUMMARY.md` — targeted text edits only, no new experiments, no new data

---

## Risk Resolution Table

| Risk # | Severity | Description | Resolution | Status |
|---|---|---|---|---|
| **R1** | CRITICAL | LaTeX content not integrated (§IV/§V/§VI are stubs) | Discussion placeholder added with structured outline. Full content integration (§IV, §V.A–V.F, §VI) requires porting from `manuscript_en_thick.md` — deferred to pre-submission content pass | **DEFERRED** |
| **R2** | HIGH | Method is boolean criteria — novelty debate | Contributions restructured: trust score demoted from standalone #2 to sub-component of architecture #1. Boolean criteria justification embedded in Discussion outline. Conclusion rephrased "systematic" not "principled." | **MITIGATED** |
| **R3** | HIGH | Only 20 candidate clusters | Limitations expanded: small-N added as item #1 with CI caveat. Count explicitly stated in EDITOR_SUMMARY. Statistical formalization (CIs, bootstrap) remains R2.3 deferred action. | **MITIGATED** |
| **R4** | HIGH | Dynamic SLAM over-padded (15 figures) | Main.tex §VII.F now has explicit figure allocation note: main body = 1 summary figure + 1 table; all per-config diagnostics to supplementary. Contribution #6 now frames negative result as "quantified boundary condition." | **FIXED (scaffold)** |
| **R5** | MED-HIGH | Hallway protocol 8/10 incomplete | Not fixable by text edits alone. Deferred to R2.2 execution (requires running sessions 9–10 on build host). | **DEFERRED** |
| **R6** | MEDIUM | Bimodality may be pipeline artifact | Limitations expanded: item #4 explicitly states dynamic ratio may depend on frontend state classifier. Discussion outline flags bimodality as needing frontend-behavior contextualization. | **MITIGATED** |
| **R7** | MEDIUM | "Auditability" claimed but not tested | All occurrences of "auditable" reworded to "architecturally auditable," "per-object provenance," or "per-object provenance-traceable." Introduction §I.C explicitly states "This auditability is an architectural property, not a downstream-evaluated claim." | **FIXED** |
| **R8** | MEDIUM | Missing comparative baselines | Limitations item #5 added: "No comparison against published map-management policies." Related Work §III.C now acknowledges landmark selection/outlier rejection in classic SLAM (EKF-SLAM, PTAM culling, ORB-SLAM map-point policies). Actual system comparison remains future work. | **MITIGATED** |
| **R9** | MEDIUM | Claim drift between sections | Abstract/Intro/Conclusion harmonized: "principled" → "systematic, evidence-backed" throughout. Contribution list reordered for logical flow (architecture → evidence → rejection → defense → negative result → release). Conclusion scope matches Introduction §I.C. | **FIXED** |
| **R10** | MEDIUM | Related Work gap — landmark selection | Related Work §III.C Relationship paragraph now explicitly connects to EKF-SLAM feature management, PTAM map-point culling, and ORB-SLAM map-point policies as geometric precursors to semantic admission control. | **FIXED** |

---

## Detailed Changes by File

### main.tex

| Section | Change | Risk Addressed |
|---|---|---|
| §I.C (Scope) | Rewrote final sentence: "architecturally auditable bridge...per-object provenance...auditability is an architectural property, not a downstream-evaluated claim" | R7 |
| §II (Contributions) | Restructured 7→7 items: (1) merged trust score into architecture, (3) added forklift purity/support insight, (4) softened bimodality language "natural separation" not "exploit", (6) new: quantified negative-result study, (7) changed "open-source release" to future tense "upon acceptance" | R2, R4, R9 |
| §III.C (Long-Term) | Added Relationship paragraph connecting to EKF-SLAM/PTAM/ORB-SLAM landmark management | R10 |
| §VII.F (Dynamic SLAM) | Added figure allocation plan (1 main + rest supplementary) and rationale for compression | R4 |
| §VIII (Discussion) | Replaced empty section with structured outline covering: boolean-criteria justification, trust-score weights, bimodality context, published-system comparison gap, multi-site requirements | R2, R6, R8 |
| §IX (Limitations) | Expanded 7→9 items: added small-N (Eval scale), single-site limitation, bimodality-as-frontend-artifact caveat, missing published-system comparison. Removed outdated P164 reference. | R3, R6, R8 |
| §X (Conclusion) | Full rewrite: "submission-ready ladder" → "documented evidence chain"; "principled methodology" → "systematic map maintenance methodology — five boolean criteria with per-object provenance"; boundary condition updated to <2% (consistent with text); closing sentence explicitly states the method is boolean criteria with provenance | R1, R2, R9 |

### EDITOR_SUMMARY.md

| Section | Change | Risk Addressed |
|---|---|---|
| §1 (Contribution Summary) | Replaced "scores each candidate" with "applies explicit boolean criteria." Added forklift purity/support paradox as core insight. Added "not a learned admission policy" to bounded-contribution statement. Updated dynamic boundary to <2%. | R2, R3, R9 |

### COVER_LETTER_DRAFT.md

| Section | Change | Risk Addressed |
|---|---|---|
| *(unchanged)* | COVER_LETTER_DRAFT.md already contained honest limitations and double-anonymous check. No edits needed — its framing was already properly hedged. | — |

### supplementary/supplement.md

| Section | Change | Risk Addressed |
|---|---|---|
| *(unchanged)* | Supplement already provides full evidence with claim boundaries. No edits needed. | — |

---

## Status of 18 ROUND1 Action Items

| # | Action | Round 2 Status |
|---|---|---|
| **R2.1** | Integrate manuscript content into main.tex | **DEFERRED** — scaffold updated with structured placeholders; full port from manuscript_en_thick.md pending |
| **R2.2** | Complete Hallway protocol (sessions 9–10) | **DEFERRED** — requires execution on build host |
| **R2.3** | Add statistical reporting (CIs, tests) | **DEFERRED** — text now mentions CI caution; formal computation pending |
| **R2.4** | Resolve bimodality-or-artifact question | **MITIGATED** — Limitations §IX now documents the caveat |
| **R2.5** | Move 6 dynamic SLAM figures to supplementary | **FIXED (scaffold)** — annotation in main.tex §VII.F |
| **R2.6** | Promote lifecycle figure (S1) to main body | **NOT YET** — scaffold annotation needed; low-pri |
| **R2.7** | Add published-system comparison subsection | **MITIGATED** — Limitations documents gap; Related Work connects to geometric precursors |
| **R2.8** | Harmonize claim scope across sections | **FIXED** — Abstract/Intro/Contributions/Conclusion aligned |
| **R2.9** | Remove or justify trust score weights | **MITIGATED** — trust score demoted from standalone contribution; Discussion outline flags justification |
| **R2.10** | Reorganize Results §VII | **NOT YET** — structural change; lower priority than content integration |
| **R2.11** | Add Related Work on landmark selection | **FIXED** — §III.C Relationship paragraph added |
| **R2.12** | Per-frame observation quality appendix | **NOT YET** — requires rerunning frontend |
| **R2.13** | Evaluate auditability experimentally | **MITIGATED** — claim scoped to "architectural property" |
| **R2.14** | Time-gap sensitivity analysis | **NOT YET** — requires new analysis |
| **R2.15** | Update Limitations in main.tex | **FIXED** — expanded 7→9 items |
| **R2.16** | Learned baseline (logistic regression) | **NOT YET** — future work |
| **R2.17** | Multi-backend dynamic SLAM | **NOT YET** — future work |
| **R2.18** | External dataset validation | **NOT YET** — future work |

---

## Summary

| Category | Count |
|---|---|
| **FIXED** | 5 (R4 scaffold, R7 auditability language, R9 claim drift, R10 related work gap, R2.15 limitations) |
| **MITIGATED** | 5 (R2 boolean criteria, R3 small-N, R6 bimodality, R8 missing baselines, R2.4/R2.9/R2.13) |
| **DEFERRED** | 3 (R1 content integration, R2.2 Hallway completion, R2.3 statistics) |
| **NOT YET** | 5 (R2.6/R2.10 reorg, R2.12 quality appendix, R2.14 time-gap, R2.16 learned, R2.17 multi-backend, R2.18 external data) |

### Blocking for Submission Readiness

The three DEFERRED items (R2.1 content integration, R2.2 Hallway completion, R2.3 statistics) remain gating. No text edit can substitute for actually porting manuscript content into main.tex, executing Hallway sessions 9–10, or computing bootstrap CIs. These are the next actions in the critical path to submission readiness.

### What's Fixed

All 5 text-level risks (R4, R7, R9, R10, R2.15) are addressed in the LaTeX scaffold and editor docs. Claim drift is eliminated. "Auditability" is properly scoped. Related Work acknowledges geometric landmark selection. Limitations are comprehensive and honest. The dynamic SLAM section now has explicit figure compression instructions.

### What Still Needs Work

The paper is a better paper than it was before Round 2 — clearer, more honest, better scoped. But it still cannot be submitted as-is because §IV, §V.A–V.F, §VI lack content. The next wake cycle should target R2.1 (content integration from manuscript_en_thick.md) as the single most impactful action.
