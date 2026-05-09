"""
Run local Grounding DINO + SAM2 image inference and emit ObjectObservation JSONs.

This is the smallest runnable bridge from the original single-image Grounded-SAM-2
stack into the paper-v1 observation pipeline in this repo.
"""

from __future__ import annotations

import argparse
import inspect
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


DEFAULT_HF_SNAPSHOT = (
    Path.home()
    / ".cache"
    / "huggingface"
    / "hub"
    / "models--IDEA-Research--grounding-dino-tiny"
    / "snapshots"
    / "a2bb814dd30d776dcf7e30523b00659f4f141c71"
)

DEFAULT_SAM2_CANDIDATES: list[tuple[Path, str]] = [
    (Path("./checkpoints/sam2.1_hiera_tiny_wrapped.pt"), "configs/sam2.1/sam2.1_hiera_t.yaml"),
    (Path("./checkpoints/sam2.1_hiera_tiny_converted.pt"), "configs/sam2.1/sam2.1_hiera_t.yaml"),
    (Path("./checkpoints/sam2_hiera_small.pt"), "configs/sam2/sam2_hiera_s.yaml"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rgb", type=Path, default=Path("notebooks/images/truck.jpg"))
    parser.add_argument("--prompt", type=str, default="car. tire.")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/local_grounded_sam2_observation_demo"))
    parser.add_argument("--session-id", type=str, default="local_grounded_sam2_demo")
    parser.add_argument("--frame-id", type=str, default=None)
    parser.add_argument("--frame-index", type=int, default=0)
    parser.add_argument("--timestamp", type=float, default=None)
    parser.add_argument("--box-threshold", type=float, default=0.35)
    parser.add_argument("--text-threshold", type=float, default=0.25)
    parser.add_argument("--max-detections", type=int, default=8)
    parser.add_argument("--hf-snapshot", type=Path, default=DEFAULT_HF_SNAPSHOT)
    parser.add_argument("--sam2-checkpoint", type=Path, default=None)
    parser.add_argument("--sam2-config", type=str, default=None)
    parser.add_argument("--grounding-device", type=str, default="auto", choices=["auto", "cpu", "cuda"])
    parser.add_argument("--sam2-device", type=str, default="auto", choices=["auto", "cpu", "cuda"])
    parser.add_argument("--detector-name", type=str, default="grounding_dino_hf")
    parser.add_argument("--segmentor-name", type=str, default="sam2_auto")
    parser.add_argument("--camera-key", type=str, default="image")
    parser.add_argument("--coordinate-frame", type=str, default="image")
    return parser.parse_args()


def normalize_prompt(prompt: str) -> str:
    normalized = prompt.strip().lower()
    if not normalized.endswith("."):
        normalized += "."
    return normalized


def slugify(label: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
    return slug or "object"


def resolve_grounding_snapshot(path: Path) -> Path:
    if path.is_dir():
        return path
    raise FileNotFoundError(
        "Grounding DINO snapshot not found. "
        f"Expected a local snapshot at {path}."
    )


def resolve_sam2_assets(checkpoint: Path | None, config: str | None) -> tuple[Path, str]:
    if checkpoint is not None and config is not None:
        if not checkpoint.is_file():
            raise FileNotFoundError(f"SAM2 checkpoint not found: {checkpoint}")
        return checkpoint, config

    for candidate_checkpoint, candidate_config in DEFAULT_SAM2_CANDIDATES:
        if checkpoint is not None and candidate_checkpoint.resolve() != checkpoint.resolve():
            continue
        if config is not None and candidate_config != config:
            continue
        if candidate_checkpoint.is_file():
            return candidate_checkpoint, candidate_config

    attempted = [
        f"{candidate_checkpoint} ({candidate_config})"
        for candidate_checkpoint, candidate_config in DEFAULT_SAM2_CANDIDATES
    ]
    raise FileNotFoundError(
        "Could not resolve a local SAM2 checkpoint/config pair. "
        f"Tried: {attempted}"
    )


def save_overlay(image_np, mask, output_path: Path) -> None:
    from PIL import Image
    import numpy as np

    overlay = image_np.copy()
    overlay[mask] = (0.65 * overlay[mask] + 0.35 * np.array([255, 0, 0])).astype(np.uint8)
    Image.fromarray(overlay).save(output_path)


def choose_device(requested: str, torch_module) -> str:
    if requested == "auto":
        return "cuda" if torch_module.cuda.is_available() else "cpu"
    if requested == "cuda" and not torch_module.cuda.is_available():
        return "cpu"
    return requested


def post_process_grounding_results(
    processor,
    outputs,
    input_ids,
    image_size: tuple[int, int],
    box_threshold: float,
    text_threshold: float,
):
    signature = inspect.signature(processor.post_process_grounded_object_detection)
    kwargs = {
        "outputs": outputs,
        "input_ids": input_ids,
        "target_sizes": [image_size[::-1]],
    }
    parameters = signature.parameters
    if "threshold" in parameters:
        kwargs["threshold"] = box_threshold
    elif "box_threshold" in parameters:
        kwargs["box_threshold"] = box_threshold
    if "text_threshold" in parameters:
        kwargs["text_threshold"] = text_threshold
    return processor.post_process_grounded_object_detection(**kwargs)[0]


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    rgb_path = args.rgb.resolve()
    if not rgb_path.is_file():
        raise FileNotFoundError(f"RGB image not found: {rgb_path}")

    grounding_snapshot = resolve_grounding_snapshot(args.hf_snapshot.resolve())
    sam2_checkpoint, sam2_config = resolve_sam2_assets(
        args.sam2_checkpoint.resolve() if args.sam2_checkpoint else None,
        args.sam2_config,
    )

    import numpy as np
    import torch
    from PIL import Image
    from sam2.build_sam import build_sam2
    from sam2.sam2_image_predictor import SAM2ImagePredictor
    from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

    grounding_device = choose_device(args.grounding_device, torch)
    sam2_device = choose_device(args.sam2_device, torch)

    frontend_dir = args.output_dir / "frontend_output"
    observation_dir = args.output_dir / "observation_output"
    frontend_dir.mkdir(parents=True, exist_ok=True)
    observation_dir.mkdir(parents=True, exist_ok=True)

    prompt = normalize_prompt(args.prompt)
    image = Image.open(rgb_path).convert("RGB")
    image_np = np.array(image)

    processor = AutoProcessor.from_pretrained(grounding_snapshot, local_files_only=True, use_fast=False)
    grounding_model = AutoModelForZeroShotObjectDetection.from_pretrained(
        grounding_snapshot,
        local_files_only=True,
    ).to(grounding_device)

    inputs = processor(images=image, text=prompt, return_tensors="pt").to(grounding_device)
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

    boxes = results["boxes"].detach().cpu().numpy()
    grounding_scores = results["scores"].detach().cpu().numpy()
    labels = [str(label).strip() for label in results["labels"]]

    if len(boxes) == 0:
        raise ValueError(f"No detections found for prompt: {prompt!r}")

    order = np.argsort(-grounding_scores)
    if args.max_detections > 0:
        order = order[: args.max_detections]
    boxes = boxes[order]
    grounding_scores = grounding_scores[order]
    labels = [labels[index] for index in order]

    sam2_model = build_sam2(sam2_config, str(sam2_checkpoint), device=sam2_device)
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

    label_counts: defaultdict[str, int] = defaultdict(int)
    instances: list[dict[str, object]] = []
    for box, label, score, mask in zip(boxes, labels, grounding_scores, masks):
        mask_bool = mask > 0
        index = label_counts[label]
        label_counts[label] += 1
        stem = f"{slugify(label)}_{index:05d}"

        mask_path = frontend_dir / f"{stem}_mask.png"
        overlay_path = frontend_dir / f"{stem}_overlay.png"
        summary_path = frontend_dir / f"{stem}_summary.json"

        Image.fromarray((mask_bool.astype(np.uint8) * 255)).save(mask_path)
        save_overlay(image_np, mask_bool, overlay_path)

        mask_area_px = int(mask_bool.sum())
        summary = {
            "method": "grounded_sam2_semantic_only_demo",
            "rgb_path": str(rgb_path),
            "object_name": stem,
            "mask_path": str(mask_path),
            "bbox_xyxy": [float(v) for v in box.tolist()],
            "mask_area_px": mask_area_px,
            "coordinate_frame": args.coordinate_frame,
            "geometry_available": False,
            "stats": {
                "mask_area_px": mask_area_px,
            },
            "outputs": {
                "overlay": str(overlay_path),
            },
        }
        summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

        score_value = float(score)
        instances.append(
            {
                "object_name": stem,
                "resolved_label": label,
                "grounding_label": label,
                "grounding_score": score_value,
                "clip_best_prompt": label,
                "clip_best_similarity": score_value,
                "clip_margin": 0.0,
                "final_score": score_value,
                "box_xyxy": [float(v) for v in box.tolist()],
                "mask_path": str(mask_path),
                "overlay_path": str(overlay_path),
                "summary_path": str(summary_path),
                "pointcloud_path": None,
                "mask_area_px": mask_area_px,
                "error": None,
            }
        )

    manifest = {
        "rgb_path": str(rgb_path),
        "depth_path": None,
        "prompt": prompt,
        "openclip_text_prompt": None,
        "target_labels": sorted({str(item["resolved_label"]) for item in instances}),
        "num_instances": len(instances),
        "instances": instances,
    }
    manifest_path = frontend_dir / "all_instances_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    cmd = [
        sys.executable,
        str((repo_root / "tools" / "build_object_observations.py").resolve()),
        "--manifest",
        str(manifest_path.resolve()),
        "--output-dir",
        str(observation_dir.resolve()),
        "--session-id",
        args.session_id,
        "--frame-index",
        str(args.frame_index),
        "--detector",
        args.detector_name,
        "--segmentor",
        args.segmentor_name,
        "--reranker",
        "none",
        "--geometry-init",
        "none",
        "--camera-key",
        args.camera_key,
        "--coordinate-frame",
        args.coordinate_frame,
    ]
    if args.frame_id:
        cmd.extend(["--frame-id", args.frame_id])
    if args.timestamp is not None:
        cmd.extend(["--timestamp", str(args.timestamp)])

    subprocess.run(cmd, check=True, cwd=repo_root)

    result = {
        "rgb_path": str(rgb_path),
        "prompt": prompt,
        "resolved_grounding_snapshot": str(grounding_snapshot),
        "resolved_sam2_checkpoint": str(sam2_checkpoint.resolve()),
        "resolved_sam2_config": sam2_config,
        "num_instances": len(instances),
        "manifest_path": str(manifest_path.resolve()),
        "observations_index_path": str((observation_dir / "observations_index.json").resolve()),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
