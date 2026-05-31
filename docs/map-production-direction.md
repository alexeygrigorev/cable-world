# Map Production Direction

Date: 2026-05-31

Status: active decision.

## Decision

Production map rendering must not depend on one generated full-map bitmap as the final visual layer.

A generated full-map image is allowed only as:

- a mood/reference image;
- a temporary preview;
- a source for identifying which glyphs we need.

The production map must be composed from:

- a clean geographic base layer;
- reusable glyph sprites;
- explicit geography data that places those glyphs by real coordinates;
- runtime city/object overlays.

## Why

The current whole-map generated underlay improved the mood, but it creates structural problems:

- baked city-like pictograms conflict with runtime city landmarks;
- baked terrain cannot be audited or corrected region by region;
- extending Germany into Europe becomes patchy, because a single bitmap does not continue cleanly over borders;
- fixing one area often damages another area;
- transport markers and city overlays fight against random details already painted into the bitmap.

This is why continuing to polish a single generated Germany image is not real progress toward `10/10`.

## Required Pipeline

1. Build a clean base map from geographic data:
   - land, sea, borders, major rivers, major real lakes, coastline/islands;
   - no baked cities, no random villages, no decorative mountains inside the base.

2. Maintain reusable glyph sheets:
   - mountain ranges: Alps, Harz, Saxon Switzerland / Elbe Sandstone, Erzgebirge, Black Forest, Bavarian Forest;
   - forests and lowlands;
   - lakes and wetland clusters;
   - ships, ports, bridges, castles, towers, and other atlas details;
   - city landmark icons stay separate from terrain glyphs.

3. Place glyphs using explicit data:
   - each glyph has an id, lon/lat anchor, width/scale, priority, and region id;
   - regions continue across borders, for example Alps are not a Germany-only asset;
   - no hash-random placement for important terrain.

4. Compose final map from layers:
   - base geography;
   - water details;
   - relief regions;
   - forest/detail glyphs;
   - labels;
   - runtime city and transport overlays.

5. Audit before claiming quality improvement:
   - visible mountains exist where real terrain exists;
   - large lakes/islands match reality;
   - city coordinates align with the base;
   - no duplicate baked/runtime cities;
   - map remains expandable to France, Spain, Italy, Switzerland, Austria, neighbors, Scandinavia, Baltics, Russia/Belarus/Ukraine, and Turkey.

## Europe Expansion Data Contract

The first Europe expansion block is #75 DACH + Northern Italy. Its planning/data contract lives in `docs/europe-expansion-plan.md`.

For Alpine expansion, relief must be derived from real elevation data before new art is drawn. Use Copernicus DEM GLO-30 or EU-DEM where possible, NASA SRTM 1 arc-second as fallback, and Natural Earth terrain only as broad low-detail context. Alpine ridge anchors and massif sectors must come from elevation masks, named massif geometry or documented real-world centroids, never from random decorative placement.

The #75 block is split into Switzerland, Austria, Northern Italy, Alpine relief source/elevation validation, city landmark coverage, and cableway/funicular object candidate data. Required city coverage starts with Zürich, Bern, Geneva, Vienna, Innsbruck, Salzburg, Milan, Turin, Venice, Verona and Bolzano.

## Stop Rules

Do not spend more time polishing `assets/map/germany_styled.png` as a monolithic final map.

Do not generate another full Germany/Europe bitmap and call it the production direction.

If a generated image is useful, extract or regenerate its components as glyphs, then place them through `map_pipeline`.

## Verification Protocol

Every map iteration must leave evidence in commands and screenshots. Do not claim that the map is `8/10` or `10/10` from a single local screenshot.

Minimum command checks:

```bash
uv run python -m map_pipeline.compose_map
python3 -m unittest tests.test_map_panel_contract tests.test_export_payload_contract tests.test_android_export_contract
godot --headless --path . --import --quit
rm -rf build/web && mkdir -p build/web && godot --headless --path . --export-release Web build/web/index.html
find build/web -maxdepth 1 -type f \( -name '*.wasm' -o -name '*.pck' -o -name '*.js' -o -name '*.html' \) -print0 | while IFS= read -r -d '' file; do gzip -9 -kf "$file"; done
curl -I --compressed http://127.0.0.1:9000/index.pck
PLAYWRIGHT_PACKAGE=/tmp/cable-playwright/node_modules/playwright URL=http://127.0.0.1:9000/ node scripts/verify-web-map.mjs
```

Required screenshot review:

- `/tmp/cable-world-web-map/mobile-390x844-initial.png`
- `/tmp/cable-world-web-map/mobile-390x844-after-drag.png`
- `/tmp/cable-world-web-map/desktop-1280x800-initial.png`

What to inspect on screenshots:

- first screen is still map-first/fullscreen, with only compact controls over it;
- city and transport icons are visible, clickable-looking, and tied to map coordinates after pan/zoom;
- zoom percent is visible and stays in the `50%..150%` range;
- labels remain readable and do not disappear under transport markers in obvious cases;
- generated/composed underlay has no baked city landmarks that duplicate runtime icons;
- Alps, Harz, Black Forest, Erzgebirge, Bavarian Forest and Saxon Switzerland are plausible for their real locations;
- major water bodies and islands are plausible: Bodensee, Müritz, Chiemsee, Schweriner See, Plauer See, Schaalsee, Steinhuder Meer, Edersee, Ammersee, Starnberger See, Tegernsee, Berlin lakes and Rügen;
- no obvious large mountains in lowland regions unless the region is known to have real relief;
- map can pan south beyond Germany so München/Alps are not clipped;
- `index.pck` is served with `Content-Encoding: gzip` and `Cache-Control: no-store`;
- payload size is recorded when it materially changes.

Quality scoring gate:

- `3/10`: technically shows a map, but stretched, sparse, or visually incoherent; objects may be hard to see or not meaningfully interactive.
- `6/10`: current working band. Map is usable and recognizably styled, but still has visual hierarchy issues, uneven geography accuracy, and insufficient polished terrain/glyph quality.
- `8/10`: readable within 1-2 seconds, no obvious coordinate drift, strong visual hierarchy, plausible relief/water/islands, cohesive glyph style, smooth pan/zoom, and acceptable payload.
- `10/10`: best practical result for this codebase: geography and visual composition have been audited region-by-region, objects/cities/labels remain clear across zoom states, and the pipeline can extend to neighboring Europe without monolithic bitmap patches.

Documentation check:

- Update `docs/map-orchestrator-progress.md` after every verifyable iteration with implemented changes, evidence, checks and self-audit.
- Update `docs/active-map-backlog.md` when an item is closed or a new concrete issue appears.
- Commit the iteration after checks pass.

## Next Concrete Step

Replace the current baked Germany underlay with a cleaner composed map:

- remove baked city/village pictograms from the base;
- keep or regenerate glyphs for Alps, Harz, Saxon Switzerland, forests, lakes, ships, and decorative atlas details;
- place those glyphs explicitly in `map_pipeline`;
- keep runtime city landmarks and transport objects as the only city/object layer.

Current reproducible commands:

```bash
uv run python -m map_pipeline.generate_map_detail_glyphs
uv run python -m map_pipeline.compose_map
godot --headless --path . --import --quit
PORT=9000 scripts/serve-web.sh
```
