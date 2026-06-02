import argparse
import sys
from pathlib import Path

from PIL import Image


DEFAULT_CITY_DIR = Path("assets/sprites/city_landmark_clusters_hi_res/outlined")


def _count_water_like_pixels(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        rgba = image.convert("RGBA")
    total = 0
    water = 0
    for r, g, b, a in rgba.getdata():
        if a < 48:
            continue
        total += 1
        # Conservative blue/cyan water heuristic. It is intentionally used as
        # a review gate, not as an automatic delete/fix operation.
        if b >= 70 and b > r * 1.18 and b > g * 0.92 and g >= r * 0.75:
            water += 1
    return water, total


def audit(paths: list[Path], max_water_ratio: float, max_water_pixels: int) -> list[str]:
    errors: list[str] = []
    for path in paths:
        water, total = _count_water_like_pixels(path)
        ratio = water / total if total else 0.0
        print(f"{path}: water_like_pixels={water} total_alpha_pixels={total} ratio={ratio:.4f}")
        if water > max_water_pixels and ratio > max_water_ratio:
            errors.append(
                f"{path}: water-like content ratio {ratio:.4f} exceeds {max_water_ratio:.4f} "
                f"with {water} pixels"
            )
    return errors


def _resolve_paths(args: argparse.Namespace) -> list[Path]:
    if args.paths:
        return args.paths
    return sorted(args.city_dir.glob("city_*.png"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit city glyphs for disallowed water-like content.")
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--city-dir", type=Path, default=DEFAULT_CITY_DIR)
    parser.add_argument("--max-water-ratio", type=float, default=0.018)
    parser.add_argument("--max-water-pixels", type=int, default=160)
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args()

    paths = _resolve_paths(args)
    if not paths:
        raise SystemExit(f"No city PNGs found in {args.city_dir}")

    errors = audit(paths, args.max_water_ratio, args.max_water_pixels)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 0 if args.warn_only else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
