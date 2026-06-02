"""Generate hex_map.json on a single GLOBAL Web Mercator hex grid.

The grid spans the whole world: hex (q,r) IDs are global, so expanding from
Germany -> Europe -> Asia -> world later just adds more cells on the SAME grid,
never re-keying existing ones. Every hex stores its real-world center lon/lat so
the map can be transferred onto a real slippy map.

This pass populates Germany (sea/plain/forest/mountain + cities) from existing
project data.
"""
import glob
import struct
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "map_pipeline"))

import geopandas as gpd
from PIL import Image
from shapely.geometry import Point, Polygon, box
from shapely.prepared import prep

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
DATA_DIR = os.path.join(ROOT, "data", "natural_earth")
MASSIF_DIR = os.path.join(ROOT, "assets", "map", "massifs")
MAP_BLOCKS = [
    os.path.join(ROOT, "map_pipeline", "data", "france_spain_map_block.json"),
    os.path.join(ROOT, "map_pipeline", "data", "nordics_baltics_map_block.json"),
    os.path.join(ROOT, "map_pipeline", "data", "eastern_europe_turkey_map_block.json"),
]
OUT = os.path.join(ROOT, "map_editor", "src", "data", "hex_map.json")

# Visual sizes are intentionally decoupled from geographic source extents:
# geo data decides where the massif lives and which hexes are mountain, while
# the PNG keeps its own readable map-symbol proportions.
MASSIF_ASSET_WIDTH_HEX = {
    "western_alps_massif": 11.0,
    "swiss_alps_massif": 11.2,
    "bavarian_tyrol_alps_massif": 10.8,
    "german_alpine_edge_massif": 9.2,
    "austrian_alps_massif": 10.6,
    "black_forest": 5.2,
    "bavarian_forest": 5.0,
    "eifel_hunsrueck": 4.8,
    "harz": 4.3,
    "erzgebirge": 5.6,
    "saxon_switzerland": 3.8,
}
MASSIF_FOOTPRINT_OVERRIDES = {
    "black_forest.png": {
        "anchor_source_x_px": 9,
        "faint_offsets": [],
    },
}
GEO_BOUNDS_MASSIF_IDS = {
    "western_alps_massif",
    "swiss_alps_massif",
    "bavarian_tyrol_alps_massif",
    "german_alpine_edge_massif",
    "austrian_alps_massif",
}

# --- global grid definition (locked once; do not change or IDs shift) ---
WORLD_SIZE_PX = 65536          # Web Mercator world width in px
TARGET_KM = 25                 # nominal ground hex size at mid-latitude
NOMINAL_LAT = 51.0             # latitude the 25 km is calibrated at
EARTH_CIRCUM_M = 40075016.686

# Germany = full-detail focus region (mountains/forests/cities)
REGION_BOUNDS = (4.5, 46.5, 15.5, 55.5)
# Europe + Turkey = wider land context you can pan around (land only; sea is background)
EUROPE_BOUNDS = (-25.0, 34.0, 45.0, 72.0)
EUROPE_ADMIN_ALLOW = {
    "Albania", "Andorra", "Austria", "Belarus", "Belgium", "Bosnia and Herzegovina",
    "Bulgaria", "Croatia", "Cyprus", "Czechia", "Denmark", "Estonia", "Finland",
    "France", "Germany", "Greece", "Hungary", "Iceland", "Ireland", "Italy",
    "Kosovo", "Latvia", "Liechtenstein", "Lithuania", "Luxembourg", "Malta",
    "Moldova", "Monaco", "Montenegro", "Netherlands", "North Macedonia", "Norway",
    "Poland", "Portugal", "Romania", "Russia", "San Marino", "Serbia", "Slovakia",
    "Slovenia", "Spain", "Sweden", "Switzerland", "Turkey", "Ukraine",
    "United Kingdom", "Vatican",
}
EUROPE_ISO_ALLOW = {
    "AL", "AD", "AT", "BY", "BE", "BA", "BG", "HR", "CY", "CZ", "DK", "EE",
    "FI", "FR", "DE", "GR", "HU", "IS", "IE", "IT", "XK", "LV", "LI", "LT",
    "LU", "MT", "MD", "MC", "ME", "NL", "MK", "NO", "PL", "PT", "RO", "RU",
    "SM", "RS", "SK", "SI", "ES", "SE", "CH", "TR", "UA", "GB", "VA",
}

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

