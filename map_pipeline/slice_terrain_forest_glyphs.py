import argparse
import os
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter


MAP_DIR = Path(__file__).resolve().parent.parent / "assets" / "map"
GLYPH_DIR = MAP_DIR / "glyphs"
DEFAULT_SHEET = GLYPH_DIR / "terrain_forest_sheet.png"
ICON_SIZE = 192
PADDING = 10

GLYPH_NAMES = [
    "atlas_forest_pine_dense",
    "atlas_forest_mixed_large",
    "atlas_forest_deciduous_dense",
    "atlas_forest_pine_round",
    "atlas_forest_mixed_wide",
    "atlas_forest_pine_tall",
    "atlas_forest_broadleaf_round",
    "atlas_forest_mixed_tall",
    "atlas_forest_pine_small",
    "atlas_forest_mixed_small",
    "atlas_land_grass_patch",
    "atlas_land_tuft_patch",
    "atlas_land_flower_meadow",
    "atlas_land_rocky_meadow",
    "atlas_forest_rocky_pine",
    "atlas_forest_rocky_mixed",
]


def _cell_bounds(width: int, height: int, index: int) -> tuple[int, int, int, int]:
    col = index % 4
    row = index // 4
    return (
        round(width * col / 4),
        round(height * row / 4),
        round(width * (col + 1) / 4),
        round(height * (row + 1) / 4),
    )


def _remove_chroma_key(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    pixels = image.load()
    width, height = image.size
    alpha = Image.new("L", image.size, 255)
    alpha_pixels = alpha.load()
    for y in range(height):
        for x in range(width):
            red, green, blue, _ = pixels[x, y]
            magenta_distance = abs(red - 255) + abs(green - 0) + abs(blue - 255)
            if magenta_distance <= 54:
                alpha_pixels[x, y] = 0
            elif red > 225 and blue > 225 and green < 80:
                alpha_pixels[x, y] = 0
    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.35))
    image.putalpha(alpha)
    return image


def _trim_alpha(image: Image.Image) -> Image.Image:
    bbox = image.getchannel("A").getbbox()
    return image.crop(bbox) if bbox else image


def _fit_glyph(image: Image.Image) -> Image.Image:
    image = _trim_alpha(image)
    canvas = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    max_width = ICON_SIZE - PADDING * 2
    max_height = ICON_SIZE - PADDING * 2
    scale = min(max_width / image.width, max_height / image.height)
    size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    resized = image.resize(size, Image.Resampling.LANCZOS)
    x = (ICON_SIZE - resized.width) // 2
    y = ICON_SIZE - resized.height - PADDING
    canvas.alpha_composite(resized, (x, y))
    return canvas


def slice_sheet(sheet_path: Path, out_dir: Path) -> None:
    sheet = Image.open(sheet_path).convert("RGBA")
    keyed = _remove_chroma_key(sheet)
    out_dir.mkdir(parents=True, exist_ok=True)
    for index, name in enumerate(GLYPH_NAMES):
        cell = keyed.crop(_cell_bounds(sheet.width, sheet.height, index))
        glyph = _fit_glyph(cell)
        output = out_dir / f"{name}.png"
        glyph.save(output, "PNG", optimize=True)
        print(f"Wrote {output}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Slice the generated terrain/forest atlas glyph sheet.")
    parser.add_argument("--sheet", type=Path, default=DEFAULT_SHEET)
    parser.add_argument("--out-dir", type=Path, default=GLYPH_DIR)
    args = parser.parse_args()
    if not args.sheet.exists():
        raise FileNotFoundError(args.sheet)
    slice_sheet(args.sheet, args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
