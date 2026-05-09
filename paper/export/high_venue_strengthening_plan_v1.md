# High-Venue Strengthening Plan — Industrial Semantic SLAM

**Generated:** 2026-05-09 19:35+08
**Phase:** P153
**Input:** Current P152 submission package (`paper/manuscript_en_thick.md`, 498 lines)
**Constraint:** existing-data-only; no new downloads, no new experiments; no ATE/RPE improvement claims

---

## 1. Reviewer-Perspective SWOT Matrix

### What Reviewers Will Like (Strengths)

| # | Strength | Evidence Location | Reviewer Appeal |
|---|---|---|---|
| S1 | **Real industrial data** | TorWIC warehouse (Jun/Jul/Aug 2023), not simulation | High — real-world validation is rare in SLAM papers |
| S2 | **Multi-scale protocol ladder** | Same-day (203/11/5) → cross-day (240/10/5) → cross-month (297/14/7) → hallway (537/16/9) | High — temporal scaling is rarely shown |
| S3 | **Transparent, reproducible admission criteria** | min_sessions=2, min_frames=4, min_support=6, max_dynamic_ratio=0.2, min_label_purity=0.7; constant across all protocols | High — few SLAM papers reveal decision thresholds |
| S4 | **Honest negative-result chapter** | §VII.E–F, Tables 4–6, quantified boundary condition (>5% coverage needed) | Medium–High — scientifically honest; some reviewers resist negative results |
| S5 | **Well-documented limitations** | §IX, 7 items, all quantified | Medium — shows awareness, but may be seen as defensive |
| S6 | **Bilingual + reproducible build** | EN/ZH manuscripts, `build_paper.py`, `final_audit.py` | Low–Medium — polish, not science |

### What Reviewers Will Attack (Weaknesses)

| # | Weakness | Severity | Attack Vector | Mitigation Path |
|---|---|---|---|---|
| W1 | **No novel algorithm** | 🔴 Critical | "This is an engineering pipeline, not a research contribution." | Reframe as *principled methodology* with *quantified design space*. |
| W2 | **All perception components are off-the-shelf** | 🟠 High | "Using Grounding DINO+SAM2+OpenCLIP is not novel." | Emphasize that the maintenance layer is *perception-agnostic*; the contribution is the admission policy, not the perception. |
| W3 | **No comparison against alternative map maintenance methods** | 🔴 Critical | "How does this compare to [X]? You didn't test against any baseline." | **Must resolve before high-venue submission.** Add naive-all-admit baseline and confidence-threshold baseline (P155). |
| W4 | **Dynamic SLAM chapter is entirely negative** | 🟠 High | "You ran 10 configurations and none improved trajectory. Why is this a contribution?" | Frame as *reproducible boundary condition* rather than failure. Consider moving most to appendix for conference venues. |
| W5 | **Single dataset — no cross-dataset generalization** | 🟡 Medium | "TorWIC is one warehouse. Does this work elsewhere?" | Honest limitation already in §IX. Add explicit generalization discussion. |
| W6 | **No runtime/efficiency analysis** | 🟡 Medium | "How fast is this? Can it run online?" | Add per-frame timing if data exists; otherwise add explicit runtime limitation. |
| W7 | **Maintenance layer is intermediate — no loop closure** | 🟡 Medium | "This is not a complete SLAM system." | Already stated in §IX.1. Consider adding end-to-end integration demo. |
| W8 | **Limited contribution boundary** | 🟠 High | "What exactly did you invent? The admission criteria thresholds?" | Need to articulate the *design methodology* as contribution: the process of deriving admission criteria from session-level evidence, not the thresholds themselves. |
| W9 | **No ablation on admission criteria** | 🔴 Critical | "Why min_sessions=2? What if you use 1 or 3? Sensitivity analysis missing." | **Must resolve.** Add parameter sensitivity study using existing data (P154). |
| W10 | **No qualitative map visualization** | 🟡 Medium | "Show me the map with and without your method." | Generate before/after map figures from existing pipeline outputs (P156). |

---

## 2. Venue-Specific Deep Dive

### T-RO (IEEE Trans. Robotics) — ⭐ Top Recommendation

| Factor | Assessment |
|---|---|
| **Length fit** | ✅ 498-line thick manuscript ≈16–18 IEEE pages; T-RO allows 14–20pp |
| **Contribution type** | ✅ Methodology paper with thorough evaluation fits T-RO expectations |
| **Negative results** | ✅ T-RO reviewers value honest negative results more than conferences |
| **Risks** | W1 (no algorithm), W3 (no baseline comparison), W9 (no ablation) must be resolved |
| **Required before submission** | Baseline/ablation study (P154–P155), map visualization (P156), W3/W9 resolution |
| **Success probability** | 40–55% after P154–P156 strengthening |

### IJRR (Int. J. Robotics Research) — ⭐ Strong Alternative

| Factor | Assessment |
|---|---|
| **Length fit** | ✅ 498 lines expandable to IJRR length |
| **Contribution type** | ✅ Survey-like context + thorough evaluation |
| **Risks** | Same as T-RO; IJRR is more selective |
| **Required before submission** | Same as T-RO; may also want cross-dataset or hardware validation |
| **Success probability** | 30–45% |

