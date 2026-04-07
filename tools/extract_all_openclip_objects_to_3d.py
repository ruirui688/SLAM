"""
Extract all target-category instances from one RGB-D frame and initialize each
as a separate 3D point-cloud segment.

Pipeline:
1. Grounding DINO proposes candidate boxes from a combined text prompt.
2. OpenCLIP reranks the candidates and resolves a final category per box.
3. SAM2 refines each kept box into a 2D mask.
4. The OVO-style geometric initializer backprojects each mask into 3D.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor

try:
    from tools.openclip_reranker import (
        DEFAULT_OPENCLIP_LABEL_MARGIN,
        DEFAULT_OPENCLIP_LABEL_MIN_SIMILARITY,
        DEFAULT_OPENCLIP_MODEL,
        DEFAULT_OPENCLIP_PRETRAINED,
        DEFAULT_OPENCLIP_SCORE_WEIGHT,
        DEFAULT_OPENCLIP_UNKNOWN_LABEL,
        rerank_detections_with_openclip,
    )
    from tools.ovo_init_mask_to_pointcloud import (
        backproject_masked_points,
        ensure_dir,
        load_intrinsics,
        load_rgb_depth_mask,
        point_cloud_stats,
        write_ascii_ply,
    )
except ImportError:
    from openclip_reranker import (
        DEFAULT_OPENCLIP_LABEL_MARGIN,
        DEFAULT_OPENCLIP_LABEL_MIN_SIMILARITY,
        DEFAULT_OPENCLIP_MODEL,
        DEFAULT_OPENCLIP_PRETRAINED,
        DEFAULT_OPENCLIP_SCORE_WEIGHT,
        DEFAULT_OPENCLIP_UNKNOWN_LABEL,
        rerank_detections_with_openclip,
    )
    from ovo_init_mask_to_pointcloud import (
        backproject_masked_points,
        ensure_dir,
        load_intrinsics,
        load_rgb_depth_mask,
        point_cloud_stats,
        write_ascii_ply,
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
    parser.add_argument("--rgb", type=Path, required=True)
    parser.add_argument("--depth", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--prompt", type=str, default="wooden crate. yellow barrier.")
    parser.add_argument("--target-labels", type=str, default="wooden crate,yellow barrier")
    parser.add_argument("--box-threshold", type=float, default=0.25)
    parser.add_argument("--text-threshold", type=float, default=0.25)
    parser.add_argument("--hf-snapshot", type=Path, default=DEFAULT_HF_SNAPSHOT)
    parser.add_argument("--clip-score-weight", type=float, default=DEFAULT_OPENCLIP_SCORE_WEIGHT)
    parser.add_argument("--openclip-model", type=str, default=DEFAULT_OPENCLIP_MODEL)
    parser.add_argument("--openclip-pretrained", type=str, default=DEFAULT_OPENCLIP_PRETRAINED)
    parser.add_argument("--openclip-text-prompt", type=str, default=None)
    parser.add_argument("--openclip-device", type=str, default="cpu", choices=["auto", "cpu", "cuda"])
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
    parser.add_argument("--calibration-file", type=Path, default=None)
    parser.add_argument("--camera-key", type=str, default="Camera1")
    parser.add_argument("--fx", type=float, default=None)
    parser.add_argument("--fy", type=float, default=None)
    parser.add_argument("--cx", type=float, default=None)
    parser.add_argument("--cy", type=float, default=None)
    parser.add_argument("--depth-scale", type=float, default=1000.0)
    parser.add_argument("--min-depth-m", type=float, default=0.1)
    parser.add_argument("--max-depth-m", type=float, default=10.0)
    parser.add_argument("--mask-threshold", type=int, default=127)
    return parser.parse_args()


def normalize_label(label: str) -> str:
    return " ".join(label.strip().rstrip(".").lower().split())


def save_overlay(rgb: np.ndarray, mask: np.ndarray, output_path: Path) -> None:
    overlay = rgb.copy()
    overlay[mask] = (0.65 * overlay[mask] + 0.35 * np.array([255, 0, 0])).astype(np.uint8)
    Image.fromarray(overlay).save(output_path)


def choose_sam2_device(device: str) -> str:
    if device == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        return "cpu"
    return device


def instance_stem(label: str, index: int, total: int, box: np.ndarray, ordered_boxes: list[np.ndarray]) -> str:
    base = label.replace(" ", "_")
    if total == 1:
        return base
    if total == 2:
        x_centers = [float((b[0] + b[2]) * 0.5) for b in ordered_boxes]
        rank = x_centers.index(float((box[0] + box[2]) * 0.5))
        return f"{base}_{'left' if rank == 0 else 'right'}"
    return f"{base}_{index + 1:02d}"


def write_pointcloud_outputs(
    args: argparse.Namespace,
    rgb_path: Path,
    depth_path: Path,
    mask_path: Path,
    object_name: str,
) -> dict[str, object]:
    intrinsics = load_intrinsics(args)
    rgb, depth, mask = load_rgb_depth_mask(rgb_path, depth_path, mask_path, args.mask_threshold)
    points, colors, pixels = backproject_masked_points(
        rgb=rgb,
        depth_u16=depth,
        mask=mask,
        intrinsics=intrinsics,
        depth_scale=args.depth_scale,
        min_depth_m=args.min_depth_m,
        max_depth_m=args.max_depth_m,
    )

    stem = object_name.replace(" ", "_")
    ply_path = args.output_dir / f"{stem}_pointcloud.ply"
    npz_path = args.output_dir / f"{stem}_pointcloud.npz"
    json_path = args.output_dir / f"{stem}_summary.json"

    write_ascii_ply(ply_path, points, colors)
    np.savez_compressed(
        npz_path,
        points_xyz_m=points.astype(np.float32),
        colors_rgb_u8=colors.astype(np.uint8),
        pixels_uv=pixels.astype(np.int32),
    )

    summary = {
        "method": "OVO-inspired minimal object initialization",
        "rgb_path": str(rgb_path),
        "depth_path": str(depth_path),
        "mask_path": str(mask_path),
        "object_name": object_name,
        "intrinsics": {
            "fx": intrinsics.fx,
            "fy": intrinsics.fy,
            "cx": intrinsics.cx,
            "cy": intrinsics.cy,
        },
        "depth_scale": args.depth_scale,
        "min_depth_m": args.min_depth_m,
        "max_depth_m": args.max_depth_m,
        "coordinate_frame": "camera",
        "stats": point_cloud_stats(points),
        "outputs": {
            "ply": str(ply_path),
            "npz": str(npz_path),
        },
    }
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    args = parse_args()
    ensure_dir(args.output_dir)

    target_labels = {normalize_label(label) for label in args.target_labels.split(",") if normalize_label(label)}
    if not target_labels:
        raise ValueError("No valid target labels were provided.")

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
    grounding_scores = results["scores"].cpu().numpy().tolist()
    grounding_labels = [str(label) for label in results["labels"]]

    if len(boxes) == 0:
        raise ValueError(f"No detections found for prompt: {args.prompt!r}")

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

    kept_details = [item for item in score_details if normalize_label(item["resolved_label"]) in target_labels]
    if not kept_details:
        raise ValueError(f"No detections resolved to target labels: {sorted(target_labels)}")

    kept_indices = [item["original_index"] for item in kept_details]
    kept_boxes = boxes[kept_indices]

    sam2_device = choose_sam2_device(args.sam2_device)
    sam2_model = build_sam2(args.sam2_config, str(args.sam2_checkpoint), device=sam2_device)
    predictor = SAM2ImagePredictor(sam2_model)
    predictor.set_image(image_np)
    masks, _, _ = predictor.predict(
        point_coords=None,
        point_labels=None,
        box=kept_boxes,
        multimask_output=False,
    )
    if masks.ndim == 4:
        masks = masks.squeeze(1)

    label_to_entries: dict[str, list[tuple[np.ndarray, dict[str, object], np.ndarray]]] = defaultdict(list)
    for box, detail, mask in zip(kept_boxes, kept_details, masks):
        label_to_entries[normalize_label(str(detail["resolved_label"]))].append((box, detail, mask > 0))

    outputs: list[dict[str, object]] = []
    for label in sorted(label_to_entries):
        entries = sorted(label_to_entries[label], key=lambda item: float((item[0][0] + item[0][2]) * 0.5))
        ordered_boxes = [entry[0] for entry in entries]
        for index, (box, detail, mask) in enumerate(entries):
            stem = f"{instance_stem(label, index, len(entries), box, ordered_boxes)}_00000"
            mask_path = args.output_dir / f"{stem}_mask.png"
            overlay_path = args.output_dir / f"{stem}_overlay.png"
            summary_path = args.output_dir / f"{stem}_summary.json"
            Image.fromarray((mask.astype(np.uint8) * 255)).save(mask_path)
            save_overlay(image_np, mask, overlay_path)
            pointcloud_path: str | None = None
            error_message: str | None = None
            try:
                summary = write_pointcloud_outputs(
                    args=args,
                    rgb_path=args.rgb,
                    depth_path=args.depth,
                    mask_path=mask_path,
                    object_name=stem,
                )
                pointcloud_path = str(summary["outputs"]["ply"])
            except Exception as exc:
                error_message = str(exc)
                summary = {
                    "method": "OVO-inspired minimal object initialization",
                    "rgb_path": str(args.rgb),
                    "depth_path": str(args.depth),
                    "mask_path": str(mask_path),
                    "object_name": stem,
                    "error": error_message,
                }
                summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

            outputs.append(
                {
                    "object_name": stem,
                    "resolved_label": label,
                    "grounding_label": detail["grounding_label"],
                    "grounding_score": detail["grounding_score"],
                    "clip_best_prompt": detail["clip_best_prompt"],
                    "clip_best_similarity": detail["clip_best_similarity"],
                    "clip_margin": detail["clip_margin"],
                    "final_score": detail["final_score"],
                    "box_xyxy": [float(v) for v in box.tolist()],
                    "mask_path": str(mask_path),
                    "overlay_path": str(overlay_path),
                    "summary_path": str(summary_path),
                    "pointcloud_path": pointcloud_path,
                    "error": error_message,
                }
            )

    manifest = {
        "rgb_path": str(args.rgb),
        "depth_path": str(args.depth),
        "prompt": args.prompt,
        "openclip_text_prompt": args.openclip_text_prompt or args.prompt,
        "target_labels": sorted(target_labels),
        "num_instances": len(outputs),
        "instances": outputs,
    }
    manifest_path = args.output_dir / "all_instances_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
