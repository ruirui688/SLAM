# Hostile Reviewer Simulation — P183

**Date:** 2026-05-10  
**Phase:** P183 — T-RO/IJRR hostile reviewer simulation and rebuttal prep  
**Method:** Three simulated reject-level reviews, each with major/minor concerns, evidence mapping, and rebuttal-ready responses  
**Status:** ✅ COMPLETE — risk map below, 3 text fixes recommended

---

## Reviewer A: Methodology and Contribution (Hostile)

**Profile:** Dyed-in-the-wool SLAM theoretician. Believes contribution must be a new mathematical framework or algorithm. Dislikes "architectural" papers. Will question whether this is a paper or an engineering report.

### Major Concerns

**A-M1: The contribution is five boolean thresholds. Where is the method?**

> The admission-control "method" (§V.E) consists entirely of five boolean criteria with hard thresholds: sessions≥2, support≥6, purity≥0.7, dynamic_ratio≤0.2, frames≥4. These are heuristics, not a method. The trust score (Eq.1) is a linear combination with no derivation, no optimality, no learning. The authors explicitly state the weights are "configurable, not optimized" — this is not a contribution, it is an admission of absence of method. A T-RO paper should have a principled formulation with guarantees. This paper's "method" is a configuration file.

*Evidence mapping:* §V.D (trust score admits "not an optimal estimator"), §V.E (five boolean criteria), §VIII.A (why boolean not learned).  
*Rebuttal backup:* The boolean criteria are deliberately transparent and auditable, not weak. Five criteria with per-object provenance at every layer is architecturally novel compared to SLAM's detection→geometry→insert pipeline. The ablation (27 combos) systemically validates the criterion set. Learned criteria would be less transferable across Aisle/Hallway.  
*Severity:* **HIGH** — if the reviewer frames heuristics as "no method," this is a desk-reject risk.

**A-M2: The four-layer architecture is just relabeling standard SLAM components.**

> Section V describes four layers: observation, tracklet, map-object, revision. But observation is detection (off-the-shelf Grounding DINO + SAM 2), tracklet is temporal association within a session, map-object is spatial matching across sessions, and revision is map update. Every SLAM system does detection, data association, map building, and map update. Renaming these standard components and adding admission criteria at the end does not constitute a new architecture. The claim of an "explicit maintenance layer" is semantic relabeling, not architectural novelty.

*Evidence mapping:* §I.C (scope boundaries), §IV.B (key distinction), §V (full method).  
*Rebuttal backup:* The claim is NOT that the components are new. The claim is that existing SLAM pipelines merge detection→geometric verification→insertion as a single step, with no explicit admission-control gate. The maintenance layer inserts a principled filter between geometric verification and map insertion — this gap is real (see Related Work §III.B relationship note).  
*Severity:* **MEDIUM-HIGH** — needs careful framing in rebuttal.

**A-M3: The trust score is arbitrary and its thresholds are post-hoc data characteristics.**

> Equation (1) assigns weights α=0.4, β=0.3, γ=0.5 with no derivation. The threshold observations (all retained τ≥0.4, all rejected τ≤0.15) are described as "empirical properties of the current data and are not claimed to generalize." If the weights are arbitrary and the thresholds don't generalize, what purpose does the trust score serve? It is neither learned, nor theoretically grounded, nor generalizable — it is a demonstration with three free parameters.

*Evidence mapping:* §V.D (trust score), §V.D qualification clause.  
*Rebuttal backup:* The trust score is an auxiliary diagnostic, not the primary gate (boolean criteria are). It is transparent and inspectable — each component has clear semantics (session persistence, observation volume, dynamicity penalty). The goal is NOT optimality but auditability: a domain expert can inspect why τ is high or low without interrogating a black box. The tradeoff (transparency vs optimality) is deliberate and defended in §VIII.A.  
*Severity:* **MEDIUM** — honest about limitations; reviewer may still be skeptical.

**A-M4: No comparison against published map-management policies.**

> The baseline comparison (§VII.G) uses two straw-man policies: "admit everything" (B0) and "purity/support only" (B1). The authors acknowledge in Limitations (§IX.5) that comparison against RTAB-Map's memory management or ORB-SLAM3's map-point culling is "deferred." If the contribution is a map-maintenance methodology, comparing against other map-maintenance policies is not optional — it is essential. The paper defeats two deliberately weak baselines and claims victory.

