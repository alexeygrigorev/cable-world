import json
from pathlib import Path

from PIL import Image, ImageDraw

from map_pipeline.compose_map import RELIEF_REGIONS


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets" / "map" / "massif_layouts"
MAP_BOUNDS = (4.5, 43.2, 16.8, 55.8)
CELL_SIZE = (1024, 768)
SHEET_COLS = 4
SHEET_ROWS = 2

BACKGROUND = (243, 236, 205, 255)
POLYGON_FILL = (87, 132, 75, 128)
POLYGON_OUTLINE = (52, 76, 45, 230)
SHADOW_FILL = (82, 100, 66, 112)
RIDGE_LINE = (90, 54, 34, 255)
HIGH_ZONE = (170, 178, 142, 170)
ANCHOR_DOT = (170, 50, 42, 255)
ALPINE_SNOW_ZONE = (235, 239, 224, 210)


def _project(lon, lat, bounds, size):
    min_lon, min_lat, max_lon, max_lat = bounds
    width, height = size
    x = (lon - min_lon) / (max_lon - min_lon) * width
    y = (max_lat - lat) / (max_lat - min_lat) * height
    return int(round(x)), int(round(y))


def _all_points(layer):
    points = []
    points.extend(layer.get("points", []))
    points.extend((lon, lat) for lon, lat, _size in layer.get("trees", []))
    points.extend((lon, lat) for _glyph, lon, lat, _width in layer.get("mountain_glyphs", []))
    for ridge in layer.get("ridge_bands", []):
        points.extend(ridge.get("points", []))
    for segment in layer.get("massif_segments", []):
        points.extend(segment.get("arc", []))
        points.extend(segment.get("shadow", []))
        points.extend((lon, lat) for _glyph, lon, lat, _width, _offset in segment.get("glyphs", []))
    return points


def _bounds_for_points(points, padding_lon=0.35, padding_lat=0.28):
    min_lon = min(lon for lon, _lat in points) - padding_lon
    max_lon = max(lon for lon, _lat in points) + padding_lon
    min_lat = min(lat for _lon, lat in points) - padding_lat
    max_lat = max(lat for _lon, lat in points) + padding_lat
    return min_lon, min_lat, max_lon, max_lat


def _fit_bounds_to_aspect(bounds, size):
    min_lon, min_lat, max_lon, max_lat = bounds
    target_aspect = size[0] / size[1]
    width = max_lon - min_lon
    height = max_lat - min_lat
    if width / height > target_aspect:
        wanted_height = width / target_aspect
        extra = wanted_height - height
        min_lat -= extra / 2
        max_lat += extra / 2
    else:
        wanted_width = height * target_aspect
        extra = wanted_width - width
        min_lon -= extra / 2
        max_lon += extra / 2
    return min_lon, min_lat, max_lon, max_lat


def _poly(draw, points, bounds, fill, outline, width=5):
    if len(points) < 3:
        return
    draw.polygon([_project(lon, lat, bounds, CELL_SIZE) for lon, lat in points], fill=fill, outline=outline)
    draw.line(
        [_project(lon, lat, bounds, CELL_SIZE) for lon, lat in points + [points[0]]],
        fill=outline,
        width=width,
        joint="curve",
    )


def _line(draw, points, bounds, fill, width=10):
    if len(points) < 2:
        return
    draw.line([_project(lon, lat, bounds, CELL_SIZE) for lon, lat in points], fill=fill, width=width, joint="curve")


def _dot(draw, lon, lat, bounds, radius=11, fill=ANCHOR_DOT):
    x, y = _project(lon, lat, bounds, CELL_SIZE)
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill)


