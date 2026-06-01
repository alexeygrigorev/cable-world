# Massif Glyph Pipeline

Дата: 2026-06-01.

Цель: получать узнаваемые горные массивы для карты не случайными текстовыми prompts, а повторяемым pipeline: географический макет -> style-consistent generation/edit -> нарезка -> explicit placement.

## Why

Текущая ошибка процесса: мы пытались улучшать Harz/Alps через текстовые описания и мелкие procedural patches. Это дает технический прогресс, но не дает визуально узнаваемые горы.

Новый критерий: screenshot должен явно показывать разные массивы:

- Alps: большие, протяженные, снежные вершины, cross-border wall/segments.
- Harz: компактный лесистый центральный массив вокруг Brocken, без снега.
- Schwarzwald / Black Forest: длинный темный лесистый southwest ridge.
- Bavarian Forest: средний лесисто-каменистый border massif.
- Erzgebirge: длинный нижний border ridge.
- Sächsische Schweiz: sandstone cliffs/table rocks, не обычные горы.
- Eifel/Hunsrück: низкие мягкие холмы.

## Pipeline

### 1. Geo Layout First

Для каждого массива сначала строится простой source layout, а не prompt only.

Layout должен содержать:

- прозрачный или flat background;
- силуэт/полигон массива в реальном примерном extent;
- ridge/arc line, где идет основной хребет;
- optional high/low zones: high peaks, forested slopes, low foothills;
- label только в metadata, не на картинке.

Important: layout is mountain-driven, not country-driven. Country borders can be visible context for review, but generation and placement must follow the geography of the massif itself: ridge arc, elevation shape, foothill edge, valley exclusions and recognizable sector shape. Do not ask the generator to make "German Alps" or "Austrian Alps" as country-shaped art; generate Alpine sectors and place them across the map.

Источники layout:

- уже существующие `map_pipeline/data/alpine_relief_extents.json`;
- `map_pipeline/data/terrain_massif_layers.json`;
- локальные Natural Earth boundaries для coast/country context;
- later: DEM/elevation raster или вручную подготовленная elevation/relief screenshot как reference.

Точность не должна быть миллиметровой. Требуется правдоподобная форма, масштаб и место: Alps большие, Harz маленький, Schwarzwald вытянутый, Sächsische Schweiz скальная.

Current reproducible command:

```bash
uv run python -m map_pipeline.render_massif_layouts
```

It writes per-massif reference layouts and a combined sheet:

```text
assets/map/massif_layouts/<massif>_layout.png
assets/map/massif_layouts/<massif>_layout.json
assets/map/massif_layouts/massif_geo_layout_sheet.png
assets/map/massif_layouts/manifest.json
```

These files are image-reference inputs for generation, not runtime art. They intentionally show silhouette, ridge direction and anchor points without labels. The `.json` sidecars hold labels and bounds.

### 2. Reference Image Or Image-To-Image

Preferred generation approach:

1. Сгенерировать layout image для massif sheet или отдельного массива.
2. Передать layout как image reference/edit target.
3. Prompt: сохранить общий силуэт и relative scale, перерисовать как 16-bit RPG atlas terrain glyph.
4. Для Alps делать несколько segments, потому что это большой массив; high Alpine segments обычно должны иметь snow caps.
5. Snow is data-driven, not manually forbidden. For every massif/sector, decide snow from elevation band, latitude/climate, season and known real-world character:
   - `expected`: high Alpine / glacier / consistently snow-capped sectors;
   - `seasonal_or_high_peaks`: snow only on highest peaks or winter/shoulder-season variants;
   - `not_expected`: low/mid highlands where snow would visually mislead the map.
   The pipeline should record the chosen policy in metadata before generating final art.

Если image-to-image недоступен или неудобен, fallback:

- текстовый prompt разрешен только для первого черновика;
- потом screenshot review обязан проверить, что форма/размер/характер совпадают с expected geography;
- не принимать prompt-only output как production, если массив выглядит generic.

