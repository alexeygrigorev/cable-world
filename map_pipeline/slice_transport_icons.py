import argparse
import os
import sys

from PIL import Image

SPRITES_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "sprites")
ICON_SIZE = 256
PADDING = 18

ICON_NAMES = [
    "icon_cable_gondola.png",
    "icon_funicular.png",
    "icon_cog_railway.png",
    "icon_suspended_monorail.png",
    "icon_chairlift.png",
    "icon_elevator.png",
    "icon_aerial_tram.png",
    "icon_station.png",
]


def _cell_bounds(width: int, height: int, index: int) -> tuple[int, int, int, int]:
    col = index % 4
    row = index // 4
    left = round(width * col / 4)
    right = round(width * (col + 1) / 4)
    top = round(height * row / 2)
    bottom = round(height * (row + 1) / 2)
    return left, top, right, bottom


def _trim_alpha(image: Image.Image) -> Image.Image:
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        return image
    return image.crop(bbox)


def _fit_icon(image: Image.Image) -> Image.Image:
    icon = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    max_side = ICON_SIZE - PADDING * 2
    scale = min(max_side / image.width, max_side / image.height)
    target_size = (
        max(1, round(image.width * scale)),
        max(1, round(image.height * scale)),
    )
    resized = image.resize(target_size, Image.Resampling.LANCZOS)
    x = (ICON_SIZE - resized.width) // 2
    y = (ICON_SIZE - resized.height) // 2
    icon.alpha_composite(resized, (x, y))
    return icon


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Slice the generated 4x2 transport icon sheet into runtime PNG icons."
    )
    parser.add_argument(
        "--sheet",
        required=True,
        help="Path to the transparent 4x2 sheet. Keep this source sheet outside runtime assets.",
    )
    parser.add_argument(
        "--out-dir",
        default=SPRITES_DIR,
        help="Directory for sliced runtime icons. Defaults to assets/sprites.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    sheet_path = os.path.abspath(args.sheet)
    out_dir = os.path.abspath(args.out_dir)

    if not os.path.exists(sheet_path):
        print(f"Missing sprite sheet: {sheet_path}", file=sys.stderr)
        return 1

    sheet = Image.open(sheet_path).convert("RGBA")
    os.makedirs(out_dir, exist_ok=True)
    for index, filename in enumerate(ICON_NAMES):
        cell = sheet.crop(_cell_bounds(sheet.width, sheet.height, index))
        icon = _fit_icon(_trim_alpha(cell))
        out_path = os.path.join(out_dir, filename)
        icon.save(out_path, "PNG", optimize=True)
        print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
