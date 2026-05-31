# Map Orchestrator Progress

Дата: 2026-05-31 10:41 CEST.

## WeChat Message

Принял первую обратную связь по карте Германии. Текущая версия технически уже грузится и двигается, но визуально пока не проходит целевой уровень: фон слишком детальный и неконтрастный, фуникулеры/канатки сливаются с подложкой, Германию сложно узнать без городских ориентиров.

Следующая итерация: усиливаем читаемость объектов, добавляем ориентиры Berlin/Hamburg/Rostock, делаем подписи городов/гор поверх карты в духе старых фэнтези-карт, приводим zoom к управляемому поведению: старт ближе, есть кнопки плюс/минус, zoom-out ограничен. Отдельно фиксируем пайплайн транспортных иконок по нормализованным типам, чтобы gondola, aerial tram, funicular и другие типы отличались сразу. После первой итерации по Германии показываем свежие screenshots и оцениваем по рубрике, затем решаем, готова ли карта к расширению на Францию/Испанию/Европу.

## Backlog

- [x] Сделать фон Германии менее шумным и более контрастным для overlay-иконок.
- [x] Усилить видимость транспортных маркеров: читаемая подложка/ореол, hover/selected state, кликабельность без потери drag.
- [x] Добавить городские ориентиры Berlin, Hamburg, Rostock независимо от наличия транспортного объекта.
- [x] Добавить подписи городов и гор поверх карты в стиле старой приключенческой карты.
- [x] Сделать default zoom ближе.
- [x] Показать кнопки zoom + и - прямо поверх fullscreen-карты.
- [x] Ограничить zoom-out так, чтобы карта не отдалялась бесконечно и не теряла фокус.
- [x] Описать city/urban-cluster strategy: как показывать несколько канаток внутри города без перегруза.
- [ ] Расширить image/icon pipeline: transport type -> recognizable icon, без `contains()`.
- [ ] Зафиксировать план будущих регионов: Germany -> France/Spain -> Europe including Russia/Belarus/Ukraine to Ukrainian mountains + Turkey; остальные страны менее детально.

## Quality Status

Предыдущая самооценка `10/10` отменена после пользовательского review. Текущая карта считается рабочей, но визуально недостаточной: `6/10`. Следующая цель для Германии - минимум `8/10` по `docs/map-quality-rubric.md`.

Новый критерий: карта должна читаться глазами сразу, без рассматривания. Текущий стиль можно оставить как основу, но надписи и ориентиры должны быть ближе к старой приключенческой карте: Middle-earth / Heroes / Warcraft top-down. Нужны более спокойные зоны под маркерами, сильнее отделенные транспортные иконки и подписи городов/гор.

## Iteration 2026-05-31 10:49

Implemented:

- Visible map overlay zoom controls on the fullscreen map.
- `DEFAULT_ZOOM = 1.10`, `MIN_ZOOM = 1.0` so zoom-out stops at the base fill.
- Landmark labels for Hamburg, Berlin, Rostock, Koeln, Muenchen, Harz, Zugspitze, Alps.
- Stronger outlined label text and larger marker hit/visual area.
- Parchment marker background, dark border, and stronger shadow for readability.

Evidence:

- `/tmp/cable-world-web-map/mobile-390x844-initial.png`
- `/tmp/cable-world-web-map/desktop-1280x800-initial.png`
- `/tmp/cable-world-web-map/mobile-390x844-after-marker-click.png`
- `/tmp/cable-world-web-map/desktop-1280x800-after-marker-click.png`

Self-audit: candidate `7/10`, not `10/10`. The biggest remaining visual problem is that the underlay still has too much texture in dense object areas. The next production-quality step is either a new generated underlay with planned quiet zones or a runtime cluster layer for city/object groups.

## Iteration 2026-05-31 11:06

Implemented:

- Deliberate low-zoom object clusters in `scripts/map_panel.gd`.
- Close objects collapse into a single large parchment/orange count marker below `OBJECT_CLUSTER_ZOOM_THRESHOLD = 1.45`.
- Clicking a cluster zooms and pans to the group instead of selecting a random representative object.
- After zooming into the group, the cluster expands back into individual transport icons.
- Cluster behavior is now covered by `tests/test_map_panel_contract.py`.

Evidence:

- `/tmp/cable-world-web-map/mobile-390x844-initial.png`
- `/tmp/cable-world-web-map/desktop-1280x800-initial.png`
- `/tmp/cable-world-web-map/mobile-cluster-after-click.png`

Checks:

- `python3 -m unittest discover -s tests`: 218 OK.
- `godot --headless --path . --quit-after 1`: no new GDScript errors; existing shutdown RID warnings remain.
- `index.pck` and `index.wasm` still return `Content-Encoding: gzip`.

Self-audit: stronger `7/10` and closer to `8/10`, but still not `10/10`. Cluster behavior reduces noise and solves the worst "too busy" issue, but the cluster count badges are still more UI-like than ideal atlas landmarks. The next visual step toward 8/10+ is a generated or post-processed underlay with quieter object zones and cluster badges that look more native to the map style.

## Iteration 2026-05-31 11:30

Implemented:

- Generated one 8x8 city landmark sprite sheet for 64 German/European city icons in one image-generation call.
- Sliced all 64 city landmark icons into `assets/sprites/city_landmarks/` for current and future maps.
- Added Germany landmarks to the map layer: Berlin, Hamburg, Rostock, Köln, München, Dresden, Stuttgart.
- Added `map_pipeline/slice_city_landmarks.py` so the sprite sheet slicing is repeatable.
- Updated German city labels to use umlauts where needed.
- Enlarged city landmark rendering and changed cluster badges to a quieter parchment/atlas treatment.

Evidence:

- `/tmp/cable-world-web-map/mobile-390x844-initial.png`
- `/tmp/cable-world-web-map/desktop-1280x800-initial.png`

Self-audit: direction improved, but still not `8/10`. City pictograms make the map more recognizable and less generic, but some icons are still too small/partly hidden on desktop and cluster badges remain a compromise. Next step: tune landmark placement/priority and replace count badges with native atlas group markers.

## Iteration 2026-05-31 12:05

Implemented:

- Reviewed and committed the parallel themed splash/loading + Android icon work as `f92eeb5`.
- Created/persisted the active TODO in `docs/active-map-backlog.md` and mapped the current work into GitHub issues `#55-#59`.
- Fixed the city landmark draw path: generated city pictograms were loaded but the draw block was accidentally unreachable after the null-texture return.
- Normalized map panning through one helper for mouse drag, touch drag, and marker drag.
- Reduced drag speed with `PAN_DRAG_SCALE = 0.22` so pan feels calmer and closer to the user's finger/mouse movement.
- Added a contract test so city landmark icons must be drawn after successful texture load.

Checks:

- `python3 -m unittest tests.test_map_panel_contract`: 10 OK.
- `godot --headless --path . --quit-after 1`: no new GDScript errors; existing shutdown RID warnings remain.

Self-audit: this fixes a functional regression that made city icons appear as plain dots. It does not yet solve the deeper geography/art alignment problem, so the map is still not an `8/10`.

## Iteration 2026-05-31 12:22

Implemented:

- Changed city landmark labels to sit centered under the pictogram instead of beside a separate city dot.
- Removed the city dot from city landmark rendering; the pictogram is now the city anchor.
- Lowered `PAN_DRAG_SCALE` again from `0.45` to `0.22` after user feedback that touch pan was still too sensitive.
- Replaced the splash/loading image with a new generated version that keeps the atlas style but shows a more plausible cable car: cabin vertical, clear hanger/roller assembly, support towers, and continuous cables.
- Removed large non-runtime source PNGs from `res://assets/branding/` and deleted the local `tmp/city-landmark-source/` folder so Web exports do not ship unused source sheets.

Self-audit: the city layer reads cleaner and splash physics is improved. Pan needs direct user feel-testing on the device; if still too fast, the next adjustment is a smaller single constant rather than structural changes.

## Iteration 2026-05-31 12:38

Implemented:

