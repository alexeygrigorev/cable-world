import argparse
from pathlib import Path

from PIL import Image

from map_pipeline.slice_city_cluster_landmarks import (
    CITY_CLUSTER_ICON_NAMES,
    _remove_tiny_alpha_islands,
    _trim_alpha,
)


ICON_SIZE = 1024
PADDING = 96
GRID_COLUMNS = 4
GRID_ROWS = 2
DEFAULT_OUT_DIR = "assets/sprites/city_landmark_clusters_hi_res"


def _cell_bounds(width: int, height: int, index: int) -> tuple[int, int, int, int]:
    col = index % GRID_COLUMNS
    row = index // GRID_COLUMNS
    return (
        round(width * col / GRID_COLUMNS),
        round(height * row / GRID_ROWS),
        round(width * (col + 1) / GRID_COLUMNS),
        round(height * (row + 1) / GRID_ROWS),
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


def _slice_sheet(sheet_path: Path, out_dir: Path) -> None:
    sheet = Image.open(sheet_path).convert("RGBA")
    for index, name in enumerate(CITY_CLUSTER_ICON_NAMES):
        cell = sheet.crop(_cell_bounds(sheet.width, sheet.height, index))
        _write_icon(cell, out_dir, name)


def _slice_sources(source_dir: Path, out_dir: Path) -> None:
    for name in CITY_CLUSTER_ICON_NAMES:
        source = Image.open(_source_path(source_dir, name)).convert("RGBA")
        _write_icon(source, out_dir, name)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build 1024px high-res city landmark cluster sprites from a 4x2 sheet or per-city sources."
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--sheet", type=Path, help="Transparent 4x2 city cluster sheet.")
    input_group.add_argument("--source-dir", type=Path, help="Directory with transparent city_<name>.png source images.")
    parser.add_argument("--out-dir", type=Path, default=Path(DEFAULT_OUT_DIR))
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.sheet:
        _slice_sheet(args.sheet, args.out_dir)
    else:
        _slice_sources(args.source_dir, args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
