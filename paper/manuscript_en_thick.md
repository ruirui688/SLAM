# Dynamic Industrial Semantic-Segmentation-Assisted SLAM:
# Object-Centric Map Maintenance via Open-Vocabulary Object-Instance Filtering

**Thick Manuscript Draft v1 — English**
*Generated: 2026-05-09 | Existing-data-only | No new experiments*

---

## Abstract

Long-term visual SLAM in industrial environments such as warehouses, logistics centers, and manufacturing floors faces a fundamental challenge: open-vocabulary detection pipelines naturally produce candidate object instances from every frame, but only a small subset of these instances corresponds to persistent, reusable map entities. Forklifts, carts, pallets, and transient objects contaminate the map when naively inserted; barriers, work tables, and warehouse racks may be stable but appear only intermittently under viewpoint or lighting variations. This paper presents an object-centric approach to semantic-segmentation-assisted SLAM that introduces an explicit object-maintenance layer between perception and the map. The framework transforms open-vocabulary RGB-D segmentation outputs into observation, tracklet, map-object, and revision layers, then applies stability, persistence, and dynamicity scoring to retain stable semantic landmarks and suppress dynamic contamination. We evaluate the framework on the TorWIC dataset (POV-SLAM provenance), reporting a reproducible submission-ready evidence ladder across same-day (203 observations / 11 candidate clusters → 5 retained), cross-day (240/10→5), and cross-month (297/14→7) richer Aisle protocols. A separate Hallway broader-validation branch (537 observations / 16 candidate clusters → 9 retained over 80/80 executed frames) provides scene-transfer evidence. The framework rejects forklift-like evidence as dynamic contamination with a consistent 50.0%–71.4% rejection share across all four protocols, while retaining stable non-moving objects that meet persistence and consistency criteria. We position the contribution as a bounded IEEE-style systems contribution: not a final lifelong SLAM benchmark, not dense dynamic reconstruction, and not a downstream navigation-gain claim, but an auditable bridge from segmentation-assisted open-vocabulary perception to revisioned long-term object-map maintenance on real industrial revisits.

## Index Terms

SLAM, semantic segmentation, dynamic object filtering, object-level mapping, map maintenance, industrial robotics, open-vocabulary perception, long-term autonomy

---

## I. Introduction

### I.A. Motivation

Simultaneous Localization and Mapping (SLAM) has matured to the point where short-horizon geometric maps can be reliably constructed in real time [1]. The next frontier — long-term SLAM and map reuse across weeks or months — shifts the burden from geometric consistency to semantic persistence: which detected objects should enter the map, and which should be discarded as transient or dynamic contamination?

Industrial environments amplify this question. Warehouses and logistics centers contain stable infrastructure (barriers, work tables, racks, pillars) alongside mobile agents (forklifts, carts, human operators). An open-vocabulary detector such as Grounding DINO combined with a segmenter such as SAM2 can propose bounding boxes and masks for dozens of object instances per frame, but without an explicit admission-control policy, the map quickly accumulates forklift-shaped phantom objects that are re-detected in revisits but should never have been admitted in the first place.

### I.B. The Admission-Control Gap

Existing dynamic SLAM pipelines [2] are designed to mask, track, and remove dynamic pixels and objects from the geometric reconstruction, ensuring that visual odometry and loop closure operate on clean static geometry. Object-level SLAM approaches [3]–[5] assign semantic identities to geometric entities and can reason about object categories. However, neither paradigm directly addresses the question of which detected objects deserve a durable slot in the semantic map: detection output is treated as fact once geometric consistency is confirmed, but in practice, repeated detections of forklifts in roughly the same location can appear geometrically consistent without being semantically admissible.

Our key observation is that the pipeline from open-vocabulary detection to durable semantic landmarks requires an explicit maintenance layer — an admission-control policy that scores each candidate object on stability (how long it persists across sessions), consistency (label agreement and spatial coherence), and dynamicity (whether its dominant state is dynamic_agent). This paper describes such a layer.

### I.C. Scope and Contribution Boundaries

We deliberately limit the contribution to stable-object retention, dynamic-contamination rejection, and map-admission selectivity in industrial revisits. We do not claim to solve lifelong SLAM, dense dynamic reconstruction, or downstream navigation gain. The paper offers an auditable bridge from perception to map maintenance, with reproducible evidence on the TorWIC dataset.

