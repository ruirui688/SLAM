# Dynamic Industrial Semantic-Segmentation-Assisted SLAM in Industrial Environments

Status: repository-visible draft, updated 2026-05-11. This draft includes the
P217-P220 dynamic-mask training and front-end masking evidence. It is a
paper-progress manuscript, not final venue typesetting.

## Abstract

Dynamic industrial environments challenge semantic SLAM because stable
infrastructure, movable equipment, forklifts, carts, people, and temporary cargo
can appear in the same RGB-D observations. A semantic map that admits every
segmented object as persistent structure risks semantic drift and dynamic-object
contamination. This paper studies semantic-segmentation-assisted SLAM for
dynamic industrial environments as an auditable map-admission problem. Starting
from an RGB-D open-vocabulary frontend based on Grounding DINO, SAM2
segmentation, OpenCLIP reranking, and 2D-to-3D object initialization, we build
an object-centric maintenance layer that converts segmentation-derived
detections into ObjectObservations, session-level TrackletRecords,
cross-session MapObjects, and revisioned map updates. The key mechanism is
explicit admission control rather than raw detection yield: persistence,
stability, and dynamicity signals determine whether segmented semantic evidence
is retained as stable landmark support or rejected as transient or dynamic
contamination. We evaluate the current system on TorWIC industrial RGB-D
revisits under same-day, cross-day, and cross-month Aisle protocols, with
Hallway retained as a separate 10-session broader-validation branch. The primary
Aisle ladder reaches `203/11/5`, `240/10/5`, and `297/14/7` for frame-level
objects, cross-session clusters, and retained stable objects; the Hallway branch
reaches `537/16/9` over `80/80` executed first-eight Hallway frames. The results
support a bounded systems claim: segmentation-assisted semantic observations can
become auditable long-term SLAM map evidence when filtered through cross-session
stable-object retention and dynamic-contamination rejection rules.

## Index Terms

Semantic SLAM, dynamic SLAM, semantic segmentation, long-term mapping,
open-vocabulary perception, object-level mapping, industrial robotics, RGB-D
perception, map maintenance.

## 1. Introduction

Industrial mobile robots operate in environments that change repeatedly over
time. A warehouse aisle, assembly area, or logistics corridor may contain
persistent infrastructure, semi-static work equipment, and dynamic agents within
the same field of view. Long-term SLAM motivates map reuse across such revisits,
while dynamic SLAM shows why moving or semi-static objects must be handled
explicitly rather than treated as rigid background structure. A
semantic-segmentation-assisted SLAM system must therefore answer a different
question from a single-frame segmenter or detector: which segmented semantic
observations should become persistent map evidence after repeated revisits, and
which should be rejected as dynamic or unreliable?

Open-vocabulary perception has made it practical to query arbitrary object
categories in real scenes. Object-level SLAM and open-vocabulary 3D mapping
provide useful precedents for compact landmarks and language-aligned 3D scene
representations. However, these outputs are not directly equivalent to durable
map entities. Labels may drift, masks may fragment across frames, dynamic agents
may reappear in different locations, and visually similar objects may be
incorrectly merged. In industrial settings, these errors are not minor: a
persistent map polluted by forklifts or temporary cargo can degrade later
inspection, planning, or navigation even when the original segmentation masks
were visually plausible.

This work focuses on the maintenance layer between semantic segmentation,
open-vocabulary perception, and a long-term SLAM object map. Instead of treating
every segmentation-derived detection as a map update, we explicitly represent
frame-level observations, aggregate them within sessions, associate them across
sessions, and decide whether a cross-session object should be retained as stable
semantic landmark evidence. The goal is not to claim a final lifelong SLAM
backend, but to make the admission process explicit, executable, and auditable
on real industrial RGB-D data.

![Figure 1. Representative TorWIC industrial RGB-D revisits with segmentation overlays. The panels show why the paper treats semantic detections as candidate evidence rather than immediate persistent map structure: stable barriers, work tables, warehouse racks, and forklift-like dynamic contamination can appear in the same revisit family.](figures/torwic_real_session_overlays.png)

## 2. Contributions

1. We formulate semantic-segmentation-assisted SLAM in dynamic industrial
   environments as a map-admission problem over segmented semantic observations,
   repeated revisits, and dynamic-object contamination.
2. We implement an object-centric maintenance pipeline that converts
   open-vocabulary RGB-D segmentation outputs into ObjectObservations,
   TrackletRecords, MapObjects, and MapRevisions.
3. We introduce interpretable persistence, stability, and dynamicity signals
   that decide whether semantic evidence is retained as stable landmark support
   or rejected as transient/dynamic evidence.
4. We define a TorWIC multi-session evaluation protocol spanning same-day,
   cross-day, cross-month, and Hallway broader-validation revisit settings
   without promoting secondary Hallway evidence into the primary Aisle ladder.
5. We provide current evidence showing stable-object retention,
   dynamic-contamination rejection, and map-admission selectivity on real
   industrial RGB-D data.
6. We report the current dataset-mask-supervised dynamic/non-static front-end
   training route, including P217 dataset construction, P218 compact mask-model
   training, P219 held-out masking quality, and P220 ORB feature-level masking
   effects.

