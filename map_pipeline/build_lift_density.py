"""Build per-hex lift density from the local OSM lift store.

Reads the tracked snapshot ``map_pipeline/data/alps_osm_lifts.json`` (no
network), keeps passenger uphill transport, groups it, bins each lift onto the
project's global Web Mercator hex grid (same math as
``map_editor/tools/gen_hex_map.py``, grid params read from ``hex_map.json``) and
writes ``map_editor/src/data/alps_lift_density.json``.

    python3 -m map_pipeline.build_lift_density

See docs/pipelines/osm-lift-density.md.
"""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from map_pipeline.lift_groups import classify

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "map_pipeline" / "data" / "osm_lifts.json"
HEX_MAP = ROOT / "map_editor" / "src" / "data" / "hex_map.json"
OUT = ROOT / "map_editor" / "src" / "data" / "lift_density.json"


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


def main() -> None:
    store = json.loads(STORE.read_text(encoding="utf-8"))
    lifts = store["lifts"]
    hexmap = json.loads(HEX_MAP.read_text(encoding="utf-8"))
    world_px = float(hexmap["grid"]["world_size_px"])
    hex_size = float(hexmap["grid"]["hex_size_px"])
    grid_hexes = set(hexmap["hexes"])
    latlon_to_hex = _binner(world_px, hex_size)

    by_hex: dict[str, Counter] = defaultdict(Counter)
    named_by_hex: dict[str, Counter] = defaultdict(Counter)  # named-only per group
    totals: Counter = Counter()
    dropped = 0
    for e in lifts:
        group = classify(e["type"], e.get("name"))
        if group is None:
            continue
        h = latlon_to_hex(e["lat"], e["lon"])
        if h not in grid_hexes:  # lift outside the populated hex grid
            dropped += 1
            continue
        by_hex[h]["passenger_total"] += 1
        by_hex[h][group] += 1
        totals[group] += 1
        if e.get("name"):
            named_by_hex[h][group] += 1

    # Stable ordering: densest first, then hex id.
    ordered = sorted(by_hex.items(), key=lambda kv: (-kv[1]["passenger_total"], kv[0]))
    out = {
        "schema": "cable-world.lift-density.v1",
        "source": "OpenStreetMap aerialway (passenger uphill transport)",
        "generated_from": "map_pipeline/data/osm_lifts.json",
        "groups": ["cable_car", "gondola", "chair_lift", "surface_tow", "zip_line", "water_ski"],
        "totals": {"passenger_total": sum(totals.values()), **dict(totals)},
        "hex_count": len(by_hex),
        # each hex: per-group totals + "named" sub-map (named-only) so the UI can
        # filter "с названием / без названия" without loading the big index.
        "by_hex": {h: {**dict(c), "named": dict(named_by_hex[h])} for h, c in ordered},
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  passenger lifts: {out['totals']['passenger_total']}  groups: {dict(totals)}")
    print(f"  hexes with lifts: {out['hex_count']}  (dropped {dropped} lifts outside the grid)")
    print("  densest:", ", ".join(f"{h}={c['passenger_total']}" for h, c in ordered[:5]))


if __name__ == "__main__":
    main()
