# Round 1 Reviewer Critique — T-RO Submission

**Manuscript:** Session-Level Map Admission Control for Semantic-Segmentation-Assisted SLAM in Dynamic Industrial Environments  
**Target:** IEEE Transactions on Robotics, Regular Paper  
**Review date:** 2026-05-09  
**Reviewer stance:** Harsh T-RO/IJRR reviewer simulation (not adversarial — this is an honest pre-submission stress test)  
**Scope:** `main.tex` scaffold + `manuscript_en_thick.md` content + supplementary package + editor-facing docs

---

## 1. Top 10 Rejection Risks (Ordered by Severity)

### Risk #1 (CRITICAL): Content Not Integrated into LaTeX — Placeholder Stubs Everywhere

**Severity: REJECT (desk rejection risk if submitted as-is)**

The `main.tex` scaffold contains placeholder stubs for §IV Problem Formulation ("TBD: Mathematical formulation..."), all five Method subsections (§V.A–V.F), and §VI Experimental Protocol. These are not minor formatting gaps — they are the technical core of the paper. A T-RO AE seeing "TBD" in the Problem Formulation will desk-reject. The thick manuscript (`manuscript_en_thick.md`) contains full prose for these sections, but it has NOT been ported into `main.tex`.

**Evidence:** Grepping `main.tex` for "TBD", "PLACEHOLDER", and empty section bodies confirms §IV, §V.A–V.F, and §VI are stubs.

**Fix:** Port manuscript content from `manuscript_en_thick.md` into `main.tex` before ANY submission attempt. This is the single most critical action item. Not a reviewer comment — a submission-eligibility requirement.

### Risk #2 (HIGH): Method Is Boolean Criteria — Novelty Debate

**Severity: MAJOR REVISION to REJECT**

The core method (§V.E) is a conjunction of five boolean thresholds: `sessions ≥ 2 AND observations ≥ 6 AND label_purity ≥ 0.7 AND dynamic_ratio ≤ 0.2 AND frames ≥ 4`. A harsh reviewer will characterize this as "a hand-tuned rule with five thresholds" rather than a principled methodology. The trust score formula (§V.D) uses fixed weights (α=0.4, β=0.3, γ=0.5) described as "configurable, not optimized" — but if not optimized, where do these specific numbers come from? Why 0.4/0.3/0.5 instead of equal weights? The "not optimized" disclaimer does not protect against this question.

**The T-RO bar:** T-RO systems papers (cf. Campos et al. ORB-SLAM3, Yang & Scherer CubeSLAM) typically contribute both architectural and algorithmic novelty. Five boolean criteria + a linear score push the contribution closer to an "engineering rule" than a "methodological contribution." The burden is on the paper to articulate WHY this particular formulation is principled beyond "it works on TorWIC."

### Risk #3 (HIGH): Experimental Scale — Only 20 Candidate Clusters

**Severity: MAJOR REVISION**

The entire admission-control evaluation is performed on 20 candidate clusters (11 same-day + 10 cross-day + 14 cross-month + 16 Hallway, after combining overlapping clusters across protocols). Among these: 5 admitted, 15 rejected. This is a very small number of data points to support claims about "principled admission control." A single forklift cluster misclassified as infrastructure (or vice versa) would swing conclusions meaningfully. Statistical significance is not reported; no confidence intervals are provided.