# Major European/Turkey anchors that already have or can fall back from city_* sprites.
# The block JSON files below add more regional/cableway-anchor cities.
EUROPE_CITY_POINTS = [
    ("Lisbon", -9.1393, 38.7223, "capital", "lisbon"),
    ("Porto", -8.6291, 41.1579, "city", "porto"),
    ("Madrid", -3.7038, 40.4168, "capital", "madrid"),
    ("Barcelona", 2.1734, 41.3851, "city", "barcelona"),
    ("Paris", 2.3522, 48.8566, "capital", "paris"),
    ("Brussels", 4.3517, 50.8503, "capital", "brussels"),
    ("Amsterdam", 4.9041, 52.3676, "capital", "amsterdam"),
    ("Luxembourg", 6.1296, 49.6116, "capital", "luxembourg"),
    ("London", -0.1276, 51.5072, "capital", "london"),
    ("Dublin", -6.2603, 53.3498, "capital", "dublin"),
    ("Rome", 12.4964, 41.9028, "capital", "rome"),
    ("Milan", 9.1900, 45.4642, "city", "milan"),
    ("Venice", 12.3155, 45.4408, "city", "venice"),
    ("San Marino", 12.4578, 43.9424, "capital", "san_marino"),
    ("Valletta", 14.5146, 35.8997, "capital", "valletta"),
    ("Nicosia", 33.3823, 35.1856, "capital", "nicosia"),
    ("Monaco", 7.4246, 43.7384, "capital", "monaco"),
    ("Vaduz", 9.5215, 47.1410, "capital", "vaduz"),
    ("Vatican City", 12.4534, 41.9029, "capital", "vatican"),
    ("Zurich", 8.5417, 47.3769, "city", "zurich"),
    ("Geneva", 6.1432, 46.2044, "city", "geneva"),
    ("Vienna", 16.3738, 48.2082, "capital", "vienna"),
    ("Prague", 14.4378, 50.0755, "capital", "prague"),
    ("Bratislava", 17.1077, 48.1486, "capital", "bratislava"),
    ("Budapest", 19.0402, 47.4979, "capital", "budapest"),
    ("Warsaw", 21.0122, 52.2297, "capital", "warsaw"),
    ("Krakow", 19.9450, 50.0647, "city", "krakow"),
    ("Ljubljana", 14.5058, 46.0569, "capital", "ljubljana"),
    ("Zagreb", 15.9819, 45.8150, "capital", "zagreb"),
    ("Sarajevo", 18.4131, 43.8563, "capital", "sarajevo"),
    ("Podgorica", 19.2594, 42.4304, "capital", "podgorica"),
    ("Pristina", 21.1655, 42.6629, "capital", "pristina"),
    ("Belgrade", 20.4489, 44.7866, "capital", "belgrade"),
    ("Tirana", 19.8189, 41.3275, "capital", "tirana"),
    ("Skopje", 21.4316, 41.9973, "capital", "skopje"),
    ("Sofia", 23.3219, 42.6977, "capital", "sofia"),
    ("Bucharest", 26.1025, 44.4268, "capital", "bucharest"),
    ("Chisinau", 28.8323, 47.0105, "capital", "chisinau"),
    ("Athens", 23.7275, 37.9838, "capital", "athens"),
    ("Kyiv", 30.5234, 50.4501, "capital", "kyiv"),
    ("Lviv", 24.0311, 49.8397, "city", "lviv"),
    ("Minsk", 27.5615, 53.9045, "capital", "minsk"),
    ("Vilnius", 25.2797, 54.6872, "capital", "vilnius"),
    ("Riga", 24.1052, 56.9496, "capital", "riga"),
    ("Tallinn", 24.7536, 59.4370, "capital", "tallinn"),
    ("Copenhagen", 12.5683, 55.6761, "capital", "copenhagen"),
    ("Stockholm", 18.0686, 59.3293, "capital", "stockholm"),
    ("Oslo", 10.7522, 59.9139, "capital", "oslo"),
    ("Helsinki", 24.9384, 60.1699, "capital", "helsinki"),
    ("Reykjavik", -21.9426, 64.1466, "capital", "reykjavik"),
    ("Istanbul", 28.9784, 41.0082, "city", "istanbul"),
    ("Ankara", 32.8597, 39.9334, "capital", "ankara"),
    ("Andorra la Vella", 1.5218, 42.5063, "capital", "andorra"),
]

MICROSTATE_COUNTRY_ANCHORS = [
    ("LI", 9.5215, 47.1410),
    ("MC", 7.4246, 43.7384),
    ("SM", 12.4578, 43.9424),
    ("VA", 12.4534, 41.9029),
]
CITY_COUNTRY_OVERRIDES = {
    "andorra": "AD",
    "monaco": "MC",
    "san_marino": "SM",
    "vaduz": "LI",
    "vatican": "VA",
}

