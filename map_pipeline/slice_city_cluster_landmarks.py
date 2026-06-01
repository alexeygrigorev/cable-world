import argparse
from pathlib import Path
from collections import deque

from PIL import Image


ICON_SIZE = 512
PADDING = 48
GRID_COLUMNS = 4
GRID_ROWS = 2

CITY_CLUSTER_ICON_NAMES = [
    "berlin",
    "hamburg",
    "rostock",
    "munich",
    "cologne",
    "frankfurt",
    "stuttgart",
    "dresden",
]


def _remove_tiny_alpha_islands(image: Image.Image, min_pixels: int = 1200) -> Image.Image:
    alpha = image.getchannel("A")
    width, height = image.size
    alpha_data = alpha.load()
    visited = bytearray(width * height)
    keep = bytearray(width * height)

    for start_y in range(height):
        for start_x in range(width):
            start_index = start_y * width + start_x
            if visited[start_index] or alpha_data[start_x, start_y] == 0:
                continue

            component: list[tuple[int, int]] = []
            queue: deque[tuple[int, int]] = deque([(start_x, start_y)])
            visited[start_index] = 1

            while queue:
                x, y = queue.popleft()
                component.append((x, y))
                for next_x, next_y in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if next_x < 0 or next_y < 0 or next_x >= width or next_y >= height:
                        continue
                    next_index = next_y * width + next_x
                    if visited[next_index] or alpha_data[next_x, next_y] == 0:
                        continue
                    visited[next_index] = 1
                    queue.append((next_x, next_y))

            min_x = min(x for x, _y in component)
            max_x = max(x for x, _y in component)
            min_y = min(y for _x, y in component)
            max_y = max(y for _x, y in component)
            touches_edge = min_x == 0 or min_y == 0 or max_x == width - 1 or max_y == height - 1
            narrow_edge_fragment = touches_edge and (max_x - min_x < 96 or max_y - min_y < 96)

            if len(component) >= min_pixels and not narrow_edge_fragment:
                for x, y in component:
                    keep[y * width + x] = 1

    cleaned_alpha = Image.new("L", image.size, 0)
    cleaned_data = cleaned_alpha.load()
    for y in range(height):
        for x in range(width):
            if keep[y * width + x]:
                cleaned_data[x, y] = alpha_data[x, y]

    cleaned = image.copy()
    cleaned.putalpha(cleaned_alpha)
    return cleaned


def _cell_bounds(width: int, height: int, index: int) -> tuple[int, int, int, int]:
    col = index % GRID_COLUMNS
    row = index // GRID_COLUMNS
    return (
        round(width * col / GRID_COLUMNS),
        round(height * row / GRID_ROWS),
        round(width * (col + 1) / GRID_COLUMNS),
        round(height * (row + 1) / GRID_ROWS),
    )


def _trim_alpha(image: Image.Image) -> Image.Image:
    bbox = image.getchannel("A").getbbox()
    return image.crop(bbox) if bbox else image


def _fit_icon(image: Image.Image) -> Image.Image:
    icon = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    max_side = ICON_SIZE - PADDING * 2
    scale = min(max_side / image.width, max_side / image.height)
    resized = image.resize(
        (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
        Image.Resampling.LANCZOS,
    )
    icon.alpha_composite(resized, ((ICON_SIZE - resized.width) // 2, (ICON_SIZE - resized.height) // 2))
    return icon


def main() -> int:
    parser = argparse.ArgumentParser(description="Slice a 4x2 multi-symbol city landmark sprite sheet.")
    parser.add_argument("--sheet", required=True)
    parser.add_argument("--out-dir", default="assets/sprites/city_landmark_clusters")
    args = parser.parse_args()

    sheet = Image.open(args.sheet).convert("RGBA")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for index, name in enumerate(CITY_CLUSTER_ICON_NAMES):
        cell = sheet.crop(_cell_bounds(sheet.width, sheet.height, index))
        icon = _fit_icon(_trim_alpha(_remove_tiny_alpha_islands(cell)))
        out = out_dir / f"city_{name}.png"
        icon.save(out, "PNG", optimize=True)
        print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
