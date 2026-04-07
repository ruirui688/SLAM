LEGACY_DINOX_SCRIPT = r'''
# dds cloudapi for DINO-X - update to V2Task API
from dds_cloudapi_sdk import Config
from dds_cloudapi_sdk import Client
from dds_cloudapi_sdk.tasks.v2_task import V2Task

import os
import cv2
import torch
import numpy as np
import supervision as sv

from pathlib import Path
from tqdm import tqdm
from PIL import Image
from sam2.build_sam import build_sam2_video_predictor, build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor 
from utils.track_utils import sample_points_from_masks
from utils.video_utils import create_video_from_images

"""
Hyperparam for Ground and Tracking
"""
VIDEO_PATH = r"D:\TorWIC-SLAM\TorWIC SLAM Dataset\Jun. 15, 2022\Aisle_CW_Run_1\image_left_first80.mp4"
TEXT_PROMPT = "wooden crate. mobile robot. warehouse rack. work table. yellow barrier."
OUTPUT_VIDEO_PATH = r"D:\TorWIC-SLAM\TorWIC SLAM Dataset\Jun. 15, 2022\Aisle_CW_Run_1\image_left_first80_dinox_tracking_demo.mp4"
SOURCE_VIDEO_FRAME_DIR = r"D:\TorWIC-SLAM\TorWIC SLAM Dataset\Jun. 15, 2022\Aisle_CW_Run_1\image_left_first80_frames"
SAVE_TRACKING_RESULTS_DIR = r"D:\TorWIC-SLAM\TorWIC SLAM Dataset\Jun. 15, 2022\Aisle_CW_Run_1\image_left_first80_tracking_results"
API_TOKEN_FOR_DINOX = "Your API token"
PROMPT_TYPE_FOR_VIDEO = "box" # choose from ["point", "box", "mask"]
BOX_THRESHOLD = 0.25
IOU_THRESHOLD = 0.5  # 添加IOU阈值参数

"""
Step 1: Environment settings and model initialization for SAM 2
"""
# use bfloat16 for the entire notebook
torch.autocast(device_type="cuda", dtype=torch.bfloat16).__enter__()

if torch.cuda.get_device_properties(0).major >= 8:
    # turn on tfloat32 for Ampere GPUs (https://pytorch.org/docs/stable/notes/cuda.html#tensorfloat-32-tf32-on-ampere-devices)
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

# init sam image predictor and video predictor model
sam2_checkpoint = "./checkpoints/sam2.1_hiera_large.pt"
model_cfg = "configs/sam2.1/sam2.1_hiera_l.yaml"

video_predictor = build_sam2_video_predictor(model_cfg, sam2_checkpoint)
sam2_image_model = build_sam2(model_cfg, sam2_checkpoint)
image_predictor = SAM2ImagePredictor(sam2_image_model)


# # `video_dir` a directory of JPEG frames with filenames like `<frame_index>.jpg`
# video_dir = "notebooks/videos/bedroom"

"""
Custom video input directly using video files
"""
video_info = sv.VideoInfo.from_video_path(VIDEO_PATH)  # get video info
print(video_info)
frame_generator = sv.get_video_frames_generator(VIDEO_PATH, stride=1, start=0, end=None)

# saving video to frames
source_frames = Path(SOURCE_VIDEO_FRAME_DIR)
source_frames.mkdir(parents=True, exist_ok=True)

with sv.ImageSink(
    target_dir_path=source_frames, 
    overwrite=True, 
    image_name_pattern="{:05d}.jpg"
) as sink:
    for frame in tqdm(frame_generator, desc="Saving Video Frames"):
        sink.save_image(frame)

# scan all the JPEG frame names in this directory
frame_names = [
    p for p in os.listdir(SOURCE_VIDEO_FRAME_DIR)
    if os.path.splitext(p)[-1] in [".jpg", ".jpeg", ".JPG", ".JPEG"]
]
frame_names.sort(key=lambda p: int(os.path.splitext(p)[0]))

# init video predictor state
inference_state = video_predictor.init_state(video_path=SOURCE_VIDEO_FRAME_DIR)

ann_frame_idx = 0  # the frame index we interact with
"""
Step 2: Prompt DINO-X with Cloud API for box coordinates
"""

# prompt grounding dino to get the box coordinates on specific frame
img_path = os.path.join(SOURCE_VIDEO_FRAME_DIR, frame_names[ann_frame_idx])
image = Image.open(img_path)

# Step 1: initialize the config
config = Config(API_TOKEN_FOR_DINOX)

# Step 2: initialize the client
client = Client(config)

# Step 3: run the task using V2Task class
# if you are processing local image file, upload them to DDS server to get the image url
image_url = client.upload_file(img_path)

task = V2Task(
    api_path="/v2/task/dinox/detection",
    api_body={
        "model": "DINO-X-1.0",
        "image": image_url,
        "prompt": {
            "type": "text",
            "text": TEXT_PROMPT
        },
        "targets": ["bbox"],
        "bbox_threshold": BOX_THRESHOLD,
        "iou_threshold": IOU_THRESHOLD,
    }
)

client.run_task(task)
result = task.result

objects = result["objects"]  # the list of detected objects


input_boxes = []
confidences = []
class_names = []

for idx, obj in enumerate(objects):
    input_boxes.append(obj["bbox"])
    confidences.append(obj["score"])
    class_names.append(obj["category"])

input_boxes = np.array(input_boxes)

print(input_boxes)

# prompt SAM image predictor to get the mask for the object
image_predictor.set_image(np.array(image.convert("RGB")))

# process the detection results
OBJECTS = class_names

print(OBJECTS)

# prompt SAM 2 image predictor to get the mask for the object
masks, scores, logits = image_predictor.predict(
    point_coords=None,
    point_labels=None,
    box=input_boxes,
    multimask_output=False,
)
# convert the mask shape to (n, H, W)
if masks.ndim == 4:
    masks = masks.squeeze(1)

"""
Step 3: Register each object's positive points to video predictor with seperate add_new_points call
"""

assert PROMPT_TYPE_FOR_VIDEO in ["point", "box", "mask"], "SAM 2 video predictor only support point/box/mask prompt"

# If you are using point prompts, we uniformly sample positive points based on the mask
if PROMPT_TYPE_FOR_VIDEO == "point":
    # sample the positive points from mask for each objects
    all_sample_points = sample_points_from_masks(masks=masks, num_points=10)

    for object_id, (label, points) in enumerate(zip(OBJECTS, all_sample_points), start=1):
        labels = np.ones((points.shape[0]), dtype=np.int32)
        _, out_obj_ids, out_mask_logits = video_predictor.add_new_points_or_box(
            inference_state=inference_state,
            frame_idx=ann_frame_idx,
            obj_id=object_id,
            points=points,
            labels=labels,
        )
# Using box prompt
elif PROMPT_TYPE_FOR_VIDEO == "box":
    for object_id, (label, box) in enumerate(zip(OBJECTS, input_boxes), start=1):
        _, out_obj_ids, out_mask_logits = video_predictor.add_new_points_or_box(
            inference_state=inference_state,
            frame_idx=ann_frame_idx,
            obj_id=object_id,
            box=box,
        )
# Using mask prompt is a more straightforward way
elif PROMPT_TYPE_FOR_VIDEO == "mask":
    for object_id, (label, mask) in enumerate(zip(OBJECTS, masks), start=1):
        labels = np.ones((1), dtype=np.int32)
        _, out_obj_ids, out_mask_logits = video_predictor.add_new_mask(
            inference_state=inference_state,
            frame_idx=ann_frame_idx,
            obj_id=object_id,
            mask=mask
        )
else:
    raise NotImplementedError("SAM 2 video predictor only support point/box/mask prompts")

"""
Step 4: Propagate the video predictor to get the segmentation results for each frame
"""
video_segments = {}  # video_segments contains the per-frame segmentation results
for out_frame_idx, out_obj_ids, out_mask_logits in video_predictor.propagate_in_video(inference_state):
    video_segments[out_frame_idx] = {
        out_obj_id: (out_mask_logits[i] > 0.0).cpu().numpy()
        for i, out_obj_id in enumerate(out_obj_ids)
    }

"""
Step 5: Visualize the segment results across the video and save them
"""

if not os.path.exists(SAVE_TRACKING_RESULTS_DIR):
    os.makedirs(SAVE_TRACKING_RESULTS_DIR)

ID_TO_OBJECTS = {i: obj for i, obj in enumerate(OBJECTS, start=1)}

for frame_idx, segments in video_segments.items():
    img = cv2.imread(os.path.join(SOURCE_VIDEO_FRAME_DIR, frame_names[frame_idx]))
    
    object_ids = list(segments.keys())
    masks = list(segments.values())
    masks = np.concatenate(masks, axis=0)
    
    detections = sv.Detections(
        xyxy=sv.mask_to_xyxy(masks),  # (n, 4)
        mask=masks, # (n, h, w)
        class_id=np.array(object_ids, dtype=np.int32),
    )
    box_annotator = sv.BoxAnnotator()
    annotated_frame = box_annotator.annotate(scene=img.copy(), detections=detections)
    label_annotator = sv.LabelAnnotator()
    annotated_frame = label_annotator.annotate(annotated_frame, detections=detections, labels=[ID_TO_OBJECTS[i] for i in object_ids])
    mask_annotator = sv.MaskAnnotator()
    annotated_frame = mask_annotator.annotate(scene=annotated_frame, detections=detections)
    cv2.imwrite(os.path.join(SAVE_TRACKING_RESULTS_DIR, f"annotated_frame_{frame_idx:05d}.jpg"), annotated_frame)


"""
Step 6: Convert the annotated frames to video
"""

create_video_from_images(SAVE_TRACKING_RESULTS_DIR, OUTPUT_VIDEO_PATH)
'''

