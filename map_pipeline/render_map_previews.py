import argparse
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "assets" / "map" / "germany_styled.png"
DEFAULT_OUT_DIR = ROOT / "assets" / "map" / "review"
DEFAULT_ZOOMS = (50, 100, 150, 200)


def _parse_zooms(value: str) -> list[int]:
    zooms = []
    for item in value.split(","):
        item = item.strip().removesuffix("%")
        if not item:
            continue
        zoom = int(item)
        if zoom <= 0:
            raise argparse.ArgumentTypeError("Zoom values must be positive percentages")
        zooms.append(zoom)
    if not zooms:
        raise argparse.ArgumentTypeError("At least one zoom is required")
    return zooms


def render_previews(source: Path, out_dir: Path, zooms: list[int]) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / ".gdignore").write_text("", encoding="utf-8")

    image = Image.open(source).convert("RGB")
    written = []
    for zoom in zooms:
        scale = zoom / 100.0
        size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
        resampling = Image.Resampling.NEAREST if zoom >= 100 else Image.Resampling.LANCZOS
        preview = image.resize(size, resampling)
        output = out_dir / f"{source.stem}_preview_{zoom:03d}.png"
        preview.save(output, "PNG", optimize=True)
        written.append(output)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render fast full-map review PNGs from the same generated map texture used by the app."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--zooms", type=_parse_zooms, default=list(DEFAULT_ZOOMS))
    args = parser.parse_args()

    for output in render_previews(args.input, args.out_dir, args.zooms):
        print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
