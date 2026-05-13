# Dynamic Industrial Semantic-Segmentation-Assisted SLAM:
# Object-Centric Map Maintenance and Bounded Dynamic-Mask Frontend Evidence

**Thick Manuscript Draft v2 - English**
*Updated: 2026-05-13 | Thick draft is the active manuscript target | Existing evidence only*

---

## Abstract

Long-term visual SLAM in industrial environments faces two related but distinct sources of dynamic-scene risk. First, semantic maps can be contaminated by objects that are real and repeatedly detected, such as forklifts or carts, but should not become durable static landmarks. Second, dynamic regions can in principle degrade visual odometry if frontend features are drawn from moving or transient objects. This manuscript treats the first problem as the primary contribution and the second as a bounded frontend smoke line. We formulate **session-level map admission control** as an explicit object-maintenance layer between open-vocabulary RGB-D perception and durable semantic map update. The layer converts segmentation outputs into observation, tracklet, map-object, and revision records, then admits objects only when multi-session presence, observation support, label consistency, static dominance, and frame coverage are all satisfied. On the TorWIC industrial dataset from POV-SLAM [6], the object-maintenance evidence ladder retains stable infrastructure across same-day Aisle (203 observations / 11 clusters / 5 retained), cross-day Aisle (240/10/5), cross-month Aisle (297/14/7), and a separate Hallway transfer branch (537/16/9). Forklift-like clusters are consistently rejected as dynamic contamination, with dynamic-like rejection shares from 50.0% to 71.4%.

We additionally consolidate the later dynamic-mask frontend evidence. A compact UNet trained on a P217 semantic-mask dataset (237 rows, 156/51/30 split, zero frame overlap, positive pixel rate 0.374176) reaches validation IoU/F1 0.671304/0.803329 and test IoU/F1 0.578580/0.733038 (P218), with held-out precision/recall/F1/IoU 0.556007/0.789669/0.604636/0.443210 (P219). Ground-truth dynamic-region ORB keypoints drop from 4795 to 2192 (54.2857% reduction, P220). P225-P228 build a 60-frame Oct. 12, 2022 Aisle_CW raw-vs-masked sequence and a confidence/coverage-gated hard black mask module. P228 is neutral on the original 480-539 window (raw/masked APE 0.088496/0.084705, RPE 0.076145/0.076224, ORB gated-region keypoints 8969 -> 5073), but P233-P234 show that this hard-boundary gate is mixed across windows and can create boundary ORB features: 120-179 gives 5927 -> 4820 while 840-899 reverses to 601 -> 1901, and a failure sweep finds no stable post-processing-only setting (best 127 -> 1197). P235 therefore tests a soft boundary/mean-fill feather candidate, `meanfill035_feather5_thr060_cap012_min256`, which removes the 840-899 ORB reversal in bounded smoke (127 -> 0, total keypoint delta 0) with neutral DROID deltas (16-frame dAPE -0.000036/dRPE +0.000007; 60-frame dAPE +0.000158/dRPE -0.000003) and backtests to 480-539 (1382 -> 188) and 120-179 (215 -> 20). These results support a bounded frontend module candidate and a failure diagnosis, not a full benchmark, navigation result, independent-label result, or learned map-admission conclusion. P195 remains BLOCKED.

## Index Terms

SLAM, semantic segmentation, dynamic object filtering, object-level mapping, map maintenance, industrial robotics, open-vocabulary perception, dynamic masking, long-term autonomy

---

## I. Introduction

### I.A. Motivation

Simultaneous Localization and Mapping (SLAM) has matured from a geometric estimation problem into a long-term autonomy problem: maps must remain useful across repeated visits, changing lighting, layout edits, and moving industrial equipment [1]. In warehouses and logistics spaces, stable infrastructure such as barriers, work tables, racks, and pillars coexists with forklifts, carts, and human-operated equipment. A camera revisiting the same aisle may see the same class of forklift many times, sometimes in similar locations, but this does not make the forklift a stable map landmark.

Modern open-vocabulary perception makes this problem sharper. Grounding DINO [7], SAM2 [8], and OpenCLIP [9] can produce dense object candidates from RGB-D frames with little task-specific training. Without a separate map-admission policy, however, a semantic SLAM pipeline may treat "detected object" as equivalent to "map-worthy object." That shortcut creates forklift-shaped phantoms in the persistent map.

### I.B. The Admission-Control Gap

Dynamic SLAM methods such as DynaSLAM [2] protect camera tracking and reconstruction by detecting and masking dynamic regions. Object-level SLAM and open-vocabulary mapping methods [3]-[5] attach semantic identity to mapped entities. These directions are complementary, but neither directly answers the durable-map question: after an object has been detected, segmented, and geometrically localized, should it be admitted to the long-term semantic map?

The core claim of this manuscript is that semantic map admission deserves its own auditable layer. Detection confidence, label purity, and geometric support are not enough. Forklifts can be detected confidently and repeatedly, yet still be inadmissible. A stable barrier may have lower per-frame confidence, yet become valuable through multi-session persistence.

### I.C. Scope and Contributions

This thick draft is organized around two evidence lines:

