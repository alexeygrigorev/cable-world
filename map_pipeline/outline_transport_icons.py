import argparse
import os
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter


def _parse_color(text: str) -> tuple[int, int, int, int]:
    value = text.removeprefix("#")
    if len(value) != 8:
        raise ValueError("color must be #rrggbbaa")
    return tuple(int(value[index : index + 2], 16) for index in range(0, 8, 2))


def _alpha_expand(alpha: Image.Image, radius: int) -> Image.Image:
    return alpha.filter(ImageFilter.MaxFilter(radius * 2 + 1))


def _transport_glow_icon(
    source_path: Path,
    output_path: Path,
    edge_radius: int,
    glow_radius: int,
    glow_blur: float,
    edge_color: tuple[int, int, int, int],
    glow_color: tuple[int, int, int, int],
) -> None:
    source = Image.open(source_path).convert("RGBA")
    alpha = source.getchannel("A")

    expanded_edge = _alpha_expand(alpha, edge_radius)
    edge_alpha = ImageChops.subtract(expanded_edge, alpha)

    expanded_glow = _alpha_expand(alpha, glow_radius).filter(ImageFilter.GaussianBlur(glow_blur))
    glow_alpha = ImageChops.subtract(expanded_glow, alpha)

    out = Image.new("RGBA", source.size, (0, 0, 0, 0))
    glow_layer = Image.new("RGBA", source.size, glow_color)
    glow_layer.putalpha(glow_alpha)
    edge_layer = Image.new("RGBA", source.size, edge_color)
    edge_layer.putalpha(edge_alpha)

    out.alpha_composite(glow_layer)
    out.alpha_composite(edge_layer)
    out.alpha_composite(source)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.save(output_path, "PNG", optimize=True)


def _iter_icons(source_dir: Path, prefix: str) -> list[Path]:
    return sorted(path for path in source_dir.glob(f"{prefix}*.png") if path.is_file())


def main() -> int:
    parser = argparse.ArgumentParser(description="Create transport icon variants with a visible map glow.")
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--prefix", default="icon_")
    parser.add_argument("--edge-radius", type=int, default=1)
    parser.add_argument("--glow-radius", type=int, default=8)
    parser.add_argument("--glow-blur", type=float, default=3.0)
    parser.add_argument("--edge-color", default="#21150bd0")
    parser.add_argument("--glow-color", default="#9da05acc")
    args = parser.parse_args()

    source_paths = _iter_icons(args.source_dir, args.prefix)
    if not source_paths:
        raise FileNotFoundError(f"No PNG files found in {args.source_dir} with prefix {args.prefix!r}")

    edge_color = _parse_color(args.edge_color)
    glow_color = _parse_color(args.glow_color)
    for source_path in source_paths:
        output_path = args.out_dir / os.path.relpath(source_path, args.source_dir)
        _transport_glow_icon(
            source_path,
            output_path,
            args.edge_radius,
            args.glow_radius,
            args.glow_blur,
            edge_color,
            glow_color,
        )
        print(f"{source_path} -> {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
