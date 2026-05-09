#!/usr/bin/env python3
"""Plot P134 dynamic SLAM backend raw-vs-masked results for the paper."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GT = ROOT / "outputs" / "dynamic_slam_backend_input_pack_64" / "groundtruth.txt"
DEFAULT_RAW = ROOT / "outputs" / "dynamic_slam_backend_smoke_p134_64_global_ba" / "raw_estimate_tum.txt"
DEFAULT_MASKED = ROOT / "outputs" / "dynamic_slam_backend_smoke_p134_64_global_ba" / "masked_estimate_tum.txt"
DEFAULT_OUTPUT = ROOT / "paper" / "figures" / "torwic_dynamic_slam_backend_p134.png"


def load_tum(path: Path) -> np.ndarray:
    rows: list[list[float]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        rows.append([float(value) for value in line.split()])
    if not rows:
        raise ValueError(f"No trajectory rows found in {path}")
    return np.asarray(rows, dtype=float)


def positions(traj: np.ndarray) -> np.ndarray:
    return traj[:, 1:4].copy()


def align_umeyama(source: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Align source positions to target with Sim(3), matching evo --align --correct_scale."""
    src_mean = source.mean(axis=0)
    tgt_mean = target.mean(axis=0)
    src_centered = source - src_mean
    tgt_centered = target - tgt_mean
    covariance = tgt_centered.T @ src_centered / len(source)
    u, singular_values, vt = np.linalg.svd(covariance)
    correction = np.eye(3)
    if np.linalg.det(u) * np.linalg.det(vt) < 0:
        correction[-1, -1] = -1.0
    rotation = u @ correction @ vt
    variance = np.mean(np.sum(src_centered * src_centered, axis=1))
    scale = np.trace(np.diag(singular_values) @ correction) / variance
    translation = tgt_mean - scale * rotation @ src_mean
    return (scale * (rotation @ source.T)).T + translation


def normalized_xy(points_xyz: np.ndarray) -> np.ndarray:
    xy = points_xyz[:, :2].copy()
    xy -= xy[0]
    return xy


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--groundtruth", type=Path, default=DEFAULT_GT)
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--masked", type=Path, default=DEFAULT_MASKED)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    gt = load_tum(args.groundtruth)
    raw = load_tum(args.raw)
    masked = load_tum(args.masked)

    metrics = {
        "APE RMSE": (0.051135, 0.051136),
        "RPE RMSE": (0.032713, 0.032713),
    }

    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "legend.fontsize": 9,
            "figure.dpi": 160,
        }
    )
    fig = plt.figure(figsize=(10.5, 4.8))
    grid = fig.add_gridspec(1, 2, width_ratios=[1.25, 1.0], wspace=0.32)

    ax0 = fig.add_subplot(grid[0, 0])
    gt_xyz = positions(gt)
    raw_xyz = align_umeyama(positions(raw), gt_xyz)
    masked_xyz = align_umeyama(positions(masked), gt_xyz)
    gt_xy = normalized_xy(gt_xyz)
    raw_xy = normalized_xy(raw_xyz)
    masked_xy = normalized_xy(masked_xyz)
    ax0.plot(gt_xy[:, 0], gt_xy[:, 1], color="#222222", linewidth=2.2, label="ground truth")
    ax0.plot(raw_xy[:, 0], raw_xy[:, 1], color="#1f77b4", linewidth=1.8, label="raw DROID")
    ax0.plot(masked_xy[:, 0], masked_xy[:, 1], color="#d62728", linewidth=1.4, linestyle="--", label="masked DROID")
    ax0.scatter([gt_xy[0, 0]], [gt_xy[0, 1]], color="#2ca02c", s=34, zorder=5, label="start")
    ax0.scatter([gt_xy[-1, 0]], [gt_xy[-1, 1]], color="#9467bd", s=34, zorder=5, label="end")
    ax0.set_title("64-frame TorWIC Aisle trajectory")
    ax0.set_xlabel("relative x (m)")
    ax0.set_ylabel("relative y (m)")
    ax0.axis("equal")
    ax0.grid(True, color="#d8d8d8", linewidth=0.7)
    ax0.legend(loc="best", frameon=False)

    ax1 = fig.add_subplot(grid[0, 1])
    labels = list(metrics)
    raw_values = [metrics[label][0] for label in labels]
    masked_values = [metrics[label][1] for label in labels]
    x = np.arange(len(labels))
    width = 0.34
    ax1.bar(x - width / 2, raw_values, width, color="#1f77b4", label="raw RGB")
    ax1.bar(x + width / 2, masked_values, width, color="#d62728", label="masked RGB")
    ax1.set_title("evo error metrics")
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

    fig.suptitle(
        "Bounded DROID-SLAM global-BA backend run: path closed, no masked-input gain yet",
        fontsize=13,
        y=0.98,
    )
    fig.text(
        0.5,
        0.015,
        "Mask coverage is limited to frame 000002 in this run; raw and masked estimates are effectively tied.",
        ha="center",
        fontsize=9,
        color="#444444",
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, bbox_inches="tight")
    print(args.output)


if __name__ == "__main__":
    main()