1. **Primary contribution: object-centric map maintenance.** We define observation, tracklet, map-object, and revision records; introduce a transparent trust score; and use boolean admission criteria to retain stable infrastructure while rejecting dynamic contamination.
2. **Secondary evidence line: bounded dynamic-mask frontend.** We document P217-P235 segmentation and raw-vs-masked SLAM smoke evidence as a constrained frontend module story. It verifies that learned, gated, and soft-boundary masks can be generated and evaluated, and it now records a hard-boundary failure mode plus a candidate soft-boundary fix. It does not yet support broad dynamic-SLAM or navigation claims.

The manuscript deliberately avoids claiming lifelong SLAM, dense dynamic reconstruction, independent dynamic segmentation labels, downstream navigation effects, or learned persistent-map admission. The contribution is an auditable bridge from segmentation-assisted open-vocabulary perception to revisioned long-term object-map maintenance, with bounded frontend mask evidence as supporting context.

---

## II. Related Work

### II.A. Semantic SLAM and Object-Level Mapping

Cadena et al. [1] frame the evolution of SLAM from geometric estimation toward robust perception and long-term autonomy. CubeSLAM [3] demonstrates that object-level representations can support monocular SLAM by fitting cuboids to detected objects. OpenScene [4] and ConceptFusion [5] show that open-vocabulary scene representations can connect language-conditioned semantics with 3D mapping.

These works establish the feasibility of semantic and object-level mapping. Our focus is narrower and complementary: given object candidates from a perception frontend, determine which candidates deserve durable map slots. The question is not whether the object is detectable; it is whether it is persistent, stable, and semantically admissible.

### II.B. Dynamic SLAM and Dynamic-Object Suppression

DynaSLAM [2] and related dynamic-SLAM systems suppress moving objects to protect tracking, mapping, and loop closure. Their typical evaluation target is trajectory or reconstruction quality under dynamic-scene disturbance. This paper uses that literature as motivation but changes the level of decision. We reject dynamic-like objects from the semantic map even when they are correctly detected and geometrically localized.

The dynamic-mask frontend section also connects to this literature, but conservatively. The P225-P235 DROID-SLAM and ORB runs are bounded smoke tests on short Aisle_CW windows. They demonstrate executable raw-vs-masked plumbing, expose a hard black mask boundary failure mode, and motivate a soft-boundary candidate; they do not establish general trajectory effects.

### II.C. Long-Term Map Maintenance and Stable Landmark Reuse

Long-term SLAM requires deciding what to retain, update, forget, or revise [1]. POV-SLAM [6] provides object-aware SLAM benchmarks and the TorWIC industrial data used here. Our maintenance layer uses TorWIC revisits to aggregate session-level evidence and make explicit map-admission decisions. Unlike map pruning based only on memory, geometry, or information gain, the proposed admission layer records why each semantic object is retained or rejected.

### II.D. Segmentation-Assisted and Open-Vocabulary Frontends

Grounding DINO [7], SAM2 [8], and OpenCLIP [9] are used as black-box observation generators for the object-maintenance line. The dynamic-mask line adds a small supervised segmentation route trained from semantic masks. These models provide object candidates and dynamic-region masks; they are not themselves claimed as the paper contribution.

---

## III. Problem Formulation

Let a SLAM session \(S_k\) contain RGB-D frames \(F_{k,1}, \ldots, F_{k,N_k}\). A perception frontend returns candidate object observations \(o_{k,i}^{(j)}\), each with a frame id, session id, box, mask, canonical label, confidence, and state tag when available.

The **map-admission problem** is to construct a durable object map \(\mathcal{M} = \{e_1,\ldots,e_M\}\) such that each admitted entity is:

| Requirement | Meaning for industrial semantic SLAM |
|---|---|
| Stability | The object persists physically across revisits rather than appearing as a transient visit. |
| Consistency | Its label and spatial support remain coherent enough to serve as a semantic landmark. |
| Static dominance | Dynamic agents and mobile equipment are rejected from the persistent static map. |
| Auditability | Every retain/reject decision can be traced to observations, sessions, and criteria. |

This formulation differs from standard detection-to-map insertion. A detected forklift may be a correct perception result and a poor map entity. The proposed layer therefore inserts an explicit maintenance process between perception and durable map update:

`RGB-D frames -> object observations -> session tracklets -> cross-session map objects -> revisioned map update`

The dynamic-mask frontend problem is separate. There, the question is whether learned or gated dynamic masks can suppress dynamic-region visual features and be evaluated against raw inputs in a SLAM backend. The current evidence treats this as a frontend smoke and diagnostic line, not as proof of improved long-horizon SLAM.

---

## IV. System Overview

The system has two cooperating but claim-separated paths.

### IV.A. Object-Maintenance Path

The object-maintenance path processes open-vocabulary object observations into revisioned map entities. It is responsible for stable infrastructure retention, dynamic contamination rejection, and per-object provenance. It is the primary paper contribution.

### IV.B. Dynamic-Mask Frontend Path