### RSS (Robotics: Science and Systems) — ⭐ Best Conference Fit

| Factor | Assessment |
|---|---|
| **Length fit** | ⚠️ 8pp requires heavy trimming; §VII.E–F to appendix |
| **Contribution type** | ✅ RSS values methodology + negative results |
| **Risks** | 8pp is very tight for a pipeline paper; may not fit admission criteria + evidence ladder + dynamic SLAM |
| **Required before submission** | Trim to 8pp, baseline comparison, ablation |
| **Success probability** | 35–50% |

### ICRA / IROS — ⚠️ Lower Fit

| Factor | Assessment |
|---|---|
| **Length fit** | ❌ 6–8pp very tight |
| **Contribution type** | ⚠️ ICRA/IROS prefer novel algorithms or hardware results |
| **Risks** | Pipeline/methodology papers struggle at ICRA/IROS; negative results not well received |
| **Required before submission** | Would need to reframe as novel admission-control algorithm (difficult) |
| **Success probability** | 20–35% |

### Verdict

| Priority | Venue | Rationale |
|---|---|---|
| **1st choice** | T-RO | Thick manuscript length fits naturally; thorough evaluation valued; revision cycles allow strengthening |
| **2nd choice** | IJRR | Similar fit; higher bar but stronger venue |
| **3rd choice** | RSS | Best conference fit if page budget demands conference |
| **Fallback** | RA-L + ICRA option | Fast turnaround, but requires significant trimming and reframing |

---

## 3. Baseline & Ablation Gap Inventory

### Priority 1: Must Resolve Before High-Venue Submission

| ID | Gap | What's Missing | Data Needed | Phases |
|---|---|---|---|---|
| **A1** | **Admission criteria ablation** | Parameter sensitivity: how do retained/rejected counts change when varying min_sessions (1/2/3), min_frames (2/4/6), max_dynamic_ratio (0.1/0.2/0.3)? | Existing pipeline outputs — re-run filtering with different thresholds on same observation data | P154 |
| **A2** | **Naive-all-admit baseline** | What happens if every detection is admitted to the map? How many phantom objects appear? | Existing observation data — disable admission filter, count resulting map objects | P155 |
| **A3** | **Confidence-threshold baseline** | Compare session-level evidence aggregation vs per-frame confidence thresholding (e.g., only admit if OpenCLIP confidence > 0.8) | Existing observation data with confidence scores | P155 |
| **A4** | **Rejection reason quantification** | Current Table 3 has rejection taxonomy. Need per-reason counts and per-category breakdown. | Existing pipeline rejection logs | P157 |

### Priority 2: High Impact, Lower Effort

| ID | Gap | Data Needed | Phases |
|---|---|---|---|
| **A5** | **Map-quality visualization** | Generate before/after map-view figures showing which objects are admitted/rejected | Existing pipeline map-object data | P156 |
| **A6** | **Per-category retention analysis** | Barrier vs work table vs rack vs forklift retention rates across protocols | Existing pipeline category labels | P157 |
| **A7** | **Object lifecycle diagram** | Show a single object through observation→tracklet→map-object→revision over multiple sessions | Existing tracklet/map-object data | P156 |

### Priority 3: Nice to Have

| ID | Gap | Notes |
|---|---|---|
| **A8** | Protocol contribution analysis | Does cross-month add information beyond same-day? Quantify marginal value of each protocol. |
| **A9** | Runtime/timing | Per-frame processing time for detection, segmentation, reranking, and admission decision |
| **A10** | Detection failure analysis | How often does Grounding DINO miss objects? False positive rate? |

---

## 4. Figure & Table Plan for High-Venue Manuscript

### New Figures (Can Generate from Existing Data)

| Fig # | Content | Type | Data Source | Priority |
|---|---|---|---|---|
| **F-N1** | Admission criteria sensitivity heatmap | 3×3 grid: min_sessions (1,2,3) × min_frames (2,4,6), color = retained object count | Re-run admission filter with parameter sweep on existing observations | 🔴 Must have |
| **F-N2** | Before/after map comparison | Side-by-side: all detections admitted vs admission-controlled map, color-coded by retention status | Existing map-object data + re-run without filter | 🟠 High |
| **F-N3** | Object lifecycle timeline | Single barrier object tracked across 3 sessions (Jun 15 → Jun 23 → Jul 2) showing tracklet formation, merge, and retention | Existing tracklet data | 🟠 High |
| **F-N4** | Rejection reason pie/bar chart | Per-reason breakdown: dynamic_contamination, low_session_support, label_fragmentation, low_support | Existing rejection logs (Table 3 data) | 🟡 Medium |
| **F-N5** | Per-category retention heatmap | Barrier/table/rack/forklift × same-day/cross-day/cross-month/hallway, color = retention rate | Aggregate existing pipeline outputs by category | 🟡 Medium |

### New Tables

