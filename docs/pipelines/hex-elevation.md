# Hex Elevation Pipeline

How the per-hex **elevation above sea level** (metres) is pulled for **every
populated hex on the map** — not just mountainous ones — so the editor can show
`Высота: N м` when any hex is clicked. This doc is the repeatable recipe: a
single network stage producing one tracked store.

```
opentopodata DEM ──fetch (network)──▶ map_pipeline/data/hex_elevation.json  (tracked store)
                                              │
                                       editor overlay (wired separately)
```

## Stage — fetch (network) → store

`python3 -m map_pipeline.fetch_hex_elevation`

- **API:** [opentopodata](https://www.opentopodata.org/) public server,
  `https://api.opentopodata.org/v1/<dataset>`
  (GET `?locations=LAT,LON|LAT,LON|…`, `User-Agent: cable-world/1.0`).
- **Primary dataset:** `eudem25m` — the European 25 m DEM (EU-DEM v1.1),
  covers our extent (lon −24…45, lat 35…71).
- **Fallback dataset:** `srtm90m` — global ~90 m SRTM, queried only for the
  points eudem leaves `null` (outside EU-DEM coverage: far north, some coast,
  open sea). If both return `null`, the hex is recorded as `null`.
- **Extent / inputs:** every populated hex center read straight from
  `hex_map.json` (`hexes: "q,r" -> {center: [lon, lat]}`). Currently ~18.7k
  hexes ⇒ ~188 batched requests.

### API limits, batching & backoff

- **Up to 100 locations per request.** We batch hexes 100 at a time; the
  request body is `lat,lon|lat,lon|…` (note: opentopodata wants **lat,lon**
  order, while `hex_map.json` stores **lon,lat** — the script swaps them).
- **~1 request/second**, **1000 requests/day.** We sleep `1.1 s` between
  requests; ~188 primary requests (plus a handful of fallback requests) fits
  comfortably under the daily cap and runs in ~4–6 min.
- **Backoff:** on HTTP `429`/`503` (or transient network errors) the script
  sleeps `5·(attempt+1)` s and retries up to 8 times before giving up.

### Output store

`map_pipeline/data/hex_elevation.json`:

```json
{ "schema": "cable-world.hex-elevation.v1",
  "source": "opentopodata eudem25m (+srtm90m fallback)",
  "pulled_at": "2026-06-03",
  "count": N,
  "by_hex": { "q,r": 1834, "q,r": 0, "q,r": null } }
```

`by_hex` maps each populated hex id to an **integer metres** above sea level
(rounded), or `null` where no DEM had coverage. Keys are sorted; only hexes
present in `hex_map.json` are emitted.

### Resumable

The job writes the store after **every batch**, and on start it reloads any
existing `hex_elevation.json` and **skips hexes already resolved** (non-null).
A crash/interrupt can be continued by simply re-running the command; `null`
hexes are retried on the next run. A single clean run is otherwise fine. Bump
`PULLED_AT` in the script when refreshing the snapshot.

## Editor overlay (wired separately)

The elevation layer is consumed by an independent editor overlay that is wired
by the orchestrator, **not** in this pipeline:

- **hypsometric tint** of hexes by elevation;
- **`Высота: N м`** line in the hex drill-in panel (shown for all hexes;
  `null` hexes show no value / "—");
- suggested **hotkey `E`**, default off.

Do not couple this store to the lift-density (`L`) or Alpine (`A`) overlays.

## Caveats

- **DEM resolution.** `eudem25m` samples a 25 m grid; `srtm90m` only ~90 m. We
  take the elevation **at the hex center point**, not an average over the hex —
  in steep terrain a single point can be tens to hundreds of metres off the
  hex's mean.
- **Coastal / sea / null handling.** Points just offshore, on water, or north
  of EU-DEM coverage come back `null` from `eudem25m`; `srtm90m` fills most of
  them (sea ≈ `0`). Anything neither dataset covers stays `null` — the UI must
  handle `null` (no value / "—").
- **eudem vs srtm vertical datums** differ slightly (EU-DEM uses EVRF2000,
  SRTM uses EGM96); the metre-level mix at coverage edges is acceptable for a
  "Высота" readout but is not survey-grade.
- **OSM-independent.** This pipeline does **not** use Overpass; it is purely a
  DEM point-sampling job and shares no code with the lift/mountain pipelines.
