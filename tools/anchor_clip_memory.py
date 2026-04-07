"""
Lightweight track-level CLIP memory for semantic stability analysis.
"""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass, field
from typing import Deque


@dataclass
class SemanticTrackMemory:
    max_history: int = 8
    posterior_alpha: float = 0.65
    clip_labels: Deque[str] = field(default_factory=deque)
    confidences: Deque[float] = field(default_factory=deque)
    margins: Deque[float] = field(default_factory=deque)
    gate_scores: Deque[float] = field(default_factory=deque)
    gate_passes: Deque[int] = field(default_factory=deque)
    ema_confidence: float | None = None
    ema_gate_score: float | None = None

    def _append(self, values: Deque, value) -> None:
        values.append(value)
        while len(values) > self.max_history:
            values.popleft()

    def update(
        self,
        clip_label: str,
        confidence: float,
        margin: float,
        gate_score: float,
        gate_passed: bool,
    ) -> None:
        self._append(self.clip_labels, str(clip_label))
        self._append(self.confidences, float(confidence))
        self._append(self.margins, float(margin))
        self._append(self.gate_scores, float(gate_score))
        self._append(self.gate_passes, int(bool(gate_passed)))

        if self.ema_confidence is None:
            self.ema_confidence = float(confidence)
        else:
            self.ema_confidence = (
                self.posterior_alpha * float(confidence) + (1.0 - self.posterior_alpha) * self.ema_confidence
            )

        if self.ema_gate_score is None:
            self.ema_gate_score = float(gate_score)
        else:
            self.ema_gate_score = (
                self.posterior_alpha * float(gate_score) + (1.0 - self.posterior_alpha) * self.ema_gate_score
            )


def _count_label_flips(labels: list[str]) -> int:
    if len(labels) <= 1:
        return 0
    flips = 0
    previous = labels[0]
    for current in labels[1:]:
        if current != previous:
            flips += 1
        previous = current
    return flips


def compute_semantic_memory_features(
    memory: SemanticTrackMemory,
    clip_label: str,
    confidence: float,
    margin: float,
    gate_score: float,
    gate_passed: bool,
) -> dict[str, float | int | str]:
    history_labels = list(memory.clip_labels)
    history_confidences = list(memory.confidences)
    history_margins = list(memory.margins)
    history_gate_scores = list(memory.gate_scores)
    history_gate_passes = list(memory.gate_passes)
    history_count = len(history_labels)

    current_label = str(clip_label)
    current_confidence = float(confidence)
    current_margin = float(margin)
    current_gate_score = float(gate_score)
    current_gate_passed = int(bool(gate_passed))
    current_combined_score = 0.5 * current_confidence + 0.5 * current_gate_score

    if history_count == 0:
        return {
            "semantic_memory_label": current_label,
            "semantic_posterior_score": current_combined_score,
            "semantic_consistency": 1.0,
            "semantic_persistence": float(current_gate_passed),
            "label_flip_count": 0,
            "mean_margin": current_margin,
            "history_observations": 0,
        }

    label_counts = Counter(history_labels)
    semantic_memory_label, dominant_count = label_counts.most_common(1)[0]
    history_label_match_ratio = sum(1 for label in history_labels if label == current_label) / history_count
    history_dominant_ratio = dominant_count / history_count
    history_confidence = (
        memory.ema_confidence
        if memory.ema_confidence is not None
        else sum(history_confidences) / max(len(history_confidences), 1)
    )
    history_gate_score = (
        memory.ema_gate_score
        if memory.ema_gate_score is not None
        else sum(history_gate_scores) / max(len(history_gate_scores), 1)
    )
    history_combined_score = 0.5 * float(history_confidence) + 0.5 * float(history_gate_score)
    semantic_posterior_score = (
        memory.posterior_alpha * current_combined_score + (1.0 - memory.posterior_alpha) * history_combined_score
    )
    semantic_consistency = 0.5 * history_label_match_ratio + 0.5 * history_dominant_ratio
    semantic_persistence = (sum(history_gate_passes) + current_gate_passed) / (history_count + 1)
    label_flip_count = _count_label_flips(history_labels + [current_label])
    mean_margin = (sum(history_margins) + current_margin) / (history_count + 1)

    return {
        "semantic_memory_label": str(semantic_memory_label),
        "semantic_posterior_score": float(semantic_posterior_score),
        "semantic_consistency": float(semantic_consistency),
        "semantic_persistence": float(semantic_persistence),
        "label_flip_count": int(label_flip_count),
        "mean_margin": float(mean_margin),
        "history_observations": int(history_count),
    }
