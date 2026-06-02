# City Glyph Pipeline

This project uses one active city pictogram process: high-resolution multi-symbol city cluster glyphs. Old single-landmark and low-resolution city sheet pipelines are archived and must not be revived.

## Source Of Truth

City coverage and prompt ingredients live in:

```text
map_pipeline/data/city_cluster_glyph_specs.json
```

Every `MapPanel.CITY_LABELS` city must have one entry in that file. The final runtime files are:

```text
assets/sprites/city_landmark_clusters_hi_res/city_<id>.png
assets/sprites/city_landmark_clusters_hi_res/outlined/city_<id>.png
```

Runtime loads only:

```text
res://assets/sprites/city_landmark_clusters_hi_res/outlined/city_%s.png
```

## Prompt Export

Print prompts from the spec file:

```bash
python3 -m map_pipeline.city_cluster_glyph_specs --prompts
```

For a subset:

```bash
python3 -m map_pipeline.city_cluster_glyph_specs \
  --status existing_cluster \
  --prompts
```

Prompt rules:

- Use 2-4 recognizable city elements, not a single landmark.
- Keep visual mass comparable across cities.
- Use painterly pixel-art / 2.5D atlas miniature style.
- Use a warm European RPG map palette and crisp dark outline.
- Generate on flat `#ff00ff` chroma key background.
- Do not include mountain backdrops, snowy peaks, broad hills, or terrain massifs in city glyphs. Terrain is rendered by the map's terrain/massif layers; city glyphs should show the town/city itself.
- Do not include water backdrops, harbor water, river strips, lakes, sea, boats, ships, piers, or wide bridges in city glyphs. Water and transport objects are separate map layers; city glyphs should not carry their own coastline/river scene.
- No text, letters, flags, labels, frames, map background, or photorealism.
- The glyph must stay clean at user zoom `300%`.

## Generate

Batch generation is the default because one sheet keeps style, scale, lighting, and outline language consistent across cities. Prefer fitting many cities into one generation when the cells still leave clear gutters, for example `4 columns x 3 rows`, `5 columns x 3 rows`, or larger review batches if the generated resolution keeps every city readable. Use single-city generation only to replace one rejected glyph after review.

Save selected generated sheets under `tmp/`, for example:

```text
tmp/city-cluster-hi-res-expanded/raw/sheet_01.png
```

Keep generator output files under `$CODEX_HOME/generated_images/` as provenance.

## High-res city cluster workflow

The original accepted pass used per-city `1254x1254` transparent sources. Runtime city sprites are normalized to `256x256` transparent PNGs for a mobile-sized map, and this size is accepted after review at user zoom `300%`. Do not upscale smaller API output to fake a larger source; keep the generator output as provenance and only downscale/crop into runtime assets.

## Remove Chroma Key

```bash
mkdir -p tmp/city-cluster-hi-res-expanded/alpha
for input in tmp/city-cluster-hi-res-expanded/raw/*.png; do
  name=$(basename "$input")
  python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/scripts/remove_chroma_key.py" \
    --input "$input" \
    --out "tmp/city-cluster-hi-res-expanded/alpha/$name" \
    --auto-key border \
    --soft-matte \
    --transparent-threshold 12 \
    --opaque-threshold 220 \
    --despill
done
```

## Audit Crop Lines

Run the sheet cut audit before accepting any generated sheet:

```bash
python3 -m map_pipeline.sheet_slice_audit \
  --sheet tmp/city-cluster-hi-res-expanded/alpha/sheet_01.png \
  --ids hannover,bremen,kiel,luebeck,duesseldorf,dortmund \
  --columns 3
```

The audit checks a narrow pixel strip around every grid cut and reports only when the same alpha component has pixels in the strip and alpha on both sides. This avoids false positives like Luxembourg, where a cell can visually touch a nominal edge without being cut. Real crop risks caught by this criterion include London, Brussels, Toulouse, Vienna, Valencia, Granada, and the same class of transport glyph artifact seen on the Dubrovnik cable-car marker.

Use `--warn-only` while exploring. For final runtime assets use the slicer with `--edge-audit error`, or fix/re-slice before accepting the sheet.

## Slice And Normalize

For a generated sheet, pass ids in exact sheet order:

```bash
python3 -m map_pipeline.slice_city_cluster_landmarks_hi_res \
  --sheet tmp/city-cluster-hi-res-expanded/alpha/sheet_01.png \
  --out-dir assets/sprites/city_landmark_clusters_hi_res \
  --ids hannover,bremen,kiel,luebeck,duesseldorf,dortmund \
  --columns 3 \
  --edge-audit error
```

For per-city transparent sources:

```bash
python3 -m map_pipeline.slice_city_cluster_landmarks_hi_res \
  --source-dir tmp/city-cluster-hi-res-expanded/alpha \
  --out-dir assets/sprites/city_landmark_clusters_hi_res \
  --ids hannover,bremen,kiel
```

The sheet slicer crops by connected alpha components, not only by the nominal grid cell. This prevents city clusters from losing a side when the generated art crosses a grid line. It also normalizes every accepted glyph to the current runtime target with transparent padding and removes tiny alpha islands from sheet edges.

Normalization rule: after alpha trim and fit, center the resized glyph horizontally and place its bottom on the shared bottom padding baseline. Do not vertically center city glyphs inside the 256x256 canvas; wide/low cities like Amsterdam and Bremen otherwise float above the map anchor while taller cities like Berlin and Hannover look correct by accident.

Wide/low city clusters must not occupy the full available width. If the trimmed glyph aspect ratio is above `1.25`, fit it to `184px` maximum content width before outline instead of the normal `208px` fit box. With the standard `--radius 2` outline this keeps wide runtime glyphs around `188px` alpha width, so examples like Dublin do not become visually wider than the rest of the city set.

The size contract lives in:

```text
map_pipeline/city_glyph_size_contract.py
```

## Outline

```bash
python3 -m map_pipeline.outline_sprites \
  --source-dir assets/sprites/city_landmark_clusters_hi_res \
  --out-dir assets/sprites/city_landmark_clusters_hi_res/outlined \
  --prefix city_ \
  --radius 2 \
  --color '#25180fe0'
```

## Size Audit

Run the size audit after every slice/outline pass:

```bash
python3 -m map_pipeline.audit_city_glyph_sizes
```

The audit checks the final runtime `outlined/city_*.png` files. It fails if:

- canvas size is not `256x256`;
- alpha content is wider or taller than the contract allows;
- wide/low glyphs exceed the stricter wide-city width;
- bottom alpha padding does not match the shared baseline.

## Import And Review

```bash
godot --headless --path . --import --quit
map_review_app/scripts/capture-godot.sh
map_review_app/scripts/start.sh
```

Open:

```text
http://127.0.0.1:9010/
```

Review rules:

- At `300%`, city glyphs must stay readable and scale with the map like boats, trees, terrain, and other glyphs.
- No visible city label should be bare text once a city has an accepted glyph.
- City labels must stay close to the pictogram and remain readable above transport markers.
- Static glyph contact sheets should normally expose only `300`; runtime Godot review captures can use `100%`, `200%`, and `300%`.

## Removed Legacy Process

Do not use or reintroduce:

```text
map_pipeline/slice_city_cluster_landmarks.py
map_pipeline/slice_city_landmarks.py
assets/sprites/city_landmark_clusters/
assets/sprites/city_landmarks/
map_review_app/scripts/build-city-cluster-review.sh
assets/map/review/city_cluster_glyphs/
```