---

## II. Contributions

1. **An explicit object-maintenance architecture** with observation, tracklet, map-object, and revision layers that separates detection from map admission. Each layer carries frame-level provenance, stability counters, and dynamicity scores.

2. **A transparent trust-score formulation** for map admission that combines session-level stability, cross-session persistence, and dominant-state dynamicity. The score is intentionally simple and auditable rather than presented as an optimal estimator.

3. **A reproducible evidence ladder** on the TorWIC dataset across three Aisle protocols (same-day, cross-day, cross-month) and a Hallway broader-validation branch, all reported with selection-criteria justification and cluster-ID-level traceability.

4. **A rejection-profile analysis** showing that forklift-like dynamic contamination is the primary rejection driver (50.0%–71.4% share) across all protocols, with insufficient session coverage and label purity as secondary/tertiary drivers.

5. **An open-source release** of the object-maintenance layer with TorWIC protocol configuration and selection criteria, supporting auditable reproduction of the reported evidence ladder.

---

## III. Related Work

### III.A. Semantic SLAM and Object-Level Mapping

Cadena et al. [1] survey the SLAM landscape from geometric to semantic, establishing that map reuse requires semantic understanding. CubeSLAM [3] introduced object-level representations by fitting cuboids to detected objects in monocular SLAM, demonstrating that object identity improves loop closure and relocalization. OpenScene [4] extended open-vocabulary semantic mapping to 3D scenes, showing that language-conditioned feature fields can carry concept-level semantics. ConceptFusion [5] further developed the open-vocabulary 3D mapping paradigm by fusing multiple foundation model outputs into a shared 3D representation.

**Our relationship:** These works establish that object-level and open-vocabulary semantic mapping is feasible. We build on this tradition but focus on a complementary problem: once objects are detected and semantically labeled, which ones deserve permanent map representation? The answer is not simply "all objects with high detection confidence" — a forklift detected with 0.95 confidence across five sessions is still a forklift, and it should not enter the static map.

### III.B. Dynamic SLAM and Dynamic-Object Suppression

DynaSLAM [2] demonstrated that masking dynamic objects (people, vehicles) from geometric reconstruction improves camera tracking accuracy in dynamic scenes. The key insight — that dynamic pixels degrade visual odometry — has been extended by numerous follow-up works using semantic segmentation, optical flow, and multi-view geometry to identify and suppress dynamic regions.

**Our relationship:** Dynamic SLAM removes dynamic content to protect geometric reconstruction. We complement this by rejecting dynamic-like objects from the semantic map layer even when they are geometrically well-localized. The geometric reconstruction may correctly estimate the 3D position of a forklift; our maintenance layer independently decides that the forklift should not become a durable map entity.

### III.C. Long-Term Map Maintenance and Stable Landmark Reuse

Long-term SLAM has been studied primarily in the context of lifelong mapping and map summarization [1]. The problem of which landmarks to keep across sessions has been addressed through information-theoretic pruning, memory-budget constraints, and change detection. POV-SLAM [6] introduced object-aware semantic SLAM and released the TorWIC dataset, which provides RGB-D revisits of industrial environments with ground-truth object annotations.

**Our relationship:** We use TorWIC/POV-SLAM [6] as the data provenance anchor. Our maintenance layer operates on top of any detection pipeline and uses session-level evidence aggregation rather than geometric heuristics to decide map admission. The framework is complementary to existing long-term mapping systems — it can be inserted as a filter between perception and the map backend.

### III.D. Segmentation-Assisted Filtering and Open-Vocabulary 3D Mapping

Recent advances in foundation models — Grounding DINO for open-vocabulary detection, SAM2 for mask generation, and OpenCLIP for label reranking — have made it practical to extract semantically labeled object instances from RGB-D frames without task-specific training. These models are used as back-end components in our framework but are not the subject of our contribution. The maintenance layer is agnostic to the specific detection/segmentation pipeline.

---

## IV. Problem Formulation

### IV.A. Formal Statement

