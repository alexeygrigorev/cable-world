# Map generation handoff

Дата: 2026-05-31.

Цель текущей итерации: стартовый экран приложения должен быть fullscreen-картой. На карте должны быть правильно расположенные интерактивные объекты из каталога. Список допустим только как маленькая кнопка-переключатель поверх карты.

Quality gate: перед тем как считать карту готовой, оценивать результат по `docs/map-quality-rubric.md`. Текущий плохой baseline считается примерно 3/10, а не готовым результатом.

## Current TODO

- [x] Найден текущий пайплайн генерации карты в `worktrees/issue-54-map-pipeline/map_pipeline/`.
- [x] Старый `germany_styled.png` признан плохим: крупные AI-спрайты механически разбросаны поверх GIS-подложки, масштаб и композиция не работают.
- [x] `map_pipeline/compose_map.py` переписан на процедурную подложку: Natural Earth shape, мягкие природные зоны, маршруты, без встроенных маркеров.
- [x] Сгенерирован единый sprite sheet иконок за один image-generation вызов.
- [x] Разрезать sprite sheet на прозрачные отдельные иконки.
- [x] Подключить иконки в `scripts/map_panel.gd` вместо текстовых маркеров.
- [x] Довести `scripts/main_screen.gd` и `scenes/Main.tscn` до fullscreen-карты без постоянного заголовка, навигации, карточки и списка.
- [x] Проверить координаты маркеров на fullscreen-карте в Godot.
- [x] Запустить headless/контрактные тесты и поправить ожидания тестов под новый map-first UX.
- [x] Удалить runtime-зависимость от исходного sprite sheet: в `assets/sprites` остаются только финальные иконки.
- [x] Защитить старый `map_pipeline/generate_assets.py` от случайной генерации отдельных ассетов.
- [x] Проверить mobile screenshot после visual-pass.
- [ ] Проверить desktop/landscape viewport отдельным harness-ом, потому что Godot movie maker сейчас пишет проектный 390x844 viewport.
- [x] Исправить растяжение карты: подложка сохраняет Mercator aspect ratio и рисуется aspect-fill без деформации.
- [x] Починить pan/drag/click на уровне MapPanel: карта двигается в координатах map rect, drag по маркеру двигает карту, click по маркеру остается.
- [x] Довести visual direction до более близкого reference target: сгенерирована цельная RPG-atlas underlay с крупными горами, плотными лесами, городами и маршрутами.
- [x] Проверить interaction в browser/web после rebuild: pan, marker click, gzip.
- [x] Добавить browser verification script `scripts/verify-web-map.mjs`.
- [ ] User review 2026-05-31: усилить контраст карты и читаемость маркеров; прежняя оценка 10/10 отменена.
- [ ] Добавить ориентиры Berlin, Hamburg, Rostock как city markers, даже если там нет отдельного объекта.
- [ ] Сделать zoom controls видимыми поверх fullscreen-карты и ограничить zoom-out.
- [ ] Описать стратегию city clusters для нескольких канаток внутри города.

## Files touched so far

- `map_pipeline/compose_map.py`
  - заменен ручной список placements AI-спрайтов на воспроизводимый procedural renderer;
  - output остается `assets/map/germany_styled.png`;
  - карта теперь является чистой underlay-подложкой без маркеров и подписей, потому что интерактивные объекты рисует Godot.
  - renderer использует `ne_50m_admin_0_countries`, если dataset уже скачан; fallback остается `ne_110m_admin_0_countries`.
  - рельеф описан именованными слоями `RELIEF_REGIONS`: `alps`, `black_forest`, `harz`, `erzgebirge`, `bavarian_forest`, `eifel_hunsrueck`, `northern_lowlands`.
  - mountain glyphs являются стилизованными символами типа рельефа, а не портретами конкретных гор. Координаты и полигон слоя решают, где символ допустим; визуальный стиль glyph решает, как выглядит массив.
  - для `northern_lowlands` список `mountains` должен оставаться пустым: это полигональное правило для North German Plain, а не общее правило "на севере нет гор". Для Норвегии/Швеции северные mountain layers будут отдельными слоями с собственными glyphs.
- `map_pipeline/adapt_generated_underlay.py`
  - повторяемо адаптирует один generated RPG map PNG в runtime asset `assets/map/germany_styled.png`;
  - crop/resize сохраняет target aspect `1568x2048`, затем quantize-компрессия оставляет карту пригодной для Web.