## 3. Method

The frontend uses text-guided detection, SAM2 segmentation, reranking, and RGB-D
initialization. Grounding DINO proposes boxes from text prompts, SAM2 generates
masks, OpenCLIP reranks and resolves labels, and depth is used to form compact
geometric summaries. Each retained candidate becomes an ObjectObservation with
frame identifiers, label information, confidence scores, mask references,
centroid estimates, size summaries, and quality metadata.

![Figure 2. Paper-facing overview of the current first-eight-frame evidence stack. The figure summarizes per-session observations, cross-session clusters, selected stable objects, and rejected dynamic-like clusters used by the current manuscript.](figures/torwic_paper_result_overview.png)

Frame-level detections are noisy and may fragment across nearby frames. The
system therefore aggregates compatible observations inside each session into
TrackletRecords. Tracklets are then matched across sessions using semantic
compatibility and geometric consistency. The current implementation is
deliberately rule-based: it favors transparent debugging and interpretable
failure analysis over opaque learned association. Each accepted association
updates a persistent MapObject.

For each MapObject, the maintenance layer records session support, label
consistency, and dynamic-contamination indicators. A simple trust score can be
interpreted as:

```text
S_trust(m) = S_persist(m) * S_stable(m) * (1 - S_dynamic(m))
```

This score is not presented as an optimal estimator. It is an auditable
admission signal used to decide whether an object belongs in the stable map
layer. Every map update is recorded as a MapRevision, making retained objects,
rejected objects, and dynamic contamination traceable to concrete sessions and
observations.

### Dynamic/Non-Static Mask Front End

The current learned component is not the map-admission gate. It is a
dataset-mask-supervised front-end model that predicts dynamic/non-static pixels
for masking before SLAM feature extraction. P217 constructs this training set
from dataset-provided TorWIC/AnnotatedSemanticSet semantic/indexed masks:
`source_image.png`, `combined_indexedImage.png`, and `raw_labels_2d.json`.
Positive pixels are semantic indices for `cart_pallet_jack`, `fork_truck`,
`goods_material`, `misc_dynamic_feature`, `misc_non_static_feature`, `person`,
and `pylon_cone`; static object, context, and background pixels are encoded as
zero. `goods_material` is treated as movable clutter for front-end masking, not
as persistent-map admission ground truth.

The resulting P217 dataset contains 237 rows from 79 frame groups, split
deterministically by frame group into 156 train, 51 validation, and 30 test
rows. Frame overlap across train/validation/test is zero. The overall
dynamic/non-static positive pixel rate is 0.374176.

P218 trains a compact UNet-style binary mask model in the `tram` CUDA
environment on an NVIDIA RTX 3060. Images and masks are resized to `320x180`.
The smoke run uses 5 epochs, batch size 8, and
`BCEWithLogitsLoss(pos_weight=1.489919) + 0.5 * DiceLoss`. The operating
threshold is selected from validation F1 and is 0.40. Validation IoU/F1 are
0.671304/0.803329; test IoU/F1 are 0.578580/0.733038. This is a semantic
dynamic-mask front-end result, not learned admission control.

P219 packages six held-out validation/test samples as raw image, predicted
mask, ground-truth dynamic mask, and masked image artifacts. Mean mask
precision/recall/F1/IoU over the package are
0.556007/0.789669/0.604636/0.443210. P220 then evaluates ORB feature-level
effects with OpenCV in the `tram` environment: total raw keypoints are 10059
and masked keypoints are 9972, while keypoints inside ground-truth dynamic
regions drop from 4795 to 2192, a 54.2857% reduction.

This front-end masking evidence does not include trajectory ATE/RPE. The P219
package is a six-frame held-out package without timestamps, calibration, or
aligned trajectory ground truth. The current admissible claim is therefore
feature-level dynamic-region suppression, not SLAM trajectory improvement.

## 4. Experimental Protocol

We use TorWIC industrial RGB-D revisits as the evaluation source. The current
protocol has four evidence families:

1. same-day richer Aisle bundle;
2. cross-day richer Aisle bundle;
3. cross-month richer Aisle bundle;
4. Hallway broader-validation branch.

The first three form the primary paper-facing Aisle ladder. The Hallway branch
is a secondary broader-validation branch and is not used to replace or expand
the primary ladder.

## 5. Results

Table 1 summarizes the current primary evidence ladder for stable
semantic-landmark retention under dynamic industrial revisit conditions.

| Setting | Sessions | Frame-Level Objects | Cross-Session Clusters | Retained Stable Objects |
|---|---:|---:|---:|---:|
| Same-day richer Aisle bundle | 4 | 203 | 11 | 5 |
| Cross-day richer Aisle bundle | 4 | 240 | 10 | 5 |
| Cross-month richer Aisle bundle | 6 | 297 | 14 | 7 |

The cross-month setting is the strongest current main-table condition. Its
retained stable subset contains work-table, warehouse-rack, and barrier
clusters. The rejected set is interpretable: repeated forklift-like evidence is
treated as dynamic-contamination-like evidence rather than admitted into the
stable map.