*Evidence mapping:* §IX.5, §VII.G baseline comparison.  
*Rebuttal backup:* RTAB-Map's memory management operates on geometric features (not semantic objects). ORB-SLAM3's map-point culling operates on reprojection error (not object identity). These are different domains — there is no off-the-shelf "semantic map admission control" baseline to compare against because the authors are defining the problem. The baselines are deliberately simple to isolate which signals (purity, support, dynamicity) provide discrimination.  
*Severity:* **HIGH** — legitimate objection from a methodology reviewer.

### Minor Concerns

**A-M5:** The term "evidence ladder" (§VI.B and throughout) is marketing. The paper evaluates 3 Aisle protocols — same-day, cross-day (8 days), cross-month (4 months) — which is a temporal progression, not an "evidence ladder." This is just multi-condition evaluation and should not be branded.

**A-M6:** The paper claims "auditability" as a contribution but never defines what constitutes an audit. Per-cluster provenance (session counts, label histograms) is standard practice in any database system — this is not an algorithmic contribution.

**A-M7:** §VIII.C's connection to EKF-SLAM, PTAM, and ORB-SLAM feature management is historically interesting but does nothing to establish the paper's contribution.

### Predicted Score: **Weak Reject (3)**

Core objection: insufficient algorithmic contribution for T-RO. The methodology is a set of heuristics, the architecture is relabeled standard components, and the baselines are weak.

---

## Reviewer B: Experiments and Statistics (Hostile)

**Profile:** Statistician-reviewer. Will count n, compute confidence intervals, flag all multiple-comparison issues, question sample sizes. Will demand more data or formal correction.

### Major Concerns

**B-M1: n=20 is too small to support the paper's claims.**

> The entire admission-control evaluation (§VII.G) operates on 20 candidate clusters after deduplication across all Aisle protocols. The per-protocol sizes are even smaller: 11 clusters (same-day), 10 (cross-day), 14 (cross-month). The authors report bootstrap 95% confidence intervals, but bootstrapping on n=11 is known to be unreliable — the CI coverage can be far below nominal at such small sample sizes. The Fisher exact test for Hallway vs Aisle (p=0.76) and the McNemar B1/B2 comparison (p=0.125, n=4 discordant pairs) both fail to reject the null at α=0.05. While the authors are honest about this (§IX.1), acknowledging a statistical problem does not resolve it. A T-RO paper should not rest its primary experimental claims on n=20 with non-significant hypothesis tests.

*Evidence mapping:* §VII.G tables, §IX.1, supplement S1-S6.  
*Rebuttal backup:* The per-protocol n values (10-14) are constrained by the dataset — TorWIC is the only multi-session industrial SLAM dataset with object annotations. The bootstrap CI caveats are explicitly documented. More importantly: the central claim does NOT depend on statistical significance. The 4/4 forklifts rejected with dynamic_ratio ≥ 0.83 vs all infrastructure at 0.00 is a complete separation — no statistical test negates this deterministic observation. McNemar B1/B2 p=0.125 has n=4 because there are only 4 forklift clusters that differ (B1 admits all, B2 rejects all) — this is a boundary property, not a power problem.  
*Severity:* **HIGH** — the most common reject reason for small-n papers.

**B-M2: The bootstrap CIs appear to be miscalculated or misleading.**

> The authors report per-protocol admission rates with bootstrap 95% CIs: same-day 45.5% (18.2–72.7%, n=11), cross-day 50.0% (20.0–80.0%, n=10), cross-month 50.0% (21.4–71.4%, n=14), Hallway 56.2% (31.2–81.2%, n=16), pooled 51.0% (37.3–64.7%, n=51). But the per-cluster admission decision is deterministic given the criteria — there is no random process generating the admission rate. Bootstrapping a deterministic outcome produces an interval that reflects only the discreteness of the binary outcome at small n, not uncertainty about the method's performance. This is misuse of bootstrapping.

*Evidence mapping:* EDITOR_SUMMARY.md, §IX.1, supplement.  
*Rebuttal backup:* The bootstrap is over clusters, treating each cluster's admission/rejection as a Bernoulli trial with probability equal to the unknown true admission rate — this is standard practice for small-sample proportion estimation. The fact that the decision is deterministic does not invalidate the CI; the CI captures sampling uncertainty over which clusters appear in the dataset, not algorithmic randomness. However, the CIs are wide and their interpretation should be tempered — the authors already say "interpret with appropriate caution" (§IX.1).  
*Severity:* **MEDIUM** — statistically sophisticated reviewer will notice this; most reviewers will not.

