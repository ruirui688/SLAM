"""
Frame-by-frame stability check for the OpenCLIP-resolved detection frontend.

This script intentionally does not use the SAM2 video predictor. Instead, it:
1. Runs Grounding DINO + OpenCLIP + SAM2 image predictor independently on each frame.
2. Associates instances across frames into stable track IDs.
3. Reports missing detections and abrupt jumps.
4. Produces an annotated review video and machine-readable reports.
"""

from __future__ import annotations

import argparse
import csv
import gc
import json
import math
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import cv2
import numpy as np
import torch
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from utils.video_utils import create_video_from_images

try:
    from tools.anchor_clip_memory import SemanticTrackMemory, compute_semantic_memory_features
    from tools.openclip_reranker import (
        DEFAULT_OPENCLIP_LABEL_MARGIN,
        DEFAULT_OPENCLIP_LABEL_MIN_SIMILARITY,
        DEFAULT_OPENCLIP_MODEL,
        DEFAULT_OPENCLIP_PRETRAINED,
        DEFAULT_OPENCLIP_SCORE_WEIGHT,
        DEFAULT_OPENCLIP_UNKNOWN_LABEL,
        load_openclip_model,
        preload_openclip_model,
        rerank_detections_with_openclip,
        resolve_openclip_device,
    )
except ImportError:
    from anchor_clip_memory import SemanticTrackMemory, compute_semantic_memory_features
    from openclip_reranker import (
        DEFAULT_OPENCLIP_LABEL_MARGIN,
        DEFAULT_OPENCLIP_LABEL_MIN_SIMILARITY,
        DEFAULT_OPENCLIP_MODEL,
        DEFAULT_OPENCLIP_PRETRAINED,
        DEFAULT_OPENCLIP_SCORE_WEIGHT,
        DEFAULT_OPENCLIP_UNKNOWN_LABEL,
        load_openclip_model,
        preload_openclip_model,
        rerank_detections_with_openclip,
        resolve_openclip_device,
    )


DEFAULT_LOCAL_HF_SNAPSHOT = REPO_ROOT / "checkpoints" / "grounding_dino_tiny_pytorch"
DEFAULT_HF_SNAPSHOT = (
    DEFAULT_LOCAL_HF_SNAPSHOT
    if DEFAULT_LOCAL_HF_SNAPSHOT.exists()
    else Path.home()
    / ".cache"
    / "huggingface"
    / "hub"
    / "models--IDEA-Research--grounding-dino-tiny"
    / "snapshots"
    / "a2bb814dd30d776dcf7e30523b00659f4f141c71"
)


@dataclass
class Detection:
    frame_index: int
    frame_name: str
    resolved_label: str
    grounding_label: str
    clip_proposed_label: str
    box: np.ndarray
    mask: np.ndarray
    grounding_score: float
    clip_similarity: float
    clip_best_prompt: str
    clip_best_similarity: float
    clip_second_similarity: float
    clip_margin: float
    clip_entropy: float
    resolved_label_confidence: float
    is_semantically_ambiguous: bool
    semantic_gate_score: float
    semantic_gate_passed: bool
    semantic_gate_reason: str
    final_score: float
    semantic_memory_label: str = ""
    semantic_posterior_score: float = 0.0
    semantic_consistency: float = 1.0
    semantic_persistence: float = 1.0
    label_flip_count: int = 0
    mean_margin: float = 0.0
    history_observations: int = 0
    track_id: str | None = None
    center_shift_px: float | None = None
    bbox_iou_prev: float | None = None
    mask_iou_prev: float | None = None
    area_ratio_prev: float | None = None
    gap_from_prev: int | None = None

    @property
    def center(self) -> np.ndarray:
        return np.array([(self.box[0] + self.box[2]) * 0.5, (self.box[1] + self.box[3]) * 0.5], dtype=np.float32)

    @property
    def area(self) -> float:
        return float(max(0.0, self.box[2] - self.box[0]) * max(0.0, self.box[3] - self.box[1]))

    @property
    def mask_area(self) -> int:
        return int(self.mask.sum())