- Moved city labels closer to their pictograms: the baseline gap changed from `14.0 * zoom` to `8.0 * zoom`.
- Replaced the splash/loading image again after user feedback that the previous version still failed cableway physics.
- Rechecked the selected splash candidate against a physics checklist before accepting it into `assets/branding/splash_loading.png`:
  - two towers visible inside the frame;
  - cables run between the towers;
  - cabin hangs below the cables;
  - cabin remains vertical;
  - cables do not pass through the cabin body/windows;
  - no funicular rails or ground track are mixed into the aerial cable car.

Self-audit: this is a stronger splash candidate, but still stylized art rather than an engineering diagram. Do not score the whole project as `10/10` from this change alone.

## Iteration 2026-05-31 12:50

Implemented:

- Changed the Germany initial map focus from the generated image center to a real geographic anchor: `Vector2(11.35, 51.45)`.
- Kept city/object coordinates unchanged; only the first camera position changed.
- Changed low-zoom cluster markers from plain numeric parchment buttons to atlas-style station markers with a small count label.
- Added contract coverage for the initial focus coordinate and cluster station icon treatment.

Self-audit: this should make the first mobile frame more recognizable and reduce the UI-button feeling of clusters. It still needs fresh screenshot review before claiming any score increase.

## Iteration 2026-05-31 15:10

Implemented:

- Corrected the quality criteria after user rated the previous map around `4/10`: procedural/GIS-looking underlays now cap the score at `4/10`, regardless of technical improvements.
- Generated a new full-map RPG-atlas underlay and adapted it into `assets/map/germany_styled.png`.
- Rebuilt Web on `http://127.0.0.1:9000/` and verified `index.pck` gzip/no-store headers.

Evidence:

- `/tmp/cable-world-web-map/mobile-390x844-initial.png`
- `/tmp/cable-world-web-map/mobile-390x844-after-marker-click.png`
- `/tmp/cable-world-web-map/mobile-390x844-after-drag.png`
- `/tmp/cable-world-web-map/desktop-1280x800-initial.png`
- `/tmp/cable-world-web-map/desktop-1280x800-after-marker-click.png`
- `/tmp/cable-world-web-map/desktop-1280x800-after-drag.png`

Checks:

- `python3 -m unittest tests.test_map_panel_contract`: 12 OK.
- `curl -I --compressed http://127.0.0.1:9000/index.pck`: `Content-Encoding: gzip`, `Cache-Control: no-store`.

Self-audit: current map is approximately `6/10`. The underlay now reads as an adventure atlas instead of a procedural/GIS canvas, but it is not `8/10`: generated decorative geography still needs an audit, edge labels need clipping fixes, dense terrain competes with markers in places, and the Web payload increased to about 15 MB gzip.

## Iteration 2026-05-31 15:24

Implemented:

- City landmark icons and labels now clamp inside the viewport and avoid the top-right controls.
- Secondary city/town labels are skipped when they collide with higher-priority city landmark blocks.
- Runtime transport markers scale with both zoom and viewport width, so resizing the map also changes marker size.
- City landmark pictograms scale with both zoom and viewport width, with a maximum cap to preserve pixel-art readability.

Evidence:

- `/tmp/cable-world-web-map/mobile-390x844-initial.png`
- `/tmp/cable-world-web-map/mobile-390x844-after-marker-click.png`
- `/tmp/cable-world-web-map/desktop-1280x800-initial.png`

Checks:

- `python3 -m unittest tests.test_map_panel_contract`: 12 OK.
- `curl -I --compressed http://127.0.0.1:9000/index.pck`: `Content-Encoding: gzip`, `Cache-Control: no-store`.

Self-audit: still around `6/10`. This fixes the user-reported resize behavior and reduces edge clipping, but the map still needs geography/aesthetic work before it can honestly be `8/10`.

## Iteration 2026-05-31 15:33

Implemented:

- MapPanel now collects visible object-marker rectangles and sends them to the underlay as reserved label zones.
- Secondary town and terrain labels skip drawing when they overlap those reserved zones.
- This removes obvious conflicts like terrain/town labels crossing the Harz transport cluster while keeping the fullscreen map clean.

Evidence:

- `/tmp/cable-world-web-map/mobile-390x844-initial.png`
- `/tmp/cable-world-web-map/mobile-390x844-after-marker-click.png`
- `/tmp/cable-world-web-map/desktop-1280x800-initial.png`

Checks:

- `python3 -m unittest tests.test_map_panel_contract`: 12 OK.
- `godot --headless --path . --import --quit`: no parse/import errors.
- `curl -I --compressed http://127.0.0.1:9000/index.pck`: `Content-Encoding: gzip`, `Cache-Control: no-store`.

Self-audit: still around `6/10`. Visual hierarchy is better, but the project still needs a geography audit of the generated underlay, stronger art direction consistency, and payload optimization before claiming `8/10`.

## Iteration 2026-05-31 15:40

Implemented:

- Compressed `assets/branding/splash_loading.png` from 3.3 MB to about 125 KB.
- Kept the file as PNG because Godot rejected JPEG for `boot_splash/image`; the engine supports PNG there.
- Added visible zoom percentage in the map zoom controls.
- Moved city landmark labels/icons to a separate overlay above transport markers.
- Removed viewport clamping from city landmark icon/label positions so Hamburg/Rostock/Berlin/etc. stay attached to their geographic coordinates during pan.

Backlog captured:

- The generated map underlay currently contains baked city-like pictograms, then runtime city landmarks are drawn over it. This needs a new underlay/pipeline pass so we do not render duplicate cities.

Self-audit: still around `6/10`. This fixes interaction/layering regressions and payload for the splash screen, but the map still needs underlay cleanup and geography audit before it can move toward `8/10`.

## Direction Lock 2026-05-31

User feedback: we are repeating the same mistake by generating or polishing one whole-map image instead of moving toward the agreed layered atlas pipeline.

Action taken:

- Added `docs/map-production-direction.md` as the active production decision.
- Added a stop rule: no more monolithic generated Germany/Europe bitmaps as the final map approach.
- Locked next map work to clean base geography + reusable glyph sprites + explicit coordinate placement.

Required next work:

- Decompose the current visual direction into glyph layers: Alps, Harz, Saxon Switzerland / Elbe Sandstone, Erzgebirge, Black Forest, Bavarian Forest, forests, lakes, ships, ports, bridges, and atlas details.
- Remove baked city/village pictograms from the base map.
- Keep runtime city landmarks and transport objects as the only city/object overlay.

## Iteration 2026-05-31 15:52

Implemented:

- Removed the baked town/city pictogram list from `map_pipeline.compose_map`.
- Added `BAKED_TOWN_DETAILS_ENABLED = False` and an empty `BAKED_TOWN_DETAILS` list as a contract: runtime city landmarks are the only city layer.
- Regenerated `assets/map/germany_styled.png` from the composed glyph pipeline, not from a monolithic generated bitmap.
- The map asset dropped from about 5.1 MB to about 272 KB.
- The Web `index.pck` dropped to about 7.1 MB gzip.

Evidence:

- `/tmp/cable-world-web-map/mobile-390x844-initial.png` shows no baked town/village scatter under the runtime city landmarks.
- `curl -I --compressed http://127.0.0.1:9000/index.pck`: `Content-Encoding: gzip`, `Cache-Control: no-store`.

Self-audit: still around `6/10`. This is an architectural correction, not a final visual win. The map is cleaner and expandable, but now needs more explicit glyph detail layers: Saxon Switzerland / Elbe Sandstone, ships/ports, better forest/lake density, and cross-border relief continuity.

## Iteration 2026-05-31 16:02

Implemented:

- Added `map_pipeline.generate_map_detail_glyphs`, a reproducible generator for small transparent atlas detail glyphs:
  - `detail_ship`
  - `detail_port`
  - `detail_bridge`
  - `detail_castle`
  - `detail_tower`
- Added `ATLAS_DETAILS` to `map_pipeline.compose_map`, with explicit `id`, `kind`, `glyph`, `lon`, `lat`, `width`, and `region`.
- Replaced procedural castle drawing with data-driven detail glyph placement.
- Added first ships/ports/bridges/castles/tower without adding baked city clutter.

Evidence:

- `/tmp/cable-world-web-map/mobile-390x844-initial.png` shows ships/ports/castles as small atlas details while runtime city landmarks remain the only city layer.
- `assets/map/germany_styled.png`: about 276 KB.
- `build/web/index.pck`: about 7.1 MB gzip.
- `curl -I --compressed http://127.0.0.1:9000/index.pck`: `Content-Encoding: gzip`, `Cache-Control: no-store`.

