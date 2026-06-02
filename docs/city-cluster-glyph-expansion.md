# City Cluster Glyph Expansion

Canonical pipeline doc: [pipelines/city-glyphs.md](pipelines/city-glyphs.md).

This file keeps expansion-specific notes and command examples from the first city cluster rollout. New repeatable pipeline rules belong in the canonical doc above.

## Source Of Truth

City coverage and prompt ingredients live in:

```text
map_pipeline/data/city_cluster_glyph_specs.json
```

Every `MapPanel.CITY_LABELS` city must have one entry in that file. The `id` is the runtime asset id used by `scripts/map_panel.gd`, and the final runtime files are:

```text
assets/sprites/city_landmark_clusters_hi_res/city_<id>.png
assets/sprites/city_landmark_clusters_hi_res/outlined/city_<id>.png
```

Runtime loads only:

```text
res://assets/sprites/city_landmark_clusters_hi_res/outlined/city_%s.png
```

## Prompt Export

Print exact per-city prompts from the spec file:

```bash
uv run python -m map_pipeline.city_cluster_glyph_specs --prompts
```

For a subset:

```bash
uv run python -m map_pipeline.city_cluster_glyph_specs \
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
- The glyph must stay clean at user zoom `200%`.

## Generate

Preferred batching is small sheets, for example `3 columns x 2 rows`, so the generated city clusters remain large enough. Save generated sheets under:

```text
tmp/city-cluster-hi-res-expanded/raw/sheet_01.png
```

Keep the generator output files under `$CODEX_HOME/generated_images/` as provenance; copy selected files into `tmp/` before processing.

## Remove Chroma Key

```bash
mkdir -p tmp/city-cluster-hi-res-expanded/alpha
for input in tmp/city-cluster-hi-res-expanded/raw/*.png; do
  name=$(basename "$input")
  uv run python "${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/scripts/remove_chroma_key.py" \
    --input "$input" \
    --out "tmp/city-cluster-hi-res-expanded/alpha/$name" \
    --auto-key border \
    --soft-matte \
    --transparent-threshold 12 \
    --opaque-threshold 220 \
    --despill
done
```

## Slice And Normalize

For a generated 3x2 sheet, pass the ids in exact sheet order:

```bash
uv run python -m map_pipeline.slice_city_cluster_landmarks_hi_res \
  --sheet tmp/city-cluster-hi-res-expanded/alpha/sheet_01.png \
  --out-dir assets/sprites/city_landmark_clusters_hi_res \
  --ids hannover,bremen,kiel,luebeck,duesseldorf,dortmund \
  --columns 3
```

For per-city transparent sources:

```bash
uv run python -m map_pipeline.slice_city_cluster_landmarks_hi_res \
  --source-dir tmp/city-cluster-hi-res-expanded/alpha \
  --out-dir assets/sprites/city_landmark_clusters_hi_res \
  --ids hannover,bremen,kiel
```

The slicer normalizes every accepted glyph to `1024x1024` with transparent padding and removes tiny alpha islands from sheet edges.

## Outline

```bash
uv run python -m map_pipeline.outline_sprites \
  --source-dir assets/sprites/city_landmark_clusters_hi_res \
  --out-dir assets/sprites/city_landmark_clusters_hi_res/outlined \
  --prefix city_ \
  --radius 6 \
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

Review tabs:

- `Hi-res City Cluster Glyphs`: source-quality contact sheet. This should normally expose only `200`, because downscaled static copies do not test runtime zoom.
- `Godot ...`: runtime map captures at `50%`, `100%`, `150%`, `200%`. These are the only tabs where zoom series is meaningful.

Review rules:

- At `200%`, city glyphs must scale with the map like boats, trees, terrain, and other glyphs.
- No visible city label should be a bare text-only label once a city has an accepted glyph.
- City labels must stay close to the pictogram and remain readable above transport markers.
- If browser output looks stale, verify the response headers include `Cache-Control: no-store`, `Pragma: no-cache`, and `Expires: 0`.

## Removed Legacy Process

Do not use or reintroduce:

```text
map_pipeline/slice_city_cluster_landmarks.py
assets/sprites/city_landmark_clusters/
map_review_app/scripts/build-city-cluster-review.sh
assets/map/review/city_cluster_glyphs/
```

Those belonged to the old `512x512` / low-resolution sheet process and are intentionally gone.
