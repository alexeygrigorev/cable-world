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
- City/terrain labels now provide orientation: Berlin, Hamburg, Rostock, Koeln, Muenchen, Harz, Zugspitze, Alps.
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
