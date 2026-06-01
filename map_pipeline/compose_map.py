import math
import os
import sys
import json

import geopandas as gpd
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
from shapely.geometry import Point, Polygon, box

from map_pipeline.projection import MapProjection

MAP_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "map")
FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "natural_earth")
PIPELINE_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
GLYPH_DIR = os.path.join(MAP_DIR, "glyphs")
MASSIF_DIR = os.path.join(MAP_DIR, "massifs")
MASSIF_MANIFEST_PATH = os.path.join(MASSIF_DIR, "manifest.json")
ALPINE_RELIEF_EXTENTS_PATH = os.path.join(PIPELINE_DATA_DIR, "alpine_relief_extents.json")
TERRAIN_MASSIF_LAYERS_PATH = os.path.join(PIPELINE_DATA_DIR, "terrain_massif_layers.json")
GERMANY_TERRAIN_AUDIT_PATH = os.path.join(PIPELINE_DATA_DIR, "germany_terrain_accuracy_audit.json")

GERMANY_BOUNDS = (4.5, 43.2, 16.8, 55.8)
# Match the Mercator aspect of GERMANY_BOUNDS and keep enough physical pixels
# that the runtime 200% zoom still has enough source detail for inspection.
MAP_SIZE = (1932, 3072)
RENDER_SCALE = 2

OCEAN = "#315f6d"
NEIGHBOR_LAND = "#8f9150"
GERMANY_LAND = "#9da05a"
GERMANY_EDGE = "#463c28"
BORDER = "#5a5037"
COUNTRY_NEIGHBOR_BORDER_WIDTH = 1
COUNTRY_GERMANY_EDGE_WIDTH = 2
LAKE = "#2d7285"
RIVER = "#3b8fa3"
ROUTE = "#d8c17a"
ROUTE_DARK = "#6e5832"
NAMED_WATER_FILL = (47, 98, 111, 118)
NAMED_WATER_SHALLOW = (71, 126, 129, 58)
NAMED_WATER_SHORE = (66, 78, 47, 34)
NAMED_WATER_OUTLINE = (39, 72, 72, 92)
NAMED_WATER_HIGHLIGHT = (139, 184, 181, 54)
MAJOR_NAMED_WATER_BODY_IDS = {"bodensee", "mueritz", "chiemsee"}
FOREST_SPRITE_CACHE = {}
GLYPH_CACHE = {}
FONT_CACHE = {}
FOREST_MASS_VISUAL_SCALE = 1.90
FOREST_MASS_MIN_WIDTH = 170
FOREST_CLUSTER_MIN_SOURCE_WIDTH = 96
RELIEF_TREE_CLUSTER_MIN_WIDTH = 146
LAND_DETAIL_VISUAL_SCALE = 0.68
LAND_DETAIL_ALPHA_SCALE = 0.0
LAND_DETAIL_TINT_STRENGTH = 0.34
GROUND_TEXTURE_LON_STEP = 0.74
GROUND_TEXTURE_LAT_STEP = 0.70
INTEGRATED_LAND_PATTERN_LON_STEP = 1.10
INTEGRATED_LAND_PATTERN_LAT_STEP = 1.00
INTEGRATED_LAND_PATTERN_ALPHA_SCALE = 0.14
INTEGRATED_LAND_PATTERN_MIN_SIZE = 36
RELIEF_SOFT_REGION_ALPHA_SCALE = 0.0
RIDGE_BAND_ALPHA_SCALE = 0.0
ATLAS_ROUTE_DOT_SPACING_SCALE = 1.75
ATLAS_ROUTE_DOT_MIN_RADIUS = 4
DEFAULT_ATLAS_ROUTES_ENABLED = False
DEFAULT_BASE_LAND_PATCHES_ENABLED = False
DEFAULT_INTEGRATED_LAND_PATTERN_ENABLED = False
DEFAULT_LAND_DETAIL_PATCHES_ENABLED = False
DEFAULT_MARSH_PATCHES_ENABLED = False
DEFAULT_MINOR_NAMED_WATER_BODIES_ENABLED = False
DEFAULT_NATURAL_EARTH_LAKES_ENABLED = False
DEFAULT_RIDGE_BAND_OVERLAYS_ENABLED = False
EXPORT_MASSIF_SOURCE_LAYERS = True
MASSIF_SOURCE_MANIFEST = []

RUNTIME_LANDMARK_AUDIT_VIEWPORT = (390, 844)
CITY_LANDMARK_PLACEMENT_AUDITS = [
    {
        "name": "Hamburg",
        "coordinates": (9.9937, 53.5511),
        "icon_offset": (0.0, 0.0),
        "icon_size": 48.0,
        "required_land_samples": ("top", "center", "bottom"),
    },
    {
        "name": "Kiel",
        "coordinates": (10.1228, 54.3233),
        "icon_offset": (0.0, 0.0),
        "icon_size": 0.0,
        "required_land_samples": ("coordinate",),
    },
    {
        "name": "Lübeck",
        "coordinates": (10.6866, 53.8655),
        "icon_offset": (0.0, 0.0),
        "icon_size": 0.0,
        "required_land_samples": ("coordinate",),
    },
    {
        "name": "Rostock",
        "coordinates": (12.0991, 54.0924),
        "icon_offset": (0.0, 52.0),
        "icon_size": 48.0,
        "required_land_samples": ("top", "center", "bottom"),
    },
]

# Runtime city landmarks are the only city/object layer. Keep the generated
# underlay free of baked villages or city-like pictograms so it can scale to
# Europe without fighting runtime overlays.
BAKED_TOWN_DETAILS_ENABLED = False
BAKED_TOWN_DETAILS = []

NAMED_WATER_BODIES = [
    {
        "id": "bodensee",
        "label": "Bodensee",
        "kind": "cross_border_lake",
        "points": [(8.96, 47.65), (9.16, 47.55), (9.55, 47.49), (9.78, 47.55), (9.66, 47.68), (9.26, 47.73)],
    },
    {
        "id": "mueritz",
        "label": "Müritz",
        "kind": "lake",
        "points": [(12.61, 53.55), (12.75, 53.58), (12.86, 53.47), (12.80, 53.31), (12.67, 53.26), (12.58, 53.40)],
    },
    {
        "id": "chiemsee",
        "label": "Chiemsee",
        "kind": "lake",
        "points": [(12.28, 47.90), (12.43, 47.94), (12.60, 47.88), (12.56, 47.78), (12.36, 47.75), (12.23, 47.82)],
    },
    {
        "id": "schweriner_see",
        "label": "Schweriner See",
        "kind": "lake",
        "points": [(11.36, 53.76), (11.54, 53.68), (11.50, 53.53), (11.37, 53.49), (11.28, 53.60)],
    },
    {
        "id": "plauer_see",
        "label": "Plauer See",
        "kind": "lake",
        "points": [(12.20, 53.53), (12.35, 53.48), (12.35, 53.37), (12.20, 53.35), (12.12, 53.44)],
    },
    {
        "id": "schaalsee",
        "label": "Schaalsee",
        "kind": "lake",
        "points": [(10.89, 53.66), (11.05, 53.68), (11.12, 53.58), (11.00, 53.50), (10.87, 53.56)],
    },
    {
        "id": "steinhuder_meer",
        "label": "Steinhuder Meer",
        "kind": "lake",
        "points": [(9.23, 52.50), (9.38, 52.52), (9.48, 52.46), (9.40, 52.40), (9.23, 52.43)],
    },
    {
        "id": "edersee",
        "label": "Edersee",
        "kind": "reservoir",
        "points": [(8.83, 51.19), (8.96, 51.21), (9.10, 51.18), (9.02, 51.13), (8.86, 51.14)],
    },
    {
        "id": "ammersee",
        "label": "Ammersee",
        "kind": "lake",
        "points": [(11.05, 48.04), (11.16, 48.00), (11.18, 47.88), (11.09, 47.84), (11.00, 47.93)],
    },
    {
        "id": "starnberger_see",
        "label": "Starnberger See",
        "kind": "lake",
        "points": [(11.25, 47.98), (11.39, 47.94), (11.39, 47.78), (11.28, 47.74), (11.20, 47.86)],
    },
    {
        "id": "tegernsee",
        "label": "Tegernsee",
        "kind": "lake",
        "points": [(11.69, 47.76), (11.78, 47.75), (11.78, 47.68), (11.70, 47.67), (11.65, 47.72)],
    },
    {
        "id": "mueggelsee",
        "label": "Müggelsee",
        "kind": "lake",
        "subtle": True,
        "points": [(13.61, 52.45), (13.72, 52.46), (13.79, 52.43), (13.78, 52.39), (13.65, 52.38), (13.58, 52.41)],
    },
    {
        "id": "wannsee_havel",
        "label": "Wannsee / Havel",
        "kind": "lake_chain",
        "subtle": True,
        "points": [(13.13, 52.47), (13.20, 52.44), (13.22, 52.38), (13.16, 52.32), (13.09, 52.35), (13.07, 52.43)],
    },
    {
        "id": "tegeler_see",
        "label": "Tegeler See",
        "kind": "lake",
        "subtle": True,
        "points": [(13.22, 52.60), (13.30, 52.61), (13.34, 52.58), (13.31, 52.54), (13.22, 52.55), (13.19, 52.58)],
    },
]