import os
from pathlib import Path

import cv2
import numpy as np
import supervision as sv
import torch
from PIL import Image
from tqdm import tqdm

from sam2.build_sam import build_sam2, build_sam2_video_predictor
from sam2.sam2_image_predictor import SAM2ImagePredictor
from tools.openclip_reranker import (
    DEFAULT_OPENCLIP_MODEL,
    DEFAULT_OPENCLIP_LABEL_MARGIN,
    DEFAULT_OPENCLIP_LABEL_MIN_SIMILARITY,
    DEFAULT_OPENCLIP_PRETRAINED,
    DEFAULT_OPENCLIP_SCORE_WEIGHT,
    DEFAULT_OPENCLIP_UNKNOWN_LABEL,
    rerank_detections_with_openclip,
)
from utils.track_utils import sample_points_from_masks
from utils.video_utils import create_video_from_images

"""
Hyperparameters for ground-and-track.

This file used to require a DINO-X cloud API token. It now supports four
grounding backends:
- "auto": prefer local Grounding DINO, then Hugging Face, then DINO-X
- "local": use the local Grounding DINO checkpoint
- "hf": use the Hugging Face Grounding DINO model
- "dinox": use the DINO-X cloud API
"""
VIDEO_PATH = r"D:\TorWIC-SLAM\TorWIC SLAM Dataset\Jun. 15, 2022\Aisle_CW_Run_1\image_left_first80.mp4"
TEXT_PROMPT = "wooden crate. mobile robot. warehouse rack. work table. yellow barrier."
GROUNDING_BACKEND = "hf"
PROMPT_TYPE_FOR_VIDEO = "box"  # choose from ["point", "box", "mask"]

