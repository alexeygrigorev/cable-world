import argparse
from pathlib import Path

from PIL import Image


TARGET_SIZE = (1568, 2048)


def _fit_crop(image: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    source_aspect = image.width / image.height
    target_aspect = target_size[0] / target_size[1]
    if source_aspect < target_aspect:
        crop_height = round(image.width / target_aspect)
        top = max(0, (image.height - crop_height) // 2)
        image = image.crop((0, top, image.width, top + crop_height))
    elif source_aspect > target_aspect:
        crop_width = round(image.height * target_aspect)
        left = max(0, (image.width - crop_width) // 2)
        image = image.crop((left, 0, left + crop_width, image.height))
    return image.resize(target_size, Image.Resampling.LANCZOS)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Adapt one generated RPG map underlay into the runtime Germany map asset."
    )
    parser.add_argument("--source", required=True, help="Generated source PNG outside assets/.")
    parser.add_argument(
        "--out",
        default="assets/map/germany_styled.png",
        help="Runtime output PNG. Defaults to assets/map/germany_styled.png.",
    )
    parser.add_argument(
        "--colors",
        type=int,
        default=128,
        help="Palette size for PNG compression. Use 0 to keep RGB.",
    )
    args = parser.parse_args()

    source = Path(args.source)
    out = Path(args.out)
    image = Image.open(source).convert("RGB")
    image = _fit_crop(image, TARGET_SIZE)
    if args.colors > 0:
        image = image.quantize(colors=args.colors, method=Image.Quantize.MEDIANCUT).convert("RGB")
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out, "PNG", optimize=True)
    print(f"Wrote {out} {image.size[0]}x{image.size[1]} {out.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