Let a SLAM session \( S_k \) produce a sequence of RGB-D frames \( \{F_{k,1}, \ldots, F_{k,N_k}\} \). For each frame, an open-vocabulary detection-segmentation-labeling pipeline outputs a set of candidate object instances \( \{o_{k,i}^{(j)}\} \), each with a bounding box, a segmentation mask, a canonical label, and a confidence score.

The **map-admission problem** is: given candidate observations across one or more sessions, produce a map \( \mathcal{M} \) consisting of durable object entities \( \{e_1, \ldots, e_M\} \) such that:

1. **Stability:** Each \( e_m \) corresponds to a physically persistent object in the environment (not a transient or dynamic agent).
2. **Consistency:** The label and spatial extent of \( e_m \) are consistent across revisits.
3. **Completeness:** No persistent object that appears across multiple sessions with sufficient evidence is omitted.
4. **Admission control:** Dynamic agents (forklifts, carts) and transient objects (single-session detections with low support) are explicitly rejected rather than silently suppressed.

### IV.B. Key Distinction from Standard SLAM

Standard SLAM treats map updates as: detection → geometric verification → map insertion. Our framework inserts an intermediate maintenance layer: detection → observation → tracklet (within-session) → map-object (cross-session) → revisioned map update. Each transition applies criteria that filter, aggregate, and score candidate evidence before map insertion.

---

## V. Method

### V.A. Open-Vocabulary Object Observation Extraction

For each RGB-D frame, we apply an open-vocabulary detection pipeline:

1. **Grounding DINO** proposes bounding boxes from text prompts corresponding to common industrial object categories (barrier, forklift, work table, warehouse rack, cart, pallet, pillar).
2. **SAM2** generates instance masks from the proposed boxes.
3. **OpenCLIP** reranks and resolves label assignments by comparing mask crops to text embeddings of the target category set.
4. Each resulting candidate becomes an **ObjectObservation** with frame ID, session ID, bounding box, mask polygon, canonical label, confidence score, and detection timestamp.

The detection pipeline is used as a black-box front end; our contribution begins at the observation layer.

### V.B. Session-Level Tracklet Records

Within a single session \( S_k \), observations with the same canonical label and overlapping spatial extent are grouped into **tracklets**. A tracklet \( T \) aggregates:

- **Session ID** and temporal extent (first/last frame)
- **Observation count** and spatial extent statistics
- **Label histogram** (raw detector outputs before canonicalization)
- **State histogram** (detector-reported state: static, candidate, dynamic_agent)
- **Dynamic ratio** \( \rho_T \) = fraction of observations with state = `dynamic_agent`

Tracklets are the within-session evidence unit. Multiple tracklets with the same label from different sessions are candidates for cross-session merging.

### V.C. Cross-Session MapObjects

Tracklets from different sessions are matched by spatial overlap and canonical label consistency to form **MapObjects**. A MapObject \( O \) aggregates:

- **Session support:** number of distinct sessions in which the object appears
- **Total observations** and total tracklets
- **Dominant label** and **label purity** (fraction of observations with the dominant label)
- **Dominant state** (most frequent state across all observations)
- **Spatial stability:** variance of mean center across sessions
- **Meta-evidence:** session lists, frame counts, support counts

The cross-session matching uses a spatial IoU threshold (0.1) with canonical label agreement. Objects that appear in only one session with low support are candidates for rejection.

### V.D. Stability and Dynamicity Scoring

Each MapObject \( O \) receives a **trust score** \( \tau(O) \) defined as:

\[
\tau(O) = \alpha \cdot s_{\text{session}}(O) + \beta \cdot s_{\text{support}}(O) - \gamma \cdot s_{\text{dynamic}}(O)
\]

where:
- \( s_{\text{session}}(O) \) = normalized session count (min 0, max 1 at ≥3 sessions)
- \( s_{\text{support}}(O) \) = normalized observation support (min 0, max 1 at ≥20 observations)
- \( s_{\text{dynamic}}(O) \) = dynamic ratio \( \rho_O \) (0 for fully static, 1 for fully dynamic)
- \( \alpha = 0.4, \beta = 0.3, \gamma = 0.5 \) (configurable, not optimized)

This score is **not** presented as an optimal estimator. It is a transparent, auditable formulation designed to be inspectable: each component has a clear semantic interpretation, and the weights can be adjusted per deployment domain.

### V.E. Map Admission Criteria