GROUNDING_DINO_CONFIG = "grounding_dino/groundingdino/config/GroundingDINO_SwinT_OGC.py"
GROUNDING_DINO_CHECKPOINT = "gdino_checkpoints/groundingdino_swint_ogc.pth"
GROUNDING_DINO_HF_MODEL_ID = "IDEA-Research/grounding-dino-tiny"
GROUNDING_DINO_CHECKPOINT_MIN_BYTES = 100 * 1024 * 1024
GROUNDING_DINO_HF_ALLOW_DOWNLOAD = os.environ.get("GROUNDING_DINO_HF_ALLOW_DOWNLOAD", "0") == "1"

API_TOKEN_FOR_DINOX = os.environ.get("DINOX_API_TOKEN", "").strip()
DINOX_MODEL = "DINO-X-1.0"


def resolve_runtime_device(device: str) -> str:
    if device == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        return "cpu"
    return device

BOX_THRESHOLD = 0.25
TEXT_THRESHOLD = 0.25
IOU_THRESHOLD = 0.5
OPENCLIP_RERANK_ENABLED = os.environ.get("OPENCLIP_RERANK", "1") == "1"
OPENCLIP_MODEL_NAME = os.environ.get("OPENCLIP_MODEL_NAME", DEFAULT_OPENCLIP_MODEL)
OPENCLIP_PRETRAINED = os.environ.get("OPENCLIP_PRETRAINED", DEFAULT_OPENCLIP_PRETRAINED)
OPENCLIP_SCORE_WEIGHT = float(os.environ.get("OPENCLIP_SCORE_WEIGHT", str(DEFAULT_OPENCLIP_SCORE_WEIGHT)))
OPENCLIP_DEVICE = os.environ.get("OPENCLIP_DEVICE", "auto")
OPENCLIP_TEXT_PROMPT = os.environ.get("OPENCLIP_TEXT_PROMPT", TEXT_PROMPT)
OPENCLIP_RESOLVE_LABELS = os.environ.get("OPENCLIP_RESOLVE_LABELS", "1") == "1"
OPENCLIP_SOFT_GATE_ENABLED = os.environ.get("OPENCLIP_SOFT_GATE", "1") == "1"
OPENCLIP_UNKNOWN_LABEL = os.environ.get("OPENCLIP_UNKNOWN_LABEL", DEFAULT_OPENCLIP_UNKNOWN_LABEL)
OPENCLIP_LABEL_MARGIN = float(os.environ.get("OPENCLIP_LABEL_MARGIN", str(DEFAULT_OPENCLIP_LABEL_MARGIN)))
OPENCLIP_LABEL_MIN_SIMILARITY = float(
    os.environ.get("OPENCLIP_LABEL_MIN_SIMILARITY", str(DEFAULT_OPENCLIP_LABEL_MIN_SIMILARITY))
)

