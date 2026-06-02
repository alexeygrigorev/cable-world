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

Corrected rubric estimate after later user review 2026-05-31: this should not have been scored as 7/10. The procedural underlay still reads too much like a GIS canvas with map symbols layered on top, so it belongs around 4/10 until the base art direction changes.

Sprite glyph terrain iteration result:

- User rated the previous state around 6/10: still visually boring, marker backings were still noticeable, and mountains/lakes/forests needed to read as intentional map features.
- Generated one reusable `assets/map/glyphs/map_glyph_sheet.png` sprite sheet with Alpine ranges, forested highlands, border highlands, lakes, and forest clusters, then sliced it into project assets.
- The map pipeline now places glyphs by geographic coordinates/layer definitions: Alps, Harz/Black Forest/Bavarian Forest/Erzgebirge, lake anchors, and forest clusters are not random decorative stamps.
- Country clipping was changed from Germany-only to land-mask clipping for soft relief, so cross-border ranges can continue beyond Germany while ocean stays clean.
- Germany border is redrawn as a visible atlas border on top of the relief, so removing Germany-only clipping does not make borders ambiguous.

Screenshots:

- `/tmp/cable-world-web-map/mobile-390x844-map-v9.png`
- `/tmp/cable-world-web-map/desktop-1280x800-map-v9.png`

Corrected rubric estimate after later user review 2026-05-31: not 7/10. Sprite glyphs improved individual details, but the overall map still fails the reference-target art direction. Treat this as 4/10 unless a new underlay makes the whole map feel cohesive.

Explicit relief placement iteration result:

- Mountain sprite selection moved from hash-based choice inside `_draw_mountains()` to explicit `mountain_glyphs` in `RELIEF_REGIONS`.
- Alps now use a controlled sequence of `alps_range_*` and `alps_peak_*` placements along the southern Alpine band, so start/end/scale can be tuned directly.
- Harz, Black Forest, Bavarian Forest and Erzgebirge now each declare their own sprite, anchor and width instead of inheriting a generic random-looking range.
- Fresh Web build is served on `http://127.0.0.1:9000/`; `index.pck` returns gzip and no-store headers.

Screenshots:

- `/tmp/cable-world-web-map/mobile-390x844-map-v11.png`
- `/tmp/cable-world-web-map/desktop-1280x800-map-v11.png`

Corrected rubric estimate after later user review 2026-05-31: still around 4/10 visually. Explicit relief placement is useful technical infrastructure, but it does not by itself solve the weak visual direction.

Outline readability iteration result:

- Transport and city landmark sprites now have generated outline-only runtime variants under `assets/sprites/outlined/` and `assets/sprites/city_landmark_clusters_hi_res/outlined/`.
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

Corrected rubric estimate after later user review 2026-05-31: still around 4/10. Outline readability fixes marker contrast, but the map still looks bad as a whole, so the score must be capped by art quality.

Adaptive default view iteration result:

- Portrait/mobile keeps `DEFAULT_ZOOM := 1.10`, preserving the stronger map-first feel the user asked for.
- Landscape/desktop now uses `DEFAULT_LANDSCAPE_ZOOM := 1.0`, so the initial view shows more context and reduces edge clipping around Köln, Hamburg, Berlin, Dresden and Stuttgart.
- City and terrain labels are skipped when their anchor is far outside the viewport, and centered labels now clamp vertically as well as horizontally.
- Fresh Web build is served on `http://127.0.0.1:9000/`; `index.pck` returns gzip and no-store headers.
- Browser verification regenerated screenshots via `PLAYWRIGHT_PACKAGE=/tmp/cable-playwright/node_modules/playwright node scripts/verify-web-map.mjs`.

Screenshots:

- `/tmp/cable-world-web-map/mobile-390x844-initial.png`
- `/tmp/cable-world-web-map/mobile-390x844-after-marker-click.png`
- `/tmp/cable-world-web-map/mobile-390x844-after-drag.png`
- `/tmp/cable-world-web-map/desktop-1280x800-initial.png`
- `/tmp/cable-world-web-map/desktop-1280x800-after-marker-click.png`
- `/tmp/cable-world-web-map/desktop-1280x800-after-drag.png`

Corrected rubric estimate after user review 2026-05-31: 4/10. Desktop composition is less cramped than before, but the base map still does not meet the desired atlas/RPG quality. The next meaningful move is not marker polish; it is replacing or heavily reworking the underlay art direction while preserving coordinate-driven interactive overlays.

Rubric correction note:

- User review: "карта все ещё выглядит очень плохо. где-то на 4/10".
- Previous assistant estimates around 7/10 were too generous because they over-weighted technical progress: aspect ratio, gzip, clickability, explicit relief data and marker outlines.
- Updated `docs/map-quality-rubric.md` now caps the score at 4/10 when the map reads as a procedural/GIS canvas with sprites layered on top.
- New target before claiming 6/10+: the underlay itself must feel like a cohesive 16-bit/RPG atlas screenshot, not a technically correct base map with decorative elements.

Generated atlas underlay iteration:

- Replaced the procedural/GIS-like runtime underlay with a new generated 16-bit/RPG atlas underlay adapted through `map_pipeline.adapt_generated_underlay`.
- Generated source:
  `/home/alexey/.codex/generated_images/019e7af1-437a-70f1-9164-d2f7b34a9c81/ig_0f7b9b4e8b981acb016a1c31509270819181e045e751bc63c8.png`
- Runtime asset:
  `assets/map/germany_styled.png`, 1568x2048, 5.1 MB.
