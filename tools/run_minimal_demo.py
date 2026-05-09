#!/usr/bin/env python3
"""Run the repository's minimal semantic-SLAM map-admission demo.

The demo is intentionally lightweight: it uses a tiny JSON fixture and the
Python standard library only. It exercises the paper's core loop:

ObjectObservation -> cross-session cluster -> retained MapObject or rejection.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "examples" / "minimal_slam_demo" / "observations.json"
DEFAULT_OUTPUT = REPO_ROOT / "outputs" / "minimal_demo"
DYNAMIC_STATES = {"dynamic_agent", "transient_object"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--min-sessions", type=int, default=2)
    parser.add_argument("--min-observations", type=int, default=3)
    parser.add_argument("--max-dynamic-ratio", type=float, default=0.34)
    parser.add_argument("--min-label-purity", type=float, default=0.60)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def canonical_label(labels: list[str]) -> str:
    if not labels:
        return "unknown"
    normalized = [label.strip().lower() for label in labels]
    aliases = {
        "barrier": "safety barrier",
        "storage rack": "warehouse rack",
        "pallet": "pallet stack",
    }
    mapped = [aliases.get(label, label) for label in normalized]
    return Counter(mapped).most_common(1)[0][0]


def average_centroid(observations: list[dict[str, Any]]) -> list[float]:
    coords = [obs.get("centroid_xyz", [0.0, 0.0, 0.0]) for obs in observations]
    return [round(mean(float(coord[index]) for coord in coords), 3) for index in range(3)]


def cluster_observations(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for obs in observations:
        grouped[str(obs["cluster_hint"])].append(obs)

    clusters = []
    for cluster_id, items in sorted(grouped.items()):
        labels = [str(item.get("label", "unknown")) for item in items]
        states = [str(item.get("state_hint", "unknown")) for item in items]
        sessions = sorted({str(item["session_id"]) for item in items})
        label_hist = Counter(canonical_label([label]) for label in labels)
        state_hist = Counter(states)
        support = len(items)
        dynamic_count = sum(count for state, count in state_hist.items() if state in DYNAMIC_STATES)
        clusters.append(
            {
                "cluster_id": cluster_id,
                "canonical_label": canonical_label(labels),
                "support_count": support,
                "session_count": len(sessions),
                "sessions": sessions,
                "label_histogram": dict(label_hist),
                "state_histogram": dict(state_hist),
                "dynamic_ratio": round(dynamic_count / max(support, 1), 3),
                "label_purity": round(max(label_hist.values()) / max(sum(label_hist.values()), 1), 3),
                "mean_confidence": round(mean(float(item.get("confidence", 0.0)) for item in items), 3),
                "reference_centroid_xyz": average_centroid(items),
                "observation_ids": [str(item["observation_id"]) for item in items],
            }
        )
    return clusters


def evaluate_clusters(clusters: list[dict[str, Any]], args: argparse.Namespace) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    retained = []
    rejected = []
    for cluster in clusters:
        reasons = []
        if cluster["session_count"] < args.min_sessions:
            reasons.append("low_session_support")
        if cluster["support_count"] < args.min_observations:
            reasons.append("low_observation_support")
        if cluster["dynamic_ratio"] > args.max_dynamic_ratio:
            reasons.append("dynamic_or_transient_contamination")
        if cluster["label_purity"] < args.min_label_purity:
            reasons.append("label_fragmentation")

        record = dict(cluster)
        if reasons:
            record["decision"] = "reject"
            record["reject_reasons"] = reasons
            rejected.append(record)
            continue

        record["decision"] = "retain"
        record["map_object_id"] = f"map_{len(retained) + 1:03d}_{record['canonical_label'].replace(' ', '_')}"
        record["map_trust_score"] = round(
            min(1.0, 0.35 * record["session_count"] + 0.25 * record["label_purity"] + 0.25 * (1.0 - record["dynamic_ratio"])),
            3,
        )
        retained.append(record)
    return retained, rejected


def render_report(dataset: dict[str, Any], retained: list[dict[str, Any]], rejected: list[dict[str, Any]], args: argparse.Namespace) -> str:
    lines = [
        "# Minimal Semantic-SLAM Demo Report",
        "",
        f"Dataset: `{dataset.get('name', 'unknown')}`",
        "",
        "This smoke demo shows the repository's core paper claim without GPU, model weights, or TorWIC downloads:",
        "segmentation-derived object observations are candidate evidence, not immediate persistent map truth.",
        "",
        "## Admission Criteria",
        "",
        f"- min sessions: {args.min_sessions}",
        f"- min observations: {args.min_observations}",
        f"- max dynamic ratio: {args.max_dynamic_ratio}",
        f"- min label purity: {args.min_label_purity}",
        "",
        "## Retained Stable Map Objects",
        "",
    ]
    if not retained:
        lines.append("- None")
    for item in retained:
        lines.append(
            f"- `{item['map_object_id']}`: {item['canonical_label']} | sessions={item['session_count']} | "
            f"support={item['support_count']} | trust={item['map_trust_score']} | centroid={item['reference_centroid_xyz']}"
        )

    lines.extend(["", "## Rejected Dynamic or Transient Evidence", ""])
    if not rejected:
        lines.append("- None")
    for item in rejected:
        lines.append(
            f"- `{item['cluster_id']}`: {item['canonical_label']} | sessions={item['session_count']} | "
            f"support={item['support_count']} | dynamic_ratio={item['dynamic_ratio']} | reasons={item['reject_reasons']}"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"The demo retains {len(retained)} stable map objects and rejects {len(rejected)} clusters.",
            "This is the same minimal logic used by the paper narrative: stable infrastructure can enter the semantic map,",
            "while forklift-like or single-session evidence is kept out of the persistent layer.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    payload = load_json(args.input)
    observations = payload.get("observations", [])
    clusters = cluster_observations(observations)
    retained, rejected = evaluate_clusters(clusters, args)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "input": str(args.input),
        "output_dir": str(args.output_dir),
        "observations": len(observations),
        "clusters": len(clusters),
        "retained_stable_map_objects": len(retained),
        "rejected_clusters": len(rejected),
        "criteria": {
            "min_sessions": args.min_sessions,
            "min_observations": args.min_observations,
            "max_dynamic_ratio": args.max_dynamic_ratio,
            "min_label_purity": args.min_label_purity,
        },
    }
    write_json(args.output_dir / "clusters.json", clusters)
    write_json(args.output_dir / "map_objects.json", retained)
    write_json(args.output_dir / "rejected_clusters.json", rejected)
    write_json(args.output_dir / "summary.json", summary)
    (args.output_dir / "report.md").write_text(
        render_report(payload.get("dataset", {}), retained, rejected, args),
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\nReport: {args.output_dir / 'report.md'}")


if __name__ == "__main__":
    main()
