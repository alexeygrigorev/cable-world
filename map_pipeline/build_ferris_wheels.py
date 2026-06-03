"""Build the per-hex Ferris-wheel index for the drill-in panel.

Reads the local OSM store (map_pipeline/data/osm_ferris_wheels.json), bins each
wheel to its hex using the same Mercator + hex math as the lift pipeline, and
emits only hexes that exist in hex_map.json:

    python3 -m map_pipeline.build_ferris_wheels

Writes map_editor/src/data/ferris_wheels_by_hex.json. Offline, stdlib only.
See docs/pipelines/ferris-wheels.md.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "map_pipeline" / "data" / "osm_ferris_wheels.json"
HEX_MAP = ROOT / "map_editor" / "src" / "data" / "hex_map.json"
OUT = ROOT / "map_editor" / "src" / "data" / "ferris_wheels_by_hex.json"


def _binner():
    grid = json.loads(HEX_MAP.read_text(encoding="utf-8"))["grid"]
    world = float(grid["world_size_px"])
    s = float(grid["hex_size_px"])

    def f(lat, lon):
        x = (lon + 180.0) / 360.0 * world
        siny = math.sin(math.radians(max(-85.05, min(85.05, lat))))
        y = (0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi)) * world
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
        return f"{rx},{rz}"

    return f


def main() -> None:
    wheels = json.loads(STORE.read_text(encoding="utf-8"))["wheels"]
    grid_hexes = set(json.loads(HEX_MAP.read_text(encoding="utf-8"))["hexes"])
    to_hex = _binner()

    by_hex: dict[str, list] = defaultdict(list)
    dropped = 0
    for w in wheels:
        h = to_hex(w["lat"], w["lon"])
        if h not in grid_hexes:  # only hexes we actually have on the map
            dropped += 1
            continue
        item = {"id": w["id"], "osm_type": w["osm_type"]}
        if w.get("name"):
            item["name"] = w["name"]
        if w.get("height"):
            item["height"] = w["height"]
        by_hex[h].append(item)

    out = {}
    for h, items in by_hex.items():
        # named first (by name), then unnamed (by id)
        items.sort(key=lambda r: (0, r["name"]) if r.get("name") else (1, str(r["id"])))
        out[h] = {"count": len(items), "wheels": items}

    ordered = dict(sorted(out.items(), key=lambda kv: -kv[1]["count"]))
    doc = {
        "schema": "cable-world.ferris-wheels.v1",
        "source": "OpenStreetMap Ferris / observation wheels",
        "generated_from": "map_pipeline/data/osm_ferris_wheels.json",
        "hex_count": len(ordered),
        "by_hex": ordered,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total = sum(v["count"] for v in ordered.values())
    named = sum(1 for v in ordered.values() for w in v["wheels"] if w.get("name"))
    print(
        f"wrote {OUT.relative_to(ROOT)}  hexes={len(ordered)} wheels={total} "
        f"named={named} dropped_off_grid={dropped}"
    )


if __name__ == "__main__":
    main()