The dynamic-mask frontend path trains or applies a dynamic-region mask generator, post-processes the predicted mask, applies masked RGB inputs or feature-region analysis, and reports bounded raw-vs-masked evidence. This path currently supports a cautious story: learned masks can suppress ORB keypoints in predicted dynamic regions, hard black gating has an observed boundary-feature failure mode, and a soft boundary/mean-fill feather candidate fixes that regression window in bounded smoke while DROID-SLAM trajectory deltas remain neutral. It does not yet admit learned objects to the persistent map and does not unblock P195, which remains BLOCKED.

### IV.C. Evidence Separation

The two paths should not be merged into one overclaim. Object-maintenance results evaluate map admission. Dynamic-mask results evaluate frontend masking behavior and bounded backend execution. A future system could connect them, but this draft keeps the evidence boundaries explicit.

---

## V. Object-Centric Maintenance

### V.A. Open-Vocabulary Object Observation Extraction

For each RGB-D frame, the observation frontend produces object instances:

1. Grounding DINO [7] proposes boxes from industrial text prompts such as barrier, forklift, work table, warehouse rack, cart, pallet, and pillar.
2. SAM2 [8] generates instance masks from the proposed boxes.
3. OpenCLIP [9] reranks or resolves labels by comparing object crops against the target category vocabulary.
4. Each candidate becomes an `ObjectObservation` with frame id, session id, box, mask polygon, canonical label, confidence, timestamp, and state metadata.

The perception models are treated as replaceable components. The contribution begins when observations are aggregated, scored, and admitted or rejected.

### V.B. Session-Level Tracklets

Within a session, observations with compatible label and spatial support are grouped into tracklets. A tracklet records:

| Field | Purpose |
|---|---|
| Session id and temporal extent | Identify where and when the object was observed. |
| Observation count and frame count | Measure support and viewpoint diversity. |
| Label histogram | Preserve pre-canonicalization ambiguity. |
| State histogram | Separate static, candidate, and dynamic-agent evidence. |
| Dynamic ratio | Fraction of observations tagged as `dynamic_agent`. |

Tracklets are the unit of within-session evidence. They are not durable map objects until cross-session evidence is sufficient.

### V.C. Cross-Session MapObjects

Tracklets from different sessions are matched by canonical label consistency and spatial overlap, using a spatial IoU threshold of 0.1 in the current implementation. A `MapObject` aggregates session support, total observations, total tracklets, dominant label, label purity, dominant state, spatial stability, and per-session provenance.

This record is intentionally verbose. Reviewers and maintainers can inspect why a cluster exists, which frames support it, and which criterion failed if it is rejected.

### V.D. Stability and Dynamicity Scoring

Each map object receives an auxiliary trust score:

\[
\tau(O) = \alpha s_{\text{session}}(O) + \beta s_{\text{support}}(O) - \gamma s_{\text{dynamic}}(O)
\]

where \(s_{\text{session}}\) normalizes session count, \(s_{\text{support}}\) normalizes observation support, and \(s_{\text{dynamic}}\) is the object dynamic ratio. The current weights are \(\alpha=0.4\), \(\beta=0.3\), and \(\gamma=0.5\). The score is not an optimized estimator; it is a compact diagnostic that exposes the same intuition as the boolean gate.

### V.E. Map Admission Criteria

A candidate is admitted only if all criteria pass:

| Criterion | Condition | Rationale |
|---|---:|---|
| Multi-session presence | sessions >= 2 | Single-session objects may be transient. |
| Minimum support | observations >= 6 | Low-support objects are unreliable. |
| Label consistency | label purity >= 0.70 | Mixed labels indicate detector ambiguity. |
| Static dominance | dynamic ratio <= 0.20 | Mobile agents should not enter the static map. |
| Minimum frames | frames >= 4 | Objects seen from too few frames lack spatial support. |

Objects that fail are not silently discarded. They are recorded with rejection reasons such as `dynamic_contamination`, `single_session_or_low_session_support`, `label_fragmentation`, and `low_support`.

### V.F. Revisioned Map Updates

When a new session arrives, each tracklet either confirms an existing map object, contributes to a new candidate, or is rejected. The map is revisioned rather than rebuilt:

| Outcome | Meaning |
|---|---|
| Confirm | A tracklet matches an admitted object and updates counters/statistics. |
| Add | A candidate accumulates enough evidence and passes all criteria. |
| Reject | A candidate fails one or more criteria and is stored with reasons. |

This design is lightweight compared with full lifelong SLAM backends, but it provides the missing semantic admission-control layer.

---

## VI. Dynamic-Mask Frontend

### VI.A. Dataset and Compact Network Evidence (P217-P220)

The dynamic-mask branch begins with a P217 semantic-mask dataset:

| Evidence | Value |
|---|---:|
| Rows | 237 |
| Split | 156 train / 51 validation / 30 test |
| Frame overlap | 0 across splits |
| Positive pixel rate | 0.374176 |

P218 trains a compact UNet-style dynamic-mask model on these semantic masks:

| Split | IoU | F1 |
|---|---:|---:|
| Validation | 0.671304 | 0.803329 |
| Test | 0.578580 | 0.733038 |

