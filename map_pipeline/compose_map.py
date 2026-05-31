import math
import os
import sys

import geopandas as gpd
from PIL import Image, ImageDraw, ImageFilter
from shapely.geometry import Point, box

from map_pipeline.projection import MapProjection

MAP_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "map")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "natural_earth")
GLYPH_DIR = os.path.join(MAP_DIR, "glyphs")

GERMANY_BOUNDS = (4.5, 43.2, 16.8, 55.8)
# Match the Mercator aspect of GERMANY_BOUNDS and keep enough physical pixels
# that the runtime 150% zoom does not upscale the map texture above source size.
MAP_SIZE = (1932, 3072)
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
FOREST_SPRITE_CACHE = {}
GLYPH_CACHE = {}

# Runtime city landmarks are the only city/object layer. Keep the generated
# underlay free of baked villages or city-like pictograms so it can scale to
# Europe without fighting runtime overlays.
BAKED_TOWN_DETAILS_ENABLED = False
BAKED_TOWN_DETAILS = []

RELIEF_REGIONS = [
    {
        "id": "black_forest",
        "label": "Black Forest",
        "kind": "forested_highland",
        "glyph": "forested_highland",
        "fill": (45, 101, 58, 92),
        "blur": 24,
        "points": [(7.45, 49.2), (8.25, 48.9), (8.55, 47.75), (7.65, 47.45), (6.95, 48.25)],
        "trees": [(8.0, 49.0, 82), (8.15, 48.45, 76), (7.8, 47.95, 70)],
        "mountain_glyphs": [("highland_forest_2", 8.00, 48.18, 150)],
        "mountains": [],
    },
    {
        "id": "alps",
        "label": "Alps",
        "kind": "cross_border_mountain",
        "glyph": "alpine",
        "fill": (58, 112, 63, 112),
        "blur": 20,
        "extends_to": ["France", "Switzerland", "Italy", "Austria", "Slovenia"],
        "points": [(9.45, 47.85), (10.5, 47.1), (12.1, 46.95), (13.35, 47.25), (13.9, 48.0), (11.5, 48.35)],
        "trees": [(10.0, 48.2, 44), (11.0, 48.05, 50), (12.35, 48.0, 46)],
        "mountain_glyphs": [
            ("alps_range_1", 10.05, 47.45, 210),
            ("alps_range_3", 11.20, 47.33, 265),
            ("alps_range_2", 12.38, 47.43, 220),
            ("alps_peak_2", 13.15, 47.62, 120),
        ],
        "mountains": [],
    },
    {
        "id": "bavarian_forest",
        "label": "Bavarian Forest",
        "kind": "forested_highland",
        "glyph": "forested_highland",
        "fill": (49, 105, 60, 80),
        "blur": 22,
        "extends_to": ["Czechia", "Austria"],
        "points": [(11.8, 49.35), (12.55, 48.8), (13.7, 48.8), (13.85, 49.35), (12.7, 49.85)],
        "trees": [(12.8, 49.35, 72), (13.2, 49.05, 62)],
        "mountain_glyphs": [("highland_forest_3", 12.95, 49.20, 150)],
        "mountains": [],
    },
    {
        "id": "harz",
        "label": "Harz",
        "kind": "isolated_mountain_range",
        "glyph": "forested_highland",
        "fill": (73, 125, 66, 64),
        "blur": 20,
        "points": [(10.0, 52.05), (10.85, 52.15), (11.35, 51.65), (10.75, 51.35), (9.9, 51.55)],
        "trees": [(10.55, 51.75, 58)],
        "mountain_glyphs": [("highland_forest_1", 10.62, 51.78, 118)],
        "mountains": [],
    },
    {
        "id": "erzgebirge",
        "label": "Erzgebirge",
        "kind": "border_mountain_range",
        "glyph": "border_highland",
        "fill": (64, 116, 63, 74),
        "blur": 18,
        "extends_to": ["Czechia"],
        "points": [(12.3, 50.95), (13.15, 50.45), (14.65, 50.45), (14.9, 50.85), (13.55, 51.15)],
        "trees": [(13.75, 50.85, 62)],
        "mountain_glyphs": [("border_highland_1", 13.10, 50.66, 145), ("border_highland_2", 14.05, 50.75, 125)],
        "mountains": [],
    },
    {
        "id": "saxon_switzerland",
        "label": "Saxon Switzerland / Elbe Sandstone",
        "kind": "sandstone_highland",
        "glyph": "border_highland",
        "fill": (76, 118, 70, 64),
        "blur": 14,
        "extends_to": ["Czechia"],
        "points": [(13.65, 51.05), (14.05, 50.82), (14.45, 50.78), (14.75, 50.98), (14.35, 51.18), (13.85, 51.22)],
        "trees": [(14.18, 50.96, 42)],
        "mountain_glyphs": [("border_highland_2", 14.18, 50.95, 108)],
        "mountains": [],
    },
    {
        "id": "eifel_hunsrueck",
        "label": "Eifel Hunsrueck",
        "kind": "low_highland",
        "glyph": "low_highland",
        "fill": (61, 112, 60, 58),
        "blur": 24,
        "extends_to": ["Belgium", "Luxembourg"],
        "points": [(5.9, 50.8), (7.7, 50.55), (7.75, 49.65), (6.25, 49.45), (5.55, 50.1)],
        "trees": [(7.05, 49.75, 64), (7.35, 50.45, 48)],
        "mountains": [],
    },
    {
        "id": "northern_lowlands",
        "label": "North German Plain",
        "kind": "lowland",
        "glyph": "lowland",
        "fill": (178, 154, 75, 64),
        "blur": 36,
        "points": [(5.4, 54.6), (14.9, 54.85), (14.4, 52.65), (5.8, 52.65)],
        "trees": [(8.0, 53.25, 34), (10.0, 53.05, 36), (11.7, 53.2, 32), (12.8, 53.1, 30)],
        "mountains": [],
    },
]

