#!/usr/bin/env python3
"""Build a minimal dynamic-mask-to-SLAM-frontend demo artifact.

The script deliberately stops before claiming full SLAM evaluation. It prepares
the exact kind of masked RGB input and manifest that a downstream visual SLAM
backend can consume, using the repository-tracked semantic segmentation example.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SEGMENTATION_DIR = ROOT / "examples" / "semantic_segmentation_example"
OUTPUT_DIR = ROOT / "examples" / "dynamic_slam_frontend_example"
FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size=size)


def load_summary(stem: str) -> dict:
    with (SEGMENTATION_DIR / f"{stem}-summary.json").open("r", encoding="utf-8") as f:
        return json.load(f)


def resolve_source_rgb(stem: str) -> tuple[Image.Image, str]:
    summary = load_summary(stem)
    rgb_path = Path(summary.get("rgb_path", ""))
    if rgb_path.exists():
        return Image.open(rgb_path).convert("RGB"), str(rgb_path)
    fallback = SEGMENTATION_DIR / f"{stem}-overlay.png"
    return Image.open(fallback).convert("RGB"), str(fallback)


def mask_dynamic_pixels(rgb: Image.Image, mask: Image.Image) -> Image.Image:
    masked = rgb.copy()
    draw = ImageDraw.Draw(masked)
    mask_l = mask.convert("L")
    # Fill dynamic pixels with neutral gray. This mirrors a common SLAM frontend
    # strategy: remove dynamic regions from feature extraction instead of
    # admitting them into the static map.
    gray = Image.new("RGB", rgb.size, (118, 118, 118))
    masked.paste(gray, mask=mask_l)
    bbox = mask_l.getbbox()
    if bbox:
        draw.rectangle(bbox, outline=(220, 38, 38), width=5)
        draw.text((bbox[0], max(8, bbox[1] - 34)), "dynamic masked: forklift", font=font(24), fill=(220, 38, 38))
    return masked


def build_panel(original: Image.Image, mask: Image.Image, masked: Image.Image, coverage: float) -> Image.Image:
    width, height = 1760, 690
    panel = Image.new("RGB", (width, height), "#f4f6f8")
    draw = ImageDraw.Draw(panel)
    draw.text((40, 34), "动态语义 mask -> SLAM 前端输入示例", font=font(42), fill="#111827")
    draw.text(
        (40, 92),
        "当前推进目标：先把动态物体区域从 RGB 输入中屏蔽，并生成给后端可消费的 manifest；尚不声称 ATE/RPE 提升。",
        font=font(24),
        fill="#4b5563",
    )

    slots = [
        ("原始/语义输出帧", original),
        ("动态 mask：forklift", mask.convert("RGB")),
        ("SLAM 输入：动态区域屏蔽", masked),
    ]
    x = 40
    for title, image in slots:
        draw.rounded_rectangle((x, 150, x + 530, 610), radius=14, fill="#ffffff", outline="#c7cdd5", width=2)
        draw.text((x + 22, 170), title, font=font(24), fill="#1f2937")
        image_copy = image.copy()
        image_copy.thumbnail((486, 360), Image.Resampling.LANCZOS)
        panel.paste(image_copy, (x + 22, 220))
        x += 570

    draw.rounded_rectangle((40, 630, 1720, 672), radius=12, fill="#e9f2ff", outline="#60a5fa", width=2)
    draw.text(
        (62, 636),
        f"输出：dynamic_mask.png, slam_input_masked.png, slam_frontend_manifest.json | dynamic coverage={coverage:.3%}",
        font=font(22),
        fill="#1d4ed8",
    )
    return panel


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = "forklift"
    original, source_rgb = resolve_source_rgb(stem)
    mask = Image.open(SEGMENTATION_DIR / f"{stem}-mask.png").convert("L")
    if mask.size != original.size:
        mask = mask.resize(original.size, Image.Resampling.NEAREST)

    masked = mask_dynamic_pixels(original, mask)
    mask_pixels = sum(1 for value in mask.getdata() if value > 0)
    total_pixels = mask.width * mask.height
    coverage = mask_pixels / max(total_pixels, 1)

    dynamic_mask_path = OUTPUT_DIR / "dynamic_mask.png"
    masked_path = OUTPUT_DIR / "slam_input_masked.png"
    panel_path = OUTPUT_DIR / "dynamic_slam_frontend_result.png"
    manifest_path = OUTPUT_DIR / "slam_frontend_manifest.json"

    mask.save(dynamic_mask_path)
    masked.save(masked_path, quality=95)
    build_panel(original, mask, masked, coverage).save(panel_path, quality=95)

    manifest = {
        "status": "frontend_mask_bridge_ready",
        "claim_boundary": "Produces dynamic-masked RGB input for a SLAM backend; does not report ATE/RPE yet.",
        "source_rgb": source_rgb,
        "dynamic_instances": [
            {
                "label": "forklift",
                "role": "dynamic_agent",
                "mask": str(dynamic_mask_path.relative_to(ROOT)),
                "mask_pixels": mask_pixels,
                "coverage_ratio": coverage,
            }
        ],
        "slam_inputs": [
            {
                "rgb_masked": str(masked_path.relative_to(ROOT)),
                "dynamic_mask": str(dynamic_mask_path.relative_to(ROOT)),
                "intended_backend": "DROID-SLAM/ORB-SLAM style visual frontend",
            }
        ],
        "next_backend_step": "Feed rgb_masked frames to a SLAM backend and compare trajectory/map metrics against unmasked RGB.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
