#!/usr/bin/env python3
"""
P154 admission criteria ablation — parameter sweep over existing data.

Builds a combined cross-session cluster file from all available Aisle + Hallway
map_objects.json files, then sweeps min_sessions/min_frames/max_dynamic_ratio
while holding min_support=6 and min_label_purity=0.7 constant.
"""

from __future__ import annotations
import json, math, sys
from pathlib import Path
from collections import Counter
from typing import Any

ROOT = Path("/home/rui/slam/outputs")
LABEL_ALIASES = {
    'fork': 'forklift', 'forklift': 'forklift',
    'table': 'work table', 'work table': 'work table',
    'barrier': 'yellow barrier', 'yellow barrier': 'yellow barrier',
    'rack': 'warehouse rack', 'warehouse rack': 'warehouse rack',
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def normalize_label(label: str) -> str:
    return LABEL_ALIASES.get(' '.join(str(label).strip().lower().split()), ' '.join(str(label).strip().lower().split()))


def center_of(obj: dict) -> list[float] | None:
    v = obj.get('geometry_profile', {}).get('reference_centroid_xyz')
    return [float(x) for x in v] if isinstance(v, list) and len(v) == 3 else None


def size_of(obj: dict) -> list[float] | None:
    v = obj.get('geometry_profile', {}).get('reference_bbox_size_xyz')
    return [float(x) for x in v] if isinstance(v, list) and len(v) == 3 else None


def euclidean(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def size_ratio_diff(a, b):
    return sum(abs(x - y) / max(abs(x), abs(y), 1e-6) for x, y in zip(a, b)) / len(a)


def mergeable(a, b, max_center_dist=220.0, max_size_ratio=0.55):
    if normalize_label(a.get('canonical_label', 'unknown')) != normalize_label(b.get('canonical_label', 'unknown')):
        return False
    ca, cb = center_of(a), center_of(b)
    if ca is None or cb is None:
        return False
    if euclidean(ca, cb) > max_center_dist:
        return False
    sa, sb = size_of(a), size_of(b)
    if sa is not None and sb is not None and size_ratio_diff(sa, sb) > max_size_ratio:
        return False
    return True


def summarize_cluster(cluster_id, items):
    labels, raw_labels, states = {}, {}, {}
    sessions, frames = set(), set()
    centers, sizes = [], []
    for item in items:
        label = normalize_label(item.get('canonical_label', 'unknown'))
        raw = str(item.get('canonical_label', 'unknown'))
        state = str(item.get('state', 'unknown'))
        labels[label] = labels.get(label, 0) + 1
        raw_labels[raw] = raw_labels.get(raw, 0) + 1
        states[state] = states.get(state, 0) + 1
        sessions.add(item.get('source_session', 'unknown'))
        frames.add(item.get('source_frame', 'unknown'))
        c = center_of(item)
        if c is not None:
            centers.append(c)
        s = size_of(item)
        if s is not None:
            sizes.append(s)
    mean_center = [sum(v) / len(v) for v in zip(*centers)] if centers else None
    mean_size = [sum(v) / len(v) for v in zip(*sizes)] if sizes else None
    return {
        'cluster_id': cluster_id, 'canonical_label': max(labels.items(), key=lambda kv: kv[1])[0] if labels else 'unknown',
        'dominant_state': max(states.items(), key=lambda kv: kv[1])[0] if states else 'unknown',
        'session_count': len(sessions), 'sessions': sorted(sessions),
        'frame_count': len(frames), 'support_count': len(items),
        'label_histogram': labels, 'raw_label_histogram': raw_labels,
        'state_histogram': states, 'mean_center_xyz': mean_center, 'mean_size_xyz': mean_size,
    }


def extract_session(path: Path) -> str:
    name = path.parent.parent.name
    for prefix, label in [('torwic_jun15', 'Jun15'), ('torwic_jun23', 'Jun23'), ('torwic_oct12', 'Oct12'),
                           ('hallway_benchmark_batch2_v1__2022-06-15', 'Jun15'),
                           ('hallway_recovery_pilot_v1__2022-06-15', 'Jun15'),
                           ('hallway_benchmark_batch2_v1__2022-06-23', 'Jun23'),
                           ('hallway_benchmark_batch2_v1__2022-10-12', 'Oct12')]:
        if name.startswith(prefix):
            return label
    return name


def build_clusters():
    paths = sorted(ROOT.glob('torwic_jun15_aisle_cw_run1_f*/map_output/map_objects.json'))
    paths += sorted(ROOT.glob('torwic_jun23_aisle_cw_run1_f*/map_output/map_objects.json'))
    paths += sorted(ROOT.glob('torwic_oct12_aisle_cw_f*/map_output/map_objects.json'))
    paths += sorted(ROOT.glob('torwic_hallway_*/map_output/map_objects.json'))

    items = []
    for path in paths:
        objs = load_json(path)
        source_session = extract_session(path)
        for obj in objs:
            x = dict(obj)
            x['source_session'] = source_session
            x['source_frame'] = path.parent.parent.name
            items.append(x)

    clusters = []
    for item in items:
        matched = False
        for cluster in clusters:
            if mergeable(item, cluster[0]):
                cluster.append(item)
                matched = True
                break
        if not matched:
            clusters.append([item])

    return [summarize_cluster(f'cluster_{i+1:04d}', c) for i, c in enumerate(clusters)], len(paths), len(items)


def test_params(clusters, min_sessions, min_frames, min_support, max_dynamic_ratio, min_label_purity):
    selected, rejected = [], []
    for c in clusters:
        sup = int(c.get('support_count', 0))
        sess = int(c.get('session_count', 0))
        frames = int(c.get('frame_count', sup))
        sh = c.get('state_histogram', {})
        dyn = float(sh.get('dynamic_agent', 0)) / max(sup, 1)
        rh = c.get('raw_label_histogram', {})
        purity = max(rh.values()) / max(sum(rh.values()), 1) if rh else 0.0
        keep = (sess >= min_sessions and frames >= min_frames and sup >= min_support
                and dyn <= max_dynamic_ratio and purity >= min_label_purity)
        reasons = []
        if sess < min_sessions:
            reasons.append('single_session')
        if frames < min_frames:
            reasons.append('low_frames')
        if sup < min_support:
            reasons.append('low_support')
        if dyn > max_dynamic_ratio:
            reasons.append('dynamic')
        if purity < min_label_purity:
            reasons.append('label_frag')
        if not reasons and not keep:
            reasons.append('other')
        item = dict(c)
        item['dynamic_ratio'] = dyn
        item['label_purity'] = purity
        item['frame_count'] = frames
        item['reject_reasons'] = reasons
        (selected if keep else rejected).append(item)
    return selected, rejected


def category_counts(items):
    cats = Counter(normalize_label(i['canonical_label']) for i in items)
    return dict(cats.most_common())


def main():
    print("Building combined Aisle + Hallway clusters...")
    clusters, num_inputs, num_objects = build_clusters()
    print(f"  {num_inputs} map_objects.json files → {num_objects} raw objects → {len(clusters)} cross-session clusters")
    print(f"  Session distribution: {dict(Counter(c['session_count'] for c in clusters))}")
    print(f"  Support distribution: {dict(Counter(c['support_count'] for c in clusters))}")

    # Save combined cluster file
    out_dir = Path("/home/rui/slam/outputs")
    cluster_file = out_dir / "torwic_ablation_combined_clusters.json"
    cluster_file.write_text(json.dumps({'num_inputs': num_inputs, 'num_raw_objects': num_objects,
                                         'num_clusters': len(clusters), 'clusters': clusters}, indent=2, ensure_ascii=False))
    print(f"  Saved: {cluster_file}")

    # Parameter sweep
    defaults = {'min_sessions': 2, 'min_frames': 4, 'min_support': 6, 'max_dynamic_ratio': 0.20, 'min_label_purity': 0.70}
    sweeps = {
        'min_sessions': [1, 2, 3],
        'min_frames': [2, 4, 6],
        'max_dynamic_ratio': [0.10, 0.20, 0.30],
    }

    results = []
    for param_name, values in sweeps.items():
        for val in values:
            p = dict(defaults)
            p[param_name] = val
            sel, rej = test_params(clusters, **p)
            sel_cats = category_counts(sel)
            rej_cats = category_counts(rej)
            results.append({
                'param': param_name, 'value': val,
                'selected': len(sel), 'rejected': len(rej),
                'selected_categories': sel_cats,
                'rejected_categories': rej_cats,
                'selected_stable': sum(v for k, v in sel_cats.items() if k in ('yellow barrier', 'work table', 'warehouse rack')),
                'selected_dynamic': sum(v for k, v in sel_cats.items() if k == 'forklift'),
            })

    # Also test the default baseline
    sel_def, rej_def = test_params(clusters, **defaults)
    sel_def_cats = category_counts(sel_def)
    rej_def_cats = category_counts(rej_def)

    # Write results
    ablation_file = out_dir / "torwic_admission_ablation_results.json"
    payload = {
        'dataset': {'num_inputs': num_inputs, 'num_raw_objects': num_objects, 'num_clusters': len(clusters)},
        'defaults': defaults,
        'default_result': {'selected': len(sel_def), 'rejected': len(rej_def),
                            'selected_categories': sel_def_cats, 'rejected_categories': rej_def_cats},
        'sweep_results': results,
    }
    ablation_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"\nSaved: {ablation_file}")

    # Print summary table
    print("\n" + "=" * 90)
    print("ABLATION SUMMARY TABLE")
    print("=" * 90)
    header = f"{'Parameter':<22s} {'Value':>6s} {'Selected':>9s} {'Rejected':>9s} {'Stable':>7s} {'Dynamic':>8s} {'Δ from default':>14s}"
    print(header)
    print("-" * 90)
    def_sel = len(sel_def)
    for r in results:
        delta = r['selected'] - def_sel
        dstr = f"{'+' if delta > 0 else ''}{delta}"
        print(f"{r['param']:<22s} {r['value']:>6} {r['selected']:>9d} {r['rejected']:>9d} {r['selected_stable']:>7d} {r['selected_dynamic']:>8d} {dstr:>14s}")
    print("-" * 90)
    print(f"{'(default)':<22s} {'':>6s} {def_sel:>9d} {len(rej_def):>9d} {sum(v for k,v in sel_def_cats.items() if k != 'forklift'):>7d} {sel_def_cats.get('forklift',0):>8d}")
    print()

    # Per-parameter analysis
    print("PER-PARAMETER ANALYSIS")
    for param_name in sweeps:
        rows = [r for r in results if r['param'] == param_name]
        print(f"  {param_name}:")
        for r in rows:
            delta = r['selected'] - def_sel
            print(f"    value={r['value']}: selected={r['selected']} rejected={r['rejected']} Δ={delta:+d}")
        # Check sensitivity
        vals = [r['selected'] for r in rows]
        if len(set(vals)) == 1:
            print(f"    → INSENSITIVE (no change in selection)")
        else:
            print(f"    → SENSITIVE (range: {min(vals)}–{max(vals)})")

    print(f"\nDone. Outputs: {cluster_file}, {ablation_file}")


if __name__ == '__main__':
    main()