- `assets/map/germany_styled.png`
  - текущая runtime-подложка собрана из generated source:
    ```bash
    uv run python -m map_pipeline.adapt_generated_underlay \
      --source /home/alexey/.codex/generated_images/019e7af1-437a-70f1-9164-d2f7b34a9c81/ig_0715a97cc1e1e04e016a1bdfd731b48191914ea24c0858fd77.png \
      --out assets/map/germany_styled.png
    ```
- `scripts/map_panel.gd`
  - начата переделка в fullscreen-режим: прозрачная panel style, скрыт toolbar, карта занимает всю доступную высоту.
  - маркеры центрируются по координате объекта;
  - иконка выбирается прямым mapping `transport_type_id -> icon_id`, без `contains()` по названию или описанию.
  - близкие объекты расходятся малым локальным cluster-offset вокруг координаты, не уезжая в произвольную сетку.
- `scripts/main_screen.gd`
  - начата переделка map-first chrome: на карте скрываются заголовок, subtitle, navigation area, selected label; создается маленькая кнопка `MapListToggle`.
  - убраны layout warnings от ручной установки size/position anchored `ContentScroll`.
  - убран автоселект первого объекта на старте, чтобы первый экран был нейтральной картой без selection ring.
- `map_pipeline/slice_transport_icons.py`
  - добавлен повторяемый slicer для 4x2 icon sheet;
  - нормализует каждую иконку в прозрачный PNG 256x256.

## Image generation workflow

Для иконок объектов использовать один sprite sheet вместо отдельных генераций. Это дешевле и дает единый стиль.

Использованный режим: built-in `image_gen` tool через skill `imagegen`.

Исходный сгенерированный файл:

```text
/home/alexey/.codex/generated_images/019e7af1-437a-70f1-9164-d2f7b34a9c81/ig_0715a97cc1e1e04e016a1be7b8dfc0819199f45d3987678a35.png
```

Prompt:

```text
Use case: stylized-concept
Asset type: sprite sheet for a Godot RPG-atlas transport map UI
Primary request: Create one consistent 4x2 sprite sheet of eight small transport landmark icons that look native to a 16-bit RPG pixel journey atlas map of Germany. These icons will be overlaid on a detailed pixel map with mountains, forests, rivers, towns, and dotted routes.
Canvas/layout: square image, 4 columns x 2 rows, each cell has one centered icon with generous padding. No text, no labels, no numbers, no borders between cells.
Icons in order, left to right, top row then bottom row: aerial cable car gondola; funicular rail car; cog railway mountain train; suspended monorail car; chairlift; vertical outdoor elevator/lift tower; aerial tramway cabin; generic cable transport station.
Style: polished 16-bit RPG pixel-art atlas landmark icons, isometric 2.5D, warm European adventure-map palette, crisp dark outline, tiny hand-painted pixel texture, readable at 40px, consistent camera angle and lighting, integrated with a game map rather than flat app icons. Each icon should feel like a miniature place/vehicle marker from the same world as a fantasy travel map.
Background: perfectly flat solid #ff00ff chroma-key background for background removal. The background must be one uniform color with no shadows, gradients, texture, reflections, floor plane, or lighting variation. Do not use #ff00ff anywhere in the icons.
Avoid: text, watermark, photorealism, modern flat vector UI, mixed styles, oversized shadows, cropped icons, red selection rings, map background behind the icons.
```

Planned post-processing:

1. Keep the original generated sheet outside runtime assets. The current source is:
   ```text
   /home/alexey/.codex/generated_images/019e7af1-437a-70f1-9164-d2f7b34a9c81/ig_0715a97cc1e1e04e016a1be7b8dfc0819199f45d3987678a35.png
   ```
2. Remove the flat magenta chroma key to alpha:
   ```bash
   mkdir -p tmp/map-icon-source
   uv run python "${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/scripts/remove_chroma_key.py" \
     --input /home/alexey/.codex/generated_images/019e7af1-437a-70f1-9164-d2f7b34a9c81/ig_0715a97cc1e1e04e016a1be7b8dfc0819199f45d3987678a35.png \
     --out tmp/map-icon-source/transport_icon_sheet.png \
     --auto-key border \
     --soft-matte \
     --transparent-threshold 12 \
     --opaque-threshold 220 \
     --despill
   ```