SAM2_CHECKPOINT = "./checkpoints/sam2.1_hiera_large.pt"
SAM2_MODEL_CFG = "configs/sam2.1/sam2.1_hiera_l.yaml"

SAM2_DEVICE = resolve_runtime_device(os.environ.get("SAM2_DEVICE", "auto"))
GROUNDING_DEVICE = resolve_runtime_device(os.environ.get("GROUNDING_DEVICE", "auto"))


def enable_torch_optimizations(device: str) -> None:
    if device != "cuda":
        return

    torch.autocast(device_type="cuda", dtype=torch.bfloat16).__enter__()

    if torch.cuda.get_device_properties(0).major >= 8:
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True


def has_local_grounding_checkpoint() -> bool:
    checkpoint_path = Path(GROUNDING_DINO_CHECKPOINT)
    return checkpoint_path.is_file() and checkpoint_path.stat().st_size >= GROUNDING_DINO_CHECKPOINT_MIN_BYTES


def has_cached_hf_grounding_model(model_id: str) -> bool:
    if "/" not in model_id:
        return False

    owner, name = model_id.split("/", 1)
    model_cache_dir = Path.home() / ".cache" / "huggingface" / "hub" / f"models--{owner}--{name}"
    snapshot_root = model_cache_dir / "snapshots"
    if not snapshot_root.is_dir():
        return False

    for snapshot_dir in snapshot_root.iterdir():
        if not snapshot_dir.is_dir():
            continue

        has_config = (snapshot_dir / "config.json").is_file()
        has_weights = any(snapshot_dir.glob("model*.safetensors")) or any(snapshot_dir.glob("pytorch_model*.bin"))
        if has_config and has_weights:
            return True

    return False


def get_cached_hf_snapshot_path(model_id: str) -> Path | None:
    if "/" not in model_id:
        return None

    owner, name = model_id.split("/", 1)
    snapshot_root = Path.home() / ".cache" / "huggingface" / "hub" / f"models--{owner}--{name}" / "snapshots"
    if not snapshot_root.is_dir():
        return None

    for snapshot_dir in sorted(snapshot_root.iterdir(), reverse=True):
        if not snapshot_dir.is_dir():
            continue

        has_config = (snapshot_dir / "config.json").is_file()
        has_weights = any(snapshot_dir.glob("model*.safetensors")) or any(snapshot_dir.glob("pytorch_model*.bin"))
        if has_config and has_weights:
            return snapshot_dir

    return None


