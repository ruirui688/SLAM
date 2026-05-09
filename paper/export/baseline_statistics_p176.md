# Baseline Statistics — P176

**Phase:** P176-b3-baseline-statistics-closure  
**Date:** 2026-05-10  
**Verdict:** ✅ **B3 RESOLVED — per-baseline admission flags recovered and exact McNemar tests computed**

---

## Per-Baseline Admission (Aisle Ladder, 20 clusters)

| Baseline | Admitted | Total | Rate |
|---|---|---|---|
| B0 (Naive all-admit) | 20 | 20 | 100.0% |
| B1 (Purity/Support) | 9 | 20 | 45.0% |
| B2 (Richer, 5-criteria) | 5 | 20 | 25.0% |

## Exact McNemar Tests

| Comparison | Discordant pairs | Direction | p-value | Significant |
|---|---|---|---|---|
| B0 vs B1 | 11 | All 11 B0-admit B1-reject | 0.0010 | ✅ p < 0.05 |
| B1 vs B2 | 4 | All 4 B1-admit B2-reject | 0.125 | ❌ Not significant |
| B0 vs B2 | 15 | All 15 B0-admit B2-reject | <0.0001 | ✅ p < 0.05 |

**Method:** Exact McNemar test (two-sided binomial on discordant pairs).  
Each of the 20 Aisle clusters is a paired observation across all 3 baselines.

## Interpretation

- **B0 vs B1:** B1's purity/support criterion eliminates 11/20 clusters (p<0.001). The reduction is statistically significant, but B1 admits all 4 forklifts (21.1% phantom risk — worse than B0's 20.0%).
- **B1 vs B2:** 4 discordant clusters (2 forklifts FL-01/FL-02 + 2 single-session SS-04/SS-05). n=4 is too small for statistical significance (p=0.125), but the effect direction is deterministic (B2 never admits a cluster that B1 rejects; B1 admits 4 clusters B2 rejects). The practical importance — B2 eliminates phantom risk entirely — is not captured by significance alone.
- **B0 vs B2:** 15 discordant clusters (p<0.0001). B2's 75% reduction over B0 is strongly significant.

## Limitation

Sample size is small (n=20 Aisle clusters). With paired binary data and one-tailed discordance (every discordant pair goes in the same direction), p-values are bounded by 2×(0.5)^n_discordant. Meaningful effect sizes (75% admission reduction) are observable, but conventional significance thresholds require caution at small N.

## B3 Status

| Component | Status |
|---|---|
| Bootstrap CIs (admission rates) | ✅ P174 |
| Wilson CIs | ✅ P174 |
| Fisher exact (Hallway vs Aisle) | ✅ P174 |
| Dynamic SLAM neutral-rate CI + group separation | ✅ P174 |
| B0/B1/B2 McNemar (Aisle ladder) | ✅ P176 |
| Hallway baseline comparison | N/A (Hallway supplementary — no B0/B1 comparison designed) |
| **B3 overall** | **✅ RESOLVED** |

## Hallway

Hallway branch (16 clusters) has no per-baseline B0/B1/B2 comparison. B0/B1 baselines were designed for Aisle ladder only. Hallway admission (B2 only): 9/16 retained (56.2%). Hallway-vs-Aisle Fisher exact p=0.7645 (P174) — no evidence of difference.

---

*Closure evidence completed 2026-05-10. JSON source: `paper/evidence/baseline_statistics_p176.json`.*