![Figure 3. Stable-object admission example. Green rows are retained as stable object evidence; red rows are rejected clusters, including forklift-like dynamic contamination and insufficiently supported candidates.](figures/torwic_stable_object_selection_v5.png)

The Hallway branch is complete over 80/80 planned first-eight-frame commands
across ten Hallway sessions. It produces 537 frame-level objects, 16
cross-session clusters, and 9 selected stable objects.

![Figure 4. Hallway broader-validation composite. This branch validates the same object-maintenance output structure on a recovered 10-session Hallway family, but remains secondary and must not be merged into the primary Aisle ladder.](figures/torwic_hallway_composite.png)

| Validation Branch | Sessions | Frame-Level Objects | Cross-Session Clusters | Retained Stable Objects |
|---|---:|---:|---:|---:|
| Hallway broader validation | 10 | 537 | 16 | 9 |

Table 2 reframes the same audited quantities as a dynamic-SLAM
map-admission view.

| Setting | Frame-Level Segmented Objects | Cross-Session Clusters | Retained Stable Landmarks | Rejected Clusters | Dynamic-Like Rejected Clusters | Map-Admission Reduction |
|---|---:|---:|---:|---:|---:|---:|
| Same-day Aisle | 203 | 11 | 5 | 6 | 3 | 97.5% |
| Cross-day Aisle | 240 | 10 | 5 | 5 | 3 | 97.9% |
| Cross-month Aisle | 297 | 14 | 7 | 7 | 5 | 97.6% |
| Hallway broader validation | 537 | 16 | 9 | 7 | 4 | 98.3% |

Across the three primary Aisle protocols, the stable-landmark retention rate
stays in the 45.5%-50.0% cluster range rather than monotonically accumulating
all detections. Dynamic-like rejection increases from three forklift-like
rejected clusters in same-day and cross-day to five in cross-month. This
supports the paper's dynamic-SLAM claim: the system does not simply accumulate
segmented objects; it filters dynamic or insufficiently supported semantic
evidence before map admission.

## 6. Discussion

The central design decision is to place an explicit maintenance layer between
semantic segmentation/open-vocabulary perception and the persistent SLAM map.
This avoids a common failure mode in semantic mapping: treating detector output
as map truth. In industrial environments, repeated detection of forklifts or
temporary objects is not stable map evidence. A long-term object map must decide
what to retain.

The current method remains lightweight, but this is useful for an initial
systems paper. Each decision can be inspected at the observation, tracklet,
map-object, and revision level. The rejection mix is not a black-box metric; it
can be traced to object categories and support patterns.

The evidence stack is intentionally layered: a primary Aisle richer ladder, a
historical fallback family, and a Hallway broader-validation branch. This makes
the current submission package easier to audit, because readers do not need to
infer which numbers are primary evidence and which are secondary validation
evidence.

## 7. Limitations

The current system is not a complete lifelong SLAM backend. Association remains
rule-based, dense object-level ground truth is not yet available, and the
submission-ready evaluation is limited to first-eight-frame windows. The Hallway
branch is complete for the current first-eight-frame validation protocol, but
larger-window or full-trajectory Hallway evaluation remains future work.

The current results should not be interpreted as downstream navigation or
planning gains. The evidence supports object-map maintenance, stable-object
retention, and dynamic-contamination rejection on real industrial revisits. It
does not yet measure improved task performance for a deployed robot.

The current learned dynamic-mask model must also be separated from
admission-control learning. P195 remains blocked because independent
`human_admit_label` and `human_same_object_label` values are absent
(`0/32` and `0/160` valid, respectively). P193 weak labels and rule-derived
proxy fields are historical evidence only and cannot support a learned
persistent-map admission claim.

## 8. Conclusion

This paper presents an object-centric approach to
semantic-segmentation-assisted SLAM for dynamic industrial environments. The
framework transforms open-vocabulary RGB-D segmentation outputs into
observation, tracklet, map-object, and revision layers, then uses explicit
persistence, stability, and dynamicity signals to retain stable semantic
landmarks and suppress dynamic contamination. Current TorWIC evidence
demonstrates a reproducible ladder across same-day, cross-day, and cross-month
Aisle protocols, with Hallway retained as a separate 10-session
broader-validation branch. The resulting package supports a bounded systems
contribution: not a final lifelong SLAM benchmark, not dense dynamic
reconstruction, and not a downstream navigation-gain claim, but an auditable
bridge from segmentation-assisted open-vocabulary perception to revisioned
long-term object-map maintenance on real industrial revisits.

## Evidence Anchors

- Progress log: `RESEARCH_PROGRESS.md`
- Dataset source policy: `DATA_SOURCES.md`
- Primary package index: `outputs/torwic_submission_ready_package_index_v8.md`
- Current closure bundle: `outputs/torwic_submission_ready_closure_bundle_v19.md`
- Inline citation/evidence threading matrix:
  `outputs/torwic_p109_inline_citation_threading_matrix_v1.md`
- Tracked paper figures: `paper/figures/`
- Dynamic-mask training section:
  `paper/export/dynamic_mask_training_section_p222.md`
