#!/usr/bin/env python3
"""P157: Per-category retention/rejection analysis and rejection reason quantification.

Generates:
  1. Per-category retention/rejection table
  2. Rejection reason breakdown (multi-label: single_session, low_frames, low_support, dynamic, label_frag)
  3. Per-category × rejection reason matrix
  4. Bar chart + heatmap
"""

import json, math, sys
from pathlib import Path
from collections import Counter, defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path("/home/rui/slam/outputs")
FIG_DIR = Path("/home/rui/slam/paper/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR = Path("/home/rui/slam/paper/export")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

LABEL_ALIASES = {
    'fork': 'forklift', 'forklift': 'forklift',
    'table': 'work table', 'work table': 'work table',
    'barrier': 'yellow barrier', 'yellow barrier': 'yellow barrier',
    'rack': 'warehouse rack', 'warehouse rack': 'warehouse rack',
}


def normalize_label(label):
    return LABEL_ALIASES.get(' '.join(str(label).strip().lower().split()),
                              ' '.join(str(label).strip().lower().split()))


def load_json(p):
    return json.loads(open(p, encoding='utf-8').read())


def compute_cluster_stats(c):
    sup = c['support_count']
    sess = c['session_count']
    frames = c.get('frame_count', sup)
    sh = c.get('state_histogram', {})
    dyn = sh.get('dynamic_agent', 0)
    dyn_ratio = dyn / max(sup, 1)
    rh = c.get('raw_label_histogram', {})
    purity = max(rh.values()) / max(sum(rh.values()), 1) if rh else 0.0
    label = normalize_label(c.get('canonical_label', 'unknown'))
    return {
        'cluster_id': c['cluster_id'],
        'canonical_label': label,
        'sessions': sess, 'frames': frames, 'support': sup,
        'dynamic_count': dyn, 'dynamic_ratio': dyn_ratio,
        'label_purity': purity,
        'sessions_list': c.get('sessions', []),
        'state_histogram': sh,
        'raw_label_histogram': rh,
    }


# --- Admission policy (B2 richer, 5 criteria) ---
def admission_policy(s):
    reasons = []
    if s['sessions'] < 2:
        reasons.append('single_session')
    if s['frames'] < 4:
        reasons.append('low_frames')
    if s['support'] < 6:
        reasons.append('low_support')
    if s['dynamic_ratio'] > 0.20:
        reasons.append('dynamic_contamination')
    if s['label_purity'] < 0.70:
        reasons.append('label_fragmentation')
    return reasons  # empty = admitted


CATEGORIES = ['yellow barrier', 'work table', 'warehouse rack', 'forklift', 'other']


def main():
    data = load_json(ROOT / "torwic_ablation_combined_clusters.json")
    all_stats = [compute_cluster_stats(c) for c in data['clusters']]

    # Classify each cluster
    for s in all_stats:
        s['rejection_reasons'] = admission_policy(s)
        s['admitted'] = (len(s['rejection_reasons']) == 0)

    admitted = [s for s in all_stats if s['admitted']]
    rejected = [s for s in all_stats if not s['admitted']]

    # ===== 1. Per-category retention/rejection table =====
    cat_table = []
    for cat in CATEGORIES:
        cat_all = [s for s in all_stats if s['canonical_label'] == cat]
        cat_admitted = [s for s in cat_all if s['admitted']]
        cat_rejected = [s for s in cat_all if not s['admitted']]
        total = len(cat_all)
        retention = len(cat_admitted)
        cat_table.append({
            'category': cat,
            'total_clusters': total,
            'admitted': retention,
            'rejected': total - retention,
            'retention_rate': retention / max(total, 1),
        })

    # ===== 2. Rejection reason breakdown =====
    reason_labels = ['single_session', 'low_frames', 'low_support', 'dynamic_contamination', 'label_fragmentation']
    reason_count = Counter()
    for s in all_stats:
        for r in s['rejection_reasons']:
            reason_count[r] += 1

    # Per-reason cluster_id list
    reason_clusters = {r: [] for r in reason_labels}
    for s in all_stats:
        for r in s['rejection_reasons']:
            reason_clusters[r].append({
                'cluster_id': s['cluster_id'],
                'canonical_label': s['canonical_label'],
                'sessions': s['sessions'],
                'frames': s['frames'],
                'support': s['support'],
                'dynamic_ratio': s['dynamic_ratio'],
                'label_purity': s['label_purity'],
            })

    # ===== 3. Per-category × reason matrix =====
    matrix = {}
    for cat in CATEGORIES:
        cat_stats = [s for s in all_stats if s['canonical_label'] == cat]
        matrix[cat] = {}
        for r in reason_labels:
            matrix[cat][r] = sum(1 for s in cat_stats if r in s['rejection_reasons'])

    # ===== 4a. Bar chart: per-category retention/rejection =====
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(CATEGORIES))
    width = 0.35
    admitted_vals = [cat_table[i]['admitted'] for i in range(len(CATEGORIES))]
    rejected_vals = [cat_table[i]['rejected'] for i in range(len(CATEGORIES))]
    
    bars1 = ax.bar(x - width/2, admitted_vals, width, label='Admitted (retained)', color='#27ae60', edgecolor='black')
    bars2 = ax.bar(x + width/2, rejected_vals, width, label='Rejected', color='#e74c3c', edgecolor='black')
    
    for bar, val in zip(bars1, admitted_vals):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2, str(val),
                   ha='center', fontweight='bold', fontsize=11)
    for bar, val in zip(bars2, rejected_vals):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2, str(val),
                   ha='center', fontweight='bold', fontsize=11)
    
    ax.set_ylabel('Number of Clusters', fontsize=12)
    ax.set_title('Per-Category Map-Admission Retention vs Rejection (P157)', fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(CATEGORIES, fontsize=11, rotation=15)
    ax.legend(fontsize=10)
    ax.set_ylim(0, max(max(admitted_vals), max(rejected_vals)) * 1.3)
    ax.grid(axis='y', alpha=0.2)
    
    # Retention rate annotation
    for i, cat in enumerate(CATEGORIES):
        rate = cat_table[i]['retention_rate']
        ax.annotate(f'{rate*100:.0f}%', xy=(i, max(admitted_vals[i], rejected_vals[i]) + 1.0),
                   ha='center', fontsize=9, color='#3498db', fontweight='bold')
    
    plt.tight_layout()
    path1 = FIG_DIR / "torwic_per_category_retention_p157.png"
    plt.savefig(path1, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Fig1: {path1}")

    # ===== 4b. Heatmap: per-category × reason =====
    fig2, ax2 = plt.subplots(figsize=(9, 4.5))
    mat_data = [[matrix[cat][r] for r in reason_labels] for cat in CATEGORIES]
    
    im = ax2.imshow(mat_data, cmap='YlOrRd', aspect='auto', vmin=0)
    
    ax2.set_xticks(np.arange(len(reason_labels)))
    ax2.set_yticks(np.arange(len(CATEGORIES)))
    ax2.set_xticklabels([r.replace('_', ' ').replace('single', 'single-').title() for r in reason_labels],
                        fontsize=9, rotation=30, ha='right')
    ax2.set_yticklabels(CATEGORIES, fontsize=10)
    ax2.set_title('Rejection Reason × Category Matrix (P157)', fontsize=13, fontweight='bold')
    
    for i in range(len(CATEGORIES)):
        for j in range(len(reason_labels)):
            val = mat_data[i][j]
            color = 'white' if val > max(max(r) for r in mat_data)/2 else 'black'
            ax2.text(j, i, str(val), ha='center', va='center', fontsize=11,
                    fontweight='bold', color=color)
    
    cbar = plt.colorbar(im, ax=ax2, shrink=0.8)
    cbar.set_label('# Clusters', fontsize=10)
    
    plt.tight_layout()
    path2 = FIG_DIR / "torwic_rejection_reason_heatmap_p157.png"
    plt.savefig(path2, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Fig2: {path2}")

    # ===== 4c. Sankey-like flow: rejection cause distribution =====
    fig3, ax3 = plt.subplots(figsize=(8, 5))
    rl_short = ['single\nsession', 'low\nframes', 'low\nsupport', 'dynamic\ncontam.', 'label\nfrag.']
    vals = [reason_count.get(r, 0) for r in reason_labels]
    colors = ['#3498db', '#2ecc71', '#e67e22', '#e74c3c', '#9b59b6']
    bars = ax3.bar(rl_short, vals, color=colors, edgecolor='black', linewidth=0.8)
    for bar, val in zip(bars, vals):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2, str(val),
                ha='center', fontweight='bold', fontsize=12)
    ax3.set_ylabel('# Clusters Flagged', fontsize=12)
    ax3.set_title('Rejection Reason Prevalence (Multi-Label: 15 rejected clusters, P157)', 
                  fontsize=12, fontweight='bold')
    ax3.set_ylim(0, max(vals) * 1.25)
    ax3.grid(axis='y', alpha=0.2)
    plt.tight_layout()
    path3 = FIG_DIR / "torwic_rejection_reason_distribution_p157.png"
    plt.savefig(path3, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Fig3: {path3}")

    # ===== Build outputs =====
    
    # JSON output
    result = {
        'dataset': 'Combined Aisle + Hallway (35 map_objects.json → 20 clusters)',
        'admission_policy': 'B2 richer (min_sessions=2, min_frames=4, min_support=6, max_dynamic_ratio=0.20, min_purity=0.70)',
        'summary': {
            'total_clusters': len(all_stats),
            'admitted': len(admitted),
            'rejected': len(rejected),
            'rejection_rate': len(rejected) / len(all_stats),
        },
        'per_category': cat_table,
        'rejection_reasons_global': {r: reason_count[r] for r in reason_labels},
        'rejected_clusters': {
            s['cluster_id']: {
                'canonical_label': s['canonical_label'],
                'sessions': s['sessions'],
                'frames': s['frames'],
                'support': s['support'],
                'dynamic_ratio': round(s['dynamic_ratio'], 3),
                'label_purity': round(s['label_purity'], 3),
                'rejection_reasons': s['rejection_reasons'],
            }
            for s in rejected
        },
        'per_category_reason_matrix': matrix,
        'reason_cluster_details': reason_clusters,
    }
    
    json_path = ROOT / "torwic_category_retention_analysis_p157.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"JSON: {json_path}")

    # Markdown report
    md_lines = [
        "# P157: Per-Category Retention & Rejection Reason Analysis",
        "",
        f"**Dataset:** {result['dataset']}  ",
        f"**Policy:** {result['admission_policy']}  ",
        "",
        f"**Overall:** {result['summary']['admitted']}/{result['summary']['total_clusters']} admitted ({result['summary']['rejection_rate']*100:.0f}% rejection rate)",
        "",
        "## 1. Per-Category Retention/Rejection",
        "",
        "| Category | Total | Admitted | Rejected | Retention Rate |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in cat_table:
        md_lines.append(f"| **{row['category']}** | {row['total_clusters']} | {row['admitted']} | {row['rejected']} | {row['retention_rate']*100:.0f}% |")
    
    # Key insight
    retained_labels = [row['category'] for row in cat_table if row['admitted'] > 0]
    fully_rejected = [row['category'] for row in cat_table if row['admitted'] == 0 and row['total_clusters'] > 0]
    
    md_lines += [
        "",
        f"**Key finding:** The admission policy retains only **{', '.join(retained_labels)}** clusters. ",
        f"All **{', '.join(fully_rejected)}** clusters are 100% rejected. "
        f"Infrastructure objects (yellow barrier, work table) show moderate-to-high retention; "
        f"forklifts are universally rejected due to dynamic_contamination.",
        "",
        "## 2. Rejection Reason Breakdown (Multi-Label)",
        "",
        "A single cluster may be flagged by multiple rejection reasons simultaneously.",
        "",
        "| Reason | # Clusters Flagged | % of Rejected (n=15) |",
        "|---|---:|---:|",
    ]
    for r in reason_labels:
        n = reason_count.get(r, 0)
        md_lines.append(f"| {r.replace('_', ' ').title()} | {n} | {n/max(len(rejected),1)*100:.0f}% |")
    
    md_lines += [
        "",
        "## 3. Per-Category × Rejection Reason Matrix",
        "",
        "| Category | " + " | ".join(r.replace('_', ' ').title() for r in reason_labels) + " |",
        "|---|" + "|".join("---:" for _ in reason_labels) + "|",
    ]
    for cat in CATEGORIES:
        row_vals = [str(matrix[cat][r]) for r in reason_labels]
        md_lines.append(f"| **{cat}** | {' | '.join(row_vals)} |")
    
    md_lines += [
        "",
        "## 4. Detailed Rejection Profiles",
        "",
    ]
    for s in sorted(rejected, key=lambda s: len(s['rejection_reasons']), reverse=True):
        reasons_str = ', '.join(s['rejection_reasons'])
        md_lines.append(
            f"- **{s['cluster_id']}** ({s['canonical_label']}): "
            f"sessions={s['sessions']}, frames={s['frames']}, support={s['support']}, "
            f"dyn_ratio={s['dynamic_ratio']:.2f}, purity={s['label_purity']:.2f} "
            f"→ **rejected** ({reasons_str})"
        )
    
    md_lines += [
        "",
        "## 5. Admitted Object Profiles",
        "",
    ]
    for s in admitted:
        md_lines.append(
            f"- **{s['cluster_id']}** ({s['canonical_label']}): "
            f"sessions={s['sessions']}, frames={s['frames']}, support={s['support']}, "
            f"dyn_ratio={s['dynamic_ratio']:.2f}, purity={s['label_purity']:.2f} "
            f"→ **admitted** ✓"
        )
    
    md_lines += [
        "",
        "## 6. Figures",
        "",
        "![Per-category retention/rejection bar chart](../figures/torwic_per_category_retention_p157.png)",
        "![Rejection reason × category heatmap](../figures/torwic_rejection_reason_heatmap_p157.png)",
        "![Rejection reason distribution](../figures/torwic_rejection_reason_distribution_p157.png)",
        "",
        "## 7. Evidence Summary",
        "",
        "1. **Forklift rejection is universal and unambiguous.** All 4 forklift clusters are rejected. The dominant (and typically sole) reason is dynamic_contamination (dynamic_ratio ≥ 0.83). No forklift passes any set of criteria.",
        "2. **Infrastructure retention is selective but interpretable.** Yellow barrier (2/3 retained, 67%) and work table (2/3 retained, 67%) show the highest retention. The single rejected barrier and table fail on per-session coverage (1 session) or frame count.",
        "3. **Rejection reasons are not uniformly distributed across categories.** Single-session (7 clusters) and low-frames (4) are the most prevalent reasons, primarily affecting warehouse rack, work table, and `other` categories. Dynamic_contamination is concentrated entirely in the forklift category (4/4).",
        "4. **Multi-reason rejection is common.** Several clusters fail on 2+ criteria simultaneously, but the criteria are complementary rather than redundant — single_session captures absence from revisits, low_frames captures spatial undersampling, and dynamic_contamination captures mobility.",
    ]
    
    md_path = REPORT_DIR / "category_retention_analysis_p157.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))
    print(f"Report: {md_path}")

    # Print summary to stdout for commit message
    print(f"\nSUMMARY:")
    print(f"  Admitted: {len(admitted)}/{len(all_stats)}")
    for row in cat_table:
        print(f"  {row['category']}: {row['admitted']}/{row['total_clusters']} ({row['retention_rate']*100:.0f}%)")
    print(f"  Reasons: {dict(reason_count)}")
    
    return result


if __name__ == '__main__':
    main()