3. Slice the transparent 4x2 sheet into 8 icons:
   ```bash
   uv run python -m map_pipeline.slice_transport_icons \
     --sheet tmp/map-icon-source/transport_icon_sheet.png \
     --out-dir assets/sprites
   ```

   Output files:
   - `icon_cable_gondola.png`
   - `icon_funicular.png`
   - `icon_cog_railway.png`
   - `icon_suspended_monorail.png`
   - `icon_chairlift.png`
   - `icon_elevator.png`
   - `icon_aerial_tram.png`
   - `icon_station.png`
4. Add `.import` files by opening/importing the project in Godot if needed.

Runtime note: do not keep `transport_icon_sheet*.png` in `assets/sprites`. Godot only needs the final icon PNGs, which keeps import/load work smaller.

Runtime visibility pass:

```bash
uv run python -m map_pipeline.outline_sprites \
  --source-dir assets/sprites \
  --out-dir assets/sprites/outlined \
  --prefix icon_ \
  --radius 3 \
  --color '#23170de8'
```

The UI loads `assets/sprites/outlined/icon_*.png`. These variants add only a natural dark pixel outline around the sprite alpha; they do not add circles, plaques, pins, or map-colored backgrounds.

## City landmark generation workflow

User feedback 2026-05-31: карта должна читаться через узнаваемые городские символы, а не только через кружки/счетчики. Для этого сгенерирован один общий 8x8 sprite sheet городских landmark-пиктограмм, затем все 64 иконки разрезаны на будущее.

Generated source:

```text
/home/alexey/.codex/generated_images/019e7af1-437a-70f1-9164-d2f7b34a9c81/ig_0485449e48f76641016a1bfd703ddc819192289bd37d2762fd.png
```

Prompt:

```text
Use case: stylized-concept
Asset type: 1024x1024 sprite sheet for a Godot 16-bit RPG atlas map UI
Primary request: Create one consistent sprite sheet of small city landmark pictograms for a European cableways/funiculars map. The icons must feel like native landmarks on a hand-painted 16-bit adventure atlas, not modern app icons.
Canvas/layout: square 1024x1024 image, 8 columns x 8 rows, one centered icon per cell with generous padding. No text, no labels, no numbers, no grid lines, no borders between cells.
Icons in order, left to right, top row then next rows:
Berlin TV Tower; Hamburg harbor warehouse and crane; Rostock Hanseatic brick gate; Munich Frauenkirche twin towers; Cologne Cathedral; Frankfurt skyline tower; Stuttgart hill tower/TV tower; Dresden church dome;
Heidelberg castle; Düsseldorf Rhine tower; Dortmund industrial tower; Wuppertal suspended railway landmark; Baden-Baden spa pavilion; Koblenz fortress; Garmisch/Zugspitze alpine peak; Harz mountain forest tower;
Paris Eiffel Tower; London Big Ben/Westminster tower; Madrid Puerta de Alcalá; Barcelona Sagrada Familia; Rome Colosseum; Milan Duomo; Venice canal bridge; Amsterdam canal houses;
Brussels Grand Place guild house; Prague castle tower; Vienna cathedral; Budapest parliament dome; Warsaw palace tower; Krakow cloth hall tower; Copenhagen Nyhavn houses; Stockholm city hall tower;
Oslo opera roof; Helsinki cathedral dome; Tallinn old town tower; Riga old town spire; Vilnius cathedral bell tower; Minsk gates towers; Kyiv golden domes; Lviv old town tower;
Istanbul Galata tower/dome; Ankara citadel; Lisbon Belém tower; Porto bridge; Athens Parthenon; Sofia cathedral dome; Bucharest parliament/palace; Belgrade fortress;
Zagreb cathedral; Ljubljana castle hill; Bratislava castle; Sarajevo old bridge; Skopje stone bridge; Tirana square tower; Reykjavik church; Dublin castle tower;
Zurich church towers; Geneva fountain; Luxembourg fortress; Monaco casino facade; Andorra mountain church; San Marino tower; Valletta fortified gate; Strasbourg cathedral.
Style: polished pixel-art / painterly-pixel hybrid, isometric 2.5D atlas landmark miniatures, warm European adventure-map palette, crisp dark outline, readable at 28-40px, consistent camera angle and lighting. Each icon should be a small symbolic landmark silhouette with a little depth, designed to sit on a detailed map. Make them charming but not childish.
Background: perfectly flat solid #ff00ff chroma-key background for background removal. The background must be one uniform color with no shadows, gradients, texture, reflections, floor plane, or lighting variation. Do not use #ff00ff anywhere in the icons.
Avoid: text, letters, city names, flags, watermark, photorealism, modern flat vector UI, mixed styles, large drop shadows, cropped icons, map background behind icons, decorative frames.
```