**B-M3: The dynamic SLAM evidence chain has no formal statistical test for neutrality.**

> The dynamic SLAM results (§VII.E-F) report 11/16 neutral configs (68.8%, 95% CI 43.8–87.5%) and describe a "complete gap" between the neutral group (|ΔAPE| ≤ 0.006 mm) and the perturbed group (0.92–7.52 mm). But "neutral" is defined by a post-hoc threshold of |ΔAPE| ≤ 0.006 mm — the value of the best neutral config. The gap is "complete" at the current sample, but there is no equivalence test (TOST) to formally demonstrate trajectory-neutrality. The APE values are computed from 64-frame single-window comparisons, not full-session trajectories — this is a short-horizon evaluation that may miss cumulative odometry drift.

*Evidence mapping:* §VII.E-F, Table 5, Table 6, supplement S4.  
*Rebuttal backup:* The 0.006 mm threshold is not post-hoc — it comes from the best-performing config in Group 1 (P134, no mask, 64-frame GBA) which sets the noise floor. The gap (0.914 mm) is large and there is zero overlap. An equivalence test would formalize this; the authors should consider adding it (or noting it as future work). The 64-frame window is acknowledged — earlier versions had longer windows but DROID-SLAM crashes on the full TorWIC sequence without GPU; this is an honest experimental constraint. The supplementary S4 provides per-config APE/RPE values.  
*Severity:* **MEDIUM** — the TOST/equivalence-test absence is noticeable to a statistician.

**B-M4: Multiple comparisons without correction.**

> The paper reports numerous hypothesis tests: McNemar B0/B1, B0/B2, B1/B2; Fisher exact Hallway vs Aisle; 27-combination ablation visually compared. The McNemar tests are reported with exact p-values but without Bonferroni or Holm correction. With 3 pairwise comparisons, the family-wise error rate exceeds α=0.05. The B0/B2 p<0.0001 would survive any correction; the B1/B2 p=0.125 is already non-significant — the issue is transparency.

*Evidence mapping:* §VII.G, §IX.1.  
*Rebuttal backup:* The McNemar tests are exact (not asymptotic), and the three comparisons are planned (not post-hoc). B0/B2 is the primary comparison (p<0.0001, survives any correction). B1/B2 is reported as supplementary context. The authors can add a note about multiplicity.  
*Severity:* **LOW** — easily fixed with a note.

### Minor Concerns

**B-M5:** The parameter ablation (27 combos) is in the supplement, not the main text. The main text only shows Table 7 (3 × 3 summary). A reviewer who doesn't read the supplement might miss the full sweep.

**B-M6:** The dynamic SLAM "Stage 2" Replication (P172-S2) adds Oct 12 cross-month and Hallway data — but Hallway has no forklifts, so the "selective mask" in Hallway masks 3/64 frames (max coverage 0.63%). Masking 3 frames out of 64 in a forklift-free environment is trivially expected to be neutral. Presenting this as "cross-scene reproducibility" oversells a near-trivial condition.

**B-M7:** The "high-coverage selective-mask pressure test" (max 17.32%, ΔAPE=+0.114 mm) is interesting but includes only one session. A single-observation pressure test is anecdotal, not systematic.

### Predicted Score: **Weak Reject (3)**

Core objection: evaluation scale (n=20) too small for T-RO; statistical tools misapplied or underpowered.

---

## Reviewer C: Dynamic SLAM, System Completeness, and Writing (Hostile)

**Profile:** Systems reviewer who has engineered real SLAM pipelines. Will question implementation details, missing evaluation modes, and writing quality. Hardest to please.

### Major Concerns

**C-M1: The dynamic SLAM section is irrelevant to the core contribution and should be removed or drastically shortened.**

> The paper's core claim is a map-admission control architecture. Yet Section VII.E-F (~200 lines, 12 figures, 3 tables) is entirely about DROID-SLAM trajectory evaluation under different dynamic masking conditions. This is a completely different research question — "does masking affect odometry?" — that has nothing to do with "which objects should be in the semantic map?" The paper states that "mask selectivity is a necessary condition for trajectory-neutrality" and that "our frontend produces sufficiently selective masks" — this is two sentences of contribution embedded in 200 lines of tangential validation. The dynamic SLAM section dilutes the paper's focus and makes it harder to follow the core argument. I recommend deleting it from the main text and moving it entirely to the supplementary material.

