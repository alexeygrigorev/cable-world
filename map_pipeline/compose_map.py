import math
import os
import sys

import geopandas as gpd
from PIL import Image, ImageDraw, ImageFilter
from shapely.geometry import Point, box

from map_pipeline.projection import MapProjection

MAP_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "map")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "natural_earth")

GERMANY_BOUNDS = (4.5, 46.5, 15.5, 55.5)
MAP_SIZE = (1568, 2048)
RENDER_SCALE = 2

OCEAN = "#315f6d"
NEIGHBOR_LAND = "#8f9150"
GERMANY_LAND = "#9da05a"
GERMANY_EDGE = "#463c28"
BORDER = "#5a5037"
LAKE = "#2d7285"
RIVER = "#3b8fa3"
ROUTE = "#d8c17a"
ROUTE_DARK = "#6e5832"


def _scale_size(size):
    return (size[0] * RENDER_SCALE, size[1] * RENDER_SCALE)


def _load_shapefile(name):
    path = os.path.join(DATA_DIR, name)
    shp_files = [f for f in os.listdir(path) if f.endswith(".shp")]
    if not shp_files:
        raise FileNotFoundError(f"No .shp file in {path}")
    return gpd.read_file(os.path.join(path, shp_files[0]))


def _clip_to_bounds(gdf, bounds):
    minx, miny, maxx, maxy = bounds
    clip_box = box(minx - 1.5, miny - 1.5, maxx + 1.5, maxy + 1.5)
    clipped = gdf[gdf.geometry.intersects(clip_box)].copy()
    clipped["geometry"] = clipped.geometry.intersection(clip_box)
    return clipped[~clipped.is_empty]


def _project_point(proj, lon, lat):
    x, y = proj.project(lon, lat)
    return (int(round(x * RENDER_SCALE)), int(round(y * RENDER_SCALE)))


def _polygon_points(poly, proj):
    return [_project_point(proj, lon, lat) for lon, lat in poly.exterior.coords]


def _draw_geometry(draw, geom, proj, fill, outline=None, width=1):
    geoms = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
    for poly in geoms:
        pts = _polygon_points(poly, proj)
        if len(pts) >= 3:
            draw.polygon(pts, fill=fill)
            if outline:
                draw.line(pts + [pts[0]], fill=outline, width=width, joint="curve")