def _draw_layout(layer):
    points = _all_points(layer)
    bounds = _fit_bounds_to_aspect(_bounds_for_points(points), CELL_SIZE)
    image = Image.new("RGBA", CELL_SIZE, BACKGROUND)
    draw = ImageDraw.Draw(image, "RGBA")

    if layer.get("points"):
        _poly(draw, layer["points"], bounds, POLYGON_FILL, POLYGON_OUTLINE)

    for segment in layer.get("massif_segments", []):
        if segment.get("shadow"):
            _poly(draw, segment["shadow"], bounds, SHADOW_FILL, POLYGON_OUTLINE, width=4)
        if segment.get("arc"):
            _line(draw, segment["arc"], bounds, RIDGE_LINE, width=12)
            _line(draw, [(lon, lat + 0.05) for lon, lat in segment["arc"]], bounds, ALPINE_SNOW_ZONE, width=8)
        for _glyph, lon, lat, width, _offset in segment.get("glyphs", []):
            _dot(draw, lon, lat, bounds, radius=max(8, int(width / 32)), fill=ANCHOR_DOT)

    for ridge in layer.get("ridge_bands", []):
        ridge_width = max(7, int(ridge.get("height", 32) / 4))
        _line(draw, ridge.get("points", []), bounds, RIDGE_LINE, width=ridge_width)
        if ridge.get("style") == "sandstone":
            _line(draw, [(lon, lat + 0.025) for lon, lat in ridge.get("points", [])], bounds, (188, 149, 91, 225), width=5)

    for _glyph, lon, lat, width in layer.get("mountain_glyphs", []):
        _dot(draw, lon, lat, bounds, radius=max(10, int(width / 24)), fill=ANCHOR_DOT)

    for lon, lat, size in layer.get("trees", []):
        _dot(draw, lon, lat, bounds, radius=max(7, int(size / 10)), fill=(46, 111, 66, 210))

    metadata = {
        "id": layer["id"],
        "label": layer.get("label", layer["id"]),
        "kind": layer.get("kind"),
        "layout_bounds": [round(value, 5) for value in bounds],
        "size_px": list(CELL_SIZE),
        "source": "map_pipeline.compose_map RELIEF_REGIONS/ALPINE_MASSIF_SEGMENTS",
        "purpose": "image-reference layout for geographically guided massif glyph generation",
    }
    return image, metadata


def _layers_to_render():
    ids = {
        "alps",
        "harz",
        "black_forest",
        "bavarian_forest",
        "erzgebirge",
        "saxon_switzerland",
        "eifel_hunsrueck",
    }
    return [region for region in RELIEF_REGIONS if region["id"] in ids]


def _write_sheet(layouts):
    sheet = Image.new("RGBA", (CELL_SIZE[0] * SHEET_COLS, CELL_SIZE[1] * SHEET_ROWS), BACKGROUND)
    manifest = []
    for index, (layer_id, image, metadata) in enumerate(layouts):
        col = index % SHEET_COLS
        row = index // SHEET_COLS
        if row >= SHEET_ROWS:
            break
        x = col * CELL_SIZE[0]
        y = row * CELL_SIZE[1]
        sheet.alpha_composite(image, (x, y))
        sheet_bbox = [x, y, x + CELL_SIZE[0], y + CELL_SIZE[1]]
        manifest.append({"id": layer_id, "sheet_bbox_px": sheet_bbox, "layout_bounds": metadata["layout_bounds"]})

    sheet_path = OUT_DIR / "massif_geo_layout_sheet.png"
    sheet.save(sheet_path, optimize=True)
    return sheet_path, manifest


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / ".gdignore").write_text("", encoding="utf-8")

    layouts = []
    for layer in _layers_to_render():
        image, metadata = _draw_layout(layer)
        image_path = OUT_DIR / f"{layer['id']}_layout.png"
        json_path = OUT_DIR / f"{layer['id']}_layout.json"
        image.save(image_path, optimize=True)
        json_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        layouts.append((layer["id"], image, metadata))

    sheet_path, sheet_entries = _write_sheet(layouts)
    manifest = {
        "schema": "cable-world.massif-geo-layouts.v1",
        "cell_size_px": list(CELL_SIZE),
        "sheet": sheet_path.name,
        "entries": sheet_entries,
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {len(layouts)} massif layouts to {OUT_DIR}")
    print(f"Wrote sheet {sheet_path}")


if __name__ == "__main__":
    raise SystemExit(main())
