#!/usr/bin/env python3
"""Generate P154 ablation visualization."""
import json, sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def load_json(p):
    return json.loads(open(p, encoding='utf-8').read())

data = load_json("/home/rui/slam/outputs/torwic_admission_ablation_results.json")
dr = data['default_result']
def_sel = dr['selected']
results = data['sweep_results']

fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
fig.suptitle("Admission Criteria Ablation — P154 Sensitivity Analysis", fontsize=13, fontweight='bold')

param_configs = [
    ('min_sessions', [1, 2, 3], 'min_sessions', axes[0]),
    ('min_frames', [2, 4, 6], 'min_frames', axes[1]),
    ('max_dynamic_ratio', [0.1, 0.2, 0.3], 'max_dynamic_ratio', axes[2]),
]

for param_name, values, title, ax in param_configs:
    rows = [r for r in results if r['param'] == param_name]
    x = np.arange(len(values))
    width = 0.35
    
    sel_vals = [r['selected'] for r in rows]
    rej_vals = [r['rejected'] for r in rows]
    
    bars1 = ax.bar(x - width/2, sel_vals, width, label='Selected (stable)', color='#2ecc71', edgecolor='#27ae60')
    bars2 = ax.bar(x + width/2, rej_vals, width, label='Rejected', color='#e74c3c', edgecolor='#c0392b')
    
    # Annotate
    for bar, val in zip(bars1, sel_vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3, str(val),
                ha='center', va='bottom', fontsize=10, fontweight='bold', color='#27ae60')
    
    # Mark default
    if param_name == 'min_sessions':
        default_idx = 1  # value=2
    elif param_name == 'min_frames':
        default_idx = 1  # value=4
    else:
        default_idx = 1  # value=0.2
    
    ax.axvspan(default_idx - 0.4, default_idx + 0.4, alpha=0.08, color='blue')
    ax.annotate('default', xy=(default_idx, sel_vals[default_idx] + 2),
                ha='center', fontsize=9, color='blue', fontweight='bold')
    
    ax.set_xlabel(title, fontsize=11)
    ax.set_ylabel('Cluster Count', fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels([str(v) for v in values])
    ax.set_title(f'Sensitivity: {title}', fontsize=11)
    ax.legend(fontsize=9)
    ax.set_ylim(0, max(sel_vals + rej_vals) + 5)
    ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
out_path = "/home/rui/slam/outputs/p154_admission_ablation_sensitivity.png"
plt.savefig(out_path, dpi=150, bbox_inches='tight')
print(f"Saved: {out_path}")

# Also create a text-based summary table
print("\nTEXT TABLE (for manuscript):")
print("Parameter        | Val1  | Val2  | Val3  | Sensitivity")
print("-----------------|-------|-------|-------|-------------")
for param_name, values, title, _ in param_configs:
    rows = [r for r in results if r['param'] == param_name]
    sel_str = " | ".join(f"sel={r['selected']}" for r in rows)
    is_sensitive = len(set(r['selected'] for r in rows)) > 1
    print(f"{title:<16s} | {sel_str:<30s} | {'SENSITIVE' if is_sensitive else 'INSENSITIVE'}")
