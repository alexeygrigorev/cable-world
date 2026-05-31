# Map Quality Audit 2026-05-31

Reference target:

```text
/home/alexey/tmp/file_000000000d5c71f4b60ecae32dd4240b.png
```

Current runtime map:

```text
assets/map/germany_styled.png
```

Source generated underlay:

```text
/home/alexey/.codex/generated_images/019e7af1-437a-70f1-9164-d2f7b34a9c81/ig_0715a97cc1e1e04e016a1bdfd731b48191914ea24c0858fd77.png
```

Current generated icon sheet:

```text
/home/alexey/.codex/generated_images/019e7af1-437a-70f1-9164-d2f7b34a9c81/ig_0715a97cc1e1e04e016a1be7b8dfc0819199f45d3987678a35.png
```

## Evidence

Browser verifier command:

```bash
PLAYWRIGHT_PACKAGE=/tmp/cable-playwright/node_modules/playwright \
  node scripts/verify-web-map.mjs
```

Screenshots:

- `/tmp/cable-world-web-map/mobile-390x844-initial.png`
- `/tmp/cable-world-web-map/mobile-390x844-after-marker-click.png`
- `/tmp/cable-world-web-map/mobile-390x844-after-drag.png`
- `/tmp/cable-world-web-map/desktop-1280x800-initial.png`
- `/tmp/cable-world-web-map/desktop-1280x800-after-marker-click.png`
- `/tmp/cable-world-web-map/desktop-1280x800-after-drag.png`

## Gate Checks

- Карта не растягивается под viewport: pass. `MapPanel` uses projected aspect and aspect-fill map rect.
- Можно двигать карту мышью/тачем: pass in browser screenshots. `after-drag` shows map displacement.
- Иконки объектов кликабельны: pass in browser screenshots. `after-marker-click` shows selected amber atlas-style glow.
- Drag по карте не ломается из-за маркеров: pass in implementation; marker drag forwards pan updates.
- Стартовый экран содержит карту fullscreen и только минимальный map UI: pass in screenshots.
- Все объекты расположены по координатам: pass in implementation; positions come from object latitude/longitude.
- Иконка выбирается по нормализованному типу: pass; `TRANSPORT_TYPE_ICON` maps `transport_type_id`.
- Web build отдается локально с gzip: pass. `index.wasm` and `index.pck` return `Content-Encoding: gzip`.

## Current Score

Rubric estimate after user review: 6/10.

Rubric estimate after iteration 2026-05-31 10:49: 7/10 candidate.

Rubric estimate after cluster iteration 2026-05-31 11:06: stronger 7/10, still not 8/10.

Rubric estimate after city landmark iteration 2026-05-31 11:30: direction improved, still about 7/10.

What passes:

- The map loads on Web with gzip.
- The map is fullscreen-first and no longer stretched.
- Pan/drag and marker click work.
- Runtime markers use `transport_type_id` mapping instead of substring matching.

What blocks 8/10:

- The underlay is too detailed/noisy behind the transport icons.
- Transport icons and funicular markers do not pop enough from the map.
- Germany is not recognizable enough at first glance.
- Berlin, Hamburg, and Rostock are missing as explicit orientation landmarks.
- Zoom needs visible + / - controls, a closer default state, and a firm zoom-out floor.

Next action: run a contrast/readability iteration before claiming any score above 6/10.

Iteration result:

- Marker readability improved with larger parchment buttons, dark border, and shadow.
- City/terrain labels now provide orientation: Berlin, Hamburg, Rostock, Koeln, Muenchen, Harz, Zugspitze, Alpen.
- Zoom controls are visible on the map; default zoom is closer, and zoom-out stops at base fill.
- Browser screenshots were regenerated under `/tmp/cable-world-web-map/`.

Remaining blockers for 8/10:

- The underlay is still busy in object-dense areas.
- Some mobile labels and marker clusters compete for space.
- Cluster count badges reduce overload but look like generic UI instead of native atlas landmarks.

Cluster iteration result:

- Object-dense areas now collapse into low-zoom cluster count markers.
- Clicking a cluster zooms to the group and expands it into individual transport icons.
- This addresses the "too busy" issue functionally, but the visual style still needs polish before 8/10+.

City landmark iteration result:

- A unified 64-icon European city landmark sheet was generated and sliced.
- Germany landmarks now appear directly on the map, including Dresden.
- Labels now use umlauts for German city names where needed.
- This improves geographic recognition, but icon size/placement and cluster styling still need more art direction before a confident 8/10.

Fix iteration result:

- City landmark textures now actually draw after successful load; the previous implementation returned before the draw block.
- Mouse, touch, and marker drag now share the same pan helper and use a calmer drag scale.
- Remaining blocker: the generated artistic Germany underlay is not a calibrated real map, so real coordinates can still look visually misaligned against coastlines/city placement until the underlay is regenerated or georeferenced.

Label/pan/splash iteration result:

- City labels now sit centered under city pictograms and city dots were removed to reduce visual noise.
- Pan speed was reduced again; device feel-test is still required because this is perception-sensitive.
- The splash image was regenerated with a more plausible cableway structure, but it should still be treated as stylized art rather than engineering documentation.

Relief/marker iteration result:

- Runtime map source returned to reproducible `map_pipeline.compose_map`, so relief, water and islands are geography-driven rather than inherited from an unaudited generated underlay.
- Relief is now split into named layers: Alps, Black Forest, Harz, Erzgebirge, Bavarian Forest, Eifel/Hunsrueck and North German Plain.
- Mountain symbols are typed by layer: `alpine`, `forested_highland`, `border_highland`, `lowland`. North German Plain has no mountain glyphs.
- Transport marker plates were reduced to a thin atlas outline and light shadow; the heavy black circular backing was removed.
- City labels clamp inside the viewport, so Berlin/Dresden labels do not cut off at the screen edge.
- Fresh Web build is served on `http://127.0.0.1:9000/`; `index.pck` returns `Content-Encoding: gzip` and `Cache-Control: no-store`.

Screenshots:

- `/tmp/cable-world-web-map/mobile-390x844-map-v4.png`
- `/tmp/cable-world-web-map/desktop-1280x800-map-v4.png`

Rubric estimate after relief/marker iteration 2026-05-31 13:36: stronger 7/10 candidate. The map is more accurate and readable, but still not 8/10 because the procedural underlay is visually flatter than the reference and desktop/landscape composition needs another art-direction pass.

Dotted route iteration result:

- Procedural route strokes were changed from thick bright continuous lines to thin dotted atlas trails.
- The intent is to keep routes as orientation hints without making the map look like a road diagram or competing with transport icons.
- Fresh Web build remains on `http://127.0.0.1:9000/`; `index.pck` returns gzip and no-store headers.

Screenshots:

- `/tmp/cable-world-web-map/mobile-390x844-map-v5.png`
- `/tmp/cable-world-web-map/desktop-1280x800-map-v5.png`

Rubric estimate after dotted route iteration 2026-05-31 13:43: still 7/10 candidate, but closer to 8/10 on marker readability. Remaining risk: trails may now be too subtle and need a small contrast increase after user review.

Sprite glyph terrain iteration result:

- User rated the previous state around 6/10: still visually boring, marker backings were still noticeable, and mountains/lakes/forests needed to read as intentional map features.
- Generated one reusable `assets/map/glyphs/map_glyph_sheet.png` sprite sheet with Alpine ranges, forested highlands, border highlands, lakes, and forest clusters, then sliced it into project assets.
- The map pipeline now places glyphs by geographic coordinates/layer definitions: Alps, Harz/Black Forest/Bavarian Forest/Erzgebirge, lake anchors, and forest clusters are not random decorative stamps.
- Country clipping was changed from Germany-only to land-mask clipping for soft relief, so cross-border ranges can continue beyond Germany while ocean stays clean.
- Germany border is redrawn as a visible atlas border on top of the relief, so removing Germany-only clipping does not make borders ambiguous.

Screenshots:

- `/tmp/cable-world-web-map/mobile-390x844-map-v9.png`
- `/tmp/cable-world-web-map/desktop-1280x800-map-v9.png`

Rubric estimate after sprite glyph terrain iteration 2026-05-31: stronger 7/10 candidate, not 8/10 yet. Alps and forests finally read as map glyphs, but the exact scale/extent of every range still needs geographic tuning before it satisfies the 10/10 terrain accuracy criterion.

Explicit relief placement iteration result:

- Mountain sprite selection moved from hash-based choice inside `_draw_mountains()` to explicit `mountain_glyphs` in `RELIEF_REGIONS`.
- Alps now use a controlled sequence of `alps_range_*` and `alps_peak_*` placements along the southern Alpine band, so start/end/scale can be tuned directly.
- Harz, Black Forest, Bavarian Forest and Erzgebirge now each declare their own sprite, anchor and width instead of inheriting a generic random-looking range.
- Fresh Web build is served on `http://127.0.0.1:9000/`; `index.pck` returns gzip and no-store headers.

Screenshots:

- `/tmp/cable-world-web-map/mobile-390x844-map-v11.png`
- `/tmp/cable-world-web-map/desktop-1280x800-map-v11.png`

Rubric estimate after explicit relief placement iteration 2026-05-31: still around 7/10. It is materially closer to 8/10 because major relief is now controllable by real layer definitions, but final quality still needs calibrated extents against a real relief source and a pass on label/marker crowding.

Outline readability iteration result:

- Transport and city landmark sprites now have generated outline-only runtime variants under `assets/sprites/outlined/` and `assets/sprites/city_landmarks/outlined/`.
- The map UI loads those outlined variants, so objects can read over forests/lakes/routes without reintroducing circles, plaques, or background disks.
- City labels were moved closer to their pictograms. Secondary town labels are hidden until zoom `1.20`, while major landmarks such as Berlin, Hamburg, Rostock, Köln, München, Dresden and Stuttgart remain available at the default view.
- Fresh Web build is served on `http://127.0.0.1:9000/`; `index.pck` returns gzip and no-store headers.
- Browser verification regenerated screenshots via `PLAYWRIGHT_PACKAGE=/tmp/cable-playwright/node_modules/playwright node scripts/verify-web-map.mjs`.

Screenshots:

- `/tmp/cable-world-web-map/mobile-390x844-initial.png`
- `/tmp/cable-world-web-map/mobile-390x844-after-marker-click.png`
- `/tmp/cable-world-web-map/mobile-390x844-after-drag.png`
- `/tmp/cable-world-web-map/desktop-1280x800-initial.png`
- `/tmp/cable-world-web-map/desktop-1280x800-after-marker-click.png`
- `/tmp/cable-world-web-map/desktop-1280x800-after-drag.png`

Rubric estimate after outline readability iteration 2026-05-31: still about 7/10, not 8/10. Readability is better and the "circles around objects" issue is reduced, but desktop composition still crops some labels/icons at the edges and terrain accuracy still needs real relief/lake extent calibration before a confident 8/10.
