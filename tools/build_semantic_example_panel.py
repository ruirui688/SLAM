#!/usr/bin/env python3
"""Build reader-facing annotated semantic segmentation example figures."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DIR = ROOT / "examples" / "semantic_segmentation_example"
FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    # The regular CJK font is available on the project host and renders Chinese
    # labels reliably in generated PNG assets.
    return ImageFont.truetype(FONT_PATH, size=size)


def load_summary(name: str) -> dict:
    with (EXAMPLE_DIR / f"{name}-summary.json").open("r", encoding="utf-8") as f:
        return json.load(f)


def draw_label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fill: str) -> None:
    x, y = xy
    label_font = font(28)
    box = draw.textbbox((x, y), text, font=label_font)
    pad_x, pad_y = 14, 8
    rect = (box[0] - pad_x, box[1] - pad_y, box[2] + pad_x, box[3] + pad_y)
    draw.rounded_rectangle(rect, radius=10, fill=fill, outline="white", width=2)
    draw.text((x, y), text, font=label_font, fill="white")


def annotate_overlay(stem: str, title: str, decision: str, color: str) -> Image.Image:
    overlay = Image.open(EXAMPLE_DIR / f"{stem}-overlay.png").convert("RGB")
    summary = load_summary(stem)
    stats = summary["stats"]
    x1, y1, _ = stats["bbox_min_xyz_m"]
    x2, y2, _ = stats["bbox_max_xyz_m"]
    cx, cy, _ = stats["centroid_xyz_m"]
    x1, y1, x2, y2, cx, cy = map(int, [x1, y1, x2, y2, cx, cy])

    canvas = overlay.copy()
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((x1, y1, x2, y2), outline=color, width=6)
    draw.ellipse((cx - 8, cy - 8, cx + 8, cy + 8), fill=color, outline="white", width=2)

    label_x = min(max(x1 - 20, 24), overlay.width - 420)
    label_y = max(24, y1 - 88)
    draw.line((label_x + 210, label_y + 48, cx, cy), fill=color, width=5)
    draw_label(draw, (label_x, label_y), title, color)
    draw.text((label_x, label_y + 58), decision, font=font(22), fill=color)

    return canvas


def fit(im: Image.Image, size: tuple[int, int]) -> Image.Image:
    out = Image.new("RGB", size, "#f7f8f5")
    im.thumbnail(size, Image.Resampling.LANCZOS)
    x = (size[0] - im.width) // 2
    y = (size[1] - im.height) // 2
    out.paste(im, (x, y))
    return out


def mask_to_rgb(stem: str, color: tuple[int, int, int]) -> Image.Image:
    mask = Image.open(EXAMPLE_DIR / f"{stem}-mask.png").convert("L")
    rgb = Image.new("RGB", mask.size, "black")
    color_layer = Image.new("RGB", mask.size, color)
    rgb.paste(color_layer, mask=mask)
    return rgb


def wrap_text(text: str, limit: int = 30) -> list[str]:
    lines: list[str] = []
    current = ""
    for token in text.replace(" -> ", " ->\n").split("\n"):
        if len(token) <= limit:
            lines.append(token)
            continue
        for char in token:
            if len(current) >= limit:
                lines.append(current)
                current = ""
            current += char
        if current:
            lines.append(current)
            current = ""
    return lines


def summary_card(stem: str, title: str, state: str, color: str) -> Image.Image:
    summary = load_summary(stem)
    stats = summary["stats"]
    card = Image.new("RGB", (520, 420), "#ffffff")
    draw = ImageDraw.Draw(card)
    draw.rounded_rectangle((0, 0, 519, 419), radius=16, fill="#ffffff", outline="#c7ced6", width=2)
    draw.text((28, 28), title, font=font(30), fill=color)
    lines = [
        f"object: {summary['object_name']}",
        f"mask_area_px: {stats['mask_area_px']}",
        f"bbox_px: {int(stats['bbox_size_xyz_m'][0])} x {int(stats['bbox_size_xyz_m'][1])}",
        f"centroid_px: {stats['centroid_xyz_m'][0]:.1f}, {stats['centroid_xyz_m'][1]:.1f}",
    ]
    y = 92
    for line in lines:
        draw.text((28, y), line, font=font(23), fill="#1f2937")
        y += 52
    draw.text((28, y), "map decision:", font=font(23), fill="#1f2937")
    y += 42
    for line in wrap_text(state, 24):
        draw.text((56, y), line, font=font(21), fill=color)
        y += 38
    return card


def row(stem: str, title: str, state: str, color: str, mask_color: tuple[int, int, int]) -> Image.Image:
    overlay = annotate_overlay(stem, title, state, color)
    mask = mask_to_rgb(stem, mask_color)
    card = summary_card(stem, title, state, color)

    row_im = Image.new("RGB", (1820, 560), "#f6f8fa")
    draw = ImageDraw.Draw(row_im)
    draw.rounded_rectangle((0, 0, 1819, 559), radius=18, fill="#f6f8fa", outline="#c5ccd4", width=2)
    row_im.paste(fit(overlay, (760, 430)), (36, 92))
    row_im.paste(fit(mask, (430, 430)), (830, 92))
    row_im.paste(card, (1290, 92))
    draw.text((36, 28), "实例 overlay：带 bbox、中心点和标签", font=font(24), fill="#374151")
    draw.text((830, 28), "二值 mask：白/彩色区域为分割结果", font=font(24), fill="#374151")
    draw.text((1290, 28), "结构化输出：summary JSON 关键字段", font=font(24), fill="#374151")
    return row_im


def main() -> None:
    barrier = row(
        "yellow-barrier",
        "稳定候选 yellow_barrier",
        "保留候选 -> 进入跨会话稳定性判断",
        "#0f766e",
        (20, 184, 166),
    )
    forklift = row(
        "forklift",
        "动态污染候选 forklift",
        "拒绝候选 -> 不写入长期静态地图",
        "#c2410c",
        (249, 115, 22),
    )

    panel = Image.new("RGB", (1920, 1420), "#f2f3ef")
    draw = ImageDraw.Draw(panel)
    draw.rounded_rectangle((34, 34, 1886, 1386), radius=24, fill="#ffffff", outline="#c9cfc8", width=2)
    draw.text((80, 76), "语义分割实际输出示例：TorWIC 工业场景", font=font(48), fill="#102027")
    draw.text(
        (80, 142),
        "一条样例帧同时输出实例 overlay、二值 mask、summary JSON，并进入对象地图准入逻辑。",
        font=font(26),
        fill="#4b5563",
    )
    panel.paste(barrier, (50, 205))
    panel.paste(forklift, (50, 795))
    draw.rounded_rectangle((80, 1300, 1840, 1350), radius=16, fill="#e8f1ff", outline="#6aa0ff", width=2)
    draw.text(
        (104, 1308),
        "运行链路：语义分割实例输出 -> ObjectObservation -> 跨会话聚类 -> 稳定对象保留 / 动态证据拒绝",
        font=font(28),
        fill="#1d4ed8",
    )

    panel.save(EXAMPLE_DIR / "semantic-segmentation-result.png", quality=95)
    annotate_overlay(
        "yellow-barrier",
        "稳定候选 yellow_barrier",
        "保留候选 -> 进入跨会话稳定性判断",
        "#0f766e",
    ).save(EXAMPLE_DIR / "yellow-barrier-annotated.png", quality=95)
    annotate_overlay(
        "forklift",
        "动态污染候选 forklift",
        "拒绝候选 -> 不写入长期静态地图",
        "#c2410c",
    ).save(EXAMPLE_DIR / "forklift-annotated.png", quality=95)


if __name__ == "__main__":
    main()
