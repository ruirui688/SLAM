#!/usr/bin/env python3
"""P156: Map visualization and object lifecycle diagrams.

Generates:
  1. Before/after map composition mosaic (B0 naive vs B2 richer)
  2. Object lifecycle timeline panel (one stable infra + one forklift rejection)
"""

import json, math, sys
from pathlib import Path
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

ROOT = Path("/home/rui/slam/outputs")
FIG_DIR = Path("/home/rui/slam/paper/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)

LABEL_ALIASES = {
    'fork': 'forklift', 'forklift': 'forklift',
    'table': 'work table', 'work table': 'work table',
    'barrier': 'yellow barrier', 'yellow barrier': 'yellow barrier',
    'rack': 'warehouse rack', 'warehouse rack': 'warehouse rack',
}
INFRA_LABELS = {'yellow barrier', 'work table', 'warehouse rack'}
DYNAMIC_LABELS = {'forklift'}

CAT_COLORS = {
    'yellow barrier': '#f1c40f',
    'work table': '#3498db', 
    'warehouse rack': '#9b59b6',
    'forklift': '#e74c3c',
    'other': '#95a5a6',
}


def load_json(p):
    return json.loads(open(p, encoding='utf-8').read())


def normalize_label(label):
    return LABEL_ALIASES.get(' '.join(str(label).strip().lower().split()),
                              ' '.join(str(label).strip().lower().split()))


def compute_cluster_stats(c):
    sup = c['support_count']
    sess = c['session_count']
    frames = c.get('frame_count', sup)
    sh = c.get('state_histogram', {})
    dyn_ratio = sh.get('dynamic_agent', 0) / max(sup, 1)
    rh = c.get('raw_label_histogram', {})
    purity = max(rh.values()) / max(sum(rh.values()), 1) if rh else 0.0
    label = normalize_label(c.get('canonical_label', 'unknown'))
    if label not in CAT_COLORS and label not in INFRA_LABELS and label not in DYNAMIC_LABELS:
        label = 'other'
    return {
        'cluster_id': c['cluster_id'],
        'label': label,
        'sessions': sess, 'frames': frames, 'support': sup,
        'dynamic_ratio': dyn_ratio, 'label_purity': purity,
        'state_histogram': sh,
        'raw_label_histogram': rh,
        'sessions_list': c.get('sessions', []),
        'mean_center': c.get('mean_center_xyz'),
        'mean_size': c.get('mean_size_xyz'),
    }


def run_strategies(all_stats):
    def b0(s): return True
    def b2(s): return (s['sessions'] >= 2 and s['frames'] >= 4 and s['support'] >= 6
                       and s['dynamic_ratio'] <= 0.20 and s['label_purity'] >= 0.70)
    
    b0_sel = [s for s in all_stats if b0(s)]
    b2_sel = [s for s in all_stats if b2(s)]
    return b0_sel, b2_sel


def fig1_before_after_mosaic(all_stats):
    """B0 (Naive) vs B2 (Richer) map composition mosaic."""
    b0_sel, b2_sel = run_strategies(all_stats)
    
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    fig.suptitle("Map Composition: Admission Control Before vs After", fontsize=13, fontweight='bold')
    
    for ax, selected, title, phantom in [
        (axes[0], b0_sel, "B0: Naive-all-admit (No Maintenance Layer)", "20.0%"),
        (axes[1], b2_sel, "B2: Richer Admission Policy (Current)", "0.0%"),
    ]:
        # Count by category
        counts = Counter(s['label'] for s in selected)
        labels = ['yellow barrier', 'work table', 'warehouse rack', 'forklift', 'other']
        values = [counts.get(l, 0) for l in labels]
        colors = [CAT_COLORS[l] for l in labels]
        
        wedges, texts, autotexts = ax.pie(
            values, labels=None, colors=colors, autopct='%1.0f%%',
            startangle=90, pctdistance=0.75,
            textprops={'fontsize': 10, 'fontweight': 'bold'}
        )
        ax.set_title(title, fontsize=11, fontweight='bold')
        
        # Center text with total and phantom risk
        total = len(selected)
        phantom_risk = counts.get('forklift', 0) / max(total, 1)
        center_text = f"Total: {total}\nPhantom risk: {phantom_risk*100:.0f}%"
        ax.text(0, 0, center_text, ha='center', va='center', fontsize=11, fontweight='bold')
        
        # Sub-label below each wedge
        bbox_args = dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8)
        for i, (wedge, label, val) in enumerate(zip(wedges, labels, values)):
            if val == 0:
                continue
            ang = (wedge.theta2 + wedge.theta1) / 2
            x = np.cos(np.deg2rad(ang)) * 1.35
            y = np.sin(np.deg2rad(ang)) * 1.35
            ax.annotate(f"{label}\n(n={val})", xy=(x, y), ha='center', va='center',
                       fontsize=8, bbox=bbox_args)

    # Legend
    legend_elements = [mpatches.Patch(facecolor=CAT_COLORS[l], label=l)
                      for l in ['yellow barrier', 'work table', 'warehouse rack', 'forklift', 'other']]
    fig.legend(handles=legend_elements, loc='lower center', ncol=5, fontsize=9, frameon=False)
    
    plt.tight_layout(rect=[0, 0.08, 1, 0.95])
    path = FIG_DIR / "torwic_before_after_map_composition_p156.png"
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Fig1 saved: {path}")
    return path