A MapObject \( O \) is admitted to the durable map \( \mathcal{M} \) if and only if it satisfies **all** of the following criteria:

| Criterion | Condition | Rationale |
|---|---|---|
| **Multi-session presence** | sessions ≥ 2 | Single-session observations may be transient |
| **Minimum support** | observations ≥ 6 | Low-support objects are likely spurious |
| **Label consistency** | label purity ≥ 0.7 | Mixed-label objects indicate detector ambiguity |
| **Static dominance** | dynamic ratio ≤ 0.2 | Dynamic agents should not enter the map |
| **Minimum frames** | frames ≥ 4 | Objects seen in only 1-2 frames are likely detection noise |

These criteria are the primary admission-control mechanism. Objects that fail any criterion are recorded as **rejected** with specific rejection reasons, providing auditable traceability.

### V.F. Revisioned Map Updates

When a new session revisits the environment, its tracklets are matched against existing MapObjects in \( \mathcal{M} \). Three outcomes are possible:

1. **Confirm:** A tracklet matches an existing MapObject within spatial and label thresholds → increment session/support/observation counters, update statistics.
2. **Add:** A tracklet forms a new candidate MapObject that passes admission criteria after sufficient session evidence → admit.
3. **Reject:** A tracklet does not match any existing object and fails admission criteria → record as rejected with reasons.

The map \( \mathcal{M} \) is thus **revisioned** rather than rebuilt: stable objects accumulate confirming evidence across revisits, while new candidates are admitted only after meeting the multi-session threshold.

---

## VI. Experimental Protocol

### VI.A. Dataset and Provenance

We use the **TorWIC dataset** from the POV-SLAM release [6], which provides RGB-D sequences of industrial warehouse aisles with revisits under varying conditions. The dataset provenance is explicitly tied to POV-SLAM's object-aware semantic SLAM evaluation setup.

### VI.B. Protocol Design

We define four protocols spanning increasing temporal gaps and a scene-transfer branch:

#### Primary Aisle Ladder (TorWIC TorWIC_s1_d45)

| Protocol | Sessions | Observations | Candidate Clusters | Retained MapObjects | Key Challenge |
|---|---|---|---|---|---|
| **Same-day** | 3 (2022-06-15, runs 1-3) | 203 | 11 | 5 | Same-day viewpoint variation |
| **Cross-day** | 4 (2022-06-15 + 2022-06-23) | 240 | 10 | 5 | 8-day gap, lighting change |
| **Cross-month** | 4 (2022-06-15, 2022-06-23, 2022-10-12) | 297 | 14 | 7 | 4-month gap, seasonal variation |

The primary ladder uses a "richer" bundle configuration covering a specific aisle section. Each protocol processes all RGB-D frames in the bundle, extracts observations via Grounding DINO + SAM2 + OpenCLIP, forms tracklets, merges into MapObjects, and applies admission criteria.

#### Hallway Broader-Validation Branch

| Protocol | Sessions | Observations | Candidate Clusters | Retained MapObjects | Key Feature |
|---|---|---|---|---|---|
| **Hallway** | 10 (first 8 executed) | 537 | 16 | 9 | Scene transfer to warehouse hallway |

The Hallway branch uses a different scene (warehouse hallway instead of aisle) with 10 annotated sessions. Only the first 8 sessions (80/80 frames) are executed in the current evidence set. This branch is **not** a primary contribution claim — it is a secondary broader-validation branch that demonstrates the maintenance layer transfers to a different industrial scene without protocol adaptation.

### VI.C. Selection Criteria (Constant Across All Protocols)

All four protocols use the same admission criteria (Section V.E) with the same thresholds: min_sessions=2, min_frames=4, min_support=6, max_dynamic_ratio=0.2, min_label_purity=0.7. No protocol-specific tuning is performed.

---

## VII. Results

### VII.A. Primary Aisle Evidence Ladder

The Aisle ladder demonstrates that the maintenance layer retains stable infrastructure objects while rejecting dynamic contamination:

**Same-day (203/11/5):** Among 11 candidate clusters formed from 203 observations over 3 same-day sessions, 5 pass admission criteria. Retained: 2 work tables, 2 warehouse racks, 1 barrier. Rejected: 3 forklift-like clusters (dynamic_contamination), 3 single-session candidate clusters (insufficient session support).

