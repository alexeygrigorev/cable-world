"""Generate hex_map.json on a single GLOBAL Web Mercator hex grid.

The grid spans the whole world: hex (q,r) IDs are global, so expanding from
Germany -> Europe -> Asia -> world later just adds more cells on the SAME grid,
never re-keying existing ones. Every hex stores its real-world center lon/lat so
the map can be transferred onto a real slippy map.

This pass populates Germany (sea/plain/forest/mountain + cities) from existing
project data.
"""
import glob
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "map_pipeline"))

import geopandas as gpd
from shapely.geometry import Point, Polygon, box
from shapely.prepared import prep

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
DATA_DIR = os.path.join(ROOT, "data", "natural_earth")
MASSIF_DIR = os.path.join(ROOT, "assets", "map", "massifs")
OUT = os.path.join(ROOT, "map_editor", "src", "data", "hex_map.json")

# --- global grid definition (locked once; do not change or IDs shift) ---
WORLD_SIZE_PX = 65536          # Web Mercator world width in px
TARGET_KM = 25                 # nominal ground hex size at mid-latitude
NOMINAL_LAT = 51.0             # latitude the 25 km is calibrated at
EARTH_CIRCUM_M = 40075016.686

# Germany = full-detail focus region (mountains/forests/cities)
REGION_BOUNDS = (4.5, 46.5, 15.5, 55.5)
# Europe = wider land context you can pan around (land only; sea is background)
EUROPE_BOUNDS = (-12.0, 34.0, 45.0, 62.0)

# name, lon, lat, kind, icon-id (matches the game's city_<icon>.png sprite)
CITIES = [
    ("Hamburg", 9.9937, 53.5511, "city", "hamburg"),
    ("Berlin", 13.4050, 52.5200, "capital", "berlin"),
    ("Rostock", 12.0991, 54.0924, "city", "rostock"),
    ("Köln", 6.9603, 50.9375, "city", "cologne"),
    ("München", 11.5820, 48.1351, "city", "munich"),
    ("Dresden", 13.7373, 51.0504, "city", "dresden"),
    ("Stuttgart", 9.1829, 48.7758, "city", "stuttgart"),
    ("Hannover", 9.7320, 52.3759, "town", "hannover"),
    ("Bremen", 8.8017, 53.0793, "town", "bremen"),
    ("Kiel", 10.1228, 54.3233, "town", "kiel"),
    ("Lübeck", 10.6866, 53.8655, "town", "luebeck"),
    ("Düsseldorf", 6.7735, 51.2277, "town", "duesseldorf"),
    ("Dortmund", 7.4653, 51.5136, "town", "dortmund"),
    ("Essen", 7.0116, 51.4556, "town", "essen"),
    ("Frankfurt", 8.6821, 50.1109, "town", "frankfurt"),
    ("Leipzig", 12.3731, 51.3397, "town", "leipzig"),
    ("Magdeburg", 11.6276, 52.1205, "town", "magdeburg"),
    ("Wolfsburg", 10.7865, 52.4227, "town", "wolfsburg"),
    ("Kassel", 9.4797, 51.3127, "town", "kassel"),
    ("Erfurt", 11.0299, 50.9848, "town", "erfurt"),
    ("Nürnberg", 11.0767, 49.4521, "town", "nuremberg"),
    ("Regensburg", 12.1016, 49.0134, "town", "regensburg"),
    ("Augsburg", 10.8978, 48.3705, "town", "augsburg"),
    ("Freiburg", 7.8421, 47.9990, "town", "freiburg"),
    ("Saarbrücken", 6.9969, 49.2402, "town", "saarbruecken"),
]

FOREST_POINTS = [
    (10.02, 53.03), (10.46, 52.88), (12.30, 53.52), (12.80, 53.22),
    (13.95, 51.86), (14.38, 51.52), (8.65, 52.08), (9.36, 51.72),
    (8.05, 51.18), (8.52, 50.96), (6.52, 50.28), (7.05, 50.10),
    (9.35, 50.03), (8.82, 49.66), (10.82, 50.74), (11.36, 50.58),
    (10.55, 49.45), (9.58, 48.62), (11.34, 48.02), (12.15, 48.10),
]
NEIGHBORS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]

