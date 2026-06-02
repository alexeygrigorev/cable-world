# Glyph Generation Pipelines

This is the index for generated map glyph workflows. Keep repeatable production steps here instead of in session handoff notes.

## Current Pipelines

- [City glyphs](city-glyphs.md): high-resolution multi-symbol city clusters, source specs, sheet cut audit, slicing, outline, and review.
- [Massif glyphs](../massif-glyph-pipeline.md): geography-backed mountain and massif glyph generation.
- Transport icons: generated 4x2 sheet -> chroma-key removal -> `map_pipeline.slice_transport_icons` -> `assets/sprites/outlined/icon_*.png`.
- Terrain and forest glyphs: generated sheet -> `map_pipeline.slice_terrain_forest_glyphs` -> explicit placement through `map_pipeline.compose_map`.

## Shared Rules

- Generated source sheets stay in `tmp/` or `$CODEX_HOME/generated_images/`, not in runtime asset folders.
- Runtime assets must be transparent PNGs with stable `city_` / `icon_` / glyph ids that match the code and data contracts.
- Before accepting any sheet sliced by a grid, run `map_pipeline.sheet_slice_audit`.
- The final acceptance zoom for map art is user zoom `300%`; do not accept assets that only look good when downscaled.
- In the hex editor, every feature shown in the clicked-hex panel must show its object id, concrete glyph filename, and a visible glyph preview.
- Multi-hex glyphs must have metadata, not per-instance footprints: `anchor_offset` is `bottom-left`, meaning `anchor_source_px` is the per-glyph lower-left support point chosen from the glyph's bottom visible alpha band and the rendered glyph is attached to the lower-left support point of the anchor hex. Footprint math uses that lower-left support point; debug dots and the yellow anchor ring are displayed at hex centers for readability. Each PNG has one canonical `glyph_ref` without a size suffix, for example `massif:swiss_alps_massif`; size lives only in metadata as `zoom_factor` / `render_width_hex`. `primary_offsets` are bright blue debug dots, and `faint_offsets` are pale gray weak-alpha debug dots. Empty alpha has no dot and must not select the glyph.
- Bottom-left anchored glyph PNGs must have minimal bottom alpha padding. Run `python3 -m map_pipeline.audit_glyph_alpha_anchor --fix assets/map/massifs/*.png` before regenerating `hex_map.json`; then run without `--fix` as the gate.
- Add or update a focused Python contract test when a pipeline rule becomes required.

## Sheet Cut Audit

Use this for any generated glyph sheet before final slicing:

```bash
python3 -m map_pipeline.sheet_slice_audit \
  --sheet tmp/<sheet>.png \
  --ids id_1,id_2,id_3,id_4 \
  --columns 4
```

The default mode checks the pixel strip around each grid cut. It reports only when one alpha component has pixels in the strip and alpha on both sides of that strip. This avoids noisy edge-only reports while catching real crop artifacts where a fixed grid crop would cut through an object.

During exploration, add `--warn-only`. For final accepted sheets, keep the non-zero exit behavior or use slicer-specific `--edge-audit error`.

## Runtime Outline

Generated transparent sprites usually need a runtime outline pass so they read over the map:

```bash
python3 -m map_pipeline.outline_sprites \
  --source-dir <source-dir> \
  --out-dir <source-dir>/outlined \
  --prefix <prefix> \
  --radius 3 \
  --color '#25180fe0'
```

Use the local pipeline-specific radius and color when a detailed doc specifies one.

## Transport Icon Sheet

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/scripts/remove_chroma_key.py" \
  --input <generated-magenta-sheet.png> \
  --out tmp/map-icon-source/transport_icon_sheet.png \
  --auto-key border \
  --soft-matte \
  --transparent-threshold 12 \
  --opaque-threshold 220 \
  --despill

python3 -m map_pipeline.slice_transport_icons \
  --sheet tmp/map-icon-source/transport_icon_sheet.png \
  --out-dir assets/sprites \
  --edge-audit error

python3 -m map_pipeline.outline_sprites \
  --source-dir assets/sprites \
  --out-dir assets/sprites/outlined \
  --prefix icon_ \
  --radius 3 \
  --color '#23170de8'
```

Runtime loads the outlined `icon_*.png` files. Do not keep source transport sheets in `assets/sprites`.

## Terrain And Forest Sheets

Terrain/forest sheets are source glyph sheets, not runtime map overlays by themselves. Slice them, then place the resulting ids explicitly through the map pipeline:

```bash
python3 -m map_pipeline.slice_terrain_forest_glyphs \
  --sheet assets/map/glyphs/terrain_forest_sheet.png \
  --out-dir assets/map/glyphs
```

Any future terrain sheet that is sliced by a grid should also run `map_pipeline.sheet_slice_audit` first.