ATLAS_DETAILS = [
    {"id": "north_sea_sail", "kind": "ship", "glyph": "detail_ship", "lon": 7.85, "lat": 54.28, "width": 52, "region": "north_sea"},
    {"id": "kiel_ferry", "kind": "ship", "glyph": "detail_ship", "lon": 10.28, "lat": 54.42, "width": 46, "region": "baltic_sea"},
    {"id": "rostock_ferry", "kind": "ship", "glyph": "detail_ship", "lon": 12.25, "lat": 54.22, "width": 46, "region": "baltic_sea"},
    {"id": "ruegen_sail", "kind": "ship", "glyph": "detail_ship", "lon": 13.70, "lat": 54.57, "width": 38, "region": "baltic_sea"},
    {"id": "hamburg_port", "kind": "port", "glyph": "detail_port", "lon": 9.90, "lat": 53.48, "width": 54, "region": "lower_elbe"},
    {"id": "luebeck_port", "kind": "port", "glyph": "detail_port", "lon": 10.82, "lat": 53.95, "width": 42, "region": "baltic_sea"},
    {"id": "bremerhaven_port", "kind": "port", "glyph": "detail_port", "lon": 8.58, "lat": 53.55, "width": 42, "region": "north_sea"},
    {"id": "rhein_bridge", "kind": "bridge", "glyph": "detail_bridge", "lon": 6.96, "lat": 50.94, "width": 48, "region": "rhein"},
    {"id": "main_bridge_wuerzburg", "kind": "bridge", "glyph": "detail_bridge", "lon": 9.93, "lat": 49.79, "width": 38, "region": "main"},
    {"id": "dresden_elbe_bridge", "kind": "bridge", "glyph": "detail_bridge", "lon": 13.74, "lat": 51.05, "width": 42, "region": "elbe"},
    {"id": "heidelberg_castle", "kind": "castle", "glyph": "detail_castle", "lon": 8.7150, "lat": 49.4106, "width": 44, "region": "neckar"},
    {"id": "wartburg_castle", "kind": "castle", "glyph": "detail_castle", "lon": 10.3067, "lat": 50.9669, "width": 40, "region": "thuringian_forest"},
    {"id": "hohenzollern_castle", "kind": "castle", "glyph": "detail_castle", "lon": 8.9678, "lat": 48.3232, "width": 38, "region": "swabian_alb"},
    {"id": "neuschwanstein_castle", "kind": "castle", "glyph": "detail_castle", "lon": 10.7498, "lat": 47.5576, "width": 42, "region": "alps"},
    {"id": "schwerin_castle", "kind": "castle", "glyph": "detail_castle", "lon": 11.4175, "lat": 53.6244, "width": 40, "region": "north_german_plain"},
    {"id": "harz_tower", "kind": "tower", "glyph": "detail_tower", "lon": 10.62, "lat": 51.80, "width": 34, "region": "harz"},
    {"id": "helgoland_lighthouse", "kind": "lighthouse", "glyph": "detail_lighthouse", "lon": 7.89, "lat": 54.18, "width": 34, "region": "north_sea"},
    {"id": "ruegen_lighthouse", "kind": "lighthouse", "glyph": "detail_lighthouse", "lon": 13.66, "lat": 54.68, "width": 34, "region": "ruegen"},
    {"id": "frisian_windmill", "kind": "windmill", "glyph": "detail_windmill", "lon": 7.55, "lat": 53.58, "width": 32, "region": "frisia"},
    {"id": "altmark_windmill", "kind": "windmill", "glyph": "detail_windmill", "lon": 11.55, "lat": 52.86, "width": 32, "region": "altmark"},
    {"id": "spreewald_watermill", "kind": "watermill", "glyph": "detail_watermill", "lon": 14.06, "lat": 51.87, "width": 34, "region": "spreewald"},
    {"id": "black_forest_watermill", "kind": "watermill", "glyph": "detail_watermill", "lon": 8.22, "lat": 48.24, "width": 34, "region": "black_forest"},
    {"id": "teutoburg_chapel", "kind": "chapel", "glyph": "detail_chapel", "lon": 8.88, "lat": 52.02, "width": 32, "region": "teutoburg"},
    {"id": "harz_chapel", "kind": "chapel", "glyph": "detail_chapel", "lon": 10.93, "lat": 51.61, "width": 30, "region": "harz"},
    {"id": "thuringian_ruins", "kind": "ruins", "glyph": "detail_ruins", "lon": 11.12, "lat": 50.63, "width": 32, "region": "thuringian_forest"},
    {"id": "rhine_ruins", "kind": "ruins", "glyph": "detail_ruins", "lon": 7.69, "lat": 50.17, "width": 32, "region": "middle_rhine"},
    {"id": "mosel_village", "kind": "village", "glyph": "detail_village", "lon": 7.17, "lat": 49.96, "width": 34, "region": "mosel"},
    {"id": "luneburg_village", "kind": "village", "glyph": "detail_village", "lon": 10.42, "lat": 53.05, "width": 34, "region": "lueneburg_heath"},
    {"id": "mueritz_village", "kind": "village", "glyph": "detail_village", "lon": 12.64, "lat": 53.33, "width": 32, "region": "mecklenburg_lakes"},
    {"id": "swabian_village", "kind": "village", "glyph": "detail_village", "lon": 9.45, "lat": 48.42, "width": 32, "region": "swabian_alb"},
    {"id": "franconian_village", "kind": "village", "glyph": "detail_village", "lon": 11.26, "lat": 49.78, "width": 32, "region": "franconia"},
    {"id": "oberlausitz_village", "kind": "village", "glyph": "detail_village", "lon": 14.64, "lat": 51.15, "width": 32, "region": "oberlausitz"},
    {"id": "holstein_chapel", "kind": "chapel", "glyph": "detail_chapel", "lon": 10.20, "lat": 54.02, "width": 30, "region": "holstein"},
    {"id": "lower_saxony_village", "kind": "village", "glyph": "detail_village", "lon": 9.42, "lat": 52.78, "width": 32, "region": "lower_saxony"},
    {"id": "weser_watermill", "kind": "watermill", "glyph": "detail_watermill", "lon": 9.36, "lat": 51.76, "width": 32, "region": "weser_uplands"},
    {"id": "sauerland_village", "kind": "village", "glyph": "detail_village", "lon": 8.05, "lat": 51.18, "width": 32, "region": "sauerland"},
    {"id": "eifel_chapel", "kind": "chapel", "glyph": "detail_chapel", "lon": 6.72, "lat": 50.28, "width": 30, "region": "eifel"},
    {"id": "palatinate_ruins", "kind": "ruins", "glyph": "detail_ruins", "lon": 8.05, "lat": 49.22, "width": 32, "region": "palatinate"},
    {"id": "odenwald_village", "kind": "village", "glyph": "detail_village", "lon": 8.82, "lat": 49.67, "width": 32, "region": "odenwald"},
    {"id": "rhoen_chapel", "kind": "chapel", "glyph": "detail_chapel", "lon": 10.00, "lat": 50.50, "width": 30, "region": "rhoen"},
    {"id": "spessart_village", "kind": "village", "glyph": "detail_village", "lon": 9.42, "lat": 50.08, "width": 32, "region": "spessart"},
    {"id": "altmuehl_watermill", "kind": "watermill", "glyph": "detail_watermill", "lon": 11.05, "lat": 48.96, "width": 32, "region": "altmuehl"},
    {"id": "bavarian_village", "kind": "village", "glyph": "detail_village", "lon": 12.10, "lat": 48.44, "width": 34, "region": "bavaria"},
    {"id": "lausitz_windmill", "kind": "windmill", "glyph": "detail_windmill", "lon": 14.33, "lat": 51.72, "width": 32, "region": "lausitz"},
]

