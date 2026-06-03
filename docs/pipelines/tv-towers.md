# TV / Telecom Tower Pipeline

How the per-hex **TV / radio / telecom tower** data is pulled from OpenStreetMap
and binned onto the hex grid. It covers **every populated hex on the map**
(currently Europe). Two stages, one network + one offline.

```
OpenStreetMap ──fetch (network)──▶ map_pipeline/data/osm_tv_towers.json  (tracked store)
                                          │
                          build_tv_towers ──▶ map_editor/src/data/tv_towers_by_hex.json (per-hex drill-in)
```

## Source tags

A "TV / radio / telecom tower" in OSM is tagged in three ways — all three are
queried:

| OSM tagging | what it is |
|---|---|
| [`man_made=communications_tower`](https://wiki.openstreetmap.org/wiki/Tag:man_made%3Dcommunications_tower) | big concrete/steel broadcast towers (e.g. Fernsehturm, Ostankino) |
| `man_made=tower` + [`tower:type=communication`](https://wiki.openstreetmap.org/wiki/Key:tower:type) | self-supporting communication towers |
| `man_made=mast` + `tower:type=communication` | guyed communication masts |

We query **nodes + ways + relations** (`nwr`); ways/relations resolve to a point
with `out center`. We keep `name` (from `name` / `name:en` / `ref`), `height`
(from `height` / `tower:height` when tagged) and the OSM `id` + `osm_type` so the
UI can link to `openstreetmap.org/<osm_type>/<id>`.

## Stage 1 — fetch (network) → store

`python3 -m map_pipeline.fetch_osm_towers`

- **API:** Overpass, `https://overpass-api.de/api/interpreter`
  (POST `data=<query>`, `User-Agent: cable-world-research/1.0`).
- **Extent:** the bounding box of all populated hex centers, read automatically
  from `hex_map.json` (currently S,W,N,E ≈ `34.85, -24.23, 71.10, 45.00`).
- **Strategy:** towers are sparse, so we do a **count probe** over the whole
  bbox first, then a **single whole-bbox fetch** (no tiling). Patient linear
  backoff on `429/502/504` and transient socket errors (15s, 30s, …, 8 tries),
  because the Overpass channel is often busy.
- **Query** (count probe uses `out count;` instead of `out tags center;`):

  ```overpassql
  [out:json][timeout:300];
  (
    nwr["man_made"="communications_tower"](S,W,N,E);
    nwr["man_made"="tower"]["tower:type"="communication"](S,W,N,E);
    nwr["man_made"="mast"]["tower:type"="communication"](S,W,N,E);
  );
  out tags center;
  ```

- **Output store** (`map_pipeline/data/osm_tv_towers.json`):

  ```json
  { "schema": "cable-world.osm-tv-towers.v1",
    "source": "...", "endpoint": "...",
    "bbox_s_w_n_e": [34.85, -24.23, 71.10, 45.00],
    "pulled_at": "2026-06-03", "count": N,
    "towers": [ {"id": 123, "osm_type": "node",
                 "lat": 52.52, "lon": 13.41,
                 "name": "Fernsehturm Berlin", "height": "368"} ] }
  ```

  One record per OSM element, deduped by `(osm_type, id)`, sorted by
  `(osm_type, id)`. Re-run only to refresh the snapshot; bump `PULLED_AT` in the
  script when you do.

## Stage 2 — build per-hex index (offline) → drill-in

`python3 -m map_pipeline.build_tv_towers`

Reads the store, bins each tower to its hex and writes
`map_editor/src/data/tv_towers_by_hex.json`:

```json
{ "schema": "cable-world.tv-towers.v1",
  "hex_count": N,
  "by_hex": { "q,r": { "count": 2,
      "towers": [ {"name": "Fernsehturm Berlin", "id": 123,
                   "osm_type": "node", "height": "368"},
                  {"id": 456, "osm_type": "way"} ] } } }
```

- Only hexes that exist in `hex_map.json` are emitted; towers that bin to a
  non-populated hex are dropped and counted in the log (`dropped_offgrid`).
- Within a hex, **named towers are sorted first** (then unnamed by id). Unnamed
  towers keep `id` + `osm_type` so the UI can still link to OSM.
- Hexes are emitted in descending `count` order.

## Binning

`(lat, lon) → "q,r"` uses the **same math as `map_editor/tools/gen_hex_map.py`**
and the lift pipeline (`merc()` + `world_to_hex()`; `world_size_px` /
`hex_size_px` read from `hex_map.json` so it can never drift):

```
x   = (lon + 180) / 360 * world
siny= sin(rad(clamp(lat, -85.05, 85.05)))
y   = (0.5 - log((1+siny)/(1-siny)) / (4*pi)) * world
qf  = ((sqrt3/3)*x - (1/3)*y) / hex_size
rf  = (2/3)*y / hex_size
# cube-round (cx=qf, cz=rf, cy=-cx-cz), fix the largest delta -> "rx,rz"
```

Nodes use their own `lat`/`lon`; ways/relations use the `out center` point.

## Editor overlay (wired by the orchestrator)

The editor overlay/drill-in and a placeholder **"телебашня"** object type / icon
will be wired separately by the orchestrator (in `map_editor/src/main.js`). This
pipeline only produces the data files; it does not touch any editor JS.

## Repeat (full pipeline)

```bash
# 1. refresh the OSM snapshot for the whole grid bbox (network; Overpass often busy)
python3 -m map_pipeline.fetch_osm_towers   # -> map_pipeline/data/osm_tv_towers.json

# 2. rebuild the per-hex index (offline, deterministic, seconds)
python3 -m map_pipeline.build_tv_towers    # -> map_editor/src/data/tv_towers_by_hex.json
```

Day to day you only run step 2 (offline). Step 1 is needed only to refresh the
OSM data or when the hex grid extent changes; the bbox is recomputed
automatically from `hex_map.json`.

## Caveats

- OSM completeness varies; counts are "what OSM knows", not an official census.
- `height` is the raw OSM string (e.g. `"368"`, `"368 m"`); it is kept verbatim.
- `man_made=communications_tower` is queried unconditionally; `tower`/`mast`
  are only kept when `tower:type=communication` (so power/observation/lighting
  towers are excluded).
- `out center` uses the element's bounding-box center for ways/relations; a
  tower is attributed to its center hex only.
- The Overpass channel is frequently rate-limited; the fetch backs off patiently
  rather than tiling, since towers are few enough for one whole-bbox query.
```
