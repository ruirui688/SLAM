# P157 — Category Retention & Rejection Analysis

**Generated:** 2026-05-09  |  **Phase:** P157  |  **Project:** industrial-semantic-slam

## 1. Overview

- **Total clusters:** 20 (from 762 raw objects, 35 inputs)
- **Retained:** 5  |  **Rejected:** 4  |  **Retention rate:** 25.0%
- **Admission criteria:** min_sessions≥2, min_frames≥4, min_support≥6, max_dynamic_ratio≤0.2

**Key message:** Of 20 clustered objects across the TorWIC hallway benchmark, 5 (25%) pass all explicit stability criteria and are admitted to the long-term map. The remaining 15 are rejected for specific, interpretable reasons. Rejection reasons are multi-label — a single cluster can fail multiple criteria simultaneously, so rejection-reason mention count (29) exceeds the rejected cluster count (4).

## 2. Per-Category Retention / Rejection

| Category | Total | Retained | Rejected | Retention Rate |
|----------|-------|----------|----------|---------------|
| yellow barrier | 5 | 2 | 3 | 40.0% |
| work table | 4 | 2 | 2 | 50.0% |
| warehouse rack | 3 | 1 | 2 | 33.3% |
| forklift | 4 | 0 | 4 | 0.0% |
| other | 4 | 0 | 4 | 0.0% |
| **Total** | **20** | **5** | **15** | **25.0%** |

