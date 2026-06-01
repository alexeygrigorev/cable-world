import argparse
import json
from pathlib import Path

from PIL import Image

from map_pipeline.slice_city_cluster_landmarks import CITY_CLUSTER_ICON_NAMES


DEFAULT_SOURCE_DIR = Path("assets/sprites/city_landmark_clusters_hi_res/outlined")
DEFAULT_OUT_DIR = Path("assets/map/review/city_cluster_glyphs_hi_res")
PREVIEW_FILE_TEMPLATE = "city_cluster_glyphs_hi_res_preview_%s.png"
PREVIEW_SCALES = {
    "050": 0.25,
    "100": 0.5,
    "150": 0.75,
    "200": 1.0,
}


def _load_icon(source_dir: Path, name: str) -> Image.Image:
    path = source_dir / f"city_{name}.png"
    if not path.exists():
        raise FileNotFoundError(f"Missing hi-res outlined city cluster: {path}")
    return Image.open(path).convert("RGBA")


def _build_contact_sheet(source_dir: Path) -> Image.Image:
    icons = [_load_icon(source_dir, name) for name in CITY_CLUSTER_ICON_NAMES]
    icon_size = max(max(icon.size) for icon in icons)
    gap = 36
    margin = 48
    cell_w = icon_size + gap
    cell_h = icon_size + gap
    sheet = Image.new("RGBA", (margin * 2 + cell_w * 4 - gap, margin * 2 + cell_h * 2 - gap), (238, 225, 196, 255))

    for index, (name, icon) in enumerate(zip(CITY_CLUSTER_ICON_NAMES, icons)):
        col = index % 4
        row = index // 4
        x = margin + col * cell_w
        y = margin + row * cell_h
        icon_x = x + (icon_size - icon.width) // 2
        icon_y = y
        sheet.alpha_composite(icon, (icon_x, icon_y))

    return sheet


def main() -> int:
    parser = argparse.ArgumentParser(description="Build static review previews for hi-res city cluster glyphs.")
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--id", default="city_cluster_glyphs_hi_res")
    parser.add_argument("--title", default="Hi-res City Cluster Glyphs")
    parser.add_argument(
        "--description",
        default="Separate per-city 1024px source glyphs for the first 8 German city clusters.",
    )
    parser.add_argument(
        "--feedback-target",
        default="Compare this against city_cluster_glyphs and check whether 200% still pixelates.",
    )
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    contact = _build_contact_sheet(args.source_dir)
    for suffix, scale in PREVIEW_SCALES.items():
        size = (round(contact.width * scale), round(contact.height * scale))
        resampling = Image.Resampling.NEAREST if scale >= 1 else Image.Resampling.LANCZOS
        out = contact.resize(size, resampling)
        out_path = args.out_dir / f"{args.id}_preview_{suffix}.png"
        out.save(out_path, "PNG", optimize=True)
        print(f"Wrote {out_path}")

    metadata = {
        "schema": "cable-world.map-review-set.v1",
        "id": args.id,
        "title": args.title,
        "description": args.description,
        "feedbackTarget": args.feedback_target,
        "source": str(args.source_dir),
        "order": sorted(PREVIEW_SCALES),
        "runtime_integrated": False,
    }
    metadata_path = args.out_dir / "review.yml"
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
