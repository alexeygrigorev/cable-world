import argparse
import os
import sys

from PIL import Image

from map_pipeline.sheet_slice_audit import audit_grid_cut_components, cell_bounds, format_cut_issues

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
    parser.add_argument("--edge-audit", choices=["off", "warn", "error"], default="warn")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    sheet_path = os.path.abspath(args.sheet)
    out_dir = os.path.abspath(args.out_dir)

    if not os.path.exists(sheet_path):
        print(f"Missing sprite sheet: {sheet_path}", file=sys.stderr)
        return 1

    sheet = Image.open(sheet_path).convert("RGBA")
    names = [filename.removesuffix(".png") for filename in ICON_NAMES]
    if args.edge_audit != "off":
        issues = audit_grid_cut_components(sheet, names, 4, 2)
        if issues:
            message = format_cut_issues(issues)
            if args.edge_audit == "error":
                print(f"Grid-cut alpha components detected in {sheet_path}:\n{message}", file=sys.stderr)
                return 1
            print(f"Grid-cut alpha components detected in {sheet_path}:\n{message}", file=sys.stderr)

    os.makedirs(out_dir, exist_ok=True)
    for index, filename in enumerate(ICON_NAMES):
        cell = sheet.crop(cell_bounds(sheet.width, sheet.height, index, 4, 2))
        icon = _fit_icon(_trim_alpha(cell))
        out_path = os.path.join(out_dir, filename)
        icon.save(out_path, "PNG", optimize=True)
        print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
