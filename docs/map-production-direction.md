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

## Stop Rules

Do not spend more time polishing `assets/map/germany_styled.png` as a monolithic final map.

Do not generate another full Germany/Europe bitmap and call it the production direction.

If a generated image is useful, extract or regenerate its components as glyphs, then place them through `map_pipeline`.

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
