import argparse
import sys
from pathlib import Path

from PIL import Image

from map_pipeline.city_glyph_size_contract import (
    ICON_SIZE,
    MAX_OUTLINED_CONTENT_SIDE,
    MAX_WIDE_OUTLINED_CONTENT_WIDTH,
    OUTLINED_BOTTOM_PADDING,
    OUTLINED_ALPHA_AREA_MAX,
    OUTLINED_ALPHA_AREA_MIN,
    WIDE_CONTENT_ASPECT_RATIO,
)


DEFAULT_CITY_DIR = Path("assets/sprites/city_landmark_clusters_hi_res/outlined")


def _alpha_metrics(path: Path) -> tuple[tuple[int, int, int, int] | None, float]:
    with Image.open(path) as image:
        if image.size != (ICON_SIZE, ICON_SIZE):
            raise ValueError(f"{path} has size {image.size}; expected {(ICON_SIZE, ICON_SIZE)}")
        alpha = image.convert("RGBA").getchannel("A")
        return alpha.getbbox(), sum(alpha.getdata()) / 255.0


def audit(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        bbox, alpha_area = _alpha_metrics(path)
        if bbox is None:
            errors.append(f"{path}: empty alpha")
            continue

        left, top, right, bottom = bbox
        width = right - left
        height = bottom - top
        aspect = width / height
        bottom_padding = ICON_SIZE - bottom
        max_width = MAX_WIDE_OUTLINED_CONTENT_WIDTH if aspect > WIDE_CONTENT_ASPECT_RATIO else MAX_OUTLINED_CONTENT_SIDE

        print(
            f"{path}: alpha_bbox={bbox} width={width} height={height} "
            f"aspect={aspect:.2f} alpha_area={alpha_area:.0f} bottom_padding={bottom_padding}"
        )

        if width > max_width:
            errors.append(f"{path}: alpha width {width}px exceeds {max_width}px for aspect {aspect:.2f}")
        if height > MAX_OUTLINED_CONTENT_SIDE:
            errors.append(f"{path}: alpha height {height}px exceeds {MAX_OUTLINED_CONTENT_SIDE}px")
        if alpha_area < OUTLINED_ALPHA_AREA_MIN or alpha_area > OUTLINED_ALPHA_AREA_MAX:
            errors.append(
                f"{path}: weighted alpha area {alpha_area:.0f}px is outside "
                f"{OUTLINED_ALPHA_AREA_MIN:.0f}..{OUTLINED_ALPHA_AREA_MAX:.0f}px"
            )
        if bottom_padding != OUTLINED_BOTTOM_PADDING:
            errors.append(f"{path}: bottom padding {bottom_padding}px; expected {OUTLINED_BOTTOM_PADDING}px")

    return errors


def _resolve_paths(args: argparse.Namespace) -> list[Path]:
    if args.paths:
        return args.paths
    return sorted(args.city_dir.glob("city_*.png"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit runtime city glyph alpha dimensions.")
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--city-dir", type=Path, default=DEFAULT_CITY_DIR)
    args = parser.parse_args()

    paths = _resolve_paths(args)
    if not paths:
        raise SystemExit(f"No city PNGs found in {args.city_dir}")

    errors = audit(paths)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