CATALOG = os.path.join(ROOT, "scripts", "demo_catalog.gd")
# transport_type_id -> icon suffix (scripts/map_panel.gd TRANSPORT_TYPE_ICON)
TYPE_ICON = {
    "cable_gondola": "cable_gondola", "cable_urban": "cable_gondola",
    "cable_tourist": "cable_gondola", "cable_aerial_tram": "aerial_tram",
    "funicular_classic": "funicular", "funicular_water": "funicular",
    "funicular_modern": "funicular", "rail_cog": "cog_railway",
    "rail_mountain": "cog_railway", "rail_suspended": "suspended_monorail",
    "elevator_vertical": "elevator", "elevator_inclined": "elevator",
    "elevator_panoramic": "elevator", "suspended_train": "suspended_monorail",
    "monorail": "suspended_monorail", "suspended_ferry": "suspended_monorail",
    "escalator_unusual": "station", "special_transport_system": "station",
    "unique_engineering_object": "station",
}


def load_catalog_objects():
    """Parse the in-game demo catalog for transport objects with coordinates."""
    text = open(CATALOG, encoding="utf-8").read()
    pat = re.compile(
        r'"id":\s*"([\w-]+)"[\s\S]*?"name":\s*"([^"]+)"[\s\S]*?'
        r'"transport_type_id":\s*"(\w+)"[\s\S]*?'
        r'"latitude":\s*([\-\d.]+),\s*"longitude":\s*([\-\d.]+)')
    out = []
    for m in pat.finditer(text):
        oid, name, tid, lat, lon = m.group(1), m.group(2), m.group(3), float(m.group(4)), float(m.group(5))
        out.append({"id": oid, "name": name, "icon": TYPE_ICON.get(tid, "station"),
                    "type_id": tid, "lon": lon, "lat": lat})
    return out


# --- global Web Mercator world pixels ---
def merc(lon, lat):
    x = (lon + 180.0) / 360.0 * WORLD_SIZE_PX
    siny = math.sin(math.radians(max(-85.05, min(85.05, lat))))
    y = (0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi)) * WORLD_SIZE_PX
    return x, y


def merc_inv(x, y):
    lon = x / WORLD_SIZE_PX * 360.0 - 180.0
    n = math.pi - 2.0 * math.pi * y / WORLD_SIZE_PX
    lat = math.degrees(math.atan(math.sinh(n)))
    return lon, lat


def hex_size_px():
    ground_mpp_eq = EARTH_CIRCUM_M / WORLD_SIZE_PX
    across_flats = TARGET_KM * 1000.0 / (ground_mpp_eq * math.cos(math.radians(NOMINAL_LAT)))
    return across_flats / math.sqrt(3)


def hex_to_world(q, r, s):
    return s * math.sqrt(3) * (q + r / 2), s * 1.5 * r


def world_to_hex(x, y, s):
    qf = ((math.sqrt(3) / 3) * x - (1 / 3) * y) / s
    rf = (2 / 3) * y / s
    cx, cz = qf, rf
    cy = -cx - cz
    rx, ry, rz = round(cx), round(cy), round(cz)
    dx, dy, dz = abs(rx - cx), abs(ry - cy), abs(rz - cz)
    if dx > dy and dx > dz:
        rx = -ry - rz
    elif dy > dz:
        ry = -rx - rz
    else:
        rz = -rx - ry
    return rx, rz


def load_ne(name):
    path = os.path.join(DATA_DIR, name)
    shp = [f for f in os.listdir(path) if f.endswith(".shp")][0]
    return gpd.read_file(os.path.join(path, shp))


def load_massifs():
    """Return (mountain_polys, pieces).

    mountain_polys: prepared region polygons used only to mark hexes as
    'mountain' terrain (e.g. the whole Alpine arc from alps.json).

    pieces: the individual art layers to actually draw. An aggregate massif
    (alps.json, which lists massif_segments) is NOT drawn as one giant image;
    its segments (western_alps_massif, swiss_alps_massif, ...) are drawn as
    separate pieces, each with its own image + geo_bounds. Single massifs
    (harz, black_forest, ...) are their own single piece."""
    mountain_polys, pieces = [], []
    for path in sorted(glob.glob(os.path.join(MASSIF_DIR, "*.json"))):
        d = json.load(open(path))
        rp, img, gb = d.get("region_polygon"), d.get("image"), d.get("geo_bounds")
        if rp:
            mountain_polys.append(prep(Polygon([(p["longitude"], p["latitude"]) for p in rp])))
        if img and gb and not d.get("massif_segments"):
            pieces.append({"id": d["id"], "image": img, "geo_bounds": gb})
    return mountain_polys, pieces


