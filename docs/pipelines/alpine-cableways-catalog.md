# Alpine Cableways Catalog & Map Display

How we collect Alpine cableways (ropeways, funiculars, cog/rack railways) and
how we show them on the hex map without turning it into clutter ("мессив").

There are **thousands** of lifts in the Alps. Showing each as its own marker is
unreadable. So the data and the display are split into **two layers**.

## Layer A — notable objects (curated)

The "основные" lifts worth a card, a photo, a visit: famous aerial tramways,
gondolas, funiculars, cog railways. These are individual `TransportObject`s with
full metadata, shown as individual markers.

- Source: manual, source-checked research (Wikipedia + operator sites).
- File: `examples/staging/research/alps_catalog_candidates.json`
  (`{"candidates": [...]}`, schema `schemas/staging_catalog_candidate.schema.json`).
- Scope: chairlifts (`Sessellift`/`télésiège`) are **excluded** here — they are
  too many and belong to Layer B.
- Status: 181 candidates across 6 countries
  (CH 43, AT 39, IT 37, FR 30, DE 25, SI 7), `review.state: "candidate"`,
  validated by `scripts/validate_staging_candidates.py`.
- Types present: aerial tram 63, gondola 64, funicular 28, cog rail 17,
  mountain rail 3, tourist/urban 6.

A future small schema change can add a `significance`/`tier` field so the list
can sort "основные → остальные". Today significance is implicit (the curated set
is already the high-priority tier).

## Layer B — lift density per hex (the "count per hexagon" idea)

Instead of plotting every chairlift, each hex shows **how many lifts fall inside
it** (a number / heat shading). This reflects the overall density of lifts
across the Alps and keeps the map clean. Notable Layer A objects still render on
top as individual markers.

- Source: OpenStreetMap via Overpass — `way["aerialway"]`. The raw Alpine bbox
  has ~14.8k `aerialway` ways, but that tag also covers stations, goods/material
  ropeways, zip lines, avalanche-control (`explosive`) and pylons. We keep only
  **passenger uphill transport**: chair_lift, gondola, cable_car, mixed_lift and
  surface tows (drag/t-bar/platter/j-bar/rope_tow/magic_carpet).
- Result: **10,097 passenger lifts** binned into **420 hexes** (414 in the
  current grid): 2,646 chair lifts, 5,951 surface tows, 980 gondolas,
  520 cable cars.
- Pull + bin: `tmp/alps_research/osm_pull.py` → `tmp/alps_research/lift_density_by_hex.json`
  (`{"q,r": {"passenger_total": N, "chair_lift": .., "gondola": .., "cable_car": .., "surface_tow": ..}}`).
  Full extraction method (Overpass query, bbox, tiling, rate-limit backoff,
  filtering, binning, reproduce steps) is documented in
  [osm-lift-density.md](osm-lift-density.md).
- Densest hexes are the French Tarentaise (Trois Vallées / Paradiski — up to
  227 lifts in one 25 km hex) and the Dolomites / Kitzbühel area. Counts are
  broken down by group, so the UI can show "227 lifts" or filter to chairlifts.

## Hex binning

Both layers map a lat/lon to a hex id on the project's single **global Web
Mercator hex grid** (see `map_editor/tools/gen_hex_map.py`). The same
`merc()` + `world_to_hex()` math is reused so ids match the editor/game exactly
(`hex_size_px` from `TARGET_KM=25`, `NOMINAL_LAT=51`, `WORLD_SIZE_PX=65536`).

- Binning helper / self-check: `tmp/alps_research/hexbin.py`
  (validated 506/506 against real `hex_map.json` centers).
- All 181 Layer A objects land on existing land hexes, occupying 85 distinct
  hexes. Densest example: the Chamonix / Mont-Blanc hex holds 11 catalog
  objects — concrete proof that per-hex aggregation is the right display.

## Display (prototype in the web editor, then port to Godot)

The display is prototyped first in the web editor (`map_editor/src/main.js`),
which renders the same `hex_map.json`, then ported to the Godot view
(`scripts/hex_map_view.gd`).

Editor prototype (implemented):

- **Heat tint** per hex from `alps_lift_density.json` (`passenger_total` on a log
  scale, pale yellow → dark red). Render pass "1b".
- **Count number** drawn on hexes with ≥6 lifts once the on-screen hex is large
  enough (pass "5c"), so the overview is just numbers, never thousands of
  markers.
- **Drill-in** ("zoom-in on a hex"): clicking a hex adds a lift section to the
  side panel — type breakdown + the named lift list for that hex. Named lifts
  first; unnamed ones are still listed but muted (`без названия`).
- Toggle the overlay with the **`L`** key.
- The named list (`alps_lift_index_by_hex.json`, ~900 KB) is **lazy-loaded** via
  dynamic `import()` — Vite code-splits it into its own chunk, so it is fetched
  only on the first drill-in, never on the overview.

Data files the editor reads (under `map_editor/src/data/`):
`alps_lift_density.json` (always, small) and `alps_lift_index_by_hex.json`
(on demand).

Godot port (TODO): mirror passes 1b/5c in `hex_map_view.gd` (`_draw`) reading
the same two JSON files, and extend the existing hex-select panel with the lift
section.

## Pipeline order

1. Collect Layer A research per country → validate → catalog file. ✅ done.
2. Pull Layer B lift density from OSM, bin to hexes. ✅ done
   (`map_pipeline/fetch_osm_lifts.py` → `build_lift_density.py` /
   `build_lift_index.py`, see [osm-lift-density.md](osm-lift-density.md)).
3. Layer B display in the web editor (heat + counts + drill-in). ✅ done.
4. Port the Layer B display to the Godot view; render Layer A markers from the
   approved catalog. (next)
5. Manual review pass for Layer A (`review.state: candidate → approved`) before
   seeding into the game catalog.
6. Glyph/image generation for objects — a **later** step, out of scope here.
