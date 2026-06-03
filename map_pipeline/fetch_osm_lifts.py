"""Fetch aerialway lift centers from Overpass for the whole populated hex grid.

Network step. Derives the pull extent from ``hex_map.json`` (every populated
hex), queries Overpass in 5° tiles that actually contain hexes (ocean tiles are
skipped), dedupes by way id and writes the tracked store
``map_pipeline/data/osm_lifts.json`` that the build steps read.

    python3 -m map_pipeline.fetch_osm_lifts

See docs/pipelines/osm-lift-density.md for the full repeatable pipeline.
"""
from __future__ import annotations

import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEX_MAP = ROOT / "map_editor" / "src" / "data" / "hex_map.json"
STORE = ROOT / "map_pipeline" / "data" / "osm_lifts.json"

ENDPOINT = "https://overpass-api.de/api/interpreter"
TILE_DEG = 5  # tile size; only tiles containing >=1 hex are queried
PULLED_AT = "2026-06-03"  # scripts can't read the clock; bump on refresh.


def hex_tiles() -> tuple[list[tuple[int, int]], list[float]]:
    """5° tiles (lon0, lat0) that contain at least one populated hex, + bbox."""
    hexes = json.loads(HEX_MAP.read_text(encoding="utf-8"))["hexes"]
    tiles, lons, lats = set(), [], []
    for cell in hexes.values():
        lon, lat = cell["center"]
        lons.append(lon)
        lats.append(lat)
        tiles.add((math.floor(lon / TILE_DEG) * TILE_DEG, math.floor(lat / TILE_DEG) * TILE_DEG))
    bbox = [min(lats), min(lons), max(lats), max(lons)]
    return sorted(tiles), bbox


def fetch_tile(s: float, w: float, n: float, e: float) -> list[dict]:
    query = f'[out:json][timeout:180];(way["aerialway"]({s},{w},{n},{e}););out tags center;'
    data = urllib.parse.urlencode({"data": query}).encode()
    for attempt in range(6):
        try:
            req = urllib.request.Request(
                ENDPOINT, data=data, headers={"User-Agent": "cable-world-research/1.0"}
            )
            return json.loads(urllib.request.urlopen(req, timeout=200).read())["elements"]
        except urllib.error.HTTPError as ex:
            if ex.code in (429, 502, 504):
                wait = 15 * (attempt + 1)
                print(f"   {ex.code}: backoff {wait}s", flush=True)
                time.sleep(wait)
                continue
            raise
    raise RuntimeError(f"giving up on tile {(s, w, n, e)}")


def record(e: dict) -> dict | None:
    if "center" not in e:
        return None
    tags = e.get("tags", {})
    name = tags.get("name") or tags.get("name:en") or tags.get("ref")
    rec = {"id": e["id"], "lat": e["center"]["lat"], "lon": e["center"]["lon"],
           "type": tags.get("aerialway", "unknown")}
    if name:
        rec["name"] = name
    return rec


def main() -> None:
    tiles, bbox = hex_tiles()
    print(f"hex bbox (S,W,N,E): {bbox}  tiles to query: {len(tiles)}", flush=True)
    elements: dict[int, dict] = {}
    for i, (lon0, lat0) in enumerate(tiles, 1):
        print(f"[{i}/{len(tiles)}] tile lon {lon0}..{lon0+TILE_DEG} lat {lat0}..{lat0+TILE_DEG}", flush=True)
        for el in fetch_tile(lat0, lon0, lat0 + TILE_DEG, lon0 + TILE_DEG):
            elements[el["id"]] = el  # dedupe by way id across tile borders
        print(f"   cumulative ways: {len(elements)}", flush=True)
        time.sleep(8)

    lifts = sorted(
        (r for r in (record(e) for e in elements.values()) if r is not None),
        key=lambda r: r["id"],
    )
    store = {
        "schema": "cable-world.osm-lifts.v1",
        "source": 'OpenStreetMap via Overpass API (way["aerialway"])',
        "endpoint": ENDPOINT,
        "extent": "populated hex grid (derived from hex_map.json)",
        "bbox_s_w_n_e": bbox,
        "pulled_at": PULLED_AT,
        "note": (
            "Raw aerialway way centers across the whole populated hex grid. One "
            "record per OSM way (deduped by id). 'type' is the raw aerialway=* "
            "value. See docs/pipelines/osm-lift-density.md."
        ),
        "count": len(lifts),
        "lifts": lifts,
    }
    STORE.write_text(json.dumps(store, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {STORE.relative_to(ROOT)}: {len(lifts)} lifts", flush=True)


if __name__ == "__main__":
    main()