Additionally, all evidence comes from one industrial site (TorWIC's warehouse). While the Hallway provides a "scene transfer" within this site, a reviewer will note that both Aisle and Hallway are the same warehouse — same lighting, same camera, same forklifts, same barriers. Scene transfer within one warehouse is weak generalization evidence.

### Risk #4 (HIGH): Dynamic SLAM as Negative Result — Page Budget Disproportionality

**Severity: MAJOR REVISION**

The dynamic SLAM negative-result study (§VII.E-F + supplementary S4-S5) occupies 7 main-body figure slots (Figs 4–10) and 8 supplementary figure slots (S2–S8). That is ~50% of the main-body figure budget and ~70% of the supplementary figure budget devoted to a negative result. The conclusion — "forklift is too small to affect DROID-SLAM" — could be stated in one paragraph with one figure. The 10-configuration sweep, the temporal/flow propagation stress tests, the concentrated-vs-uniform comparison, and the coverage-power gradient analysis are excessive for a negative result and make the paper look padded.

A T-RO reviewer will ask: "If dynamic masking doesn't matter in your setting, why is half your paper about dynamic masking?"

**Recommendation:** Retain the negative result in a compact form (1 paragraph + 1 summary table + 1 figure), move the 10-configuration sweep entirely to supplementary, and reclaim main-body space for method detail and discussion.

### Risk #5 (MEDIUM-HIGH): Hallway Protocol Is Incomplete — 8/10 Sessions

**Severity: MAJOR REVISION**

The Hallway protocol is advertised as "10 sessions" but only 8 are executed ("first 8 executed" / "80/80 frames"). This is a 20% missing-data rate on the secondary validation branch. The claim that this "demonstrates scene transfer" is weakened when the scene-transfer evidence is itself incomplete. A reviewer will ask: why are 2 sessions missing, and do those missing sessions contradict the current finding?

Additionally, the reports state "80/80 frames" — suggesting each session has exactly 10 frames, which is very sparse. A T-RO reviewer will question whether 10-frame sessions provide enough observation density for a "session-level map maintenance" claim.

### Risk #6 (MEDIUM): Bimodality Claim Could Be a Pipeline Artifact

**Severity: MAJOR REVISION**

The paper claims that `max_dynamic_ratio` insensitivity demonstrates "natural data bimodality" — infrastructure at dynamic_ratio=0.00, forklifts at ≥0.83, no intermediate values. But the `dynamic_ratio` is computed from the detector's `state` output (static / candidate / dynamic_agent), which is itself a classifier output. The bimodality may be an artifact of the detector's state classifier producing binary decisions rather than a property of the physical environment.

If the detector's state classifier assigns `dynamic_agent` to any object with moving appearance > threshold, and `static` otherwise, then the "bimodality" is trivially explained by the classifier's decision boundary, not by any property of the admission policy. The paper should discuss whether the dynamic_ratio distribution is genuinely bimodal in the physics or merely reflects the frontend's state-classification behavior.

### Risk #7 (MEDIUM): The "Auditability" Claim Is Not Tested

**Severity: MINOR to MAJOR REVISION**

The paper repeatedly claims the framework is "auditable" (Contributions #1, #8; Abstract; Discussion §VIII.C). But no experiment tests auditability — there is no inter-rater reliability study, no comparison of admission decisions against an oracle, no ablation that demonstrates per-component inspectability matters. "Auditability" is an architectural property, not an evaluated property. In a systems paper, architectural claims without systems-level evaluation are vulnerable.

### Risk #8 (MEDIUM): Missing Comparative Baselines

**Severity: MAJOR REVISION**

The baseline comparison (§VII.G.2) compares against B0 (naive all-admit) and B1 (purity/support heuristic). Both are straw-man baselines that no published SLAM system would actually use. Missing comparisons:

- **Standard SLAM map management:** How would RTAB-Map's memory management, ORB-SLAM3's multi-map fusion, or Kimera's mesh persistence handle the same 20 clusters? These are real systems with real map management. The paper should identify which existing systems would admit or reject forklifts under their native policies.
- **Confidence-based threshold:** Using actual NN confidence scores (if available from a rerun) rather than the label-purity proxy.
- **Learned classifier:** A simple logistic regression on the same five signals would establish whether the rule-based criteria outperform a learned equivalent — or whether learning adds nothing, which would actually strengthen the paper's "simple and interpretable" claim.

### Risk #9 (MEDIUM): Claim Drift Between Sections

**Severity: MINOR REVISION**

There is subtle claim drift between the abstract/introduction and the results/discussion:

| Section | Claim |
|---|---|
| Abstract | "an explicit, auditable, multi-layer map maintenance architecture" |
| Introduction (§I.C) | "We deliberately limit the contribution to stable-object retention, dynamic-contamination rejection" |
| Discussion (§VIII.A) | "Why Not Just Filter by Detection Confidence?" — framing the paper as solving a problem that standard SLAM can't |

The abstract implies the contribution is the architecture. The introduction limits it to a specific filtering task. The discussion reframes it as answering a question about detection confidence. These are three different scopes, and the inconsistency will confuse reviewers.

### Risk #10 (MEDIUM): Related Work Overlap with Existing Admission-Control Paradigms

**Severity: MINOR REVISION**

The related work (§III) positions the paper against semantic SLAM, dynamic SLAM, long-term mapping, and segmentation-assisted filtering. But it does not engage with the closest conceptual relatives: **map management policies** in topological SLAM, **landmark selection** in filter-based SLAM, and **outlier rejection** in structure-from-motion. These fields have decades of literature on "which observations to keep," and the paper should acknowledge that the admission-control question has been studied in adjacent communities, even if their solutions don't transfer directly.

---

## 2. Results Section Adequacy for Strong-Journal Submission

### 2.1 What Works

| Element | Adequacy | Notes |
|---|---|---|
| Multi-condition evidence ladder | STRONG | Three Aisle protocols + Hallway transfer is above RA-L/IROS expectation |
| Parameter ablation (27 combinations) | STRONG | Exceeds typical SLAM paper ablation depth |
| Baseline comparison (3-way) | ADEQUATE | Baselines are simple but the analysis of B1's failure is insightful |
| Per-category retention/rejection | STRONG | Forklift=0% universal rejection is the paper's strongest result |
| Negative-result dynamic SLAM | ADEQUATE | Honest and well-documented, but over-padded (see Risk #4) |
| Map-composition visualization | ADEQUATE | Before/after maps + decision space scatter are effective |
| Per-cluster evidence traceability | STRONG | Cluster-ID-level audit trail is genuinely uncommon and valuable |

### 2.2 What's Missing

| Gap | Severity | Fix |
|---|---|---|
| No statistical significance tests | HIGH | Add confidence intervals for admission rates; bootstrap p-values for B0/B1/B2 comparison |
| No per-frame observation quality metrics | MEDIUM | Report per-frame detection count, mask IoU distribution |
| No sensitivity to time gap | MEDIUM | Cross-day vs cross-month should show whether temporal gap matters for the same object — currently only reported at cluster level |
| No per-cluster dynamic_ratio histogram | LOW | Supplementary-only figure showing the actual histogram behind the "bimodality" claim |
| No Hallway protocol completion | MEDIUM | Execute sessions 9–10; or explain why 8/10 is sufficient |
| No comparison against published systems | HIGH | See Risk #8 — must name-check real SLAM backends' map policies |

### 2.3 Verdict

The evidence base is **above the ICRA/IROS bar** (multi-condition, ablation, baseline, per-category) but **below the T-RO submission-readiness bar** in its current state. The two gaps that most threaten T-RO acceptance: (1) no comparison against real published systems (Risk #8), and (2) missing statistical rigor on a 20-cluster dataset (Risk #3).

---

## 3. Figure/Table Placement: Main Body vs Supplementary

### 3.1 Current Allocation (Problematic)

| Location | Count | Figures |
|---|---|---|
| Main body | 12 | Figs 1–3 (overview) + Figs 4–10 (dynamic SLAM) + Figs 11,13 (admission defense) |
| Supplementary | 11 | S1 (lifecycle) + S2–S8 (dynamic SLAM) + S9–S11 (retention/rejection) |
| **Dynamic SLAM total** | **15** | 7 main + 8 supplementary |

### 3.2 Recommended Reallocation

**Move TO supplementary:**
| Figure | Reason |
|---|---|
| Figs 5–10 (6 dynamic SLAM diagnostics) | Negative-result detail. Retain only Fig 4 (summary) in main body |
| Fig 3 (Hallway composite) | Secondary protocol, not primary evidence |

**Move TO main body:**
| Figure | Reason |
|---|---|
| Fig S1 (object lifecycle, barrier vs forklift) | The single most compelling figure in the paper — makes the admission/rejection distinction visceral |
| Fig S11 (category × rejection reason heatmap) | Central to the per-category analysis (§VII.G.3) — stronger than the distribution bar chart |
| Decision space scatter (currently Fig 13) | Keep — this is the bimodality evidence |

**Net effect:** 12 main-body figures → 7 main-body figures (+1 lifecycle, +1 heatmap, −6 dynamic SLAM, −1 Hallway). This frees 5 figure slots for method diagrams, expanded discussion, or future additions.

### 3.3 Table Placement

| Table | Location | Notes |
|---|---|---|
| Evidence ladder summary (Table 1) | Main body | Essential |
| Baseline comparison (B0/B1/B2) | Main body | Essential |
| 10-config dynamic SLAM | Supplementary | Already in S4 |
| Per-cluster admission matrix | Supplementary | Already in S2 |
| Per-cluster rejection profiles | Supplementary | Already in S6 |
| Evidence file index | Supplementary | Already in S8 |

**Recommendation:** Current table placement is correct. No changes needed.

---

## 4. Claims Assessment: Too Strong, Too Weak, or Just Right?

### 4.1 Overstated Claims ⚠️

| Claim | Assessment | Why |
|---|---|---|
| "A principled session-level map admission control methodology" | **SLIGHTLY OVERSTATED** | "Principled" implies theoretical grounding. The method is rule-based with configurable thresholds. Replace with "systematic" or "evidence-backed." |
| "The trust score is intentionally simple and auditable" | **ADEQUATE** | The simplicity is honestly stated; "auditable" needs evaluation backing (Risk #7). |
| "The admission criteria exploit data bimodality" | **OVERSTATED** | The bimodality may be a pipeline artifact (Risk #6). Reframe: "The admission criteria benefit from a natural separation in the data, which we verify through parameter ablation." |
| "Zero phantom risk" | **ADEQUATE** | Correct on the 20-cluster dataset. Add CI: "0/4 forklifts admitted (95% CI: 0–60% under Wilson interval)" |
| "The framework is backend-agnostic" | **ADEQUATE** | Correct — only depends on detection output format. |

### 4.2 Understated Claims 💡

| Claim | Assessment | Why |
|---|---|---|
| "Cluster-ID-level traceability" | **UNDERSTATED** | This is genuinely distinguishing — very few SLAM papers provide per-object audit trails. The paper should foreground this more prominently. |
| "Negative result as boundary condition" | **ADEQUATE** | Well-framed. The coverage-power analysis (§VII.F) is the strongest part of the dynamic SLAM section — keep this, trim the rest. |
| "Why B1 (purity/support) still fails" | **UNDERSTATED** | The insight that forklifts have high purity AND high support is the paper's most important observation. It should appear in the abstract. |
| "Hallway transfer without protocol adaptation" | **ADEQUATE** | Correct framing. But needs completion (Risk #5). |

### 4.3 Missing Claims (Should Add)

| Gap | Recommended Claim |
|---|---|
| No quantitative comparison against published map policies | "Under [System X]'s map management policy, Y/20 clusters would be admitted (Z forklifts), compared to our 5/20 (0 forklifts)" |
| No statement about what "good enough" admission looks like | "An admission policy with >90% recall on infrastructure and 0% false-admission on dynamic agents, even at the cost of conservative infrastructure rejection" |
| No generalizability caveat | "The current evidence is sufficient to demonstrate the architecture's viability on TorWIC; we do not claim the specific thresholds transfer without validation to other environments" |

---

## 5. Three Reviewer Archetypes and Rebuttal Directions

### Reviewer A: The Systems Architect (Semantic SLAM / Object-Level Mapping)

**Likely background:** CubeSLAM, Kimera, OpenScene, or ConceptFusion author. Values architectural clarity and system integration.

**Likely critiques:**
1. "This is a filter, not a system. What makes this a 'layer' rather than a post-processing step?"
2. "Why boolean criteria instead of a learned policy? Your ablation shows the data is separable — why not train a classifier?"
3. "How does this integrate with a full SLAM pipeline? Show it working with ORB-SLAM3 or Kimera, not just the observation layer in isolation."

**Rebuttal direction:**
- The maintenance layer is architecturally distinct from the perception frontend and the SLAM backend — it can be inserted between any detection pipeline and any map representation. The supplementary provides interface specifications.
- Boolean criteria were chosen deliberately because (a) they are auditable per-object (every rejection has a traceable reason), (b) they transfer across scenes without retraining (Hallway evidence), and (c) the ablation shows learned weights would not improve separation on this dataset.
- Integration with a full SLAM system is deferred to future work (§IX). The current contribution is the admission-control layer itself, validated at the object level.

### Reviewer B: The Dynamic SLAM Expert

**Likely background:** DynaSLAM, DynaSLAM II, Co-Fusion, or FlowFusion author. Values rigorous dynamic/static evaluation.

**Likely critiques:**
1. "Your dynamic SLAM evaluation is a negative result — why is it in the paper at all?"
2. "You only tested DROID-SLAM. DSO, ORB-SLAM3, or VINS-Fusion might be more sensitive to dynamic content."
3. "The 𝚫ATE values (0.05 mm) are far below evo's measurement noise floor. You're reporting noise as data."
4. "1.39% coverage is the maximum — but what about the frame where the forklift is closest? Was the forklift actually occluding tracked features or just occupying empty image area?"

**Rebuttal direction:**
- The negative result is scientifically valuable because it provides a boundary condition: at <2% dynamic coverage, DROID-SLAM is robust. This is actionable for future researchers — they know to look for >5% coverage data, not rerun DROID-SLAM on warehouse aisles.
- Single-backend limitation is acknowledged (§IX). Adding ORB-SLAM3 is a future-work item.
- The 𝚫ATE is indeed at the noise floor — this IS the finding. We are not claiming subtle differences; we are reporting that all configurations are indistinguishable from raw.
- Per-frame coverage analysis (supplementary S5.2) shows the maximum single-frame coverage is 1.39%. The forklift's position in the frame is visualized (supplementary S3)—it occupies a small region in the lower half of the image, partially overlapping textured aisle floor.

### Reviewer C: The Evaluation Methodologist

**Likely background:** SLAM benchmark author, evaluation metrics researcher. Values statistical rigor, reproducibility, and honest reporting.

**Likely critiques:**
1. "20 candidate clusters is too few for any statistical claim. You need at least 50+ clusters or a clear power analysis."
2. "The admission criteria thresholds (min_sessions=2, min_frames=4, etc.) appear to be post-hoc chosen from the ablation. Were these selected before seeing the data?"
3. "No comparison against an information-theoretic baseline (e.g., 'keep the top-K by mutual information with map quality'). Your baselines are too weak."
4. "The 'trust score' uses weights (0.4, 0.3, 0.5) that are stated as 'not optimized.' This is a red flag — either justify the weights from domain knowledge or remove the trust score entirely."

**Rebuttal direction:**
- We acknowledge the small-N limitation. The contribution is architectural, not statistical. The 20 clusters represent all object-level entities detected across 35 sessions — this is the population, not a sample. The replication question is about transfer to other sites, not sampling error within this site.
- The thresholds were fixed BEFORE the ablation sweep. The ablation is a verification, not a search. Protocol §VI.C states: "All four protocols use the same admission criteria with the same thresholds."
- Information-theoretic baselines require a downstream task metric (e.g., navigation success), which we explicitly defer (§IX). The B1 baseline is deliberately simple because the paper's core claim is that purity/support ALONE cannot reject forklifts — this is validated.
- The trust score weights are domain-informed: session persistence (α=0.4) is weighted higher than observation support (β=0.3) because cross-session evidence is the strongest signal in the data (§VIII.B). Dynamic penalty (γ=0.5) is highest because dynamic contamination is the most severe failure mode. These are plausible defaults, not optimized estimates, and the paper is explicit about this. If a reviewer prefers, the trust score can be removed — the boolean criteria are the primary admission gate.

---

## 6. Round 2 Executable Modification List

### Blocking (Must Fix Before Submission)

| # | Action | Owner | Effort |
|---|---|---|---|
| R2.1 | **Integrate manuscript content into main.tex.** Port all sections from `manuscript_en_thick.md` into `main.tex` placeholders. Remove all "TBD" and "PLACEHOLDER" markers. | Author | 4–8 hours |
| R2.2 | **Complete Hallway protocol.** Execute sessions 9–10 or document why 8/10 is sufficient with missing-session audit. | Author | 2–4 hours |
| R2.3 | **Add statistical reporting.** Bootstrap CIs for admission rates. χ² or Fisher's exact test for B0/B1/B2 forklift-admission comparison. | Author | 2–3 hours |
| R2.4 | **Resolve bimodality-or-artifact question.** Add analysis of dynamic_ratio distribution per detection state classifier output. If the frontend produces binary states, document this as a limitation. | Author | 1–2 hours |

### High Priority (Strongly Recommended Before Submission)

| # | Action | Owner | Effort |
|---|---|---|---|
| R2.5 | **Move 6 dynamic SLAM figures to supplementary.** Keep only Fig 4 (summary) + Table 6 (evidence chain) in main body. Free 5 figure slots. | Author | 1 hour |
| R2.6 | **Promote object lifecycle figure (S1) to main body.** It is the paper's strongest visualization. | Author | 0.5 hours |
| R2.7 | **Add "Comparison with Published Systems" subsection.** Identify which published SLAM systems' map policies would admit or reject TorWIC forklifts (even qualitatively). | Author | 3–5 hours |
| R2.8 | **Harmonize claim scope across sections.** Ensure abstract, introduction, and discussion use consistent framing. Remove "principled methodology" → "systematic, evidence-backed admission control." | Author | 1–2 hours |
| R2.9 | **Remove or justify trust score weights.** Either provide domain-informed justification for (α=0.4, β=0.3, γ=0.5) or remove the trust score and rely solely on boolean criteria. | Author | 0.5 hours |
| R2.10 | **Reorganize Results §VII.G into §VII.A–C sequence.** Currently the evidence ladder (§VII.A) is separated from its defense (§VII.G) by 5 unrelated subsections. Reorder for narrative flow. | Author | 2–3 hours |

### Medium Priority (Improves Review Outcome)

| # | Action | Owner | Effort |
|---|---|---|---|
| R2.11 | **Add Related Work paragraph on landmark selection/outlier rejection.** Connect to SLAM filter literature (EKF-SLAM landmark management, PTAM map-point culling, ORB-SLAM map-point policies). | Author | 2–3 hours |
| R2.12 | **Add per-frame observation quality appendix.** Detection count distribution, mask IoU statistics, label confidence histogram (if confidence data available). | Author | 2–4 hours |
| R2.13 | **Evaluate auditability.** Simple experiment: can an independent evaluator reproduce admission decisions from the per-cluster profiles? Report yes/no with step-by-step evidence. | Author | 2–3 hours |
| R2.14 | **Add time-gap sensitivity analysis.** For cross-day and cross-month protocols, report per-object stability vs temporal separation. | Author | 2–3 hours |
| R2.15 | **Update Limitations §IX in main.tex.** Current 7-point list needs expansion: add "small-N evaluation," "bimodality may depend on frontend," "no comparison with published map policies." | Author | 1 hour |

### Low Priority (Acceptable to Defer to Revision)

| # | Action | Owner | Effort |
|---|---|---|---|
| R2.16 | **Learned baseline.** Train logistic regression on the five signals, compare to boolean criteria. Even a null result (classifier = boolean) would strengthen the paper. | Author | 4–6 hours |
| R2.17 | **Multi-backend dynamic SLAM.** Test ORB-SLAM3 on the same 64-frame window. | Author | 6–10 hours |
| R2.18 | **External dataset validation.** Identify any second industrial SLAM dataset (even without annotations) and report qualitative transfer. | Author | Unknown |

---

## 7. Overall Pre-Submission Readiness Assessment

| Dimension | Score | Notes |
|---|---|---|
| **Novelty** | 6/10 | The architecture is genuinely novel; the method (boolean criteria) may face pushback |
| **Technical depth** | 5/10 | LaTeX has placeholder stubs; method is simple; Trust score not justified |
| **Experimental thoroughness** | 7/10 | Multi-condition + ablation + baseline + per-category is above average; 20-cluster scale is below T-RO norm |
| **Clarity and organization** | 6/10 | Thick manuscript is well-structured but LaTeX integration incomplete; results section ordering suboptimal |
| **Honesty and limitations** | 9/10 | Exceptionally honest — negative result, boundary conditions, missing confidence scores all disclosed |
| **T-RO fit** | 7/10 | Systems/methodology category fits; evidence package would benefit from published-system comparison |
| **Submission readiness** | 4/10 | **Cannot submit as-is** — LaTeX content integration (R2.1) is blocking |

### Bottom Line

**Do not submit in current state.** The paper has a strong evidence base and an honest framing, but three items are submission-blocking: (1) LaTeX content not integrated, (2) Hallway protocol incomplete, (3) missing statistical rigor. R2.1–R2.4 must be completed before submission. R2.5–R2.10 are strongly recommended and would significantly improve the review outcome. The dynamic SLAM section, while scientifically honest, is over-padded and should be drastically compressed — a T-RO reviewer will not appreciate 15 figures devoted to a negative result.

**Estimated time to submission-ready:** 2–3 weeks of focused author work after content integration.

---

*This review is a pre-submission stress test, not an adversarial attack. All weaknesses identified are real vulnerabilities that a T-RO reviewer could exploit. Addressing R2.1–R2.10 before submission would substantially improve the paper's chances at T-RO.*