def resolve_grounding_backend() -> str:
    allowed_backends = {"auto", "local", "hf", "dinox"}
    if GROUNDING_BACKEND not in allowed_backends:
        raise ValueError(f"GROUNDING_BACKEND must be one of {sorted(allowed_backends)}, got {GROUNDING_BACKEND!r}")

    if GROUNDING_BACKEND == "local":
        if not has_local_grounding_checkpoint():
            raise FileNotFoundError(
                f"Local Grounding DINO checkpoint is missing or incomplete: {GROUNDING_DINO_CHECKPOINT}"
            )
        return "local"

    if GROUNDING_BACKEND == "hf":
        if not GROUNDING_DINO_HF_ALLOW_DOWNLOAD and not has_cached_hf_grounding_model(GROUNDING_DINO_HF_MODEL_ID):
            raise FileNotFoundError(
                "GROUNDING_BACKEND='hf' needs cached HF model weights or GROUNDING_DINO_HF_ALLOW_DOWNLOAD=1."
            )
        try:
            from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor  # noqa: F401
        except ImportError as exc:
            raise ImportError("GROUNDING_BACKEND='hf' requires transformers to be installed.") from exc
        return "hf"

    if GROUNDING_BACKEND == "dinox":
        if not API_TOKEN_FOR_DINOX:
            raise ValueError("GROUNDING_BACKEND='dinox' requires DINOX_API_TOKEN in the environment.")
        try:
            from dds_cloudapi_sdk import Client, Config  # noqa: F401
            from dds_cloudapi_sdk.tasks.v2_task import V2Task  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "GROUNDING_BACKEND='dinox' requires dds-cloudapi-sdk. Install it with `pip install -U dds-cloudapi-sdk`."
            ) from exc
        return "dinox"

    if has_local_grounding_checkpoint():
        return "local"

    if has_cached_hf_grounding_model(GROUNDING_DINO_HF_MODEL_ID) or GROUNDING_DINO_HF_ALLOW_DOWNLOAD:
        try:
            from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor  # noqa: F401
            return "hf"
        except ImportError:
            pass

    if API_TOKEN_FOR_DINOX:
        try:
            from dds_cloudapi_sdk import Client, Config  # noqa: F401
            from dds_cloudapi_sdk.tasks.v2_task import V2Task  # noqa: F401
            return "dinox"
        except ImportError:
            pass

    raise RuntimeError(
        "No available grounding backend. Download the local Grounding DINO checkpoint, "
        "or use transformers for Hugging Face, or configure DINOX_API_TOKEN plus dds-cloudapi-sdk."
    )


def load_grounding_model(backend: str, device: str):
    if backend == "local":
        from grounding_dino.groundingdino.util.inference import load_model

        return load_model(
            model_config_path=GROUNDING_DINO_CONFIG,
            model_checkpoint_path=GROUNDING_DINO_CHECKPOINT,
            device=device,
        )

    if backend == "hf":
        from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

        hf_source = get_cached_hf_snapshot_path(GROUNDING_DINO_HF_MODEL_ID) or GROUNDING_DINO_HF_MODEL_ID
        local_files_only = not GROUNDING_DINO_HF_ALLOW_DOWNLOAD or isinstance(hf_source, Path)

        processor = AutoProcessor.from_pretrained(
            str(hf_source),
            local_files_only=local_files_only,
            use_fast=False,
        )
        model = AutoModelForZeroShotObjectDetection.from_pretrained(
            str(hf_source),
            local_files_only=local_files_only,
        ).to(device)
        return {"processor": processor, "model": model}

    if backend == "dinox":
        from dds_cloudapi_sdk import Client, Config

        config = Config(API_TOKEN_FOR_DINOX)
        return Client(config)

    raise NotImplementedError(f"Unsupported backend: {backend}")