P219 reports held-out precision/recall/F1/IoU as 0.556007/0.789669/0.604636/0.443210. P220 checks downstream feature relevance: ORB keypoints inside ground-truth dynamic regions drop from 4795 to 2192, a 54.2857% reduction. These facts support the feasibility of a learned dynamic-mask frontend, but the labels are derived from semantic-mask evidence and should not be described as independent dynamic segmentation ground truth.

### VI.B. P225 Learned-Mask Sequence

P225 packages a 60-frame learned-mask sequence from the Oct. 12, 2022 Aisle_CW run, source indices 480-539. The original P218 checkpoint was unavailable, so the sequence uses a bounded retrained SmallUNet from the P217 semantic masks. The artifact is trajectory-ready input only. It should not be described as a final model checkpoint recovery or a trajectory claim.

### VI.C. P227 DROID Baseline Reproduction

P227 evaluates the P225 learned-mask package with DROID-SLAM [10]. The 60-frame raw/masked APE is 0.088504/0.084529, and raw/masked RPE is 0.076145/0.076226. ORB keypoints in the predicted dynamic region drop from 21030 to 18617. The status is neutral: the trajectory smoke reproduces, but the result is not an improvement claim.

### VI.D. P228-P235 Confidence/Coverage Gate and Soft-Boundary Candidate

P228 adds a small post-network gate:

| Parameter | Value |
|---|---:|
| Probability threshold | 0.50 |
| Dilation | 1 px |
| Minimum connected component | 128 px |
| Maximum coverage | 0.22 |
| Target coverage | 0.18 |
| Mean coverage on 60 frames | 14.127053% |

The original 480-539 60-frame raw/masked APE is 0.088496/0.084705, and raw/masked RPE is 0.076145/0.076224. ORB keypoints in the gated predicted region drop from 8969 to 5073. Compared with P227, P228 is trajectory-neutral and provides the original story seed for the dynamic-mask frontend.

P233 extends the same hard black gate to two non-overlapping Aisle_CW windows. The result is mixed rather than supportive across windows: 120-179 remains neutral and reduces gated-region ORB keypoints from 5927 to 4820, while 840-899 is neutral in trajectory but reverses the ORB proxy from 601 to 1901. P234 sweeps threshold, coverage, component area, and dilation on the 840-899 failure window. No tested post-processing-only hard gate produces both an ORB proxy decrease and neutral DROID evidence; even the best proxy variant remains 127 -> 1197. The diagnosis is that hard black mask boundaries can create ORB corners, so coverage/threshold tuning alone is not a stable fix.

P235 tests a soft boundary/mean-fill feather frontend over the same probability maps. The selected candidate is `meanfill035_feather5_thr060_cap012_min256`: mean-fill with feather sigma 5, probability threshold 0.60, max/target coverage 0.12/0.10, and minimum component area 256 px. On the first regression window 840-899 it changes ORB predicted-region keypoints from 127 to 0 with total keypoint delta 0. Its DROID deltas remain neutral in bounded gates: 16-frame dAPE -0.000036 and dRPE +0.000007; 60-frame dAPE +0.000158 and dRPE -0.000003. Backtests are also ORB-positive and trajectory-neutral in 16-frame smoke: 480-539 changes 1382 -> 188, and 120-179 changes 215 -> 20.

The correct interpretation is narrow: hard black confidence/coverage gating has a documented boundary-feature failure mode, and the P235 soft-boundary candidate fixes the observed regression window in bounded smoke. It is not yet a full dynamic-SLAM benchmark, navigation gain, independent-label validation, or learned map-admission result.

---

## VII. Experimental Protocol

### VII.A. Object-Maintenance Protocols

The object-maintenance evidence uses TorWIC industrial RGB-D revisits from the POV-SLAM release [6]. All object-maintenance protocols use the same criteria: min_sessions=2, min_frames=4, min_support=6, max_dynamic_ratio=0.2, min_label_purity=0.7. No protocol-specific tuning is performed.

| Protocol | Sessions | Observations | Candidate Clusters | Retained MapObjects | Role |
|---|---:|---:|---:|---:|---|
| Same-day Aisle | 3 sessions from 2022-06-15 | 203 | 11 | 5 | Primary ladder start |
| Cross-day Aisle | 2022-06-15 + 2022-06-23 | 240 | 10 | 5 | 8-day revisit |
| Cross-month Aisle | June + Oct. 2022 | 297 | 14 | 7 | 4-month revisit |
| Hallway | first 8 executed sessions | 537 | 16 | 9 | Secondary scene transfer |

The Aisle ladder is the main evidence sequence. Hallway is retained as a separate broader-validation branch rather than merged into a single aggregate score.

### VII.B. Dynamic-Mask Protocols

The dynamic-mask line uses two protocol families:

| Phase range | Protocol | Claim status |
|---|---|---|
| P135-P143 | 64-frame dynamic-mask backend diagnostics on available TorWIC Aisle windows | Negative-result boundary: available forklift masks occupy too little image area to affect trajectory. |
| P217-P220 | Compact learned dynamic-mask dataset/model/ORB sanity | Feasibility evidence for semantic-mask-supervised dynamic masking. |
| P225-P228 | 60-frame Oct. 12, 2022 Aisle_CW learned-mask and hard confidence/coverage-gated DROID smoke | Original bounded frontend story seed. |
| P233-P235 | Multi-window hard-gate validation, failure sweep, and soft-boundary candidate | Mixed hard-gate evidence plus bounded candidate fix; not a full benchmark. |