### 3. Generate In Families

Можно генерировать одним sheet или несколькими запросами. Важно не количество запросов, а единый visual language.

Для consistency:

- один и тот же style block в каждом prompt;
- одинаковый chroma key или alpha workflow;
- одинаковая высота камеры: orthographic / slight isometric atlas glyph;
- одинаковая светотень;
- no labels, no UI, no roads, no buildings;
- generous padding and no cropping;
- source size должен выдерживать runtime zoom `200%`.

Minimum source sizes:

- Alps segment: желательно `>= 420px` по ширине после trim.
- Medium massif: желательно `>= 320px` по ширине.
- Small massif: желательно `>= 260px` по ширине.

Если source меньше, не растягивать до production size; перегенерировать крупнее или разбить на segments.

### 4. Slice And Normalize

Generated sheets go to:

```text
assets/map/glyphs/massif_glyph_sheet.png
```

Sliced glyphs go to:

```text
assets/map/glyphs/massif_<name>.png
```

Use:

```bash
uv run python -m map_pipeline.slice_massif_glyphs
```

Rules:

- remove chroma key to alpha;
- trim with padding;
- do not downscale to icon-size;
- keep large source resolution for `200%` zoom;
- do not ship source sheets in runtime payload if export excludes them.

### 5. Metadata And Placement

Every production massif glyph must be declared in metadata:

- source glyph id;
- intended massif id;
- geographic anchors or arc points;
- intended display width;
- source size px;
- snow policy (`expected`, `seasonal_or_high_peaks`, `not_expected`) with a short geography note;
- expected character notes.

Composer places glyphs by real coordinates and known region extents, not by random decoration.

Alps are composed from multiple `massif_alps_*` segments along the Alpine arc. Small massifs usually use one major glyph plus optional secondary texture/ridge glyph.

### 6. Review

A massif pass is not accepted by code tests alone.

Required checks:

- full map screenshot at default, 150%, 200%;
- mobile and desktop;
- compare to `docs/map-quality-rubric.md`;
- explicit self-audit: are Alps/Harz/Schwarzwald/Sächsische Schweiz visually different within 1-2 seconds?
- reject if mountains are generic, too pixelated at 200%, or placed as stickers with no geographic meaning.

## Current First Sheet

First generated source:

```text
assets/map/glyphs/massif_glyph_sheet.png
```

It contains:

- `massif_alps_wall_1`
- `massif_alps_wall_2`
- `massif_harz_brocken`
- `massif_black_forest_spine`
- `massif_bavarian_forest`
- `massif_erzgebirge_ridge`
- `massif_saxon_switzerland_sandstone`
- `massif_eifel_hunsrueck_low`

This sheet is only first pass. It is useful because it proves the visual distinction idea, but the next iteration should add geo-layout-guided generation, especially for Alps and Harz.

## Current Geo Layout Sheet

First generated layout source:

```text
assets/map/massif_layouts/massif_geo_layout_sheet.png
```

It is generated from `RELIEF_REGIONS` and `ALPINE_MASSIF_SEGMENTS`, so changing real anchors in `map_pipeline/compose_map.py` updates the reference geometry. The next production glyph generation should use this sheet or the individual `<massif>_layout.png` files as image references, then replace the first-pass `massif_*.png` art where it improves geographic recognition.

## Current Alpine Sector Sheet

Generated source:

```text
assets/map/glyphs/massif_alps_sector_sheet.png
```

Slice with:

```bash
uv run python -m map_pipeline.slice_alps_sector_glyphs
```

It produces:

- `massif_alps_western_arc`
- `massif_alps_central_high`
- `massif_alps_eastern_arc`
- `massif_alps_tyrol_wall`
- `massif_alps_northern_edge`
- `massif_alps_foothill_connector`

These are still generated art, but they are a better production step than repeating two generic wall glyphs across the whole Alpine arc.