Self-audit: still around `6/10`. This improves the production architecture and adds visual detail, but the map still needs stronger art direction, better regional density, and a relief/lake/city-position audit before claiming `8/10`.

## Iteration 2026-05-31 16:17

Implemented:

- Used the previous monolithic RPG-atlas map as a detail donor, but did not restore it as the runtime background.
- Added six more reproducible atlas glyph types:
  - `detail_village`
  - `detail_chapel`
  - `detail_ruins`
  - `detail_windmill`
  - `detail_lighthouse`
  - `detail_watermill`
- Added more `ATLAS_DETAILS` placements for villages, chapels, ruins, windmills, lighthouses, watermills, ships, ports and bridges.
- Added more route segments, tree clusters and field patches to reduce the empty-map feeling.
- Expanded the coordinate/map bounds from Germany-only `4.5..15.5 / 46.5..55.5` to `4.5..16.8 / 43.2..55.8`, so the user can pan south below Germany and see neighboring country outlines around Switzerland, Austria and northern Italy.
- Limited runtime zoom to `50%..150%` instead of allowing `400%`, because higher zoom was making the current raster/glyph composition visibly pixelated.

Evidence:

- `/tmp/cable-world-web-map/mobile-390x844-initial.png` shows München and the Alps in the initial frame instead of hard clipping them out.
- `/tmp/cable-world-web-map/mobile-390x844-after-drag.png` shows the new `150%` zoom cap and denser map details.
- `assets/map/germany_styled.png`: about 301 KB.
- `build/web/index.pck.gz`: about 7.0 MB.
- `curl -I --compressed http://127.0.0.1:9000/index.pck`: `Content-Encoding: gzip`, `Cache-Control: no-store`.

Checks:

- `python3 -m unittest tests.test_map_panel_contract`: 12 OK.
- `godot --headless --path . --import --quit`: no parse/import errors. Existing worktree warning and adb daemon warning remain.
- `PLAYWRIGHT_PACKAGE=/tmp/cable-playwright/node_modules/playwright URL=http://127.0.0.1:9000/ node scripts/verify-web-map.mjs`: screenshots regenerated.

Self-audit: still around `6/10`. This fixes the immediate south-pan/cropped-München problem and makes the map less empty, but it is not yet the requested `8/10`: the Alps/relief glyph set still needs a dedicated quality pass, and glyph assets should be regenerated or resized around the `150%` maximum so details stay clean at the chosen zoom cap.

## Iteration 2026-05-31 16:26

Implemented:

- Fixed the map texture aspect after expanding the geographic bounds. The expanded Mercator bounds are about `0.629` wide/tall, while the old `1568x2048` texture was `0.766`, which could visibly stretch the map.
- Regenerated `assets/map/germany_styled.png` at `1932x3072`, close to the active Mercator aspect and large enough that runtime `150%` zoom does not upscale the base map texture beyond its source resolution.
- Added a contract assertion for `MAP_SIZE = (1932, 3072)` so future map edits do not silently return to the stretched old texture shape.

Evidence:

- `assets/map/germany_styled.png`: `1932x3072`, about 422 KB.
- `/tmp/cable-world-web-map/mobile-390x844-initial.png` and `/tmp/cable-world-web-map/mobile-390x844-after-drag.png` regenerated after rebuild.
- The after-drag screenshot shows the expected `150%` cap with a sharper base map than the previous `1568x2048` texture.
- `curl -I --compressed http://127.0.0.1:9000/index.pck`: `Content-Encoding: gzip`, `Cache-Control: no-store`, gzip payload about 7.1 MB.

Checks:

- `python3 -m unittest tests.test_map_panel_contract`: 12 OK.
- `godot --headless --path . --import --quit`: no parse/import errors. Existing worktree warning and adb daemon warning remain.
- Web export rebuilt and served on `http://127.0.0.1:9000/`.
- `PLAYWRIGHT_PACKAGE=/tmp/cable-playwright/node_modules/playwright URL=http://127.0.0.1:9000/ node scripts/verify-web-map.mjs`: screenshots regenerated.

Self-audit: still around `6/10`. This removes a technical quality blocker: stretched geometry and source upscaling at `150%`. It does not yet solve the artistic target for Alps/relief glyphs or the overall `8/10+` visual density.

## Iteration 2026-05-31 16:41

Implemented:

- Expanded the Alps relief from a Germany-edge patch into a cross-border band spanning France, Switzerland, Italy and Austria inside the current extended map bounds.
- Added explicit `ridge_bands` for `main_alpine_wall` and `northern_alpine_foothills`, rendered before the individual mountain glyphs.
- Replaced the first geometric/sawtooth ridge attempt with a softer continuous ridge layer so the Alps read as one mountain mass instead of isolated pasted icons.
- Redistributed `alps_range_*` and `alps_peak_*` glyphs across the Alpine arc.
- Rechecked the active zoom requirement: runtime zoom is capped at `50%..150%`, the zoom percentage is visible on screen, and the base map source remains `1932x3072` so `150%` does not upscale the base texture above its source pixels in the tested mobile/desktop views.

Evidence:

- `assets/map/germany_styled.png`: `1932x3072`, about 453 KB.
- `/tmp/cable-world-web-map/mobile-390x844-initial.png` shows northern Germany plus München/Alps reachable in the same extended map.
- `/tmp/cable-world-web-map/mobile-390x844-after-drag.png` shows the `150%` zoom cap and scaled glyph/marker presentation.
- `/tmp/cable-world-web-map/desktop-1280x800-initial.png` shows the same map without the previous texture stretch.
- `curl -I --compressed http://127.0.0.1:9000/index.pck`: `Content-Encoding: gzip`, `Cache-Control: no-store`.

Checks:

- `python3 -m unittest tests.test_map_panel_contract`: 12 OK.
- `godot --headless --path . --import --quit`: no parse/import errors. Existing worktree warning and adb daemon warning remain.
- Web export rebuilt and served on `http://127.0.0.1:9000/`.
- `PLAYWRIGHT_PACKAGE=/tmp/cable-playwright/node_modules/playwright URL=http://127.0.0.1:9000/ node scripts/verify-web-map.mjs`: screenshots regenerated.

Self-audit: still around `6/10`. The Alps are now structurally closer to the requested direction, but this is not the final 8/10+ art pass. The next quality step remains a proper high-resolution terrain glyph set and relief/lake/city-position audit, with source assets sized for the `150%` maximum.

## Iteration 2026-05-31 16:48

Implemented:

- Removed the renderer's artificial half-size pixelation pass. The map no longer renders to `MAP_SIZE / 2` and then stretches back to `MAP_SIZE` with `Image.Resampling.NEAREST`.
- Kept the final map at `1932x3072`, but now downsamples the internal `2x` render buffer with `Image.Resampling.LANCZOS`, quantizes at full output resolution and applies a light sharpen pass.
- Added a contract guard so the map pipeline cannot silently reintroduce the half-size/nearest upscale finish.

Evidence:

- `assets/map/germany_styled.png`: `1932x3072`, about 1.9 MB.
- `/tmp/cable-world-web-map/mobile-390x844-initial.png` and `/tmp/cable-world-web-map/mobile-390x844-after-drag.png` regenerated. The `150%` screenshot is visibly less blocky than the previous nearest-upscaled map.
- `build/web/index.pck.gz`: about 8.4 MB after the quality pass.
- `curl -I --compressed http://127.0.0.1:9000/index.pck`: `Content-Encoding: gzip`, `Cache-Control: no-store`.

Checks:

- `python3 -m unittest tests.test_map_panel_contract`: 12 OK.
- `godot --headless --path . --import --quit`: no parse/import errors. Existing worktree warning and adb daemon warning remain.
- Web export rebuilt and served on `http://127.0.0.1:9000/`.
- `PLAYWRIGHT_PACKAGE=/tmp/cable-playwright/node_modules/playwright URL=http://127.0.0.1:9000/ node scripts/verify-web-map.mjs`: screenshots regenerated.