P225-P235 are included only as bounded frontend evidence, separate from the object-maintenance contribution.

---

## VIII. Results

### VIII.A. Primary Aisle Evidence Ladder

| Protocol | Observations | Clusters | Retained | Main Retained Categories | Main Rejection Pattern |
|---|---:|---:|---:|---|---|
| Same-day Aisle | 203 | 11 | 5 | 2 work tables, 2 racks, 1 barrier | 3 forklift-like dynamic, 3 single-session |
| Cross-day Aisle | 240 | 10 | 5 | Same stable categories | 3 forklift-like dynamic, 2 single-session |
| Cross-month Aisle | 297 | 14 | 7 | Additional barriers/racks reach support | 5 forklift-like dynamic, 2 single-session |

The ladder shows that longer revisits increase the opportunity for stable infrastructure to accumulate support, while forklift-like objects remain rejected because their dominant state remains dynamic. The cross-month row adds two retained objects, illustrating the value of longer observation windows for map completeness.

### VIII.B. Stable Subset Composition

| Category | Same-day | Cross-day | Cross-month | Hallway |
|---|---:|---:|---:|---:|
| Barrier | 1 | 1 | 3 | 1 |
| Work table | 2 | 2 | 2 | 3 |
| Warehouse rack | 2 | 2 | 2 | 4 |
| Cart | 0 | 0 | 0 | 1 |
| Total retained | 5 | 5 | 7 | 9 |
| Forklift-like rejected | 3/6 | 3/5 | 5/7 | 5/7 |

Barriers, work tables, and racks dominate the retained map. The Hallway cart is retained because it satisfies the static-dominance and multi-session criteria; the system does not reject the label "cart" by category alone.

### VIII.C. Rejection Profile

| Rejection Reason | Count | Interpretation |
|---|---:|---|
| dynamic_contamination | 16 | Forklift-like clusters detected consistently but dominated by dynamic-agent state. |
| single_session_or_low_session_support | 13 | Insufficient revisit evidence for durable admission. |
| label_fragmentation | 3 | Mixed labels indicate detector ambiguity. |
| low_support | 2 | Too few observations for reliable map insertion. |

Dynamic-like rejection shares are 50.0% for Same-day Aisle, 60.0% for Cross-day Aisle, 71.4% for Cross-month Aisle, and 71.4% for Hallway. The important point is not simply that forklifts are removed; it is that they are removed with explicit, auditable reasons while stable infrastructure is retained.

### VIII.D. Admission Criteria Defense (P154-P157)

The admission policy is checked against ablations, baselines, and category-level profiles.

| Test | Finding |
|---|---|
| Parameter ablation (P154) | min_sessions and min_frames are sensitive filters; max_dynamic_ratio is saturated by data bimodality because infrastructure has dynamic_ratio=0.00 and forklifts are >=0.83. |
| Baseline comparison (P155) | Naive-all-admit keeps 20 clusters and 4 forklifts (20.0% phantom risk). Purity/support heuristic keeps 19 clusters and still keeps 4 forklifts (21.1% phantom risk). Full policy keeps 5 clusters and 0 forklifts. |
| Map-composition visualization (P156) | Before/after map and lifecycle figures make the admission decision visually inspectable. |
| Per-category analysis (P157) | Forklift retention is 0/4; infrastructure retention is selective: yellow barriers 40%, work tables 50%, warehouse racks 33%. |

The P155 B1 result is a useful warning: label purity and support alone cannot reject forklifts because forklifts can be consistently detected and supported. Static dominance and session evidence are necessary.

### VIII.E. Dynamic-Mask Frontend Results (P217-P235)

| Evidence | Main Result | Conservative Interpretation |
|---|---|---|
| P217 dataset | 237 rows, 156/51/30 split, zero frame overlap, positive pixel rate 0.374176 | Clean split for semantic-mask-supervised dynamic-mask training. |
| P218 compact UNet | val IoU/F1 0.671304/0.803329; test IoU/F1 0.578580/0.733038 | Feasible compact frontend, not independent GT proof. |
| P219 held-out | precision/recall/F1/IoU 0.556007/0.789669/0.604636/0.443210 | Recall-oriented behavior with moderate precision. |
| P220 ORB GT-region proxy | 4795 -> 2192 keypoints, 54.2857% reduction | Dynamic-region feature suppression is plausible. |
| P225 sequence | 60 frames, Oct. 12 2022 Aisle_CW indices 480-539; bounded retrained SmallUNet | Trajectory-ready input only. |
| P227 baseline | APE 0.088504 -> 0.084529; RPE 0.076145 -> 0.076226; ORB predicted-region 21030 -> 18617 | Neutral DROID baseline reproduction. |
| P228 hard gated module | APE 0.088496 -> 0.084705; RPE 0.076145 -> 0.076224; ORB gated-region 8969 -> 5073; mean coverage 14.127053% | Original story seed; lower gated-region ORB proxy, trajectory-neutral on 480-539. |
| P233 multi-window hard gate | 120-179 ORB 5927 -> 4820; 840-899 ORB 601 -> 1901 | Mixed result; do not claim multi-window support for hard black gating. |
| P234 hard-gate failure sweep | 840-899 best tested hard/post-processing variant still 127 -> 1197 | No stable post-processing-only hard gate found; boundary keypoint creation is the failure diagnosis. |
| P235 soft-boundary candidate | `meanfill035_feather5_thr060_cap012_min256`; 840-899 ORB 127 -> 0, total delta 0; DROID 16f dAPE -0.000036/dRPE +0.000007; DROID 60f dAPE +0.000158/dRPE -0.000003; backtests 480-539 ORB 1382 -> 188 and 120-179 ORB 215 -> 20 | Candidate soft-boundary frontend fixes the regression window in bounded smoke; no full benchmark or navigation claim. |

