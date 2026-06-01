import argparse
import math
from collections import deque
from pathlib import Path

from PIL import Image

from map_pipeline.city_cluster_glyph_specs import DEFAULT_SPECS_FILE, city_ids, load_specs


ICON_SIZE = 1024
PADDING = 96
GRID_COLUMNS = 4
GRID_ROWS = 2
DEFAULT_OUT_DIR = "assets/sprites/city_landmark_clusters_hi_res"
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


def _trim_alpha(image: Image.Image) -> Image.Image:
    bbox = image.getchannel("A").getbbox()
    return image.crop(bbox) if bbox else image


def _cell_bounds(width: int, height: int, index: int, columns: int, rows: int) -> tuple[int, int, int, int]:
    col = index % columns
    row = index // columns
    return (
        round(width * col / columns),
        round(height * row / rows),
        round(width * (col + 1) / columns),
        round(height * (row + 1) / rows),
    )


def _fit_hi_res_icon(image: Image.Image) -> Image.Image:
    icon = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    max_side = ICON_SIZE - PADDING * 2
    scale = min(max_side / image.width, max_side / image.height)
    resized = image.resize(
        (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
        Image.Resampling.LANCZOS,
    )
    icon.alpha_composite(resized, ((ICON_SIZE - resized.width) // 2, (ICON_SIZE - resized.height) // 2))
    return icon


def _source_path(source_dir: Path, name: str) -> Path:
    for candidate in (source_dir / f"city_{name}.png", source_dir / f"{name}.png"):
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Missing source for {name}: expected city_{name}.png or {name}.png in {source_dir}")


def _write_icon(image: Image.Image, out_dir: Path, name: str) -> None:
    icon = _fit_hi_res_icon(_trim_alpha(_remove_tiny_alpha_islands(image)))
    out = out_dir / f"city_{name}.png"
    icon.save(out, "PNG", optimize=True)
    print(f"Wrote {out}")


def _slice_sheet(sheet_path: Path, out_dir: Path, names: list[str], columns: int) -> None:
    sheet = Image.open(sheet_path).convert("RGBA")
    rows = max(1, math.ceil(len(names) / columns))
    for index, name in enumerate(names):
        cell = sheet.crop(_cell_bounds(sheet.width, sheet.height, index, columns, rows))
        _write_icon(cell, out_dir, name)


def _slice_sources(source_dir: Path, out_dir: Path, names: list[str]) -> None:
    for name in names:
        source = Image.open(_source_path(source_dir, name)).convert("RGBA")
        _write_icon(source, out_dir, name)


def _resolve_names(args: argparse.Namespace) -> list[str]:
    if args.ids:
        return [item.strip() for item in args.ids.split(",") if item.strip()]
    if args.specs_file:
        return city_ids(load_specs(args.specs_file), args.status)
    return CITY_CLUSTER_ICON_NAMES


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build 1024px high-res city landmark cluster sprites from a sheet or per-city sources."
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--sheet", type=Path, help="Transparent city cluster sheet.")
    input_group.add_argument("--source-dir", type=Path, help="Directory with transparent city_<name>.png source images.")
    parser.add_argument("--out-dir", type=Path, default=Path(DEFAULT_OUT_DIR))
    parser.add_argument("--specs-file", type=Path, default=DEFAULT_SPECS_FILE, help=f"City specs JSON. Defaults to {DEFAULT_SPECS_FILE}.")
    parser.add_argument("--status", choices=["existing_cluster", "planned_cluster"], default=None)
    parser.add_argument("--ids", help="Comma-separated city ids in sheet/source order.")
    parser.add_argument("--columns", type=int, default=GRID_COLUMNS)
    args = parser.parse_args()

    names = _resolve_names(args)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.sheet:
        _slice_sheet(args.sheet, args.out_dir, names, max(1, args.columns))
    else:
        _slice_sources(args.source_dir, args.out_dir, names)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
