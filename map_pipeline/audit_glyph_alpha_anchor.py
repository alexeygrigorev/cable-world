"""Audit transparent glyph PNGs for bottom-left anchor readiness."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GLOB = "assets/map/massifs/*.png"


def alpha_bbox(path: Path) -> tuple[int, int, int, int] | None:
    with Image.open(path) as image:
        return image.convert("RGBA").getchannel("A").getbbox()


def bottom_padding(path: Path) -> int:
    with Image.open(path) as image:
        bbox = image.convert("RGBA").getchannel("A").getbbox()
        if bbox is None:
            return image.height
        return image.height - bbox[3]


def shift_alpha_to_bottom(path: Path) -> int:
    with Image.open(path) as source:
        image = source.convert("RGBA")
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        return 0
    shift = image.height - bbox[3]
    if shift <= 0:
        return 0
    output = Image.new("RGBA", image.size, (0, 0, 0, 0))
    output.alpha_composite(image, (0, shift))
    output.save(path, "PNG", optimize=True)
    return shift


def audit(paths: list[Path], max_bottom_padding: int, fix: bool) -> list[str]:
    errors: list[str] = []
    for path in paths:
        if fix:
            shift_alpha_to_bottom(path)
        padding = bottom_padding(path)
        bbox = alpha_bbox(path)
        print(f"{path}: bottom_padding={padding} alpha_bbox={bbox}")
        if padding > max_bottom_padding:
            errors.append(
                f"{path} bottom alpha padding is {padding}px; expected <= {max_bottom_padding}px "
                "for bottom-left glyph anchoring"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="PNG glyphs to audit; defaults to assets/map/massifs/*.png")
    parser.add_argument("--max-bottom-padding", type=int, default=1)
    parser.add_argument("--fix", action="store_true", help="Shift alpha content down so bottom padding becomes zero.")
    args = parser.parse_args()

    paths = args.paths or sorted(ROOT.glob(DEFAULT_GLOB))
    errors = audit(paths, args.max_bottom_padding, args.fix)
    if errors:
        for error in errors:
            print(error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
