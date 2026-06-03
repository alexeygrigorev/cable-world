"""Build per-hex mountain regions + icon size from curated polygons and OSM peaks.

Offline (stdlib only). For every populated hex in ``hex_map.json`` it:

1. point-in-polygon tests the hex center against ``mountain_systems.json``
   (subregions first, then systems) to assign a mountain system + subregion;
2. bins ``osm_peaks.json`` notable peaks onto the hex grid (same math as
   ``map_editor/tools/gen_hex_map.py``) and attaches up to ~8 top peaks by ele;
3. computes an icon_size class (small|medium|large) from the region magnitude
   and the max peak elevation, taking the larger of the two signals.

Only hexes that have a mountain region OR at least one notable peak are emitted.

    python3 -m map_pipeline.build_mountain_regions

Writes map_editor/src/data/mountain_regions_by_hex.json. See
docs/pipelines/mountain-regions.md.
"""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEX_MAP = ROOT / "map_editor" / "src" / "data" / "hex_map.json"
SYSTEMS = ROOT / "map_pipeline" / "data" / "mountain_systems.json"
PEAKS = ROOT / "map_pipeline" / "data" / "osm_peaks.json"
OUT = ROOT / "map_editor" / "src" / "data" / "mountain_regions_by_hex.json"
ELEV = ROOT / "map_pipeline" / "data" / "hex_elevation.json"
# A hex inside a range polygon only counts as mountain above this elevation,
# so sea-level / plain hexes (Venice lagoon, Po valley) drop out.
MOUNTAIN_MIN_ELE = 300

MAX_PEAKS_PER_HEX = 8
SIZE_RANK = {"small": 0, "medium": 1, "large": 2}
SIZE_BY_RANK = {v: k for k, v in SIZE_RANK.items()}

# Peak-elevation -> icon size signal.
ELE_LARGE = 2500
ELE_MEDIUM = 1200


def _binner(world_px: float, hex_size: float):
    def latlon_to_hex(lat: float, lon: float) -> str:
        x = (lon + 180.0) / 360.0 * world_px
        siny = math.sin(math.radians(max(-85.05, min(85.05, lat))))
        y = (0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi)) * world_px
        qf = ((math.sqrt(3) / 3) * x - (1 / 3) * y) / hex_size
        rf = (2 / 3) * y / hex_size
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
        return f"{rx},{rz}"

    return latlon_to_hex


def point_in_polygon(lon: float, lat: float, poly: list[list[float]]) -> bool:
    """Ray-casting point-in-polygon. poly is a list of [lon, lat] vertices."""
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i][0], poly[i][1]
        xj, yj = poly[j][0], poly[j][1]
        if ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / (yj - yi) + xi
        ):
            inside = not inside
        j = i
    return inside


def ele_size(max_ele: float | None) -> int:
    if max_ele is None:
        return SIZE_RANK["small"]
    if max_ele >= ELE_LARGE:
        return SIZE_RANK["large"]
    if max_ele >= ELE_MEDIUM:
        return SIZE_RANK["medium"]
    return SIZE_RANK["small"]