SUPPLEMENTAL_RELIEF_LAYERS = [
    {
        "id": "scottish_highlands",
        "label": "Scottish Highlands",
        "bounds": [-6.9, 56.0, -3.0, 58.7],
        "countries": ["GB"],
    },
    {
        "id": "pennines_wales",
        "label": "Pennines and Wales uplands",
        "bounds": [-4.8, 51.6, -1.2, 55.4],
        "countries": ["GB"],
    },
    {
        "id": "irish_uplands",
        "label": "Irish uplands",
        "bounds": [-10.5, 51.7, -6.0, 55.2],
        "countries": ["IE"],
    },
    {
        "id": "troodos_mountains",
        "label": "Troodos Mountains",
        "bounds": [32.5, 34.6, 33.4, 35.1],
        "countries": ["CY"],
    },
]

FOREST_POINTS = [
    (10.02, 53.03), (10.46, 52.88), (12.30, 53.52), (12.80, 53.22),
    (13.95, 51.86), (14.38, 51.52), (8.65, 52.08), (9.36, 51.72),
    (8.05, 51.18), (8.52, 50.96), (6.52, 50.28), (7.05, 50.10),
    (9.35, 50.03), (8.82, 49.66), (10.82, 50.74), (11.36, 50.58),
    (10.55, 49.45), (9.58, 48.62), (11.34, 48.02), (12.15, 48.10),
]
NEIGHBORS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]
HEX_ALPHA_STEP = 0.18
PRIMARY_ALPHA_RATIO = 0.22
ALPHA_THRESHOLD = 50

CATALOGS = [
    os.path.join(ROOT, "scripts", "demo_catalog.gd"),
    os.path.join(ROOT, "scripts", "demo_catalog_europe.gd"),
    os.path.join(ROOT, "scripts", "demo_catalog_russia.gd"),
]
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

COUNTRY_NAME_TO_ISO = {
    "Австрия": "AT", "Германия": "DE", "Италия": "IT", "Польша": "PL",
    "Португалия": "PT", "Россия": "RU", "Словакия": "SK", "Франция": "FRA",
    "Чехия": "CZ",
}

