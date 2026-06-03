"""Fetch notable named mountain peaks from Overpass for the populated hex grid.

Network step. Mirrors ``fetch_osm_lifts.py``: derives the pull extent from
``hex_map.json`` (every populated hex), queries Overpass in 5° tiles that
actually contain hexes (ocean tiles are skipped), dedupes by node id and writes
the tracked store ``map_pipeline/data/osm_peaks.json`` that the build step reads.

KEPT LEAN to avoid a huge download / rate limits: only ``natural=peak`` nodes
that are NAMED and EITHER have an ``ele`` tag OR are notable (``wikidata`` /
``wikipedia``). Unnamed peaks and bare summit dots are dropped at query time.

    python3 -m map_pipeline.fetch_mountain_peaks

See docs/pipelines/mountain-regions.md for the full repeatable pipeline.
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
STORE = ROOT / "map_pipeline" / "data" / "osm_peaks.json"
# Per-tile checkpoint so a long pull can resume if it is interrupted/killed.
# Holds raw kept records keyed by id + the set of completed tiles. Deleted on
# a clean finish.
CHECKPOINT = ROOT / "map_pipeline" / "data" / "osm_peaks.checkpoint.json"

ENDPOINT = "https://overpass-api.de/api/interpreter"
TILE_DEG = 5  # tile size; only tiles containing >=1 hex are queried
PULLED_AT = "2026-06-03"  # scripts can't read the clock; bump on refresh.

# If Overpass keeps rate-limiting, raise this to shrink the pull (e.g. 1000 to
# keep only named peaks >= 1000 m). 0 keeps every named+notable peak.
MIN_ELE = 1000


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
    # Named peaks that have an elevation OR a wikidata/wikipedia link (notable).
    # nwr is unnecessary; peaks are nodes. The regex on name[~".",~"."] keeps
    # only peaks that actually carry a name tag.
    query = (
        f'[out:json][timeout:180];'
        f'('
        f'  node["natural"="peak"]["name"]["ele"]({s},{w},{n},{e});'
        f'  node["natural"="peak"]["name"]["wikidata"]({s},{w},{n},{e});'
        f'  node["natural"="peak"]["name"]["wikipedia"]({s},{w},{n},{e});'
        f');'
        f'out tags center;'  # 'center' also emits lat/lon for the matched nodes
    )
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


def parse_ele(raw: str | None) -> float | None:
    if not raw:
        return None
    # OSM ele can be "1234", "1234 m", "1,234", "1234.5". Take the leading number.
    txt = raw.strip().replace(",", ".")
    num = ""
    for ch in txt:
        if ch.isdigit() or (ch == "." and "." not in num) or (ch == "-" and not num):
            num += ch
        else:
            break
    try:
        return float(num)
    except ValueError:
        return None


def record(e: dict) -> dict | None:
    tags = e.get("tags", {})
    name = tags.get("name") or tags.get("name:en")
    if not name or "lat" not in e or "lon" not in e:
        return None
    ele = parse_ele(tags.get("ele"))
    if MIN_ELE and (ele is None or ele < MIN_ELE):
        return None
    rec = {"id": e["id"], "lat": e["lat"], "lon": e["lon"], "name": name}
    if ele is not None:
        rec["ele"] = round(ele, 1) if ele % 1 else int(ele)
    return rec


def main() -> None:
    tiles, bbox = hex_tiles()
    print(f"hex bbox (S,W,N,E): {bbox}  tiles to query: {len(tiles)}", flush=True)
    if MIN_ELE:
        print(f"LEAN MODE: only named peaks with ele >= {MIN_ELE} m", flush=True)

    # Resume from checkpoint if present. We store only KEPT records (already
    # filtered by record()) keyed by id, plus which tiles are done — so memory
    # and the checkpoint stay lean even across the dense Alpine tiles.
    kept: dict[int, dict] = {}
    done: set[tuple[int, int]] = set()
    if CHECKPOINT.exists():
        ck = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
        kept = {r["id"]: r for r in ck.get("peaks", [])}
        done = {tuple(t) for t in ck.get("done_tiles", [])}
        print(f"resuming: {len(done)} tiles done, {len(kept)} peaks so far", flush=True)

    failed: list = []
    for i, (lon0, lat0) in enumerate(tiles, 1):
        if (lon0, lat0) in done:
            continue
        print(f"[{i}/{len(tiles)}] tile lon {lon0}..{lon0+TILE_DEG} lat {lat0}..{lat0+TILE_DEG}", flush=True)
        try:
            els = fetch_tile(lat0, lon0, lat0 + TILE_DEG, lon0 + TILE_DEG)
        except RuntimeError as ex:
            # Overpass overload on a dense tile: skip it (do NOT mark done) so a
            # later rerun retries it, and keep going with the rest.
            print(f"   SKIP, will retry next run: {ex}", flush=True)
            failed.append((lon0, lat0))
            continue
        for el in els:
            rec = record(el)
            if rec is not None:
                kept[rec["id"]] = rec  # dedupe by node id across tile borders
        done.add((lon0, lat0))
        CHECKPOINT.write_text(
            json.dumps({"done_tiles": sorted(done), "peaks": list(kept.values())}, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"   cumulative kept peaks: {len(kept)}", flush=True)
        time.sleep(8)

    peaks = sorted(kept.values(), key=lambda r: r["id"])
    store = {
        "schema": "cable-world.osm-peaks.v1",
        "source": 'OpenStreetMap via Overpass API (node["natural"="peak"], named + ele/wikidata/wikipedia)',
        "endpoint": ENDPOINT,
        "extent": "populated hex grid (derived from hex_map.json)",
        "bbox_s_w_n_e": bbox,
        "pulled_at": PULLED_AT,
        "min_ele_filter": MIN_ELE,
        "note": (
            "Notable named mountain peaks across the whole populated hex grid. One "
            "record per OSM node (deduped by id). Only NAMED peaks that have an "
            "'ele' tag and/or a wikidata/wikipedia link are kept. "
            "See docs/pipelines/mountain-regions.md."
        ),
        "count": len(peaks),
        "peaks": peaks,
    }
    STORE.write_text(json.dumps(store, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if failed:
        print(f"NOTE: {len(failed)} tiles skipped on Overpass overload; rerun to fill: {failed}", flush=True)
    else:
        CHECKPOINT.unlink(missing_ok=True)  # clean finish: drop the resume file
    print(f"wrote {STORE.relative_to(ROOT)}: {len(peaks)} peaks", flush=True)


if __name__ == "__main__":
    main()