def main() -> None:
    hexmap = json.loads(HEX_MAP.read_text(encoding="utf-8"))
    world_px = float(hexmap["grid"]["world_size_px"])
    hex_size = float(hexmap["grid"]["hex_size_px"])
    hexes = hexmap["hexes"]
    latlon_to_hex = _binner(world_px, hex_size)

    # Self-check the binner against real hex centers before trusting it.
    ok = sum(1 for k, c in hexes.items() if latlon_to_hex(c["center"][1], c["center"][0]) == k)
    print(f"binner self-check: {ok}/{len(hexes)} hex centers map back to their key")
    if ok != len(hexes):
        bad = [k for k, c in hexes.items() if latlon_to_hex(c["center"][1], c["center"][0]) != k][:5]
        print(f"  WARNING: {len(hexes) - ok} mismatches, e.g. {bad}")

    sys_doc = json.loads(SYSTEMS.read_text(encoding="utf-8"))
    systems = sys_doc["systems"]
    subregions = sys_doc["subregions"]

    # per-hex elevation gate (drops flat hexes that fall inside coarse polygons)
    elev = json.loads(ELEV.read_text(encoding="utf-8")).get("by_hex", {}) if ELEV.exists() else {}

    # Bin notable peaks onto hexes (store may be absent if the network step
    # hasn't run yet; the region layer still works without it).
    peaks_by_hex: dict[str, list] = defaultdict(list)
    peak_total = 0
    if PEAKS.exists():
        store = json.loads(PEAKS.read_text(encoding="utf-8"))
        for p in store.get("peaks", []):
            h = latlon_to_hex(p["lat"], p["lon"])
            if h not in hexes:
                continue
            peaks_by_hex[h].append(p)
            peak_total += 1
        print(f"peaks: {peak_total} notable peaks binned into {len(peaks_by_hex)} hexes")
    else:
        print(f"NOTE: {PEAKS.relative_to(ROOT)} not found — run fetch_mountain_peaks first for peaks")

    by_hex: dict[str, dict] = {}
    size_counts: Counter = Counter()
    system_counts: Counter = Counter()

    for key, cell in hexes.items():
        lon, lat = cell["center"]
        entry: dict = {}

        # Region classification: subregions first (more specific), then systems.
        region_size = None
        for sub in subregions:
            if point_in_polygon(lon, lat, sub["polygon"]):
                entry["system"] = sub["system"]
                entry["subregion"] = sub["name_ru"]
                region_size = SIZE_RANK[sub["magnitude"]]
                break
        if "system" not in entry:
            for sysreg in systems:
                if point_in_polygon(lon, lat, sysreg["polygon"]):
                    entry["system"] = sysreg["name_ru"]
                    region_size = SIZE_RANK[sysreg["magnitude"]]
                    break

        # Notable peaks in this hex (top by elevation, named-with-ele preferred).
        hex_peaks = peaks_by_hex.get(key, [])
        max_ele = None
        if hex_peaks:
            with_ele = [p for p in hex_peaks if "ele" in p]
            if with_ele:
                max_ele = max(p["ele"] for p in with_ele)
            ranked = sorted(hex_peaks, key=lambda p: (-(p.get("ele") or -1), p["name"]))
            top = ranked[:MAX_PEAKS_PER_HEX]
            entry["peaks"] = [
                ({"name": p["name"], "ele": p["ele"]} if "ele" in p else {"name": p["name"]})
                for p in top
            ]

        # Keep a hex only if it actually reads as mountainous:
        #  - it has a notable peak (always keep), or
        #  - it is inside a range polygon AND high enough (elevation gate).
        # A flat hex inside a coarse polygon (Venice, Po valley) is dropped.
        # Unknown elevation (null, e.g. east of EU-DEM) is not used to drop.
        hex_ele = elev.get(key)
        if not hex_peaks:
            if "system" not in entry:
                continue
            if hex_ele is not None and hex_ele < MOUNTAIN_MIN_ELE:
                continue

        # icon_size = max of region magnitude, peak elevation and hex elevation.
        candidates = []
        if region_size is not None:
            candidates.append(region_size)
        if max_ele is not None:
            candidates.append(ele_size(max_ele))
        if hex_ele is not None:
            candidates.append(ele_size(hex_ele))
        if not candidates:
            candidates.append(SIZE_RANK["small"])
        size_rank = max(candidates)
        entry["icon_size"] = SIZE_BY_RANK[size_rank]
        if max_ele is not None:
            entry["max_ele"] = max_ele
        elif hex_ele is not None:
            entry["max_ele"] = hex_ele

        by_hex[key] = entry
        size_counts[entry["icon_size"]] += 1
        if "system" in entry:
            system_counts[entry["system"]] += 1

    # Stable order: largest icon first, then by hex id.
    ordered = dict(
        sorted(by_hex.items(), key=lambda kv: (-SIZE_RANK[kv[1]["icon_size"]], kv[0]))
    )
    doc = {
        "schema": "cable-world.mountain-regions.v1",
        "source": "curated mountain_systems.json polygons + OpenStreetMap notable peaks",
        "generated_from": ["map_pipeline/data/mountain_systems.json", "map_pipeline/data/osm_peaks.json"],
        "icon_size_rule": (
            f"max of region magnitude and peak elevation (>= {ELE_LARGE} m -> large, "
            f">= {ELE_MEDIUM} m -> medium, else small)"
        ),
        "hex_count": len(ordered),
        "by_hex": ordered,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {OUT.relative_to(ROOT)}  hexes={len(ordered)}  size={OUT.stat().st_size//1024} KB")
    print("  by icon_size:", dict(sorted(size_counts.items(), key=lambda kv: -SIZE_RANK[kv[0]])))
    print("  by system:")
    for name, n in system_counts.most_common():
        print(f"    {name}: {n}")


if __name__ == "__main__":
    main()