Self-audit: still around `6/10`. This fixes a real technical blocker for the user's `50%..150%` zoom requirement, but increases payload size and does not replace the need for better terrain/city/relief art direction. Next pass should optimize the map import/payload without returning to `NEAREST` blockiness, then continue with high-quality reusable terrain glyphs.

## Iteration 2026-05-31 16:54

Implemented:

- Reduced the Web payload without touching the new full-resolution map finish.
- Added export excludes for source-only sprite/material assets:
  - `assets/map/glyphs/map_glyph_sheet.png`
  - non-outlined transport source icons under `assets/sprites/icon_*.png`
  - non-outlined city landmark source icons under `assets/sprites/city_landmarks/city_*.png`
- Kept the runtime assets that the app actually loads: `assets/sprites/outlined/*` and `assets/sprites/city_landmarks/outlined/*`.
- Added `tests/test_export_payload_contract.py` so Web/Linux/Android presets keep excluding source-only assets.

Evidence:

- `build/web/index.pck.gz`: reduced from about 8.4 MB to about 5.4 MB.
- `curl -I --compressed http://127.0.0.1:9000/index.pck`: `Content-Encoding: gzip`, `Content-Length: 5653815`, `Cache-Control: no-store`.
- `/tmp/cable-world-web-map/mobile-390x844-initial.png`, `/tmp/cable-world-web-map/mobile-390x844-after-drag.png` and `/tmp/cable-world-web-map/desktop-1280x800-initial.png` regenerated after the exclude pass; runtime map/city/transport icons still render.

Checks:

- `python3 -m unittest tests.test_export_payload_contract tests.test_map_panel_contract tests.test_android_export_contract`: 18 OK.
- Web export rebuilt and served on `http://127.0.0.1:9000/`.
- `PLAYWRIGHT_PACKAGE=/tmp/cable-playwright/node_modules/playwright URL=http://127.0.0.1:9000/ node scripts/verify-web-map.mjs`: screenshots regenerated.

Self-audit: still around `6/10`. This removes the payload regression from the full-resolution finish and keeps the iteration testable. It does not solve the remaining 10/10 issues: stronger art direction, terrain/lake/city-position audit, and higher-quality reusable relief glyphs.

## Iteration 2026-05-31 17:04

Implemented:

- Replaced generic lake glyph placement for key water bodies with explicit named coordinate outlines in `NAMED_WATER_BODIES`.
- Added smoothed closed outlines for Bodensee, Müritz, Chiemsee, Schweriner See, Plauer See, Schaalsee, Steinhuder Meer, Edersee, Ammersee, Starnberger See, Tegernsee and Berlin lakes.
- Kept water bodies reproducible inside `map_pipeline.compose_map` instead of a one-off bitmap.
- First polygon pass was too angular; added `_smooth_closed_points` to keep coordinate anchoring while avoiding obvious low-poly lake shapes.

- Documented the map verification protocol in `docs/map-production-direction.md`.
- Made the verification process explicit: renderer command, unittest gate, Godot import/export, gzip header check, Playwright screenshot generation, screenshot review checklist, quality scoring gate and documentation/commit requirements.
- Added the current named water-body expectations to the screenshot review list so future map passes keep checking lakes/islands instead of treating them as decoration.

Evidence:

- `assets/map/germany_styled.png`: `1932x3072`, about 1.9 MB after the named-lake pass.
- `build/web/index.pck.gz`: about 5.4 MB after export.
- `curl -I --compressed http://127.0.0.1:9000/index.pck`: `Content-Encoding: gzip`, `Content-Length: 5631201`, `Cache-Control: no-store`.
- `/tmp/cable-world-web-map/mobile-390x844-initial.png`, `/tmp/cable-world-web-map/mobile-390x844-after-drag.png` and `/tmp/cable-world-web-map/desktop-1280x800-initial.png` regenerated after the named-lake pass.
- `docs/map-production-direction.md` now contains `Verification Protocol`.
- The protocol names the exact screenshots used for review:
  - `/tmp/cable-world-web-map/mobile-390x844-initial.png`
  - `/tmp/cable-world-web-map/mobile-390x844-after-drag.png`
  - `/tmp/cable-world-web-map/desktop-1280x800-initial.png`
- The protocol preserves the honest scoring gate: current working band is still `6/10`; `8/10` and `10/10` require broader proof than one screenshot.

Checks:

- `python3 -m unittest tests.test_map_panel_contract tests.test_export_payload_contract tests.test_android_export_contract`: 18 OK.
- `godot --headless --path . --import --quit`: no parse/import errors. Existing worktree warning and adb daemon warning remain.
- Web export rebuilt and served on `http://127.0.0.1:9000/`.
- `PLAYWRIGHT_PACKAGE=/tmp/cable-playwright/node_modules/playwright URL=http://127.0.0.1:9000/ node scripts/verify-web-map.mjs`: screenshots regenerated.

Self-audit: still around `6/10`. Named water bodies improve geography auditability and make the map less arbitrary, but the water visual hierarchy now needs art-direction tuning so lakes read as natural map features rather than isolated blue markers.

## Iteration 2026-05-31 17:14

Implemented:

- Tuned named water-body visual hierarchy after the first exact lake-outline pass.
- Replaced the saturated marker-like lake palette with muted atlas water constants: `NAMED_WATER_FILL`, `NAMED_WATER_SHALLOW`, `NAMED_WATER_SHORE`, `NAMED_WATER_OUTLINE` and `NAMED_WATER_HIGHLIGHT`.
- Added shoreline underpaint and softer highlights so Bodensee, Müritz, Chiemsee and the other named lakes sit inside the map instead of reading as UI overlays.

Evidence:

- `assets/map/germany_styled.png`: `1932x3072`, about 1.9 MB after the lake hierarchy pass.
- `build/web/index.pck.gz`: about 5.4 MB after export.
- `curl -I --compressed http://127.0.0.1:9000/index.pck`: `Content-Encoding: gzip`, `Content-Length: 5626184`, `Cache-Control: no-store`.
- `/tmp/cable-world-web-map/mobile-390x844-initial.png`, `/tmp/cable-world-web-map/mobile-390x844-after-drag.png` and `/tmp/cable-world-web-map/desktop-1280x800-initial.png` regenerated after the lake hierarchy pass.

Checks:

- `python3 -m unittest tests.test_map_panel_contract tests.test_export_payload_contract tests.test_android_export_contract`: 18 OK.
- `godot --headless --path . --import --quit`: no parse/import errors. Existing worktree warning and adb daemon warning remain.
- Web export rebuilt and served on `http://127.0.0.1:9000/`.
- `PLAYWRIGHT_PACKAGE=/tmp/cable-playwright/node_modules/playwright URL=http://127.0.0.1:9000/ node scripts/verify-web-map.mjs`: screenshots regenerated.

Self-audit: still around `6/10`. The exact lake layer now has better hierarchy, but this is not an `8/10` map yet. The next visible win should be a stronger terrain/glyph art pass plus geography audit for relief, city positions, islands and large water bodies.

## Iteration 2026-05-31 17:22

Implemented:

- Reworked the Alps from a generic mountain row into a composed Alpine massif layer.
- Added `ALPINE_MASSIF_SEGMENTS` with named segments:
  - `western_alps_massif`
  - `swiss_alps_massif`
  - `bavarian_tyrol_alps_massif`
  - `austrian_alps_massif`
- Each segment has an explicit geographic arc, a soft relief shadow and multiple overlapping Alpine glyph placements. This keeps the production direction as reusable glyph layers, not a monolithic generated map.
- Did not spend a new image-generation request for this pass; reused the existing Alpine glyph source assets and composed them more intentionally.
- Tightened city labels under landmark pictograms: label baseline moved from `4.0 * zoom` to `1.5 * zoom`.
- Changed pan drag to viewport-local deltas: mouse/touch panning now uses `event.relative` with `PAN_DRAG_SCALE := 1.0` instead of `screen_relative`, so drag speed should feel closer to 1:1 across desktop and mobile.

Evidence:

- `assets/map/germany_styled.png`: `1932x3072`, about 2.2 MB after the composed Alpine massif pass.
- Mobile screenshot `/tmp/cable-world-web-map/mobile-390x844-initial.png` now shows a continuous Alpine wall near München/Alpen instead of disconnected generic mountains.
- Mobile screenshot `/tmp/cable-world-web-map/mobile-390x844-after-drag.png` shows zoom capped at `150%` with the new pan behavior active.
- Desktop screenshot `/tmp/cable-world-web-map/desktop-1280x800-initial.png` regenerated after the same build.
- `curl -I --compressed http://127.0.0.1:9000/index.pck`: `Content-Encoding: gzip`, `Content-Length: 5916349`, `Cache-Control: no-store`.

Checks:

- `python3 -m unittest tests.test_map_panel_contract tests.test_export_payload_contract tests.test_android_export_contract`: 18 OK.
- `godot --headless --path . --import --quit`: no parse/import errors. Existing worktree warning and adb daemon warning remain.
- Web export rebuilt and served on `http://127.0.0.1:9000/`.
- `PLAYWRIGHT_PACKAGE=/tmp/cable-playwright/node_modules/playwright URL=http://127.0.0.1:9000/ node scripts/verify-web-map.mjs`: screenshots regenerated.

Self-audit: still not `8/10`; call it about `6/10` overall, with the Alpine area improved toward `6.5/10`. The Alps now read as a real massif, but the scale may be too dominant and needs geography/art audit against Switzerland/Austria/Italy before this can count as final.

## Iteration 2026-05-31 17:39

Implemented:

- Added a vendored atlas label font: `assets/fonts/LiberationSerif-BoldItalic.ttf`.
- Switched runtime map city labels to use the atlas font through `_map_label_font()` instead of the generic theme font.
- Switched baked terrain labels in `map_pipeline.compose_map` to the same serif italic font through `ImageFont.truetype`.
- Replaced ASCII terrain label text with proper umlauts: `Müritz`, `Rügen`.
- Removed runtime terrain label drawing from `map_layer` so labels no longer appear twice; terrain labels are now baked into the underlay, while city labels remain a runtime overlay above objects.
- Repositioned the `Harz` terrain label so it remains readable next to the Harz glyph/detail cluster.

Evidence:

- `assets/map/germany_styled.png`: `1932x3072`, about 2.26 MB after the atlas-label pass.
- Mobile screenshot `/tmp/cable-world-web-map/mobile-390x844-initial.png` shows city labels in the serif atlas style and no duplicated terrain labels.
- Desktop screenshot `/tmp/cable-world-web-map/desktop-1280x800-initial.png` shows `Harz`, `Müritz`, `Berlin`, `Dresden`, `Köln` and `Hamburg` in a more consistent map-label style.
- `curl -I --compressed http://127.0.0.1:9000/index.pck`: `Content-Encoding: gzip`, `Content-Length: 6159504`, `Cache-Control: no-store`.

Checks:

- `python3 -m unittest tests.test_map_panel_contract tests.test_export_payload_contract tests.test_android_export_contract`: 18 OK.
- `godot --headless --path . --import --quit`: no parse/import errors. Existing worktree warning and adb daemon warning remain.
- Web export rebuilt and served on `http://127.0.0.1:9000/`.
- `PLAYWRIGHT_PACKAGE=/tmp/cable-playwright/node_modules/playwright URL=http://127.0.0.1:9000/ node scripts/verify-web-map.mjs`: screenshots regenerated.

Self-audit: still around `6/10` overall. The labels now move toward the requested Middle-earth/atlas direction, but the map still needs stronger terrain art, geography audit and better cross-border density before it can be honestly called `8/10`.

## Iteration 2026-05-31 18:05

Implemented:

- Disabled finger pinch/magnify zoom. Touch gestures no longer change zoom; one-finger pan remains active, and `+/-` plus mouse wheel remain the controlled zoom inputs.
- Raised runtime zoom cap from `150%` to `200%`.
- Changed zoom controls from multiplicative scaling to fixed `25` percentage-point steps: `100 -> 125 -> 150`, and `100 -> 75 -> 50`.
- Applied pixel snapping to runtime map objects using the same principle as labels: transport markers, city landmark pictograms, landmark labels and marker sizes now round to whole pixels after pan/zoom calculations.
- Increased tiny atlas detail glyphs through `MIN_ATLAS_DETAIL_WIDTH = 54`, so small houses/chapels/windmills/ruins/watermills read as objects instead of specks.
- Removed the most distracting stripe layers from the current generated map: route overlay and overly straight procedural waterways are no longer rendered, and procedural field hatch/field patch strokes were replaced with quieter tufts/hill marks.
- Added first cross-border context pass for neighboring country texture and atlas labels: `Dänemark`, `Niederlande`, `Belgien`, `Luxemburg`, `Frankreich`, `Schweiz`, `Österreich`, `Tschechien`, `Polen`.

Evidence:

- `assets/map/germany_styled.png`: `1932x3072`, about `2.06 MB` after detail sizing and stripe removal.
- `curl -I --compressed http://127.0.0.1:9000/index.pck`: `Content-Encoding: gzip`, `Content-Length: 6015668`, `Cache-Control: no-store`.
- `/tmp/cable-world-web-map/mobile-390x844-initial.png` and `/tmp/cable-world-web-map/desktop-1280x800-initial.png` show the straight route/waterway stripes removed from the current underlay.
- Contract tests now explicitly forbid `_zoom_at(event.position, event.factor)`, pinch-distance zoom, and `1.0 / ZOOM_STEP`.
- Contract tests require `MAX_ZOOM := 2.0`, `ZOOM_STEP := 0.25`, `_zoom_by_delta`, marker pixel snapping, and `MIN_ATLAS_DETAIL_WIDTH = 54`; they also forbid rendering routes/waterways from `main()`.

Checks so far:

- `python3 -m unittest tests.test_map_panel_contract tests.test_export_payload_contract tests.test_android_export_contract`: 18 OK.
- `godot --headless --path . --import --quit`: no parse/import errors. Existing nested worktree warning and adb daemon warning remain.
- Web export rebuilt and served on `http://127.0.0.1:9000/`.
- `PLAYWRIGHT_PACKAGE=/tmp/cable-playwright/node_modules/playwright URL=http://127.0.0.1:9000/ node scripts/verify-web-map.mjs`: screenshots regenerated.

Self-audit: still around `6/10`. This iteration fixes control feel and visual noise, but the map is not yet `8/10`: terrain art, Europe continuity, relief accuracy and better object hierarchy still need a stronger art/geography pass.

## Iteration 2026-05-31 18:18

Implemented:

- Rebalanced runtime object hierarchy so interactive transport markers read above city landmarks.
- Raised transport marker visual range from `48..78` to `60..96`; cluster marker cap from `70` to `88`.
- Reduced city landmark pictogram range from `46..88` to `42..76`, keeping cities useful as orientation but less dominant than clickable objects.

Evidence to verify after export:

- Contract tests require the new marker constants and city landmark clamp.
- `/tmp/cable-world-web-map/mobile-390x844-after-marker-click.png` shows transport markers at `170%` reading clearly above the city landmark layer.
- `/tmp/cable-world-web-map/mobile-390x844-initial.png` and `/tmp/cable-world-web-map/desktop-1280x800-initial.png` regenerated after the marker hierarchy pass.
- `curl -I --compressed http://127.0.0.1:9000/index.pck`: `Content-Encoding: gzip`, `Content-Length: 6015655`, `Cache-Control: no-store`.

Checks:

- `python3 -m unittest tests.test_map_panel_contract tests.test_export_payload_contract tests.test_android_export_contract`: 18 OK.
- `godot --headless --path . --import --quit`: no parse/import errors. Existing nested worktree warning and adb daemon warning remain.
- Web export rebuilt and served on `http://127.0.0.1:9000/`.
- `PLAYWRIGHT_PACKAGE=/tmp/cable-playwright/node_modules/playwright URL=http://127.0.0.1:9000/ node scripts/verify-web-map.mjs`: screenshots regenerated.

Self-audit: still around `6/10`. This removes one hierarchy blocker, but it will only count toward `7/10+` if screenshot review confirms clickable objects are visibly primary without making the map cluttered.

## Iteration 2026-05-31 18:31

Implemented:

- Reintroduced atlas journey structure without returning to the previous technical stripe problem.
- Added explicit `ATLAS_ROUTE_SEGMENTS` with named coordinate trails:
  - `north_to_harz_trail`
  - `harz_to_berlin_trail`
  - `elbe_dresden_trail`
  - `rhine_to_south_trail`
  - `southern_alps_trail`