def detect_objects(img_path: str, text_prompt: str, backend: str, grounding_model, device: str):
    if backend == "local":
        from grounding_dino.groundingdino.util.inference import load_image, predict
        from torchvision.ops import box_convert

        image_source, image = load_image(img_path)
        boxes, confidences, labels = predict(
            model=grounding_model,
            image=image,
            caption=text_prompt,
            box_threshold=BOX_THRESHOLD,
            text_threshold=TEXT_THRESHOLD,
        )

        h, w, _ = image_source.shape
        boxes = boxes * torch.tensor([w, h, w, h])
        input_boxes = box_convert(boxes=boxes, in_fmt="cxcywh", out_fmt="xyxy").cpu().numpy()
        class_names = [str(label) for label in labels]
        grounding_scores = confidences.cpu().numpy().tolist()
        image_source_np = image_source
    elif backend == "hf":
        processor = grounding_model["processor"]
        model = grounding_model["model"]

        image = Image.open(img_path).convert("RGB")
        inputs = processor(images=image, text=text_prompt, return_tensors="pt").to(device)

        with torch.no_grad():
            outputs = model(**inputs)

        results = processor.post_process_grounded_object_detection(
            outputs,
            inputs.input_ids,
            threshold=BOX_THRESHOLD,
            text_threshold=TEXT_THRESHOLD,
            target_sizes=[image.size[::-1]],
        )

        input_boxes = results[0]["boxes"].cpu().numpy()
        class_names = [str(label) for label in results[0]["labels"]]
        grounding_scores = results[0]["scores"].cpu().numpy().tolist()
        image_source_np = np.array(image)
    elif backend == "dinox":
        from dds_cloudapi_sdk.tasks.v2_task import V2Task

        image = Image.open(img_path).convert("RGB")
        image_url = grounding_model.upload_file(img_path)
        task = V2Task(
            api_path="/v2/task/dinox/detection",
            api_body={
                "model": DINOX_MODEL,
                "image": image_url,
                "prompt": {"type": "text", "text": text_prompt},
                "targets": ["bbox"],
                "bbox_threshold": BOX_THRESHOLD,
                "iou_threshold": IOU_THRESHOLD,
            },
        )
        grounding_model.run_task(task)
        result = task.result or {}
        objects = result.get("objects", [])

        input_boxes = np.array([obj["bbox"] for obj in objects], dtype=np.float32) if objects else np.empty((0, 4), dtype=np.float32)
        grounding_scores = [obj["score"] for obj in objects]
        class_names = [obj["category"] for obj in objects]
        image_source_np = np.array(image)
    else:
        raise NotImplementedError(f"Unsupported backend: {backend}")

    if not OPENCLIP_RERANK_ENABLED or input_boxes.size == 0:
        score_details = [
            {
                "grounding_label": label,
                "clip_proposed_label": label,
                "resolved_label": label,
                "semantic_gate_label": label,
                "semantic_gate_score": 1.0,
                "semantic_gate_passed": True,
                "semantic_gate_reason": "openclip_disabled",
                "is_semantically_uncertain": False,
                "grounding_score": float(score),
                "clip_similarity": 0.0,
                "clip_best_prompt": label,
                "clip_best_similarity": 0.0,
                "clip_second_similarity": 0.0,
                "clip_margin": 0.0,
                "clip_entropy": 0.0,
                "resolved_label_confidence": 1.0,
                "is_semantically_ambiguous": False,
                "ranking_score": float(score),
                "final_score": float(score),
            }
            for label, score in zip(class_names, grounding_scores)
        ]
        return image_source_np, input_boxes, class_names, [item["final_score"] for item in score_details], score_details

    original_class_names = list(class_names)
    score_details = rerank_detections_with_openclip(
        image=image_source_np,
        boxes=input_boxes,
        labels=original_class_names,
        grounding_scores=grounding_scores,
        text_prompt=OPENCLIP_TEXT_PROMPT,
        score_weight=OPENCLIP_SCORE_WEIGHT,
        model_name=OPENCLIP_MODEL_NAME,
        pretrained=OPENCLIP_PRETRAINED,
        device=OPENCLIP_DEVICE,
        unknown_margin=OPENCLIP_LABEL_MARGIN,
        min_best_similarity=OPENCLIP_LABEL_MIN_SIMILARITY,
        unknown_label=OPENCLIP_UNKNOWN_LABEL,
    )
    reranked_indices = [item["original_index"] for item in score_details]
    input_boxes = input_boxes[reranked_indices]
    if OPENCLIP_RESOLVE_LABELS:
        downstream_labels: list[str] = []
        for item in score_details:
            original_label = str(original_class_names[item["original_index"]])
            if OPENCLIP_SOFT_GATE_ENABLED and not bool(item["semantic_gate_passed"]):
                downstream_label = original_label
            else:
                downstream_label = str(item["semantic_gate_label"])
            item["downstream_label"] = downstream_label
            downstream_labels.append(downstream_label)
        class_names = downstream_labels
    else:
        class_names = [original_class_names[idx] for idx in reranked_indices]
        for item, label in zip(score_details, class_names):
            item["downstream_label"] = label
    final_scores = [item["ranking_score"] for item in score_details]
    return image_source_np, input_boxes, class_names, final_scores, score_details


