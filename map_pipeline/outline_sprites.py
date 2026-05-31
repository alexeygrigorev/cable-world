import argparse
import os
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter


def _outline_sprite(source_path: Path, output_path: Path, radius: int, color: tuple[int, int, int, int]) -> None:
    source = Image.open(source_path).convert("RGBA")
    alpha = source.getchannel("A")
    outline_alpha = alpha.filter(ImageFilter.MaxFilter(radius * 2 + 1))
    outline_alpha = ImageChops.subtract(outline_alpha, alpha)

    outlined = Image.new("RGBA", source.size, (0, 0, 0, 0))
    outline_layer = Image.new("RGBA", source.size, color)
    outline_layer.putalpha(outline_alpha)
    outlined.alpha_composite(outline_layer)
    outlined.alpha_composite(source)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    outlined.save(output_path, "PNG", optimize=True)


def _iter_pngs(source_dir: Path, prefix: str) -> list[Path]:
    return sorted(path for path in source_dir.glob(f"{prefix}*.png") if path.is_file())


def main() -> int:
    parser = argparse.ArgumentParser(description="Create outlined runtime sprite variants for the map UI.")
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--prefix", default="", help="Only process PNG files with this prefix.")
    parser.add_argument("--radius", type=int, default=3)
    parser.add_argument("--color", default="#23170de0", help="Outline color as #rrggbbaa.")
    args = parser.parse_args()

    color_text = args.color.removeprefix("#")
    if len(color_text) != 8:
        raise ValueError("--color must be #rrggbbaa")
    color = tuple(int(color_text[index : index + 2], 16) for index in range(0, 8, 2))

    source_paths = _iter_pngs(args.source_dir, args.prefix)
    if not source_paths:
        raise FileNotFoundError(f"No PNG files found in {args.source_dir} with prefix {args.prefix!r}")

    for source_path in source_paths:
        output_path = args.out_dir / os.path.relpath(source_path, args.source_dir)
        _outline_sprite(source_path, output_path, args.radius, color)
        print(f"{source_path} -> {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
