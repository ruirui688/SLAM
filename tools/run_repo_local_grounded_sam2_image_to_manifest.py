"""
Run a minimal repo-local Grounded-SAM2 + GroundingDINO inference on a single RGB image
and emit an all_instances_manifest.json compatible with the long-term mapping bridge.

This script is designed as the reproducible entrypoint between the original upstream
recognition stack and the custom ObjectObservation pipeline.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import inspect

import numpy as np
import torch
from PIL import Image
from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rgb", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--prompt", type=str, required=True)
    parser.add_argument("--grounding-model", type=str, default="IDEA-Research/grounding-dino-tiny")
    parser.add_argument("--sam2-checkpoint", type=Path, default=Path("./checkpoints/sam2_hiera_small.pt"))
    parser.add_argument("--sam2-config", type=str, default="configs/sam2/sam2_hiera_s.yaml")
    parser.add_argument("--box-threshold", type=float, default=0.25)
    parser.add_argument("--text-threshold", type=float, default=0.25)
    parser.add_argument("--device", type=str, default="auto", choices=["auto", "cpu", "cuda"])
    return parser.parse_args()


def choose_device(name: str) -> str:
    if name == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if name == "cuda" and not torch.cuda.is_available():
        return "cpu"
    return name


def save_overlay(rgb: np.ndarray, mask: np.ndarray, output_path: Path) -> None:
    overlay = rgb.copy()
    overlay[mask] = (0.65 * overlay[mask] + 0.35 * np.array([255, 0, 0])).astype(np.uint8)
    Image.fromarray(overlay).save(output_path)


def post_process_grounding_results(processor, outputs, input_ids, image_size, box_threshold: float, text_threshold: float):
    sig = inspect.signature(processor.post_process_grounded_object_detection)
    kwargs = {
        "outputs": outputs,
        "input_ids": input_ids,
        "target_sizes": [image_size[::-1]],
    }
    params = sig.parameters
    if "threshold" in params:
        kwargs["threshold"] = box_threshold
    elif "box_threshold" in params:
        kwargs["box_threshold"] = box_threshold
    if "text_threshold" in params:
        kwargs["text_threshold"] = text_threshold
    return processor.post_process_grounded_object_detection(**kwargs)[0]


def main() -> None:
    args = parse_args()
    device = choose_device(args.device)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    image = Image.open(args.rgb).convert("RGB")
    image_np = np.array(image)

    processor = AutoProcessor.from_pretrained(args.grounding_model)
    grounding_model = AutoModelForZeroShotObjectDetection.from_pretrained(args.grounding_model).to(device)

    inputs = processor(images=image, text=args.prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = grounding_model(**inputs)

    results = post_process_grounding_results(
        processor=processor,
        outputs=outputs,
        input_ids=inputs.input_ids,
        image_size=image.size,
        box_threshold=args.box_threshold,
        text_threshold=args.text_threshold,
    )

    boxes = results["boxes"].cpu().numpy()
    labels = [str(label) for label in results["labels"]]
    scores = results["scores"].cpu().numpy().tolist()

    if len(boxes) == 0:
        raise ValueError(f"No detections found for prompt: {args.prompt!r}")

    sam2_model = build_sam2(args.sam2_config, str(args.sam2_checkpoint), device=device)
    predictor = SAM2ImagePredictor(sam2_model)
    predictor.set_image(image_np)
    masks, _, _ = predictor.predict(
        point_coords=None,
        point_labels=None,
        box=boxes,
        multimask_output=False,
    )
    if masks.ndim == 4:
        masks = masks.squeeze(1)

    instances: list[dict[str, object]] = []
    for idx, (box, label, score, mask) in enumerate(zip(boxes, labels, scores, masks), start=1):
        stem = f"{label.replace(' ', '_')}_{idx:03d}"
        mask_path = args.output_dir / f"{stem}_mask.png"
        overlay_path = args.output_dir / f"{stem}_overlay.png"
        summary_path = args.output_dir / f"{stem}_summary.json"
        mask_bool = mask > 0
        Image.fromarray((mask_bool.astype(np.uint8) * 255)).save(mask_path)
        save_overlay(image_np, mask_bool, overlay_path)

        y_coords, x_coords = np.nonzero(mask_bool)
        if len(x_coords) == 0:
            bbox_min = bbox_max = bbox_size = None
            centroid = None
            num_points = 0
        else:
            bbox_min = [float(x_coords.min()), float(y_coords.min()), 0.0]
            bbox_max = [float(x_coords.max()), float(y_coords.max()), 0.0]
            bbox_size = [bbox_max[0] - bbox_min[0], bbox_max[1] - bbox_min[1], 0.0]
            centroid = [float(x_coords.mean()), float(y_coords.mean()), 0.0]
            num_points = int(mask_bool.sum())

        summary = {
            "method": "repo-local grounded-sam2 image demo",
            "rgb_path": str(args.rgb),
            "object_name": stem,
            "coordinate_frame": "image",
            "stats": {
                "num_points": num_points,
                "centroid_xyz_m": centroid,
                "bbox_min_xyz_m": bbox_min,
                "bbox_max_xyz_m": bbox_max,
                "bbox_size_xyz_m": bbox_size,
            },
            "outputs": {
                "mask": str(mask_path),
                "overlay": str(overlay_path),
            },
        }
        summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

        instances.append(
            {
                "object_name": stem,
                "resolved_label": label,
                "grounding_label": label,
                "grounding_score": float(score),
                "clip_best_prompt": label,
                "clip_best_similarity": float(score),
                "clip_margin": 0.0,
                "final_score": float(score),
                "box_xyxy": [float(v) for v in box.tolist()],
                "mask_path": str(mask_path),
                "overlay_path": str(overlay_path),
                "summary_path": str(summary_path),
                "pointcloud_path": None,
                "error": None,
            }
        )

    manifest = {
        "rgb_path": str(args.rgb),
        "depth_path": None,
        "prompt": args.prompt,
        "openclip_text_prompt": args.prompt,
        "target_labels": sorted(set(labels)),
        "num_instances": len(instances),
        "instances": instances,
    }
    manifest_path = args.output_dir / "all_instances_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"manifest_path": str(manifest_path), "num_instances": len(instances)}, indent=2))


if __name__ == "__main__":
    main()