| Table # | Content | Data Source | Priority |
|---|---|---|---|
| **T-N1** | Baseline comparison: Naive vs Confidence vs Richer | Counts: total admitted, phantom rate, stable retention, precision/recall-like metrics | Re-run with naive and confidence baselines | 🔴 Must have |
| **T-N2** | Ablation: parameter sweep results | min_sessions × min_frames × max_dynamic_ratio → retained/rejected counts | Parameter sweep on existing data | 🔴 Must have |
| **T-N3** | Per-rejection-reason statistics | Count + percentage for each rejection reason across all protocols | Existing rejection logs | 🟡 Medium |

---

## 5. Executable Phase Backlog (P154–P158)

| Phase | Goal | Bounded Steps | Estimated Duration | Dependencies |
|---|---|---|---|---|
| **P154** | Admission criteria ablation | 1) Parameter sweep: vary min_sessions (1/2/3), min_frames (2/4/6), max_dynamic_ratio (0.1/0.2/0.3). 2) Generate sensitivity heatmap (F-N1). 3) Produce ablation table (T-N2). 4) Update manuscript §VII.D with ablation results. | 4–6 steps | None |
| **P155** | Baseline comparison study | 1) Implement naive-all-admit baseline (disable filter). 2) Implement confidence-threshold baseline (>0.8). 3) Compare counts: richer vs naive vs confidence (T-N1). 4) Update manuscript §VII.C–D with baseline comparison. | 4–5 steps | None |
| **P156** | Map visualization & lifecycle | 1) Generate before/after map figure (F-N2). 2) Generate object lifecycle diagram (F-N3). 3) Integrate into manuscript §V or §VII. | 3–4 steps | None |
| **P157** | Per-category & rejection analysis | 1) Compute per-category retention rates (F-N5). 2) Quantify rejection reasons per protocol (F-N4, T-N3). 3) Update manuscript §VII.D. | 3–4 steps | None |
| **P158** | High-venue manuscript rewrite | 1) Reframe contribution as principled methodology. 2) Integrate all P154–P157 results. 3) Strengthen §I–III (contribution statement, problem formalization). 4) Rebuild exports + audit. 5) Produce venue-specific submission package. | 5–8 steps | P154–P157 |

### Phase Dependencies

```
P154 (ablation) ──┐
                  ├──→ P158 (rewrite)
P155 (baselines) ─┤
                  │
P156 (maps) ──────┤
                  │
P157 (categories)─┘
```

All P154–P157 are parallelizable — they use different subsets of existing data.

---

## 6. Contribution Reframing Strategy

### Current Weakness

The current manuscript positions itself as "we built a pipeline." Reviewers will ask: *What is the research contribution?*

### Proposed Reframing

**From:** "A semantic segmentation-assisted long-term map maintenance pipeline for industrial SLAM"

**To:** "Principled Session-Level Map Admission Control for Long-Term Industrial SLAM: An Evidence-Ladder Methodology"

**Core claim shift:**

| Before | After |
|---|---|
| We built a pipeline that filters dynamic objects | We propose a *methodology* for deriving map admission criteria from cross-session evidence, and validate it with a 4-protocol evidence ladder |
| Grounding DINO + SAM2 + OpenCLIP are our frontend | The admission layer is *perception-agnostic*; any detection pipeline can be plugged in |
| We ran 10 DROID-SLAM configs and none improved trajectory | We established *reproducible boundary conditions* for when dynamic masking matters (and when it doesn't) — a contribution to experimental methodology |

### Contribution Statement (Draft for High-Venue Rewrite)

> This paper contributes a principled methodology for session-level map admission control in long-term industrial SLAM. Rather than proposing a new detection or SLAM algorithm, we (1) formalize the map admission problem as a cross-session evidence aggregation task, (2) derive transparent, reproducible admission criteria from session-level statistics, (3) validate the methodology with a 4-protocol evidence ladder spanning same-day, cross-day, and cross-month warehouse revisits, and (4) establish quantified boundary conditions for when dynamic-object masking affects trajectory accuracy — demonstrating that at typical industrial aisle camera distances, dynamic objects are too small (<2% frame coverage) to measurably perturb modern SLAM backends. The contribution is the *methodology* and its *empirical validation*, not any single algorithmic component.

---

## 7. Risk Assessment Summary

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Ablation shows criteria are insensitive (small parameter range) | Medium | Low | Even null ablation results are publishable with honest reporting |
| Naive baseline outperforms richer on some metrics | Low | Medium | Would indicate the maintenance layer is unnecessary — need to check carefully |
| Cannot generate map visualization from existing data | Medium | Medium | Fall back to abstract pipeline diagram |
| After P154–P158, manuscript is too long for T-RO | Medium | Medium | Trim dynamic SLAM chapter to appendix; move per-category to supplemental |
| Venue rejects due to lack of hardware experiment | Medium | High | Frame as "methodology paper with real-world data validation" not "system paper" |

---

*Generated by P153 high-venue-strengthening-plan. All recommendations are based on existing data and current manuscript content. No new experiments have been executed. The P154–P158 backlog represents the minimum credible strengthening path for T-RO/IJRR submission.*
