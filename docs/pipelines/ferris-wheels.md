# Ferris / Observation Wheels Pipeline

How the per-hex Ferris-wheel (колесо обозрения) layer is pulled from
OpenStreetMap and binned onto the hex grid. It covers **every populated hex on
the map** (currently Europe). Repeatable recipe: two stages, one offline.

```
OpenStreetMap ──fetch (network)──▶ map_pipeline/data/osm_ferris_wheels.json   (tracked store)
                                          │
                       build_ferris_wheels ──▶ map_editor/src/data/ferris_wheels_by_hex.json (per-hex drill-in)
```

Ferris wheels are **few** (a few hundred across Europe), so unlike the lift
pipeline this does a **single whole-bbox query** — no tiling.

## Stage 1 — fetch (network) → store

`python3 -m map_pipeline.fetch_osm_ferris_wheels`

- **API:** Overpass, `https://overpass-api.de/api/interpreter`
  (POST `data=<query>`, `User-Agent: cable-world-research/1.0`).
- **Tags** ([OSM](https://wiki.openstreetmap.org/wiki/Tag:attraction%3Dbig_wheel)):
  - `attraction=big_wheel` — the standard tag for Ferris wheels,
  - `man_made=ferris_wheel` — also caught if present,
  - `tourism=attraction` whose `name` matches
    `/ferris|big wheel|observation wheel|колесо обозрения|riesenrad|grande roue|noria/i`.
- **Elements:** `nwr` — nodes **and** ways **and** relations. Nodes use their
  own `lat`/`lon`; ways/relations use `out center` (bounding-box center).
- **Extent:** derived automatically from `hex_map.json` — the bounding box of
  all populated hex centers (currently S,W,N,E ≈ `34.8, −24.2, 71.1, 45.0`).
- **Query** (one coordinate + tags per wheel, no full geometry):

  ```overpassql
  [out:json][timeout:180];
  (
    nwr["attraction"="big_wheel"](S,W,N,E);
    nwr["man_made"="ferris_wheel"](S,W,N,E);
    nwr["tourism"="attraction"]["name"~"ferris|big wheel|observation wheel|колесо обозрения|riesenrad|grande roue|noria",i](S,W,N,E);
  );
  out tags center;
  ```

  > The `tourism=attraction` branch filters by name **server-side** (`~,i`). An
  > unfiltered `tourism=attraction` pull over the whole Europe bbox is enormous
  > and times Overpass out — keep the regex on the server.

- **Backoff:** the Overpass channel is busy (peak/lift pulls run on it too), so
  expect `429/502/504`. Linear backoff `15s, 30s, …` up to 6 tries
  (also retries on transient `URLError`/timeout).
- **Dedupe:** by `(osm_type, id)` — the same wheel can match more than one tag.
- **Output store** (`map_pipeline/data/osm_ferris_wheels.json`,
  `schema: cable-world.osm-ferris-wheels.v1`): metadata
  (`source, endpoint, extent, bbox_s_w_n_e, pulled_at, count`) + `wheels`, one
  record per element: `{id, osm_type, lat, lon, name?, height?}`. Sorted by
  `(osm_type, id)`. Re-run only to refresh; bump `PULLED_AT` in the script.

`id` + `osm_type` let the UI link to
`https://www.openstreetmap.org/{osm_type}/{id}`.

## Stage 2 — build per-hex index (offline) → drill-in

`python3 -m map_pipeline.build_ferris_wheels`

Reads the store, bins each wheel to its hex and writes
`map_editor/src/data/ferris_wheels_by_hex.json`
(`schema: cable-world.ferris-wheels.v1`, stdlib only):

```json
{ "schema": "cable-world.ferris-wheels.v1", "hex_count": N,
  "by_hex": { "q,r": { "count": 6, "wheels": [
      {"name": "Солнце Москвы", "id": 1093600277, "osm_type": "way", "height": "140"},
      {"id": 8245742052, "osm_type": "node"}
  ] } } }
```

- Per hex: `count` (total wheels in the hex) + `wheels` list. Each item keeps
  `id`, `osm_type`, and `name`/`height` when tagged.
- **Named first** (sorted by name), then unnamed (sorted by id) — unnamed
  wheels have no `name` key so the UI can show them muted but still linkable.
- **Only hexes present in `hex_map.json` are emitted** — wheels binning to a
  non-populated hex are dropped and counted in the log.

## Binning

`(lat, lon) → "q,r"` uses the **same Mercator + hex math as the lift pipeline**
(`map_pipeline/build_lift_index.py`): read `world_size_px`/`hex_size_px` from
`hex_map.json` so it can never drift.

```
x   = (lon + 180) / 360 * world
siny= sin(rad(clamp(lat, -85.05, 85.05)))
y   = (0.5 - log((1+siny)/(1-siny)) / (4·π)) * world
qf  = ((√3/3)·x - (1/3)·y) / hex_size
rf  = (2/3)·y / hex_size
# cube-round (cx=qf, cz=rf, cy=-cx-cz); fix the largest delta → "rx,rz"
```

## Current snapshot (`pulled_at` 2026-06-03)

- store: **455 wheels** (351 nodes, 103 ways, 1 relation; 261 named, 63 with
  `height`).
- per-hex index: **362 wheels** in **297 hexes** (211 named; 93 dropped as
  off-grid — coastal/non-land bins not in the populated grid).
- Notable named wheels present: **London Eye** (way 204068874, h 136.5),
  **Wiener Riesenrad** Vienna (way 97979331, h 64.8), **Grande Roue** Paris
  (node 13836394015), **Солнце Москвы** Moscow (way 1093600277, h 140), plus
  ~130 Riesenrad / колесо обозрения / grande roue entries across the grid.

## Editor overlay (wired separately)

The editor overlay + drill-in panel and the placeholder **«колесо обозрения»**
object type / icon are **wired by the orchestrator** (in `map_editor/src/main.js`),
not by this pipeline. This pipeline is **data + doc only**; it does not touch any
editor JS. The UI lazy-loads `ferris_wheels_by_hex.json` on first drill-in,
the same way it loads `lift_index_by_hex.json`.

## Repeat (full pipeline)

```bash
# 1. refresh the OSM snapshot for the whole grid (network; single bbox query)
python3 -m map_pipeline.fetch_osm_ferris_wheels   # -> map_pipeline/data/osm_ferris_wheels.json

# 2. rebuild the per-hex index (offline, deterministic, seconds)
python3 -m map_pipeline.build_ferris_wheels       # -> map_editor/src/data/ferris_wheels_by_hex.json
```

Day to day you only run step 2 (offline). Step 1 is needed only to refresh the
OSM data or when the hex grid extent changes (it recomputes the bbox from
`hex_map.json` automatically).

## Caveats

- OSM completeness varies; counts are "what OSM knows", not an official census.
- Some entries are travelling-fair / seasonal wheels, not permanent landmarks —
  OSM does not always distinguish them.
- `out center` uses the way/relation bounding-box center; a wheel is attributed
  to that one center hex.
