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
- Do not include water backdrops, harbor water, river strips, lakes, sea, boats, ships, piers in city glyphs. Water and transport objects are separate map layers; city glyphs should not carry their own coastline/river scene.
- No text, letters, flags, labels, frames, map background, or photorealism.
- The glyph must stay clean at user zoom `300%`.

## Repeatable Style Contract

Prompt text alone is not enough to keep city glyphs repeatable. Every new batch must be generated and reviewed against an approved reference sheet.

Approved style reference:

```text
assets/map/references/city-glyph-style-reference-5x3.png
```

This sheet is the style source of truth. It is a pre-slice `5 columns x 3 rows` reference generated from these city-token concepts:

```text
Venice, Bolzano, Augsburg, Leipzig, Brno
Bremen, Kiel, Berlin, Milan, Prague
Brussels, Frankfurt, Riga, Kyiv, Athens
```

When prompting, explicitly ask for the batch to match the approved reference sheet in:

- 2.5D cluster volume, not flat architectural elevation;
- compact footprint with one shared bottom baseline;
- warm painted roofs and stone, not realistic postcard lighting;
- dark readable outline at the same strength as the reference sprites;
- varied landmark silhouettes that still read as one city token.

Rejected style patterns:

- flat skyline/collage sprites, especially realistic landmark elevations;
- single giant monument with tiny filler houses;
- terrain or scenic bases that make the city behave like a mountain/water glyph;
- wide city blocks that dominate neighboring cities after normalization.

Do not integrate a batch until its review sheet is visually checked against these references. If a whole batch uses the wrong style, reject the batch and regenerate from the reference sheet; do not patch individual cities from that batch unless the style already matches.

## Reference-Sheet Batch Prompt

Use the approved `5x3` reference image as an input image for every city generation batch. Ask for the output to use the same `5 columns x 3 rows` layout so the model sees and returns the same structure.

Generate batch prompts from the city spec file instead of writing them by hand:

```bash
python3 -m map_pipeline.city_cluster_glyph_specs --batch-prompts
```

For five parallel workers:

```bash
python3 -m map_pipeline.city_cluster_glyph_specs --batch-prompts --shard-count 5 --shard-index 1
python3 -m map_pipeline.city_cluster_glyph_specs --batch-prompts --shard-count 5 --shard-index 2
python3 -m map_pipeline.city_cluster_glyph_specs --batch-prompts --shard-count 5 --shard-index 3
python3 -m map_pipeline.city_cluster_glyph_specs --batch-prompts --shard-count 5 --shard-index 4
python3 -m map_pipeline.city_cluster_glyph_specs --batch-prompts --shard-count 5 --shard-index 5
```

The generated prompts deliberately ignore old generic city hints that mention water, harbors, hills, or mountains. City glyphs must stay city-only tokens; those other concepts belong to map layers.

Batch prompt shape:

```text
Input image: assets/map/references/city-glyph-style-reference-5x3.png is the style reference.
Create one coherent 5 columns x 3 rows city glyph sheet for these 15 cities, in this exact order:
<city ids / display names>.

Match the reference sheet's compact European RPG map city-token style:
single artist, painterly pixel-art / 2.5D atlas miniature, warm stone and terracotta palette,
crisp dark outline, consistent camera angle, consistent lighting, shared bottom baseline,
medium-small controlled tokens, comparable visual mass.

Use only positive city elements in each cell: compact old-town architecture, civic buildings,
churches, palaces, domes, roofs, towers as modest accents, arcades as building architecture.

Do not mention optional unwanted motifs in the city hints. If a motif should not appear,
avoid naming it unless it is a hard layer violation.

Hard constraints: no water, canals, rivers, sea, harbor water, boats, ships, piers, docks,
waterfront bases, terrain massifs, mountain backdrops, snowy peaks, broad hills, flags,
readable text, labels, frames, watermarks, photorealism, flat vector app-icon style.

Background: perfectly flat solid #ff00ff chroma-key background only, with clean #ff00ff gutters.
```

Do not ask for one city at a time during a full pass. Use full `5x3` visual batches. If a batch has fewer than 15 real cities, pad it with generated `style_filler_*` cells and discard those filler outputs after slicing. Do not ask for empty magenta cells in partial batches; empty cells make the model drift and can confuse component assignment during slicing.

## Full Regeneration Pass

When the city style drifts, regenerate all city glyphs from the approved reference sheet instead of patching isolated cities. Split the work into five shards with `--shard-count 5`; each worker writes only to its own `tmp/city-full-regen-agent-<n>/` directory:

```text
tmp/city-full-regen-agent-<n>/raw
tmp/city-full-regen-agent-<n>/alpha
tmp/city-full-regen-agent-<n>/sliced
tmp/city-full-regen-agent-<n>/outlined
tmp/city-full-regen-agent-<n>/review
```

Workers must not write to `assets/`, `docs/`, `map_editor/`, `map_pipeline/data/`, or commit. Integration happens only after the combined review sheets are accepted.

For each shard:

1. Generate coherent `5x3` raw sheets from the approved reference image and generated batch prompts.
2. Remove chroma key into `alpha/`.
3. Slice into `sliced/` with ids in exact sheet order and `--columns 5`; include any `style_filler_*` ids in the slice command, then discard those filler PNGs before integration.
4. Outline into `outlined/` with the normal city outline.
5. Build a review sheet from `outlined/`.
6. Run size and content audits; report warnings instead of integrating.

Reject a generated sheet if it visibly changes style, produces water/scenic terrain, creates a flat skyline, makes tokens much taller/wider than the approved reference, or makes neighboring cities visually incomparable.

## Generate

Batch generation is the default because one sheet keeps style, scale, lighting, and outline language consistent across cities. Prefer `5 columns x 3 rows` batches using the approved reference sheet. Use single-city generation only to replace one rejected glyph after review.

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

Normalization rule: after alpha trim, scale the resized glyph uniformly toward the shared target content height, center it horizontally, and place its bottom on the shared bottom padding baseline. Do not vertically center city glyphs inside the 256x256 canvas; wide/low cities like Amsterdam and Bremen otherwise float above the map anchor while taller cities like Berlin and Hannover look correct by accident.

Runtime city glyphs must be comparable by visible size, not only "below maximum". Normal-aspect city clusters should finish at the target outlined alpha height from `city_glyph_size_contract.py` on the shared baseline. The size audit fails normal-aspect glyphs that are visibly shorter than that target, which catches mistakes like Odesa or Venice looking smaller than neighboring cities.

Wide/low city clusters use the same uniform scale but may hit the canvas width first. Do not fix these by non-uniform X/Y stretching; regenerate the city art if its aspect makes it impossible to read at the shared size.

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
- normal-aspect alpha content is shorter than the shared target height;
- bottom alpha padding does not match the shared baseline.

## Content Audit

Run the content audit after every slice/outline pass while replacing old city glyphs:

```bash
python3 -m map_pipeline.audit_city_glyph_content --warn-only
```

It reports water-like content so batches with rivers, harbors, seas, boats, or blue water bases can be rejected before integration. During the current cleanup pass use `--warn-only` to get the candidate list without blocking older accepted assets. After all water-bearing city glyphs are replaced, run it without `--warn-only` as a gate.

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
- Compare neighboring cities on the actual map before accepting replacements. Nearby pairs such as Copenhagen/Malmo must have comparable visual mass unless the design intentionally marks one as a much larger city.

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