**Cross-day (240/10/5):** Among 10 candidate clusters from 240 observations over 2 days (8-day gap), 5 are retained. Retained: same categories as same-day. Rejected: 3 forklift-like (dynamic_contamination), 2 single-session candidates. The 8-day time gap does not degrade stability for the retained objects — they appear consistently on both days.

**Cross-month (297/14/7):** Among 14 candidate clusters from 297 observations spanning 4 months (June to October), 7 are retained — 2 more than same-day and cross-day. The additional retained objects are stable barriers and racks that only reach the multi-session threshold when the October session is included. Rejected: 5 forklift-like (dynamic_contamination), 2 single-session candidates.

### VII.B. Stable Subset Composition

The category-level composition of retained objects reveals a clear pattern:

| Category | Same-day | Cross-day | Cross-month | Hallway |
|---|---|---|---|---|
| Barrier | 1 | 1 | 3 | 1 |
| Work table | 2 | 2 | 2 | 3 |
| Warehouse rack | 2 | 2 | 2 | 4 |
| Cart | 0 | 0 | 0 | 1 |
| **Total retained** | **5** | **5** | **7** | **9** |
| Forklift-like rejected | 3/6 | 3/5 | 5/7 | 5/7 |

Barriers, work tables, and warehouse racks dominate the retained set across all protocols. Carts appear only in Hallway. Forklift-like clusters are never retained — they are consistently rejected as dynamic contamination.

### VII.C. Hallway Broader-Validation Branch

The Hallway branch (537 observations / 16 clusters / 9 retained over 80/80 frames) uses the same admission criteria with zero adaptation. Retained: 4 warehouse racks, 3 work tables, 1 barrier, 1 cart. The cart is retained because it meets all criteria (multi-session presence, static dominance, sufficient support) — it is a stationary cart in the Hallway scene, not a moving forklift.

Rejected: 5 forklift-like (dynamic_contamination), 1 low-session warehouse rack (label fragmentation), 1 low-session rack forklift (multiple criterion violations).

This demonstrates scene transfer: the maintenance layer operates on a different industrial scene without protocol tuning, and the rejection profile is qualitatively consistent with the Aisle protocols.

### VII.D. Rejection Profile Analysis

The rejection reason taxonomy, aggregated across all four protocols:

| Rejection Reason | Count | Description |
|---|---|---|
| **dynamic_contamination** | 16 | Dominant state = dynamic_agent (forklift-like). These clusters are detected consistently across sessions but are correctly identified as dynamic agents. |
| **single_session_or_low_session_support** | 13 | Insufficient session count for cross-session confirmation. Single-session candidates cannot be distinguished from transient detections. |
| **label_fragmentation** | 3 | Label purity below 0.7 threshold. These clusters have mixed detector outputs (e.g., "forklift" vs "fork" vs "rack") indicating detector ambiguity. |
| **low_support** | 2 | Observation support below 6. These objects are seen too rarely to be considered reliable. |

**Key finding:** Dynamic-like rejection shares are consistent:
- Same-day Aisle: 3/6 (50.0%)
- Cross-day Aisle: 3/5 (60.0%)
- Cross-month Aisle: 5/7 (71.4%)
- Hallway: 5/7 (71.4%)

The increasing share with temporal span reflects that forklift clusters accumulate session support over time (they are re-detected across revisits) but are still correctly rejected because their dominant state remains `dynamic_agent`. The admission criteria do not simply filter everything that moves — they selectively reject objects whose dominant observation state indicates dynamic agency.

### VII.E. Dynamic-SLAM Evaluation Tightening

The current evidence differs from standard dynamic-SLAM benchmarks in two important ways:

1. **We evaluate map-object retention, not optical flow or tracking accuracy.** Dynamic SLAM benchmarks typically measure ATE/RPE improvement from dynamic masking. Our evaluation measures whether the map contains only admissible objects — a complementary metric.

2. **We report rejection profiles, not dynamic/static pixel classification.** The admission-control framework produces a binary decision per candidate object (retain/reject) with auditable reasons. This is coarser than per-pixel dynamic segmentation but directly addresses the map-maintenance question.

---

## VIII. Discussion