def main():
    s = hex_size_px()
    minlon, minlat, maxlon, maxlat = EUROPE_BOUNDS
    dminlon, dminlat, dmaxlon, dmaxlat = REGION_BOUNDS  # Germany detail window

    countries = load_ne("ne_50m_admin_0_countries")
    clip = box(minlon - 1, minlat - 1, maxlon + 1, maxlat + 1)
    countries = countries[countries.geometry.intersects(clip)].copy()
    germany = countries[countries["ADMIN"] == "Germany"].geometry.union_all()
    land_prep = prep(countries.geometry.union_all())
    # per-country prepared geometry + bbox + ISO code, for fast point lookup
    cgeo = []
    for _, row in countries.iterrows():
        iso = row.get("ISO_A2")
        if not iso or iso == "-99":
            iso = str(row.get("ADMIN", "??"))[:3].upper()
        cgeo.append((iso, prep(row.geometry), row.geometry.bounds))
    mountain_polys, massif_pieces = load_massifs()

    def country_of(pt):
        for iso, pg, (bx0, by0, bx1, by1) in cgeo:
            if bx0 <= pt.x <= bx1 and by0 <= pt.y <= by1 and pg.contains(pt):
                return iso
        return "??"

    # q,r range covering all of Europe in world px
    xs = [merc(minlon, maxlat)[0], merc(maxlon, minlat)[0]]
    ys = [merc(minlon, maxlat)[1], merc(maxlon, minlat)[1]]
    r_lo = int(min(ys) / (1.5 * s)) - 1
    r_hi = int(max(ys) / (1.5 * s)) + 1

    # store land hexes only; open sea is just the background
    hexes = {}
    for r in range(r_lo, r_hi + 1):
        q_lo = int(min(xs) / (math.sqrt(3) * s) - r / 2) - 1
        q_hi = int(max(xs) / (math.sqrt(3) * s) - r / 2) + 1
        for q in range(q_lo, q_hi + 1):
            wx, wy = hex_to_world(q, r, s)
            lon, lat = merc_inv(wx, wy)
            if not (minlon <= lon <= maxlon and minlat <= lat <= maxlat):
                continue
            pt = Point(lon, lat)
            if not land_prep.contains(pt):
                continue
            # massifs are cross-border: mountain regardless of country
            terrain = "mountain" if any(m.contains(pt) for m in mountain_polys) else "plain"
            hexes[f"{q},{r}"] = {"country": country_of(pt), "terrain": terrain,
                                 "center": [round(lon, 5), round(lat, 5)]}

    # forests as multi-hex bundles: a patch of plain-land hexes, drawn as a
    # cluster of forest glyphs and moved/selected as one object.
    forests = []
    for i, (lon, lat) in enumerate(FOREST_POINTS):
        wx, wy = merc(lon, lat)
        q0, r0 = world_to_hex(wx, wy, s)
        cells = [f"{q0 + dq},{r0 + dr}" for dq, dr in [(0, 0)] + NEIGHBORS
                 if hexes.get(f"{q0 + dq},{r0 + dr}", {}).get("terrain") == "plain"]
        if cells:
            anchor = f"{q0},{r0}" if f"{q0},{r0}" in cells else cells[0]
            forests.append({"id": f"forest-{i}", "glyph": "forest", "label": "Лес",
                            "cells": cells, "anchor": anchor, "home": anchor})

    features = list(forests)

    # separate massif glyph pieces: Alps as its named segments, every other
    # massif as its own piece — each its own image, placed by real geo_bounds.
    for m in massif_pieces:
        gb = m["geo_bounds"]
        x0, y0 = merc(gb["min_longitude"], gb["max_latitude"])
        x1, y1 = merc(gb["max_longitude"], gb["min_latitude"])
        cells = [k for k, c in hexes.items()
                 if c["terrain"] == "mountain"
                 and gb["min_longitude"] <= c["center"][0] <= gb["max_longitude"]
                 and gb["min_latitude"] <= c["center"][1] <= gb["max_latitude"]]
        aq, ar = world_to_hex((x0 + x1) / 2, (y0 + y1) / 2, s)
        features.append({"id": m["id"], "glyph": "massif", "image": m["image"],
                         "label": m["id"], "bounds_px": [round(x0, 1), round(y0, 1),
                         round(x1, 1), round(y1, 1)], "cells": cells,
                         "anchor": f"{aq},{ar}", "home": f"{aq},{ar}"})

    for name, lon, lat, kind, icon in CITIES:
        wx, wy = merc(lon, lat)
        q, r = world_to_hex(wx, wy, s)
        features.append({"id": icon, "glyph": "city", "kind": kind,
                         "label": name, "icon": icon, "lon": lon, "lat": lat,
                         "anchor": f"{q},{r}", "home": f"{q},{r}"})

    # in-game transport objects (cable cars, funiculars, ...) within the map
    for o in load_catalog_objects():
        if not (minlon <= o["lon"] <= maxlon and minlat <= o["lat"] <= maxlat):
            continue
        q, r = world_to_hex(*merc(o["lon"], o["lat"]), s)
        features.append({"id": o["id"], "glyph": "transport", "icon": o["icon"],
                         "label": o["name"], "type_id": o["type_id"],
                         "lon": o["lon"], "lat": o["lat"],
                         "anchor": f"{q},{r}", "home": f"{q},{r}"})

    # view = world-px bbox of populated hexes (for the editor camera)
    pts = [hex_to_world(*map(int, k.split(",")), s) for k in hexes]
    minx = min(p[0] for p in pts) - s * 2
    maxx = max(p[0] for p in pts) + s * 2
    miny = min(p[1] for p in pts) - s * 2
    maxy = max(p[1] for p in pts) + s * 2

    outline = []
    polys = [germany] if germany.geom_type == "Polygon" else list(germany.geoms)
    for p in polys:
        outline.append([[round(a, 2), round(b, 2)] for a, b in
                        (merc(x, y) for x, y in p.exterior.coords)])

    # focus = the EXACT Germany geo_bounds the game uses at zoom 1.0
    # (scripts/map_panel.gd _active_coordinate_bounds, MAP_SCOPE_GERMANY).
    # The editor fits this box with COVER, identical to the game's
    # _map_base_size_for_viewport, so 100% framing matches the game exactly.
    GAME_DE = (4.5, 43.2, 16.8, 55.8)  # min_lon, min_lat, max_lon, max_lat
    fx0, fy0 = merc(GAME_DE[0], GAME_DE[3])
    fx1, fy1 = merc(GAME_DE[2], GAME_DE[1])
    focus = {"origin": [round(fx0, 2), round(fy0, 2)],
             "size": [round(fx1 - fx0, 2), round(fy1 - fy0, 2)],
             "geo_bounds": list(GAME_DE), "fit": "cover"}

    data = {
        "schema": "cable-world.hex-map.v2-global",
        "grid": {
            "orientation": "pointy",
            "projection": "web_mercator",
            "world_size_px": WORLD_SIZE_PX,
            "hex_size_px": round(s, 4),
            "nominal_km": TARGET_KM,
            "nominal_lat": NOMINAL_LAT,
            "scope": "world",
            "populated": "europe-land+germany-detail",
        },
        "view": {"origin": [round(minx, 2), round(miny, 2)],
                 "size": [round(maxx - minx, 2), round(maxy - miny, 2)]},
        "focus": focus,
        "reference_outline": outline,
        "hexes": hexes,
        "features": features,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(data, open(OUT, "w"), indent=2, ensure_ascii=False)

    tally = {}
    for c in hexes.values():
        tally[c["terrain"]] = tally.get(c["terrain"], 0) + 1
    print(f"hex_size_px={s:.3f} terrain={tally} cities={len(features)} "
          f"view={data['view']['size']} -> {OUT}")


if __name__ == "__main__":
    main()
