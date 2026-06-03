"""Build the per-hex TV / telecom tower index for the drill-in panel.

Reads the local OSM store, bins each tower to its hex (same hex math as
map_editor/tools/gen_hex_map.py, params read from hex_map.json so it can't
drift) and records, per hex that exists in the grid:
- `count`: total towers in the hex (named + unnamed),
- `towers`: one entry per tower {name?, id, osm_type, height?}, named first.

    python3 -m map_pipeline.build_tv_towers

Writes map_editor/src/data/tv_towers_by_hex.json. See docs/pipelines/tv-towers.md.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "map_pipeline" / "data" / "osm_tv_towers.json"
HEX_MAP = ROOT / "map_editor" / "src" / "data" / "hex_map.json"
OUT = ROOT / "map_editor" / "src" / "data" / "tv_towers_by_hex.json"


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
    towers = json.loads(STORE.read_text(encoding="utf-8"))["towers"]
    grid_hexes = set(json.loads(HEX_MAP.read_text(encoding="utf-8"))["hexes"])
    to_hex = _binner()

    by_hex: dict[str, list] = defaultdict(list)
    dropped = 0
    for t in towers:
        h = to_hex(t["lat"], t["lon"])
        if h not in grid_hexes:  # only hexes we actually have on the map
            dropped += 1
            continue
        entry = {"id": t["id"], "osm_type": t["osm_type"]}
        if t.get("name"):
            entry["name"] = t["name"]
        if t.get("height"):
            entry["height"] = t["height"]
        by_hex[h].append(entry)

    out = {}
    for h, items in by_hex.items():
        # named first, then by id; entries keyed for stable, readable order
        items.sort(key=lambda r: (0 if "name" in r else 1, r.get("name", ""), r["id"]))
        # rebuild each dict so name comes first in JSON
        ordered_items = []
        for r in items:
            o = {}
            if "name" in r:
                o["name"] = r["name"]
            o["id"] = r["id"]
            o["osm_type"] = r["osm_type"]
            if "height" in r:
                o["height"] = r["height"]
            ordered_items.append(o)
        out[h] = {"count": len(ordered_items), "towers": ordered_items}

    ordered = dict(sorted(out.items(), key=lambda kv: -kv[1]["count"]))
    doc = {
        "schema": "cable-world.tv-towers.v1",
        "source": "OpenStreetMap TV / telecom towers",
        "generated_from": "map_pipeline/data/osm_tv_towers.json",
        "hex_count": len(ordered),
        "by_hex": ordered,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total = sum(v["count"] for v in ordered.values())
    named = sum(1 for v in ordered.values() for t in v["towers"] if "name" in t)
    print(f"wrote {OUT.relative_to(ROOT)}  hexes={len(ordered)} towers={total} "
          f"named={named} unnamed={total-named} dropped_offgrid={dropped}")
    print(f"  size: {OUT.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