The dynamic-mask result should be phrased as follows: P228 provided the first viable hard-gated story seed, P233-P234 exposed a hard black boundary failure mode, and P235 provides a bounded soft-boundary candidate that removes the observed ORB regression while keeping DROID smoke neutral.

---

## IX. Failure and Boundary Analysis

### IX.A. Why Earlier Dynamic-SLAM Runs Were Trajectory-Neutral

The P135-P143 diagnostic chain shows that available TorWIC forklift masks are too small in the tested Aisle windows to measurably affect DROID-SLAM trajectory accuracy. In the 64-frame chain, forklift coverage remains below 1.39% per frame, and all raw-vs-masked configurations remain below meaningful trajectory-effect thresholds. DROID-SLAM's internal flow-consistency filtering likely suppresses many small dynamic outliers already.

This is a negative result, not a pipeline failure. It defines a boundary: trajectory-improvement claims require data where dynamic objects occupy a larger image fraction, plausibly above 5%, or an evaluation target other than short-window APE/RPE.

### IX.B. P225-P235 Boundary

P225-P235 improve the frontend story but do not erase the boundary:

| Boundary | Status |
|---|---|
| Broad dynamic-SLAM evaluation | Not claimed. |
| Navigation or planning effects | Not claimed. |
| Independent dynamic segmentation ground truth | Not claimed. |
| Learned persistent-map admission | Not claimed. |
| P195 | Still BLOCKED. |
| 60-frame DROID smoke | Executable and trajectory-neutral. |
| ORB predicted/gated-region suppression | Supported as a proxy, with a documented hard-boundary failure mode and a P235 candidate fix. |

The correct claim is a bounded frontend smoke: learned, hard-gated, and soft-boundary masks can be generated for short industrial windows, evaluated through DROID-SLAM, and used to diagnose ORB feature behavior in predicted dynamic regions. The hard black gate should not be promoted as multi-window support; the P235 soft-boundary candidate should be treated as a candidate module pending more windows and independent labels.

### IX.C. Object-Maintenance Failure Modes

The object-maintenance layer is intentionally conservative. False negatives can occur when a stable object appears in only one session or too few frames. Label fragmentation can reject a real object if open-vocabulary labels are inconsistent. Spatial-IoU association may fail under strong viewpoint changes or object relocation. These are acceptable first-draft limitations because rejected candidates remain auditable and can be revisited when more evidence arrives.

---

## X. Discussion

### X.A. Why Not Confidence-Only Admission?

Confidence-only admission confuses detector certainty with map worthiness. A forklift can be confidently detected and still be a poor static landmark. The P155 purity/support baseline demonstrates this failure mode: it admits all 4 forklift clusters. The full policy needs dynamic ratio and multi-session criteria to separate stable infrastructure from mobile agents.

### X.B. Why Keep Object Maintenance and Dynamic Masking Separate?

Object maintenance and dynamic masking operate at different levels. Map admission decides which semantic entities persist in a durable map. Dynamic masking decides which pixels or features should influence frontend/backend estimation. A future integrated system may use learned dynamic masks as one signal in map admission, but the current evidence does not justify that integration claim.

### X.C. Lightweight Design Trade-Off

The maintenance layer is simple: thresholded criteria, interpretable counters, and revision records. That simplicity makes the method easy to audit and reproduce, but it also limits robustness under severe viewpoint change, partial observation, or category ambiguity. A learned association or admission policy could improve recall, but it would need the same or better auditability to be acceptable for long-term map maintenance.

### X.D. Aisle and Hallway Roles

The Aisle ladder is the main protocol because it gives same-day, cross-day, and cross-month structure. Hallway is a separate transfer branch. Keeping them separate avoids hiding scene-specific behavior behind a single aggregate number.

---

## XI. Limitations