STAGING_TRANSPORT_POINTS = [
    ("funicamp-encamp", "Funicamp Encamp", "cable_gondola", 1.5860, 42.5360, "AD"),
    ("dajti-ekspres", "Канатная дорога Dajti Ekspres", "cable_gondola", 19.8940, 41.3530, "AL"),
    ("innsbruck-hungerburgbahn", "Hungerburgbahn Innsbruck", "funicular_modern", 11.3940, 47.2690, "AT"),
    ("namur-citadelle-cable-car", "Канатная дорога цитадели Намюра", "cable_gondola", 4.8670, 50.4620, "BE"),
    ("minsk-childrens-railway", "Минская детская железная дорога", "special_transport_system", 27.6410, 53.9310, "BY"),
    ("troodos-ski-lifts", "Подъемники Троодоса", "cable_tourist", 32.8830, 34.9360, "CY"),
    ("zurich-polybahn", "Цюрихский Polybahn", "funicular_classic", 8.5450, 47.3760, "CH"),
    ("copenhill-ski-lift", "Подъемник CopenHill в Копенгагене", "special_transport_system", 12.6220, 55.6840, "DK"),
    ("tallinn-tv-tower-elevator", "Лифт Таллинской телебашни", "elevator_vertical", 24.8870, 59.4710, "EE"),
    ("levi-gondola", "Гондольная дорога Levi", "cable_gondola", 24.8470, 67.8050, "FI"),
    ("london-cable-car", "London Cable Car", "cable_urban", 0.0055, 51.4997, "GB"),
    ("lycabettus-funicular", "Фуникулер Ликавит", "funicular_classic", 23.7430, 37.9810, "GR"),
    ("zagreb-funicular", "Загребский фуникулер", "funicular_classic", 15.9740, 45.8150, "HR"),
    ("dursey-island-cable-car", "Канатная дорога Dursey Island", "cable_aerial_tram", -10.1540, 51.6180, "IE"),
    ("blafjoll-ski-lifts", "Подъемники Bláfjöll", "cable_tourist", -21.6830, 63.9930, "IS"),
    ("brezovica-ski-lift", "Подъемники Brezovica", "cable_tourist", 20.9640, 42.1990, "KOS"),
    ("malbun-sareis-chairlift", "Кресельная дорога Malbun Sareis", "cable_tourist", 9.6090, 47.1020, "LI"),
    ("vilnius-tv-tower-elevator", "Лифт Вильнюсской телебашни", "elevator_vertical", 25.2140, 54.6870, "LT"),
    ("pfaffenthal-panoramic-elevator", "Панорамный лифт Pfaffenthal", "elevator_panoramic", 6.1330, 49.6180, "LU"),
    ("sigulda-cable-car", "Сигулдская канатная дорога", "cable_aerial_tram", 24.8460, 57.1650, "LV"),
    ("monaco-public-elevator", "Общественный лифт Монако", "elevator_vertical", 7.4246, 43.7380, "MC"),
    ("chisinau-childrens-railway", "Кишиневская детская железная дорога", "special_transport_system", 28.7970, 47.0130, "MD"),
    ("kotor-cable-car", "Канатная дорога Котор — Ловчен", "cable_gondola", 18.7660, 42.4040, "ME"),
    ("millennium-cross-cable-car", "Канатная дорога к Кресту Тысячелетия", "cable_gondola", 21.3980, 41.9620, "MK"),
    ("barrakka-lift", "Лифт Barrakka", "elevator_vertical", 14.5120, 35.8940, "MT"),
    ("adam-lookout-elevator", "Лифт A'DAM Lookout", "elevator_vertical", 4.9020, 52.3840, "NL"),
    ("zlatibor-gold-gondola", "Gold Gondola Zlatibor", "cable_gondola", 19.7000, 43.7250, "RS"),
    ("are-kabinbana", "Канатная дорога Åre Kabinbana", "cable_aerial_tram", 13.0830, 63.3990, "SE"),
    ("san-marino-cable-car", "Канатная дорога Сан-Марино", "cable_aerial_tram", 12.4510, 43.9360, "SM"),
    ("st-peters-dome-elevator", "Лифт купола собора Святого Петра", "elevator_vertical", 12.4534, 41.9029, "VA"),
    ("montmartre-funicular", "Фуникулер Монмартра", "funicular_classic", 2.3429, 48.8842, "FRA"),
    ("lyon-fourviere-funicular", "Фуникулер Фурвьер в Лионе", "funicular_classic", 4.8218, 45.7600, "FRA"),
    ("pau-funicular", "Фуникулер По", "funicular_classic", -0.3705, 43.2951, "FRA"),
    ("madrid-teleferico", "Канатная дорога Мадрида", "cable_urban", -3.7247, 40.4258, "ES"),
    ("barcelona-port-cable-car", "Портовая канатная дорога Барселоны", "cable_aerial_tram", 2.1870, 41.3728, "ES"),
    ("bilbao-artxanda-funicular", "Фуникулер Арчанда в Бильбао", "funicular_classic", -2.9279, 43.2661, "ES"),
    ("bergen-floibanen", "Фуникулер Флёйбанен в Бергене", "funicular_classic", 5.3287, 60.3950, "NOR"),
    ("bergen-ulriken-cable-car", "Канатная дорога Ульрикен в Бергене", "cable_aerial_tram", 5.3787, 60.3770, "NOR"),
    ("tromso-fjellheisen", "Канатная дорога Fjellheisen в Тромсё", "cable_aerial_tram", 18.9924, 69.6412, "NOR"),
    ("budapest-castle-hill-funicular", "Будапештский фуникулер на Замковую гору", "funicular_classic", 19.0396, 47.4977, "HU"),
    ("ljubljana-castle-funicular", "Фуникулер Люблянского замка", "funicular_classic", 14.5083, 46.0491, "SI"),
    ("sarajevo-trebevic-cable-car", "Канатная дорога Требевич в Сараево", "cable_aerial_tram", 18.4318, 43.8570, "BA"),
    ("dubrovnik-cable-car", "Канатная дорога Дубровника", "cable_aerial_tram", 18.1126, 42.6467, "HR"),
    ("kyiv-funicular", "Киевский фуникулер", "funicular_classic", 30.5235, 50.4590, "UA"),
    ("istanbul-eyup-pierre-loti-cable-car", "Канатная дорога Эюп — Пьер Лоти", "cable_gondola", 28.9340, 41.0506, "TR"),
    ("bursa-uludag-cable-car", "Канатная дорога Улудаг в Бурсе", "cable_aerial_tram", 29.0806, 40.1710, "TR"),
    ("ankara-yenimahalle-cable-car", "Канатная дорога Енимахалле в Анкаре", "cable_urban", 32.8065, 39.9655, "TR"),
    ("izmir-balcova-cable-car", "Канатная дорога Балчова в Измире", "cable_tourist", 27.0408, 38.3898, "TR"),
    ("antalya-tunektepe-cable-car", "Канатная дорога Тюнектепе в Анталье", "cable_tourist", 30.5720, 36.8442, "TR"),
    ("trabzon-besikduzu-cable-car", "Канатная дорога Бешикдюзю в Трабзоне", "cable_tourist", 39.2290, 41.0520, "TR"),
    ("sofia-vitosha-lift", "Витошская канатная дорога в Софии", "cable_gondola", 23.2862, 42.6207, "BG"),
    ("sinaia-cable-car", "Канатная дорога Синая", "cable_aerial_tram", 25.5480, 45.3500, "RO"),
]