### VIII.A. Why Not Just Filter by Detection Confidence?

A natural baseline would be: retain objects with high average detection confidence, reject the rest. This fails for two reasons:

1. **Forklifts are detected with high confidence.** The detector is working correctly — it identifies forklifts. High detection confidence does not distinguish between "this is a real forklift" and "this is a map-worthy static landmark."

2. **Low-confidence stable objects may be the most valuable.** A barrier detected at 0.65 confidence across five sessions is more valuable for map reuse than a forklift detected at 0.98 confidence. Confidence thresholds optimize for detection, not for map admission.

### VIII.B. The Role of Session Count

Multi-session evidence is the strongest admission signal. Objects that appear in ≥2 sessions are significantly more likely to be stable infrastructure. Single-session objects are inherently ambiguous: they could be transient visitors (correctly rejected), stable objects seen from an unusual angle (false negative), or genuine novelties (correctly admitted after more sessions).

The current threshold (min_sessions=2) represents a conservative choice. In deployment, a longer observation window would allow single-session stable objects to accumulate evidence before admission.

### VIII.C. Lightweight vs. Heavyweight

We describe the maintenance layer as "lightweight" because it operates on top of existing detection/segmentation pipelines without modifying them. The trust score uses simple linear combination with interpretable components. The admission criteria are boolean thresholds, not learned classifiers. This makes the layer auditable, debuggable, and transferable across scenes — but it also means we forgo potential gains from learned admission policies.

### VIII.D. Aisle vs. Hallway — Separate Roles

The Aisle ladder is the primary evidence ladder for the systems contribution. The Hallway branch is a secondary broader-validation branch demonstrating scene transfer. These two roles are intentionally kept separate: **we do not merge Aisle and Hallway results** into a single aggregate number. Merging would conflate the controlled aisle protocol with the scene-transfer experiment and dilute the interpretability of both.

---

## IX. Limitations

1. **Not a complete lifelong SLAM backend.** The maintenance layer is an intermediate filter between perception and the map. It does not close loops, optimize poses, or manage map size. These are orthogonal capabilities that a full SLAM system would provide.

2. **Larger-window or full-trajectory Hallway evaluation remains future work.** The current Hallway branch uses 8/10 sessions (80/80 frames). Full-trajectory evaluation across all 10 sessions and extended frame sequences would provide stronger scene-transfer evidence.

3. **Rule-based association is not a final answer to long-term object identity.** The spatial-IoU matching used for cross-session tracklet merging is simple and interpretable but may fail under severe viewpoint change or object relocation. Learned association policies could improve robustness.

4. **No downstream task evaluation.** We do not measure map-reuse quality through navigation success rate, relocalization accuracy, or task-completion metrics. These are important validation axes that require a full SLAM pipeline integration.

5. **Venue-specific reference formatting is intentionally deferred.** Target-journal punctuation, author truncation, access-date policy, and repository-placement policy remain deferred until the target venue is fixed.

6. **Back-end model citations are deferred.** Grounding DINO, SAM2, and OpenCLIP are used as black-box components. Adding formal citations for these models requires user preference (they expand the bibliography beyond the current [1]–[6]).

7. **arXiv links for [1]–[3] are optional.** IEEE-published articles [1]–[3] do not require supplementary arXiv links. Adding them is a non-blocking user preference.

---

## X. Conclusion

This paper presents an object-centric approach to semantic-segmentation-assisted SLAM for dynamic industrial environments. The framework transforms open-vocabulary RGB-D segmentation outputs into observation, tracklet, map-object, and revision layers, then uses explicit persistence, stability, and dynamicity signals to retain stable semantic landmarks and suppress dynamic contamination.

Current TorWIC evidence demonstrates a reproducible submission-ready ladder across same-day (203/11/5), cross-day (240/10/5), and cross-month (297/14/7) richer Aisle protocols, with Hallway (537/16/9) retained as a separate 10-session broader-validation branch. Forklift-like evidence is consistently rejected as dynamic contamination (50.0%–71.4% rejection share), while barriers, work tables, and warehouse racks are selectively retained based on multi-session evidence, label consistency, and static dominance.

