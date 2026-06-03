"""Fetch per-hex elevation above sea level for the whole populated hex grid.

Network step. Reads every populated hex center from ``hex_map.json`` and queries
the public opentopodata DEM API (dataset ``eudem25m``, with ``srtm90m`` fallback
for points outside eudem coverage) in batches of 100 at ~1 request/second, then
writes the tracked store ``map_pipeline/data/hex_elevation.json`` that the editor
elevation overlay reads.

    python3 -m map_pipeline.fetch_hex_elevation

Resumable: hex ids already present in an existing partial output are skipped.

See docs/pipelines/hex-elevation.md for the full repeatable pipeline.
"""
from __future__ import annotations

import json
import math
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEX_MAP = ROOT / "map_editor" / "src" / "data" / "hex_map.json"
OUT = ROOT / "map_pipeline" / "data" / "hex_elevation.json"

API = "https://api.opentopodata.org/v1/{dataset}"
PRIMARY = "eudem25m"   # European 25m DEM, covers lon -24..45 lat 35..71
FALLBACK = "srtm90m"   # global ~90m DEM, fills gaps (far north, coast, etc.)
BATCH = 100            # max locations per opentopodata request
THROTTLE = 1.1         # seconds between requests (API limit ~1 req/s)
HEADERS = {"User-Agent": "cable-world/1.0"}
PULLED_AT = "2026-06-03"  # scripts can't read the clock; bump on refresh.

SCHEMA = "cable-world.hex-elevation.v1"
SOURCE = "opentopodata eudem25m (+srtm90m fallback)"


def load_hexes() -> dict[str, list[float]]:
    """{"q,r": [lon, lat]} for every populated hex."""
    hexes = json.loads(HEX_MAP.read_text(encoding="utf-8"))["hexes"]
    return {key: cell["center"] for key, cell in hexes.items()}


def load_partial() -> dict[str, int | None]:
    """Resume support: previously written elevations (real values only)."""
    if not OUT.exists():
        return {}
    try:
        prev = json.loads(OUT.read_text(encoding="utf-8")).get("by_hex", {})
    except (json.JSONDecodeError, OSError):
        return {}
    # Keep only resolved (non-null) hexes so nulls get retried on a re-run.
    return {k: v for k, v in prev.items() if v is not None}


def query(dataset: str, points: list[tuple[float, float]]) -> list[float | None]:
    """One opentopodata batch -> elevation per point (m, or None). Backs off."""
    locations = "|".join(f"{lat},{lon}" for lon, lat in points)
    url = API.format(dataset=dataset) + "?" + urllib.parse.urlencode({"locations": locations})
    for attempt in range(8):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            payload = json.loads(urllib.request.urlopen(req, timeout=120).read())
            results = payload.get("results") or []
            out: list[float | None] = []
            for r in results:
                ele = r.get("elevation")
                out.append(ele)
            return out
        except urllib.error.HTTPError as ex:
            if ex.code in (429, 503):
                wait = 5 * (attempt + 1)
                print(f"   {dataset} {ex.code}: backoff {wait}s", flush=True)
                time.sleep(wait)
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as ex:
            wait = 5 * (attempt + 1)
            print(f"   {dataset} network error ({ex}): backoff {wait}s", flush=True)
            time.sleep(wait)
            continue
    raise RuntimeError(f"giving up on {dataset} batch of {len(points)} points")


def chunks(seq: list, size: int):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def main() -> None:
    centers = load_hexes()
    resolved = load_partial()
    by_hex: dict[str, int | None] = dict(resolved)

    todo = [(k, centers[k]) for k in centers if k not in resolved]
    print(
        f"{len(centers)} populated hexes; {len(resolved)} already resolved, "
        f"{len(todo)} to fetch.",
        flush=True,
    )

    n_batches = math.ceil(len(todo) / BATCH) if todo else 0
    for bi, batch in enumerate(chunks(todo, BATCH), start=1):
        keys = [k for k, _ in batch]
        points = [tuple(c) for _, c in batch]

        eles = query(PRIMARY, points)
        time.sleep(THROTTLE)

        # Fall back to srtm90m for points eudem left null.
        gaps = [i for i, e in enumerate(eles) if e is None]
        if gaps:
            gap_pts = [points[i] for i in gaps]
            for sub_idx, sub in zip(
                [gaps[j : j + BATCH] for j in range(0, len(gaps), BATCH)],
                [gap_pts[j : j + BATCH] for j in range(0, len(gap_pts), BATCH)],
            ):
                fb = query(FALLBACK, sub)
                time.sleep(THROTTLE)
                for local_i, val in zip(sub_idx, fb):
                    if val is not None:
                        eles[local_i] = val

        for key, ele in zip(keys, eles):
            by_hex[key] = None if ele is None else int(round(ele))

        print(f"  batch {bi}/{n_batches} ({len(by_hex)}/{len(centers)} hexes)", flush=True)

        # Persist after every batch so the job is resumable / crash-safe.
        write_output(by_hex, len(centers))

    write_output(by_hex, len(centers))
    summary(by_hex)


def write_output(by_hex: dict[str, int | None], total: int) -> None:
    doc = {
        "schema": SCHEMA,
        "source": SOURCE,
        "pulled_at": PULLED_AT,
        "count": len(by_hex),
        "by_hex": dict(sorted(by_hex.items())),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, ensure_ascii=False) + "\n", encoding="utf-8")


def summary(by_hex: dict[str, int | None]) -> None:
    vals = sorted(v for v in by_hex.values() if v is not None)
    nulls = sum(1 for v in by_hex.values() if v is None)
    print("\n--- elevation summary ---", flush=True)
    print(f"total hexes : {len(by_hex)}", flush=True)
    print(f"with value  : {len(vals)}", flush=True)
    print(f"null        : {nulls}", flush=True)
    if vals:
        print(f"min (m)     : {vals[0]}", flush=True)
        print(f"median (m)  : {int(statistics.median(vals))}", flush=True)
        print(f"max (m)     : {vals[-1]}", flush=True)
    print(f"-> {OUT}", flush=True)


if __name__ == "__main__":
    main()