def load_catalog_objects():
    """Parse the in-game demo catalog for transport objects with coordinates."""
    out, seen = [], set()
    field = lambda block, name: re.search(rf'"{name}":\s*"([^"]+)"', block)
    number = lambda block, name: re.search(rf'"{name}":\s*([\-\d.]+)', block)
    for path in CATALOGS:
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8").read()
        start = text.find("var objects")
        start = text.find("=", start)
        start = text.find("[", start)
        if start < 0:
            continue
        depth = 0
        block_start = None
        in_string = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
                if depth == 1:
                    block_start = i
            elif ch == "}":
                if depth == 1 and block_start is not None:
                    block = text[block_start:i + 1]
                    oid_m, name_m, tid_m = field(block, "id"), field(block, "name"), field(block, "transport_type_id")
                    country_m = field(block, "country")
                    lat_m, lon_m = number(block, "latitude"), number(block, "longitude")
                    if oid_m and name_m and tid_m and lat_m and lon_m:
                        oid = oid_m.group(1)
                        if oid not in seen:
                            seen.add(oid)
                            tid = tid_m.group(1)
                            out.append({
                                "id": oid,
                                "name": name_m.group(1),
                                "icon": TYPE_ICON.get(tid, "station"),
                                "type_id": tid,
                                "lon": float(lon_m.group(1)),
                                "lat": float(lat_m.group(1)),
                                "country_code": COUNTRY_NAME_TO_ISO.get(country_m.group(1)) if country_m else None,
                            })
                depth -= 1
            elif ch == "]" and depth == 0:
                break
    return out


def load_map_block_cities():
    cities = []
    seen = set()
    for path in MAP_BLOCKS:
        if not os.path.exists(path):
            continue
        data = json.load(open(path, encoding="utf-8"))
        for city in data.get("city_landmarks", []):
            city_id = city.get("id")
            lon, lat = city.get("lon"), city.get("lat")
            if not city_id or lon is None or lat is None or city_id in seen:
                continue
            seen.add(city_id)
            icon_id = str(city.get("landmark_icon_id") or city_id)
            if icon_id.startswith("city_"):
                icon_id = icon_id[5:]
            if icon_id == "missing_landmark_icon":
                icon_id = city_id
            kind = "capital" if city.get("priority") in {"major"} and city_id in {
                "paris", "madrid", "oslo", "stockholm", "copenhagen", "helsinki",
                "tallinn", "riga", "vilnius", "warsaw", "prague", "bratislava",
                "budapest", "bucharest", "sofia", "belgrade", "zagreb", "kyiv",
                "minsk", "istanbul", "ankara",
            } else "city"
            cities.append((city.get("display_name", city_id), float(lon), float(lat), kind, icon_id, city_id))
    return cities


def load_expansion_relief_layers():
    relief = []
    seen = set()
    for path in MAP_BLOCKS:
        if not os.path.exists(path):
            continue
        data = json.load(open(path, encoding="utf-8"))
        for layer in data.get("relief_layers", []):
            layer_id = str(layer.get("id", ""))
            display = str(layer.get("display_name") or layer_id)
            text = " ".join([layer_id, display, str(layer.get("source_rule", ""))]).lower()
            if not layer_id or layer_id in seen:
                continue
            if layer_id == "western_alps_france":
                continue
            if "exclusion" in text or "lowland" in text or "low-relief" in text:
                continue
            bounds = layer.get("bounds")
            if not isinstance(bounds, list) or len(bounds) != 4:
                continue
            seen.add(layer_id)
            relief.append({
                "id": layer_id,
                "label": display,
                "bounds": [float(v) for v in bounds],
                "countries": layer.get("countries", []),
            })
    for layer in SUPPLEMENTAL_RELIEF_LAYERS:
        layer_id = layer["id"]
        if layer_id in seen:
            continue
        seen.add(layer_id)
        relief.append({
            "id": layer_id,
            "label": layer["label"],
            "bounds": [float(v) for v in layer["bounds"]],
            "countries": layer.get("countries", []),
        })
    return relief


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


