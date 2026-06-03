# Mountain Regions Pipeline

How the per-hex **mountain regions** layer is built: for every populated hex
that has mountains, which mountain SYSTEM and SUB-REGION it belongs to
(e.g. Альпы → Доломиты), a list of notable named peaks, and an icon-size class
(small | medium | large) so the editor/UI can draw a peak icon sized by how
prominent the mountains are. It covers **every populated hex on the map**
(Europe + Turkey + European Russia/Ukraine, lon −24…45, lat 35…71), not just
the Alps. Same three-stage shape as the lift-density pipeline
([osm-lift-density.md](osm-lift-density.md)), and only one stage needs network.

```
curated polygons ── map_pipeline/data/mountain_systems.json (tracked, hand-drawn)
OpenStreetMap ──fetch (network)──▶ map_pipeline/data/osm_peaks.json (tracked store)
                                          │
        build_mountain_regions ──▶ map_editor/src/data/mountain_regions_by_hex.json
                                   (system + subregion + icon_size + notable peaks)
```

## Stage 0 — region definition (hand-drawn, no network)

`map_pipeline/data/mountain_systems.json` is a curated set of mountain
**systems** and **sub-regions** with approximate `[lon, lat]` polygons.

Each region: `{id, name_ru, name_en, magnitude, polygon}`; sub-regions also
carry `system` (their parent system's `name_ru`). `magnitude` is the baseline
icon-size class (`small|medium|large`) for hexes inside the polygon.

Coverage (systems, with the required sub-regions where called out):

- **Альпы** (Alps) — large, subdivided into Западные/Пеннинские/Бернские/
  Центральные Альпы, Тироль, Высокий Тауэрн, **Доломиты**, Юлийские,
  Восточные Альпы;
- **Пиренеи** (large, with Центральные Пиренеи), **Карпаты** (medium, with
  **Татры** and Южные Карпаты — large), **Скандинавские горы** (large),
  **Динарское нагорье**, **Апеннины**, **Кавказ** (large), **Балканы
  (Стара-Планина)**, **Родопы**, **Центральный массив**, **Юра**,
  **Шварцвальд**, **Гарц**, **Шотландское нагорье**, **Кантабрийские горы**,
  **Сьерра-Невада (Испания)**, Иберийские горы, Центральная Кордильера,
  **Понтийские горы** и **Тавр** (Турция, large), Центральноанатолийские горы,
  Среднегерманские горы, Чешский массив, Рудные горы, Вогезы, Крымские горы.

Урал is intentionally excluded (only a sliver is inside the grid and it is east
of the European focus).

`magnitude` baseline: **large** for high alpine systems (Alps, Pyrenees,
Caucasus, Scandinavian Mountains, Tatras/Southern Carpathians core, Pontic,
Taurus); **medium** for Carpathians/Apennines/Dinarides/Balkan/Anatolia;
**small** for Harz/Black Forest/Jura/Vosges and the central uplands.

The polygons are **approximate** simple convex/bbox-ish outlines drawn from
general geographic knowledge — they are meant for coarse per-hex classification,
not survey-grade boundaries. Where two systems overlap (e.g. Bohemian Massif and
the Ore Mountains), the first match in the list wins.

## Stage 1 — fetch notable peaks (network) → store

`python3 -m map_pipeline.fetch_mountain_peaks`

- **API:** Overpass, `https://overpass-api.de/api/interpreter`
  (POST `data=<query>`, `User-Agent: cable-world-research/1.0`).
- **Tag:** `natural=peak` nodes. KEPT LEAN to avoid a huge download / rate
  limits — only peaks that are **named** AND either have an `ele` tag or a
  `wikidata`/`wikipedia` link (notable):

  ```overpassql
  [out:json][timeout:180];
  (
    node["natural"="peak"]["name"]["ele"](S,W,N,E);
    node["natural"="peak"]["name"]["wikidata"](S,W,N,E);
    node["natural"="peak"]["name"]["wikipedia"](S,W,N,E);
  );
  out tags;
  ```

- **Extent / tiling:** identical to `fetch_osm_lifts.py` — extent derived from
  `hex_map.json`, cut into **5° tiles**, only tiles containing a populated hex
  are queried (~82 tiles), linear backoff on `429/502/504`, `sleep(8)` between
  tiles, **dedupe by node `id`**.
- **Lean knob:** if Overpass keeps rate-limiting, set `MIN_ELE` in the script
  (e.g. `1000`) to keep only named peaks ≥ that elevation. The applied value is
  recorded in the store as `min_ele_filter` and logged.
- **Output store** (`map_pipeline/data/osm_peaks.json`): metadata
  (`source, endpoint, extent, bbox_s_w_n_e, pulled_at, min_ele_filter, count`) +
  `peaks`, one record per node: `{id, lat, lon, name, ele?}` (`ele` parsed from
  the raw OSM string, leading number only). Sorted by id.

## Stage 2 — build per-hex regions (offline) → output

`python3 -m map_pipeline.build_mountain_regions`

For every hex in `hex_map.json`:

1. **Region:** point-in-polygon (ray casting, stdlib) test of the hex **center**
   against `mountain_systems.json`. Sub-regions are tested **before** their
   parent systems, so a hex in the Dolomites resolves to `Доломиты`, not just
   `Альпы`.
2. **Peaks:** notable peaks from the store are binned onto the grid (same hex
   math as `gen_hex_map.py`), and up to **8** top peaks by elevation are
   attached to the hex.
3. **icon_size:** the **max** of the region magnitude and the peak-elevation
   signal: `max_ele ≥ 2500 m → large`, `≥ 1200 m → medium`, else `small`. A hex
   with a mountain region but no peaks keeps its region magnitude; a hex with
   peaks but outside every polygon gets sized from elevation alone.

Only hexes that have a region **or** at least one notable peak are emitted.

Output shape (`map_editor/src/data/mountain_regions_by_hex.json`):

```json
{ "schema": "cable-world.mountain-regions.v1",
  "by_hex": { "q,r": { "system": "Альпы", "subregion": "Доломиты",
                       "icon_size": "large", "max_ele": 3343,
                       "peaks": [ {"name": "Marmolada", "ele": 3343}, ... ] } } }
```

The build runs without the peak store (it just omits peaks and sizes hexes from
region magnitude) and prints a summary: hexes per `icon_size` and per system.

## Editor overlay flag

The mountain layer is an independent editor overlay (mirrors the lift overlay):

- runtime flag: `overlays.mountains`;
- hotkey: **`M`**;
- default: **off**.

When on, a peak icon (reusing `drawPeak()`) is drawn per hex, scaled by
`icon_size` (small/medium/large → 0.42/0.62/0.85). It does not disturb the
lift-density (`L`) or Alpine-planning (`A`) overlays. Clicking a hex shows, in
the side panel, the mountain **system → sub-region**, the icon-size class, the
max elevation and the list of notable peaks (`appendMountainSection`, called
right after `appendLiftSection` in `renderPanelList`).

## Binning

`(lat, lon) → "q,r"` uses the **same math as `map_editor/tools/gen_hex_map.py`**
(`world_size_px`/`hex_size_px` read from `hex_map.json` so it can never drift).
The build step self-checks the binner against every real hex center on startup
(maps 18716/18716 hex centers back to their own key) before trusting it.

## Repeat (full pipeline)

```bash
# 1. refresh notable peaks for the whole grid (network; ~15–30 min, ~82 tiles)
python3 -m map_pipeline.fetch_mountain_peaks    # -> map_pipeline/data/osm_peaks.json

# 2. rebuild the per-hex region/icon-size/peaks file (offline, seconds)
python3 -m map_pipeline.build_mountain_regions  # -> map_editor/src/data/mountain_regions_by_hex.json
```

Day to day you only run step 2 (offline) — and also after editing the curated
polygons in `mountain_systems.json`. Step 1 is needed only to refresh the OSM
peaks or when the hex grid extent changes.

## Caveats

- The region polygons are **curated approximations**, not official boundaries;
  hexes near a system edge may be mis-classified or fall into a neighbouring
  system. Refine the polygons in `mountain_systems.json` and re-run step 2.
- OSM peak coverage and `ele`/`wikidata` tagging vary by country, so the notable
  peak list is "what OSM knows", not a definitive ranking.
- `icon_size` is a coarse 3-class signal; it is driven by region magnitude and
  the single highest peak in the hex, not by relief/ruggedness.
- If a peak fetch had to be limited for rate-limiting, `min_ele_filter` in
  `osm_peaks.json` records the applied elevation floor.
```
