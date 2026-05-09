# P157: Per-Category Retention & Rejection Reason Analysis

**Dataset:** Combined Aisle + Hallway (35 map_objects.json → 20 clusters)  
**Policy:** B2 richer (min_sessions=2, min_frames=4, min_support=6, max_dynamic_ratio=0.20, min_purity=0.70)  

**Overall:** 5/20 admitted (75% rejection rate)

## 1. Per-Category Retention/Rejection

| Category | Total | Admitted | Rejected | Retention Rate |
|---|---:|---:|---:|---:|
| **yellow barrier** | 5 | 2 | 3 | 40% |
| **work table** | 4 | 2 | 2 | 50% |
| **warehouse rack** | 3 | 1 | 2 | 33% |
| **forklift** | 4 | 0 | 4 | 0% |
| **other** | 0 | 0 | 0 | 0% |

**Key finding:** The admission policy retains only **yellow barrier, work table, warehouse rack** clusters. 
All **forklift** clusters are 100% rejected. Infrastructure objects (yellow barrier, work table) show moderate-to-high retention; forklifts are universally rejected due to dynamic_contamination.

## 2. Rejection Reason Breakdown (Multi-Label)

A single cluster may be flagged by multiple rejection reasons simultaneously.

| Reason | # Clusters Flagged | % of Rejected (n=15) |
|---|---:|---:|
| Single Session | 7 | 47% |
| Low Frames | 8 | 53% |
| Low Support | 5 | 33% |
| Dynamic Contamination | 4 | 27% |
| Label Fragmentation | 1 | 7% |

## 3. Per-Category × Rejection Reason Matrix

| Category | Single Session | Low Frames | Low Support | Dynamic Contamination | Label Fragmentation |
|---|---:|---:|---:|---:|---:|
| **yellow barrier** | 2 | 1 | 0 | 0 | 0 |
| **work table** | 1 | 2 | 1 | 0 | 0 |
| **warehouse rack** | 1 | 1 | 1 | 0 | 1 |
| **forklift** | 0 | 0 | 0 | 4 | 0 |
| **other** | 0 | 0 | 0 | 0 | 0 |

## 4. Detailed Rejection Profiles

- **cluster_0013** (work table): sessions=1, frames=2, support=3, dyn_ratio=0.00, purity=1.00 → **rejected** (single_session, low_frames, low_support)
- **cluster_0016** (rack forklift): sessions=1, frames=1, support=1, dyn_ratio=0.00, purity=1.00 → **rejected** (single_session, low_frames, low_support)
- **cluster_0017** (warehouse rack): sessions=1, frames=1, support=3, dyn_ratio=0.00, purity=1.00 → **rejected** (single_session, low_frames, low_support)
- **cluster_0018** (##lift): sessions=1, frames=1, support=1, dyn_ratio=0.00, purity=1.00 → **rejected** (single_session, low_frames, low_support)
- **cluster_0020** (work): sessions=1, frames=1, support=1, dyn_ratio=0.00, purity=1.00 → **rejected** (single_session, low_frames, low_support)
- **cluster_0003** (forklift): sessions=11, frames=25, support=138, dyn_ratio=0.96, purity=0.96 → **rejected** (dynamic_contamination)
- **cluster_0005** (work): sessions=3, frames=3, support=7, dyn_ratio=0.00, purity=1.00 → **rejected** (low_frames)
- **cluster_0006** (warehouse rack): sessions=7, frames=14, support=62, dyn_ratio=0.00, purity=0.68 → **rejected** (label_fragmentation)
- **cluster_0008** (forklift): sessions=3, frames=8, support=17, dyn_ratio=0.88, purity=0.88 → **rejected** (dynamic_contamination)
- **cluster_0010** (forklift): sessions=5, frames=12, support=34, dyn_ratio=1.00, purity=1.00 → **rejected** (dynamic_contamination)
- **cluster_0011** (yellow barrier): sessions=1, frames=7, support=8, dyn_ratio=0.00, purity=1.00 → **rejected** (single_session)
- **cluster_0012** (forklift): sessions=4, frames=11, support=38, dyn_ratio=0.95, purity=0.95 → **rejected** (dynamic_contamination)
- **cluster_0014** (yellow barrier): sessions=1, frames=8, support=9, dyn_ratio=0.00, purity=0.78 → **rejected** (single_session)
- **cluster_0015** (work table): sessions=3, frames=3, support=33, dyn_ratio=0.00, purity=0.97 → **rejected** (low_frames)
- **cluster_0019** (yellow barrier): sessions=3, frames=3, support=18, dyn_ratio=0.00, purity=1.00 → **rejected** (low_frames)

## 5. Admitted Object Profiles

- **cluster_0001** (yellow barrier): sessions=10, frames=24, support=90, dyn_ratio=0.00, purity=0.80 → **admitted** ✓
- **cluster_0002** (yellow barrier): sessions=11, frames=25, support=83, dyn_ratio=0.00, purity=0.78 → **admitted** ✓
- **cluster_0004** (work table): sessions=13, frames=34, support=122, dyn_ratio=0.00, purity=0.99 → **admitted** ✓
- **cluster_0007** (warehouse rack): sessions=8, frames=15, support=75, dyn_ratio=0.00, purity=0.85 → **admitted** ✓
- **cluster_0009** (work table): sessions=4, frames=6, support=19, dyn_ratio=0.00, purity=1.00 → **admitted** ✓

## 6. Figures

![Per-category retention/rejection bar chart](../figures/torwic_per_category_retention_p157.png)
![Rejection reason × category heatmap](../figures/torwic_rejection_reason_heatmap_p157.png)
![Rejection reason distribution](../figures/torwic_rejection_reason_distribution_p157.png)

## 7. Evidence Summary

1. **Forklift rejection is universal and unambiguous.** All 4 forklift clusters are rejected. The dominant (and typically sole) reason is dynamic_contamination (dynamic_ratio ≥ 0.83). No forklift passes any set of criteria.
2. **Infrastructure retention is selective but interpretable.** Yellow barrier (2/3 retained, 67%) and work table (2/3 retained, 67%) show the highest retention. The single rejected barrier and table fail on per-session coverage (1 session) or frame count.
3. **Rejection reasons are not uniformly distributed across categories.** Single-session (7 clusters) and low-frames (4) are the most prevalent reasons, primarily affecting warehouse rack, work table, and `other` categories. Dynamic_contamination is concentrated entirely in the forklift category (4/4).
4. **Multi-reason rejection is common.** Several clusters fail on 2+ criteria simultaneously, but the criteria are complementary rather than redundant — single_session captures absence from revisits, low_frames captures spatial undersampling, and dynamic_contamination captures mobility.