def png_size(path):
    with open(path, "rb") as file:
        sig = file.read(24)
    if len(sig) < 24 or sig[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", sig[16:24])


def city_icon_exists(icon_id):
    if not icon_id:
        return False
    names = [f"city_{icon_id}.png"]
    dirs = [
        os.path.join(ROOT, "assets", "sprites", "city_landmark_clusters_hi_res", "outlined"),
        os.path.join(ROOT, "assets", "sprites", "city_landmark_clusters_hi_res"),
    ]
    return any(os.path.exists(os.path.join(d, n)) for d in dirs for n in names)


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
            piece = {"id": d["id"], "image": img, "geo_bounds": gb}
            if rp:
                piece["region_polygon"] = Polygon([(p["longitude"], p["latitude"]) for p in rp])
            size = png_size(os.path.join(MASSIF_DIR, img))
            if size:
                piece["image_size"] = size
            if d["id"] in MASSIF_ASSET_WIDTH_HEX:
                piece["asset_width_hex"] = MASSIF_ASSET_WIDTH_HEX[d["id"]]
            pieces.append(piece)
    return mountain_polys, pieces


def relief_image_for(layer_id):
    alpine_ids = ("alps", "carpath", "pyrenees", "scandinavian", "taurus", "pontic", "caucasus", "troodos")
    wooded_ids = ("massif_central", "vosges", "jura", "bohemian", "sudetes", "swedish", "lapland", "baltic", "scottish", "pennines", "wales", "irish")
    sandstone_ids = ("dinaric", "balkan", "pindus", "rhodope", "crimean")
    if any(token in layer_id for token in alpine_ids):
        return "swiss_alps_massif.png", MASSIF_ASSET_WIDTH_HEX["swiss_alps_massif"]
    if any(token in layer_id for token in sandstone_ids):
        return "saxon_switzerland.png", MASSIF_ASSET_WIDTH_HEX["saxon_switzerland"]
    if any(token in layer_id for token in wooded_ids):
        return "black_forest.png", MASSIF_ASSET_WIDTH_HEX["black_forest"]
    return "erzgebirge.png", MASSIF_ASSET_WIDTH_HEX["erzgebirge"]


def feature_bounds_from_center(cx, cy, image_name, width_hex, s):
    size = png_size(os.path.join(MASSIF_DIR, image_name)) or (1, 1)
    width_px = s * float(width_hex)
    height_px = width_px * size[1] / size[0]
    return [
        round(cx - width_px / 2, 1),
        round(cy - height_px / 2, 1),
        round(cx + width_px / 2, 1),
        round(cy + height_px / 2, 1),
    ]


def point_inside_hex(dx, dy, s):
    return abs(dx) <= (math.sqrt(3) / 2) * s and abs(dy) + abs(dx) / math.sqrt(3) <= s


def glyph_ref(image_name):
    return f"massif:{os.path.splitext(image_name)[0]}"


def alpha_bottom_left_anchor_x(alpha, threshold=ALPHA_THRESHOLD):
    bbox = alpha.getbbox()
    if not bbox:
        return 0
    width, _height = alpha.size
    pixels = alpha.load()
    alpha_height = bbox[3] - bbox[1]
    band_top = max(bbox[1], bbox[3] - max(12, int(alpha_height * 0.08)))
    xs = []
    for y in range(band_top, bbox[3]):
        for x in range(width):
            if pixels[x, y] > threshold:
                xs.append(x)
    if not xs:
        return bbox[0]
    xs.sort()
    # Use the lower-left support mass, not the first stray edge pixel. The 25th
    # percentile keeps the anchor on the left side while putting the anchor hex
    # inside the visible glyph base.
    return xs[len(xs) // 4]


def glyph_footprint(image_name, zoom_factor, s):
    path = os.path.join(MASSIF_DIR, image_name)
    with Image.open(path) as img:
        alpha = img.convert("RGBA").getchannel("A")
        iw, ih = alpha.size
        alpha_px = alpha.load()

    width_px = s * float(zoom_factor)
    height_px = width_px * ih / iw
    anchor_x_px = MASSIF_FOOTPRINT_OVERRIDES.get(image_name, {}).get(
        "anchor_source_x_px",
        alpha_bottom_left_anchor_x(alpha),
    )
    anchor_x = width_px * anchor_x_px / iw
    x0, y0, x1, y1 = -anchor_x, -height_px, width_px - anchor_x, 0
    primary_offsets = []
    faint_offsets = []
    max_dq = math.ceil((abs(x0) + abs(x1)) / (math.sqrt(3) * s)) + 3
    max_dr = math.ceil((abs(y0) + abs(y1)) / (1.5 * s)) + 3
    for dr in range(-max_dr, max_dr + 1):
        if dr > 0:
            continue
        for dq in range(-max_dq, max_dq + 1):
            wx, wy = hex_to_world(dq, dr, s)
            wx += math.sqrt(3) * s / 2
            wy -= s * 0.75
            if wx + s < x0 or wx - s > x1 or wy + s < y0 or wy - s > y1:
                continue
            opaque = 0
            sampled = 0
            oy = -0.9
            while oy <= 0.91:
                ox = -0.9
                while ox <= 0.91:
                    sx, sy = wx + ox * s, wy + oy * s
                    if point_inside_hex(sx - wx, sy - wy, s):
                        ix = round(((sx - x0) / width_px) * (iw - 1))
                        iy = round(((sy - y0) / height_px) * (ih - 1))
                        if 0 <= ix < iw and 0 <= iy < ih:
                            sampled += 1
                            if alpha_px[ix, iy] > ALPHA_THRESHOLD:
                                opaque += 1
                    ox += HEX_ALPHA_STEP
                oy += HEX_ALPHA_STEP
            if not sampled or not opaque:
                continue
            key = f"{dq},{dr}"
            if opaque / sampled >= PRIMARY_ALPHA_RATIO:
                primary_offsets.append(key)
            else:
                faint_offsets.append(key)

    return {
        "type": "massif",
        "file": image_name,
        "anchor_offset": "bottom-left",
        "zoom_factor": round(float(zoom_factor), 1),
        "render_width_hex": round(float(zoom_factor), 1),
        "render_height_hex": round(height_px / s, 1),
        "anchor_source_px": [anchor_x_px, ih - 1],
        "bounds_offset_hex": [
            round(x0 / s, 3), round(y0 / s, 3),
            round(x1 / s, 3), round(y1 / s, 3),
        ],
        "primary_offsets": MASSIF_FOOTPRINT_OVERRIDES.get(image_name, {}).get("primary_offsets", primary_offsets),
        "faint_offsets": MASSIF_FOOTPRINT_OVERRIDES.get(image_name, {}).get("faint_offsets", faint_offsets),
    }


def apply_offset(anchor, offset):
    aq, ar = [int(v) for v in anchor.split(",")]
    dq, dr = [int(v) for v in offset.split(",")]
    return f"{aq + dq},{ar + dr}"


def main():
    s = hex_size_px()
    minlon, minlat, maxlon, maxlat = EUROPE_BOUNDS
    dminlon, dminlat, dmaxlon, dmaxlat = REGION_BOUNDS  # Germany detail window

    countries = load_ne("ne_50m_admin_0_countries")
    clip = box(minlon - 1, minlat - 1, maxlon + 1, maxlat + 1)
    countries = countries[countries.geometry.intersects(clip)].copy()
    countries = countries[
        countries["ADMIN"].isin(EUROPE_ADMIN_ALLOW)
        | countries["ISO_A2"].isin(EUROPE_ISO_ALLOW)
    ].copy()
    germany = countries[countries["ADMIN"] == "Germany"].geometry.union_all()
    land_prep = prep(countries.geometry.union_all())
    # per-country prepared geometry + bbox + ISO code, for fast point lookup
    cgeo = []
    for _, row in countries.iterrows():
        iso = row.get("ISO_A2")
        if not iso or iso == "-99":
            iso = str(row.get("ADMIN", "??"))[:3].upper()
        cgeo.append((iso, prep(row.geometry), row.geometry.bounds, row.geometry))
    mountain_polys, massif_pieces = load_massifs()
    expansion_relief = load_expansion_relief_layers()
    def country_of(pt):
        for iso, pg, (bx0, by0, bx1, by1), _geom in cgeo:
            if bx0 <= pt.x <= bx1 and by0 <= pt.y <= by1 and pg.contains(pt):
                return iso
        return "??"

    def nearest_country_code(lon, lat):
        pt = Point(lon, lat)
        exact = country_of(pt)
        if exact != "??":
            return exact
        closest_iso = None
        closest_distance = None
        for iso, _pg, _bounds, geom in cgeo:
            distance = geom.distance(pt)
            if closest_distance is None or distance < closest_distance:
                closest_iso = iso
                closest_distance = distance
        return closest_iso

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
            hexes[f"{q},{r}"] = {"country": country_of(pt), "terrain": "plain",
                                 "center": [round(lon, 5), round(lat, 5)]}

    def nearest_land_key(lon, lat, radius=8, preferred_country=None):
        q, r = world_to_hex(*merc(lon, lat), s)
        closest_key = None
        closest_distance = None
        preferred_key = None
        preferred_distance = None
        for dq in range(-radius, radius + 1):
            for dr in range(-radius, radius + 1):
                if max(abs(dq), abs(dr), abs(dq + dr)) > radius:
                    continue
                key = f"{q + dq},{r + dr}"
                cell = hexes.get(key)
                if not cell:
                    continue
                distance = (cell["center"][0] - lon) ** 2 + (cell["center"][1] - lat) ** 2
                if closest_distance is None or distance < closest_distance:
                    closest_key = key
                    closest_distance = distance
                if preferred_country and cell.get("country") == preferred_country:
                    if preferred_distance is None or distance < preferred_distance:
                        preferred_key = key
                        preferred_distance = distance
        if preferred_key:
            return preferred_key
        return closest_key or f"{q},{r}"

    for iso, lon, lat in MICROSTATE_COUNTRY_ANCHORS:
        key = nearest_land_key(lon, lat)
        if key in hexes:
            hexes[key]["country"] = iso

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
    glyphs = {}

    def ensure_massif_glyph(image_name, zoom_factor):
        ref = glyph_ref(image_name)
        if ref not in glyphs:
            glyphs[ref] = glyph_footprint(image_name, zoom_factor, s)
        return ref

    def massif_cells(anchor, ref):
        glyph = glyphs[ref]
        offsets = glyph["primary_offsets"] + glyph["faint_offsets"]
        return [key for key in (apply_offset(anchor, offset) for offset in offsets) if key in hexes]

    # separate massif glyph pieces: Alps as its named segments, every other
    # massif as its own piece — each its own image, placed by real geo_bounds.
    for m in massif_pieces:
        gb = m["geo_bounds"]
        cx, cy = merc((gb["min_longitude"] + gb["max_longitude"]) / 2,
                      (gb["min_latitude"] + gb["max_latitude"]) / 2)
        aq, ar = world_to_hex(cx, cy, s)
        ax, ay = hex_to_world(aq, ar, s)
        zoom_factor = float(m.get("asset_width_hex", 5.0))
        ref = ensure_massif_glyph(m["image"], zoom_factor)
        anchor = f"{aq},{ar}"
        features.append({"id": m["id"], "glyph": "massif", "image": m["image"],
                         "glyph_ref": ref, "label": m["id"],
                         "anchor": anchor, "home": anchor})

    for layer in expansion_relief:
        min_lon, min_lat, max_lon, max_lat = layer["bounds"]
        cx, cy = merc((min_lon + max_lon) / 2, (min_lat + max_lat) / 2)
        aq, ar = world_to_hex(cx, cy, s)
        ax, ay = hex_to_world(aq, ar, s)
        image_name, zoom_factor = relief_image_for(layer["id"])
        ref = ensure_massif_glyph(image_name, zoom_factor)
        anchor = f"{aq},{ar}"
        cells = massif_cells(anchor, ref)
        if not cells:
            continue
        features.append({
            "id": f"relief-{layer['id']}",
            "glyph": "massif",
            "image": image_name,
            "glyph_ref": ref,
            "label": layer["label"],
            "anchor": anchor,
            "home": anchor,
            "source": "map_block_relief_layer",
        })

    for feature in features:
        if feature.get("glyph") != "massif":
            continue
        ref = feature.get("glyph_ref")
        keys = massif_cells(feature["anchor"], ref) if ref else feature.get("cells", [])
        for key in keys:
            if key in hexes:
                hexes[key]["terrain"] = "mountain"

    city_rows = []
    seen_city_ids = set()
    for name, lon, lat, kind, icon in CITIES + EUROPE_CITY_POINTS:
        city_rows.append((name, lon, lat, kind, icon, icon))
        seen_city_ids.add(icon)
    for name, lon, lat, kind, icon, city_id in load_map_block_cities():
        if city_id in seen_city_ids or icon in seen_city_ids:
            continue
        seen_city_ids.add(city_id)
        city_rows.append((name, lon, lat, kind, icon, city_id))

    for name, lon, lat, kind, icon, city_id in city_rows:
        if not (minlon <= lon <= maxlon and minlat <= lat <= maxlat):
            continue
        icon = icon if city_icon_exists(icon) else None
        preferred_country = CITY_COUNTRY_OVERRIDES.get(city_id) or nearest_country_code(lon, lat)
        anchor = nearest_land_key(lon, lat, preferred_country=preferred_country)
        features.append({"id": city_id, "glyph": "city", "kind": kind,
                         "label": name, "icon": icon, "lon": lon, "lat": lat,
                         "anchor": anchor, "home": anchor})

    # in-game transport objects (cable cars, funiculars, ...) within the map
    transport_rows = load_catalog_objects()
    seen_transport = {o["id"] for o in transport_rows}
    for oid, name, tid, lon, lat, country_code in STAGING_TRANSPORT_POINTS:
        if oid in seen_transport:
            continue
        seen_transport.add(oid)
        transport_rows.append({
            "id": oid,
            "name": name,
            "icon": TYPE_ICON.get(tid, "station"),
            "type_id": tid,
            "lon": lon,
            "lat": lat,
            "country_code": country_code,
            "source": "staging_transport_anchor",
        })

    for o in transport_rows:
        if not (minlon <= o["lon"] <= maxlon and minlat <= o["lat"] <= maxlat):
            continue
        anchor = nearest_land_key(o["lon"], o["lat"], preferred_country=o.get("country_code"))
        features.append({"id": o["id"], "glyph": "transport", "icon": o["icon"],
                         "label": o["name"], "type_id": o["type_id"],
                         "lon": o["lon"], "lat": o["lat"],
                         "anchor": anchor, "home": anchor})

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
        "glyphs": glyphs,
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
