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
