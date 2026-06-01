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

Источники layout:

- уже существующие `map_pipeline/data/alpine_relief_extents.json`;
- `map_pipeline/data/terrain_massif_layers.json`;
- локальные Natural Earth boundaries для coast/country context;
- later: DEM/elevation raster или вручную подготовленная elevation/relief screenshot как reference.

Точность не должна быть миллиметровой. Требуется правдоподобная форма, масштаб и место: Alps большие, Harz маленький, Schwarzwald вытянутый, Sächsische Schweiz скальная.

### 2. Reference Image Or Image-To-Image

Preferred generation approach:

1. Сгенерировать layout image для massif sheet или отдельного массива.
2. Передать layout как image reference/edit target.
3. Prompt: сохранить общий силуэт и relative scale, перерисовать как 16-bit RPG atlas terrain glyph.
4. Для Alps делать несколько segments, потому что это большой массив; каждый segment должен иметь snow caps.
5. Для остальных массивов snow запрещен, кроме если будущий region реально требует snow.

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
- whether snow is allowed;
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