@dataclass
class Track:
    track_id: str
    label: str
    created_frame_index: int
    last_box: np.ndarray
    last_mask: np.ndarray
    last_frame_index: int
    detections: list[Detection] = field(default_factory=list)
    missing_frames: list[int] = field(default_factory=list)
    issue_frames: list[dict[str, object]] = field(default_factory=list)
    clip_memory: SemanticTrackMemory = field(default_factory=SemanticTrackMemory)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-frames", type=int, default=80)
    parser.add_argument("--prompt", type=str, default="wooden crate. yellow barrier.")
    parser.add_argument("--target-labels", type=str, default="wooden crate,yellow barrier")
    parser.add_argument("--box-threshold", type=float, default=0.25)
    parser.add_argument("--text-threshold", type=float, default=0.25)
    parser.add_argument("--hf-snapshot", type=Path, default=DEFAULT_HF_SNAPSHOT)
    parser.add_argument("--clip-score-weight", type=float, default=DEFAULT_OPENCLIP_SCORE_WEIGHT)
    parser.add_argument("--openclip-model", type=str, default=DEFAULT_OPENCLIP_MODEL)
    parser.add_argument("--openclip-pretrained", type=str, default=DEFAULT_OPENCLIP_PRETRAINED)
    parser.add_argument("--openclip-text-prompt", type=str, default=None)
    parser.add_argument("--openclip-device", type=str, default="auto", choices=["auto", "cpu", "cuda"])
    parser.add_argument("--openclip-soft-gate", type=int, default=1, choices=[0, 1])
    parser.add_argument("--clip-memory-size", type=int, default=8)
    parser.add_argument("--clip-memory-alpha", type=float, default=0.65)
    parser.add_argument("--openclip-label-margin", type=float, default=DEFAULT_OPENCLIP_LABEL_MARGIN)
    parser.add_argument(
        "--openclip-label-min-similarity",
        type=float,
        default=DEFAULT_OPENCLIP_LABEL_MIN_SIMILARITY,
    )
    parser.add_argument("--unknown-label", type=str, default=DEFAULT_OPENCLIP_UNKNOWN_LABEL)
    parser.add_argument("--sam2-checkpoint", type=Path, default=Path("./checkpoints/sam2.1_hiera_large.pt"))
    parser.add_argument("--sam2-config", type=str, default="configs/sam2.1/sam2.1_hiera_l.yaml")
    parser.add_argument("--sam2-device", type=str, default="auto", choices=["auto", "cpu", "cuda"])
    parser.add_argument("--grounding-device", type=str, default="cpu", choices=["auto", "cpu", "cuda"])
    parser.add_argument("--match-max-center-distance-px", type=float, default=220.0)
    parser.add_argument("--jump-center-distance-px", type=float, default=90.0)
    parser.add_argument("--jump-bbox-iou-threshold", type=float, default=0.15)
    parser.add_argument("--jump-mask-iou-threshold", type=float, default=0.10)
    parser.add_argument("--jump-area-ratio-threshold", type=float, default=1.8)
    parser.add_argument("--video-fps", type=float, default=9.0)
    return parser.parse_args()


def normalize_label(label: str) -> str:
    return " ".join(label.strip().rstrip(".").lower().split())


def choose_sam2_device(device: str) -> str:
    if device == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        return "cpu"
    return device


def enable_torch_optimizations(device: str) -> None:
    if device != "cuda":
        return

    torch.autocast(device_type="cuda", dtype=torch.bfloat16).__enter__()

    if torch.cuda.get_device_properties(0).major >= 8:
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True


def configure_runtime_stability() -> None:
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)


def preload_runtime_models(args: argparse.Namespace) -> None:
    preload_openclip_model(args.openclip_model, args.openclip_pretrained, args.openclip_device)
    gc.collect()
    if args.openclip_device == "cuda":
        torch.cuda.empty_cache()


def _expand_grounding_bbox_embed_state_dict(
    state_dict: dict[str, torch.Tensor],
    decoder_layers: int,
) -> dict[str, torch.Tensor]:
    expanded = dict(state_dict)
    base_prefix = "bbox_embed.0."
    base_keys = [key for key in expanded if key.startswith(base_prefix)]
    if not base_keys:
        return expanded

    for layer_idx in range(decoder_layers):
        for key in base_keys:
            suffix = key[len(base_prefix) :]
            template_value = expanded[key]
            expanded.setdefault(f"bbox_embed.{layer_idx}.{suffix}", template_value.clone())
            expanded.setdefault(f"model.decoder.bbox_embed.{layer_idx}.{suffix}", template_value.clone())
    return expanded


def load_grounding_model(snapshot_dir: Path, device: str):
    from transformers import AutoConfig, AutoModelForZeroShotObjectDetection

    bin_checkpoint = snapshot_dir / "pytorch_model.bin"
    if bin_checkpoint.is_file():
        state_dict = torch.load(
            bin_checkpoint,
            map_location="cpu",
            weights_only=False,
            mmap=False,
        )
        config = AutoConfig.from_pretrained(snapshot_dir, local_files_only=True)
        state_dict = _expand_grounding_bbox_embed_state_dict(
            state_dict=state_dict,
            decoder_layers=int(getattr(config, "decoder_layers", 6)),
        )
        model = AutoModelForZeroShotObjectDetection.from_config(config)
        missing_keys, unexpected_keys = model.load_state_dict(state_dict, strict=False)
        if missing_keys or unexpected_keys:
            raise RuntimeError(
                "Grounding DINO checkpoint load mismatch: "
                f"missing_keys={len(missing_keys)}, unexpected_keys={len(unexpected_keys)}"
            )
        return model.to(device)

    return AutoModelForZeroShotObjectDetection.from_pretrained(
        snapshot_dir,
        local_files_only=True,
        low_cpu_mem_usage=True,
        use_safetensors=False,
    ).to(device)


