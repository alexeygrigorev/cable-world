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
