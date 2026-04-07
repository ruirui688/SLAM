"""
OpenCLIP-based second-stage reranking for Grounding DINO detections.
"""

from __future__ import annotations

import re
from contextlib import nullcontext
from functools import lru_cache
from typing import Any, Sequence

import numpy as np
import torch
from PIL import Image

DEFAULT_OPENCLIP_MODEL = "ViT-B-32"
DEFAULT_OPENCLIP_PRETRAINED = "laion2b_s34b_b79k"
DEFAULT_OPENCLIP_SCORE_WEIGHT = 0.35
DEFAULT_OPENCLIP_UNKNOWN_LABEL = "unknown"
DEFAULT_OPENCLIP_LABEL_MARGIN = 0.03
DEFAULT_OPENCLIP_LABEL_MIN_SIMILARITY = 0.2
DEFAULT_OPENCLIP_ENTROPY_THRESHOLD = 0.85


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().rstrip(".").lower())


def extract_prompt_phrases(text_prompt: str) -> list[str]:
    phrases: list[str] = []
    for part in re.split(r"[.;\n]+", text_prompt):
        phrase = normalize_text(part)
        if phrase and phrase not in phrases:
            phrases.append(phrase)
    return phrases


def resolve_openclip_device(device: str) -> str:
    if device == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        return "cpu"
    return device


@lru_cache(maxsize=4)
def load_openclip_model(model_name: str, pretrained: str, device: str):
    try:
        import open_clip
    except ImportError as exc:
        raise ImportError(
            "OpenCLIP reranking requires open_clip_torch. Install it with `pip install open_clip_torch`."
        ) from exc

    model, _, preprocess = open_clip.create_model_and_transforms(model_name, pretrained=pretrained, device=device)
    model.eval()
    tokenizer = open_clip.get_tokenizer(model_name)
    return model, preprocess, tokenizer


def preload_openclip_model(model_name: str, pretrained: str, device: str):
    resolved_device = resolve_openclip_device(device)
    return load_openclip_model(model_name, pretrained, resolved_device)


def _to_pil_image(image: np.ndarray | Image.Image) -> Image.Image:
    if isinstance(image, Image.Image):
        return image.convert("RGB")
    return Image.fromarray(image).convert("RGB")


def _crop_box(image: Image.Image, box: Sequence[float]) -> Image.Image:
    width, height = image.size
    x0, y0, x1, y1 = [float(v) for v in box]
    left = max(0, min(width - 1, int(np.floor(x0))))
    top = max(0, min(height - 1, int(np.floor(y0))))
    right = max(left + 1, min(width, int(np.ceil(x1))))
    bottom = max(top + 1, min(height, int(np.ceil(y1))))
    return image.crop((left, top, right, bottom))


def _resolve_target_prompt_index(label: str, prompt_phrases: list[str], similarity_row: np.ndarray) -> int:
    label_norm = normalize_text(label)
    if label_norm in prompt_phrases:
        return prompt_phrases.index(label_norm)

    label_tokens = set(label_norm.split())
    overlapping_indices = [
        idx for idx, phrase in enumerate(prompt_phrases) if label_tokens.intersection(set(phrase.split()))
    ]
    if overlapping_indices:
        best_local_idx = int(np.argmax(similarity_row[overlapping_indices]))
        return overlapping_indices[best_local_idx]

    return int(np.argmax(similarity_row))


def _softmax_probabilities(similarity_row: np.ndarray, logit_scale: float = 1.0) -> np.ndarray:
    shifted = (similarity_row - np.max(similarity_row)) * float(logit_scale)
    exp_row = np.exp(shifted)
    total = float(exp_row.sum())
    if not np.isfinite(total) or total <= 0.0:
        return np.full(len(similarity_row), 1.0 / max(len(similarity_row), 1), dtype=np.float32)
    return (exp_row / total).astype(np.float32)