ATLAS_DETAIL_KIND_SCALE = {
    "bridge": 1.15,
    "castle": 1.25,
    "chapel": 1.55,
    "lighthouse": 1.45,
    "port": 1.15,
    "ruins": 1.55,
    "ship": 1.18,
    "tower": 1.45,
    "village": 1.60,
    "watermill": 1.55,
    "windmill": 1.55,
}


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
            if fill is not None:
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

    land_mask = Image.new("L", canvas.size, 0)
    land_mask_draw = ImageDraw.Draw(land_mask)
    for _, row in countries.iterrows():
        _draw_geometry(land_mask_draw, row.geometry, proj, 255)
    return germany, mask, land_mask


def _draw_country_border_overlay(canvas, proj, germany_geom):
    draw = ImageDraw.Draw(canvas)
    _draw_geometry(draw, germany_geom, proj, None, (230, 201, 119, 150), 7 * RENDER_SCALE)
    _draw_geometry(draw, germany_geom, proj, None, GERMANY_EDGE, 4 * RENDER_SCALE)
    _draw_geometry(draw, germany_geom, proj, None, (49, 39, 25, 230), 2 * RENDER_SCALE)


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

    for glyph, lon, lat, width in [
        ("lake_long_1", 9.35, 47.62, 110),   # Bodensee edge
        ("lake_small_1", 12.42, 47.86, 70),  # Chiemsee
        ("lake_large_1", 12.75, 53.43, 86),  # Mueritz
        ("lake_small_3", 13.78, 52.42, 58),  # Berlin lakes
        ("lake_small_2", 11.43, 53.63, 72),  # Schweriner See
        ("lake_small_4", 12.27, 53.46, 62),  # Plauer See
        ("lake_small_3", 10.98, 53.58, 48),  # Schaalsee
        ("lake_small_1", 9.35, 52.47, 54),   # Steinhuder Meer
        ("lake_small_4", 9.00, 51.18, 48),   # Edersee
        ("lake_small_2", 11.10, 47.98, 48),  # Ammersee
        ("lake_small_3", 11.34, 47.91, 46),  # Starnberger See
        ("lake_small_4", 11.73, 47.72, 40),  # Tegernsee
    ]:
        _draw_glyph_center(layer, proj, glyph, lon, lat, width)

    canvas.alpha_composite(layer)


