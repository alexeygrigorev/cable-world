# OSM Lift Density Pipeline

How the per-hex lift-density data for Layer B (see
[alpine-cableways-catalog.md](alpine-cableways-catalog.md)) is pulled from
OpenStreetMap and binned onto the hex grid. It covers **every populated hex on
the map** (currently Europe), not just the Alps. This doc is the repeatable
recipe: three stages, two of them offline.

```
OpenStreetMap ──fetch (network)──▶ map_pipeline/data/osm_lifts.json  (tracked store)
                                          │
                          build_lift_density ──▶ map_editor/src/data/lift_density.json   (counts, small, always loaded)
                          build_lift_index   ──▶ map_editor/src/data/lift_index_by_hex.json (named drill-in, lazy-loaded)
```

## Stage 1 — fetch (network) → store

`python3 -m map_pipeline.fetch_osm_lifts`

- **API:** Overpass, `https://overpass-api.de/api/interpreter`
  (POST `data=<query>`, `User-Agent: cable-world-research/1.0`).
- **Tag:** every uphill rope/lift line is a way tagged
  [`aerialway=*`](https://wiki.openstreetmap.org/wiki/Key:aerialway).
- **Extent:** derived automatically from `hex_map.json` — the bounding box of
  all populated hex centers (currently lon −24.2…45.0, lat 34.8…71.1).
- **Query** (one coordinate + tags per lift, no full geometry):

  ```overpassql
  [out:json][timeout:180];
  ( way["aerialway"](S,W,N,E); );
  out tags center;
  ```

- **Tiling:** the extent is cut into **5° tiles**, and only tiles that actually
  contain a populated hex are queried (ocean tiles are skipped) — ~82 tiles for
  the current grid. Per tile: linear backoff on `429/502/504`
  (15s, 30s, …, 6 tries), `sleep(8)` between tiles, **dedupe by way `id`**
  across tile borders.
- **Output store** (`map_pipeline/data/osm_lifts.json`): metadata
  (`source, endpoint, extent, bbox_s_w_n_e, pulled_at, count`) + `lifts`, one
  record per way: `{id, lat, lon, type, name?}` (`name` from `name` / `name:en`
  / `ref` when present). Sorted by id. Re-run only to refresh the snapshot;
  bump `PULLED_AT` in the script when you do.

## Stage 2 — build density (offline) → counts

`python3 -m map_pipeline.build_lift_density`

Reads the store, keeps **passenger uphill transport**, groups it, bins to hexes
and writes `map_editor/src/data/lift_density.json`.

`aerialway=*` covers more than passenger transport; we keep/group:

| raw `aerialway` value | group |
|---|---|
| `chair_lift` | **chair_lift** |
| `gondola`, `mixed_lift` | **gondola** |
| `cable_car`, `cablecar`, `funicular` | **cable_car** |
| `drag_lift`, `t-bar`, `platter`, `j-bar`, `rope_tow`, `magic_carpet` | **surface_tow** |

Dropped: `station`, `goods`, `zip_line`, `explosive`, `avalanche`, `pylon`,
`yes/no`, `construction/proposed/razed/disused/abandoned`, …

Output shape:

```json
{ "schema": "...", "totals": {...}, "hex_count": N,
  "by_hex": { "q,r": { "passenger_total": 228, "chair_lift": 89,
                       "gondola": 25, "cable_car": 8, "surface_tow": 106 } } }
```

Only hexes that exist in `hex_map.json` are emitted (lifts that bin to a
non-populated hex are dropped and counted in the log).

## Stage 3 — build index (offline) → named drill-in

`python3 -m map_pipeline.build_lift_index`

Same filter + binning, but emits the per-hex **named list** for the drill-in
panel → `map_editor/src/data/lift_index_by_hex.json`:

```json
{ "by_hex": { "q,r": { "counts": {...},
    "lifts": [ {"name": "Vanoise Express 1", "group": "cable_car"}, ... ] } } }
```

Named lifts sorted first; unnamed lifts are kept (no `name` key) so the UI can
list them muted. This file is larger (~900 KB) and is **lazy-loaded** by the
editor on first drill-in.

## Editor Overlay Flag

The lift heatmap is an independent editor overlay:

- runtime flag: `overlays.liftDensity`;
- hotkey: `L`;
- default: off.

Do not reuse this flag for terrain planning overlays. The Alpine planning
placeholder layer uses `overlays.alpsTarget` and hotkey `A`, so lift-density
work and Alpine glyph placement can be reviewed independently.

## Binning

`(lat, lon) → "q,r"` uses the **same math as `map_editor/tools/gen_hex_map.py`**
(`merc()` + `world_to_hex()`; `world_size_px`/`hex_size_px` read from
`hex_map.json` so it can never drift). Self-checked 506/506 against real hex
centers (`tmp/alps_research/hexbin.py`).

## Repeat (full pipeline)

```bash
# 1. refresh the OSM snapshot for the whole grid (network; ~15–30 min, ~82 tiles)
python3 -m map_pipeline.fetch_osm_lifts        # -> map_pipeline/data/osm_lifts.json

# 2. rebuild per-hex counts (offline, deterministic, seconds)
python3 -m map_pipeline.build_lift_density     # -> map_editor/src/data/lift_density.json

# 3. rebuild the named drill-in index (offline)
python3 -m map_pipeline.build_lift_index       # -> map_editor/src/data/lift_index_by_hex.json
```

Day to day you only run steps 2–3 (offline). Step 1 is needed only to refresh
the OSM data or when the hex grid extent changes. After step 1 the extent and
tile list are recomputed automatically from `hex_map.json`.

## Caveats

- OSM completeness varies; counts are "what OSM knows", not an official census.
- `out center` uses the way's bounding-box center; a long lift crossing a hex
  boundary is attributed to its center hex only.
- The first Alpine-only prototypes still live in `tmp/alps_research/`
  (`osm_pull.py`, `hexbin.py`); the maintained versions are the `map_pipeline/`
  modules above.