def register_prompts_to_video(video_predictor, inference_state, ann_frame_idx: int, prompt_type: str, input_boxes: np.ndarray, masks: np.ndarray) -> None:
    assert prompt_type in ["point", "box", "mask"], "SAM 2 video predictor only supports point/box/mask prompts"

    if prompt_type == "point":
        all_sample_points = sample_points_from_masks(masks=masks, num_points=10)
        for object_id, points in enumerate(all_sample_points, start=1):
            labels = np.ones((points.shape[0]), dtype=np.int32)
            video_predictor.add_new_points_or_box(
                inference_state=inference_state,
                frame_idx=ann_frame_idx,
                obj_id=object_id,
                points=points,
                labels=labels,
            )
        return

    if prompt_type == "box":
        for object_id, box in enumerate(input_boxes, start=1):
            video_predictor.add_new_points_or_box(
                inference_state=inference_state,
                frame_idx=ann_frame_idx,
                obj_id=object_id,
                box=box,
            )
        return

    for object_id, mask in enumerate(masks, start=1):
        video_predictor.add_new_mask(
            inference_state=inference_state,
            frame_idx=ann_frame_idx,
            obj_id=object_id,
            mask=mask,
        )


def main() -> None:
    video_path = Path(VIDEO_PATH)
    if not video_path.is_file():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    enable_torch_optimizations(SAM2_DEVICE)
    enable_torch_optimizations(GROUNDING_DEVICE)

    resolved_backend = resolve_grounding_backend()
    print(f"Using grounding backend: {resolved_backend}")
    print(f"Runtime devices: grounding={GROUNDING_DEVICE}, sam2={SAM2_DEVICE}, openclip={OPENCLIP_DEVICE}")

    video_stem = video_path.stem
    video_parent_dir = video_path.parent
    run_id = os.getpid()
    output_video_path = str(video_parent_dir / f"{video_stem}_{resolved_backend}_tracking_demo.mp4")
    source_video_frame_dir = str(video_parent_dir / f"{video_stem}_{resolved_backend}_frames_{run_id}")
    save_tracking_results_dir = str(video_parent_dir / f"{video_stem}_{resolved_backend}_tracking_results")

    grounding_model = load_grounding_model(resolved_backend, GROUNDING_DEVICE)

    video_predictor = build_sam2_video_predictor(SAM2_MODEL_CFG, SAM2_CHECKPOINT)
    sam2_image_model = build_sam2(SAM2_MODEL_CFG, SAM2_CHECKPOINT)
    image_predictor = SAM2ImagePredictor(sam2_image_model)

    video_info = sv.VideoInfo.from_video_path(str(video_path))
    print(video_info)
    frame_generator = sv.get_video_frames_generator(str(video_path), stride=1, start=0, end=None)

    source_frames = Path(source_video_frame_dir)

    with sv.ImageSink(
        target_dir_path=source_frames,
        overwrite=True,
        image_name_pattern="{:05d}.jpg",
    ) as sink:
        for frame in tqdm(frame_generator, desc="Saving Video Frames"):
            sink.save_image(frame)

    frame_names = [
        p
        for p in os.listdir(source_video_frame_dir)
        if os.path.splitext(p)[-1] in [".jpg", ".jpeg", ".JPG", ".JPEG"]
    ]
    frame_names.sort(key=lambda p: int(os.path.splitext(p)[0]))

    if not frame_names:
        raise RuntimeError(f"No frames were extracted from video: {video_path}")

    inference_state = video_predictor.init_state(video_path=source_video_frame_dir)
    ann_frame_idx = 0

    img_path = os.path.join(source_video_frame_dir, frame_names[ann_frame_idx])
    image_source, input_boxes, class_names, confidences, score_details = detect_objects(
        img_path=img_path,
        text_prompt=TEXT_PROMPT,
        backend=resolved_backend,
        grounding_model=grounding_model,
        device=GROUNDING_DEVICE,
    )

    if input_boxes.size == 0 or len(class_names) == 0:
        raise RuntimeError(
            f"No objects detected on the first frame using backend '{resolved_backend}'. "
            "Adjust TEXT_PROMPT / BOX_THRESHOLD / TEXT_THRESHOLD and retry."
        )

    print(input_boxes)
    print(class_names)
    print(confidences)
    for idx, detail in enumerate(score_details):
        print(
            f"candidate[{idx}] grounding_label={detail['grounding_label']} downstream_label={detail['downstream_label']} "
            f"clip_label={detail['clip_proposed_label']} gate_passed={detail['semantic_gate_passed']} "
            f"gate_reason={detail['semantic_gate_reason']} gate_score={detail['semantic_gate_score']:.6f} "
            f"grounding_score={detail['grounding_score']:.6f} clip_similarity={detail['clip_similarity']:.6f} "
            f"clip_best_prompt={detail['clip_best_prompt']} clip_margin={detail['clip_margin']:.6f} "
            f"ranking_score={detail['ranking_score']:.6f}"
        )

    image_predictor.set_image(image_source)
    masks, scores, logits = image_predictor.predict(
        point_coords=None,
        point_labels=None,
        box=input_boxes,
        multimask_output=False,
    )
    if masks.ndim == 4:
        masks = masks.squeeze(1)

    register_prompts_to_video(
        video_predictor=video_predictor,
        inference_state=inference_state,
        ann_frame_idx=ann_frame_idx,
        prompt_type=PROMPT_TYPE_FOR_VIDEO,
        input_boxes=input_boxes,
        masks=masks,
    )

    video_segments = {}
    for out_frame_idx, out_obj_ids, out_mask_logits in video_predictor.propagate_in_video(inference_state):
        video_segments[out_frame_idx] = {
            out_obj_id: (out_mask_logits[i] > 0.0).cpu().numpy()
            for i, out_obj_id in enumerate(out_obj_ids)
        }

    os.makedirs(save_tracking_results_dir, exist_ok=True)
    id_to_objects = {i: obj for i, obj in enumerate(class_names, start=1)}

    for frame_idx, segments in video_segments.items():
        img = cv2.imread(os.path.join(source_video_frame_dir, frame_names[frame_idx]))

        object_ids = list(segments.keys())
        frame_masks = np.concatenate(list(segments.values()), axis=0)
        detections = sv.Detections(
            xyxy=sv.mask_to_xyxy(frame_masks),
            mask=frame_masks,
            class_id=np.array(object_ids, dtype=np.int32),
        )

        annotated_frame = sv.BoxAnnotator().annotate(scene=img.copy(), detections=detections)
        annotated_frame = sv.LabelAnnotator().annotate(
            annotated_frame,
            detections=detections,
            labels=[id_to_objects[i] for i in object_ids],
        )
        annotated_frame = sv.MaskAnnotator().annotate(scene=annotated_frame, detections=detections)
        cv2.imwrite(os.path.join(save_tracking_results_dir, f"annotated_frame_{frame_idx:05d}.jpg"), annotated_frame)

    create_video_from_images(save_tracking_results_dir, output_video_path)
    print(f"Tracking video saved to: {output_video_path}")
    print(f"Annotated frames saved to: {save_tracking_results_dir}")


if __name__ == "__main__":
    main()