def _soft_region(canvas, mask, points, fill, blur=26):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.polygon(points, fill=fill)
    layer = layer.filter(ImageFilter.GaussianBlur(blur * RENDER_SCALE))
    if mask is not None:
        alpha = Image.composite(layer.getchannel("A"), Image.new("L", canvas.size, 0), mask)
        layer.putalpha(alpha)
    canvas.alpha_composite(layer)


def _draw_terrain(canvas, proj, land_mask):
    for region in RELIEF_REGIONS:
        _soft_region(
            canvas,
            land_mask,
            [_project_point(proj, lon, lat) for lon, lat in region["points"]],
            region["fill"],
            blur=region["blur"],
        )

    decor = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(decor)
    for region in RELIEF_REGIONS:
        for lon, lat, size in region.get("trees", []):
            _draw_tree_cluster(decor, proj, lon, lat, size)
        for glyph_name, lon, lat, width in region.get("mountain_glyphs", []):
            _draw_glyph_center(decor, proj, glyph_name, lon, lat, width)
        for lon, lat, size in region.get("mountains", []):
            _draw_mountains(decor, draw, proj, lon, lat, size, region.get("glyph", "alpine"))
    for lon, lat, size in [
        (9.8, 50.4, 38), (11.0, 49.0, 38), (6.3, 51.4, 28),
        (8.8, 50.0, 28), (9.6, 52.0, 24), (12.3, 52.4, 24),
        (13.7, 52.0, 23), (14.1, 53.0, 20), (10.1, 53.2, 44),
        (13.9, 52.2, 42), (11.1, 50.8, 46), (9.2, 51.0, 40),
        (7.6, 50.2, 36), (10.4, 48.0, 40), (12.2, 49.2, 38),
        (7.6, 53.2, 34), (8.4, 52.2, 34), (9.2, 52.8, 30),
        (10.9, 53.4, 32), (12.1, 53.9, 30), (13.0, 53.6, 32),
        (13.8, 51.3, 30), (12.8, 51.1, 28), (11.7, 51.2, 30),
        (10.2, 50.6, 34), (8.6, 50.7, 30), (7.1, 49.5, 32),
        (8.2, 48.8, 32), (9.7, 48.6, 34), (11.7, 48.6, 32),
        (12.8, 48.3, 34), (13.4, 49.5, 36), (14.4, 50.4, 30),
    ]:
        _draw_tree_cluster(decor, proj, lon, lat, size)
    if BAKED_TOWN_DETAILS_ENABLED:
        for lon, lat, size in BAKED_TOWN_DETAILS:
            _draw_town(draw, proj, lon, lat, size)
    for lon, lat, width, height in [
        (7.6, 52.2, 58, 34), (8.7, 51.2, 72, 38), (9.4, 50.7, 62, 32),
        (11.9, 51.6, 70, 36), (12.8, 52.6, 58, 30), (8.6, 49.6, 66, 34),
        (10.8, 48.6, 56, 30), (13.2, 51.35, 54, 30),
        (6.9, 52.7, 58, 28), (9.9, 52.9, 60, 28), (11.2, 52.7, 52, 26),
        (12.2, 50.1, 48, 24), (7.4, 48.3, 44, 24), (10.0, 49.6, 50, 24),
        (7.9, 53.0, 54, 24), (8.9, 52.4, 52, 24), (11.6, 53.2, 52, 24),
        (12.9, 52.9, 48, 22), (13.8, 51.7, 48, 22), (8.4, 50.7, 50, 22),
        (9.2, 48.9, 48, 22), (11.8, 49.5, 48, 22), (12.7, 48.1, 44, 22),
    ]:
        _draw_field_patch(draw, proj, lon, lat, width, height)
    for lon, lat, size in [
        (8.7, 53.4, 38), (11.6, 53.8, 34), (13.0, 54.0, 30),
        (12.3, 53.3, 34), (9.8, 54.1, 28), (14.1, 52.0, 30),
        (13.8, 51.85, 28),
    ]:
        _draw_marsh_patch(draw, proj, lon, lat, size)

    canvas.alpha_composite(decor)


