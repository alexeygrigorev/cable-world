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
- No text, letters, flags, labels, frames, map background, or photorealism.
- The glyph must stay clean at user zoom `300%`.

## Generate

Preferred batching is small sheets, for example `3 columns x 2 rows` or `4 columns x 2 rows`, so generated city clusters remain large enough. Save selected generated sheets under `tmp/`, for example:

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

## Outline

```bash
python3 -m map_pipeline.outline_sprites \
  --source-dir assets/sprites/city_landmark_clusters_hi_res \
  --out-dir assets/sprites/city_landmark_clusters_hi_res/outlined \
  --prefix city_ \
  --radius 2 \
  --color '#25180fe0'
```

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