Post-processing:

```bash
mkdir -p tmp/city-landmark-source
cp /home/alexey/.codex/generated_images/019e7af1-437a-70f1-9164-d2f7b34a9c81/ig_0485449e48f76641016a1bfd703ddc819192289bd37d2762fd.png \
  tmp/city-landmark-source/city_landmark_sheet_source.png
uv run python "${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/scripts/remove_chroma_key.py" \
  --input tmp/city-landmark-source/city_landmark_sheet_source.png \
  --out tmp/city-landmark-source/city_landmark_sheet_alpha.png \
  --auto-key border \
  --soft-matte \
  --transparent-threshold 12 \
  --opaque-threshold 220 \
  --despill
uv run python -m map_pipeline.slice_city_landmarks \
  --sheet tmp/city-landmark-source/city_landmark_sheet_alpha.png \
  --out-dir assets/sprites/city_landmarks
godot --headless --path . --import --quit
```

Runtime note: keep only sliced `city_*.png` files under `assets/sprites/city_landmarks/`. Source sheets belong under `tmp/` or `$CODEX_HOME/generated_images/`.

City icon visibility pass:

```bash
uv run python -m map_pipeline.outline_sprites \
  --source-dir assets/sprites/city_landmarks \
  --out-dir assets/sprites/city_landmarks/outlined \
  --prefix city_ \
  --radius 2 \
  --color '#25180fe0'
```

The app loads `assets/sprites/city_landmarks/outlined/city_*.png`. Major city landmarks remain visible at the default zoom. Smaller town labels are intentionally hidden until zoom `1.20` to avoid the “too busy” failure mode.

## Multi-symbol city cluster workflow

User feedback 2026-06-01: one-symbol city pictograms make city weight inconsistent. Berlin with only the TV tower reads smaller than München with a broader gate/building shape. The next city pass must use small landmark clusters: 2-4 recognizable city elements per icon, balanced to similar visual mass.

Start with the first 8 high-impact cities before replacing the full 64-icon set:

- Berlin: Fernsehturm, Brandenburger Tor, Reichstag dome or compact skyline mass.
- Hamburg: Speicherstadt warehouse, harbor crane, church spire or ship.
- Rostock: Hanseatic brick gate, harbor/ship, church spire.
- München: Frauenkirche towers, Rathaus/Marienplatz or city gate element.
- Köln: cathedral, Rhine bridge or river element.
- Frankfurt: skyline cluster, Römer/old town element.
- Stuttgart: Fernsehturm, Schlossplatz/industrial hill form.
- Dresden: Frauenkirche dome, Elbe bridge, old town silhouette.

Source quality rule: user zoom `200%` is our source-quality target. Generate cluster sheets with enough resolution that the `200%` in-app view still looks like the native asset, not a magnified low-res sprite. The first cluster sheet uses 4 columns x 2 rows at `2048x1024`, then slices each city to a `512x512` transparent source icon.

First generated source:

```text
/home/alexey/.codex/generated_images/019e7af1-437a-70f1-9164-d2f7b34a9c81/ig_0a51518699bf0fba016a1d5706b5288191b554444218cf4757.png
```

Current review tab:

```text
http://127.0.0.1:9010/ -> city_cluster_glyphs
```

Important slicer behavior: `map_pipeline.slice_city_cluster_landmarks` removes tiny edge-connected alpha islands before fitting each icon. This is required because generated sheets can place small fragments of the neighboring cell near cell boundaries.

Prompt:

```text
Use case: stylized-concept
Asset type: 2048x1024 sprite sheet for a Godot 16-bit RPG atlas map UI
Primary request: Create one consistent sprite sheet of multi-symbol city landmark cluster pictograms for a European cableways/funiculars map. Each icon must be a compact cluster of 2-4 recognizable city elements, balanced so each city has similar visual weight. The icons must feel like native landmarks on a hand-painted 16-bit adventure atlas, not modern app icons.
Canvas/layout: 2048x1024 image, 4 columns x 2 rows, one centered city cluster per cell with generous padding. No text, no labels, no numbers, no grid lines, no borders between cells.
Icons in order, left to right, top row then bottom row:
Berlin cluster with Fernsehturm, Brandenburg Gate, and Reichstag dome/skyline mass;
Hamburg cluster with Speicherstadt warehouse, harbor crane, church spire/ship;
Rostock cluster with Hanseatic brick gate, harbor ship, church spire;
Munich cluster with Frauenkirche twin towers, Rathaus/Marienplatz or city gate;
Cologne cluster with Cologne Cathedral, Rhine bridge/river element;
Frankfurt cluster with skyline towers and Römer/old town element;
Stuttgart cluster with TV tower, Schlossplatz/industrial hill form;
Dresden cluster with Frauenkirche dome, Elbe bridge, old town silhouette.
Style: polished pixel-art / painterly-pixel hybrid, isometric 2.5D atlas landmark miniatures, warm European adventure-map palette, crisp dark outline, readable on a detailed map, consistent camera angle and lighting. Make clusters compact and iconic, not crowded.
Background: perfectly flat solid #ff00ff chroma-key background for background removal. The background must be one uniform color with no shadows, gradients, texture, reflections, floor plane, or lighting variation. Do not use #ff00ff anywhere in the icons.
Avoid: text, letters, city names, flags, watermark, photorealism, modern flat vector UI, mixed styles, large drop shadows, cropped icons, map background behind icons, decorative frames, one-symbol-only cities.
```

Post-processing:

```bash
mkdir -p tmp/city-cluster-source
cp /path/to/generated/city_cluster_sheet.png tmp/city-cluster-source/city_cluster_sheet_source.png
uv run python "${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/scripts/remove_chroma_key.py" \
  --input tmp/city-cluster-source/city_cluster_sheet_source.png \
  --out tmp/city-cluster-source/city_cluster_sheet_alpha.png \
  --auto-key border \
  --soft-matte \
  --transparent-threshold 12 \
  --opaque-threshold 220 \
  --despill
uv run python -m map_pipeline.slice_city_cluster_landmarks \
  --sheet tmp/city-cluster-source/city_cluster_sheet_alpha.png \
  --out-dir assets/sprites/city_landmark_clusters
uv run python -m map_pipeline.outline_sprites \
  --source-dir assets/sprites/city_landmark_clusters \
  --out-dir assets/sprites/city_landmark_clusters/outlined \
  --prefix city_ \
  --radius 4 \
  --color '#25180fe0'
godot --headless --path . --import --quit
scripts/map-review-capture-godot.sh
```

Review rule: do not swap `scripts/map_panel.gd` to the cluster directory until the 8-city sheet passes the Godot-native review captures at `50%`, `100%`, `150%` and `200%`. The review should specifically compare Berlin/Hamburg/Rostock/München visual weight and reject if any city reads as a tiny single-object icon.

## Terrain and forest glyph generation workflow

User feedback 2026-05-31: trees and land texture must move toward the stronger generated donor map language, but the production map must remain glyph-based and expandable. The first new terrain sheet was generated as one 4x4 sheet, then sliced into reusable map glyphs.

Generated source:

```text
/home/alexey/.codex/generated_images/019e7af1-437a-70f1-9164-d2f7b34a9c81/ig_0023c5c793b5ea5e016a1c82b09f80819198e46012daa6c8cf.png
```

Project source copy:

```text
assets/map/glyphs/terrain_forest_sheet.png
```

This source sheet is excluded from Godot exports together with the other map pipeline source glyphs; runtime only needs `assets/map/germany_styled.png`.

Prompt:

```text
Use case: stylized-concept
Asset type: 1024x1024 game map sprite sheet for a Godot atlas map.
Primary request: Create a single 4x4 sprite sheet of reusable map glyphs: large readable forest masses, mixed deciduous/conifer forest clusters, grassy land texture patches, meadow tufts, small rocky forest foothills. Each cell must contain exactly one centered glyph with generous padding.
Style/medium: polished 16-bit RPG / pixel journey atlas, top-down fantasy travel map, warm European adventure-map palette, visually compatible with classic RPG map sprites. Similar density and readability to a hand-painted fantasy atlas, not GIS.
Composition/framing: orthographic top-down/isometric map glyphs, no perspective horizon, no UI. Keep all objects inside their cells. Make the forest glyphs large and readable from mobile-map distance, not tiny icons.
Color palette: warm olive grass, deep pine greens, yellow-green highlights, dark brown ink outlines, small beige stone accents only where needed.
Materials/textures: hand-painted pixel-art foliage, clustered tree canopies, subtle ground texture patches with soft irregular edges.
Text: none.
Constraints: perfectly flat solid #ff00ff chroma-key background only; no shadows cast onto background; no gradients or texture in the background; do not use #ff00ff inside any glyph. No labels, no city buildings, no roads, no water, no mountains except tiny stones inside foothill forest glyphs. The sheet must be cleanly sliceable into 16 equal cells.
```

Post-processing:

```bash
uv run python -m map_pipeline.slice_terrain_forest_glyphs \
  --sheet assets/map/glyphs/terrain_forest_sheet.png \
  --out-dir assets/map/glyphs
```

Output files:

- `atlas_forest_pine_dense.png`
- `atlas_forest_mixed_large.png`
- `atlas_forest_deciduous_dense.png`
- `atlas_forest_pine_round.png`
- `atlas_forest_mixed_wide.png`
- `atlas_forest_pine_tall.png`
- `atlas_forest_broadleaf_round.png`
- `atlas_forest_mixed_tall.png`
- `atlas_forest_pine_small.png`
- `atlas_forest_mixed_small.png`
- `atlas_land_grass_patch.png`
- `atlas_land_tuft_patch.png`
- `atlas_land_flower_meadow.png`
- `atlas_land_rocky_meadow.png`
- `atlas_forest_rocky_pine.png`
- `atlas_forest_rocky_mixed.png`

Composition:

- `ATLAS_FOREST_MASSES` places the forest glyphs by explicit German region coordinates.
- `ATLAS_LAND_DETAIL_PATCHES` places the land/meadow glyphs as a separate terrain layer under routes, details, city landmarks and transport markers.
- `audit_geography_layers()` checks that forest glyph ids start with `atlas_forest_`, land detail ids start with `atlas_land_`, and all anchors remain inside the map bounds.

## Map rendering workflow

Data source: local Natural Earth shapefiles under `data/natural_earth/`.

Required datasets:

- `ne_50m_admin_0_countries` for cleaner country borders;
- `ne_110m_lakes`;
- `ne_50m_land`;
- 110m datasets remain as fallbacks and lightweight reference data.

Procedural fallback render command:

```bash
uv run python -m map_pipeline.compose_map
```

Current runtime map workflow uses a reproducible procedural atlas underlay:

```bash
uv run python -m map_pipeline.compose_map
godot --headless --path . --import --quit
```

The older generated RPG underlay workflow is kept only as visual reference/experiment. Do not use it as the authoritative geography source unless it is re-audited against the relief/water/island criteria:

```bash
uv run python -m map_pipeline.adapt_generated_underlay \
  --source /home/alexey/.codex/generated_images/019e7af1-437a-70f1-9164-d2f7b34a9c81/ig_0715a97cc1e1e04e016a1bdfd731b48191914ea24c0858fd77.png \
  --out assets/map/germany_styled.png
godot --headless --path . --import --quit
```

Current visual-review underlay workflow uses a generated RPG-atlas source because the procedural/GIS underlay was capped at 4/10 by user review and the rubric:

```bash
uv run python -m map_pipeline.adapt_generated_underlay \
  --source /home/alexey/.codex/generated_images/019e7af1-437a-70f1-9164-d2f7b34a9c81/ig_0f7b9b4e8b981acb016a1c31509270819181e045e751bc63c8.png \
  --out assets/map/germany_styled.png \
  --colors 192
godot --headless --path . --import --quit
PORT=9000 scripts/serve-web.sh
```

Current generated underlay prompt:

