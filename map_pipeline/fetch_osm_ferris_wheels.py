"""Fetch Ferris / observation wheels from Overpass for the whole hex grid.

Network step. Ferris wheels (колесо обозрения) are few — a few hundred across
Europe — so this does a SINGLE whole-bbox Overpass query (bbox derived from
``hex_map.json``) instead of tiling. Queries nodes, ways and relations and
writes the tracked store ``map_pipeline/data/osm_ferris_wheels.json`` that the
build step reads.

    python3 -m map_pipeline.fetch_osm_ferris_wheels

See docs/pipelines/ferris-wheels.md for the full repeatable pipeline.
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEX_MAP = ROOT / "map_editor" / "src" / "data" / "hex_map.json"
STORE = ROOT / "map_pipeline" / "data" / "osm_ferris_wheels.json"

ENDPOINT = "https://overpass-api.de/api/interpreter"
PULLED_AT = "2026-06-03"  # scripts can't read the clock; bump on refresh.

# tourism=attraction with a name that looks like a Ferris/observation wheel.
NAME_RE = re.compile(
    r"ferris|big wheel|observation wheel|колесо обозрения|riesenrad|grande roue|noria",
    re.IGNORECASE,
)


def hex_bbox() -> list[float]:
    """Bounding box (S, W, N, E) of all populated hex centers."""
    hexes = json.loads(HEX_MAP.read_text(encoding="utf-8"))["hexes"]
    lons = [c["center"][0] for c in hexes.values()]
    lats = [c["center"][1] for c in hexes.values()]
    return [min(lats), min(lons), max(lats), max(lons)]


# Server-side name regex for the tourism=attraction fallback. Filtering by name
# on the server keeps the attraction branch cheap — an unfiltered
# tourism=attraction pull over the whole Europe bbox is huge and times Overpass
# out. Mirrors NAME_RE below.
NAME_REGEX_OVERPASS = "ferris|big wheel|observation wheel|колесо обозрения|riesenrad|grande roue|noria"


def build_query(s: float, w: float, n: float, e: float) -> str:
    bbox = f"({s},{w},{n},{e})"
    # nwr = nodes + ways + relations; out center gives a coordinate for w/r.
    return (
        "[out:json][timeout:180];"
        "("
        f'nwr["attraction"="big_wheel"]{bbox};'
        f'nwr["man_made"="ferris_wheel"]{bbox};'
        f'nwr["tourism"="attraction"]["name"~"{NAME_REGEX_OVERPASS}",i]{bbox};'
        ");"
        "out tags center;"
    )


def fetch(query: str) -> list[dict]:
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
        except (urllib.error.URLError, TimeoutError) as ex:
            wait = 15 * (attempt + 1)
            print(f"   {ex}: backoff {wait}s", flush=True)
            time.sleep(wait)
            continue
    raise RuntimeError("giving up on Overpass query")


def is_wheel(tags: dict) -> bool:
    """True for actual Ferris/observation wheels.

    big_wheel / ferris_wheel are kept unconditionally; a tourism=attraction is
    kept only when its name matches the wheel regex (so the broad attraction
    pull does not flood the store with unrelated attractions).
    """
    if tags.get("attraction") == "big_wheel":
        return True
    if tags.get("man_made") == "ferris_wheel":
        return True
    if tags.get("tourism") == "attraction":
        name = tags.get("name") or tags.get("name:en") or ""
        return bool(NAME_RE.search(name))
    return False


def coord(e: dict) -> tuple[float, float] | None:
    if e["type"] == "node":
        return e.get("lat"), e.get("lon")
    c = e.get("center")
    if c:
        return c.get("lat"), c.get("lon")
    return None


def record(e: dict) -> dict | None:
    tags = e.get("tags", {})
    if not is_wheel(tags):
        return None
    ll = coord(e)
    if not ll or ll[0] is None or ll[1] is None:
        return None
    lat, lon = ll
    rec = {"id": e["id"], "osm_type": e["type"], "lat": lat, "lon": lon}
    name = tags.get("name") or tags.get("name:en")
    if name:
        rec["name"] = name
    height = tags.get("height")
    if height:
        rec["height"] = height
    return rec


def main() -> None:
    bbox = hex_bbox()
    print(f"hex bbox (S,W,N,E): {bbox}", flush=True)
    query = build_query(*bbox)
    elements = fetch(query)
    print(f"raw elements returned: {len(elements)}", flush=True)

    # dedupe by (osm_type, id) — same wheel can appear via several tags.
    by_key: dict[tuple[str, int], dict] = {}
    for e in elements:
        rec = record(e)
        if rec is None:
            continue
        by_key[(rec["osm_type"], rec["id"])] = rec

    wheels = sorted(by_key.values(), key=lambda r: (r["osm_type"], r["id"]))
    store = {
        "schema": "cable-world.osm-ferris-wheels.v1",
        "source": (
            "OpenStreetMap via Overpass API "
            '(attraction=big_wheel, man_made=ferris_wheel, named tourism=attraction)'
        ),
        "endpoint": ENDPOINT,
        "extent": "populated hex grid (derived from hex_map.json)",
        "bbox_s_w_n_e": bbox,
        "pulled_at": PULLED_AT,
        "note": (
            "Ferris / observation wheels (колесо обозрения) across the whole "
            "populated hex grid. One record per OSM element (deduped by "
            "osm_type+id). See docs/pipelines/ferris-wheels.md."
        ),
        "count": len(wheels),
        "wheels": wheels,
    }
    STORE.write_text(json.dumps(store, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    named = sum(1 for w in wheels if w.get("name"))
    print(f"wrote {STORE.relative_to(ROOT)}: {len(wheels)} wheels ({named} named)", flush=True)


if __name__ == "__main__":
    main()