def _normalized_entropy(probabilities: np.ndarray) -> float:
    if len(probabilities) <= 1:
        return 0.0
    safe_probabilities = np.clip(probabilities.astype(np.float64), 1e-12, 1.0)
    entropy = float(-(safe_probabilities * np.log(safe_probabilities)).sum())
    return float(np.clip(entropy / np.log(len(probabilities)), 0.0, 1.0))


def resolve_openclip_label(
    prompt_phrases: Sequence[str],
    similarity_row: np.ndarray,
    unknown_margin: float = DEFAULT_OPENCLIP_LABEL_MARGIN,
    min_best_similarity: float = DEFAULT_OPENCLIP_LABEL_MIN_SIMILARITY,
    unknown_label: str = DEFAULT_OPENCLIP_UNKNOWN_LABEL,
    entropy_threshold: float = DEFAULT_OPENCLIP_ENTROPY_THRESHOLD,
) -> dict[str, Any]:
    if len(prompt_phrases) == 0:
        raise ValueError("OpenCLIP label resolution needs at least one prompt phrase.")

    ordered_indices = np.argsort(similarity_row)[::-1]
    best_prompt_idx = int(ordered_indices[0])
    best_prompt = str(prompt_phrases[best_prompt_idx])
    best_similarity = float(np.clip(similarity_row[best_prompt_idx], -1.0, 1.0))
    ambiguity_logit_scale = 1.0 / max(float(unknown_margin), 1e-6)
    prompt_probabilities = _softmax_probabilities(
        np.asarray(similarity_row, dtype=np.float32),
        logit_scale=ambiguity_logit_scale,
    )
    best_prompt_probability = float(np.clip(prompt_probabilities[best_prompt_idx], 0.0, 1.0))
    clip_entropy = _normalized_entropy(prompt_probabilities)

    if len(ordered_indices) > 1:
        second_prompt_idx = int(ordered_indices[1])
        second_prompt = str(prompt_phrases[second_prompt_idx])
        second_similarity = float(np.clip(similarity_row[second_prompt_idx], -1.0, 1.0))
    else:
        second_prompt = ""
        second_similarity = -1.0

    margin = best_similarity - second_similarity
    similarity_score = float(np.clip((best_similarity + 1.0) / 2.0, 0.0, 1.0))
    margin_score = 1.0 if len(prompt_phrases) <= 1 else float(np.clip(margin / max(unknown_margin, 1e-6), 0.0, 1.0))
    entropy_score = 1.0 - float(np.clip(clip_entropy / max(entropy_threshold, 1e-6), 0.0, 1.0))
    semantic_gate_score = float(
        np.clip(0.45 * best_prompt_probability + 0.35 * margin_score + 0.20 * entropy_score, 0.0, 1.0)
    )

    resolved_label = best_prompt
    resolution_reason = "best_prompt"
    resolved_label_confidence = best_prompt_probability
    semantic_gate_reason = "accepted"
    if best_similarity < min_best_similarity:
        resolved_label = unknown_label
        resolution_reason = "low_similarity"
        resolved_label_confidence = 1.0 - similarity_score
        semantic_gate_score *= 0.25
        semantic_gate_reason = "low_similarity"
    elif len(prompt_phrases) > 1 and margin < unknown_margin:
        resolved_label = unknown_label
        resolution_reason = "low_margin"
        resolved_label_confidence = 1.0 - best_prompt_probability
        semantic_gate_score *= 0.5
        semantic_gate_reason = "low_margin"

    if clip_entropy > entropy_threshold:
        semantic_gate_score *= 0.75
        if semantic_gate_reason == "accepted":
            semantic_gate_reason = "high_entropy"

    semantic_gate_passed = semantic_gate_reason == "accepted"
    is_semantically_ambiguous = bool(len(prompt_phrases) > 1 and not semantic_gate_passed)

    return {
        "clip_proposed_label": best_prompt,
        "resolved_label": resolved_label,
        "resolution_reason": resolution_reason,
        "clip_best_prompt": best_prompt,
        "clip_best_similarity": best_similarity,
        "clip_second_prompt": second_prompt,
        "clip_second_similarity": second_similarity,
        "clip_margin": margin,
        "clip_entropy": clip_entropy,
        "resolved_label_confidence": float(np.clip(resolved_label_confidence, 0.0, 1.0)),
        "is_semantically_ambiguous": is_semantically_ambiguous,
        "is_semantically_uncertain": not semantic_gate_passed,
        "semantic_gate_label": best_prompt if semantic_gate_passed else unknown_label,
        "semantic_gate_score": float(np.clip(semantic_gate_score, 0.0, 1.0)),
        "semantic_gate_passed": semantic_gate_passed,
        "semantic_gate_reason": semantic_gate_reason,
    }