- Added `_draw_atlas_routes()` and `_draw_atlas_dotted_route()` as a separate renderer that uses only small dots, no continuous route line.
- Kept old `_draw_routes()` unused for now as historical code, but the main renderer calls only `_draw_atlas_routes()`.

Evidence:

- `assets/map/germany_styled.png`: `1932x3072`, about `2.07 MB` after atlas route dots.
- Full-map review shows subtle dotted trails instead of long blue/technical strips.
- `/tmp/cable-world-web-map/mobile-390x844-initial.png` shows the route dots as quiet atlas texture on the initial portrait view; they do not dominate Hamburg/Rostock/Berlin/München.
- `/tmp/cable-world-web-map/mobile-390x844-after-marker-click.png` confirms the same route layer stays behind transport objects at `170%`.
- `/tmp/cable-world-web-map/desktop-1280x800-initial.png` shows dotted coordinate trails crossing Germany without returning to continuous technical route lines.
- `curl -I --compressed http://127.0.0.1:9000/index.pck`: `Content-Encoding: gzip`, `Content-Length: 6024002`, `Cache-Control: no-store`.
- Contract tests require `ATLAS_ROUTE_SEGMENTS`, `_draw_atlas_routes()`, `_draw_atlas_dotted_route()`, and explicitly forbid `draw.line` inside the new atlas dotted route renderer.

Checks:

- `python3 -m unittest tests.test_map_panel_contract tests.test_export_payload_contract tests.test_android_export_contract`: 18 OK.
- `godot --headless --path . --import --quit`: no parse/import errors. Existing nested worktree warning and adb daemon warning remain.
- Web export rebuilt and served on `http://127.0.0.1:9000/`.
- `PLAYWRIGHT_PACKAGE=/tmp/cable-playwright/node_modules/playwright URL=http://127.0.0.1:9000/ node scripts/verify-web-map.mjs`: screenshots regenerated.

Self-audit: still around `6/10`. This restores some "journey map" structure needed for the reference direction and removes the old technical-line failure mode, but it does not solve the bigger art/geography blockers: stronger terrain glyphs, accurate Europe-scale relief, more readable non-random detail density, and final object hierarchy.

## Iteration 2026-05-31 18:55

Implemented:

- Added explicit `ATLAS_FOREST_MASSES` as a named glyph layer for real/plausible German forest regions instead of relying only on sparse procedural ground texture.
- Covered Lüneburger Heide, Mecklenburg lake forests, Spreewald/Lausitz, Teutoburg/Weser uplands, Sauerland/Rothaar, Eifel/Ardennes edge, Spessart/Odenwald, Thuringian Forest, Franconian/Swabian uplands and Upper Bavaria foothills.
- Raised `MIN_ATLAS_DETAIL_WIDTH` from `54` to `66`, so small houses/chapels/ruins/watermills are less likely to read as dust.
- Added contract coverage for the new forest mass layer and the higher atlas detail minimum.

Evidence:

- `assets/map/germany_styled.png`: `1932x3072`, about `2.35 MB` after the forest/detail density pass.
- `/tmp/cable-world-web-map/mobile-390x844-initial.png` shows more visible forests and villages while city landmarks and labels remain readable.
- `/tmp/cable-world-web-map/mobile-390x844-after-marker-click.png` shows transport markers still sit above the new forest/village texture at `170%`.
- `/tmp/cable-world-web-map/desktop-1280x800-initial.png` shows the map is less empty across central/northern Germany without reintroducing technical route stripes.
- `curl -I --compressed http://127.0.0.1:9000/index.pck`: `Content-Encoding: gzip`, `Content-Length: 6260903`, `Cache-Control: no-store`.

Checks:

- `python3 -m unittest tests.test_map_panel_contract tests.test_export_payload_contract tests.test_android_export_contract`: 18 OK.
- `godot --headless --path . --import --quit`: no parse/import errors. Existing nested worktree warning and adb daemon warning remain.
- Web export rebuilt and served on `http://127.0.0.1:9000/`; the server had to be restarted after the export returned an empty response.
- `PLAYWRIGHT_PACKAGE=/tmp/cable-playwright/node_modules/playwright URL=http://127.0.0.1:9000/ node scripts/verify-web-map.mjs`: screenshots regenerated.

Self-audit: about `6.5/10`, not `8/10`. This fixes part of the "boring/empty" failure mode, but some forest+village clusters are now visually heavy and still need a stronger art-directed glyph pass. The larger blockers remain relief accuracy, Europe-scale continuity and final marker/list polish.

## Iteration 2026-05-31 19:32

Implemented:

- Replaced generic cluster marker appearance with an atlas-style icon stack: clustered transport objects now render 2-3 real transport sprites with slight offsets, without count text, circles or a station badge.
- Added `_cluster_icon_ids()` so the stack uses distinct transport types where possible and falls back to `icon_station` only if needed.
- Cleared old cluster stack children when markers switch back to single-object style, preventing stale icons.
- Set explicit layer ordering: map content at `z_index = 10`, city label overlay at `20`, zoom controls at `30`.
- Passed marker reserved rects to the label overlay as well, so labels can remain above markers while still avoiding overlap where possible.
- Restored runtime city labels to the theme/default font after user feedback; the atlas serif font remains for terrain/map labels only.

Evidence:

- `/tmp/cable-world-web-map/mobile-390x844-initial.png` shows grouped transport objects as sprite stacks rather than UI count badges.
- `/tmp/cable-world-web-map/mobile-390x844-after-marker-click.png` shows individual transport markers at `170%` and labels still visible around the dense Magdeburg/Harz area.
- `/tmp/cable-world-web-map/desktop-1280x800-after-marker-click.png` shows clustered markers no longer look like external UI counters; city labels render above marker content.
- `/tmp/cable-world-web-map/mobile-390x844-initial.png` confirms city names are back on the previous sans/default font instead of the serif atlas font.
- `curl -I --compressed http://127.0.0.1:9000/index.pck`: `Content-Encoding: gzip`, `Content-Length: 6262069`, `Cache-Control: no-store`.

Checks:

- `python3 -m unittest tests.test_map_panel_contract tests.test_export_payload_contract tests.test_android_export_contract`: 18 OK.
- `godot --headless --path . --import --quit`: no parse/import errors. Existing nested worktree warning and adb daemon warning remain.
- Web export rebuilt and served on `http://127.0.0.1:9000/`; the server had to be restarted after export again because the old process returned an empty response.
- `PLAYWRIGHT_PACKAGE=/tmp/cable-playwright/node_modules/playwright URL=http://127.0.0.1:9000/ node scripts/verify-web-map.mjs`: screenshots regenerated.

Self-audit: still about `6.5/10`. The cluster layer is less UI-like, but marker composition remains dense in cities with many objects and needs a stronger final interaction/art pass before the map can honestly reach `8/10`.

## Iteration 2026-05-31 19:45

Implemented:

- Added `audit_geography_layers()` to `map_pipeline.compose_map`.
- The audit checks manual terrain/water/detail/forest data instead of relying only on screenshot review:
  - relief polygons must be valid;
  - `northern_lowlands` must not define mountain glyphs, ridge bands, massif segments or decorative mountains;
  - mountain glyph anchors must stay inside their named relief region with a small tolerance;
  - Alpine ridge/massif points must stay near the Alps region;
  - named water bodies must have real outline polygons and stay inside map bounds;
  - atlas details cannot accidentally use relief glyphs;
  - forest mass clusters must use forest glyphs and remain readable size.
- Added `tests/test_map_geography_audit.py`; it skips under plain `python3` if map pipeline dependencies are absent, and runs fully under `uv`.
- Added contract coverage so the audit function and its key failure modes stay in the pipeline.

Evidence:

- `python3 -m unittest tests.test_map_panel_contract tests.test_export_payload_contract tests.test_android_export_contract tests.test_map_geography_audit`: 19 tests, OK, 1 skipped because plain Python lacks map pipeline dependencies.
- `uv run python -m unittest tests.test_map_geography_audit tests.test_map_panel_contract tests.test_export_payload_contract tests.test_android_export_contract`: 19 tests OK, including the real geography audit.