*Evidence mapping:* §VII.E-F, P179 R5 (dynamic SLAM section disproportionate).  
*Rebuttal backup:* The dynamic SLAM section serves as a **boundary condition study**, not the core contribution. It answers a reviewer question preemptively: if you mask objects for semantic map admission, does it break odometry? The answer matters because a rejection that helps map maintenance but harms pose estimation would be a non-starter. The section demonstrates that it does NOT break odometry (7/12 neutral) — this strengthens, not dilutes, the contribution.  
*Severity:* **HIGH** — this is a likely genuine reviewer concern. The R5 risk was noted in P179.

**C-M2: Single 64-frame window is not a DROID-SLAM evaluation.**

> The dynamic SLAM evaluation (§VII.E-F) compares trajectories over a SINGLE 64-frame window. DROID-SLAM typically operates over hundreds or thousands of frames on a full sequence. A 64-frame snippet cannot capture loop closures, long-term drift, or keyframe management — the very properties that make SLAM evaluations meaningful. The authors mention "DROID-SLAM crashes on the full TorWIC sequence" but do not explain why (GPU memory? frame rate? missing calibration?). Reporting ΔAPE on a 64-frame snippet and calling it a "DROID-SLAM evaluation" is misleading.

*Evidence mapping:* §VII.E-F, Table 5, supplement S4.  
*Rebuttal backup:* This is a legitimate and serious limitation. The 64-frame window is indeed short. The crash is due to DROID-SLAM's GPU memory requirements on a local desktop without CUDA — this is an honest experimental constraint, not an attempt to cherry-pick. The evaluation should be reframed as a "short-window bundle-adjustment perturbation study" rather than a "DROID-SLAM evaluation." The authors should consider a Cloud GPU run for full-sequence evaluation as future work.  
*Severity:* **HIGH** — a systems reviewer will tear into this.

**C-M3: The Hallway protocol is not a genuine scene-transfer test.**

> The paper presents Hallway as a "scene-transfer branch" and "negative-control environment." But Hallway is in the SAME warehouse building — it's the next corridor over from the Aisle, collected on the same three dates (Jun 15, Jun 23, Oct 12) with the same camera/lighting conditions. Calling this a "scene transfer" is misleading — it is within-site protocol variation, not scene transfer in any meaningful cross-site sense. The paper should call it what it is: a different area within the same building evaluated under the same collection conditions.

*Evidence mapping:* §VI.B Hallway description, §VII.C.  
*Rebuttal backup:* The Hallway is indeed within the same building — the authors already acknowledge single-site limitation (§IX.2, §VIII.D). "Scene-transfer" is used internally, not as a cross-site claim. The text should be revised to "within-site scene variation" or "different floor plan" throughout to avoid the cross-site implication. The Hallway's value is as a static-only environment verifying the framework doesn't spuriously reject infrastructure in the absence of dynamic agents.  
*Severity:* **MEDIUM** — wording issue, not evidence issue.

**C-M4: The supplementary evidence package is under-described in the main text.**

> The supplement (supplement.md) contains 11 sections with full tables, figures, and evidence logs. But the main text references to the supplement are sparse — some sections have no main-text pointer. For example, S7 (per-category figures 14-16) and S8 (evidence file index) receive no main-text reference. A reviewer trying to verify claims by following supplement pointers would find dead ends.

*Evidence mapping:* Supplement section headers, main-text cross-references.  
*Rebuttal backup:* Audit all supplement references and ensure every supplement section has a main-text pointer. This is a mechanical fix.  
*Severity:* **MEDIUM** — easily fixed.

**C-M5: The paper uses "richer" as an opaque internal label without defining it.**

> §VI.B describes the Aisle protocols using a "richer bundle configuration" — but never defines what "richer" means compared to what baseline. The term appears to be internal project terminology that leaked into the submission. Define or remove.

*Evidence mapping:* §VI.B, line ~255.  
*Rebuttal backup:* Replace "richer" with a descriptive term ("high-fidelity protocol bundle") or remove.  
*Severity:* **LOW** — embarrassing but not critical.

### Minor Concerns

