# Submission-Grade Statistical Formalization — P174

**Phase:** P174-statistical-formalization-for-submission
**Date:** 2026-05-10
**Policy:** Existing-data-only. No downloads. No GPU.

---

## 1. Semantic Map Admission Rates

**Unit:** Cross-session semantic cluster

**Method:** Bootstrap percentile 95% CI (10,000 resamples) + Wilson score 95% CI

### Per-Protocol Admission

| Protocol | Clusters | Admitted | Rejected | Rate | Bootstrap 95% CI | Wilson 95% CI |
|---|---|---|---|---|---|---|
| Same-day Aisle | 11 | 5 | 6 | 45.5% | 18.2–72.7% | 21.3–72.0% |
| Cross-day Aisle | 10 | 5 | 5 | 50.0% | 20.0–80.0% | 23.7–76.3% |
| Cross-month Aisle | 14 | 7 | 7 | 50.0% | 21.4–78.6% | 26.8–73.2% |
| Hallway broader validation | 16 | 9 | 7 | 56.2% | 31.2–81.2% | 33.2–76.9% |
| **Pooled** | **51** | **26** | **25** | **51.0%** | **37.3–64.7%** | **37.7–64.1%** |

### Retained Composition

- **Same-day Aisle (45.5%):** 5 clusters — 3×barrier, 1×work table, 1×warehouse rack
- **Cross-day Aisle (50.0%):** 5 clusters — 2×barrier, 2×warehouse rack, 1×work table
- **Cross-month Aisle (50.0%):** 7 clusters — 3×barrier, 2×work table, 2×warehouse rack
- **Hallway broader validation (56.2%):** 9 clusters — 4×barrier, 4×work table, 1×warehouse rack

### Hallway vs Aisle

- **Fisher exact (two-sided):** Aisle pooled 17/35 (48.6%) vs Hallway 9/16 (56.2%)
- **p = 0.7645** — No evidence of difference. Hallway validates Aisle admission regime.

### Label Purity

- Mean purity: 94.7% (bootstrap 95% CI: 92.2–97.2%)
- **n = 26** retained clusters
- *Note:* High purity is a consequence of the admission criteria, not an independent finding.

---

## 2. Dynamic SLAM Statistics

**Unit:** DROID-SLAM configuration (64-frame, global BA)
**Total:** 16 configurations (11 neutral, 5 perturbed)

### Neutral Rate

- Observed: 11/16 = 68.8%
- Bootstrap 95% CI: [43.8%–87.5%]
- Wilson 95% CI: [44.4%–85.8%]

### Two-Group ΔAPE

| Group | n | ΔAPE Range (mm) | Mean (mm) | Bootstrap 95% CI (mm) |
|---|---|---|---|---|
| Neutral | 11 | -0.002–0.006 | 9.1e-05 | [-0.000818–0.001455] |
| Perturbed | 5 | 0.92–7.517 | 3.5594 | [0.9208–6.198] |

- **Group separation gap:** 0.914 mm
- Complete separation at |ΔAPE| ≤ 0.006 mm boundary. No overlap between groups.

### Interpretation

Bootstrap 95% CI for neutral rate [43.8%–87.5%] supports a majority-neutral claim but does not exclude the possibility of ≤50% neutral rate. The evidence supports "mask selectivity is a necessary condition for trajectory neutrality" but not "selective masking always guarantees neutrality."

---

## 3. Limitations

1. **No B0/B1/B2 Fisher tests:** Per-baseline per-cluster admission flags not exported. Fisher exact between baselines was planned but cannot be computed with current data.
2. **Small cluster counts per protocol:** n = 10–16 clusters → wide CIs.
3. **Dynamic SLAM sample size:** 16 configurations is small for rate estimation. CI lower bound crosses 50%.
4. **No covariate modeling:** Logistic regression for within-protocol covariates (dynamic_ratio, session_count) would require n=10–16 clusters and is underpowered.
5. **Cluster-level exchangeability assumed:** Session-level clustering not modeled in bootstrap.

---

*Statistical formalization completed 2026-05-10. JSON source: `paper/evidence/submission_statistics_p174.json`.*