```text
Use case: stylized-concept. Create a full-screen game map underlay asset for a Godot mobile/web app. Portrait 3:4 composition, no UI chrome.

Reference style direction: classic 16-bit RPG / pixel journey atlas like a cozy European adventure map, comparable in density and readability to a hand-painted pixel atlas with mountains, forests, water, small towns, and dotted routes. Warm natural palette, crisp silhouettes, slight parchment/painted-pixel texture, strong dark coast and country outlines. It should feel like a finished game map, not GIS, not a procedural canvas.

Subject: Germany and its immediate neighbors as an adventure atlas underlay for cableways and funiculars. Germany must be geographically recognizable and centered, full country visible from North Sea and Baltic Sea down to the Alps, with neighboring land/sea margin. Preserve real-feeling geography: North Sea/Baltic coast, Rügen island, Hamburg/Rostock north, Berlin east, Rhine west, Dresden southeast, Munich/Alps south, Harz central, Black Forest southwest, Bavarian Forest southeast, Müritz and other major lakes. Alps should be a strong coherent southern mountain wall extending beyond Germany; Harz, Black Forest, Bavarian Forest should be smaller distinct ranges; north German plain should stay mostly flat with forests, lakes, towns, coast, and fields, not giant mountains.

Art direction: dense but readable 16-bit RPG pixel atlas, cozy European colors, deep blue seas/lakes, varied green and ochre land, painterly pixel shading, forests as clustered tree masses, mountains as illustrated ranges, lakes and rivers with clear dark outlines, subtle roads/dotted travel routes integrated into terrain, small town silhouettes as background details only. Leave enough quiet terrain around major city/object areas for later clickable icons, but avoid empty boring areas. The map itself should look beautiful before icons are added.

Constraints: no text, no letters, no city labels, no flags, no pins, no markers, no app UI, no legend, no watermark. Do not add large random mountains in northern Germany. Do not make it a flat vector map, satellite map, realistic paper map, or stretched skinny Germany. No circular halos for future objects. No decorative border frame.
```

Important caveat: this source is allowed for visual iteration, not final geography authority. Before scoring 8/10 or higher, audit generated towns, rivers, lakes, islands and mountain ranges against real layers or replace them with controlled overlays.

## Relief and mountain glyph rules

- Real geography comes from named relief polygons/layers, not from decorative placements.
- A mountain glyph may be generic, but it must be placed only inside a real mountain/highland layer that supports that visual weight.
- Each layer should declare the intended glyph type:
  - `alpine`: sharp snowy high mountains for Alps and future Switzerland/Austria/Italy layers.
  - `forested_highland`: rounded forested hills/mountains for Black Forest, Bavarian Forest, Harz-like regions.
  - `border_highland`: smaller ridge symbols for Erzgebirge and similar border ranges.
  - `lowland`: no mountain glyphs; may use fields, marsh/forest texture, towns, rivers, islands, lakes.
- Large lakes and islands must be geography-driven. Do not add decorative lakes unless they correspond to real features; important shapes like Rügen must remain readable through Natural Earth coast/island geometry or explicit audited overlays.
- For future Europe expansion, do not encode accuracy as latitude rules. Encode it as region/layer rules: Norway can have northern mountains; North German Plain should not.

Generated RPG underlay prompt:

```text
Use case: stylized-concept
Asset type: full-screen Godot map underlay, portrait 3:4 aspect, no UI chrome
Primary request: Create a high-quality 16-bit RPG / pixel journey atlas map of Germany for a cableways and funiculars game. The map must fit a portrait 3:4 canvas, not an ultra-tall scroll. Germany should be geographically recognizable and centered, with the full country visible from North Sea/Baltic Sea to the Alps.
Canvas/layout: portrait 3:4 composition, full Germany visible, no frame, no title panel, no legend, no UI elements. Keep enough margin around Germany for neighboring land and seas. Do not make the country long and skinny.
Subject: Germany as a stylized adventure atlas. Strong visible Alpine mountains in the south, central mountain ranges, dense forest clusters, rivers, lakes, rolling fields, small towns, and winding dotted travel routes. Leave room for interactive transport icons to be overlaid later.
Style: 16-bit RPG pixel atlas, cozy European journey map, warm greens and ochres, dark readable coast/border outlines, subtle isometric 2.5D terrain icons, crisp silhouettes, painterly-pixel hybrid like a polished game map. Mountains and forests must be large and visible on a mobile screen.
Important constraints: no text, no labels, no numbers, no UI, no transport icons, no markers, no pins, no red circles, no watermark. Do not stretch the geography. Avoid a flat GIS look. Avoid photorealism. Avoid empty plains.
```