1. **Not a complete lifelong SLAM backend.** The object-maintenance layer does not perform loop closure, pose optimization, map compression, or full lifelong map management.
2. **No downstream task evaluation.** The evidence does not measure navigation success, relocalization improvement, planning quality, or task completion.
3. **Rule-based association can fail.** Spatial-IoU and label matching are transparent but may be brittle under major viewpoint shifts, occlusion, and object relocation.
4. **Open-vocabulary perception remains a dependency.** Grounding DINO [7], SAM2 [8], and OpenCLIP [9] are black-box components whose errors propagate into observation records.
5. **Dynamic-mask supervision is not independent GT.** P217-P220 use semantic-mask-supervised dynamic labels; these support a frontend route but not independent dynamic segmentation validation.
6. **P225-P235 are bounded smoke tests.** The Oct. 12, 2022 Aisle_CW evidence uses short constrained frontend checks. P233-P234 show that hard black gating can fail through boundary keypoint creation, while P235 is only a candidate soft-boundary fix.
7. **P195 remains BLOCKED.** The current work does not solve learned persistent-map admission.
8. **Venue formatting is deferred.** Reference punctuation, repository placement, and final citation style should be finalized after target venue selection.

---

## XII. Conclusion

This manuscript presents a thick, paper-shaped account of dynamic industrial semantic-segmentation-assisted SLAM centered on object-centric map maintenance. The primary contribution is a session-level admission-control layer that turns open-vocabulary RGB-D observations into auditable map-object decisions. On TorWIC, the evidence ladder retains stable infrastructure across same-day, cross-day, cross-month, and Hallway protocols while consistently rejecting forklift-like dynamic contamination.

The manuscript also integrates the newer P217-P235 dynamic-mask frontend evidence. Compact learned masks, a 60-frame learned-mask package, DROID-SLAM raw-vs-masked reproduction, the P228 confidence/coverage gate, the P233-P234 hard-boundary failure diagnosis, and the P235 soft-boundary candidate provide a bounded frontend story: hard black gating can reduce ORB counts on the original window but can also create boundary keypoints on a regression window, while mean-fill feathering removes that observed regression in bounded smoke. This strengthens the paper as a dynamic-scene SLAM manuscript without crossing the evidence boundary into unsupported broad-evaluation, navigation, independent-GT, or learned map-admission claims.

The resulting claim is conservative but useful: semantic map maintenance should be an explicit, auditable layer between perception and long-term maps, and dynamic-mask frontends can be evaluated as bounded supporting modules until stronger independent labels and larger dynamic-scene evidence are available.

---

## References

[1] C. Cadena, L. Carlone, H. Carrillo, Y. Latif, D. Scaramuzza, J. Neira, I. Reid, and J. J. Leonard, "Past, present, and future of simultaneous localization and mapping: Toward the robust-perception age," *IEEE Trans. Robot.*, vol. 32, no. 6, pp. 1309-1332, 2016. DOI: 10.1109/TRO.2016.2624754.

[2] B. Bescos, J. M. Facil, J. Civera, and J. Neira, "DynaSLAM: Tracking, mapping, and inpainting in dynamic scenes," *IEEE Robot. Autom. Lett.*, vol. 3, no. 4, pp. 4076-4083, 2018. DOI: 10.1109/LRA.2018.2860039.

[3] S. Yang and S. Scherer, "CubeSLAM: Monocular 3-D object SLAM," *IEEE Trans. Robot.*, vol. 35, no. 4, pp. 925-938, 2019. DOI: 10.1109/TRO.2019.2909168.

[4] S. Peng, K. Genova, C. Jiang, A. Tagliasacchi, M. Pollefeys, and T. Funkhouser, "OpenScene: 3D scene understanding with open vocabularies," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, 2023, pp. 815-824. DOI: 10.1109/CVPR52729.2023.00085.

[5] K. M. Jatavallabhula, A. Kuwajerwala, Q. Gu, M. Omama, T. Chen, S. Li, G. Iyer, S. Saryazdi, N. Keetha, A. Tewari, J. B. Tenenbaum, C. M. de Melo, M. Krishna, L. Paull, F. Shkurti, and A. Torralba, "ConceptFusion: Open-set multimodal 3D mapping," in *Proc. Robot.: Sci. Syst. (RSS)*, 2023. DOI: 10.15607/RSS.2023.XIX.066.

[6] D. Barath, B. Bescos, D. Mishkin, D. Rozumnyi, and J. Matas, "POV-SLAM: Probabilistic object-aware SLAM with semantic mapping benchmarks," in *Proc. Robot.: Sci. Syst. (RSS)*, 2023. DOI: 10.15607/RSS.2023.XIX.069. TorWICDataset repository: github.com/dbarath/POV-SLAM.

[7] S. Liu, Z. Zeng, T. Ren, F. Li, H. Zhang, J. Yang, Q. Jiang, C. Li, J. Yang, H. Su, J. Zhu, and L. Zhang, "Grounding DINO: Marrying DINO with grounded pre-training for open-set object detection," in *Proc. Eur. Conf. Comput. Vis. (ECCV)*, 2024. arXiv: 2303.05499.

[8] N. Ravi, V. Gabeur, Y.-T. Hu, R. Hu, C. Ryali, T. Ma, H. Khedr, R. Radle, C. Rolland, L. Gustafson, E. Mintun, J. Pan, K. V. Alwala, N. Carion, C.-Y. Wu, R. Girshick, P. Dollar, and C. Feichtenhofer, "SAM 2: Segment anything in images and videos," arXiv:2408.00714, 2024.

[9] M. Cherti, R. Beaumont, R. Wightman, M. Wortsman, G. Ilharco, C. Gordon, C. Schuhmann, L. Schmidt, and J. Jitsev, "Reproducible scaling laws for contrastive language-image learning," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, 2023, pp. 2818-2829. arXiv: 2212.07143.