def bbox_iou(box_a: np.ndarray, box_b: np.ndarray) -> float:
    xa0, ya0, xa1, ya1 = [float(v) for v in box_a]
    xb0, yb0, xb1, yb1 = [float(v) for v in box_b]
    inter_x0 = max(xa0, xb0)
    inter_y0 = max(ya0, yb0)
    inter_x1 = min(xa1, xb1)
    inter_y1 = min(ya1, yb1)
    inter_w = max(0.0, inter_x1 - inter_x0)
    inter_h = max(0.0, inter_y1 - inter_y0)
    inter_area = inter_w * inter_h
    area_a = max(0.0, xa1 - xa0) * max(0.0, ya1 - ya0)
    area_b = max(0.0, xb1 - xb0) * max(0.0, yb1 - yb0)
    union = area_a + area_b - inter_area
    if union <= 0:
        return 0.0
    return inter_area / union


def mask_iou(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
    intersection = float(np.logical_and(mask_a, mask_b).sum())
    union = float(np.logical_or(mask_a, mask_b).sum())
    if union <= 0:
        return 0.0
    return intersection / union


def track_id_from_order(label: str, order: int, total: int) -> str:
    base = label.replace(" ", "_")
    if total == 1:
        return base
    if total == 2:
        return f"{base}_{'left' if order == 0 else 'right'}"
    return f"{base}_{order + 1:02d}"


def color_for_track(track_id: str) -> tuple[int, int, int]:
    palette = [
        (0, 165, 255),
        (255, 140, 0),
        (0, 220, 220),
        (255, 80, 80),
        (140, 220, 0),
        (255, 0, 180),
    ]
    index = sum(ord(ch) for ch in track_id) % len(palette)
    return palette[index]


def detect_frame(
    frame_path: Path,
    frame_index: int,
    args: argparse.Namespace,
    processor,
    model,
    predictor: SAM2ImagePredictor,
    target_labels: set[str],
) -> tuple[np.ndarray, list[Detection]]:
    image = Image.open(frame_path).convert("RGB")
    image_np = np.array(image)
    inputs = processor(images=image, text=args.prompt, return_tensors="pt").to(args.grounding_device)
    with torch.no_grad():
        outputs = model(**inputs)

    results = processor.post_process_grounded_object_detection(
        outputs,
        inputs.input_ids,
        threshold=args.box_threshold,
        text_threshold=args.text_threshold,
        target_sizes=[image.size[::-1]],
    )[0]

    boxes = results["boxes"].cpu().numpy()
    if len(boxes) == 0:
        return image_np, []

    grounding_scores = results["scores"].cpu().numpy().tolist()
    grounding_labels = [str(label) for label in results["labels"]]
    del inputs, outputs, results
    if args.grounding_device == "cuda":
        torch.cuda.empty_cache()
    score_details = rerank_detections_with_openclip(
        image=image,
        boxes=boxes,
        labels=grounding_labels,
        grounding_scores=grounding_scores,
        text_prompt=args.openclip_text_prompt or args.prompt,
        score_weight=args.clip_score_weight,
        model_name=args.openclip_model,
        pretrained=args.openclip_pretrained,
        device=args.openclip_device,
        unknown_margin=args.openclip_label_margin,
        min_best_similarity=args.openclip_label_min_similarity,
        unknown_label=args.unknown_label,
    )

    kept_details: list[dict[str, object]] = []
    for item in score_details:
        grounding_label = normalize_label(str(item["grounding_label"]))
        clip_proposed_label = normalize_label(str(item["clip_proposed_label"]))
        semantic_gate_label = normalize_label(str(item["semantic_gate_label"]))

        if bool(args.openclip_soft_gate):
            downstream_label = semantic_gate_label if bool(item["semantic_gate_passed"]) else grounding_label
        else:
            downstream_label = normalize_label(str(item["resolved_label"]))

        item["grounding_label_normalized"] = grounding_label
        item["clip_proposed_label_normalized"] = clip_proposed_label
        item["downstream_label"] = downstream_label
        if downstream_label in target_labels:
            kept_details.append(item)

    if not kept_details:
        return image_np, []

    kept_indices = [item["original_index"] for item in kept_details]
    kept_boxes = boxes[kept_indices]

    predictor.set_image(image_np)
    masks, _, _ = predictor.predict(
        point_coords=None,
        point_labels=None,
        box=kept_boxes,
        multimask_output=False,
    )
    if masks.ndim == 4:
        masks = masks.squeeze(1)

    detections: list[Detection] = []
    for detail, box, mask in zip(kept_details, kept_boxes, masks):
        detections.append(
            Detection(
                frame_index=frame_index,
                frame_name=frame_path.name,
                resolved_label=str(detail["downstream_label"]),
                grounding_label=str(detail["grounding_label"]),
                clip_proposed_label=str(detail["clip_proposed_label"]),
                box=box.astype(np.float32),
                mask=(mask > 0),
                grounding_score=float(detail["grounding_score"]),
                clip_similarity=float(detail["clip_similarity"]),
                clip_best_prompt=str(detail["clip_best_prompt"]),
                clip_best_similarity=float(detail["clip_best_similarity"]),
                clip_second_similarity=float(detail["clip_second_similarity"]),
                clip_margin=float(detail["clip_margin"]),
                clip_entropy=float(detail["clip_entropy"]),
                resolved_label_confidence=float(detail["resolved_label_confidence"]),
                is_semantically_ambiguous=bool(detail["is_semantically_ambiguous"]),
                semantic_gate_score=float(detail["semantic_gate_score"]),
                semantic_gate_passed=bool(detail["semantic_gate_passed"]),
                semantic_gate_reason=str(detail["semantic_gate_reason"]),
                final_score=float(detail["final_score"]),
            )
        )

    detections.sort(key=lambda det: (det.resolved_label, float(det.center[0])))
    return image_np, deduplicate_detections(detections)


def deduplicate_detections(detections: list[Detection]) -> list[Detection]:
    if not detections:
        return []

    kept: list[Detection] = []
    for detection in sorted(detections, key=lambda det: det.final_score, reverse=True):
        is_duplicate = False
        for existing in kept:
            if existing.resolved_label != detection.resolved_label:
                continue
            center_dist = float(np.linalg.norm(existing.center - detection.center))
            if bbox_iou(existing.box, detection.box) > 0.75 or mask_iou(existing.mask, detection.mask) > 0.85:
                is_duplicate = True
                break
            if center_dist < 18.0:
                area_ratio = max(existing.mask_area, detection.mask_area) / max(min(existing.mask_area, detection.mask_area), 1)
                if area_ratio < 1.25:
                    is_duplicate = True
                    break
        if not is_duplicate:
            kept.append(detection)

    kept.sort(key=lambda det: (det.resolved_label, float(det.center[0])))
    return kept


def compute_match_cost(track: Track, detection: Detection) -> tuple[float, float, float]:
    center_dist = float(np.linalg.norm(track.last_box.reshape(2, 2).mean(axis=0) - detection.center))
    iou = bbox_iou(track.last_box, detection.box)
    prev_area = max(float(np.count_nonzero(track.last_mask)), 1.0)
    curr_area = max(float(detection.mask_area), 1.0)
    area_ratio = max(prev_area, curr_area) / min(prev_area, curr_area)
    cost = center_dist / 120.0 + (1.0 - iou) * 0.7 + abs(math.log(area_ratio)) * 0.3
    return cost, center_dist, iou


def greedy_match(
    tracks: list[Track],
    detections: list[Detection],
    max_center_distance_px: float,
) -> tuple[list[tuple[int, int]], list[int], list[int]]:
    candidates: list[tuple[float, int, int, float, float]] = []
    for track_idx, track in enumerate(tracks):
        for det_idx, detection in enumerate(detections):
            cost, center_dist, iou = compute_match_cost(track, detection)
            if center_dist <= max_center_distance_px or iou >= 0.01:
                candidates.append((cost, track_idx, det_idx, center_dist, iou))

    candidates.sort(key=lambda item: item[0])
    used_tracks: set[int] = set()
    used_dets: set[int] = set()
    matches: list[tuple[int, int]] = []
    for _, track_idx, det_idx, _, _ in candidates:
        if track_idx in used_tracks or det_idx in used_dets:
            continue
        used_tracks.add(track_idx)
        used_dets.add(det_idx)
        matches.append((track_idx, det_idx))

    unmatched_tracks = [idx for idx in range(len(tracks)) if idx not in used_tracks]
    unmatched_detections = [idx for idx in range(len(detections)) if idx not in used_dets]
    return matches, unmatched_tracks, unmatched_detections


def draw_mask(image: np.ndarray, mask: np.ndarray, color: tuple[int, int, int], alpha: float = 0.25) -> None:
    overlay = image.astype(np.float32)
    overlay[mask] = overlay[mask] * (1.0 - alpha) + np.array(color, dtype=np.float32) * alpha
    image[:] = overlay.astype(np.uint8)


def annotate_frame(
    image: np.ndarray,
    detections: list[Detection],
    missing_track_ids: list[str],
    frame_issue_texts: list[str],
) -> np.ndarray:
    annotated = image.copy()
    for detection in detections:
        if detection.track_id is None:
            continue
        color = color_for_track(detection.track_id)
        draw_mask(annotated, detection.mask, color)
        x0, y0, x1, y1 = [int(round(v)) for v in detection.box.tolist()]
        cv2.rectangle(annotated, (x0, y0), (x1, y1), color, 2)
        text = f"{detection.track_id} | {detection.resolved_label} | {detection.final_score:.2f}"
        cv2.putText(annotated, text, (x0, max(22, y0 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2, cv2.LINE_AA)

    text_lines = []
    if missing_track_ids:
        text_lines.append("Missing: " + ", ".join(missing_track_ids))
    text_lines.extend(frame_issue_texts[:5])

    for idx, line in enumerate(text_lines):
        y = 24 + idx * 24
        cv2.putText(annotated, line, (16, y), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 3, cv2.LINE_AA)
        cv2.putText(annotated, line, (16, y), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (20, 20, 20), 1, cv2.LINE_AA)

    return annotated


def apply_semantic_memory(track: Track, detection: Detection) -> None:
    memory_features = compute_semantic_memory_features(
        memory=track.clip_memory,
        clip_label=detection.clip_proposed_label,
        confidence=detection.resolved_label_confidence,
        margin=detection.clip_margin,
        gate_score=detection.semantic_gate_score,
        gate_passed=detection.semantic_gate_passed,
    )
    detection.semantic_memory_label = str(memory_features["semantic_memory_label"])
    detection.semantic_posterior_score = float(memory_features["semantic_posterior_score"])
    detection.semantic_consistency = float(memory_features["semantic_consistency"])
    detection.semantic_persistence = float(memory_features["semantic_persistence"])
    detection.label_flip_count = int(memory_features["label_flip_count"])
    detection.mean_margin = float(memory_features["mean_margin"])
    detection.history_observations = int(memory_features["history_observations"])

    track.clip_memory.update(
        clip_label=detection.clip_proposed_label,
        confidence=detection.resolved_label_confidence,
        margin=detection.clip_margin,
        gate_score=detection.semantic_gate_score,
        gate_passed=detection.semantic_gate_passed,
    )


def summarize_tracks(tracks: list[Track], total_frames: int) -> dict[str, dict[str, object]]:
    summaries: dict[str, dict[str, object]] = {}
    for track in tracks:
        present_frames = [det.frame_index for det in track.detections]
        center_shifts = [det.center_shift_px for det in track.detections if det.center_shift_px is not None]
        semantic_posteriors = [det.semantic_posterior_score for det in track.detections]
        semantic_consistencies = [det.semantic_consistency for det in track.detections]
        mean_margins = [det.clip_margin for det in track.detections]
        gate_pass_count = sum(1 for det in track.detections if det.semantic_gate_passed)
        track_span = max(1, (present_frames[-1] - track.created_frame_index + 1)) if present_frames else 1
        final_detection = track.detections[-1] if track.detections else None
        longest_missing_run = 0
        current_run = 0
        missing_set = set(track.missing_frames)
        for frame_index in range(total_frames):
            if frame_index in missing_set:
                current_run += 1
                longest_missing_run = max(longest_missing_run, current_run)
            else:
                current_run = 0

        summaries[track.track_id] = {
            "label": track.label,
            "created_frame_index": track.created_frame_index,
            "num_present_frames": len(track.detections),
            "present_frames": present_frames,
            "missing_frames": track.missing_frames,
            "longest_missing_run": longest_missing_run,
            "max_center_shift_px": max(center_shifts) if center_shifts else 0.0,
            "semantic_memory_label": final_detection.semantic_memory_label if final_detection else track.label,
            "semantic_posterior_mean": float(np.mean(semantic_posteriors)) if semantic_posteriors else 0.0,
            "semantic_consistency_mean": float(np.mean(semantic_consistencies)) if semantic_consistencies else 0.0,
            "label_flip_count": final_detection.label_flip_count if final_detection else 0,
            "mean_margin": float(np.mean(mean_margins)) if mean_margins else 0.0,
            "semantic_persistence": gate_pass_count / track_span,
            "semantic_gate_pass_ratio": gate_pass_count / max(len(track.detections), 1),
            "issue_frames": track.issue_frames,
        }
    return summaries


def main() -> None:
    configure_runtime_stability()
    args = parse_args()
    args.grounding_device = choose_sam2_device(args.grounding_device)
    args.sam2_device = choose_sam2_device(args.sam2_device)
    args.openclip_device = resolve_openclip_device(args.openclip_device)
    enable_torch_optimizations(args.sam2_device)
    target_labels = {normalize_label(label) for label in args.target_labels.split(",") if normalize_label(label)}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    annotated_dir = args.output_dir / "annotated_frames"
    annotated_dir.mkdir(parents=True, exist_ok=True)

    frame_paths = sorted(args.frames_dir.glob("*.jpg"))[: args.max_frames]
    if not frame_paths:
        raise FileNotFoundError(f"No JPG frames found in {args.frames_dir}")

    preload_runtime_models(args)
    from transformers import AutoProcessor
    from sam2.build_sam import build_sam2
    from sam2.sam2_image_predictor import SAM2ImagePredictor

    sam2_model = build_sam2(args.sam2_config, str(args.sam2_checkpoint), device=args.sam2_device)
    predictor = SAM2ImagePredictor(sam2_model)
    processor = AutoProcessor.from_pretrained(args.hf_snapshot, local_files_only=True, use_fast=False)
    model = load_grounding_model(args.hf_snapshot, args.grounding_device)
    gc.collect()
    if args.openclip_device == "cuda" or args.sam2_device == "cuda" or args.grounding_device == "cuda":
        torch.cuda.empty_cache()

    tracks: list[Track] = []
    next_extra_index: defaultdict[str, int] = defaultdict(int)
    frame_records: list[dict[str, object]] = []
    csv_rows: list[dict[str, object]] = []

    for frame_index, frame_path in enumerate(frame_paths):
        image_np, detections = detect_frame(
            frame_path=frame_path,
            frame_index=frame_index,
            args=args,
            processor=processor,
            model=model,
            predictor=predictor,
            target_labels=target_labels,
        )

        frame_issue_texts: list[str] = []
        missing_track_ids: list[str] = []

        if frame_index == 0:
            grouped: defaultdict[str, list[Detection]] = defaultdict(list)
            for detection in detections:
                grouped[detection.resolved_label].append(detection)

            for label, items in grouped.items():
                items.sort(key=lambda det: float(det.center[0]))
                for order, detection in enumerate(items):
                    track_id = track_id_from_order(label, order, len(items))
                    detection.track_id = track_id
                    track = Track(
                        track_id=track_id,
                        label=label,
                        created_frame_index=frame_index,
                        last_box=detection.box.copy(),
                        last_mask=detection.mask.copy(),
                        last_frame_index=frame_index,
                        clip_memory=SemanticTrackMemory(
                            max_history=args.clip_memory_size,
                            posterior_alpha=args.clip_memory_alpha,
                        ),
                    )
                    apply_semantic_memory(track, detection)
                    track.detections = [detection]
                    tracks.append(track)
        else:
            detections_by_label: defaultdict[str, list[Detection]] = defaultdict(list)
            for detection in detections:
                detections_by_label[detection.resolved_label].append(detection)

            tracks_by_label: defaultdict[str, list[Track]] = defaultdict(list)
            for track in tracks:
                tracks_by_label[track.label].append(track)

            all_labels = sorted(set(tracks_by_label) | set(detections_by_label))
            for label in all_labels:
                label_tracks = sorted(tracks_by_label.get(label, []), key=lambda track: track.track_id)
                label_detections = sorted(detections_by_label.get(label, []), key=lambda det: float(det.center[0]))

                if not label_tracks:
                    for detection in label_detections:
                        next_extra_index[label] += 1
                        track_id = f"{label.replace(' ', '_')}_extra_{next_extra_index[label]:02d}"
                        detection.track_id = track_id
                        track = Track(
                            track_id=track_id,
                            label=label,
                            created_frame_index=frame_index,
                            last_box=detection.box.copy(),
                            last_mask=detection.mask.copy(),
                            last_frame_index=frame_index,
                            clip_memory=SemanticTrackMemory(
                                max_history=args.clip_memory_size,
                                posterior_alpha=args.clip_memory_alpha,
                            ),
                        )
                        apply_semantic_memory(track, detection)
                        track.detections = [detection]
                        tracks.append(track)
                        frame_issue_texts.append(f"new track: {track_id}")
                    continue

                matches, unmatched_track_indices, unmatched_detection_indices = greedy_match(
                    tracks=label_tracks,
                    detections=label_detections,
                    max_center_distance_px=args.match_max_center_distance_px,
                )

                for track_idx, det_idx in matches:
                    track = label_tracks[track_idx]
                    detection = label_detections[det_idx]
                    detection.track_id = track.track_id
                    gap = frame_index - track.last_frame_index
                    detection.gap_from_prev = gap
                    detection.center_shift_px = float(np.linalg.norm(track.last_box.reshape(2, 2).mean(axis=0) - detection.center))
                    detection.bbox_iou_prev = bbox_iou(track.last_box, detection.box)
                    detection.mask_iou_prev = mask_iou(track.last_mask, detection.mask)
                    previous_mask_area = max(float(np.count_nonzero(track.last_mask)), 1.0)
                    detection.area_ratio_prev = max(previous_mask_area, float(detection.mask_area)) / min(
                        previous_mask_area, float(detection.mask_area)
                    )

                    issue_types: list[str] = []
                    if gap > 1:
                        issue_types.append(f"recovered_after_{gap - 1}_missing")
                    if gap == 1 and detection.center_shift_px > args.jump_center_distance_px:
                        issue_types.append("box_jump")
                    if gap == 1 and detection.bbox_iou_prev < args.jump_bbox_iou_threshold:
                        issue_types.append("low_bbox_iou")
                    if gap == 1 and detection.mask_iou_prev < args.jump_mask_iou_threshold:
                        issue_types.append("low_mask_iou")
                    if gap == 1 and detection.area_ratio_prev > args.jump_area_ratio_threshold:
                        issue_types.append("area_jump")

                    if issue_types:
                        issue_record = {
                            "frame_index": frame_index,
                            "types": issue_types,
                            "center_shift_px": detection.center_shift_px,
                            "bbox_iou_prev": detection.bbox_iou_prev,
                            "mask_iou_prev": detection.mask_iou_prev,
                            "area_ratio_prev": detection.area_ratio_prev,
                        }
                        track.issue_frames.append(issue_record)
                        frame_issue_texts.append(f"{track.track_id}: {','.join(issue_types)}")

                    apply_semantic_memory(track, detection)
                    track.detections.append(detection)
                    track.last_box = detection.box.copy()
                    track.last_mask = detection.mask.copy()
                    track.last_frame_index = frame_index

                for unmatched_track_idx in unmatched_track_indices:
                    track = label_tracks[unmatched_track_idx]
                    track.missing_frames.append(frame_index)
                    missing_track_ids.append(track.track_id)

                for unmatched_detection_idx in unmatched_detection_indices:
                    detection = label_detections[unmatched_detection_idx]
                    next_extra_index[label] += 1
                    track_id = f"{label.replace(' ', '_')}_extra_{next_extra_index[label]:02d}"
                    detection.track_id = track_id
                    track = Track(
                        track_id=track_id,
                        label=label,
                        created_frame_index=frame_index,
                        last_box=detection.box.copy(),
                        last_mask=detection.mask.copy(),
                        last_frame_index=frame_index,
                        clip_memory=SemanticTrackMemory(
                            max_history=args.clip_memory_size,
                            posterior_alpha=args.clip_memory_alpha,
                        ),
                    )
                    apply_semantic_memory(track, detection)
                    track.detections = [detection]
                    tracks.append(track)
                    frame_issue_texts.append(f"new track: {track_id}")

        present_track_ids = [det.track_id for det in detections if det.track_id]
        frame_record = {
            "frame_index": frame_index,
            "frame_name": frame_path.name,
            "present_track_ids": present_track_ids,
            "missing_track_ids": missing_track_ids,
            "issues": frame_issue_texts,
            "detections": [],
        }

        for detection in detections:
            frame_record["detections"].append(
                {
                    "track_id": detection.track_id,
                    "resolved_label": detection.resolved_label,
                    "grounding_label": detection.grounding_label,
                    "clip_proposed_label": detection.clip_proposed_label,
                    "grounding_score": detection.grounding_score,
                    "clip_similarity": detection.clip_similarity,
                    "clip_best_prompt": detection.clip_best_prompt,
                    "clip_best_similarity": detection.clip_best_similarity,
                    "clip_second_similarity": detection.clip_second_similarity,
                    "clip_margin": detection.clip_margin,
                    "clip_entropy": detection.clip_entropy,
                    "resolved_label_confidence": detection.resolved_label_confidence,
                    "is_semantically_ambiguous": detection.is_semantically_ambiguous,
                    "semantic_gate_score": detection.semantic_gate_score,
                    "semantic_gate_passed": detection.semantic_gate_passed,
                    "semantic_gate_reason": detection.semantic_gate_reason,
                    "semantic_memory_label": detection.semantic_memory_label,
                    "semantic_posterior_score": detection.semantic_posterior_score,
                    "semantic_consistency": detection.semantic_consistency,
                    "semantic_persistence": detection.semantic_persistence,
                    "label_flip_count": detection.label_flip_count,
                    "mean_margin": detection.mean_margin,
                    "history_observations": detection.history_observations,
                    "final_score": detection.final_score,
                    "box_xyxy": [float(v) for v in detection.box.tolist()],
                    "mask_area_px": detection.mask_area,
                    "center_xy_px": [float(v) for v in detection.center.tolist()],
                    "center_shift_px": detection.center_shift_px,
                    "bbox_iou_prev": detection.bbox_iou_prev,
                    "mask_iou_prev": detection.mask_iou_prev,
                    "area_ratio_prev": detection.area_ratio_prev,
                    "gap_from_prev": detection.gap_from_prev,
                }
            )
            csv_rows.append(
                {
                    "frame_index": frame_index,
                    "frame_name": frame_path.name,
                    "track_id": detection.track_id or "",
                    "resolved_label": detection.resolved_label,
                    "grounding_label": detection.grounding_label,
                    "clip_proposed_label": detection.clip_proposed_label,
                    "grounding_score": f"{detection.grounding_score:.6f}",
                    "clip_similarity": f"{detection.clip_similarity:.6f}",
                    "clip_best_prompt": detection.clip_best_prompt,
                    "clip_best_similarity": f"{detection.clip_best_similarity:.6f}",
                    "clip_second_similarity": f"{detection.clip_second_similarity:.6f}",
                    "clip_margin": f"{detection.clip_margin:.6f}",
                    "clip_entropy": f"{detection.clip_entropy:.6f}",
                    "resolved_label_confidence": f"{detection.resolved_label_confidence:.6f}",
                    "is_semantically_ambiguous": int(detection.is_semantically_ambiguous),
                    "semantic_gate_score": f"{detection.semantic_gate_score:.6f}",
                    "semantic_gate_passed": int(detection.semantic_gate_passed),
                    "semantic_gate_reason": detection.semantic_gate_reason,
                    "semantic_memory_label": detection.semantic_memory_label,
                    "semantic_posterior_score": f"{detection.semantic_posterior_score:.6f}",
                    "semantic_consistency": f"{detection.semantic_consistency:.6f}",
                    "semantic_persistence": f"{detection.semantic_persistence:.6f}",
                    "label_flip_count": detection.label_flip_count,
                    "mean_margin": f"{detection.mean_margin:.6f}",
                    "history_observations": detection.history_observations,
                    "final_score": f"{detection.final_score:.6f}",
                    "box_x0": f"{detection.box[0]:.3f}",
                    "box_y0": f"{detection.box[1]:.3f}",
                    "box_x1": f"{detection.box[2]:.3f}",
                    "box_y1": f"{detection.box[3]:.3f}",
                    "mask_area_px": detection.mask_area,
                    "center_x_px": f"{detection.center[0]:.3f}",
                    "center_y_px": f"{detection.center[1]:.3f}",
                    "center_shift_px": "" if detection.center_shift_px is None else f"{detection.center_shift_px:.3f}",
                    "bbox_iou_prev": "" if detection.bbox_iou_prev is None else f"{detection.bbox_iou_prev:.6f}",
                    "mask_iou_prev": "" if detection.mask_iou_prev is None else f"{detection.mask_iou_prev:.6f}",
                    "area_ratio_prev": "" if detection.area_ratio_prev is None else f"{detection.area_ratio_prev:.6f}",
                    "gap_from_prev": "" if detection.gap_from_prev is None else detection.gap_from_prev,
                }
            )

        annotated = annotate_frame(image_np, detections, missing_track_ids, frame_issue_texts)
        cv2.imwrite(str(annotated_dir / f"annotated_{frame_index:05d}.jpg"), annotated)
        frame_records.append(frame_record)
        del image_np, detections, annotated
        if args.openclip_device == "cuda" or args.sam2_device == "cuda" or args.grounding_device == "cuda":
            torch.cuda.empty_cache()
        if (frame_index + 1) % 8 == 0:
            gc.collect()

    track_summaries = summarize_tracks(tracks, total_frames=len(frame_paths))
    report = {
        "frames_dir": str(args.frames_dir),
        "prompt": args.prompt,
        "openclip_text_prompt": args.openclip_text_prompt or args.prompt,
        "openclip_soft_gate": bool(args.openclip_soft_gate),
        "clip_memory_size": args.clip_memory_size,
        "clip_memory_alpha": args.clip_memory_alpha,
        "target_labels": sorted(target_labels),
        "num_frames": len(frame_paths),
        "tracks": track_summaries,
        "frames": frame_records,
    }

    report_path = args.output_dir / "stability_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    csv_path = args.output_dir / "per_frame_detections.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = list(csv_rows[0].keys()) if csv_rows else []
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if fieldnames:
            writer.writeheader()
            writer.writerows(csv_rows)

    video_path = args.output_dir / "stability_review.mp4"
    create_video_from_images(str(annotated_dir), str(video_path), frame_rate=args.video_fps)

    print(json.dumps({"report_path": str(report_path), "csv_path": str(csv_path), "video_path": str(video_path)}, indent=2))


if __name__ == "__main__":
    main()
