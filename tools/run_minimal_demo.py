#!/usr/bin/env python3
"""Run the repository's minimal semantic-SLAM map-admission demo.

The demo is intentionally lightweight: it uses a tiny JSON fixture and the
Python standard library only. It exercises the paper's core loop:

ObjectObservation -> cross-session cluster -> retained MapObject or rejection.
"""

from __future__ import annotations

import argparse
import html
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
        "# 最小语义 SLAM Demo 报告",
        "",
        f"数据集：`{dataset.get('name', 'unknown')}`",
        "",
        "这个 smoke demo 不需要 GPU、模型权重或 TorWIC 下载，用一个极小样例展示论文核心主张：",
        "语义分割得到的对象观测只是候选证据，不能直接写入持久 SLAM 地图。",
        "",
        "## 地图准入规则",
        "",
        f"- 最少跨会话数：{args.min_sessions}",
        f"- 最少观测数：{args.min_observations}",
        f"- 最大动态/瞬时比例：{args.max_dynamic_ratio}",
        f"- 最小标签纯度：{args.min_label_purity}",
        "",
        "## 保留的稳定地图对象",
        "",
    ]
    if not retained:
        lines.append("- 无")
    for item in retained:
        lines.append(
            f"- `{item['map_object_id']}`: {item['canonical_label']} | sessions={item['session_count']} | "
            f"support={item['support_count']} | trust={item['map_trust_score']} | centroid={item['reference_centroid_xyz']}"
        )

    lines.extend(["", "## 拒绝的动态或瞬时证据", ""])
    if not rejected:
        lines.append("- 无")
    for item in rejected:
        lines.append(
            f"- `{item['cluster_id']}`: {item['canonical_label']} | sessions={item['session_count']} | "
            f"support={item['support_count']} | dynamic_ratio={item['dynamic_ratio']} | reasons={item['reject_reasons']}"
        )

    lines.extend(
        [
            "",
            "## 解释",
            "",
            f"该 demo 保留 {len(retained)} 个稳定地图对象，拒绝 {len(rejected)} 个对象簇。",
            "这对应论文中的最小逻辑：稳定基础设施可以进入语义地图，",
            "而 forklift-like 或单会话瞬时证据会被排除在持久地图层之外。",
            "",
        ]
    )
    return "\n".join(lines)


def render_svg(summary: dict[str, Any], retained: list[dict[str, Any]], rejected: list[dict[str, Any]]) -> str:
    retained_lines = [
        f"{item['map_object_id']}: {item['canonical_label']}  sessions={item['session_count']}  support={item['support_count']}"
        for item in retained
    ]
    rejected_lines = [
        f"{item['cluster_id']}: {item['canonical_label']}  reasons={','.join(item['reject_reasons'])}"
        for item in rejected
    ]

    def text_line(content: str, x: int, y: int, size: int = 18, color: str = "#172026") -> str:
        return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}">{html.escape(content)}</text>'

    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="700" viewBox="0 0 1120 700">',
        '<rect width="1120" height="700" fill="#f7f8f3"/>',
        '<rect x="42" y="36" width="1036" height="628" rx="18" fill="#ffffff" stroke="#d6d9cf"/>',
        text_line("最小语义 SLAM Demo 运行结果", 72, 88, 30, "#102027"),
        text_line("ObjectObservation -> Cross-session Cluster -> Stable MapObject / Rejection", 72, 124, 18, "#50606a"),
        '<rect x="72" y="160" width="220" height="118" rx="14" fill="#e8f1ff" stroke="#8ab4f8"/>',
        '<rect x="326" y="160" width="220" height="118" rx="14" fill="#f0f7e8" stroke="#9cc878"/>',
        '<rect x="580" y="160" width="220" height="118" rx="14" fill="#e9f8f5" stroke="#63b6aa"/>',
        '<rect x="834" y="160" width="190" height="118" rx="14" fill="#fff0eb" stroke="#ee9b7a"/>',
        text_line(f"{summary['observations']}", 158, 214, 38, "#174ea6"),
        text_line("观测", 160, 248, 20, "#174ea6"),
        text_line(f"{summary['clusters']}", 417, 214, 38, "#4e7d20"),
        text_line("对象簇", 400, 248, 20, "#4e7d20"),
        text_line(f"{summary['retained_stable_map_objects']}", 672, 214, 38, "#00796b"),
        text_line("保留稳定对象", 632, 248, 20, "#00796b"),
        text_line(f"{summary['rejected_clusters']}", 922, 214, 38, "#c2410c"),
        text_line("拒绝对象簇", 884, 248, 20, "#c2410c"),
        '<path d="M294 219 L324 219" stroke="#73808a" stroke-width="3" marker-end="url(#arrow)"/>',
        '<path d="M548 219 L578 219" stroke="#73808a" stroke-width="3" marker-end="url(#arrow)"/>',
        '<path d="M802 219 L832 219" stroke="#73808a" stroke-width="3" marker-end="url(#arrow)"/>',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#73808a"/></marker></defs>',
        text_line("保留的稳定地图对象", 88, 332, 24, "#0f766e"),
    ]
    y = 370
    for line in retained_lines:
        lines.append('<circle cx="98" cy="{}" r="6" fill="#0f766e"/>'.format(y - 5))
        lines.append(text_line(line, 116, y, 18, "#172026"))
        y += 34
    y += 24
    lines.append(text_line("拒绝的动态/瞬时证据", 88, y, 24, "#b45309"))
    y += 38
    for line in rejected_lines:
        lines.append('<circle cx="98" cy="{}" r="6" fill="#b45309"/>'.format(y - 5))
        lines.append(text_line(line, 116, y, 18, "#172026"))
        y += 34
    lines.extend(
        [
            text_line("结论：稳定基础设施进入地图；forklift-like 和单会话瞬时对象被挡在持久地图外。", 72, 618, 19, "#38444d"),
            text_line("运行命令：python tools/run_minimal_demo.py  或  make demo", 72, 646, 16, "#66727c"),
            "</svg>",
        ]
    )
    return "\n".join(lines) + "\n"


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
    (args.output_dir / "result.svg").write_text(render_svg(summary, retained, rejected), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\nReport: {args.output_dir / 'report.md'}")
    print(f"Result image: {args.output_dir / 'result.svg'}")


if __name__ == "__main__":
    main()
