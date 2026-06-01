import argparse
from pathlib import Path

from PIL import Image, ImageFilter


MAP_DIR = Path(__file__).resolve().parent.parent / "assets" / "map"
GLYPH_DIR = MAP_DIR / "glyphs"
DEFAULT_SHEET = GLYPH_DIR / "massif_alps_sector_sheet.png"
PADDING = 14
MIN_COMPONENT_AREA = 2000

GLYPH_NAMES = [
    "massif_alps_western_arc",
    "massif_alps_central_high",
    "massif_alps_eastern_arc",
    "massif_alps_tyrol_wall",
    "massif_alps_northern_edge",
    "massif_alps_foothill_connector",
]


def _cell_bounds(width: int, height: int, index: int) -> tuple[int, int, int, int]:
    col = index % 3
    row = index // 3
    return (
        round(width * col / 3),
        round(height * row / 2),
        round(width * (col + 1) / 3),
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
            if magenta_distance <= 70 or (red > 220 and blue > 220 and green < 105):
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


def _remove_small_alpha_components(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    alpha = image.getchannel("A")
    pixels = alpha.load()
    width, height = alpha.size
    visited = bytearray(width * height)
    keep = bytearray(width * height)

    for y in range(height):
        for x in range(width):
            index = y * width + x
            if visited[index] or pixels[x, y] == 0:
                continue

            stack = [(x, y)]
            visited[index] = 1
            component = []
            while stack:
                cx, cy = stack.pop()
                component.append((cx, cy))
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if nx < 0 or ny < 0 or nx >= width or ny >= height:
                        continue
                    nindex = ny * width + nx
                    if visited[nindex] or pixels[nx, ny] == 0:
                        continue
                    visited[nindex] = 1
                    stack.append((nx, ny))

            if len(component) >= MIN_COMPONENT_AREA:
                for cx, cy in component:
                    keep[cy * width + cx] = 1

    clean_alpha = Image.new("L", alpha.size, 0)
    clean_pixels = clean_alpha.load()
    for y in range(height):
        for x in range(width):
            if keep[y * width + x]:
                clean_pixels[x, y] = pixels[x, y]
    image.putalpha(clean_alpha)
    return image


def slice_sheet(sheet_path: Path, out_dir: Path) -> None:
    sheet = Image.open(sheet_path).convert("RGBA")
    keyed = _remove_chroma_key(sheet)
    out_dir.mkdir(parents=True, exist_ok=True)
    for index, name in enumerate(GLYPH_NAMES):
        cell = keyed.crop(_cell_bounds(sheet.width, sheet.height, index))
        glyph = _trim_with_padding(_remove_small_alpha_components(cell))
        output = out_dir / f"{name}.png"
        glyph.save(output, "PNG", optimize=True)
        print(f"Wrote {output} {glyph.width}x{glyph.height}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Slice generated Alpine sector glyph sheet into source glyphs.")
    parser.add_argument("--sheet", type=Path, default=DEFAULT_SHEET)
    parser.add_argument("--out-dir", type=Path, default=GLYPH_DIR)
    args = parser.parse_args()
    if not args.sheet.exists():
        raise FileNotFoundError(args.sheet)
    slice_sheet(args.sheet, args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