def _draw_atlas_details(canvas, proj):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    for detail in ATLAS_DETAILS:
        kind_scale = ATLAS_DETAIL_KIND_SCALE.get(detail["kind"], 1.0)
        _draw_glyph_center(
            layer,
            proj,
            detail["glyph"],
            detail["lon"],
            detail["lat"],
            detail["width"] * kind_scale,
        )
    canvas.alpha_composite(layer)


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
            lat += 0.34
            lat_index += 1
        lon += 0.38
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


def _draw_field_patch(draw, proj, lon, lat, width, height):
    x, y = _project_point(proj, lon, lat)
    w = width * RENDER_SCALE
    h = height * RENDER_SCALE
    fill = (158, 149, 82, 48)
    outline = (92, 104, 59, 62)
    polygon = [
        (x - w // 2, y - h // 3),
        (x + w // 2, y - h // 2),
        (x + w // 2, y + h // 3),
        (x - w // 3, y + h // 2),
    ]
    draw.polygon(polygon, fill=fill)
    draw.line(polygon + [polygon[0]], fill=outline, width=max(1, RENDER_SCALE))
    for step in range(-2, 3):
        yy = y + step * h // 6
        draw.line((x - w // 3, yy, x + w // 3, yy + h // 8), fill=(202, 183, 111, 58), width=max(1, RENDER_SCALE))


def _draw_marsh_patch(draw, proj, lon, lat, size):
    x, y = _project_point(proj, lon, lat)
    s = size * RENDER_SCALE
    draw.ellipse((x - s, y - s // 3, x + s, y + s // 3), fill=(75, 128, 105, 34))
    for index in range(7):
        offset = (index - 3) * s // 5
        draw.arc((x + offset - s // 5, y - s // 5, x + offset + s // 5, y + s // 5), 210, 340, fill=(57, 101, 85, 72), width=max(1, RENDER_SCALE))


def _draw_castle_marker(draw, proj, lon, lat, size):
    x, y = _project_point(proj, lon, lat)
    s = size * RENDER_SCALE
    draw.ellipse((x - s * 0.72, y + s * 0.34, x + s * 0.72, y + s * 0.62), fill=(66, 52, 34, 50))
    wall = (181, 137, 82)
    outline = (68, 48, 31)
    roof = (117, 56, 43)
    body = (x - s * 0.42, y - s * 0.08, x + s * 0.42, y + s * 0.42)
    draw.rectangle(body, fill=wall, outline=outline, width=max(1, RENDER_SCALE))
    for offset in [-0.48, 0.48]:
        cx = x + int(offset * s)
        tower = (cx - s * 0.16, y - s * 0.28, cx + s * 0.16, y + s * 0.42)
        draw.rectangle(tower, fill=wall, outline=outline, width=max(1, RENDER_SCALE))
        draw.polygon(
            [(cx - s * 0.22, y - s * 0.28), (cx, y - s * 0.55), (cx + s * 0.22, y - s * 0.28)],
            fill=roof,
        )
    draw.polygon([(x - s * 0.48, y - s * 0.08), (x, y - s * 0.38), (x + s * 0.48, y - s * 0.08)], fill=roof)
    draw.line((x - s * 0.48, y - s * 0.08, x, y - s * 0.38, x + s * 0.48, y - s * 0.08), fill=outline, width=max(1, RENDER_SCALE))


def _draw_hill_mark(draw, x, y, size, color):
    s = size * RENDER_SCALE
    draw.arc((x - s, y - s // 2, x + s, y + s // 2), 200, 340, fill=color, width=max(1, RENDER_SCALE * 2))


def _load_glyph(name):
    if name not in GLYPH_CACHE:
        path = os.path.join(GLYPH_DIR, f"{name}.png")
        GLYPH_CACHE[name] = Image.open(path).convert("RGBA") if os.path.exists(path) else None
    return GLYPH_CACHE[name]


def _draw_glyph_center(canvas, proj, glyph_name, lon, lat, target_width):
    x, y = _project_point(proj, lon, lat)
    return _draw_glyph_at(canvas, glyph_name, x, y, target_width)


def _draw_glyph_at(canvas, glyph_name, x, y, target_width):
    if canvas is None:
        return False
    glyph = _load_glyph(glyph_name)
    if glyph is None:
        return False
    width = max(1, int(target_width * RENDER_SCALE))
    height = max(1, int(width * glyph.height / glyph.width))
    resized = glyph.resize((width, height), Image.Resampling.LANCZOS)
    canvas.alpha_composite(resized, (int(x - width * 0.5), int(y - height * 0.62)))
    return True


def _draw_tree_cluster(canvas, proj, lon, lat, radius):
    x, y = _project_point(proj, lon, lat)
    glyphs = ["forest_cluster_1", "forest_cluster_2", "forest_cluster_3", "forest_cluster_4", "forest_cluster_5", "forest_cluster_6"]
    glyph = glyphs[_stable_hash(round(lon, 2), round(lat, 2), int(radius)) % len(glyphs)]
    _draw_glyph_at(canvas, glyph, x, y, radius * 2.0)


def _forest_sprite(radius):
    key = int(radius)
    if key in FOREST_SPRITE_CACHE:
        return FOREST_SPRITE_CACHE[key]

    r = radius * RENDER_SCALE
    width = int(r * 2.2)
    height = int(r * 1.55)
    sprite = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(sprite)
    cx = width // 2
    cy = int(height * 0.46)
    draw.ellipse((cx - r, cy + r * 0.20, cx + r, cy + r * 0.62), fill=(73, 86, 48, 48))
    colors = [(55, 103, 72, 235), (72, 122, 65, 232), (97, 143, 76, 224), (48, 91, 71, 230)]
    for i in range(22):
        angle = i * 2.399
        dist = (0.12 + (i % 6) * 0.12) * r
        tx = cx + int(math.cos(angle) * dist)
        ty = cy + int(math.sin(angle) * dist * 0.58)
        size = int(r * (0.15 + (i % 4) * 0.025))
        _draw_tree_glyph(draw, tx, ty, size, colors[i % len(colors)])
    FOREST_SPRITE_CACHE[key] = sprite
    return sprite


def _draw_tree_glyph(draw, x, y, size, color):
    trunk = (80, 57, 33, 190)
    outline = (41, 64, 45, 150)
    draw.rectangle((x - max(1, size // 8), y, x + max(1, size // 8), y + size // 2), fill=trunk)
    draw.ellipse((x - size, y - size, x + size, y + size // 2), fill=outline)
    inner = max(1, int(size * 0.82))
    draw.ellipse((x - inner, y - inner, x + inner, y + inner // 2), fill=color)


def _draw_mountains(canvas, draw, proj, lon, lat, size, glyph="alpine"):
    target_width = size * (3.15 if glyph == "alpine" else 2.75)
    if glyph == "alpine":
        sprite = ["alps_range_1", "alps_range_2", "alps_range_3"][_stable_hash(lon, lat, size) % 3]
    elif glyph == "border_highland":
        sprite = ["border_highland_1", "border_highland_2"][_stable_hash(lon, lat, size) % 2]
    else:
        sprite = ["highland_forest_1", "highland_forest_2", "highland_forest_3"][_stable_hash(lon, lat, size) % 3]
    if _draw_glyph_center(canvas, proj, sprite, lon, lat, target_width):
        return
    x, y = _project_point(proj, lon, lat)
    s = size * RENDER_SCALE
    if glyph == "alpine":
        _draw_alpine_mountains(draw, x, y, s)
    elif glyph == "border_highland":
        _draw_border_highland(draw, x, y, s)
    else:
        _draw_forested_highland(draw, x, y, s)


def _draw_alpine_mountains(draw, x, y, s):
    draw.ellipse((x - s, y + s * 0.48, x + s, y + s * 0.92), fill=(117, 103, 75, 45))
    for offset, scale in [(-0.54, 0.88), (-0.15, 1.08), (0.28, 1.22), (0.62, 0.78)]:
        cx = x + int(offset * s)
        h = int(s * scale)
        base = int(s * 0.50 * scale)
        pts = [(cx - base, y + int(s * 0.66)), (cx, y - h // 2), (cx + base, y + int(s * 0.66))]
        draw.polygon(pts, fill="#746b57")
        draw.polygon([(cx, y - h // 2), (cx - base // 3, y + int(s * 0.12)), (cx + base // 8, y + int(s * 0.26))], fill="#f3f0df")
        draw.line(pts + [pts[0]], fill="#514939", width=max(2, s // 36))


def _draw_forested_highland(draw, x, y, s):
    draw.ellipse((x - s, y + s * 0.32, x + s, y + s * 0.80), fill=(70, 92, 55, 54))
    for offset, scale in [(-0.45, 0.70), (0.05, 0.86), (0.48, 0.62)]:
        cx = x + int(offset * s)
        h = int(s * scale)
        base = int(s * 0.60 * scale)
        pts = [(cx - base, y + int(s * 0.54)), (cx, y - h // 3), (cx + base, y + int(s * 0.54))]
        draw.polygon(pts, fill="#6c7353")
        draw.line(pts + [pts[0]], fill="#4f563e", width=max(2, s // 40))
    colors = ["#315f45", "#47733f", "#6f944b"]
    for i in range(10):
        cx = x + int((i % 5 - 2) * s * 0.22)
        cy = y + int((0.22 + (i // 5) * 0.16) * s)
        rr = max(2, int(s * 0.10))
        draw.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=colors[i % len(colors)])


def _draw_border_highland(draw, x, y, s):
    draw.ellipse((x - s * 0.95, y + s * 0.38, x + s * 0.95, y + s * 0.76), fill=(91, 88, 66, 46))
    ridge = []
    for index, offset in enumerate([-0.75, -0.45, -0.12, 0.20, 0.52, 0.78]):
        px = x + int(offset * s)
        py = y + int((0.10 if index % 2 == 0 else -0.04) * s)
        ridge.append((px, py))
    baseline = y + int(s * 0.46)
    for left, peak in zip(ridge, ridge[1:]):
        pts = [(left[0], baseline), peak, (peak[0] + int(s * 0.18), baseline)]
        draw.polygon(pts, fill="#747056")
        draw.line(pts + [pts[0]], fill="#514d3a", width=max(2, s // 44))


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
        ("Harz", 10.5600, 51.8000),
        ("Zugspitze", 10.9900, 47.4300),
        ("Alpen", 11.7000, 47.1200),
        ("Mueritz", 12.7500, 53.4300),
        ("Ruegen", 13.3800, 54.4500),
    ]:
        x, y = _project_point(proj, lon, lat)
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
        ((7.4, 53.4), (8.6, 53.6), (9.5, 53.7), (10.8, 53.9)),
        ((10.8, 53.9), (11.5, 54.0), (12.4, 54.1), (13.4, 54.4)),
        ((9.9, 53.5), (10.0, 52.7), (10.3, 52.2), (10.6, 51.8)),
        ((8.6, 53.1), (9.4, 52.6), (9.8, 52.1), (10.6, 51.8)),
        ((11.6, 52.1), (12.1, 52.6), (12.4, 53.0), (12.7, 53.4)),
        ((13.4, 52.5), (14.0, 52.1), (14.2, 51.6), (14.4, 51.1)),
        ((8.7, 49.4), (9.4, 49.6), (10.1, 49.8), (11.3, 49.8)),
        ((11.3, 49.8), (12.0, 49.4), (12.7, 49.1), (13.3, 48.8)),
        ((7.7, 50.4), (7.4, 49.9), (7.3, 49.6), (7.1, 49.3)),
        ((8.0, 48.3), (8.5, 48.6), (9.0, 48.7), (9.6, 48.8)),
    ]
    for route in routes:
        p0, p1, p2, p3 = [_project_point(proj, lon, lat) for lon, lat in route]
        pts = _bezier(p0, p1, p2, p3)
        _draw_dotted_route(draw, pts)
    alpha = Image.composite(layer.getchannel("A"), Image.new("L", canvas.size, 0), germany_mask)
    layer.putalpha(alpha)
    canvas.alpha_composite(layer)


def _draw_dotted_route(draw, pts):
    draw.line(pts, fill=(67, 52, 31, 122), width=4 * RENDER_SCALE, joint="curve")
    draw.line(pts, fill=(238, 214, 141, 146), width=max(1, RENDER_SCALE * 2), joint="curve")
    for index, p in enumerate(pts[::8]):
        rr = (3 if index % 2 == 0 else 2) * RENDER_SCALE
        draw.ellipse((p[0] - rr, p[1] - rr, p[0] + rr, p[1] + rr), fill=(75, 56, 32, 190))
        inner = max(1, rr - RENDER_SCALE)
        draw.ellipse((p[0] - inner, p[1] - inner, p[0] + inner, p[1] + inner), fill=(244, 224, 153, 238))


def main():
    os.makedirs(MAP_DIR, exist_ok=True)
    render_size = _scale_size(MAP_SIZE)
    proj = MapProjection(GERMANY_BOUNDS, MAP_SIZE)

    canvas = Image.new("RGBA", render_size, OCEAN)
    _draw_ocean_texture(canvas)
    print("Step 1: Draw countries and Germany mask")
    germany, germany_mask, land_mask = _draw_country_layer(canvas, proj)

    print("Step 2: Add terrain, texture, lakes, and routes")
    _draw_terrain(canvas, proj, land_mask)
    _draw_ground_texture(canvas, proj, germany_mask, germany)
    _draw_lakes(canvas, proj, germany_mask)
    _draw_waterways(canvas, proj, germany_mask)
    _draw_atlas_details(canvas, proj)
    _draw_routes(canvas, proj, germany_mask)
    _draw_map_labels(canvas, proj, germany_mask)
    _draw_country_border_overlay(canvas, proj, germany)

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
