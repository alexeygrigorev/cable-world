"""Fetch TV / radio / telecom towers from Overpass for the whole hex grid.

Network step. Derives the pull bbox from ``hex_map.json`` (every populated hex)
and queries Overpass for broadcast / communication towers and masts. The whole
continent is far too heavy for a single query on the frequently-busy Overpass
channel, so we cut the bbox into big tiles and **adaptively subdivide** any tile
whose cheap ``out count`` probe exceeds ``MAX_PER_FETCH`` — this keeps every
``out tags center`` response small. Patient backoff on 429/502/504 and transient
socket errors, dedupe across tile borders, and the store is **rewritten after
every leaf tile** so a late failure never loses earlier progress (re-running
resumes from the last good snapshot). Writes the tracked store
``map_pipeline/data/osm_tv_towers.json`` that the build step reads.

    python3 -m map_pipeline.fetch_osm_towers

See docs/pipelines/tv-towers.md for the full repeatable pipeline.
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
STORE = ROOT / "map_pipeline" / "data" / "osm_tv_towers.json"

ENDPOINT = "https://overpass-api.de/api/interpreter"
PULLED_AT = "2026-06-03"  # scripts can't read the clock; bump on refresh.

# Big seed tiles; tiles over MAX_PER_FETCH are recursively quartered so each
# data fetch stays small enough to survive the busy channel.
LON_STEP = 10
LAT_STEP = 9
MAX_PER_FETCH = 4000  # split any tile whose count probe exceeds this

# The three OSM ways of tagging a TV / radio / telecom tower:
#   man_made=communications_tower            (big broadcast towers, Fernsehturm)
#   man_made=tower + tower:type=communication
#   man_made=mast  + tower:type=communication
SELECTORS = (
    'nwr["man_made"="communications_tower"](BBOX);'
    'nwr["man_made"="tower"]["tower:type"="communication"](BBOX);'
    'nwr["man_made"="mast"]["tower:type"="communication"](BBOX);'
)


def hex_bbox() -> list[float]:
    """Bounding box (S, W, N, E) of all populated hex centers."""
    hexes = json.loads(HEX_MAP.read_text(encoding="utf-8"))["hexes"]
    lons = [cell["center"][0] for cell in hexes.values()]
    lats = [cell["center"][1] for cell in hexes.values()]
    return [min(lats), min(lons), max(lats), max(lons)]


def tiles(bbox: list[float]) -> list[tuple[float, float, float, float]]:
    """Cut the bbox into big (LON_STEP x LAT_STEP) tiles, each (s, w, n, e)."""
    s, w, n, e = bbox
    out = []
    lat0 = math.floor(s / LAT_STEP) * LAT_STEP
    while lat0 < n:
        lon0 = math.floor(w / LON_STEP) * LON_STEP
        while lon0 < e:
            out.append((max(lat0, s), max(lon0, w),
                        min(lat0 + LAT_STEP, n), min(lon0 + LON_STEP, e)))
            lon0 += LON_STEP
        lat0 += LAT_STEP
    return out


def _post(query: str) -> dict:
    """POST a query with patient backoff on busy/transient Overpass errors."""
    data = urllib.parse.urlencode({"data": query}).encode()
    for attempt in range(8):
        try:
            req = urllib.request.Request(
                ENDPOINT, data=data, headers={"User-Agent": "cable-world-research/1.0"}
            )
            return json.loads(urllib.request.urlopen(req, timeout=300).read())
        except urllib.error.HTTPError as ex:
            if ex.code in (429, 502, 504):
                wait = 15 * (attempt + 1)
                print(f"   {ex.code}: backoff {wait}s", flush=True)
                time.sleep(wait)
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as ex:
            wait = 15 * (attempt + 1)
            print(f"   {ex}: backoff {wait}s", flush=True)
            time.sleep(wait)
            continue
    raise RuntimeError("giving up on Overpass query")


def count_probe(s: float, w: float, n: float, e: float) -> int:
    bbox = f"{s},{w},{n},{e}"
    query = f"[out:json][timeout:300];({SELECTORS.replace('BBOX', bbox)});out count;"
    res = _post(query)
    tags = res["elements"][0]["tags"] if res.get("elements") else {}
    return int(tags.get("total", 0))


def fetch_bbox(s: float, w: float, n: float, e: float) -> list[dict]:
    bbox = f"{s},{w},{n},{e}"
    query = f"[out:json][timeout:300];({SELECTORS.replace('BBOX', bbox)});out tags center;"
    return _post(query)["elements"]


def _osm_type(el: dict) -> str:
    t = el.get("type", "")
    return t if t in ("node", "way", "relation") else "node"


def record(el: dict) -> dict | None:
    osm_type = _osm_type(el)
    if osm_type == "node":
        lat, lon = el.get("lat"), el.get("lon")
    else:
        center = el.get("center")
        if not center:
            return None
        lat, lon = center["lat"], center["lon"]
    if lat is None or lon is None:
        return None
    tags = el.get("tags", {})
    rec = {"id": el["id"], "osm_type": osm_type, "lat": lat, "lon": lon}
    name = tags.get("name") or tags.get("name:en") or tags.get("ref")
    if name:
        rec["name"] = name
    height = tags.get("height") or tags.get("tower:height")
    if height:
        rec["height"] = height
    return rec


def quarter(s: float, w: float, n: float, e: float):
    """Split a tile into four quadrants."""
    mlat, mlon = (s + n) / 2, (w + e) / 2
    return [(s, w, mlat, mlon), (s, mlon, mlat, e),
            (mlat, w, n, mlon), (mlat, mlon, n, e)]


def write_store(bbox: list[float], towers: list[dict]) -> None:
    towers = sorted(towers, key=lambda r: (r["osm_type"], r["id"]))
    store = {
        "schema": "cable-world.osm-tv-towers.v1",
        "source": (
            "OpenStreetMap via Overpass API "
            "(man_made=communications_tower; man_made=tower|mast + tower:type=communication)"
        ),
        "endpoint": ENDPOINT,
        "extent": "populated hex grid bbox (derived from hex_map.json)",
        "bbox_s_w_n_e": bbox,
        "pulled_at": PULLED_AT,
        "note": (
            "TV / radio / telecom towers and masts across the whole populated hex "
            "grid bbox. One record per OSM element (deduped by osm_type+id). "
            "See docs/pipelines/tv-towers.md."
        ),
        "count": len(towers),
        "towers": towers,
    }
    STORE.write_text(json.dumps(store, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_resume() -> tuple[dict, set]:
    """Resume from a partial store if present (dedupe + skip done tiles)."""
    by_key: dict = {}
    done: set = set()
    if STORE.exists():
        try:
            prev = json.loads(STORE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return by_key, done
        for r in prev.get("towers", []):
            by_key[(r["osm_type"], r["id"])] = r
        done = set(tuple(t) for t in prev.get("_done_tiles", []))
    return by_key, done


def collect(tile, by_key: dict, depth: int = 0) -> None:
    """Fetch one tile, subdividing on count > MAX_PER_FETCH."""
    s, w, n, e = tile
    cnt = count_probe(s, w, n, e)
    pad = "  " * depth
    print(f"{pad}tile lat {s:.2f}..{n:.2f} lon {w:.2f}..{e:.2f}  count={cnt}", flush=True)
    time.sleep(3)
    if cnt == 0:
        return
    if cnt > MAX_PER_FETCH:
        for q in quarter(s, w, n, e):
            collect(q, by_key, depth + 1)
        return
    added = 0
    for el in fetch_bbox(s, w, n, e):
        rec = record(el)
        if rec is None:
            continue
        key = (rec["osm_type"], rec["id"])
        if key not in by_key:
            added += 1
        by_key[key] = rec  # dedupe across tile borders
    print(f"{pad}  +{added} (total {len(by_key)})", flush=True)
    time.sleep(5)


def main() -> None:
    bbox = hex_bbox()
    print(f"hex bbox (S,W,N,E): {bbox}", flush=True)
    seed = tiles(bbox)
    print(f"seed tiles: {len(seed)} ({LON_STEP}deg lon x {LAT_STEP}deg lat); "
          f"subdivide if count > {MAX_PER_FETCH}", flush=True)

    by_key, done = load_resume()
    if by_key:
        print(f"resuming from partial store: {len(by_key)} towers, "
              f"{len(done)} seed tiles already done", flush=True)

    for i, tile in enumerate(seed, 1):
        if tuple(tile) in done:
            continue
        print(f"[{i}/{len(seed)}]", flush=True)
        collect(tile, by_key)
        done.add(tuple(tile))
        write_store(bbox, list(by_key.values()))  # incremental: never lose progress

    write_store(bbox, list(by_key.values()))
    print(f"wrote {STORE.relative_to(ROOT)}: {len(by_key)} towers", flush=True)


if __name__ == "__main__":
    main()
