# Europe Journey Map Pipeline v1

## Objective

Build a production-ready map generation pipeline for a transport exploration game.

The map must:

- remain geographically accurate
- support future expansion to Asia and the rest of the world
- support multiple zoom levels
- use a consistent visual style
- allow programmatic placement of transport objects
- avoid AI-generated full-map images

AI should only generate reusable visual assets.

---

# Core Principle

Never generate the map.

Generate map assets.

The map is rendered from geographic data.

Visual style is applied through reusable assets.

---

# Target Visual Style

Reference:

- Dorfromantik
- Heroes III Adventure Map
- tabletop miniature landscapes
- soft painterly rendering
- slightly tilted camera

Not:

- pixel art
- photorealism
- satellite imagery
- procedural noise

Camera:

35 degree tilt

Lighting:

top-left

Terrain:

miniature tabletop appearance

Cities:

miniature city clusters

Mountains:

miniature mountain ranges

Forests:

dense rounded forest clusters

---

# System Architecture

## Layer 1 — Geography

Source of truth.

Input:

- Natural Earth (v1)
- OpenStreetMap (later)

Files:

```text
data/
  europe_land.geojson
  cities.geojson
  mountains.geojson
  lakes.geojson
```

No AI.

---

## Layer 2 — Map Projection

Convert latitude/longitude into screen coordinates.

Implementation:

- pyproj

Requirements:

- Europe support
- future world support
- zoom levels

---

## Layer 3 — Terrain Regions

Examples:

- Alps
- Pyrenees
- Carpathians
- Tatras
- Black Forest
- Scandinavian Forest
- Iceland Volcanic Region

```python
Region(
    id="alps",
    type="mountains",
    style_pack="alps"
)
```

---

## Layer 4 — Style Packs

```text
styles/
  europe_journey/
    mountains/
    forests/
    cities/
    stations/
```

Future:

```text
styles/heroes/
styles/watercolor/
styles/pixel/
```

Renderer must be style-agnostic.

---

# AI Asset Generation

Model:

- gpt-image-1

Never generate maps.

Generate assets only.

Examples:

- alpine mountain clusters
- carpathian mountain clusters
- black forest clusters
- city icons
- funicular stations
- cable car stations

Output:

- transparent PNG
- 1024x1024

---

# Prompt Template

Every prompt starts with:

```text
Europe Journey Style

- tabletop miniature landscape
- tilted 35 degree camera
- soft painterly rendering
- readable at map scale
- warm color palette
- no text
- transparent background
- suitable for strategy game map
```

Example:

```text
Europe Journey Style.

Alpine mountain cluster.

Requirements:

- recognizable Alpine appearance
- snow-capped peaks
- miniature tabletop landscape
- transparent background
```

---

# Asset Library Generator

Create:

```text
generate_style_pack.py
```

Responsibilities:

- generate assets via OpenAI
- store metadata
- version assets
- avoid duplicates

---

# Map Renderer

Create:

```text
render_map.py
```

Pipeline:

```text
Load geography
    ↓
Load style pack
    ↓
Place terrain assets
    ↓
Place cities
    ↓
Place transport objects
    ↓
Export PNG
```

---

# Terrain Placement

Do not place random mountains.

Use region-aware placement.

Example:

```text
Alps polygon
    ↓
sample points
    ↓
place alpine mountain assets
```

Same for:

- Carpathians
- Pyrenees
- Tatras
- Forest regions

---

# Transport Layer

Input:

```json
{
  "id": "heidelberg_bergbahn",
  "lat": 49.4106,
  "lon": 8.7153,
  "type": "funicular"
}
```

Renderer:

```text
coordinates
    ↓
icon
    ↓
metadata
```

---

# Zoom Levels

## LOD0

Entire Europe

Show:

- capitals
- mountain ranges
- transport markers

## LOD1

Country scale

Show:

- cities
- stations
- routes

## LOD2

Local scale

Show:

- station details

Prototype requires:

- LOD0
- LOD1

---

# Deliverables

Package:

```text
map_pipeline/
```

Modules:

```text
projection.py
renderer.py
asset_generation.py
terrain.py
transport.py
```

Scripts:

```text
generate_style_pack.py
render_map.py
```

Outputs:

```text
europe_lod0.png
germany_lod1.png
```

---

# Success Criteria

- Europe geographically correct
- Alps visually distinct from Carpathians
- Black Forest differs from Scandinavian forests
- Heidelberg marker appears correctly
- New transport objects added through JSON only
- Entire style replaced by switching style packs