Self-audit: still about `6.5/10`. This does not improve the pixels directly, but it removes a major process risk: the next terrain/lake/Europe edits now have automated guardrails against putting mountains/water/details in impossible places. It supports future `8/10+`, but the visible art pass is still required.

## Iteration 2026-05-31 20:53

Implemented:

- Raised `MIN_ATLAS_DETAIL_WIDTH` from `66` to `78`, so small atlas detail glyphs read more like intentional places and less like pixel dust at mobile zoom.
- Split named water rendering into `_draw_named_water_bodies()` and kept the straight procedural river/blue-line layer disabled after screenshot review.
- Softened named water alpha/shore/highlight values so lakes sit more naturally in the atlas underlay and do not compete with clickable transport/city markers.
- Updated contracts for the new water/detail readability pass.

Evidence:

- `assets/map/germany_styled.png`: `1932x3072`, about `2.37 MB`.
- First attempted river pass was rejected during self-review because it produced long straight blue strips; the final exported pass does not call `_draw_waterways()` from `main()`.
- `/tmp/cable-world-web-map/mobile-390x844-initial.png` shows larger atlas details, no circular city-marker backgrounds and runtime city labels still on the default font.
- `/tmp/cable-world-web-map/desktop-1280x800-initial.png` shows the new underlay in the exported web build.
- `curl -I --compressed http://127.0.0.1:9000/index.pck`: `Content-Encoding: gzip`, `Content-Length: 6281373`, `Cache-Control: no-store`.

Checks:

- `python3 -m unittest tests.test_map_panel_contract tests.test_export_payload_contract tests.test_android_export_contract tests.test_map_geography_audit`: 19 tests OK, 1 skipped under plain Python.
- `uv run python -m unittest tests.test_map_geography_audit tests.test_map_panel_contract tests.test_export_payload_contract tests.test_android_export_contract`: 19 tests OK.
- `godot --headless --path . --import --quit`: import completed. Existing nested worktree warning and adb daemon warning remain.
- Web export rebuilt, gzip files regenerated and `scripts/serve-web.sh --no-export` restarted on `http://127.0.0.1:9000/`.
- `PLAYWRIGHT_PACKAGE=/tmp/cable-playwright/node_modules/playwright URL=http://127.0.0.1:9000/ node scripts/verify-web-map.mjs`: screenshots regenerated.

Self-audit: still about `6.5/10`, not `8/10`. The detail readability is better and the failed river-strip direction was avoided, but several named lakes still look too round/blobby on mobile. The next visible pass should improve lake silhouettes and continue terrain/mountain art calibration rather than claiming completion.

## Backlog Triage 2026-05-31 21:05

Created GitHub issues from the latest user feedback so the work follows issues instead of relying on chat memory:

- `#66` Map texture: add reusable ground and water base textures.
- `#67` Map clutter: remove or enlarge tiny houses and tiny trees. The user clarified that "details" means small houses/trees specifically, not every atlas detail.
- `#68` Map terrain: make German Alps visible and correctly placed.
- `#69` Map terrain sprites: create separate glyph/sprite layer per mountain massif.
- `#70` Map city coordinates: fix Rostock landmark placement on land.

Current priority order: fix visible clutter from tiny houses/trees, add base land/water texture, then recalibrate Rostock/Alps/massif sprite layers under the existing geography-audit process.

## Iteration 2026-05-31 21:12

Implemented:

- Added reproducible masked base textures in `map_pipeline.compose_map`:
  - `_draw_base_land_texture()` adds subtle grain and atlas-style land arcs through `land_mask`;
  - `_draw_base_water_texture()` adds subtle wave texture through `water_mask`.
- Reduced tiny decorative clutter from issue `#67`:
  - `DEFAULT_ATLAS_DETAIL_KINDS` now renders only larger landmark categories by default: bridges, castles, lighthouses, ports, ships and towers;
  - tiny village/chapel/ruins/watermill/windmill glyphs remain available as assets/data but are skipped by the default underlay;
  - removed the extra scattered small tree-cluster pass from `_draw_terrain()`, leaving named forest masses and larger relief/forest glyphs.
- Rebuilt `assets/map/germany_styled.png` from the reproducible pipeline.

Evidence:

- `/tmp/cable-world-web-map/mobile-390x844-initial.png` shows fewer tiny houses/trees and a less flat land/water base.
- `/tmp/cable-world-web-map/desktop-1280x800-initial.png` shows the texture pass without the earlier straight river-line artifact.
- `curl -I --compressed http://127.0.0.1:9000/index.pck`: `Content-Encoding: gzip`, `Content-Length: 6360740`, `Cache-Control: no-store`.

Checks:

- `python3 -m unittest tests.test_map_panel_contract tests.test_export_payload_contract tests.test_android_export_contract tests.test_map_geography_audit`: 19 tests OK, 1 skipped under plain Python.
- `uv run python -m unittest tests.test_map_geography_audit tests.test_map_panel_contract tests.test_export_payload_contract tests.test_android_export_contract`: 19 tests OK.
- `godot --headless --path . --import --quit`: import completed. Existing nested worktree warning and adb daemon warning remain.
- Web export rebuilt and served on `http://127.0.0.1:9000/`; Playwright screenshots regenerated.

Self-audit: about `6.7/10`, still not `8/10`. This is a real readability improvement, but open issues remain: Rostock is visually too far into the water, German Alps need recalibration, and separate massif sprite layers are still required for the target direction.

## Iteration 2026-05-31 21:17

Implemented:

- Added data-driven city landmark icon offsets in `scripts/map_panel.gd`.
- Applied `icon_offset: Vector2(0.0, 23.0)` to Rostock so the pictogram sits closer to the land/harbor coast instead of floating in the Baltic Sea.
- Kept the real coordinate and map projection unchanged; this is a marker drawing offset only, so it does not reintroduce viewport clamping or marker drift.

Evidence:

- `/tmp/cable-world-web-map/mobile-390x844-initial.png` shows Rostock no longer floating in open water.
- `curl -I --compressed http://127.0.0.1:9000/index.pck`: `Content-Encoding: gzip`, `Content-Length: 6360906`, `Cache-Control: no-store`.

Checks:

- `python3 -m unittest tests.test_map_panel_contract tests.test_export_payload_contract tests.test_android_export_contract tests.test_map_geography_audit`: 19 tests OK, 1 skipped under plain Python.
- `uv run python -m unittest tests.test_map_geography_audit tests.test_map_panel_contract tests.test_export_payload_contract tests.test_android_export_contract`: 19 tests OK.
- Web export rebuilt and served on `http://127.0.0.1:9000/`; Playwright screenshots regenerated.

Self-audit: this addresses `#70` first pass. The broader map remains below `8/10`; next high-impact work is German Alps visibility and separate massif sprite layers (`#68`, `#69`).

## Iteration 2026-05-31 19:25

Implemented:

- Added a separate `german_alpine_edge_massif` segment to the map composition pipeline so the German side of the Alps is visible around Bavaria instead of only continuing south of the border.
- Increased Rostock's runtime city landmark offset from `Vector2(0.0, 23.0)` to `Vector2(0.0, 52.0)` after user feedback that it still looked like it was hanging over the sea.
- Kept Rostock's real coordinates unchanged; this remains a drawing offset for the icon, not a fake city coordinate.

Evidence:

- `assets/map/germany_styled.png` regenerated with the German Alpine edge visible in the south.
- `/tmp/cable-world-web-map/mobile-390x844-initial.png` shows Rostock's pictogram on land and the Alps visible near München.
- `curl -I --compressed http://127.0.0.1:9000/index.pck`: `Content-Encoding: gzip`, `Content-Length: 6439694`, `Cache-Control: no-store`.

Checks:

- `python3 -m unittest tests.test_map_panel_contract tests.test_export_payload_contract tests.test_android_export_contract tests.test_map_geography_audit`: 19 tests OK, 1 skipped under plain Python.
- `uv run python -m unittest tests.test_map_geography_audit tests.test_map_panel_contract tests.test_export_payload_contract tests.test_android_export_contract`: 19 tests OK.
- Web export rebuilt, gzip files regenerated, server restarted on `http://127.0.0.1:9000/`, and Playwright screenshots regenerated.

