# Advisor Handoff & Venue Decision Pack — Industrial Semantic SLAM

**Generated:** 2026-05-09 18:47+08
**Phase:** P152
**Status:** Ready for advisor review

---

## 1. One-Page Delivery Index

| Artifact | Path | Description |
|---|---|---|
| **EN Manuscript** | `paper/manuscript_en_thick.md` | 499 lines / 47 sections. Thick manuscript with full method + evidence. |
| **ZH Manuscript** | `paper/manuscript_zh_thick.md` | 497 lines / 47 sections. Bilingual mirror, structurally aligned. |
| **EN PDF** | `paper/export/manuscript_en_thick.pdf` | 643 KB. Compiled via markdown+weasyprint. |
| **ZH PDF** | `paper/export/manuscript_zh_thick.pdf` | 820 KB. CJK rendered with Noto Serif CJK SC. |
| **EN HTML** | `paper/export/manuscript_en_thick.html` | 61 KB. Browser-readable with KaTeX math. |
| **ZH HTML** | `paper/export/manuscript_zh_thick.html` | 51 KB. Browser-readable. |
| **Package Index v10** | `outputs/torwic_submission_ready_package_index_v10.md` | Full navigator: 44 bundles, 394 output files, 232 manifest entries. |
| **Submission Checklist** | `outputs/torwic_submission_readiness_checklist_v1.md` | 36-point audit across 5 dimensions. |
| **Final Audit (P151)** | `paper/export/final_audit_p151.json` | 85/88 checks pass (97%). Automated + reproducible. |
| **Evidence Data** | `paper/evidence/dynamic_slam_backend_metrics.json` | 12-config DROID-SLAM raw-vs-masked ATE/RPE metrics. |
| **Figures** | `paper/figures/` | 11 PNGs. Figs 1–10 mapped explicitly in captions. |
| **Build Script** | `paper/build_paper.py` | Reproducible markdown→HTML→PDF; `pip install markdown weasyprint`. |
| **Audit Script** | `paper/final_audit.py` | 88-dimension automated audit. Re-run after any manuscript change. |
| **Main Table** | `outputs/torwic_submission_ready_main_table_v2.md` | 4-protocol evidence ladder: 203/11/5 → 537/16/9. |
| **Appendix Table** | `outputs/torwic_submission_ready_appendix_table_closure_final_v1.md` | Rejection taxonomy + branch comparison. |
| **Closure Bundle** | `outputs/torwic_submission_ready_closure_bundle_v29.md` | Autonomous baseline 10-phase summary. |

### Quick-Start for Advisor

1. **Fast read**: `paper/export/manuscript_en_thick.pdf` (30+ pages, self-contained)
2. **Evidence at a glance**: §VII.D Tables 1–3 + §VII.F Tables 4–6
3. **Gaps & limitations**: §IX (7 items, all quantified)
4. **Reproducibility**: `paper/build_paper.py` + `paper/final_audit.py`

---

## 2. Venue Decision Matrix

No venue has been selected. The manuscript is venue-agnostic: all claims are evidence-grounded, all citations are formal IEEE-style, and the structure follows standard CS conference/journal conventions.

| Venue Type | Candidate | Fit Assessment | Page Budget | Timeline | Notes |
|---|---|---|---|---|---|
| **Robotics Conf.** | ICRA | Strong: systems focus, real-world evidence. | 6–8 pp. | Jan deadline, May conf. | Would need to trim §VII.E–F appendix material to supplemental. |
| | IROS | Good: SLAM + perception. | 6–8 pp. | Mar deadline, Oct conf. | Similar trimming needed. |
| | RSS | Strong: methodology-first, negative results valued. | 8 pp. | Jan deadline, Jul conf. | Best fit for negative-result framing. |
| **Vision Conf.** | CVPR | Moderate: pipeline paper, no novel vision module. | 8 pp. | Nov deadline, Jun conf. | Would need to emphasize methodological contribution. |
| | ECCV | Moderate. | 14 pp. | Mar deadline, Sep conf. | More space for full method description. |
| **Robotics Journal** | IEEE RA-L + ICRA | Good: short format + conference option. | 8 pp. | Rolling. | RA-L typically requires hardware validation. |
| | IEEE T-RO | Strong: mature evaluation, long-term SLAM survey context. | 14–20 pp. | Rolling. | Thick manuscript maps naturally to T-RO length. |
| | JFR | Good: field robotics, industrial application. | 20+ pp. | Rolling. | Industrial focus fits. |
| **SLAM-Specific** | IJRR | Strong: long-form, survey-contextualized. | 20+ pp. | Rolling. | May require additional hardware experiments. |

### Recommendation (Advisor Decision)

- **Short-term**: If timeline is urgent, consider RA-L + ICRA option (8pp, cut §VII.E–F to supplemental).
- **Long-term**: The thick manuscript maps naturally to T-RO (14–20pp) or IJRR (20+ pp). The current 499-line markdown corresponds to approximately 16–18 IEEE two-column pages.
- **Philosophical fit**: RSS values negative-result studies most highly; T-RO/IJRR value thorough evaluation.

---

## 3. Cover Letter Skeleton