- Fresh Web build is served on `http://127.0.0.1:9000/`; `index.pck` returns `Content-Encoding: gzip` and `Cache-Control: no-store`.
- `index.pck` is now about 15 MB gzip. This is acceptable for visual review, but asset size must be optimized before calling the result production-ready.
- Browser verification regenerated screenshots via `PLAYWRIGHT_PACKAGE=/tmp/cable-playwright/node_modules/playwright URL=http://127.0.0.1:9000/ node scripts/verify-web-map.mjs`.

Screenshots:

- `/tmp/cable-world-web-map/mobile-390x844-initial.png`
- `/tmp/cable-world-web-map/mobile-390x844-after-marker-click.png`
- `/tmp/cable-world-web-map/mobile-390x844-after-drag.png`
- `/tmp/cable-world-web-map/desktop-1280x800-initial.png`
- `/tmp/cable-world-web-map/desktop-1280x800-after-marker-click.png`
- `/tmp/cable-world-web-map/desktop-1280x800-after-drag.png`

Rubric estimate after screenshot review: 6/10. This is no longer capped at 4/10 by the procedural/GIS-underlay rule because the base image now reads as an adventure atlas. It is still not 8/10: geography is not sufficiently audited, generated decorative towns/rivers may conflict with real coordinates, some labels are clipped near viewport edges, dense terrain competes with interactive icons, and the Web payload grew.

Viewport-aware icon iteration:

- City landmark rectangles are clamped inside the visible viewport and outside the top-right zoom/list controls.
- Secondary town labels are skipped when they would overlap higher-priority city landmark rectangles.
- Transport markers now scale with both zoom and viewport width via `_map_visual_scale()`, with min/max caps.
- City landmark pictograms now scale with both zoom and viewport width via `_landmark_visual_scale()`, with min/max caps.
- Fresh Web build is served on `http://127.0.0.1:9000/`; `index.pck` returns gzip/no-store.

Screenshots:

- `/tmp/cable-world-web-map/mobile-390x844-initial.png`
- `/tmp/cable-world-web-map/mobile-390x844-after-marker-click.png`
- `/tmp/cable-world-web-map/mobile-390x844-after-drag.png`
- `/tmp/cable-world-web-map/desktop-1280x800-initial.png`
- `/tmp/cable-world-web-map/desktop-1280x800-after-marker-click.png`
- `/tmp/cable-world-web-map/desktop-1280x800-after-drag.png`

Rubric estimate remains around 6/10. This fixes an interaction/responsive rendering problem, but it does not solve the remaining 8/10 blockers: generated geography audit, visual hierarchy over dense terrain, and payload size.

Marker-priority label iteration:

- Object marker rectangles are now passed into the underlay as reserved label zones.
- Secondary town and terrain labels skip drawing when they would overlap visible object markers or clusters.
- This keeps interactive transport icons visually dominant without adding circular marker backgrounds or moving real coordinates.
- Fresh Web build is served on `http://127.0.0.1:9000/`; `index.pck` returns gzip/no-store.

Screenshots:

- `/tmp/cable-world-web-map/mobile-390x844-initial.png`
- `/tmp/cable-world-web-map/mobile-390x844-after-marker-click.png`
- `/tmp/cable-world-web-map/mobile-390x844-after-drag.png`
- `/tmp/cable-world-web-map/desktop-1280x800-initial.png`
- `/tmp/cable-world-web-map/desktop-1280x800-after-marker-click.png`
- `/tmp/cable-world-web-map/desktop-1280x800-after-drag.png`

Rubric estimate remains around 6/10. The interaction layer is cleaner, but the 8/10 blockers are still the generated geography audit, stronger object/background hierarchy across all regions, and payload size.

Pan/label/splash iteration:

- City landmark icons and labels are no longer clamped to the viewport edge. They stay tied to their projected map coordinates while panning.
- City landmark rendering was split into an overlay above transport markers, so city names remain legible when markers are nearby.
- Zoom controls now show the current zoom percentage.
- `assets/branding/splash_loading.png` was compressed from 3.3 MB to about 125 KB. JPEG was tested but rejected by Godot for boot splash, so the boot image remains PNG.
- Added backlog item: remove baked city-like pictograms from the generated underlay to avoid duplicate cities under runtime landmarks.

Rubric estimate remains around 6/10. These are usability and payload fixes; the underlay itself still needs art/geography cleanup.

Production direction correction:

- Current whole-map generated underlay is not acceptable as a final production architecture.
- The map must move to a clean base + glyph-layer composition, documented in `docs/map-production-direction.md`.
- A whole generated map can be used only as reference/mood or to identify needed glyphs.
- Quality cannot improve past the current ~6/10 while baked cities, baked random details, and runtime overlays fight each other in one bitmap.

Glyph-pipeline first cut:

- `map_pipeline.compose_map` no longer places baked town/city pictograms in the underlay.
- `assets/map/germany_styled.png` is regenerated from the clean composed pipeline and is now about 272 KB.
- Web `index.pck` is about 7.1 MB gzip.
- Runtime city landmarks are now the only city layer visible over the base.

Rubric estimate remains around 6/10. This removes a structural blocker, but the map still needs more high-quality explicit glyph layers before it looks rich enough.

Atlas detail glyph iteration:

- Added reproducible glyph generation for ships, ports, bridges, castles, and a tower.
- Added explicit `ATLAS_DETAILS` placement data instead of embedding those details in a whole generated bitmap.
- The details are intentionally small so they add life without becoming city markers or competing with runtime transport icons.

Rubric estimate remains around 6/10. The architecture is now more correct, but visual richness still needs more region-specific glyph work.