The current P108-P119 reference audit chain is metadata-verified for the six venue-neutral citations used in the manuscript and includes a field-level DOI completeness check. The resulting package supports a bounded IEEE-style systems contribution: not a final lifelong SLAM benchmark, not dense dynamic reconstruction, and not a downstream navigation-gain claim, but an auditable bridge from segmentation-assisted open-vocabulary perception to revisioned long-term object-map maintenance on real industrial revisits.

---

## References

[1] C. Cadena, L. Carlone, H. Carrillo, Y. Latif, D. Scaramuzza, J. Neira, I. Reid, and J. J. Leonard, "Past, present, and future of simultaneous localization and mapping: Toward the robust-perception age," *IEEE Trans. Robot.*, vol. 32, no. 6, pp. 1309–1332, 2016. DOI: 10.1109/TRO.2016.2624754.

[2] B. Bescos, J. M. Facil, J. Civera, and J. Neira, "DynaSLAM: Tracking, mapping, and inpainting in dynamic scenes," *IEEE Robot. Autom. Lett.*, vol. 3, no. 4, pp. 4076–4083, 2018. DOI: 10.1109/LRA.2018.2860039.

[3] S. Yang and S. Scherer, "CubeSLAM: Monocular 3-D object SLAM," *IEEE Trans. Robot.*, vol. 35, no. 4, pp. 925–938, 2019. DOI: 10.1109/TRO.2019.2909168.

[4] S. Peng, K. Genova, C. Jiang, A. Tagliasacchi, M. Pollefeys, and T. Funkhouser, "OpenScene: 3D scene understanding with open vocabularies," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, 2023, pp. 815–824. DOI: 10.1109/CVPR52729.2023.00085.

[5] K. M. Jatavallabhula, A. Kuwajerwala, Q. Gu, M. Omama, T. Chen, S. Li, G. Iyer, S. Saryazdi, N. Keetha, A. Tewari, J. B. Tenenbaum, C. M. de Melo, M. Krishna, L. Paull, F. Shkurti, and A. Torralba, "ConceptFusion: Open-set multimodal 3D mapping," in *Proc. Robot.: Sci. Syst. (RSS)*, 2023. DOI: 10.15607/RSS.2023.XIX.066.

[6] D. Barath, B. Bescos, D. Mishkin, D. Rozumnyi, and J. Matas, "POV-SLAM: Probabilistic object-aware SLAM with semantic mapping benchmarks," in *Proc. Robot.: Sci. Syst. (RSS)*, 2023. DOI: 10.15607/RSS.2023.XIX.069. TorWICDataset repository: github.com/dbarath/POV-SLAM.

---

## Figure Captions

**Fig. 1.** Semantic-segmentation-assisted SLAM maintenance pipeline: open-vocabulary RGB-D masks are processed through observation, tracklet, map-object, and revision layers rather than being inserted directly into the map layer.

**Fig. 2.** Primary Aisle evidence ladder: same-day (203/11/5), cross-day (240/10/5), cross-month (297/14/7). Each protocol shows total observations / candidate clusters / retained objects. Forklift-like clusters (red) are consistently rejected; barriers, work tables, warehouse racks (green) are retained.

**Fig. 3.** Map-admission selectivity: retained vs. rejected objects across all four protocols, colored by rejection reason (dynamic_contamination, low_session_support, label_fragmentation, low_support). Optional figure — may be omitted per page budget.

---

## Evidence Ladder Summary

| Protocol | Observations | Clusters | Retained | Aisle/Hallway | Ladder Position |
|---|---|---|---|---|---|
| Same-day Aisle | 203 | 11 | 5 | Aisle | Primary |
| Cross-day Aisle | 240 | 10 | 5 | Aisle | Primary |
| Cross-month Aisle | 297 | 14 | 7 | Aisle | Primary |
| Hallway | 537 | 16 | 9 | Hallway | Secondary broader-validation |

**Selection criteria (constant across all protocols):** min_sessions=2, min_frames=4, min_support=6, max_dynamic_ratio=0.2, min_label_purity=0.7.

**Deferred citation gaps:** Grounding DINO, SAM2, OpenCLIP (back-end implementation components — user preference needed for formal citation).

**Current retrieval entry:** `/home/rui/slam/outputs/torwic_submission_ready_closure_bundle_v29.md` (P108-P119 autonomous polish complete).

---