Self-audit: about `6.8/10`, still not `8/10`. This fixes two concrete geography/readability defects, but `#69` is still the important architectural/art task: each mountain massif needs its own reusable glyph/sprite layer, with stronger terrain accuracy and less ad hoc composition.

## Iteration 2026-05-31 19:37

Implemented:

- Added a non-render geography audit before screenshot review:
  - `german_alpine_edge_massif` now declares `required_country_overlap: "Germany"` and the audit verifies that it really intersects the Germany geometry.
  - `CITY_LANDMARK_PLACEMENT_AUDITS` verifies Rostock's runtime icon placement by sampling the projected top/center/bottom icon points against the Germany polygon.
- Started `#69` with a first architecture pass:
  - each Alpine massif segment is rendered through `_render_alpine_massif_segment_layer()`;
  - source layers are cropped and written to `assets/map/massifs/*.png`;
  - the final underlay composites those same per-massif layers.
- Added `assets/map/massifs/.gdignore` and `assets/map/massifs/**` export excludes so source layers do not inflate Web/Android payloads.

Evidence:

- Generated source layers:
  - `western_alps_massif.png`
  - `swiss_alps_massif.png`
  - `bavarian_tyrol_alps_massif.png`
  - `german_alpine_edge_massif.png`
  - `austrian_alps_massif.png`
- `assets/map/germany_styled.png` regenerated from the per-massif composition path.
- `curl -I --compressed http://127.0.0.1:9000/index.pck`: `Content-Encoding: gzip`, `Content-Length: 6439692`, `Cache-Control: no-store`.
- `/tmp/cable-world-web-map/mobile-390x844-initial.png` regenerated from the current Web build.

Checks:

- `python3 -m unittest tests.test_map_panel_contract tests.test_export_payload_contract tests.test_android_export_contract tests.test_map_geography_audit`: 19 tests OK, 1 skipped under plain Python.
- `uv run python -m unittest tests.test_map_geography_audit tests.test_map_panel_contract tests.test_export_payload_contract tests.test_android_export_contract`: 19 tests OK.
- `uv run python -m map_pipeline.compose_map`: regenerated map and source massif layers.
- Web export rebuilt, gzip files regenerated, server restarted on `http://127.0.0.1:9000/`, and Playwright screenshots regenerated.

Self-audit: still about `6.8/10`. This improves process and architecture, not enough visual quality by itself. The next quality step is to replace the current repeated Alpine glyphs with better per-massif art/placement and continue lake/forest/city density checks.

## Iteration 2026-05-31 19:45

Implemented:

- Added reproducible metadata for massif source layers:
  - each `assets/map/massifs/*.png` now has a matching JSON sidecar;
  - `assets/map/massifs/manifest.json` records map bounds, map size, render scale and all massif layers.
- Metadata includes source image name, render bbox, map bbox, geographic bounds, arc points, shadow polygon, glyph anchors and required country overlap.
- Added `audit_massif_source_manifest()` so massif source layers can be checked without rendering screenshots:
  - all expected Alpine massif ids must exist in the manifest;
  - each source PNG must exist, be RGBA, match the metadata size and be non-blank;
  - geographic bounds must be non-degenerate.

Evidence:

- Manifest generated at `assets/map/massifs/manifest.json`.
- Sidecars generated for all current Alpine source layers:
  - `western_alps_massif.json`
  - `swiss_alps_massif.json`
  - `bavarian_tyrol_alps_massif.json`
  - `german_alpine_edge_massif.json`
  - `austrian_alps_massif.json`

Checks:

- `uv run python -m map_pipeline.compose_map`: regenerated source massif PNGs and metadata.
- `uv run python -m unittest tests.test_map_geography_audit tests.test_map_panel_contract tests.test_export_payload_contract`: 15 tests OK.
- `python3 -m unittest tests.test_map_panel_contract tests.test_export_payload_contract tests.test_android_export_contract tests.test_map_geography_audit`: 20 tests OK, 2 skipped under plain Python where geo dependencies are unavailable.

Self-audit: still about `6.8/10`. This does not improve the screenshot by itself, but it removes a major process weakness: terrain sprites now carry enough placement metadata to audit and replace them deterministically. Next visual pass should use this to improve the Alpine/Harz/forest art rather than editing a monolithic map.

## Iteration 2026-05-31 19:55

Implemented:

- Extended the source-layer pipeline beyond Alpine segments:
  - each named relief region now renders through `_render_relief_region_decor_layer()`;
  - the composed map still uses the same layer output, so source assets and final map do not diverge.
- Added per-region source PNG/JSON layers for:
  - `alps`
  - `black_forest`
  - `bavarian_forest`
  - `harz`
  - `erzgebirge`
  - `saxon_switzerland`
  - `eifel_hunsrueck`
- Kept `northern_lowlands` out of the source-layer export on purpose; it is not a mountain/massif layer and must not become a false terrain asset.
- Expanded source metadata with `source_type`, region polygon, trees, ridge bands, massif segment references, glyph anchors and cross-border `extends_to` data.

Evidence:

- `assets/map/massifs/manifest.json` now contains 12 layers: 5 Alpine massif segments plus 7 named relief regions.
- `assets/map/massifs/harz.png` is a standalone transparent source layer for Harz.
- `/tmp/cable-world-web-map/mobile-390x844-initial.png` and `/tmp/cable-world-web-map/desktop-1280x800-initial.png` regenerated from the current Web build.
- `curl -I --compressed http://127.0.0.1:9000/index.pck`: `Content-Encoding: gzip`, `Content-Length: 6439692`, `Cache-Control: no-store`.

Checks:

- `uv run python -m map_pipeline.compose_map`: regenerated final map and all terrain source layers.
- `uv run python -m unittest tests.test_map_geography_audit tests.test_map_panel_contract tests.test_export_payload_contract`: 15 tests OK.
- `python3 -m unittest tests.test_map_panel_contract tests.test_export_payload_contract tests.test_android_export_contract tests.test_map_geography_audit`: 20 tests OK, 2 skipped under plain Python where geo dependencies are unavailable.
- Godot import/export completed, with the known nested worktree and adb warnings only.
- Web server restarted on `http://127.0.0.1:9000/`; Playwright screenshots regenerated.

Self-audit: still about `6.8/10`. The pipeline is now much closer to the requested component-based direction, but visual quality is unchanged. The next user-visible improvement should be replacing weak region glyph art/placement, especially making Alps and Harz look less like repeated generic sprites.

## Iteration 2026-05-31 20:05

Implemented:

- Removed the duplicate generic `alps_range_*` mountain-glyph row from the full `alps` relief region.
- The Alpine layer now renders through ridge bands plus named massif source layers instead of drawing a second repeated strip of generic mountains over the same area.
- Regenerated `assets/map/germany_styled.png`, `assets/map/massifs/alps.png`, `assets/map/massifs/alps.json` and `assets/map/massifs/manifest.json`.
- Updated the contract test so the full `alps` region is expected to have `mountain_glyphs: []`.

Checks:

- `uv run python -m map_pipeline.compose_map`: regenerated final map and source layers.
- `uv run python -m unittest tests.test_map_geography_audit tests.test_map_panel_contract tests.test_export_payload_contract`: 15 tests OK.
- `python3 -m unittest tests.test_map_panel_contract tests.test_export_payload_contract tests.test_android_export_contract tests.test_map_geography_audit`: 20 tests OK, 2 skipped under plain Python where geo dependencies are unavailable.
- `curl -I --compressed http://127.0.0.1:9000/index.pck`: `Content-Encoding: gzip`, `Content-Length: 6360156`, `Cache-Control: no-store`.
- Playwright screenshots regenerated:
  - `/tmp/cable-world-web-map/mobile-390x844-initial.png`
  - `/tmp/cable-world-web-map/desktop-1280x800-initial.png`

Non-render verification notes:

- We can audit coordinates, region bounds, layer metadata, PNG sizes/non-blank state, expected draw calls and payload headers without screenshots.
- We still need screenshots/manual review for final quality signals: contrast, clutter, whether the relief reads naturally, whether marker hierarchy is clear, and whether the map feels close to the reference style.

Self-audit: still about `6.8/10`, not `8/10`. The screenshot is cleaner because Alps are no longer double-drawn, but the Alpine art itself is still too generic and needs a better per-massif visual pass.