```
[Date]
[Editor-in-Chief Name]
[Journal/Conference Name]

Dear [Editor-in-Chief / Program Chairs],

We submit "Semantic Segmentation-Assisted Long-Term Map Maintenance
for Industrial SLAM" for consideration at [VENUE NAME].

This paper addresses a persistent problem in long-term SLAM for
industrial environments: without an explicit admission-control policy,
open-vocabulary perception pipelines continuously admit dynamic-object
re-detections into the map, creating phantom objects that degrade
map quality over revisits. We propose a session-level maintenance
layer that operates between a black-box perception frontend
(Grounding DINO + SAM2 + OpenCLIP) and any SLAM backend. The layer
uses cross-session evidence aggregation — not geometric heuristics
— to distinguish stable infrastructure from mobile agents.

Key contributions:

1. A principled four-layer pipeline (observation → tracklet →
   map-object → revision) with transparent admission criteria
   (§V, min_sessions=2, min_frames=4, min_support=6,
   max_dynamic_ratio=0.2, min_label_purity=0.7).

2. An evidence ladder across four protocols (same-day 203/11/5,
   cross-day 240/10/5, cross-month 297/14/7, hallway 537/16/9),
   demonstrating consistent retention of stable infrastructure
   and rejection of forklift-like mobile agents (§VII.D, Tables 1–3).

3. A complete dynamic SLAM backend evaluation as a self-contained
   negative-result study: 10 DROID-SLAM configurations across
   masking strategies produce trajectory-neutral results
   (|ΔATE| < 0.1 mm, Table 6). We quantitatively trace this to a
   data constraint: forklifts in TorWIC warehouse aisles occupy
   at most 1.39% of the image frame, below DROID-SLAM's flow-
   consistency filtering threshold. Boundary condition: >5%
   frame coverage needed for observable trajectory effect (§VII.F).

4. Open-source reproducible build: the paper itself is generated
   from tracked markdown sources with an automated audit script
   (85/88 checks pass).

We believe this work provides a reproducible, evidence-grounded,
and honest contribution to long-term industrial SLAM — establishing
both what the proposed method can do (admission control for stable
objects) and the quantified conditions under which dynamic masking
does not help (forklift-to-frame ratio below threshold).

This manuscript has not been submitted elsewhere. All authors have
approved the submission.

Sincerely,
[Author Names]
```

---

## 4. Final Remaining Decisions for User / Advisor

| # | Decision | Current State | Options |
|---|---|---|---|
| D1 | **Target venue** | Not selected. Manuscript is venue-agnostic. | See Venue Decision Matrix §2. |
| D2 | **Page budget** | Thick manuscript ≈16–18 IEEE pages. | Trim to 8pp (conf) or expand to T-RO/IJRR format. |
| D3 | **§VII.E–F disposition** | Full 64-frame dynamic SLAM chapter in main text. | Keep in main (journal) or move to supplemental (conf). |
| D4 | **Fig. 3 inclusion** | Marked "optional — may be omitted per page budget." | Keep or drop based on venue page constraints. |
| D5 | **Chinese manuscript** | ZH mirror available. | Most venues do not require bilingual submission; keep as internal reference. |
| D6 | **Cover letter** | Skeleton provided. | Fill author list, add any venue-specific requirements. |
| D7 | **Author ordering** | Not specified. | Advisor + user to decide. |
| D8 | **Hardware validation** | Current evidence is TorWIC dataset only (pre-recorded). | RA-L/T-RO may request robot-mounted experiments — discuss with advisor. |
| D9 | **arXiv preprint** | Not posted. | Consider posting before/during review to establish priority. |
| D10 | **Code release** | Pipeline code in repo; not yet packaged as standalone release. | Package as `pip install` / Docker or release as companion repo. |
| D11 | **Acknowledgment formatting** | Not included. | Add funding sources, lab affiliation, thanks. |
| D12 | **POV-SLAM/TorWIC attribution** | Cited as [6] with GitHub link. | Confirm attribution format meets TorWIC license terms. |

---

## 5. Gap Status Summary (Final)

| Gap ID | Component | Status |
|---|---|---|
| GAP-001–003 | Grounding DINO/SAM2/OpenCLIP citations | ✅ RESOLVED (P150, [7]–[9]) |
| GAP-004–006 | arXiv links for [1]–[3] | DEFERRED — optional per venue |
| GAP-007 | Target venue formatting | DEFERRED — needs venue selection (D1) |
| GAP-008 | Figure paths | ✅ RESOLVED (P148) |
| GAP-009 | Package index | ✅ RESOLVED (P148, v10) |
| GAP-010 | Local PDF compile | ✅ RESOLVED (P149, weasyprint) |

**No substantive gaps remain.** All deferred items are venue-specific formatting or user-preference decisions.

---

## 6. Project Closure Summary

### What This Project Achieved

| Dimension | Result |
|---|---|
| **Reproducible experiment pipeline** | 4 protocols, 4-branch baseline comparison, admission criteria constant across all. |
| **Trusted stable-object evidence** | 537/16/9 Hallway protocol validates Aisle findings at broader scale. |
| **Paper Results/Discussion/Appendix** | §VII complete with Tables 1–6, Figs 1–10, evidence chain P135–P143. |
| **Final delivery package** | Manuscripts (EN+ZH), figures (11 PNGs), exports (HTML+PDF), build/audit scripts, package index. |
| **Negative-result contribution** | 10-config DROID-SLAM study establishes reproducible boundary conditions for dynamic masking. |

### What This Project Does NOT Claim

- This is not a new SLAM backend or perception model.
- The maintenance layer does not close loops or optimize poses.
- Dynamic masking does not improve trajectory ATE/RPE on available TorWIC data.
- The method has not been validated on live robot hardware.

---

*Generated by P152 advisor-handoff-and-venue-decision-pack. All content is data-derived; no claims exceed the evidence boundary established in P135–P151 audits.*