**C-M6:** Figure 1 (pipeline overview) is dense and would benefit from a simplified version for the main text with a detailed version in the supplement. At the 150 DPI render resolution, fine text labels may be illegible in print.

**C-M7:** The contribution list (§II) has 7 items. Items 1-3 describe the paper structure, not contributions. Contributions should be statements of what the paper provides, not an enumerated table of contents.

**C-M8:** The abstract.tex uses author-year citations, but IEEEtran with the `journal` option uses numeric citations. Check consistency — mixed citation styles would be flagged by the IEEE production team.

**C-M9:** The paper never explicitly states the computing environment (CPU/GPU, memory, OS) used for DROID-SLAM experiments. Reproducibility requires this information.

### Predicted Score: **Borderline Reject (3.5)**

Core objections: dynamic SLAM section distracts from core contribution; DROID-SLAM evaluation window too short; "scene transfer" is misleading.

---

## Risk Aggregation

### Accept/Reject Risk by Reviewer

| Reviewer | Likely Score | Accept Risk | Major Concerns Count | Primary Objection |
|----------|-------------|-------------|---------------------|-------------------|
| A (Method) | 3 (Weak Reject) | 40% | 4 | Heuristics not method; no stronger baselines |
| B (Stats) | 3 (Weak Reject) | 35% | 4 | n=20 too small; bootstrapping on deterministic outcome |
| C (Systems) | 3.5 (Borderline) | 50% | 5 | Dynamic SLAM irrelevant; 64-frame not a SLAM eval |

### Aggregated Risk Profile

| Scenario | Probability | Outcome |
|----------|------------|---------|
| All three accept or borderline | ~5% | Accept with minor revision |
| Two accept, one weak reject | ~20% | Major revision likely |
| Two weak reject, one accept | ~45% | Reject; revise and resubmit |
| All three weak reject | ~30% | Desk reject |

**Conservative estimate: 60-70% chance of first-round reject with major revision opportunity.**

### Fatal Risks (Must Fix Before Submission)

| Risk | Severity | Fix Type | Section |
|------|----------|----------|---------|
| A-M4: No strong baselines | HIGH | **Text fix** — strengthen §IX.5 framing: RTAB-Map/ORB-SLAM3 operate on different domains; semantic map maintenance is a new problem | §VIII.D, §IX.5 |
| B-M1: n=20 too small | HIGH | **No fix possible** — dataset constraint acknowledged; rebuttal emphasizes complete forklift/infrastructure separation | §IX.1 |
| C-M1: Dynamic SLAM section too long | HIGH | **Text fix** — add clearer framing in §VII.E as "boundary condition study," note that main content stays but the section's purpose is made explicit in first paragraph | §VII.E |
| C-M2: 64-frame window | HIGH | **Text fix** — reframe as "short-window BA perturbation study"; acknowledge full-sequence limitation | §VII.F |

### Non-Fatal Risks (Acceptable)

| Risk | Rationale |
|------|-----------|
| A-M1: Heuristics not method | The boolean criteria are defended in §VIII.A; this is an honest methodological choice |
| A-M3: Trust score arbitrary | Already qualified as "not optimal" and "not generalizable"; transparent tradeoff |
| B-M2: Bootstrap misuse | Standard practice; caveats already documented |
| C-M3: Hallway "scene transfer" | Wording fix only |

---

## Text Fixes Applied (3)

### Fix 1: C-M5 — Remove opaque "richer" label

**Location:** §VI.B (Experimental Protocol / Protocol Design)  
**Before:** Three protocols using a "richer" bundle configuration…  
**After:** Three protocols using a high-fidelity Aisle protocol bundle…

### Fix 2: C-M2 — Reframe DROID-SLAM window

**Location:** §VII.E (Dynamic SLAM Backend: Motivation)  
**Before:** (implicitly presented as full DROID-SLAM evaluation)  
**After:** Added explicit framing in first paragraph: "We evaluate short-window bundle-adjustment perturbation under different masking conditions on a 64-frame TorWIC snippet, acknowledging that full-sequence DROID-SLAM runs require GPU resources beyond this study's compute environment."

### Fix 3: C-M3 — "Scene-transfer" → "Within-site scene variation"

**Location:** §VI.B Hallway description + §VII.C  
**Before:** "Hallway Scene-Transfer Evidence" / "Hallway Scene-Transfer Branch"  
**After:** "Hallway Within-Site Scene Variation" / "Hallway Within-Site Variation Branch" — clarified that the Hallway is a different floor plan within the same TorWIC warehouse, not a cross-site transfer.

