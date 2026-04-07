"""
Single-frame 2D mask extraction with Grounding DINO + SAM2.

This helper is intentionally small and separate from the OVO-style 2D->3D
initialization script. It exists only to generate the 2D mask input.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor
try:
    from tools.openclip_reranker import (
        DEFAULT_OPENCLIP_MODEL,
        DEFAULT_OPENCLIP_LABEL_MARGIN,
        DEFAULT_OPENCLIP_LABEL_MIN_SIMILARITY,
        DEFAULT_OPENCLIP_PRETRAINED,
        DEFAULT_OPENCLIP_SCORE_WEIGHT,
        DEFAULT_OPENCLIP_UNKNOWN_LABEL,
        rerank_detections_with_openclip,
    )
except ImportError:
    from openclip_reranker import (
        DEFAULT_OPENCLIP_MODEL,
        DEFAULT_OPENCLIP_LABEL_MARGIN,
        DEFAULT_OPENCLIP_LABEL_MIN_SIMILARITY,
        DEFAULT_OPENCLIP_PRETRAINED,
        DEFAULT_OPENCLIP_SCORE_WEIGHT,
        DEFAULT_OPENCLIP_UNKNOWN_LABEL,
        rerank_detections_with_openclip,
    )


DEFAULT_HF_SNAPSHOT = (
    Path.home()
    / ".cache"
    / "huggingface"
    / "hub"
    / "models--IDEA-Research--grounding-dino-tiny"
    / "snapshots"
    / "a2bb814dd30d776dcf7e30523b00659f4f141c71"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rgb", type=Path, required=True, help="Path to the RGB image.")
    parser.add_argument("--prompt", type=str, required=True, help="Grounding prompt, e.g. 'wooden crate.'.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for the extracted mask.")
    parser.add_argument("--name", type=str, default="object", help="Stem for output files.")
    parser.add_argument("--box-threshold", type=float, default=0.25)
    parser.add_argument("--text-threshold", type=float, default=0.25)
    parser.add_argument("--clip-score-weight", type=float, default=DEFAULT_OPENCLIP_SCORE_WEIGHT)
    parser.add_argument("--openclip-model", type=str, default=DEFAULT_OPENCLIP_MODEL)
    parser.add_argument("--openclip-pretrained", type=str, default=DEFAULT_OPENCLIP_PRETRAINED)
    parser.add_argument("--openclip-label-margin", type=float, default=DEFAULT_OPENCLIP_LABEL_MARGIN)
    parser.add_argument("--openclip-label-min-similarity", type=float, default=DEFAULT_OPENCLIP_LABEL_MIN_SIMILARITY)
    parser.add_argument("--unknown-label", type=str, default=DEFAULT_OPENCLIP_UNKNOWN_LABEL)
    parser.add_argument(
        "--openclip-text-prompt",
        type=str,
        default=None,
        help="Optional text vocabulary for OpenCLIP reranking. Defaults to --prompt.",
    )
    parser.add_argument(
        "--openclip-device",
        type=str,
        default="cpu",
        choices=["auto", "cpu", "cuda"],
        help="Device for OpenCLIP reranking.",
    )
    parser.add_argument(
        "--selection-strategy",
        type=str,
        default="highest_score",
        choices=["highest_score", "largest_area", "rightmost", "leftmost", "topmost", "bottommost"],
        help="How to choose one detection when multiple boxes match the prompt.",
    )
    parser.add_argument(
        "--hf-snapshot",
        type=Path,
        default=DEFAULT_HF_SNAPSHOT,
        help="Local Grounding DINO HF snapshot path.",
    )
    parser.add_argument(
        "--sam2-checkpoint",
        type=Path,
        default=Path("./checkpoints/sam2.1_hiera_large.pt"),
    )
    parser.add_argument(
        "--sam2-config",
        type=str,
        default="configs/sam2.1/sam2.1_hiera_l.yaml",
    )
    parser.add_argument(
        "--sam2-device",
        type=str,
        default="auto",
        choices=["auto", "cpu", "cuda"],
        help="Device for SAM2 mask extraction.",
    )
    return parser.parse_args()


def choose_detection(
    labels: list[str],
    scores: np.ndarray,
    boxes: np.ndarray,
    prompt: str,
    strategy: str,
) -> int:
    normalized_prompt = prompt.strip().rstrip(".").lower()
    exact_matches = [i for i, label in enumerate(labels) if label.strip().lower() == normalized_prompt]
    candidate_indices = exact_matches if exact_matches else list(range(len(labels)))
    if not candidate_indices:
        raise ValueError("No candidate detections available.")

    if strategy == "highest_score":
        return max(candidate_indices, key=lambda i: float(scores[i]))

    if strategy == "largest_area":
        return max(
            candidate_indices,
            key=lambda i: float((boxes[i, 2] - boxes[i, 0]) * (boxes[i, 3] - boxes[i, 1])),
        )

    if strategy == "rightmost":
        return max(candidate_indices, key=lambda i: float(boxes[i, 0] + boxes[i, 2]))

    if strategy == "leftmost":
        return min(candidate_indices, key=lambda i: float(boxes[i, 0] + boxes[i, 2]))

    if strategy == "topmost":
        return min(candidate_indices, key=lambda i: float(boxes[i, 1] + boxes[i, 3]))

    if strategy == "bottommost":
        return max(candidate_indices, key=lambda i: float(boxes[i, 1] + boxes[i, 3]))

    raise ValueError(f"Unknown selection strategy: {strategy}")


def save_overlay(rgb: np.ndarray, mask: np.ndarray, output_path: Path) -> None:
    overlay = rgb.copy()
    overlay[mask] = (0.65 * overlay[mask] + 0.35 * np.array([255, 0, 0])).astype(np.uint8)
    Image.fromarray(overlay).save(output_path)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    processor = AutoProcessor.from_pretrained(args.hf_snapshot, local_files_only=True, use_fast=False)
    model = AutoModelForZeroShotObjectDetection.from_pretrained(args.hf_snapshot, local_files_only=True).to("cpu")

    image = Image.open(args.rgb).convert("RGB")
    image_np = np.array(image)

    inputs = processor(images=image, text=args.prompt, return_tensors="pt")
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
    grounding_scores = results["scores"].cpu().numpy()
    labels = [str(label) for label in results["labels"]]

    if len(boxes) == 0:
        raise ValueError(f"No detections found for prompt: {args.prompt!r}")

    reranked = rerank_detections_with_openclip(
        image=image,
        boxes=boxes,
        labels=labels,
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
    order = np.array([item["original_index"] for item in reranked], dtype=np.int64)
    boxes = boxes[order]
    grounding_scores = grounding_scores[order]
    grounding_labels = [labels[idx] for idx in order]
    labels = [item["resolved_label"] for item in reranked]
    clip_similarities = np.array([item["clip_similarity"] for item in reranked], dtype=np.float32)
    final_scores = np.array([item["final_score"] for item in reranked], dtype=np.float32)

    chosen_idx = choose_detection(
        labels=labels,
        scores=final_scores,
        boxes=boxes,
        prompt=args.prompt,
        strategy=args.selection_strategy,
    )
    chosen_box = boxes[chosen_idx : chosen_idx + 1]

    sam2_device = "cuda" if args.sam2_device == "auto" and torch.cuda.is_available() else args.sam2_device
    if sam2_device == "auto":
        sam2_device = "cpu"
    sam2_model = build_sam2(args.sam2_config, str(args.sam2_checkpoint), device=sam2_device)
    predictor = SAM2ImagePredictor(sam2_model)
    predictor.set_image(image_np)
    masks, _, _ = predictor.predict(
        point_coords=None,
        point_labels=None,
        box=chosen_box,
        multimask_output=False,
    )
    if masks.ndim == 4:
        masks = masks.squeeze(1)

    mask = masks[0] > 0
    mask_image = (mask.astype(np.uint8) * 255)

    mask_path = args.output_dir / f"{args.name}_mask.png"
    overlay_path = args.output_dir / f"{args.name}_overlay.png"

    Image.fromarray(mask_image).save(mask_path)
    save_overlay(image_np, mask, overlay_path)

    for idx, (grounding_label, resolved_label, grounding_score, clip_similarity, final_score, box, detail) in enumerate(
        zip(grounding_labels, labels, grounding_scores, clip_similarities, final_scores, boxes, reranked)
    ):
        print(
            f"candidate[{idx}] grounding_label={grounding_label} resolved_label={resolved_label} "
            f"grounding_score={float(grounding_score):.6f} clip_similarity={float(clip_similarity):.6f} "
            f"clip_best_prompt={detail['clip_best_prompt']} clip_margin={float(detail['clip_margin']):.6f} "
            f"final_score={float(final_score):.6f} "
            f"box={box.tolist()}"
        )

    print(f"prompt={args.prompt}")
    print(f"chosen_label={labels[chosen_idx]}")
    print(f"chosen_grounding_label={grounding_labels[chosen_idx]}")
    print(f"chosen_grounding_score={float(grounding_scores[chosen_idx])}")
    print(f"chosen_clip_similarity={float(clip_similarities[chosen_idx])}")
    print(f"chosen_clip_best_prompt={reranked[chosen_idx]['clip_best_prompt']}")
    print(f"chosen_clip_margin={float(reranked[chosen_idx]['clip_margin'])}")
    print(f"chosen_final_score={float(final_scores[chosen_idx])}")
    print(f"selection_strategy={args.selection_strategy}")
    print(f"chosen_box={chosen_box.tolist()}")
    print(f"mask_path={mask_path}")
    print(f"overlay_path={overlay_path}")


if __name__ == "__main__":
    main()
