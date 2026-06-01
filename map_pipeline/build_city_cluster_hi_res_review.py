import argparse
import json
from pathlib import Path

from PIL import Image

from map_pipeline.city_cluster_glyph_specs import DEFAULT_SPECS_FILE, city_ids, load_specs
from map_pipeline.slice_city_cluster_landmarks_hi_res import CITY_CLUSTER_ICON_NAMES


DEFAULT_SOURCE_DIR = Path("assets/sprites/city_landmark_clusters_hi_res/outlined")
DEFAULT_OUT_DIR = Path("assets/map/review/city_cluster_glyphs_hi_res")
PREVIEW_FILE_TEMPLATE = "city_cluster_glyphs_hi_res_preview_%s.png"
PREVIEW_SCALES = {
    "200": 1.0,
}


def _load_icon(source_dir: Path, name: str) -> Image.Image:
    path = source_dir / f"city_{name}.png"
    if not path.exists():
        raise FileNotFoundError(f"Missing hi-res outlined city cluster: {path}")
    return Image.open(path).convert("RGBA")


def _build_contact_sheet(source_dir: Path, names: list[str]) -> Image.Image:
    icons = [_load_icon(source_dir, name) for name in names]
    icon_size = max(max(icon.size) for icon in icons)
    gap = 36
    margin = 48
    columns = min(5, max(1, len(names)))
    rows = (len(names) + columns - 1) // columns
    cell_w = icon_size + gap
    cell_h = icon_size + gap
    sheet = Image.new(
        "RGBA",
        (margin * 2 + cell_w * columns - gap, margin * 2 + cell_h * rows - gap),
        (238, 225, 196, 255),
    )

    for index, (name, icon) in enumerate(zip(names, icons)):
        col = index % columns
        row = index // columns
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
    parser.add_argument("--specs-file", type=Path, default=DEFAULT_SPECS_FILE, help=f"City specs JSON. Defaults to {DEFAULT_SPECS_FILE}.")
    parser.add_argument("--status", choices=["existing_cluster", "planned_cluster"], default=None)
    parser.add_argument(
        "--description",
        default="Separate per-city 1024px source glyphs for German city clusters.",
    )
    parser.add_argument(
        "--feedback-target",
        default="Review source-quality city cluster glyphs before replacing or adding runtime city assets.",
    )
    args = parser.parse_args()

    names = city_ids(load_specs(args.specs_file), args.status) if args.specs_file else CITY_CLUSTER_ICON_NAMES
    args.out_dir.mkdir(parents=True, exist_ok=True)
    contact = _build_contact_sheet(args.source_dir, names)
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
        "cities": names,
        "order": sorted(PREVIEW_SCALES),
        "scaleSemantics": "static_source_quality_only",
        "runtime_integrated": True,
    }
    metadata_path = args.out_dir / "review.yml"
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
