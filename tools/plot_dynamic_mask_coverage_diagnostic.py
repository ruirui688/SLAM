#!/usr/bin/env python3
"""Plot dynamic-mask coverage diagnostics for bounded backend experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "outputs" / "dynamic_slam_backend_input_pack_64_semantic_masks" / "backend_input_manifest.json"
METRICS = ROOT / "outputs" / "dynamic_slam_backend_smoke_p135_64_semantic_masks_global_ba" / "p135_semantic_mask_metrics.json"
OUTPUT = ROOT / "paper" / "figures" / "torwic_dynamic_mask_coverage_p135.png"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--metrics", type=Path, default=METRICS)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--title", default="P135 diagnosis: real semantic masks are present but still sparse")
    parser.add_argument(
        "--caption",
        default="Existing frontend masks cover frames 000004, 000005, and 000007; trajectory metrics remain tied.",
    )
    parser.add_argument("--masked-label", default="semantic masked RGB")
    return parser.parse_args()


def load_metric_pairs(path: Path, masked_label: str) -> dict[str, tuple[float, float]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    metrics = payload["metrics"]
    raw = metrics.get("raw RGB") or metrics.get("raw")
    masked = metrics.get(masked_label) or metrics.get("semantic_masked") or metrics.get("masked")
    if raw is None or masked is None:
        raise KeyError(f"Could not find raw/masked metrics in {path}")
    return {
        "APE RMSE": (raw["ape_rmse_m"], masked["ape_rmse_m"]),
        "RPE RMSE": (raw["rpe_rmse_m"], masked["rpe_rmse_m"]),
    }


def main() -> None:
    args = parse_args()
    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    frames = payload["frames"]
    frame_indices = np.asarray([frame["frame_index"] for frame in frames])
    coverage = np.asarray([frame["coverage_ratio"] * 100.0 for frame in frames])
    nonzero = coverage > 0

    metrics = load_metric_pairs(args.metrics, args.masked_label)

    plt.rcParams.update({"font.size": 10, "figure.dpi": 160})
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.6), gridspec_kw={"width_ratios": [1.35, 1.0]})

    ax0 = axes[0]
    ax0.bar(frame_indices, coverage, color=np.where(nonzero, "#d62728", "#cfcfcf"), width=0.85)
    ax0.set_title("Dynamic mask coverage over 64 frames")
    ax0.set_xlabel("frame index")
    ax0.set_ylabel("masked pixels (%)")
    ax0.set_xlim(-1, 64)
    ax0.set_ylim(0, max(coverage) * 1.28)
    ax0.grid(True, axis="y", color="#d8d8d8", linewidth=0.7)
    for idx, value in zip(frame_indices[nonzero], coverage[nonzero]):
        ax0.text(idx, value + 0.04, f"{value:.2f}%", ha="center", va="bottom", fontsize=8, rotation=90)
    avg = coverage.mean()
    ax0.axhline(avg, color="#222222", linewidth=1.2, linestyle="--", label=f"64-frame avg {avg:.3f}%")
    ax0.legend(frameon=False, loc="upper right")

    ax1 = axes[1]
    labels = list(metrics)
    raw_values = [metrics[label][0] for label in labels]
    masked_values = [metrics[label][1] for label in labels]
    x = np.arange(len(labels))
    width = 0.34
    ax1.bar(x - width / 2, raw_values, width, color="#1f77b4", label="raw RGB")
    ax1.bar(x + width / 2, masked_values, width, color="#d62728", label=args.masked_label)
    ax1.set_title("Global-BA evo metrics")
    ax1.set_ylabel("RMSE (m)")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.set_ylim(0, max(raw_values + masked_values) * 1.35)
    ax1.grid(True, axis="y", color="#d8d8d8", linewidth=0.7)
    ax1.legend(frameon=False)
    for xpos, value in zip(x - width / 2, raw_values):
        ax1.text(xpos, value + 0.0015, f"{value:.6f}", ha="center", va="bottom", fontsize=8)
    for xpos, value in zip(x + width / 2, masked_values):
        ax1.text(xpos, value + 0.0015, f"{value:.6f}", ha="center", va="bottom", fontsize=8)

    fig.suptitle(args.title, fontsize=13, y=0.985)
    fig.text(
        0.5,
        0.012,
        args.caption,
        ha="center",
        fontsize=9,
        color="#444444",
    )
    fig.subplots_adjust(bottom=0.18, top=0.84)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, bbox_inches="tight")
    print(args.output)


if __name__ == "__main__":
    main()
