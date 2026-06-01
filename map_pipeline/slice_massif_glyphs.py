import argparse
from pathlib import Path

from PIL import Image, ImageFilter


MAP_DIR = Path(__file__).resolve().parent.parent / "assets" / "map"
GLYPH_DIR = MAP_DIR / "glyphs"
DEFAULT_SHEET = GLYPH_DIR / "massif_glyph_sheet.png"
PADDING = 12

GLYPH_NAMES = [
    "massif_alps_wall_1",
    "massif_alps_wall_2",
    "massif_harz_brocken",
    "massif_black_forest_spine",
    "massif_bavarian_forest",
    "massif_erzgebirge_ridge",
    "massif_saxon_switzerland_sandstone",
    "massif_eifel_hunsrueck_low",
]


def _cell_bounds(width: int, height: int, index: int) -> tuple[int, int, int, int]:
    col = index % 4
    row = index // 4
    return (
        round(width * col / 4),
        round(height * row / 2),
        round(width * (col + 1) / 4),
        round(height * (row + 1) / 2),
    )


def _remove_chroma_key(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    pixels = image.load()
    alpha = Image.new("L", image.size, 255)
    alpha_pixels = alpha.load()
    for y in range(image.height):
        for x in range(image.width):
            red, green, blue, _ = pixels[x, y]
            magenta_distance = abs(red - 255) + abs(green) + abs(blue - 255)
            if magenta_distance <= 60 or (red > 222 and blue > 222 and green < 95):
                alpha_pixels[x, y] = 0
    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.25))
    image.putalpha(alpha)
    return image


def _trim_with_padding(image: Image.Image) -> Image.Image:
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    left = max(0, bbox[0] - PADDING)
    top = max(0, bbox[1] - PADDING)
    right = min(image.width, bbox[2] + PADDING)
    bottom = min(image.height, bbox[3] + PADDING)
    return image.crop((left, top, right, bottom))


def slice_sheet(sheet_path: Path, out_dir: Path) -> None:
    sheet = Image.open(sheet_path).convert("RGBA")
    keyed = _remove_chroma_key(sheet)
    out_dir.mkdir(parents=True, exist_ok=True)
    for index, name in enumerate(GLYPH_NAMES):
        cell = keyed.crop(_cell_bounds(sheet.width, sheet.height, index))
        glyph = _trim_with_padding(cell)
        output = out_dir / f"{name}.png"
        glyph.save(output, "PNG", optimize=True)
        print(f"Wrote {output} {glyph.width}x{glyph.height}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Slice generated massif map glyph sheet into large source glyphs.")
    parser.add_argument("--sheet", type=Path, default=DEFAULT_SHEET)
    parser.add_argument("--out-dir", type=Path, default=GLYPH_DIR)
    args = parser.parse_args()
    if not args.sheet.exists():
        raise FileNotFoundError(args.sheet)
    slice_sheet(args.sheet, args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