[10] Z. Teed and J. Deng, "DROID-SLAM: Deep visual SLAM for monocular, stereo, and RGB-D cameras," in *Proc. Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 34, 2021. arXiv: 2108.10869.

**Software.** M. Grupp, "evo: Python package for the evaluation of odometry and SLAM," 2017. [Online]. Available: https://github.com/MichaelGrupp/evo

---

## Table Captions and Evidence Notes

**Table 1. Object-maintenance protocol ladder.** Same-day Aisle (203/11/5), Cross-day Aisle (240/10/5), Cross-month Aisle (297/14/7), and Hallway transfer (537/16/9).

**Table 2. Admission criteria.** Multi-session presence, minimum support, label consistency, static dominance, and minimum frames.

**Table 3. Rejection taxonomy.** dynamic_contamination 16, single_session_or_low_session_support 13, label_fragmentation 3, low_support 2.

**Table 4. Admission-defense summary.** P154 ablation, P155 baseline comparison, P156 visualization, and P157 per-category retention/rejection.

**Table 5. Dynamic-mask frontend evidence.** P217-P235 dataset, compact model, ORB proxy, learned-mask sequence, DROID baseline, hard confidence/coverage gate, multi-window failure evidence, and soft-boundary candidate.

**Table 6. P225-P235 bounded DROID smoke.** P227 learned-mask baseline, P228 confidence/coverage-gated module, P233-P234 hard-gate failure evidence, and P235 soft-boundary candidate. Report as neutral trajectory evidence with ORB proxy diagnostics, not a navigation or full-benchmark claim.

## Figure Captions

**Fig. 1.** Semantic-segmentation-assisted SLAM maintenance pipeline. [File: `paper/figures/torwic_paper_result_overview.png`]

**Fig. 2.** Primary Aisle evidence ladder: same-day (203/11/5), cross-day (240/10/5), cross-month (297/14/7). [File: `paper/figures/torwic_real_session_overlays.png`]

**Fig. 3.** Map-admission selectivity across retained and rejected objects. [File: `paper/figures/torwic_hallway_composite.png`]

**Fig. 4.** Bounded DROID-SLAM 64-frame raw-vs-masked backend diagnostic. [File: `paper/figures/torwic_dynamic_slam_backend_p134.png`]

**Fig. 5.** Dynamic-mask coverage diagnostic for existing semantic frontend masks. [File: `paper/figures/torwic_dynamic_mask_coverage_p135.png`]

**Fig. 6.** Temporal-mask propagation stress test. [File: `paper/figures/torwic_dynamic_mask_temporal_stress_p136.png`]

**Fig. 7.** Optical-flow mask propagation stress test. [File: `paper/figures/torwic_dynamic_mask_flow_stress_p137.png`]

**Fig. 8.** First-eight real semantic mask backend diagnostic. [File: `paper/figures/torwic_dynamic_mask_first8_real_p138.png`]

**Fig. 9.** First-sixteen real semantic mask backend diagnostic. [File: `paper/figures/torwic_dynamic_mask_first16_real_p139.png`]

**Fig. 10.** First-thirty-two real semantic mask backend diagnostic. [File: `paper/figures/torwic_dynamic_mask_first32_real_p140.png`]

**Fig. 11.** Before/after map composition: B0 naive-all-admit vs B2 richer admission policy. [File: `paper/figures/torwic_before_after_map_composition_p156.png`]

**Fig. 12.** Object lifecycle: stable barrier admission vs forklift rejection. [File: `paper/figures/torwic_object_lifecycle_p156.png`]

**Fig. 13.** Map-admission decision space: dynamic ratio vs session count. [File: `paper/figures/torwic_admission_decision_space_p156.png`]

**Fig. 14.** Per-category retention/rejection bar chart. [File: `paper/figures/torwic_per_category_retention_p157.png`]

**Fig. 15.** Rejection reason distribution. [File: `paper/figures/torwic_rejection_reason_distribution_p157.png`]

**Fig. 16.** Per-category by rejection-reason heatmap. [File: `paper/figures/torwic_rejection_reason_heatmap_p157.png`]

## Appendix: Archived Evidence Pointers

- Object-maintenance closure and package indexes remain in `outputs/` and the P154-P157 export/evidence chain.
- P225 package: `paper/export/temporal_masked_sequence_p225.md`.
- P227 baseline reproduction: `paper/export/p225_baseline_reproduction_p227.md`.
- P228 module: `paper/export/confidence_gated_mask_module_p228.md`.
- P228 story table: `paper/export/p228_paper_story_results.md`.
- P233 multi-window hard-gate validation: `paper/export/gated_mask_multi_window_p233.md`.
- P234 hard-gate failure sweep: `paper/export/gated_mask_failure_sweep_p234.md`.
- P235 soft-boundary candidate: `paper/export/soft_boundary_mask_p235.md`.
- P236 integration lock: `paper/export/thick_results_lock_p236.md`.
- Current reorganization summary: `paper/export/thick_manuscript_reorganization_p229.md`.