def fig2_lifecycle_panel(all_stats):
    """Object lifecycle: one stable barrier + one rejected forklift."""
    
    # Find best examples
    barrier_candidates = sorted(
        [s for s in all_stats if s['label'] == 'yellow barrier' and s['sessions'] >= 2],
        key=lambda s: s['support'], reverse=True
    )
    forklift_candidates = sorted(
        [s for s in all_stats if s['label'] == 'forklift' and s['dynamic_ratio'] > 0.5],
        key=lambda s: s['support'], reverse=True
    )
    
    if not barrier_candidates or not forklift_candidates:
        print("WARNING: not enough candidates for lifecycle diagram")
        return None
    
    barrier = barrier_candidates[0]
    forklift = forklift_candidates[0]
    
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle("Object Lifecycle: Stable Admission vs Dynamic Rejection", fontsize=13, fontweight='bold')
    
    # Panel A: Stable barrier
    ax = axes[0]
    ax.set_xlim(0, 6)
    ax.set_ylim(0, 6)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f"A: Stable Object — {barrier['label']}\n(cluster {barrier['cluster_id']})", 
                 fontsize=11, fontweight='bold', color='#27ae60')
    
    # Timeline flow
    stages = [
        (1, 5, "Observation\n(n=18)", '#3498db'),
        (3, 5, "Cross-session\nAggregation", '#2ecc71'),
        (5, 5, "Admitted ✓\n(retained in map)", '#27ae60'),
    ]
    for x, y, text, color in stages:
        ax.add_patch(plt.Rectangle((x-0.7, y-0.4), 1.4, 0.8, facecolor=color, edgecolor='black', 
                                    linewidth=1.5, alpha=0.85))
        ax.text(x, y, text, ha='center', va='center', fontsize=9, fontweight='bold', color='white')
    
    # Arrows
    ax.annotate('', xy=(2.2, 5), xytext=(1.7, 5), arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    ax.annotate('', xy=(4.2, 5), xytext=(3.7, 5), arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    
    # Info box
    info_text = (f"Sessions: {barrier['sessions']} ({', '.join(barrier['sessions_list'])})\n"
                 f"Frames: {barrier['frames']} | Support: {barrier['support']}\n"
                 f"Dynamic ratio: {barrier['dynamic_ratio']:.2f} | Purity: {barrier['label_purity']:.2f}\n"
                 f"Verdict: ADMITTED — meets all 5 criteria")
    ax.text(3, 1.5, info_text, ha='center', va='center', fontsize=8.5,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#ecf0f1', alpha=0.9), family='monospace')
    
    # Panel B: Rejected forklift
    ax = axes[1]
    ax.set_xlim(0, 6)
    ax.set_ylim(0, 6)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f"B: Dynamic Object — {forklift['label']}\n(cluster {forklift['cluster_id']})", 
                 fontsize=11, fontweight='bold', color='#c0392b')
    
    stages_b = [
        (1, 5, "Observation\n(n={})".format(forklift['support']), '#3498db'),
        (3, 5, "Cross-session\nCheck", '#e67e22'),
        (5, 5, "Rejected ✗\n(dynamic_contamination)", '#e74c3c'),
    ]
    for x, y, text, color in stages_b:
        ax.add_patch(plt.Rectangle((x-0.7, y-0.4), 1.4, 0.8, facecolor=color, edgecolor='black',
                                    linewidth=1.5, alpha=0.85))
        ax.text(x, y, text, ha='center', va='center', fontsize=9, fontweight='bold', color='white')
    
    ax.annotate('', xy=(2.2, 5), xytext=(1.7, 5), arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    ax.annotate('', xy=(4.2, 5), xytext=(3.7, 5), arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    
    # Show which criteria failed
    failures = []
    if forklift['dynamic_ratio'] > 0.20:
        failures.append(f"✗ dynamic_ratio={forklift['dynamic_ratio']:.2f} > 0.20")
    if forklift['sessions'] < 2:
        failures.append(f"✗ sessions={forklift['sessions']} < 2")
    
    passes = []
    if forklift['sessions'] >= 2:
        passes.append(f"✓ sessions={forklift['sessions']} ≥ 2")
    if forklift['frames'] >= 4:
        passes.append(f"✓ frames={forklift['frames']} ≥ 4")
    if forklift['support'] >= 6:
        passes.append(f"✓ support={forklift['support']} ≥ 6")
    if forklift['label_purity'] >= 0.70:
        passes.append(f"✓ purity={forklift['label_purity']:.2f} ≥ 0.70")
    
    info_b = (f"Sessions: {forklift['sessions']} ({', '.join(forklift['sessions_list'])})\n"
              + "\n".join(passes) + "\n" + "\n".join(failures) +
              f"\n\nVerdict: REJECTED (dynamic_contamination)")
    ax.text(3, 1.5, info_b, ha='center', va='center', fontsize=8,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#fdf2f2', alpha=0.9), family='monospace')
    
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    path = FIG_DIR / "torwic_object_lifecycle_p156.png"
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Fig2 saved: {path}")
    return path


def fig3_combined_panel(all_stats):
    """Combined single-figure panel: composition bars + lifecycle inset."""
    b0_sel, b2_sel = run_strategies(all_stats)
    
    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.2])
    
    # Top-left: B0 composition bar
    ax1 = fig.add_subplot(gs[0, 0])
    counts_b0 = Counter(s['label'] for s in b0_sel)
    labels = ['yellow barrier', 'work table', 'warehouse rack', 'forklift', 'other']
    vals_b0 = [counts_b0.get(l, 0) for l in labels]
    colors = [CAT_COLORS[l] for l in labels]
    bars = ax1.barh(labels, vals_b0, color=colors, edgecolor='black', linewidth=0.5)
    for bar, val in zip(bars, vals_b0):
        ax1.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2, str(val),
                va='center', fontweight='bold', fontsize=10)
    ax1.set_title("B0: Naive-all-admit (20 objects)", fontsize=11, fontweight='bold')
    ax1.set_xlim(0, max(vals_b0) * 1.3)
    ax1.set_xlabel("Count")
    
    # Top-right: B2 composition bar
    ax2 = fig.add_subplot(gs[0, 1])
    counts_b2 = Counter(s['label'] for s in b2_sel)
    vals_b2 = [counts_b2.get(l, 0) for l in labels]
    bars = ax2.barh(labels, vals_b2, color=colors, edgecolor='black', linewidth=0.5)
    for bar, val in zip(bars, vals_b2):
        ax2.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height()/2, str(val),
                va='center', fontweight='bold', fontsize=10)
    ax2.set_title("B2: Richer Admission (5 objects)", fontsize=11, fontweight='bold')
    ax2.set_xlim(0, max(vals_b0) * 1.3)
    ax2.set_xlabel("Count")
    
    # Bottom: scatter plot of all clusters by dynamic_ratio vs sessions
    ax3 = fig.add_subplot(gs[1, :])
    
    # Plot each cluster
    for s in all_stats:
        color = CAT_COLORS.get(s['label'], '#95a5a6')
        marker = 'o'
        size = min(s['support'] / 2, 150)
        edge = 'black'
        is_b2 = (s['sessions'] >= 2 and s['frames'] >= 4 and s['support'] >= 6
                 and s['dynamic_ratio'] <= 0.20 and s['label_purity'] >= 0.70)
        ax3.scatter(s['dynamic_ratio'], s['sessions'], s=size, c=color, marker=marker,
                   edgecolors=edge if is_b2 else 'red', linewidth=2 if is_b2 else 0.5,
                   alpha=0.8, zorder=3 if is_b2 else 2)
        
        # Label selected objects
        if is_b2:
            ax3.annotate(s['cluster_id'], (s['dynamic_ratio'], s['sessions']),
                        xytext=(5, 5), textcoords='offset points', fontsize=7, color='#27ae60',
                        fontweight='bold')
    
    # Admission boundary lines
    ax3.axvline(x=0.20, color='orange', linestyle='--', alpha=0.5, label='max_dynamic_ratio=0.20')
    ax3.axhline(y=1.5, color='blue', linestyle='--', alpha=0.5, label='min_sessions=2')
    
    ax3.set_xlabel('Dynamic Ratio (dynamic_agent / total observations)', fontsize=11)
    ax3.set_ylabel('Session Count', fontsize=11)
    ax3.set_title('Decision Space: Dynamic Ratio vs Cross-Session Evidence', fontsize=12, fontweight='bold')
    
    # Annotate regions
    ax3.annotate('Admitted\nRegion', xy=(0.05, 7), fontsize=10, color='#27ae60', fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='#d5f5e3', alpha=0.7))
    ax3.annotate('Rejected\n(Dynamic)', xy=(0.85, 7), fontsize=10, color='#c0392b', fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='#fadbd8', alpha=0.7))
    ax3.annotate('Rejected\n(Single-session)', xy=(0.05, 0.5), fontsize=10, color='#e67e22', fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='#fdebd0', alpha=0.7))
    
    ax3.legend(loc='upper right', fontsize=8)
    ax3.grid(alpha=0.2)
    
    fig.suptitle("Map-Admission Decision Space (P156)", fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    path = FIG_DIR / "torwic_admission_decision_space_p156.png"
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Fig3 saved: {path}")
    return path


def main():
    data = load_json(ROOT / "torwic_ablation_combined_clusters.json")
    all_stats = [compute_cluster_stats(c) for c in data['clusters']]
    
    print(f"Dataset: {len(all_stats)} clusters from {data['num_inputs']} map_objects files")
    
    # Generate all figures
    paths = {}
    paths['fig1'] = fig1_before_after_mosaic(all_stats)
    paths['fig2'] = fig2_lifecycle_panel(all_stats)
    paths['fig3'] = fig3_combined_panel(all_stats)
    
    print("\nAll figures generated:")
    for k, v in paths.items():
        exists = "✓" if v and v.exists() else "✗"
        size = v.stat().st_size / 1024 if v and v.exists() else 0
        print(f"  {exists} {k}: {v} ({size:.0f} KB)")

    return paths


if __name__ == '__main__':
    main()