The map underlay should not include object icons. Object positions must come from catalog coordinates in Godot:

- `latitude`
- `longitude`
- optional `coordinates: Vector2(longitude, latitude)`

Icon selection must use normalized catalog data:

```gdscript
const TRANSPORT_TYPE_ICON := {
    "cable_gondola": "icon_cable_gondola",
    "cable_aerial_tram": "icon_aerial_tram",
    "funicular_classic": "icon_funicular",
    "rail_cog": "icon_cog_railway",
    "rail_suspended": "icon_suspended_monorail",
    "elevator_vertical": "icon_elevator",
}
```

Do not infer icon type with substring matching in UI code. If a new transport type needs a new icon, add it to the mapping and keep the database/catalog type normalized.

Germany map bounds currently used by both renderer and `MapPanel`:

```text
min_longitude = 4.5
max_longitude = 15.5
min_latitude = 46.5
max_latitude = 55.5
```

## UX constraints from user

- Start with fullscreen map.
- The screen should contain only the map by default.
- Objects must be correctly placed on the map.
- A small icon to switch to the list is acceptable.
- Focus remains on the map, not on list/card chrome.
- Generate icons as a single sheet when possible, to reduce cost and keep style consistent.

## Visual direction

User reference direction: classic 16-bit RPG / pixel journey map, not a plain GIS panel.

Useful traits to keep:

- fullscreen playable map first;
- readable stylized Europe/Germany geography;
- warm, natural 32-64 color palette;
- pixel/atlas texture instead of smooth GIS rendering;
- routes as adventure paths;
- object icons as small transport landmarks;
- UI chrome reduced to tiny overlay controls.

Current state after first pass:

- fullscreen Godot screenshot written by:
  ```bash
  xvfb-run -a godot --path . --write-movie tmp/map-screenshot.png --quit-after 3
  ```
- actual screenshot frame:
  ```text
  tmp/map-screenshot00000002.png
  ```
- compile/import checks pass:
  ```bash
  godot --headless --path . --import --quit
  godot --headless --path . --quit-after 1
  ```
- remaining visual work: add a dedicated viewport screenshot harness for landscape/desktop. The mobile viewport now opens directly on a fullscreen Germany map with only the map and small list toggle visible.

Latest verification:

```bash
uv run python -m map_pipeline.compose_map
python3 -m unittest discover -s tests
godot --headless --path . --quit-after 1
```

Results:

- `python3 -m unittest discover -s tests`: 218 tests OK.
- `godot --headless --path . --quit-after 1`: no GDScript/layout errors; Godot still prints shutdown RID leak warnings.
- latest visual screenshot frame: `tmp/map-screenshot00000002.png`.

Latest visual-pass notes:

- `assets/map/germany_styled.png`: 1568x2048, about 4.9 MB, generated RPG-atlas underlay.
- Runtime sprite payload: eight final icon PNGs, about 44-84 KB each; source sprite sheet is not kept under `assets/`.
- Latest mobile screenshot command:
  ```bash
  xvfb-run -a godot --path . --write-movie tmp/iter-map.png --quit-after 3
  ```
- Latest mobile screenshot frame:
  ```text
  tmp/iter-map00000002.png
  ```
  Historical note from an earlier self-check: this was previously over-scored as `10/10`. User review on 2026-05-31 rejected that assessment; the honest current target state is still below `8/10` until city landmarks are visible, coordinates feel aligned, pan is calmer, and the visual hierarchy reads instantly.

Browser verification:

```bash
PLAYWRIGHT_PACKAGE=/tmp/cable-playwright/node_modules/playwright \
  node scripts/verify-web-map.mjs
```

Evidence screenshots:

- `/tmp/cable-world-web-map/mobile-390x844-initial.png`
- `/tmp/cable-world-web-map/mobile-390x844-after-marker-click.png`
- `/tmp/cable-world-web-map/mobile-390x844-after-drag.png`
- `/tmp/cable-world-web-map/desktop-1280x800-initial.png`
- `/tmp/cable-world-web-map/desktop-1280x800-after-marker-click.png`
- `/tmp/cable-world-web-map/desktop-1280x800-after-drag.png`

Latest audit:

```text
docs/map-quality-audit-2026-05-31.md
```
