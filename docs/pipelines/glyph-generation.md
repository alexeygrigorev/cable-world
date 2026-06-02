# Glyph Generation Pipelines

This is the index for generated map glyph workflows. Keep repeatable production steps here instead of in session handoff notes.

## Current Pipelines

- [City glyphs](city-glyphs.md): high-resolution multi-symbol city clusters, source specs, sheet cut audit, slicing, outline, and review.
- [Massif glyphs](../massif-glyph-pipeline.md): geography-backed mountain and massif glyph generation.

## Shared Rules

- Generated source sheets stay in `tmp/` or `$CODEX_HOME/generated_images/`, not in runtime asset folders.
- Runtime assets must be transparent PNGs with stable `city_` / `icon_` / glyph ids that match the code and data contracts.
- Before accepting any sheet sliced by a grid, run `map_pipeline.sheet_slice_audit`.
- The final acceptance zoom for map art is user zoom `200%`; do not accept assets that only look good when downscaled.
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
