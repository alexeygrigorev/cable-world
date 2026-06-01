import argparse
import json
import shutil
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "assets" / "map" / "germany_styled.png"
DEFAULT_OUT_DIR = ROOT / "assets" / "map" / "review"
MASSIF_DIR = ROOT / "assets" / "map" / "massifs"
DEFAULT_ZOOMS = (50, 100, 150, 200)
DEFAULT_CROP_PADDING = 96


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


def _clean_output_dir(out_dir: Path) -> None:
    if not out_dir.exists():
        return
    for path in out_dir.iterdir():
        if path.name == ".gdignore":
            continue
        if path.is_dir():
            shutil.rmtree(path)
        elif path.suffix.lower() == ".png":
            path.unlink()


def _resize_for_zoom(image: Image.Image, zoom: int) -> Image.Image:
    scale = zoom / 100.0
    size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    resampling = Image.Resampling.NEAREST if zoom >= 100 else Image.Resampling.LANCZOS
    return image.resize(size, resampling)


def _render_zoom_set(image: Image.Image, out_dir: Path, stem: str, zooms: list[int]) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for zoom in zooms:
        preview = _resize_for_zoom(image, zoom)
        output = out_dir / f"{stem}_preview_{zoom:03d}.png"
        preview.save(output, "PNG", optimize=True)
        written.append(output)
    return written


def _crop_bbox(bbox: list[float], image_size: tuple[int, int], padding: int) -> tuple[int, int, int, int]:
    left, top, right, bottom = bbox
    return (
        max(0, int(left) - padding),
        max(0, int(top) - padding),
        min(image_size[0], int(right + 0.999) + padding),
        min(image_size[1], int(bottom + 0.999) + padding),
    )


def _massif_entries() -> list[dict]:
    entries = []
    for path in sorted(MASSIF_DIR.glob("*.json")):
        if path.name == "manifest.json":
            continue
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if data.get("map_bbox_px"):
            entries.append(data)
    return entries


def render_previews(
    source: Path,
    out_dir: Path,
    zooms: list[int],
    include_tabs: bool = True,
    crop_padding: int = DEFAULT_CROP_PADDING,
    clean: bool = True,
) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / ".gdignore").write_text("", encoding="utf-8")
    if clean:
        _clean_output_dir(out_dir)

    image = Image.open(source).convert("RGB")
    written = _render_zoom_set(image, out_dir, source.stem, zooms)
    manifest_tabs = [
        {
            "id": "full-map",
            "title": "Full map",
            "description": "Current generated map texture at review zoom levels.",
        }
    ]

    if include_tabs:
        for entry in _massif_entries():
            crop = image.crop(_crop_bbox(entry["map_bbox_px"], image.size, crop_padding))
            tab_id = entry.get("id", "review_set")
            tab_dir = out_dir / str(tab_id)
            written.extend(_render_zoom_set(crop, tab_dir, str(tab_id), zooms))
            manifest_tabs.append(
                {
                    "id": str(tab_id),
                    "title": str(entry.get("label") or tab_id).replace("_", " "),
                    "description": str(entry.get("kind") or "Massif crop from generated map texture."),
                }
            )
    manifest = {
        "schema": "cable-world.map-review-previews.v1",
        "source": str(source.relative_to(ROOT) if source.is_relative_to(ROOT) else source),
        "zooms": zooms,
        "crop_padding_px": crop_padding,
        "tabs": manifest_tabs,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return written


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render fast full-map review PNGs from the same generated map texture used by the app."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--zooms", type=_parse_zooms, default=list(DEFAULT_ZOOMS))
    parser.add_argument("--crop-padding", type=int, default=DEFAULT_CROP_PADDING)
    parser.add_argument("--no-tabs", action="store_true", help="Only render the full-map preview set.")
    parser.add_argument("--no-clean", action="store_true", help="Keep existing review PNGs instead of replacing them.")
    args = parser.parse_args()

    for output in render_previews(
        args.input,
        args.out_dir,
        args.zooms,
        include_tabs=not args.no_tabs,
        crop_padding=args.crop_padding,
        clean=not args.no_clean,
    ):
        print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