def rerank_detections_with_openclip(
    image: np.ndarray | Image.Image,
    boxes: np.ndarray,
    labels: Sequence[str],
    grounding_scores: Sequence[float],
    text_prompt: str,
    score_weight: float = DEFAULT_OPENCLIP_SCORE_WEIGHT,
    model_name: str = DEFAULT_OPENCLIP_MODEL,
    pretrained: str = DEFAULT_OPENCLIP_PRETRAINED,
    device: str = "cpu",
    unknown_margin: float = DEFAULT_OPENCLIP_LABEL_MARGIN,
    min_best_similarity: float = DEFAULT_OPENCLIP_LABEL_MIN_SIMILARITY,
    unknown_label: str = DEFAULT_OPENCLIP_UNKNOWN_LABEL,
) -> list[dict[str, Any]]:
    if len(boxes) == 0:
        return []

    resolved_device = resolve_openclip_device(device)
    prompt_phrases = extract_prompt_phrases(text_prompt)
    if not prompt_phrases:
        prompt_phrases = [normalize_text(label) for label in labels if normalize_text(label)]
    if not prompt_phrases:
        raise ValueError("OpenCLIP reranking needs at least one non-empty text prompt.")

    model, preprocess, tokenizer = load_openclip_model(model_name, pretrained, resolved_device)
    pil_image = _to_pil_image(image)
    crops = [_crop_box(pil_image, box) for box in boxes]

    image_batch = torch.stack([preprocess(crop) for crop in crops]).to(resolved_device)
    text_tokens = tokenizer(prompt_phrases).to(resolved_device)

    autocast_context = torch.autocast(device_type="cuda") if resolved_device == "cuda" else nullcontext()
    with torch.inference_mode(), autocast_context:
        image_features = model.encode_image(image_batch)
        text_features = model.encode_text(text_tokens)
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)

    similarity_matrix = (image_features @ text_features.T).float().detach().cpu().numpy()
    del image_batch, text_tokens, image_features, text_features
    if resolved_device == "cuda":
        torch.cuda.empty_cache()

    details: list[dict[str, Any]] = []
    for idx, similarity_row in enumerate(similarity_matrix):
        target_prompt_idx = _resolve_target_prompt_index(str(labels[idx]), prompt_phrases, similarity_row)
        clip_similarity = float(np.clip(similarity_row[target_prompt_idx], -1.0, 1.0))
        clip_similarity_01 = (clip_similarity + 1.0) / 2.0
        grounding_score = float(grounding_scores[idx])
        label_resolution = resolve_openclip_label(
            prompt_phrases=prompt_phrases,
            similarity_row=similarity_row,
            unknown_margin=unknown_margin,
            min_best_similarity=min_best_similarity,
            unknown_label=unknown_label,
        )
        ranking_score = grounding_score + score_weight * clip_similarity_01

        details.append(
            {
                "original_index": idx,
                "grounding_label": str(labels[idx]),
                "grounding_score": grounding_score,
                "clip_similarity": clip_similarity,
                "clip_similarity_01": clip_similarity_01,
                "ranking_score": ranking_score,
                "final_score": ranking_score,
                **label_resolution,
            }
        )

    details.sort(key=lambda item: item["ranking_score"], reverse=True)
    return details