def _draw_country_layer(canvas, proj):
    admin_dataset = "ne_50m_admin_0_countries"
    if not os.path.isdir(os.path.join(DATA_DIR, admin_dataset)):
        admin_dataset = "ne_110m_admin_0_countries"
    countries = _clip_to_bounds(_load_shapefile(admin_dataset), GERMANY_BOUNDS)
    draw = ImageDraw.Draw(canvas)

    for _, row in countries.iterrows():
        if row["ADMIN"] != "Germany":
            _draw_geometry(draw, row.geometry, proj, NEIGHBOR_LAND, BORDER, 2 * RENDER_SCALE)

    germany = countries[countries["ADMIN"] == "Germany"].iloc[0].geometry
    _draw_geometry(draw, germany, proj, GERMANY_LAND, GERMANY_EDGE, 5 * RENDER_SCALE)

    mask = Image.new("L", canvas.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    _draw_geometry(mask_draw, germany, proj, 255)
    return germany, mask


def _draw_ocean_texture(canvas):
    draw = ImageDraw.Draw(canvas)
    width, height = canvas.size
    for y in range(0, height, 34 * RENDER_SCALE):
        for x in range(((y // (34 * RENDER_SCALE)) % 2) * 17 * RENDER_SCALE, width, 68 * RENDER_SCALE):
            draw.arc(
                (
                    x,
                    y,
                    x + 24 * RENDER_SCALE,
                    y + 10 * RENDER_SCALE,
                ),
                190,
                350,
                fill=(99, 153, 158, 82),
                width=max(1, RENDER_SCALE),
            )


def _draw_lakes(canvas, proj, germany_mask):
    lakes = _clip_to_bounds(_load_shapefile("ne_110m_lakes"), GERMANY_BOUNDS)
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for _, row in lakes.iterrows():
        _draw_geometry(draw, row.geometry, proj, LAKE, "#6eabc9", 2 * RENDER_SCALE)
    layer.putalpha(Image.composite(layer.getchannel("A"), Image.new("L", canvas.size, 0), germany_mask))
    canvas.alpha_composite(layer)


def _draw_waterways(canvas, proj, germany_mask):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    rivers = [
        # Rhein
        [(7.9, 47.6), (7.7, 48.2), (7.8, 49.0), (8.3, 49.5), (8.2, 50.0), (7.6, 50.4), (7.1, 50.8), (6.8, 51.2), (6.7, 51.7)],
        # Elbe
        [(14.2, 50.8), (13.7, 51.1), (13.3, 51.5), (12.6, 52.0), (11.7, 52.5), (10.6, 53.1), (9.9, 53.5)],
        # Donau
        [(8.7, 48.0), (9.5, 48.4), (10.4, 48.7), (11.4, 48.8), (12.4, 48.9), (13.3, 48.7)],
        # Main
        [(9.9, 50.0), (9.2, 50.1), (8.7, 50.1), (8.2, 50.0), (7.7, 49.9)],
        # Weser
        [(9.5, 51.2), (9.4, 51.8), (9.2, 52.4), (8.8, 53.0)],
    ]
    for river in rivers:
        pts = [_project_point(proj, lon, lat) for lon, lat in river]
        draw.line(pts, fill=(42, 81, 85, 190), width=7 * RENDER_SCALE, joint="curve")
        draw.line(pts, fill=(76, 139, 142, 230), width=4 * RENDER_SCALE, joint="curve")
        draw.line(pts, fill=(130, 184, 179, 170), width=1 * RENDER_SCALE, joint="curve")

    for lon, lat, rx, ry in [
        (9.35, 47.62, 0.42, 0.14),   # Bodensee edge
        (12.42, 47.86, 0.24, 0.12),  # Chiemsee
        (12.75, 53.43, 0.22, 0.16),  # Mueritz
        (13.78, 52.42, 0.18, 0.11),  # Berlin lakes
    ]:
        x, y = _project_point(proj, lon, lat)
        w = int(rx * 110 * RENDER_SCALE)
        h = int(ry * 110 * RENDER_SCALE)
        draw.ellipse((x - w, y - h, x + w, y + h), fill=(52, 112, 124, 220), outline=(31, 70, 78, 220), width=2 * RENDER_SCALE)
        draw.arc((x - w // 2, y - h // 2, x + w // 2, y + h // 2), 20, 170, fill=(132, 188, 188, 180), width=1 * RENDER_SCALE)

    alpha = Image.composite(layer.getchannel("A"), Image.new("L", canvas.size, 0), germany_mask)
    layer.putalpha(alpha)
    canvas.alpha_composite(layer)


def _soft_region(canvas, mask, points, fill, blur=26):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.polygon(points, fill=fill)
    layer = layer.filter(ImageFilter.GaussianBlur(blur * RENDER_SCALE))
    alpha = Image.composite(layer.getchannel("A"), Image.new("L", canvas.size, 0), mask)
    layer.putalpha(alpha)
    canvas.alpha_composite(layer)


def _draw_terrain(canvas, proj, germany_mask):
    _soft_region(
        canvas,
        germany_mask,
        [_project_point(proj, 7.0, 49.4), _project_point(proj, 9.1, 48.0), _project_point(proj, 8.2, 47.3), _project_point(proj, 6.2, 48.2)],
        (46, 103, 59, 92),
    )
    _soft_region(
        canvas,
        germany_mask,
        [_project_point(proj, 9.8, 48.0), _project_point(proj, 13.6, 47.2), _project_point(proj, 14.9, 48.9), _project_point(proj, 11.4, 49.4)],
        (52, 115, 62, 98),
    )
    _soft_region(
        canvas,
        germany_mask,
        [_project_point(proj, 9.0, 51.9), _project_point(proj, 11.2, 52.2), _project_point(proj, 12.4, 50.6), _project_point(proj, 10.0, 50.0)],
        (70, 123, 64, 78),
    )
    _soft_region(
        canvas,
        germany_mask,
        [_project_point(proj, 5.4, 53.9), _project_point(proj, 14.8, 54.7), _project_point(proj, 14.0, 52.9), _project_point(proj, 6.0, 52.6)],
        (176, 153, 70, 72),
        blur=34,
    )

    decor = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(decor)
    for lon, lat, size in [
        (10.7, 47.7, 96), (11.3, 47.8, 110), (12.2, 47.9, 88),
        (8.2, 48.4, 80), (9.8, 50.4, 70), (10.4, 51.6, 74),
        (13.1, 50.8, 72), (7.4, 51.1, 64), (11.0, 49.0, 62),
        (7.3, 50.6, 28), (8.8, 50.0, 24), (9.6, 52.0, 24),
        (12.3, 52.4, 27), (13.7, 52.0, 25), (8.0, 53.3, 23),
        (11.7, 53.2, 23), (14.1, 53.0, 22), (6.3, 51.4, 24),
        (12.8, 49.5, 26), (7.7, 49.1, 22), (10.0, 48.2, 25),
        (8.0, 49.0, 92), (7.0, 49.7, 76), (9.1, 49.7, 68),
        (10.8, 50.8, 82), (11.8, 51.2, 70), (13.8, 51.8, 78),
        (12.8, 53.1, 72), (10.0, 53.0, 76), (7.9, 52.3, 70),
    ]:
        _draw_tree_cluster(draw, proj, lon, lat, size)
    for lon, lat, size in [
        (10.9, 47.35, 112), (11.7, 47.45, 104), (12.6, 47.55, 86),
        (10.5, 47.75, 70), (12.2, 48.0, 68), (8.1, 48.1, 58),
        (9.3, 48.6, 52), (10.2, 50.2, 48), (13.2, 50.5, 52),
        (7.7, 50.1, 44), (10.6, 51.8, 46), (14.0, 50.8, 44),
    ]:
        _draw_mountains(draw, proj, lon, lat, size)
    for lon, lat, size in [
        (6.9, 50.9, 34), (7.6, 51.2, 30), (8.7, 50.1, 32),
        (9.2, 48.8, 33), (11.6, 48.2, 36), (13.4, 52.5, 38),
        (13.8, 51.1, 34), (10.0, 53.5, 34), (6.8, 51.3, 30),
        (9.7, 52.4, 31), (12.4, 51.3, 31), (8.0, 48.8, 30),
    ]:
        _draw_town(draw, proj, lon, lat, size)

    alpha = Image.composite(decor.getchannel("A"), Image.new("L", canvas.size, 0), germany_mask)
    decor.putalpha(alpha)
    canvas.alpha_composite(decor)


def _stable_hash(*values) -> int:
    text = "|".join(str(value) for value in values)
    total = 2166136261
    for char in text:
        total ^= ord(char)
        total = (total * 16777619) & 0xFFFFFFFF
    return total


def _draw_ground_texture(canvas, proj, germany_mask, germany_geom):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    lon = 4.85
    lon_index = 0
    while lon <= 15.25:
        lat = 46.8
        lat_index = 0
        while lat <= 55.25:
            seed = _stable_hash(lon_index, lat_index)
            jitter_lon = ((seed & 255) / 255.0 - 0.5) * 0.32
            jitter_lat = (((seed >> 8) & 255) / 255.0 - 0.5) * 0.24
            point_lon = lon + jitter_lon
            point_lat = lat + jitter_lat
            if germany_geom.contains(Point(point_lon, point_lat)):
                x, y = _project_point(proj, point_lon, point_lat)
                kind = seed % 9
                scale = RENDER_SCALE
                if kind in (0, 1, 2):
                    color = (76, 112, 62, 80) if point_lat < 52.0 else (91, 111, 66, 64)
                    _draw_tuft(draw, x, y, 8 + seed % 9, color)
                elif kind in (3, 4):
                    _draw_field_hatch(draw, x, y, 24 + seed % 12, (150, 143, 78, 54))
                elif kind == 5 and point_lat < 51.8:
                    _draw_hill_mark(draw, x, y, 16 + seed % 12, (113, 100, 73, 70))
                elif kind == 6:
                    rr = (2 + seed % 3) * scale
                    draw.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(70, 103, 77, 58))
                else:
                    length = (9 + seed % 10) * scale
                    draw.line((x - length // 2, y, x + length // 2, y + scale), fill=(101, 118, 68, 42), width=max(1, scale))
            lat += 0.42
            lat_index += 1
        lon += 0.48
        lon_index += 1

    alpha = Image.composite(layer.getchannel("A"), Image.new("L", canvas.size, 0), germany_mask)
    layer.putalpha(alpha)
    canvas.alpha_composite(layer)


def _draw_tuft(draw, x, y, size, color):
    s = size * RENDER_SCALE
    draw.line((x, y, x - s // 2, y + s // 2), fill=color, width=max(1, RENDER_SCALE))
    draw.line((x, y, x, y + s // 2), fill=color, width=max(1, RENDER_SCALE))
    draw.line((x, y, x + s // 2, y + s // 2), fill=color, width=max(1, RENDER_SCALE))


def _draw_field_hatch(draw, x, y, size, color):
    s = size * RENDER_SCALE
    for offset in range(-2, 3):
        yy = y + offset * s // 5
        draw.line((x - s // 2, yy, x + s // 2, yy + s // 5), fill=color, width=max(1, RENDER_SCALE))


def _draw_hill_mark(draw, x, y, size, color):
    s = size * RENDER_SCALE
    draw.arc((x - s, y - s // 2, x + s, y + s // 2), 200, 340, fill=color, width=max(1, RENDER_SCALE * 2))


def _draw_tree_cluster(draw, proj, lon, lat, radius):
    x, y = _project_point(proj, lon, lat)
    r = radius * RENDER_SCALE
    draw.ellipse((x - r, y + r * 0.20, x + r, y + r * 0.62), fill=(104, 125, 62, 42))
    colors = ["#47733f", "#5f944e", "#86ad58", "#386b48"]
    for i in range(18):
        angle = i * 2.399
        dist = (0.18 + (i % 5) * 0.14) * r
        cx = x + int(math.cos(angle) * dist)
        cy = y + int(math.sin(angle) * dist * 0.65)
        rr = int(r * (0.16 + (i % 3) * 0.025))
        draw.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=colors[i % len(colors)])


def _draw_mountains(draw, proj, lon, lat, size):
    x, y = _project_point(proj, lon, lat)
    s = size * RENDER_SCALE
    draw.ellipse((x - s, y + s * 0.48, x + s, y + s * 0.92), fill=(117, 103, 75, 45))
    for offset, scale in [(-0.45, 0.9), (0.0, 1.15), (0.46, 0.82)]:
        cx = x + int(offset * s)
        h = int(s * scale)
        base = int(s * 0.55 * scale)
        pts = [(cx - base, y + int(s * 0.64)), (cx, y - h // 2), (cx + base, y + int(s * 0.64))]
        draw.polygon(pts, fill="#766e5a")
        draw.polygon([(cx, y - h // 2), (cx - base // 3, y + int(s * 0.18)), (cx + base // 7, y + int(s * 0.28))], fill="#f2f0e7")
        draw.line(pts + [pts[0]], fill="#5a5143", width=max(2, s // 35))


def _draw_town(draw, proj, lon, lat, size):
    x, y = _project_point(proj, lon, lat)
    s = size * RENDER_SCALE
    draw.ellipse((x - s, y + s * 0.45, x + s, y + s * 0.82), fill=(64, 56, 38, 48))
    for i, offset in enumerate([-0.55, -0.18, 0.20, 0.55]):
        bx = x + int(offset * s)
        by = y + int((0.04 if i % 2 == 0 else -0.10) * s)
        w = int(s * 0.36)
        h = int(s * (0.42 if i % 2 == 0 else 0.52))
        draw.rectangle((bx - w // 2, by - h // 2, bx + w // 2, by + h // 2), fill="#b98b55", outline="#4b3825", width=max(1, RENDER_SCALE))
        roof = [(bx - w // 2 - 3 * RENDER_SCALE, by - h // 2), (bx, by - h // 2 - int(s * 0.24)), (bx + w // 2 + 3 * RENDER_SCALE, by - h // 2)]
        draw.polygon(roof, fill="#7e3e31")


def _draw_map_labels(canvas, proj, germany_mask):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for name, lon, lat in [
        ("Hamburg", 9.9937, 53.5511),
        ("Berlin", 13.4050, 52.5200),
        ("Koeln", 6.9603, 50.9375),
        ("Frankfurt", 8.6821, 50.1109),
        ("Stuttgart", 9.1829, 48.7758),
        ("Muenchen", 11.5820, 48.1351),
        ("Dresden", 13.7373, 51.0504),
        ("Harz", 10.5600, 51.8000),
        ("Zugspitze", 10.9900, 47.4300),
    ]:
        x, y = _project_point(proj, lon, lat)
        dot = 4 * RENDER_SCALE
        draw.ellipse((x - dot, y - dot, x + dot, y + dot), fill=(44, 34, 24, 210))
        text_pos = (x + 8 * RENDER_SCALE, y - 10 * RENDER_SCALE)
        draw.text((text_pos[0] + RENDER_SCALE, text_pos[1] + RENDER_SCALE), name, fill=(42, 31, 22, 180))
        draw.text(text_pos, name, fill=(244, 225, 165, 230))
    alpha = Image.composite(layer.getchannel("A"), Image.new("L", canvas.size, 0), germany_mask)
    layer.putalpha(alpha)
    canvas.alpha_composite(layer)


def _bezier(p0, p1, p2, p3, steps=80):
    points = []
    for i in range(steps + 1):
        t = i / steps
        mt = 1 - t
        x = mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
        y = mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
        points.append((int(x), int(y)))
    return points


def _draw_routes(canvas, proj, germany_mask):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    routes = [
        ((6.8, 51.2), (7.7, 51.7), (9.2, 51.6), (11.0, 51.8)),
        ((11.0, 51.8), (12.1, 52.0), (13.0, 52.3), (13.6, 52.5)),
        ((6.9, 50.9), (7.4, 50.0), (8.2, 49.5), (9.2, 48.8)),
        ((9.2, 48.8), (9.9, 48.1), (10.4, 47.7), (11.1, 47.5)),
        ((8.2, 50.1), (9.3, 50.4), (11.0, 50.7), (13.8, 51.1)),
        ((10.6, 51.8), (10.4, 50.8), (10.8, 49.4), (11.5, 48.1)),
    ]
    for route in routes:
        p0, p1, p2, p3 = [_project_point(proj, lon, lat) for lon, lat in route]
        pts = _bezier(p0, p1, p2, p3)
        draw.line(pts, fill=(255, 239, 166, 214), width=9 * RENDER_SCALE, joint="curve")
        draw.line(pts, fill=ROUTE_DARK, width=2 * RENDER_SCALE, joint="curve")
        for p in pts[::16]:
            rr = 2 * RENDER_SCALE
            draw.ellipse((p[0] - rr, p[1] - rr, p[0] + rr, p[1] + rr), fill="#f2df98")
    alpha = Image.composite(layer.getchannel("A"), Image.new("L", canvas.size, 0), germany_mask)
    layer.putalpha(alpha)
    canvas.alpha_composite(layer)


def main():
    os.makedirs(MAP_DIR, exist_ok=True)
    render_size = _scale_size(MAP_SIZE)
    proj = MapProjection(GERMANY_BOUNDS, MAP_SIZE)

    canvas = Image.new("RGBA", render_size, OCEAN)
    _draw_ocean_texture(canvas)
    print("Step 1: Draw countries and Germany mask")
    germany, germany_mask = _draw_country_layer(canvas, proj)

    print("Step 2: Add terrain, texture, lakes, and routes")
    _draw_terrain(canvas, proj, germany_mask)
    _draw_ground_texture(canvas, proj, germany_mask, germany)
    _draw_lakes(canvas, proj, germany_mask)
    _draw_waterways(canvas, proj, germany_mask)
    _draw_routes(canvas, proj, germany_mask)
    _draw_map_labels(canvas, proj, germany_mask)

    print("Step 3: Finish clean interactive map underlay")

    canvas = _pixel_finish(canvas)
    out_path = os.path.join(MAP_DIR, "germany_styled.png")
    canvas.save(out_path, "PNG", optimize=True)
    file_size = os.path.getsize(out_path)
    print(f"Output: {out_path}")
    print(f"Size: {canvas.size[0]}x{canvas.size[1]}, {file_size:,} bytes")
    return 0


def _pixel_finish(canvas: Image.Image) -> Image.Image:
    small_size = (MAP_SIZE[0] // 2, MAP_SIZE[1] // 2)
    pixel = canvas.resize(small_size, Image.Resampling.BILINEAR).convert("RGB")
    pixel = pixel.quantize(colors=48, method=Image.Quantize.MEDIANCUT).convert("RGB")
    return pixel.resize(MAP_SIZE, Image.Resampling.NEAREST)


if __name__ == "__main__":
    sys.exit(main())
