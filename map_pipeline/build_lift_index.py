"""Build the per-hex lift index for the drill-in panel.

Reads the local OSM store, classifies each lift (shared map_pipeline/lift_groups),
bins it to its hex and records:
- `counts`: total lifts per display group (named + unnamed),
- `lifts`: the NAMED lifts only, each {name, group, type} (raw aerialway type kept
  so the UI can say exactly what each one is).
Unnamed lifts are not listed individually (without a name there is nothing to
look up), but they stay in `counts`, so the UI can still say e.g.
"без названия: бугельные ×3, кресельные ×2" by subtracting the named ones.

    python3 -m map_pipeline.build_lift_index

Writes map_editor/src/data/lift_index_by_hex.json. See docs/pipelines/osm-lift-density.md.
"""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from map_pipeline.lift_groups import GROUPS, classify

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "map_pipeline" / "data" / "osm_lifts.json"
HEX_MAP = ROOT / "map_editor" / "src" / "data" / "hex_map.json"
OUT = ROOT / "map_editor" / "src" / "data" / "lift_index_by_hex.json"

GROUP_ORDER = {g: i for i, g in enumerate(GROUPS)}


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
    lifts = json.loads(STORE.read_text(encoding="utf-8"))["lifts"]
    grid_hexes = set(json.loads(HEX_MAP.read_text(encoding="utf-8"))["hexes"])
    to_hex = _binner()
    counts: dict[str, Counter] = defaultdict(Counter)
    named: dict[str, list] = defaultdict(list)
    unnamed: dict[str, list] = defaultdict(list)
    for e in lifts:
        group = classify(e["type"], e.get("name"))
        if group is None:
            continue
        h = to_hex(e["lat"], e["lon"])
        if h not in grid_hexes:  # only hexes we actually have on the map
            continue
        counts[h][group] += 1
        if e.get("name"):
            named[h].append({"name": e["name"], "group": group, "type": e["type"], "id": e["id"]})
        else:
            # no name to look up, but keep id/type so the UI can still link to OSM
            unnamed[h].append({"group": group, "type": e["type"], "id": e["id"]})

    out = {}
    for h, c in counts.items():
        items = named.get(h, [])
        items.sort(key=lambda r: (GROUP_ORDER.get(r["group"], 99), r["name"]))
        anon = unnamed.get(h, [])
        anon.sort(key=lambda r: (GROUP_ORDER.get(r["group"], 99), r["id"]))
        out[h] = {
            "counts": {"passenger_total": sum(c.values()), **{g: c[g] for g in GROUPS if c[g]}},
            "lifts": items,
            "unnamed": anon,
        }

    ordered = dict(sorted(out.items(), key=lambda kv: -kv[1]["counts"]["passenger_total"]))
    doc = {
        "schema": "cable-world.lift-index.v1",
        "source": "OpenStreetMap aerialway",
        "generated_from": "map_pipeline/data/osm_lifts.json",
        "groups": GROUPS,
        "hex_count": len(ordered),
        "by_hex": ordered,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total = sum(v["counts"]["passenger_total"] for v in ordered.values())
    named_total = sum(len(v["lifts"]) for v in ordered.values())
    print(f"wrote {OUT.relative_to(ROOT)}  hexes={len(ordered)} lifts={total} named={named_total} unnamed={total-named_total}")
    print(f"  size: {OUT.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