ALPINE_MASSIF_SEGMENTS = [
    {
        "id": "western_alps_massif",
        "label": "Western Alps",
        "source_extent_id": "western_alps_massif",
        "arc": [(6.20, 46.78), (7.10, 46.55), (8.05, 46.45)],
        "shadow": [(6.00, 46.95), (7.05, 46.66), (8.35, 46.58), (8.55, 47.18), (7.25, 47.30), (6.10, 47.22)],
        "glyphs": [
            ("alps_range_3", 6.75, 46.78, 300, 0.00),
            ("alps_peak_1", 7.45, 46.58, 150, -0.03),
            ("alps_range_1", 7.92, 46.72, 255, 0.04),
        ],
    },
    {
        "id": "swiss_alps_massif",
        "label": "Swiss Alps",
        "source_extent_id": "swiss_alps_massif",
        "arc": [(8.05, 46.48), (9.10, 46.46), (10.20, 46.58)],
        "shadow": [(7.75, 46.70), (9.05, 46.46), (10.45, 46.62), (10.65, 47.28), (9.25, 47.28), (7.80, 47.14)],
        "glyphs": [
            ("alps_range_1", 8.60, 46.72, 330, 0.00),
            ("alps_peak_2", 9.35, 46.52, 170, -0.05),
            ("alps_range_3", 10.00, 46.82, 300, 0.03),
        ],
    },
    {
        "id": "bavarian_tyrol_alps_massif",
        "label": "Bavarian and Tyrol Alps",
        "source_extent_id": "bavarian_tyrol_alps_massif",
        "arc": [(10.20, 46.60), (11.30, 46.82), (12.45, 47.05)],
        "shadow": [(9.95, 46.84), (11.25, 46.74), (12.75, 47.06), (12.95, 47.78), (11.25, 47.78), (10.05, 47.46)],
        "glyphs": [
            ("alps_range_2", 10.55, 46.96, 330, 0.00),
            ("alps_range_1", 11.42, 47.12, 320, -0.01),
            ("alps_peak_1", 12.05, 46.95, 160, -0.06),
            ("alps_range_3", 12.45, 47.24, 275, 0.03),
        ],
    },
    {
        "id": "german_alpine_edge_massif",
        "label": "German Alpine Edge",
        "source_extent_id": "german_alpine_edge_massif",
        "required_country_overlap": "Germany",
        "arc": [(10.15, 47.55), (11.10, 47.55), (12.25, 47.62), (13.05, 47.70)],
        "shadow": [(9.85, 47.48), (10.95, 47.36), (12.45, 47.46), (13.35, 47.70), (13.20, 48.04), (11.45, 47.98), (10.00, 47.86)],
        "glyphs": [
            ("alps_range_2", 10.55, 47.57, 185, -0.02),
            ("alps_peak_1", 10.98, 47.45, 125, -0.08),
            ("alps_range_1", 11.65, 47.64, 195, -0.01),
            ("alps_range_3", 12.55, 47.74, 175, 0.00),
        ],
    },
    {
        "id": "austrian_alps_massif",
        "label": "Austrian Alps",
        "source_extent_id": "austrian_alps_massif",
        "arc": [(12.45, 47.05), (13.70, 47.28), (15.25, 47.62)],
        "shadow": [(12.20, 47.26), (13.75, 47.18), (15.75, 47.60), (15.95, 48.18), (14.05, 48.15), (12.35, 47.82)],
        "glyphs": [
            ("alps_range_1", 13.05, 47.34, 300, 0.00),
            ("alps_peak_2", 13.82, 47.24, 145, -0.04),
            ("alps_range_3", 14.45, 47.56, 290, 0.02),
            ("alps_range_2", 15.20, 47.78, 245, 0.04),
        ],
    },
]

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
        "ridge_bands": [
            {
                "id": "black_forest_spine",
                "style": "forested",
                "points": [(7.78, 49.00), (8.05, 48.55), (8.05, 48.12), (7.82, 47.72)],
                "height": 38,
                "step": 34,
            },
        ],
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
        "points": [
            (5.95, 46.45), (7.15, 46.05), (8.75, 45.78), (10.35, 45.82),
            (12.05, 46.02), (14.05, 46.38), (16.05, 46.92), (16.25, 47.70),
            (14.40, 48.18), (12.05, 48.30), (10.10, 48.05), (8.35, 47.55),
            (6.65, 47.18),
        ],
        "trees": [(8.45, 47.35, 50), (10.0, 48.2, 44), (11.0, 48.05, 50), (12.35, 48.0, 46), (14.15, 47.75, 44)],
        "ridge_bands": [
            {
                "id": "main_alpine_wall",
                "points": [(6.25, 46.62), (7.45, 46.34), (8.85, 46.23), (10.25, 46.30), (11.70, 46.43), (13.20, 46.66), (14.80, 47.00), (15.80, 47.30)],
                "height": 82,
                "step": 42,
            },
            {
                "id": "northern_alpine_foothills",
                "points": [(8.00, 47.28), (9.55, 47.08), (10.95, 47.12), (12.35, 47.32), (13.75, 47.55)],
                "height": 50,
                "step": 48,
            },
        ],
        "massif_segments": ALPINE_MASSIF_SEGMENTS,
        "mountain_glyphs": [],
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
        "ridge_bands": [
            {
                "id": "bavarian_forest_spine",
                "style": "forested",
                "points": [(12.15, 49.38), (12.70, 49.12), (13.40, 49.02)],
                "height": 36,
                "step": 34,
            },
        ],
        "mountain_glyphs": [("highland_forest_3", 12.95, 49.20, 150)],
        "mountains": [],
    },
    {
        "id": "harz",
        "label": "Harz",
        "kind": "isolated_mountain_range",
        "glyph": "forested_highland",
        "fill": (55, 112, 59, 96),
        "blur": 24,
        "points": [(9.76, 52.14), (10.55, 52.22), (11.36, 51.92), (11.48, 51.52), (10.72, 51.24), (9.72, 51.42)],
        "trees": [(10.36, 51.88, 72), (10.84, 51.58, 64)],
        "ridge_bands": [
            {
                "id": "harz_brocken_spine",
                "style": "forested",
                "points": [(9.95, 51.94), (10.36, 51.84), (10.82, 51.72), (11.20, 51.56)],
                "height": 52,
                "step": 26,
            },
            {
                "id": "harz_south_spur",
                "style": "forested",
                "points": [(10.05, 51.58), (10.48, 51.50), (10.92, 51.42)],
                "height": 34,
                "step": 28,
            },
        ],
        "mountain_glyphs": [("highland_forest_1", 10.50, 51.78, 188), ("highland_forest_2", 10.92, 51.55, 138)],
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
        "ridge_bands": [
            {
                "id": "erzgebirge_border_spine",
                "style": "border",
                "points": [(12.55, 50.82), (13.40, 50.66), (14.45, 50.68)],
                "height": 36,
                "step": 32,
            },
        ],
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
        "ridge_bands": [
            {
                "id": "elbe_sandstone_rim",
                "style": "sandstone",
                "points": [(13.78, 51.04), (14.20, 50.92), (14.58, 50.96)],
                "height": 28,
                "step": 28,
            },
        ],
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
        "ridge_bands": [
            {
                "id": "eifel_hunsrueck_low_spine",
                "style": "low",
                "points": [(5.95, 50.55), (6.70, 50.25), (7.40, 49.90)],
                "height": 30,
                "step": 34,
            },
        ],
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

ATLAS_ROUTE_SEGMENTS = [
    {
        "id": "north_to_harz_trail",
        "points": [(9.90, 53.48), (9.65, 52.82), (10.18, 52.25), (10.62, 51.80)],
        "step": 18,
    },
    {
        "id": "harz_to_berlin_trail",
        "points": [(10.62, 51.80), (11.42, 51.92), (12.42, 52.18), (13.40, 52.52)],
        "step": 20,
    },
    {
        "id": "elbe_dresden_trail",
        "points": [(10.62, 51.80), (11.72, 51.55), (12.72, 51.34), (13.74, 51.05)],
        "step": 20,
    },
    {
        "id": "rhine_to_south_trail",
        "points": [(6.96, 50.94), (7.82, 50.22), (8.58, 49.56), (9.18, 48.78)],
        "step": 19,
    },
    {
        "id": "southern_alps_trail",
        "points": [(9.18, 48.78), (10.18, 48.34), (10.92, 48.12), (11.58, 48.14)],
        "step": 18,
    },
]

ATLAS_FOREST_MASSES = [
    {
        "id": "lueneburg_heath",
        "label": "Lueneburg Heath",
        "clusters": [
            ("atlas_forest_pine_dense", 10.02, 53.03, 128),
            ("atlas_forest_pine_round", 10.46, 52.88, 104),
        ],
    },
    {
        "id": "mecklenburg_lake_forests",
        "label": "Mecklenburg Lake District forests",
        "clusters": [
            ("atlas_forest_mixed_large", 12.30, 53.52, 120),
            ("atlas_forest_broadleaf_round", 12.80, 53.22, 96),
        ],
    },
    {
        "id": "spreewald_lausitz",
        "label": "Spreewald and Lausitz",
        "clusters": [
            ("atlas_forest_mixed_wide", 13.95, 51.86, 104),
            ("atlas_forest_deciduous_dense", 14.38, 51.52, 104),
        ],
    },
    {
        "id": "teutoburg_weser",
        "label": "Teutoburg and Weser uplands",
        "clusters": [
            ("atlas_forest_mixed_tall", 8.65, 52.08, 104),
            ("atlas_forest_pine_small", 9.36, 51.72, 100),
        ],
    },
    {
        "id": "sauerland_rothaar",
        "label": "Sauerland and Rothaar",
        "clusters": [
            ("atlas_forest_rocky_mixed", 8.05, 51.18, 118),
            ("atlas_forest_mixed_large", 8.52, 50.96, 100),
        ],
    },
    {
        "id": "eifel_ardennes_edge",
        "label": "Eifel and Ardennes edge",
        "clusters": [
            ("atlas_forest_mixed_wide", 6.52, 50.28, 118),
            ("atlas_forest_pine_dense", 7.05, 50.10, 100),
        ],
    },
    {
        "id": "spessart_odenwald",
        "label": "Spessart and Odenwald",
        "clusters": [
            ("atlas_forest_deciduous_dense", 9.35, 50.03, 104),
            ("atlas_forest_mixed_tall", 8.82, 49.66, 100),
        ],
    },
    {
        "id": "thuringian_forest",
        "label": "Thuringian Forest",
        "clusters": [
            ("atlas_forest_rocky_pine", 10.82, 50.74, 118),
            ("atlas_forest_pine_round", 11.36, 50.58, 100),
        ],
    },
    {
        "id": "franconian_swabian_uplands",
        "label": "Franconian and Swabian uplands",
        "clusters": [
            ("atlas_forest_pine_dense", 10.55, 49.45, 100),
            ("atlas_forest_deciduous_dense", 9.58, 48.62, 100),
        ],
    },
    {
        "id": "upper_bavaria_foothills",
        "label": "Upper Bavaria foothill forests",
        "clusters": [
            ("atlas_forest_rocky_mixed", 11.34, 48.02, 96),
            ("atlas_forest_rocky_pine", 12.15, 48.10, 100),
        ],
    },
]

ATLAS_LAND_DETAIL_PATCHES = [
    ("atlas_land_grass_patch", 8.95, 53.38, 176),
    ("atlas_land_tuft_patch", 11.20, 53.28, 154),
    ("atlas_land_flower_meadow", 7.70, 52.54, 156),
    ("atlas_land_rocky_meadow", 12.25, 52.22, 150),
    ("atlas_land_grass_patch", 9.95, 51.34, 164),
    ("atlas_land_tuft_patch", 13.72, 50.62, 154),
    ("atlas_land_flower_meadow", 8.72, 49.16, 158),
    ("atlas_land_rocky_meadow", 10.52, 48.74, 152),
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
MIN_ATLAS_DETAIL_WIDTH = 118
DEFAULT_ATLAS_DETAIL_KINDS = {"ship"}


def audit_geography_layers():
    errors = []
    bounds_poly = box(*GERMANY_BOUNDS)
    relief_polygons = {region["id"]: Polygon(region["points"]) for region in RELIEF_REGIONS}
    admin_dataset = "ne_50m_admin_0_countries"
    if not os.path.isdir(os.path.join(DATA_DIR, admin_dataset)):
        admin_dataset = "ne_110m_admin_0_countries"
    countries = _clip_to_bounds(_load_shapefile(admin_dataset), GERMANY_BOUNDS)
    country_geometries = {row["ADMIN"]: row.geometry for _, row in countries.iterrows()}

    for region in RELIEF_REGIONS:
        region_id = region["id"]
        region_polygon = relief_polygons[region_id]
        if not region_polygon.is_valid or region_polygon.area <= 0:
            errors.append(f"relief region {region_id} has invalid polygon")
        if region_id == "northern_lowlands":
            for key in ("mountain_glyphs", "ridge_bands", "massif_segments"):
                if region.get(key):
                    errors.append(f"northern_lowlands must not define {key}")
            if region.get("mountains"):
                errors.append("northern_lowlands must not define mountains")

        for glyph_name, lon, lat, _width in region.get("mountain_glyphs", []):
            _audit_point(errors, bounds_poly, lon, lat, f"{region_id}:{glyph_name}")
            if not region_polygon.buffer(0.20).covers(Point(lon, lat)):
                errors.append(f"mountain glyph {glyph_name} is outside relief region {region_id}")

        for ridge_band in region.get("ridge_bands", []):
            for lon, lat in ridge_band["points"]:
                _audit_point(errors, bounds_poly, lon, lat, f"{region_id}:{ridge_band['id']}")
                if not region_polygon.buffer(0.25).covers(Point(lon, lat)):
                    errors.append(f"ridge band {ridge_band['id']} is outside relief region {region_id}")

        for segment in region.get("massif_segments", []):
            for point_group in ("arc", "shadow"):
                for lon, lat in segment.get(point_group, []):
                    _audit_point(errors, bounds_poly, lon, lat, f"{region_id}:{segment['id']}:{point_group}")
                    if not region_polygon.buffer(0.50).covers(Point(lon, lat)):
                        errors.append(f"massif {segment['id']} {point_group} is outside relief region {region_id}")
            for glyph_name, lon, lat, _width, _y_offset in segment.get("glyphs", []):
                _audit_point(errors, bounds_poly, lon, lat, f"{region_id}:{segment['id']}:{glyph_name}")
                if not region_polygon.buffer(0.25).covers(Point(lon, lat)):
                    errors.append(f"massif glyph {glyph_name} is outside relief region {region_id}")
            required_country = segment.get("required_country_overlap")
            if required_country:
                country_geom = country_geometries.get(required_country)
                if country_geom is None:
                    errors.append(f"massif {segment['id']} requires unknown country {required_country}")
                else:
                    massif_points = []
                    for point_group in ("arc", "shadow"):
                        massif_points.extend(segment.get(point_group, []))
                    massif_points.extend(
                        (lon, lat)
                        for _glyph_name, lon, lat, _width, _y_offset in segment.get("glyphs", [])
                    )
                    if not any(country_geom.covers(Point(lon, lat)) for lon, lat in massif_points):
                        errors.append(f"massif {segment['id']} must overlap {required_country}")

    for water_body in NAMED_WATER_BODIES:
        if len(water_body["points"]) < 4:
            errors.append(f"water body {water_body['id']} needs at least four outline points")
        for lon, lat in water_body["points"]:
            _audit_point(errors, bounds_poly, lon, lat, f"water:{water_body['id']}")

    for detail in ATLAS_DETAILS:
        _audit_point(errors, bounds_poly, detail["lon"], detail["lat"], f"detail:{detail['id']}")
        if str(detail["glyph"]).startswith(("alps_", "border_highland", "highland_forest")):
            errors.append(f"atlas detail {detail['id']} must not use relief glyph {detail['glyph']}")
        if detail["kind"] in DEFAULT_ATLAS_DETAIL_KINDS:
            kind_scale = ATLAS_DETAIL_KIND_SCALE.get(detail["kind"], 1.0)
            target_width = max(MIN_ATLAS_DETAIL_WIDTH, detail["width"] * kind_scale)
            if target_width < MIN_ATLAS_DETAIL_WIDTH:
                errors.append(f"default atlas detail {detail['id']} is too small for the default map")

    for forest_mass in ATLAS_FOREST_MASSES:
        for glyph_name, lon, lat, width in forest_mass["clusters"]:
            _audit_point(errors, bounds_poly, lon, lat, f"forest:{forest_mass['id']}:{glyph_name}")
            if not str(glyph_name).startswith("atlas_forest_"):
                errors.append(f"forest mass {forest_mass['id']} uses non-forest glyph {glyph_name}")
            if width < FOREST_CLUSTER_MIN_SOURCE_WIDTH:
                errors.append(f"forest mass {forest_mass['id']} cluster {glyph_name} is too small for the default map")
            display_width = max(FOREST_MASS_MIN_WIDTH, int(width * FOREST_MASS_VISUAL_SCALE))
            if display_width < FOREST_MASS_MIN_WIDTH:
                errors.append(f"forest mass {forest_mass['id']} cluster {glyph_name} renders below the forest readability minimum")
    for region in RELIEF_REGIONS:
        for lon, lat, tree_size in region.get("trees", []):
            _audit_point(errors, bounds_poly, lon, lat, f"relief tree:{region['id']}")
            if _relief_tree_cluster_width(tree_size) < RELIEF_TREE_CLUSTER_MIN_WIDTH:
                errors.append(f"relief tree cluster in {region['id']} is too small for the default map")
    if DEFAULT_ATLAS_ROUTES_ENABLED:
        errors.append("default atlas routes must stay hidden until route dots read above mobile screenshot scale")
    for glyph_name, lon, lat, width in ATLAS_LAND_DETAIL_PATCHES:
        _audit_point(errors, bounds_poly, lon, lat, f"land detail:{glyph_name}")
        if not str(glyph_name).startswith("atlas_land_"):
            errors.append(f"land detail {glyph_name} must use atlas_land_* glyphs")
        if width < 150:
            errors.append(f"land detail {glyph_name} is too small to read as terrain")

    errors.extend(audit_terrain_massif_layer_contract())
    errors.extend(audit_germany_terrain_accuracy_contract())
    errors.extend(audit_runtime_landmark_placement(country_geometries=country_geometries))
    return errors


def audit_germany_terrain_accuracy_contract():
    errors = []
    if not os.path.exists(GERMANY_TERRAIN_AUDIT_PATH):
        return [f"Germany terrain accuracy audit contract is missing: {GERMANY_TERRAIN_AUDIT_PATH}"]
    with open(GERMANY_TERRAIN_AUDIT_PATH, "r", encoding="utf-8") as file:
        contract = json.load(file)

    if contract.get("schema") != "cable-world.germany-terrain-accuracy-audit.v1":
        errors.append("Germany terrain accuracy audit contract has an unknown schema")

    if contract.get("claim_policy") != "audit_guardrail_not_visual_10_10":
        errors.append("Germany terrain accuracy audit must not claim full visual 10/10 readiness")

    relief_regions = {region["id"]: region for region in RELIEF_REGIONS}
    if "northern_lowlands" not in relief_regions:
        errors.append("Germany terrain audit requires a northern_lowlands exclusion region")

    with open(TERRAIN_MASSIF_LAYERS_PATH, "r", encoding="utf-8") as file:
        terrain_contract = json.load(file)
    source_layers = {layer.get("id"): layer for layer in terrain_contract.get("source_layers", [])}

    for massif in contract.get("required_massifs", []):
        massif_id = massif.get("id")
        layer_id = massif.get("terrain_layer_id", massif_id)
        region = relief_regions.get(layer_id)
        layer = source_layers.get(layer_id)
        if region is None:
            errors.append(f"required Germany massif {massif_id} is missing relief region {layer_id}")
            continue
        if layer is None:
            errors.append(f"required Germany massif {massif_id} is missing terrain source metadata {layer_id}")
            continue
        for required_key in ("source_extent_id", "source_type", "placement_policy", "source_confidence", "replacement_status"):
            if not layer.get(required_key):
                errors.append(f"required Germany massif {massif_id} lacks terrain source metadata {required_key}")
        if massif.get("requires_ridge_bands") and not region.get("ridge_bands"):
            errors.append(f"required Germany massif {massif_id} must have ridge bands")
        if massif.get("requires_rendered_relief"):
            has_rendered_relief = any(region.get(key) for key in ("ridge_bands", "massif_segments", "mountain_glyphs", "trees"))
            if not has_rendered_relief:
                errors.append(f"required Germany massif {massif_id} has no rendered relief anchors")
        expected_source_confidence = massif.get("source_confidence_must_not_be")
        if expected_source_confidence and layer.get("source_confidence") == expected_source_confidence:
            errors.append(f"required Germany massif {massif_id} still has forbidden source confidence {expected_source_confidence}")
        if massif.get("not_final_until_elevation_backed") and layer.get("replacement_status") == "production_approved":
            errors.append(f"required Germany massif {massif_id} cannot be production approved before elevation-backed review")

    for exclusion in contract.get("north_german_plain_exclusions", []):
        exclusion_id = exclusion.get("id", "<missing>")
        exclusion_box = box(*exclusion["bbox"])
        max_large_width = float(exclusion.get("max_mountain_glyph_width_px", 0))
        for region in RELIEF_REGIONS:
            if region["id"] == "northern_lowlands":
                for forbidden_key in exclusion.get("forbidden_keys", []):
                    if region.get(forbidden_key):
                        errors.append(f"lowland exclusion {exclusion_id} forbids northern_lowlands {forbidden_key}")
            for glyph_name, lon, lat, width in region.get("mountain_glyphs", []):
                if exclusion_box.covers(Point(lon, lat)) and width > max_large_width:
                    errors.append(
                        f"mountain glyph {region['id']}:{glyph_name} width {width} falls inside lowland exclusion {exclusion_id}"
                    )
            for ridge_band in region.get("ridge_bands", []):
                for lon, lat in ridge_band.get("points", []):
                    if exclusion_box.covers(Point(lon, lat)):
                        errors.append(f"ridge band {region['id']}:{ridge_band['id']} falls inside lowland exclusion {exclusion_id}")
            for segment in region.get("massif_segments", []):
                for point_group in ("arc", "shadow"):
                    for lon, lat in segment.get(point_group, []):
                        if exclusion_box.covers(Point(lon, lat)):
                            errors.append(f"massif {region['id']}:{segment['id']} {point_group} falls inside lowland exclusion {exclusion_id}")
                for glyph_name, lon, lat, width, _y_offset in segment.get("glyphs", []):
                    if exclusion_box.covers(Point(lon, lat)) and width > max_large_width:
                        errors.append(f"massif glyph {region['id']}:{segment['id']}:{glyph_name} falls inside lowland exclusion {exclusion_id}")

    water_ids = {water_body["id"] for water_body in NAMED_WATER_BODIES}
    for expected_water in contract.get("required_water_bodies", []):
        water_id = expected_water.get("id")
        if water_id not in water_ids:
            errors.append(f"required Germany water body is missing: {water_id}")
            continue
        water_body = next(water for water in NAMED_WATER_BODIES if water["id"] == water_id)
        if len(water_body.get("points", [])) < int(expected_water.get("min_outline_points", 4)):
            errors.append(f"required Germany water body {water_id} does not have enough outline points")

    map_labels = {label["name"]: label for label in MAP_LABELS}
    detail_ids = {detail["id"] for detail in ATLAS_DETAILS}
    for island in contract.get("required_islands", []):
        island_name = island.get("name")
        label = map_labels.get(island_name)
        if label is None or label.get("kind") != "island":
            errors.append(f"required Germany island label is missing or not marked as island: {island_name}")
            continue
        if "bbox" in island and not box(*island["bbox"]).covers(Point(label["lon"], label["lat"])):
            errors.append(f"required Germany island label {island_name} falls outside its audit bbox")
        for detail_id in island.get("required_detail_ids", []):
            if detail_id not in detail_ids:
                errors.append(f"required Germany island detail is missing: {detail_id}")

    required_sources = contract.get("source_requirements", {}).get("required_before_final_relief", [])
    alpine_sources = set()
    if os.path.exists(ALPINE_RELIEF_EXTENTS_PATH):
        with open(ALPINE_RELIEF_EXTENTS_PATH, "r", encoding="utf-8") as file:
            alpine_contract = json.load(file)
        primary = alpine_contract.get("elevation_source_strategy", {}).get("primary", {})
        fallbacks = alpine_contract.get("elevation_source_strategy", {}).get("fallbacks", [])
        alpine_sources.add(primary.get("id"))
        alpine_sources.update(source.get("id") for source in fallbacks)
    for source_id in required_sources:
        if source_id not in alpine_sources:
            errors.append(f"Germany terrain audit requires source strategy {source_id}")

    return errors


def audit_alpine_relief_contract():
    errors = []
    if not os.path.exists(ALPINE_RELIEF_EXTENTS_PATH):
        return [f"Alpine relief extents metadata is missing: {ALPINE_RELIEF_EXTENTS_PATH}"]
    with open(ALPINE_RELIEF_EXTENTS_PATH, "r", encoding="utf-8") as file:
        contract = json.load(file)

    if contract.get("schema") != "cable-world.alpine-relief-extents.v1":
        errors.append("Alpine relief extents metadata has an unknown schema")

    source_strategy = contract.get("elevation_source_strategy", {})
    primary_source = source_strategy.get("primary", {})
    fallback_sources = source_strategy.get("fallbacks", [])
    source_ids = {primary_source.get("id")}
    source_ids.update(source.get("id") for source in fallback_sources)
    source_ids.discard(None)
    for required_source in ("copernicus_dem_glo_30", "eu_dem", "nasa_srtm_1_arc_second"):
        if required_source not in source_ids:
            errors.append(f"Alpine elevation source strategy is missing {required_source}")
    for source in [primary_source] + list(fallback_sources):
        if not source:
            continue
        for required_key in ("id", "name", "url", "license_note", "download_status"):
            if not source.get(required_key):
                errors.append(f"Alpine elevation source {source.get('id', '<missing>')} lacks {required_key}")
    if source_strategy.get("anchor_policy") != "anchors_must_be_dem_ridge_or_named_massif_centroid":
        errors.append("Alpine anchor policy must forbid random decorative anchors")

    extent_segments = {segment.get("id"): segment for segment in contract.get("massif_segments", [])}
    rendered_segments = {segment["id"]: segment for segment in ALPINE_MASSIF_SEGMENTS}
    for segment_id in sorted(set(rendered_segments) - set(extent_segments)):
        errors.append(f"rendered Alpine segment {segment_id} has no source extent metadata")
    for segment_id in sorted(set(extent_segments) - set(rendered_segments)):
        errors.append(f"Alpine source extent {segment_id} is not rendered by ALPINE_MASSIF_SEGMENTS")

    forbidden_geometry_tokens = ("random", "decorative", "sticker")
    for segment_id, rendered_segment in rendered_segments.items():
        source_extent_id = rendered_segment.get("source_extent_id")
        if source_extent_id != segment_id:
            errors.append(f"rendered Alpine segment {segment_id} must point at matching source_extent_id")
        extent = extent_segments.get(segment_id)
        if not extent:
            continue
        geometry_source = str(extent.get("geometry_source", ""))
        if not geometry_source:
            errors.append(f"Alpine source extent {segment_id} lacks geometry_source")
        if any(token in geometry_source for token in forbidden_geometry_tokens):
            errors.append(f"Alpine source extent {segment_id} uses forbidden decorative geometry source")
        if extent.get("source_dataset") not in source_ids:
            errors.append(f"Alpine source extent {segment_id} references unknown source_dataset")
        if not extent.get("coverage_regions"):
            errors.append(f"Alpine source extent {segment_id} must declare coverage_regions")
        if not extent.get("elevation_band_m"):
            errors.append(f"Alpine source extent {segment_id} must declare planned elevation bands")
        if extent.get("review_status") == "production_approved" and source_strategy.get("primary", {}).get("download_status") == "planned":
            errors.append(f"Alpine source extent {segment_id} cannot be production approved before DEM processing")

    admin_dataset = "ne_50m_admin_0_countries"
    if not os.path.isdir(os.path.join(DATA_DIR, admin_dataset)):
        admin_dataset = "ne_110m_admin_0_countries"
    countries = _clip_to_bounds(_load_shapefile(admin_dataset), GERMANY_BOUNDS)
    country_geometries = {row["ADMIN"]: row.geometry for _, row in countries.iterrows()}
    segment_geometries = {
        segment_id: _alpine_segment_geometry(segment)
        for segment_id, segment in rendered_segments.items()
    }

    for requirement in contract.get("coverage_requirements", []):
        requirement_id = requirement.get("id", "<missing>")
        required_segment_ids = requirement.get("required_segment_ids") or list(rendered_segments)
        required_segment_ids = [segment_id for segment_id in required_segment_ids if segment_id in segment_geometries]
        if requirement.get("country"):
            target = country_geometries.get(requirement["country"])
            if target is None:
                errors.append(f"Alpine coverage requirement {requirement_id} references unknown country")
                continue
        else:
            target = box(*requirement["bbox"])
        overlapping_segments = [
            segment_id
            for segment_id in required_segment_ids
            if segment_geometries[segment_id].intersects(target)
        ]
        minimum = int(requirement.get("minimum_rendered_segments", 1))
        if len(overlapping_segments) < minimum:
            errors.append(
                f"Alpine coverage requirement {requirement_id} has only "
                f"{len(overlapping_segments)} rendered segment overlaps; expected {minimum}"
            )
        for segment_id in requirement.get("required_segment_ids", []):
            if segment_id not in overlapping_segments:
                errors.append(f"Alpine coverage requirement {requirement_id} must include {segment_id}")

    for exclusion in contract.get("lowland_exclusions", []):
        if exclusion.get("rule") != "no_alpine_mountain_glyphs":
            continue
        exclusion_box = box(*exclusion["bbox"])
        for segment in ALPINE_MASSIF_SEGMENTS:
            for glyph_name, lon, lat, _width, _y_offset in segment.get("glyphs", []):
                if exclusion_box.covers(Point(lon, lat)):
                    errors.append(
                        f"Alpine glyph {segment['id']}:{glyph_name} falls inside lowland exclusion {exclusion['id']}"
                    )
    return errors


def _alpine_segment_geometry(segment):
    shadow = segment.get("shadow", [])
    if len(shadow) >= 3:
        polygon = Polygon(shadow)
        if polygon.is_valid and polygon.area > 0:
            return polygon
    points = list(segment.get("arc", []))
    points.extend((lon, lat) for _glyph_name, lon, lat, _width, _y_offset in segment.get("glyphs", []))
    if not points:
        return Polygon()
    min_lon = min(lon for lon, _lat in points)
    max_lon = max(lon for lon, _lat in points)
    min_lat = min(lat for _lon, lat in points)
    max_lat = max(lat for _lon, lat in points)
    return box(min_lon, min_lat, max_lon, max_lat)


def audit_runtime_landmark_placement(country_geometries=None):
    errors = []
    if country_geometries is None:
        admin_dataset = "ne_50m_admin_0_countries"
        if not os.path.isdir(os.path.join(DATA_DIR, admin_dataset)):
            admin_dataset = "ne_110m_admin_0_countries"
        countries = _clip_to_bounds(_load_shapefile(admin_dataset), GERMANY_BOUNDS)
        country_geometries = {row["ADMIN"]: row.geometry for _, row in countries.iterrows()}

    germany = country_geometries.get("Germany")
    if germany is None:
        return ["runtime landmark audit requires Germany geometry"]

    base_size = _runtime_map_base_size_for_viewport(RUNTIME_LANDMARK_AUDIT_VIEWPORT)
    proj = MapProjection(GERMANY_BOUNDS, base_size)
    for landmark in CITY_LANDMARK_PLACEMENT_AUDITS:
        lon, lat = landmark["coordinates"]
        icon_offset_x, icon_offset_y = landmark["icon_offset"]
        icon_size = float(landmark["icon_size"])
        x, y = proj.project(lon, lat)
        sample_points = {
            "coordinate": (x, y),
            "top": (x + icon_offset_x, y - icon_size - 9.0 + icon_offset_y),
            "center": (x + icon_offset_x, y - icon_size * 0.5 - 9.0 + icon_offset_y),
            "bottom": (x + icon_offset_x, y - 9.0 + icon_offset_y),
        }
        for sample_name in landmark.get("required_land_samples", ()):
            sample_x, sample_y = sample_points[sample_name]
            sample_lon, sample_lat = proj.inverse(sample_x, sample_y)
            if not germany.covers(Point(sample_lon, sample_lat)):
                errors.append(
                    f"runtime landmark {landmark['name']} {sample_name} sample "
                    f"falls outside Germany at ({sample_lon:.4f}, {sample_lat:.4f})"
                )
    return errors


def audit_massif_source_manifest():
    errors = []
    if not os.path.exists(MASSIF_MANIFEST_PATH):
        return [f"massif source manifest is missing: {MASSIF_MANIFEST_PATH}"]
    with open(MASSIF_MANIFEST_PATH, "r", encoding="utf-8") as file:
        manifest = json.load(file)

    contract = _load_terrain_massif_contract()
    asset_contract = contract.get("production_asset_contract", {})
    expected_schema = asset_contract.get("manifest_schema", "cable-world.massif-source-layers.v1")
    if manifest.get("schema") != expected_schema:
        errors.append("massif source manifest has an unknown schema")
    render_scale = manifest.get("render_scale")
    if not isinstance(render_scale, (int, float)) or render_scale <= 0:
        errors.append("massif source manifest must declare positive render_scale")

    expected_ids = _expected_source_layer_ids()
    layers = manifest.get("layers", [])
    actual_ids = {layer.get("id") for layer in layers}
    missing_ids = sorted(expected_ids - actual_ids)
    extra_ids = sorted(actual_ids - expected_ids)
    for segment_id in missing_ids:
        errors.append(f"massif source layer {segment_id} is missing from manifest")
    for segment_id in extra_ids:
        errors.append(f"massif source manifest has unexpected layer {segment_id}")

    for layer in layers:
        layer_id = layer.get("id", "")
        image_name = layer.get("image", "")
        image_path = os.path.join(MASSIF_DIR, image_name)
        sidecar_path = os.path.join(MASSIF_DIR, f"{layer_id}.json")
        _audit_massif_source_layer_metadata(errors, layer, asset_contract, render_scale)
        if not image_name or not os.path.exists(image_path):
            errors.append(f"massif source layer {layer_id} image is missing: {image_name}")
            continue
        if not os.path.exists(sidecar_path):
            errors.append(f"massif source layer {layer_id} sidecar is missing: {sidecar_path}")
        else:
            with open(sidecar_path, "r", encoding="utf-8") as file:
                sidecar = json.load(file)
            if sidecar != layer:
                errors.append(f"massif source layer {layer_id} sidecar does not match manifest metadata")
        with Image.open(image_path) as image:
            if image.mode != "RGBA":
                errors.append(f"massif source layer {layer_id} must be RGBA")
            expected_size = tuple(layer.get("cropped_size_px", []))
            if expected_size != image.size:
                errors.append(f"massif source layer {layer_id} metadata size does not match PNG")
            if image.getbbox() is None:
                errors.append(f"massif source layer {layer_id} is blank")
        geo_bounds = layer.get("geo_bounds", {})
        if geo_bounds:
            width = float(geo_bounds["max_longitude"]) - float(geo_bounds["min_longitude"])
            height = float(geo_bounds["max_latitude"]) - float(geo_bounds["min_latitude"])
            if width <= 0.10 or height <= 0.10:
                errors.append(f"massif source layer {layer_id} geo bounds are too small")
    return errors


def _audit_massif_source_layer_metadata(errors, layer, asset_contract, render_scale):
    layer_id = layer.get("id", "")
    required_fields = asset_contract.get(
        "required_layer_metadata",
        ["id", "image", "source_extent_id", "source_type", "geo_bounds", "render_bbox_px", "map_bbox_px", "cropped_size_px"],
    )
    for field in required_fields:
        if field not in layer:
            errors.append(f"massif source layer {layer_id} must declare {field}")

    image_name = layer.get("image", "")
    forbidden_images = set(asset_contract.get("forbidden_image_names", []))
    if image_name in forbidden_images or os.path.basename(image_name) != image_name:
        errors.append(f"massif source layer {layer_id} must use its own source layer PNG, not {image_name}")
    elif layer_id and image_name != f"{layer_id}.png":
        errors.append(f"massif source layer {layer_id} image must be named {layer_id}.png")

    if layer.get("source_type") not in {"relief_region", "massif_segment"}:
        errors.append(f"massif source layer {layer_id} has unknown source_type")

    render_bbox = layer.get("render_bbox_px")
    map_bbox = layer.get("map_bbox_px")
    cropped_size = layer.get("cropped_size_px")
    if not _is_numeric_list(render_bbox, 4):
        errors.append(f"massif source layer {layer_id} must declare a 4-value render_bbox_px")
        render_bbox = None
    if not _is_numeric_list(map_bbox, 4):
        errors.append(f"massif source layer {layer_id} must declare a 4-value map_bbox_px")
        map_bbox = None
    if not _is_numeric_list(cropped_size, 2):
        errors.append(f"massif source layer {layer_id} must declare a 2-value cropped_size_px")
        cropped_size = None

    if render_bbox:
        render_width = render_bbox[2] - render_bbox[0]
        render_height = render_bbox[3] - render_bbox[1]
        if render_width <= 0 or render_height <= 0:
            errors.append(f"massif source layer {layer_id} render_bbox_px must have positive size")
        if cropped_size and [int(render_width), int(render_height)] != [int(cropped_size[0]), int(cropped_size[1])]:
            errors.append(f"massif source layer {layer_id} cropped_size_px must match render_bbox_px size")

    if render_bbox and map_bbox and isinstance(render_scale, (int, float)) and render_scale > 0:
        expected_map_bbox = [value / render_scale for value in render_bbox]
        for expected, actual in zip(expected_map_bbox, map_bbox):
            if abs(float(actual) - expected) > 0.51:
                errors.append(f"massif source layer {layer_id} map_bbox_px must match render_bbox_px/render_scale")
                break

    geo_bounds = layer.get("geo_bounds")
    required_geo_keys = {"min_longitude", "max_longitude", "min_latitude", "max_latitude"}
    if not isinstance(geo_bounds, dict) or set(geo_bounds) < required_geo_keys:
        errors.append(f"massif source layer {layer_id} must declare complete geo_bounds")
    elif (
        float(geo_bounds["min_longitude"]) >= float(geo_bounds["max_longitude"])
        or float(geo_bounds["min_latitude"]) >= float(geo_bounds["max_latitude"])
    ):
        errors.append(f"massif source layer {layer_id} geo_bounds must have positive size")


def _is_numeric_list(values, length):
    return (
        isinstance(values, list)
        and len(values) == length
        and all(isinstance(value, (int, float)) for value in values)
    )


def audit_terrain_massif_layer_contract():
    errors = []
    contract = _load_terrain_massif_contract()
    if not contract:
        return [f"terrain massif layer contract is missing: {TERRAIN_MASSIF_LAYERS_PATH}"]

    if contract.get("schema") != "cable-world.terrain-massif-layers.v1":
        errors.append("terrain massif layer contract has an unknown schema")

    production_asset_contract = contract.get("production_asset_contract", {})
    if production_asset_contract.get("manifest_schema") != "cable-world.massif-source-layers.v1":
        errors.append("terrain massif production asset contract must name the massif manifest schema")
    if production_asset_contract.get("asset_policy") != "one_png_and_one_json_sidecar_per_massif_or_source_layer":
        errors.append("terrain massif production asset contract must require one PNG and one JSON sidecar per layer")
    if production_asset_contract.get("bbox_policy") and "render_bbox_px" not in production_asset_contract.get("bbox_policy", ""):
        errors.append("terrain massif production asset contract must require render/map/geo bbox metadata")
    required_metadata = set(production_asset_contract.get("required_layer_metadata", []))
    for field in ("source_extent_id", "source_type", "geo_bounds", "render_bbox_px", "map_bbox_px", "cropped_size_px"):
        if field not in required_metadata:
            errors.append(f"terrain massif production asset contract must require {field}")

    forbidden_policy = set(contract.get("placement_policy", {}).get("forbidden", []))
    required_forbidden = {"hash_random_mountain_stamp", "decorative_anchor_only", "full_map_generated_bitmap"}
    missing_forbidden = sorted(required_forbidden - forbidden_policy)
    for policy in missing_forbidden:
        errors.append(f"terrain massif placement policy must forbid {policy}")

    exported_regions = {
        region["id"]: region
        for region in RELIEF_REGIONS
        if _should_export_relief_region_source_layer(region)
    }
    source_layers = {layer.get("id"): layer for layer in contract.get("source_layers", [])}
    missing_layers = sorted(set(exported_regions) - set(source_layers))
    extra_layers = sorted(set(source_layers) - set(exported_regions))
    for layer_id in missing_layers:
        errors.append(f"terrain source layer contract is missing exported relief region {layer_id}")
    for layer_id in extra_layers:
        errors.append(f"terrain source layer contract has unknown relief region {layer_id}")

    alpine_segment_ids = {segment["id"] for segment in ALPINE_MASSIF_SEGMENTS}
    for layer_id, layer in source_layers.items():
        region = exported_regions.get(layer_id)
        if region is None:
            continue
        if layer.get("region_id") != layer_id:
            errors.append(f"terrain source layer {layer_id} must point at its matching region_id")
        if layer.get("production_asset_id") != layer_id:
            errors.append(f"terrain source layer {layer_id} must declare matching production_asset_id")
        if layer.get("asset_role") not in {"composite_source_layer", "named_massif_source_layer"}:
            errors.append(f"terrain source layer {layer_id} must declare a production asset_role")
        if not layer.get("source_extent_id"):
            errors.append(f"terrain source layer {layer_id} must declare source_extent_id")
        if layer.get("placement_policy") in forbidden_policy:
            errors.append(f"terrain source layer {layer_id} uses forbidden placement policy")
        if not layer.get("source_confidence"):
            errors.append(f"terrain source layer {layer_id} must declare source_confidence")
        if not layer.get("replacement_status"):
            errors.append(f"terrain source layer {layer_id} must declare replacement_status")

        if region.get("mountains"):
            errors.append(f"terrain source layer {layer_id} must not use legacy generic mountains list")

        required_ridge_bands = set(layer.get("required_ridge_bands", []))
        actual_ridge_bands = {ridge_band["id"] for ridge_band in region.get("ridge_bands", [])}
        for ridge_band_id in sorted(required_ridge_bands - actual_ridge_bands):
            errors.append(f"terrain source layer {layer_id} is missing ridge band {ridge_band_id}")

        actual_glyphs = [glyph_name for glyph_name, _lon, _lat, _width in region.get("mountain_glyphs", [])]
        allowed_glyphs = set(layer.get("allowed_glyphs", []))
        allowed_prefixes = tuple(layer.get("allowed_glyph_prefixes", []))
        if allowed_glyphs or allowed_prefixes:
            for glyph_name in actual_glyphs:
                if glyph_name not in allowed_glyphs and not glyph_name.startswith(allowed_prefixes):
                    errors.append(f"terrain source layer {layer_id} uses glyph outside contract: {glyph_name}")
        elif actual_glyphs:
            errors.append(f"terrain source layer {layer_id} defines glyph anchors but contract allows none")

        for child_id in layer.get("required_child_layers", []):
            if child_id not in alpine_segment_ids:
                errors.append(f"terrain source layer {layer_id} requires unknown child massif {child_id}")

    if os.path.exists(MASSIF_MANIFEST_PATH):
        with open(MASSIF_MANIFEST_PATH, "r", encoding="utf-8") as file:
            manifest = json.load(file)
        manifest_layers = {layer.get("id"): layer for layer in manifest.get("layers", [])}
        for layer_id, contract_layer in source_layers.items():
            manifest_layer = manifest_layers.get(layer_id)
            if not manifest_layer:
                errors.append(f"terrain source layer {layer_id} is missing from massif manifest")
                continue
            if manifest_layer.get("source_extent_id") != contract_layer.get("source_extent_id"):
                errors.append(f"terrain source layer {layer_id} manifest source_extent_id does not match contract")
            if manifest_layer.get("replacement_status") != contract_layer.get("replacement_status"):
                errors.append(f"terrain source layer {layer_id} manifest replacement_status does not match contract")
    return errors


def _load_terrain_massif_contract():
    if not os.path.exists(TERRAIN_MASSIF_LAYERS_PATH):
        return {}
    with open(TERRAIN_MASSIF_LAYERS_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def _expected_source_layer_ids():
    ids = {segment["id"] for segment in ALPINE_MASSIF_SEGMENTS}
    ids.update(region["id"] for region in RELIEF_REGIONS if _should_export_relief_region_source_layer(region))
    return ids


def _runtime_map_base_size_for_viewport(viewport_size):
    viewport_width, viewport_height = viewport_size
    aspect = MAP_SIZE[0] / MAP_SIZE[1]
    viewport_aspect = viewport_width / viewport_height
    if viewport_aspect > aspect:
        return (viewport_width, viewport_width / aspect)
    return (viewport_height * aspect, viewport_height)


def _audit_point(errors, bounds_poly, lon, lat, label):
    if not bounds_poly.covers(Point(lon, lat)):
        errors.append(f"{label} point ({lon}, {lat}) is outside map bounds")


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
            _draw_geometry(draw, row.geometry, proj, NEIGHBOR_LAND, BORDER, COUNTRY_NEIGHBOR_BORDER_WIDTH * RENDER_SCALE)

    germany = countries[countries["ADMIN"] == "Germany"].iloc[0].geometry
    _draw_geometry(draw, germany, proj, GERMANY_LAND, GERMANY_EDGE, COUNTRY_GERMANY_EDGE_WIDTH * RENDER_SCALE)

    mask = Image.new("L", canvas.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    _draw_geometry(mask_draw, germany, proj, 255)

    land_mask = Image.new("L", canvas.size, 0)
    land_mask_draw = ImageDraw.Draw(land_mask)
    for _, row in countries.iterrows():
        _draw_geometry(land_mask_draw, row.geometry, proj, 255)
    return germany, mask, land_mask


def _draw_base_land_texture(canvas, land_mask, germany_mask):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    width, height = canvas.size

    if DEFAULT_BASE_LAND_PATCHES_ENABLED:
        for y in range(0, height, 96 * RENDER_SCALE):
            for x in range(0, width, 112 * RENDER_SCALE):
                seed = _stable_hash("land_patch", x // RENDER_SCALE, y // RENDER_SCALE)
                patch_w = (74 + seed % 58) * RENDER_SCALE
                patch_h = (30 + (seed >> 6) % 34) * RENDER_SCALE
                jitter_x = ((seed >> 12) % 43 - 21) * RENDER_SCALE
                jitter_y = ((seed >> 18) % 37 - 18) * RENDER_SCALE
                if seed % 4 == 0:
                    color = (126, 142, 73, 8)
                elif seed % 4 == 1:
                    color = (174, 160, 90, 5)
                elif seed % 4 == 2:
                    color = (82, 123, 66, 6)
                else:
                    color = (105, 93, 55, 4)
                draw.ellipse(
                    (
                        x + jitter_x - patch_w // 2,
                        y + jitter_y - patch_h // 2,
                        x + jitter_x + patch_w // 2,
                        y + jitter_y + patch_h // 2,
                    ),
                    fill=color,
                )

    for y in range(0, height, 42 * RENDER_SCALE):
        for x in range(0, width, 46 * RENDER_SCALE):
            seed = _stable_hash("land_texture", x // RENDER_SCALE, y // RENDER_SCALE)
            alpha = 3 + seed % 3
            if seed % 5 == 0:
                color = (219, 203, 132, alpha)
            elif seed % 5 in (1, 2):
                color = (78, 112, 62, alpha)
            else:
                color = (91, 84, 50, alpha)
            jitter_x = ((seed >> 8) % 17 - 8) * RENDER_SCALE
            jitter_y = ((seed >> 16) % 17 - 8) * RENDER_SCALE
            if seed % 3 == 0:
                patch_w = (24 + (seed >> 21) % 12) * RENDER_SCALE
                patch_h = (10 + (seed >> 25) % 6) * RENDER_SCALE
                draw.arc(
                    (
                        x + jitter_x - patch_w,
                        y + jitter_y - patch_h,
                        x + jitter_x + patch_w,
                        y + jitter_y + patch_h,
                    ),
                    215,
                    330,
                    fill=color,
                    width=max(1, RENDER_SCALE),
                )
            else:
                rr = (6 + seed % 5) * RENDER_SCALE
                draw.arc(
                    (
                        x + jitter_x - rr,
                        y + jitter_y - rr // 2,
                        x + jitter_x + rr,
                        y + jitter_y + rr // 2,
                    ),
                    205,
                    330,
                    fill=color,
                    width=max(1, RENDER_SCALE),
                )

    for y in range(0, height, 72 * RENDER_SCALE):
        x_offset = ((y // (72 * RENDER_SCALE)) % 2) * 36 * RENDER_SCALE
        for x in range(x_offset, width, 112 * RENDER_SCALE):
            draw.arc(
                (x, y, x + 30 * RENDER_SCALE, y + 11 * RENDER_SCALE),
                195,
                340,
                fill=(73, 91, 52, 12),
                width=max(1, RENDER_SCALE),
            )

    alpha = Image.composite(layer.getchannel("A"), Image.new("L", canvas.size, 0), land_mask)
    layer.putalpha(alpha)
    canvas.alpha_composite(layer)


def _draw_base_water_texture(canvas, water_mask):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    width, height = canvas.size

    for y in range(0, height, 28 * RENDER_SCALE):
        x_offset = ((y // (28 * RENDER_SCALE)) % 2) * 24 * RENDER_SCALE
        for x in range(x_offset, width, 58 * RENDER_SCALE):
            seed = _stable_hash("water_texture", x // RENDER_SCALE, y // RENDER_SCALE)
            arc_width = (18 + seed % 16) * RENDER_SCALE
            arc_height = (7 + seed % 5) * RENDER_SCALE
            alpha = 34 + seed % 34
            draw.arc(
                (x, y, x + arc_width, y + arc_height),
                195,
                345,
                fill=(107, 158, 160, alpha),
                width=max(1, RENDER_SCALE),
            )

    alpha = Image.composite(layer.getchannel("A"), Image.new("L", canvas.size, 0), water_mask)
    layer.putalpha(alpha)
    canvas.alpha_composite(layer)


def _draw_country_border_overlay(canvas, proj, germany_geom):
    # The base country layer already outlines Germany. A second overlay reads as
    # a technical route stroke near Dresden/Erzgebirge, so keep this pass inert.
    return


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
        draw.line(pts, fill=(38, 68, 70, 138), width=8 * RENDER_SCALE, joint="curve")
        draw.line(pts, fill=(53, 116, 126, 204), width=4 * RENDER_SCALE, joint="curve")
        draw.line(pts, fill=(135, 184, 176, 128), width=max(1, RENDER_SCALE), joint="curve")

    for water_body in NAMED_WATER_BODIES:
        _draw_named_water_body(draw, proj, water_body)

    canvas.alpha_composite(layer)


def _draw_named_water_bodies(canvas, proj, germany_mask):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for water_body in NAMED_WATER_BODIES:
        _draw_named_water_body(draw, proj, water_body)
    alpha = Image.composite(layer.getchannel("A"), Image.new("L", canvas.size, 0), germany_mask)
    layer.putalpha(alpha)
    canvas.alpha_composite(layer)


def _draw_named_water_body(draw, proj, water_body):
    if (
        not DEFAULT_MINOR_NAMED_WATER_BODIES_ENABLED
        and water_body.get("id") not in MAJOR_NAMED_WATER_BODY_IDS
    ):
        return
    pts = _smooth_closed_points([_project_point(proj, lon, lat) for lon, lat in water_body["points"]])
    if len(pts) < 3:
        return
    alpha_scale = _named_water_alpha_scale(water_body)
    shore = _scale_alpha(NAMED_WATER_SHORE, alpha_scale)
    fill = _scale_alpha(NAMED_WATER_FILL, alpha_scale)
    shallow = _scale_alpha(NAMED_WATER_SHALLOW, alpha_scale)
    outline = _scale_alpha(NAMED_WATER_OUTLINE, alpha_scale)
    highlight = _scale_alpha(NAMED_WATER_HIGHLIGHT, alpha_scale)
    draw.line(pts + [pts[0]], fill=shore, width=max(2, RENDER_SCALE * 4), joint="curve")
    draw.polygon(pts, fill=fill)
    draw.line(pts + [pts[0]], fill=shallow, width=max(1, RENDER_SCALE * 2), joint="curve")
    draw.line(pts + [pts[0]], fill=outline, width=max(1, RENDER_SCALE), joint="curve")

    min_x = min(x for x, _ in pts)
    max_x = max(x for x, _ in pts)
    min_y = min(y for _, y in pts)
    max_y = max(y for _, y in pts)
    width = max(1, max_x - min_x)
    height = max(1, max_y - min_y)
    wave_count = max(1, min(4, width // (20 * RENDER_SCALE)))
    for index in range(wave_count):
        wave_x = min_x + int(width * (0.24 + index * 0.18))
        wave_y = min_y + int(height * (0.42 + (index % 2) * 0.18))
        draw.arc(
            (
                wave_x - 8 * RENDER_SCALE,
                wave_y - 3 * RENDER_SCALE,
                wave_x + 8 * RENDER_SCALE,
                wave_y + 5 * RENDER_SCALE,
            ),
            190,
            350,
            fill=highlight,
            width=max(1, RENDER_SCALE),
        )


def _named_water_alpha_scale(water_body):
    if water_body.get("id") in MAJOR_NAMED_WATER_BODY_IDS:
        return 1.0
    if water_body.get("subtle", False):
        return 0.12
    return 0.18


def _scale_alpha(color, scale):
    return (color[0], color[1], color[2], int(round(color[3] * scale)))


def _smooth_closed_points(points, subdivisions=6):
    if len(points) < 4:
        return points
    smoothed = []
    count = len(points)
    for index in range(count):
        p0 = points[(index - 1) % count]
        p1 = points[index]
        p2 = points[(index + 1) % count]
        p3 = points[(index + 2) % count]
        for step in range(subdivisions):
            t = step / subdivisions
            t2 = t * t
            t3 = t2 * t
            x = 0.5 * (
                2 * p1[0]
                + (-p0[0] + p2[0]) * t
                + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
            )
            y = 0.5 * (
                2 * p1[1]
                + (-p0[1] + p2[1]) * t
                + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
            )
            smoothed.append((int(round(x)), int(round(y))))
    return smoothed


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
            _scale_alpha(region["fill"], RELIEF_SOFT_REGION_ALPHA_SCALE),
            blur=region["blur"],
        )

    decor = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    for region in RELIEF_REGIONS:
        region_layer = _render_relief_region_decor_layer(canvas.size, proj, region)
        if _should_export_relief_region_source_layer(region):
            _save_relief_region_source_layer(region_layer, region, proj)
        decor.alpha_composite(region_layer)
    draw = ImageDraw.Draw(decor)
    if BAKED_TOWN_DETAILS_ENABLED:
        for lon, lat, size in BAKED_TOWN_DETAILS:
            _draw_town(draw, proj, lon, lat, size)
    if DEFAULT_MARSH_PATCHES_ENABLED:
        for lon, lat, size in [
            (8.7, 53.4, 38), (11.6, 53.8, 34), (13.0, 54.0, 30),
            (12.3, 53.3, 34), (9.8, 54.1, 28), (14.1, 52.0, 30),
            (13.8, 51.85, 28),
        ]:
            _draw_marsh_patch(draw, proj, lon, lat, size)

    canvas.alpha_composite(decor)


def _render_relief_region_decor_layer(size, proj, region):
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for lon, lat, tree_size in region.get("trees", []):
        _draw_tree_cluster(layer, proj, lon, lat, tree_size)
    for ridge_band in region.get("ridge_bands", []):
        _draw_alpine_ridge_band(layer, proj, ridge_band)
    for massif_segment in region.get("massif_segments", []):
        _draw_alpine_massif_segment(layer, proj, massif_segment)
    for glyph_name, lon, lat, width in region.get("mountain_glyphs", []):
        _draw_glyph_center(layer, proj, glyph_name, lon, lat, width)
    for lon, lat, mountain_size in region.get("mountains", []):
        _draw_mountains(layer, draw, proj, lon, lat, mountain_size, region.get("glyph", "alpine"))
    return layer


def _should_export_relief_region_source_layer(region):
    if region["id"] == "northern_lowlands":
        return False
    return any(
        region.get(key)
        for key in ("trees", "ridge_bands", "massif_segments", "mountain_glyphs", "mountains")
    )


def _draw_atlas_details(canvas, proj):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    for detail in ATLAS_DETAILS:
        if detail["kind"] not in DEFAULT_ATLAS_DETAIL_KINDS:
            continue
        kind_scale = ATLAS_DETAIL_KIND_SCALE.get(detail["kind"], 1.0)
        target_width = max(MIN_ATLAS_DETAIL_WIDTH, detail["width"] * kind_scale)
        _draw_glyph_center(
            layer,
            proj,
            detail["glyph"],
            detail["lon"],
            detail["lat"],
            target_width,
        )
    canvas.alpha_composite(layer)


def _draw_atlas_forest_masses(canvas, proj, land_mask):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    for mass in ATLAS_FOREST_MASSES:
        for glyph_name, lon, lat, width in mass["clusters"]:
            display_width = max(FOREST_MASS_MIN_WIDTH, int(width * FOREST_MASS_VISUAL_SCALE))
            _draw_glyph_center(layer, proj, glyph_name, lon, lat, display_width)
    alpha = Image.composite(layer.getchannel("A"), Image.new("L", canvas.size, 0), land_mask)
    layer.putalpha(alpha)
    canvas.alpha_composite(layer)


def _draw_atlas_land_detail_patches(canvas, proj, germany_mask):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    for glyph_name, lon, lat, width in ATLAS_LAND_DETAIL_PATCHES:
        _draw_glyph_center(layer, proj, glyph_name, lon, lat, width * LAND_DETAIL_VISUAL_SCALE)
    layer = _blend_land_detail_layer(layer)
    alpha = Image.composite(layer.getchannel("A"), Image.new("L", canvas.size, 0), germany_mask)
    layer.putalpha(alpha)
    canvas.alpha_composite(layer)


def _blend_land_detail_layer(layer):
    alpha = layer.getchannel("A")
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.9 * RENDER_SCALE))
    alpha = alpha.point(lambda value: int(value * LAND_DETAIL_ALPHA_SCALE))
    tinted_rgb = Image.blend(
        layer.convert("RGB"),
        Image.new("RGB", layer.size, (151, 154, 86)),
        LAND_DETAIL_TINT_STRENGTH,
    )
    blended = tinted_rgb.convert("RGBA")
    blended.putalpha(alpha)
    return blended


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
            jitter_lon = ((seed & 255) / 255.0 - 0.5) * 0.26
            jitter_lat = (((seed >> 8) & 255) / 255.0 - 0.5) * 0.22
            point_lon = lon + jitter_lon
            point_lat = lat + jitter_lat
            if germany_geom.contains(Point(point_lon, point_lat)):
                x, y = _project_point(proj, point_lon, point_lat)
                kind = seed % 9
                if kind in (0, 1, 2):
                    color = (76, 112, 62, 22) if point_lat < 52.0 else (91, 111, 66, 18)
                    _draw_tuft(draw, x, y, 26 + seed % 12, color)
                elif kind in (3, 4, 5) and point_lat < 51.8:
                    _draw_hill_mark(draw, x, y, 34 + seed % 16, (113, 100, 73, 20))
                elif kind == 6:
                    _draw_hill_mark(draw, x, y, 30 + seed % 11, (70, 103, 77, 14))
                else:
                    _draw_tuft(draw, x, y, 25 + seed % 10, (87, 110, 68, 14))
            lat += GROUND_TEXTURE_LAT_STEP
            lat_index += 1
        lon += GROUND_TEXTURE_LON_STEP
        lon_index += 1

    alpha = Image.composite(layer.getchannel("A"), Image.new("L", canvas.size, 0), germany_mask)
    layer.putalpha(alpha)
    canvas.alpha_composite(layer)


def _draw_integrated_land_pattern(canvas, proj, germany_mask, germany_geom):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    lon = 4.85
    lon_index = 0
    while lon <= 15.35:
        lat = 46.75
        lat_index = 0
        while lat <= 55.35:
            seed = _stable_hash("integrated_land_pattern", lon_index, lat_index)
            jitter_lon = ((seed & 255) / 255.0 - 0.5) * 0.16
            jitter_lat = (((seed >> 8) & 255) / 255.0 - 0.5) * 0.14
            point_lon = lon + jitter_lon
            point_lat = lat + jitter_lat
            if germany_geom.contains(Point(point_lon, point_lat)):
                x, y = _project_point(proj, point_lon, point_lat)
                kind = seed % 12
                size = INTEGRATED_LAND_PATTERN_MIN_SIZE + ((seed >> 16) % 15)
                if point_lat > 52.2 and kind in (3, 4, 8):
                    kind = 1
                if point_lat < 48.7 and kind in (0, 1, 2):
                    kind = 6
                _draw_land_pattern_mark(draw, x, y, size, kind, seed)
            lat += INTEGRATED_LAND_PATTERN_LAT_STEP
            lat_index += 1
        lon += INTEGRATED_LAND_PATTERN_LON_STEP
        lon_index += 1

    alpha = layer.getchannel("A")
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.25 * RENDER_SCALE))
    alpha = alpha.point(lambda value: int(value * INTEGRATED_LAND_PATTERN_ALPHA_SCALE))
    alpha = Image.composite(alpha, Image.new("L", canvas.size, 0), germany_mask)
    layer.putalpha(alpha)
    canvas.alpha_composite(layer)


def _draw_land_pattern_mark(draw, x, y, size, kind, seed):
    s = size * RENDER_SCALE
    line_width = max(1, RENDER_SCALE)
    warm_grass = (88, 112, 63, 22)
    dry_grass = (150, 136, 78, 14)
    earth = (104, 91, 57, 14)
    shadow_green = (61, 93, 55, 14)

    if kind in (0, 1, 2):
        color = warm_grass if kind != 2 else shadow_green
        for offset in (-1, 0, 1):
            ox = offset * s // 3
            draw.arc(
                (x + ox - s // 2, y - s // 3, x + ox + s // 2, y + s // 2),
                215,
                330,
                fill=color,
                width=line_width,
            )
    elif kind in (3, 4):
        color = dry_grass if kind == 3 else earth
        for offset in range(-1, 2):
            yy = y + offset * s // 4
            draw.line(
                (x - s // 2, yy, x + s // 2, yy + s // 5),
                fill=color,
                width=line_width,
            )
    elif kind in (5, 6, 7):
        color = earth if kind != 5 else dry_grass
        draw.arc((x - s, y - s // 2, x + s, y + s // 2), 205, 335, fill=color, width=line_width)
        if seed % 3 != 0:
            draw.arc(
                (x - s // 2, y - s // 4, x + s // 2, y + s // 3),
                205,
                335,
                fill=(76, 103, 61, 10),
                width=line_width,
            )
    elif kind in (8, 9):
        color = (92, 96, 64, 12)
        draw.arc((x - s, y - s // 3, x + s, y + s // 2), 205, 335, fill=color, width=line_width)
    else:
        color = (72, 105, 60, 12)
        draw.line((x, y - s // 2, x - s // 2, y + s // 2), fill=color, width=line_width)
        draw.line((x, y - s // 2, x + s // 2, y + s // 2), fill=color, width=line_width)


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
    _draw_glyph_at(canvas, glyph, x, y, _relief_tree_cluster_width(radius))


def _relief_tree_cluster_width(radius):
    return max(RELIEF_TREE_CLUSTER_MIN_WIDTH, radius * 2.0)


def _draw_alpine_ridge_band(canvas, proj, ridge_band):
    if not DEFAULT_RIDGE_BAND_OVERLAYS_ENABLED:
        return
    points = [_project_point(proj, lon, lat) for lon, lat in ridge_band["points"]]
    if len(points) < 2:
        return

    ridge_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(ridge_layer)
    height = int(ridge_band.get("height", 72) * RENDER_SCALE)
    style = ridge_band.get("style", "alpine")
    if style == "forested":
        fill = (45, 87, 51, 66)
        core = (55, 78, 48, 104)
        highlight = (137, 132, 76, 72)
        shadow = (32, 63, 43, 62)
        mark_color = (47, 45, 29, 76)
    elif style == "border":
        fill = (54, 83, 54, 72)
        core = (68, 74, 51, 112)
        highlight = (151, 135, 83, 78)
        shadow = (36, 61, 45, 70)
        mark_color = (52, 45, 32, 86)
    elif style == "sandstone":
        fill = (83, 93, 62, 58)
        core = (96, 88, 58, 100)
        highlight = (171, 139, 82, 80)
        shadow = (53, 61, 43, 58)
        mark_color = (73, 51, 36, 78)
    elif style == "low":
        fill = (58, 91, 52, 48)
        core = (80, 91, 55, 82)
        highlight = (145, 132, 83, 58)
        shadow = (41, 69, 44, 48)
        mark_color = (56, 49, 34, 58)
    else:
        fill = (56, 86, 55, 42)
        core = (74, 75, 49, 92)
        highlight = (134, 124, 74, 66)
        shadow = (39, 67, 48, 42)
        mark_color = (54, 48, 33, 76)
    lower_points = [(x, y + int(height * 0.58)) for x, y in reversed(points)]
    upper_points = [(x, y - int(height * 0.32)) for x, y in points]
    band_polygon = upper_points + lower_points
    draw.polygon(band_polygon, fill=fill)
    draw.line(points, fill=core, width=max(2, int(height * 0.34)), joint="curve")
    draw.line([(x, y - int(height * 0.12)) for x, y in points], fill=highlight, width=max(2, int(height * 0.12)), joint="curve")
    draw.line([(x, y + int(height * 0.40)) for x, y in points], fill=shadow, width=max(2, int(height * 0.20)), joint="curve")

    step = max(18 * RENDER_SCALE, int(ridge_band.get("step", 44) * RENDER_SCALE))
    for start, end in zip(points, points[1:]):
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        segment_length = max(1.0, math.hypot(dx, dy))
        count = max(1, int(segment_length / step))
        normal_x = -dy / segment_length
        normal_y = dx / segment_length
        for index in range(count):
            t = (index + 0.35) / count
            cx = start[0] + dx * t
            cy = start[1] + dy * t
            mark = int(height * (0.10 + 0.02 * ((index + count) % 3)))
            left = (int(cx - dx / segment_length * mark * 0.95), int(cy - dy / segment_length * mark * 0.95))
            peak = (int(cx - normal_x * mark * 1.35), int(cy - normal_y * mark * 1.35))
            right = (int(cx + dx / segment_length * mark * 0.95), int(cy + dy / segment_length * mark * 0.95))
            draw.line([left, peak, right], fill=mark_color, width=max(1, RENDER_SCALE), joint="curve")

    ridge_layer = ridge_layer.filter(ImageFilter.GaussianBlur(0.30 * RENDER_SCALE))
    alpha = ridge_layer.getchannel("A")
    alpha = alpha.point(lambda value: int(value * RIDGE_BAND_ALPHA_SCALE))
    ridge_layer.putalpha(alpha)
    canvas.alpha_composite(ridge_layer)


def _draw_alpine_massif_segment(canvas, proj, segment):
    massif_layer = _render_alpine_massif_segment_layer(canvas.size, proj, segment)
    if EXPORT_MASSIF_SOURCE_LAYERS:
        _save_massif_source_layer(massif_layer, segment, proj)
    canvas.alpha_composite(massif_layer)


def _render_alpine_massif_segment_layer(size, proj, segment):
    massif_layer = Image.new("RGBA", size, (0, 0, 0, 0))

    shadow_points = [_project_point(proj, lon, lat) for lon, lat in segment.get("shadow", [])]
    if len(shadow_points) >= 3:
        shadow_layer = Image.new("RGBA", size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_layer)
        shadow_draw.polygon(shadow_points, fill=(47, 75, 45, 52))
        shadow_draw.line(shadow_points + [shadow_points[0]], fill=(108, 113, 68, 46), width=4 * RENDER_SCALE, joint="curve")
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(6 * RENDER_SCALE))
        massif_layer.alpha_composite(shadow_layer)

    arc_points = [_project_point(proj, lon, lat) for lon, lat in segment.get("arc", [])]
    if len(arc_points) >= 2:
        line_layer = Image.new("RGBA", size, (0, 0, 0, 0))
        line_draw = ImageDraw.Draw(line_layer)
        line_draw.line(arc_points, fill=(43, 59, 40, 82), width=8 * RENDER_SCALE, joint="curve")
        line_draw.line([(x, y - 5 * RENDER_SCALE) for x, y in arc_points], fill=(180, 168, 112, 62), width=3 * RENDER_SCALE, joint="curve")
        _draw_massif_crest_peaks(line_draw, arc_points, segment["id"])
        line_layer = line_layer.filter(ImageFilter.GaussianBlur(1.2 * RENDER_SCALE))
        massif_layer.alpha_composite(line_layer)

    for glyph_name, lon, lat, width, y_offset in segment.get("glyphs", []):
        x, y = _project_point(proj, lon, lat)
        _draw_glyph_at(massif_layer, glyph_name, x, y + int(float(y_offset) * width * RENDER_SCALE), width)
    return massif_layer


def _draw_massif_crest_peaks(draw, arc_points, segment_id):
    for segment_index, (start, end) in enumerate(zip(arc_points, arc_points[1:])):
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        segment_length = max(1.0, math.hypot(dx, dy))
        tangent_x = dx / segment_length
        tangent_y = dy / segment_length
        normal_x = -dy / segment_length
        normal_y = dx / segment_length
        if normal_y < 0.0:
            normal_x *= -1.0
            normal_y *= -1.0
        step = 30 * RENDER_SCALE
        count = max(2, int(segment_length / step))
        for peak_index in range(count):
            seed = _stable_hash("massif_crest", segment_id, segment_index, peak_index)
            t = (peak_index + 0.5) / count
            cx = start[0] + dx * t
            cy = start[1] + dy * t
            half_width = (14 + seed % 10) * RENDER_SCALE
            height = (18 + (seed >> 5) % 14) * RENDER_SCALE
            base_y_shift = (3 + (seed >> 10) % 6) * RENDER_SCALE
            left = (
                int(cx - tangent_x * half_width + normal_x * base_y_shift),
                int(cy - tangent_y * half_width + normal_y * base_y_shift),
            )
            right = (
                int(cx + tangent_x * half_width + normal_x * base_y_shift),
                int(cy + tangent_y * half_width + normal_y * base_y_shift),
            )
            peak = (
                int(cx - normal_x * height),
                int(cy - normal_y * height),
            )
            snow_left = (
                int(cx - tangent_x * half_width * 0.34 - normal_x * height * 0.30),
                int(cy - tangent_y * half_width * 0.34 - normal_y * height * 0.30),
            )
            snow_right = (
                int(cx + tangent_x * half_width * 0.28 - normal_x * height * 0.26),
                int(cy + tangent_y * half_width * 0.28 - normal_y * height * 0.26),
            )
            draw.polygon([left, peak, right], fill=(86, 79, 54, 118))
            draw.line([left, peak, right], fill=(42, 37, 26, 126), width=max(1, RENDER_SCALE), joint="curve")
            draw.polygon([peak, snow_left, snow_right], fill=(224, 213, 165, 142))


def _save_massif_source_layer(layer, segment, proj):
    bbox = layer.getbbox()
    if bbox is None:
        return
    os.makedirs(MASSIF_DIR, exist_ok=True)
    cropped = layer.crop(bbox)
    image_name = f"{segment['id']}.png"
    metadata_name = f"{segment['id']}.json"
    cropped.save(os.path.join(MASSIF_DIR, image_name), optimize=True)

    metadata = _massif_source_metadata(segment, image_name, bbox, cropped.size, proj)
    with open(os.path.join(MASSIF_DIR, metadata_name), "w", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=2, sort_keys=True)
        file.write("\n")
    MASSIF_SOURCE_MANIFEST.append(metadata)


def _save_relief_region_source_layer(layer, region, proj):
    bbox = layer.getbbox()
    if bbox is None:
        return
    os.makedirs(MASSIF_DIR, exist_ok=True)
    cropped = layer.crop(bbox)
    image_name = f"{region['id']}.png"
    metadata_name = f"{region['id']}.json"
    cropped.save(os.path.join(MASSIF_DIR, image_name), optimize=True)

    metadata = _relief_region_source_metadata(region, image_name, bbox, cropped.size, proj)
    with open(os.path.join(MASSIF_DIR, metadata_name), "w", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=2, sort_keys=True)
        file.write("\n")
    MASSIF_SOURCE_MANIFEST.append(metadata)


def _massif_source_metadata(segment, image_name, render_bbox, cropped_size, proj):
    left, top, right, bottom = render_bbox
    map_bbox = [value / RENDER_SCALE for value in render_bbox]
    west, north = proj.inverse(map_bbox[0], map_bbox[1])
    east, south = proj.inverse(map_bbox[2], map_bbox[3])
    return {
        "id": segment["id"],
        "label": segment["label"],
        "source_extent_id": segment.get("source_extent_id", segment["id"]),
        "source_type": "massif_segment",
        "image": image_name,
        "render_bbox_px": [int(value) for value in render_bbox],
        "map_bbox_px": [round(value, 2) for value in map_bbox],
        "cropped_size_px": [int(cropped_size[0]), int(cropped_size[1])],
        "geo_bounds": {
            "min_longitude": round(min(west, east), 5),
            "max_longitude": round(max(west, east), 5),
            "min_latitude": round(min(south, north), 5),
            "max_latitude": round(max(south, north), 5),
        },
        "arc": [{"longitude": lon, "latitude": lat} for lon, lat in segment.get("arc", [])],
        "shadow": [{"longitude": lon, "latitude": lat} for lon, lat in segment.get("shadow", [])],
        "glyphs": [
            {
                "glyph": glyph_name,
                "longitude": lon,
                "latitude": lat,
                "width": width,
                "y_offset": y_offset,
            }
            for glyph_name, lon, lat, width, y_offset in segment.get("glyphs", [])
        ],
        "required_country_overlap": segment.get("required_country_overlap", ""),
    }


def _relief_region_source_metadata(region, image_name, render_bbox, cropped_size, proj):
    contract_layer = _terrain_massif_contract_layers().get(region["id"], {})
    metadata = _source_layer_base_metadata(region, image_name, render_bbox, cropped_size, proj)
    metadata.update(
        {
            "source_extent_id": contract_layer.get("source_extent_id", region["id"]),
            "source_type": "relief_region",
            "kind": region.get("kind", ""),
            "placement_policy": contract_layer.get("placement_policy", "named_region_layer"),
            "source_confidence": contract_layer.get("source_confidence", "uncontracted"),
            "replacement_status": contract_layer.get("replacement_status", "needs_custom_asset"),
            "region_polygon": [{"longitude": lon, "latitude": lat} for lon, lat in region.get("points", [])],
            "trees": [
                {"longitude": lon, "latitude": lat, "radius": radius}
                for lon, lat, radius in region.get("trees", [])
            ],
            "ridge_bands": [
                {
                    "id": ridge_band["id"],
                    "style": ridge_band.get("style", "alpine"),
                    "points": [{"longitude": lon, "latitude": lat} for lon, lat in ridge_band.get("points", [])],
                    "height": ridge_band.get("height", 72),
                    "step": ridge_band.get("step", 44),
                }
                for ridge_band in region.get("ridge_bands", [])
            ],
            "massif_segments": [segment["id"] for segment in region.get("massif_segments", [])],
            "glyphs": [
                {
                    "glyph": glyph_name,
                    "longitude": lon,
                    "latitude": lat,
                    "width": width,
                    "y_offset": 0.0,
                }
                for glyph_name, lon, lat, width in region.get("mountain_glyphs", [])
            ],
            "extends_to": region.get("extends_to", []),
        }
    )
    return metadata


def _terrain_massif_contract_layers():
    if not os.path.exists(TERRAIN_MASSIF_LAYERS_PATH):
        return {}
    with open(TERRAIN_MASSIF_LAYERS_PATH, "r", encoding="utf-8") as file:
        contract = json.load(file)
    return {layer.get("id"): layer for layer in contract.get("source_layers", [])}


def _source_layer_base_metadata(source, image_name, render_bbox, cropped_size, proj):
    map_bbox = [value / RENDER_SCALE for value in render_bbox]
    west, north = proj.inverse(map_bbox[0], map_bbox[1])
    east, south = proj.inverse(map_bbox[2], map_bbox[3])
    return {
        "id": source["id"],
        "label": source["label"],
        "image": image_name,
        "render_bbox_px": [int(value) for value in render_bbox],
        "map_bbox_px": [round(value, 2) for value in map_bbox],
        "cropped_size_px": [int(cropped_size[0]), int(cropped_size[1])],
        "geo_bounds": {
            "min_longitude": round(min(west, east), 5),
            "max_longitude": round(max(west, east), 5),
            "min_latitude": round(min(south, north), 5),
            "max_latitude": round(max(south, north), 5),
        },
    }


def _prepare_massif_source_dir():
    if not EXPORT_MASSIF_SOURCE_LAYERS:
        return
    os.makedirs(MASSIF_DIR, exist_ok=True)
    MASSIF_SOURCE_MANIFEST.clear()
    for name in os.listdir(MASSIF_DIR):
        if name.endswith((".png", ".json")):
            os.remove(os.path.join(MASSIF_DIR, name))


def _write_massif_source_manifest():
    if not EXPORT_MASSIF_SOURCE_LAYERS:
        return
    manifest = {
        "schema": "cable-world.massif-source-layers.v1",
        "map_bounds": {
            "min_longitude": GERMANY_BOUNDS[0],
            "min_latitude": GERMANY_BOUNDS[1],
            "max_longitude": GERMANY_BOUNDS[2],
            "max_latitude": GERMANY_BOUNDS[3],
        },
        "map_size_px": [MAP_SIZE[0], MAP_SIZE[1]],
        "render_scale": RENDER_SCALE,
        "layers": MASSIF_SOURCE_MANIFEST,
    }
    with open(MASSIF_MANIFEST_PATH, "w", encoding="utf-8") as file:
        json.dump(manifest, file, ensure_ascii=False, indent=2, sort_keys=True)
        file.write("\n")


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


MAP_LABELS = [
    {"name": "Harz", "lon": 10.5200, "lat": 51.7600, "size": 24, "kind": "relief"},
    {"name": "Zugspitze", "lon": 10.9900, "lat": 47.4300, "size": 19, "kind": "peak"},
    {"name": "Alpen", "lon": 11.7000, "lat": 47.1200, "size": 25, "kind": "relief"},
    {"name": "Müritz", "lon": 12.7500, "lat": 53.4300, "size": 20, "kind": "water"},
    {"name": "Rügen", "lon": 13.3800, "lat": 54.4500, "size": 20, "kind": "island"},
]

NEIGHBOR_COUNTRY_LABELS = [
    {"name": "Dänemark", "lon": 9.80, "lat": 55.18, "size": 20},
    {"name": "Niederlande", "lon": 5.55, "lat": 52.10, "size": 18},
    {"name": "Belgien", "lon": 5.55, "lat": 50.62, "size": 18},
    {"name": "Luxemburg", "lon": 6.18, "lat": 49.78, "size": 16},
    {"name": "Frankreich", "lon": 6.35, "lat": 47.55, "size": 19},
    {"name": "Schweiz", "lon": 8.35, "lat": 46.58, "size": 18},
    {"name": "Österreich", "lon": 14.10, "lat": 47.80, "size": 18},
    {"name": "Tschechien", "lon": 14.50, "lat": 49.35, "size": 18},
    {"name": "Polen", "lon": 16.10, "lat": 52.40, "size": 18},
]


def _map_label_font(size):
    key = int(size)
    if key not in FONT_CACHE:
        font_path = os.path.join(FONT_DIR, "LiberationSerif-BoldItalic.ttf")
        try:
            FONT_CACHE[key] = ImageFont.truetype(font_path, key * RENDER_SCALE)
        except OSError:
            FONT_CACHE[key] = ImageFont.load_default()
    return FONT_CACHE[key]


def _draw_map_labels(canvas, proj, germany_mask):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for label in MAP_LABELS:
        x, y = _project_point(proj, label["lon"], label["lat"])
        font = _map_label_font(label["size"])
        name = label["name"]
        bbox = draw.textbbox((0, 0), name, font=font, stroke_width=2 * RENDER_SCALE)
        text_width = bbox[2] - bbox[0]
        text_pos = (x - text_width // 2, y - 13 * RENDER_SCALE)
        draw.text(
            text_pos,
            name,
            font=font,
            fill=(242, 221, 162, 232),
            stroke_width=2 * RENDER_SCALE,
            stroke_fill=(47, 34, 20, 205),
        )
    alpha = Image.composite(layer.getchannel("A"), Image.new("L", canvas.size, 0), germany_mask)
    layer.putalpha(alpha)
    canvas.alpha_composite(layer)


def _neighbor_land_mask(land_mask, germany_mask):
    return ImageChops.subtract(land_mask, germany_mask)


def _draw_neighbor_ground_texture(canvas, proj, neighbor_mask):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    lon = 4.85
    lon_index = 0
    while lon <= 16.45:
        lat = 43.55
        lat_index = 0
        while lat <= 55.45:
            seed = _stable_hash("neighbor", lon_index, lat_index)
            if seed % 3 != 0:
                lat += 0.48
                lat_index += 1
                continue
            jitter_lon = ((seed & 255) / 255.0 - 0.5) * 0.26
            jitter_lat = (((seed >> 8) & 255) / 255.0 - 0.5) * 0.22
            x, y = _project_point(proj, lon + jitter_lon, lat + jitter_lat)
            kind = seed % 7
            if kind in (0, 1):
                _draw_tuft(draw, x, y, 5 + seed % 8, (62, 95, 57, 36))
            elif kind in (2, 3, 4):
                _draw_hill_mark(draw, x, y, 12 + seed % 8, (103, 95, 66, 34))
            else:
                _draw_tuft(draw, x, y, 4 + seed % 6, (72, 96, 60, 30))
            lat += 0.48
            lat_index += 1
        lon += 0.54
        lon_index += 1

    alpha = Image.composite(layer.getchannel("A"), Image.new("L", canvas.size, 0), neighbor_mask)
    layer.putalpha(alpha)
    canvas.alpha_composite(layer)


def _draw_neighbor_country_labels(canvas, proj, neighbor_mask):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for label in NEIGHBOR_COUNTRY_LABELS:
        x, y = _project_point(proj, label["lon"], label["lat"])
        font = _map_label_font(label["size"])
        name = label["name"]
        bbox = draw.textbbox((0, 0), name, font=font, stroke_width=2 * RENDER_SCALE)
        text_width = bbox[2] - bbox[0]
        text_pos = (x - text_width // 2, y - 8 * RENDER_SCALE)
        draw.text(
            text_pos,
            name,
            font=font,
            fill=(220, 204, 143, 118),
            stroke_width=2 * RENDER_SCALE,
            stroke_fill=(53, 41, 27, 122),
        )
    alpha = Image.composite(layer.getchannel("A"), Image.new("L", canvas.size, 0), neighbor_mask)
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


def _draw_atlas_routes(canvas, proj, germany_mask):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for route in ATLAS_ROUTE_SEGMENTS:
        points = [_project_point(proj, lon, lat) for lon, lat in route["points"]]
        trail = _smooth_polyline(points, subdivisions=12)
        _draw_atlas_dotted_route(draw, trail, route.get("step", 20))
    alpha = Image.composite(layer.getchannel("A"), Image.new("L", canvas.size, 0), germany_mask)
    layer.putalpha(alpha)
    canvas.alpha_composite(layer)


def _smooth_polyline(points, subdivisions=10):
    if len(points) < 2:
        return points
    smooth_points = []
    for index in range(len(points) - 1):
        p0 = points[max(0, index - 1)]
        p1 = points[index]
        p2 = points[index + 1]
        p3 = points[min(len(points) - 1, index + 2)]
        for step in range(subdivisions):
            t = step / subdivisions
            t2 = t * t
            t3 = t2 * t
            x = 0.5 * (
                (2 * p1[0])
                + (-p0[0] + p2[0]) * t
                + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
            )
            y = 0.5 * (
                (2 * p1[1])
                + (-p0[1] + p2[1]) * t
                + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
            )
            smooth_points.append((int(x), int(y)))
    smooth_points.append(points[-1])
    return smooth_points


def _draw_atlas_dotted_route(draw, points, step):
    if len(points) < 2:
        return
    distance_since_dot = 0.0
    dot_index = 0
    last_point = points[0]
    for point in points[1:]:
        segment_length = math.dist(last_point, point)
        distance_since_dot += segment_length
        if distance_since_dot >= step * RENDER_SCALE * ATLAS_ROUTE_DOT_SPACING_SCALE:
            rr = (ATLAS_ROUTE_DOT_MIN_RADIUS + (1 if dot_index % 3 == 0 else 0)) * RENDER_SCALE
            draw.ellipse((point[0] - rr, point[1] - rr, point[0] + rr, point[1] + rr), fill=(64, 46, 25, 104))
            inner = max(1, rr - RENDER_SCALE)
            draw.ellipse((point[0] - inner, point[1] - inner, point[0] + inner, point[1] + inner), fill=(224, 195, 121, 132))
            distance_since_dot = 0.0
            dot_index += 1
        last_point = point


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
    _prepare_massif_source_dir()
    render_size = _scale_size(MAP_SIZE)
    proj = MapProjection(GERMANY_BOUNDS, MAP_SIZE)

    canvas = Image.new("RGBA", render_size, OCEAN)
    _draw_ocean_texture(canvas)
    print("Step 1: Draw countries and Germany mask")
    germany, germany_mask, land_mask = _draw_country_layer(canvas, proj)
    neighbor_mask = _neighbor_land_mask(land_mask, germany_mask)
    water_mask = ImageChops.invert(land_mask)
    _draw_base_water_texture(canvas, water_mask)
    _draw_base_land_texture(canvas, land_mask, germany_mask)

    print("Step 2: Add terrain, texture, lakes, and atlas details")
    _draw_terrain(canvas, proj, land_mask)
    _draw_neighbor_ground_texture(canvas, proj, neighbor_mask)
    _draw_ground_texture(canvas, proj, germany_mask, germany)
    if DEFAULT_INTEGRATED_LAND_PATTERN_ENABLED:
        _draw_integrated_land_pattern(canvas, proj, germany_mask, germany)
    if DEFAULT_NATURAL_EARTH_LAKES_ENABLED:
        _draw_lakes(canvas, proj, germany_mask)
    _draw_named_water_bodies(canvas, proj, germany_mask)
    if DEFAULT_LAND_DETAIL_PATCHES_ENABLED:
        _draw_atlas_land_detail_patches(canvas, proj, germany_mask)
    _draw_atlas_forest_masses(canvas, proj, land_mask)
    if DEFAULT_ATLAS_ROUTES_ENABLED:
        _draw_atlas_routes(canvas, proj, germany_mask)
    _draw_atlas_details(canvas, proj)
    _draw_neighbor_country_labels(canvas, proj, neighbor_mask)
    _draw_map_labels(canvas, proj, germany_mask)
    _write_massif_source_manifest()

    print("Step 3: Finish clean interactive map underlay")

    canvas = _pixel_finish(canvas)
    out_path = os.path.join(MAP_DIR, "germany_styled.png")
    canvas.save(out_path, "PNG", optimize=True)
    file_size = os.path.getsize(out_path)
    print(f"Output: {out_path}")
    print(f"Size: {canvas.size[0]}x{canvas.size[1]}, {file_size:,} bytes")
    return 0


def _pixel_finish(canvas: Image.Image) -> Image.Image:
    full_resolution = canvas.resize(MAP_SIZE, Image.Resampling.LANCZOS).convert("RGB")
    stylized = full_resolution.quantize(colors=64, method=Image.Quantize.MEDIANCUT).convert("RGB")
    return stylized.filter(ImageFilter.UnsharpMask(radius=0.7, percent=90, threshold=2))


if __name__ == "__main__":
    sys.exit(main())
