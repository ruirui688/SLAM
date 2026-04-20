"""
Build ObjectObservation records from the outputs of extract_all_openclip_objects_to_3d.py.

This is the first runnable bridge from the current open-vocabulary RGB-D frontend
into the long-term object-map pipeline proposed for the paper.

Inputs:
1. all_instances_manifest.json produced by extract_all_openclip_objects_to_3d.py
2. Optional frame/session metadata from CLI flags

Outputs:
- observations_index.json
- one JSON file per observation under <output-dir>/observations/
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True, help="Path to all_instances_manifest.json")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for ObjectObservation outputs")
    parser.add_argument("--session-id", type=str, required=True)
    parser.add_argument("--frame-id", type=str, default=None)
    parser.add_argument("--frame-index", type=int, default=0)
    parser.add_argument("--timestamp", type=float, default=None)
    parser.add_argument("--tracklet-prefix", type=str, default="trk")
    parser.add_argument("--detector", type=str, default="grounding_dino_hf")
    parser.add_argument("--segmentor", type=str, default="sam2.1")
    parser.add_argument("--reranker", type=str, default="openclip_vit_b32")
    parser.add_argument("--geometry-init", type=str, default="ovo_init_v1")
    parser.add_argument("--camera-key", type=str, default="Camera1")
    parser.add_argument("--coordinate-frame", type=str, default="camera")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def infer_summary(summary_path: str | None) -> dict[str, Any]:
    if not summary_path:
        return {}
    path = Path(summary_path)
    if not path.is_file():
        return {}
    return load_json(path)


def make_observation(
    instance: dict[str, Any],
    summary: dict[str, Any],
    args: argparse.Namespace,
    index: int,
    frame_id: str,
) -> dict[str, Any]:
    stats = summary.get("stats", {}) if isinstance(summary, dict) else {}
    error = instance.get("error") or summary.get("error")
    clip_best_similarity = float(instance.get("clip_best_similarity", 0.0) or 0.0)
    clip_margin = float(instance.get("clip_margin", 0.0) or 0.0)
    semantic_gate_score = float(instance.get("final_score", 0.0) or 0.0)
    grounding_score = float(instance.get("grounding_score", 0.0) or 0.0)
    object_name = str(instance["object_name"])
    observation_id = f"obs_{frame_id}_{index:03d}"

    return {
        "observation_id": observation_id,
        "frame_id": frame_id,
        "session_id": args.session_id,
        "frame_index": args.frame_index,
        "timestamp": args.timestamp,
        "tracklet_id": f"{args.tracklet_prefix}_{args.session_id}_{index:03d}",
        "source_pipeline": {
            "detector": args.detector,
            "segmentor": args.segmentor,
            "reranker": args.reranker,
            "geometry_init": args.geometry_init,
        },
        "camera_key": args.camera_key,
        "object_name": object_name,
        "bbox_xyxy": [float(v) for v in instance.get("box_xyxy", [])],
        "mask_path": instance.get("mask_path"),
        "overlay_path": instance.get("overlay_path"),
        "mask_area_px": None,
        "grounding_label": instance.get("grounding_label"),
        "resolved_label": instance.get("resolved_label"),
        "clip_topk": [
            {
                "label": instance.get("clip_best_prompt", instance.get("resolved_label")),
                "score": clip_best_similarity,
            }
        ],
        "grounding_score": grounding_score,
        "clip_similarity": clip_best_similarity,
        "semantic_gate_score": semantic_gate_score,
        "semantic_gate_passed": error is None,
        "semantic_uncertainty": {
            "entropy": None,
            "margin": clip_margin,
            "unknown_flag": str(instance.get("resolved_label", "")).lower() == "unknown",
            "ambiguity_flag": False,
        },
        "geometry": {
            "pointcloud_path": instance.get("pointcloud_path"),
            "centroid_xyz": stats.get("centroid_xyz_m"),
            "bbox_min_xyz": stats.get("bbox_min_xyz_m"),
            "bbox_max_xyz": stats.get("bbox_max_xyz_m"),
            "bbox_size_xyz": stats.get("bbox_size_xyz_m"),
            "num_points": stats.get("num_points"),
            "coordinate_frame": summary.get("coordinate_frame", args.coordinate_frame),
        },
        "quality": {
            "depth_valid_ratio": None if error else 1.0,
            "mask_stability_score": None,
            "tracking_consistency_score": None,
            "geometry_quality_score": 0.0 if error else 1.0,
        },
        "association": {
            "candidate_map_object_ids": [],
            "candidate_scores": [],
            "matched_map_object_id": None,
            "matched_score": None,
            "association_status": "failed_geometry" if error else "unmatched",
        },
        "artifacts": {
            "summary_path": instance.get("summary_path"),
        },
        "error": error,
    }


def main() -> None:
    args = parse_args()
    manifest = load_json(args.manifest)
    frame_id = args.frame_id or f"{args.session_id}_{args.frame_index:06d}"

    observations_dir = args.output_dir / "observations"
    observations_dir.mkdir(parents=True, exist_ok=True)

    observations: list[dict[str, Any]] = []
    for index, instance in enumerate(manifest.get("instances", []), start=1):
        summary = infer_summary(instance.get("summary_path"))
        observation = make_observation(instance, summary, args, index, frame_id)
        observation_path = observations_dir / f"{observation['observation_id']}.json"
        observation_path.write_text(json.dumps(observation, indent=2, ensure_ascii=False), encoding="utf-8")
        observations.append(observation)

    index_payload = {
        "session_id": args.session_id,
        "frame_id": frame_id,
        "frame_index": args.frame_index,
        "timestamp": args.timestamp,
        "manifest_path": str(args.manifest),
        "rgb_path": manifest.get("rgb_path"),
        "depth_path": manifest.get("depth_path"),
        "prompt": manifest.get("prompt"),
        "openclip_text_prompt": manifest.get("openclip_text_prompt"),
        "target_labels": manifest.get("target_labels", []),
        "num_observations": len(observations),
        "observation_paths": [str(observations_dir / f"{item['observation_id']}.json") for item in observations],
        "observations": observations,
    }
    index_path = args.output_dir / "observations_index.json"
    index_path.write_text(json.dumps(index_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(index_payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