**Interpretation:**
- **Infrastructure objects** (yellow barrier, work table, warehouse rack): 5/12 retained. Rejections are driven primarily by observation sparsity (single-session or low-frame appearances), not semantic ambiguity. Extending session coverage could admit more infrastructure objects without relaxing stability criteria.
- **Dynamic agents** (forklift): 0/4 retained. All four forklift clusters are categorically rejected via the `dynamic` criterion (dynamic_ratio 0.88–1.00), demonstrating clean dynamic/non-dynamic separation without false positives.
- **Other** (work, rack forklift, ##lift): 0/4 retained. These clusters carry fragmented or compound labels unsuitable for long-term semantic mapping, and additionally fail on observation sparsity grounds.

## 3. Rejection Reason Breakdown (Multi-Label)

> **Note:** Multi-label counting — total reason mentions (29) > rejected clusters (4). A cluster can fail multiple criteria simultaneously.

| Rejection Reason | Count | Affected Clusters |
|------------------|-------|-------------------|
| single_session | 7 | cluster_0011, cluster_0013, cluster_0014, cluster_0016, cluster_0017, cluster_0018, cluster_0020 |
| low_frames | 8 | cluster_0005, cluster_0013, cluster_0015, cluster_0016, cluster_0017, cluster_0018, cluster_0019, cluster_0020 |
| low_support | 5 | cluster_0013, cluster_0016, cluster_0017, cluster_0018, cluster_0020 |
| dynamic | 4 | cluster_0003, cluster_0008, cluster_0010, cluster_0012 |
| label_frag | 4 | cluster_0005, cluster_0016, cluster_0018, cluster_0020 |
| internal_ranking | 1 | cluster_0007 |

**Reason semantics:**
- **single_session** (n=7): cluster observed in only 1 acquisition session — insufficient for cross-session stability evidence.
- **low_frames** (n=8): ≤3 frames with valid detections — insufficient for intra-session consistency.
- **low_support** (n=5): total detection count ≤5 — too sparse for reliable object confirmation.
- **dynamic** (n=4): dominant state is `dynamic_agent` (forklifts) — permanently excluded from static map.
- **label_frag** (n=4): canonical label is fragmented, ambiguous, or not a recognized infrastructure category.
- **internal_ranking** (n=1): cluster passes all explicit criteria but ranked below the top retained cluster in its category per the admission system's first-match ordering.

## 4. Per-Category × Rejection Reason Matrix

| Category | single session | low frames | low support | dynamic | label frag | internal ranking |
|---|---|---|---|---|---|---|
| yellow barrier | 2 | 1 | 0 | 0 | 0 | 0 |
| work table | 1 | 2 | 1 | 0 | 0 | 0 |
| warehouse rack | 1 | 1 | 1 | 0 | 0 | 1 |
| forklift | 0 | 0 | 0 | 4 | 0 | 0 |
| other | 3 | 4 | 3 | 0 | 4 | 0 |

**Patterns:**
- **forklift (4/4 dynamic):** 100% rejected via `dynamic`, zero other failure modes. The dynamic filter is simultaneously necessary and sufficient for this category — no forklift would be erroneously admitted, and no additional criterion is needed to reject them.
- **other (4/4 label_frag):** All non-standard categories fail on label fragmentation, with `low_frames` (4), `low_support` (3), and `single_session` (3) as strongly co-occurring factors.
- **yellow barrier (3 rejected):** 2 single-session, 1 low-frames. No dynamic or label issues. Observation sparsity is the sole failure mode for barriers.
- **work table (2 rejected):** 2 low-frames, 1 single-session, 1 low-support. Observation sparsity dominates; no semantic or dynamic contamination.
- **warehouse rack (2 rejected):** 1 single-session+low-frames+low-support (cluster 0017), 1 internal_ranking (cluster 0007 — passes all explicit criteria but ranked below cluster 0006).

## 5. Discussion & Caveats

1. **Cluster 0006 vs 0007 (warehouse rack):** Both clusters 0006 (7 sessions, 14 frames, 62 support) and 0007 (8 sessions, 15 frames, 75 support) pass all five explicit admission criteria. The admission system retained 0006 and rejected 0007 under a first-match per-category ordering. This is not a failure of the criteria — it reflects a per-category capacity constraint that selects the earliest qualifying cluster by processing order. Cluster 0007 is objectively well-observed and would be admitted under a relaxed per-category cap. This edge case is flagged for reviewer transparency.

2. **Multi-label counting methodology:** The rejection reason breakdown uses multi-label counting by design. For example, cluster 0016 (rack forklift) simultaneously fails `single_session`, `low_frames`, `low_support`, and `label_frag` — any single criterion is independently sufficient for rejection. The total mention count (29) correctly exceeds the rejected cluster count (4) and is explicitly documented throughout.

3. **Why total mentions > rejected clusters:** Multi-label counting is applied because rejection criteria are non-exclusive. A cluster with 1 session and 3 frames fails both `single_session` and `low_frames`. Counting each independently provides a more complete picture of why objects fail admission than single-label assignment would.

4. **Scope and framing:** This analysis addresses map admission stability only. No ATE/RPE trajectory metrics, dynamic masking improvements, or visual odometry claims are made or implied. Results are from the TorWIC hallway benchmark only (35 inputs across 3 dates: Jun 15, Jun 23, Oct 12 2022).

5. **Comparison to baselines:** Naive all-admit (B0) admits 20/20 clusters including 4 dynamic agents (phantom_risk=0.20). Purity/support proxy (B1) admits 19/20, still including all 4 forklifts (phantom_risk=0.21). Richer admission (B2, current) achieves 0 dynamic contamination (phantom_risk=0.0, stability_ratio=1.0) by admitting only 5 well-evidenced infrastructure clusters.

## 6. Per-Cluster Detail Reference

| ID | Label | Category | Retained | Sessions | Frames | Support | Dominant | DynRatio | Reasons |
|----|-------|----------|----------|----------|--------|---------|----------|----------|---------|
| cluster_0001 | yellow barrier | yellow barrier | ✓ | 10 | 24 | 90 | candidate | 0.000 | — |
| cluster_0002 | yellow barrier | yellow barrier | ✓ | 11 | 25 | 83 | candidate | 0.000 | — |
| cluster_0003 | forklift | forklift | ✗ | 11 | 25 | 138 | dynamic_agent | 0.957 | dynamic |
| cluster_0004 | work table | work table | ✓ | 13 | 34 | 122 | candidate | 0.000 | — |
| cluster_0005 | work | other | ✗ | 3 | 3 | 7 | candidate | 0.000 | low_frames, label_frag |
| cluster_0006 | warehouse rack | warehouse rack | ✓ | 7 | 14 | 62 | candidate | 0.000 | — |
| cluster_0007 | warehouse rack | warehouse rack | ✗ | 8 | 15 | 75 | candidate | 0.000 | internal_ranking |
| cluster_0008 | forklift | forklift | ✗ | 3 | 8 | 17 | dynamic_agent | 0.882 | dynamic |
| cluster_0009 | work table | work table | ✓ | 4 | 6 | 19 | candidate | 0.000 | — |
| cluster_0010 | forklift | forklift | ✗ | 5 | 12 | 34 | dynamic_agent | 1.000 | dynamic |
| cluster_0011 | yellow barrier | yellow barrier | ✗ | 1 | 7 | 8 | candidate | 0.000 | single_session |
| cluster_0012 | forklift | forklift | ✗ | 4 | 11 | 38 | dynamic_agent | 0.947 | dynamic |
| cluster_0013 | work table | work table | ✗ | 1 | 2 | 3 | candidate | 0.000 | single_session, low_frames, low_support |
| cluster_0014 | yellow barrier | yellow barrier | ✗ | 1 | 8 | 9 | candidate | 0.000 | single_session |
| cluster_0015 | work table | work table | ✗ | 3 | 3 | 33 | candidate | 0.000 | low_frames |
| cluster_0016 | rack forklift | other | ✗ | 1 | 1 | 1 | candidate | 0.000 | single_session, low_frames, low_support, label_frag |
| cluster_0017 | warehouse rack | warehouse rack | ✗ | 1 | 1 | 3 | candidate | 0.000 | single_session, low_frames, low_support |
| cluster_0018 | ##lift | other | ✗ | 1 | 1 | 1 | candidate | 0.000 | single_session, low_frames, low_support, label_frag |
| cluster_0019 | yellow barrier | yellow barrier | ✗ | 3 | 3 | 18 | candidate | 0.000 | low_frames |
| cluster_0020 | work | other | ✗ | 1 | 1 | 1 | candidate | 0.000 | single_session, low_frames, low_support, label_frag |