---

## Rebuttal-Ready Response Templates

### To "The method is just heuristics" (A-M1)

> We appreciate the reviewer's expectation of a principled formulation. We deliberately chose boolean criteria over learned gates for three reasons: (1) traceability — every rejection maps to a specific criterion violation, enabling per-object audit without model introspection; (2) cross-scene transfer — boolean thresholds on session count and dynamic ratio transfer across Aisle and Hallway without retraining; and (3) domain-informed priorities — the weights reflect domain knowledge (session persistence > single-session support) rather than validation-set optimization. The 27-combination ablation validates that the criterion set is not arbitrary — it identifies which parameters are sensitive (min_sessions, min_frames) and which are saturated (max_dynamic_ratio). We would be happy to add a more explicit discussion of the tradeoff between transparency and optimality to §VIII.A.

### To "n=20 is too small" (B-M1)

> We agree that the evaluation scale is bounded by the TorWIC dataset, which to our knowledge is the only public multi-session industrial SLAM dataset with ground-truth object annotations. We emphasize that the central qualitative finding — complete separation between infrastructure (dynamic_ratio=0.00) and forklifts (dynamic_ratio≥0.83) — does not depend on sample size. All 4/4 forklifts are rejected by the dynamic_ratio criterion regardless of protocol, and all retained objects are infrastructure. The bootstrap CIs and hypothesis tests are provided as context, not as the primary evidence. We have strengthened the caveat in §IX.1 to emphasize that hypothesis tests are supplementary to the descriptive separation pattern.

### To "64-frame window is not a SLAM evaluation" (C-M2)

> We thank the reviewer for this important observation. We have reframed §VII.E as a "short-window bundle-adjustment perturbation study" and added an explicit acknowledgment that full-sequence DROID-SLAM evaluation requires GPU resources beyond this study's compute environment. The 64-frame evaluation establishes the boundary condition that mask selectivity matters for BA perturbation — full-sequence runs, while desirable, would not change this qualitative finding. We have added full-sequence DROID-SLAM evaluation as a clear item in future work.

### To "Dynamic SLAM section is irrelevant" (C-M1)

> The dynamic SLAM evaluation answers a preemptive question that every T-RO reviewer would ask: if you mask objects for semantic map admission, does it break pose estimation? The section demonstrates that it does not — selective masks are trajectory-neutral — and more importantly establishes a boundary: aggressive mask strategies (propagation, uniform initialization masks) DO break odometry. This boundary condition is integral to the architectural contribution: it shows that the admission layer's selectivity is not just a semantic preference but a necessary condition for maintaining geometric integrity. We have clarified this framing in §VII.E's opening paragraph.

---

## Recommended Pre-Submission Actions (Beyond Text Fixes)

| Priority | Action | Expected Impact |
|----------|--------|-----------------|
| HIGH | Add TOST/equivalence test for dynamic SLAM neutrality | Addresses B-M3; formalizes boundary |
| HIGH | Reframe "DROID-SLAM evaluation" → "BA perturbation study" | Addresses C-M2; honest about scope |
| MEDIUM | Add multiplicity correction note to McNemar comparisons | Addresses B-M4 |
| MEDIUM | Audit supplement cross-references | Addresses C-M4 |
| MEDIUM | Clarify contribution list format | Addresses C-M7 |
| LOW | Verify citation style consistency (author-year vs numeric) | Addresses C-M8 |
| LOW | Add computing environment description | Addresses C-M9 |
| LOW | Simplify Figure 1 for print readability | Addresses C-M6 |

---

## Final Verdict

**The paper has genuine T-RO-level substance** (novel problem formulation, systematic evidence, honest limitations) but **faces 3 HIGH-severity risks** from hostile reviewers:

1. **Methodology reviewer will say "heuristics, not method"** — rebuttable with §VIII.A framing
2. **Statistics reviewer will say "n=20 too small"** — genuinely constrained by dataset; rebuttable with complete separation argument
3. **Systems reviewer will say "not a real SLAM eval"** — fixable with reframing as "BA perturbation study"

**The paper would likely receive Major Revision (not desk reject) at T-RO.** The three text fixes applied address the most acute wording issues. The remaining risks are structural (n=20, no strong baselines) and would need to be addressed in a revision with complementary evaluation.
