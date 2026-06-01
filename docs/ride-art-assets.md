# Ride Art Assets

Issue: #92.

The ride side-view uses one generated sprite sheet:

- `asset_sources/ride/ride_sprite_sheet_source_chroma.png`: original generated sheet with a chroma-key background. The folder has `.gdignore` so Godot does not import this source-only file into runtime assets.
- `assets/sprites/ride/ride_sprite_sheet.png`: workspace asset used by Godot after chroma-key removal.

Generation mode: built-in `image_gen` tool, then local chroma-key removal.

Prompt:

```text
Use case: stylized-concept
Asset type: reusable sprite sheet for a Godot mobile game ride scene
Primary request: Create a 1024x1024 pixel-art sprite sheet for a European cableway/funicular journey game, matching a warm 16-bit RPG atlas style. The sheet must contain separate reusable sprites arranged in a clean grid with generous padding: 1 red gondola cabin hanging below a short hanger arm, 1 cream/yellow gondola cabin variant, 1 lower cableway station building, 1 upper cableway station building, 2 cable support towers with pulleys/sheaves, 3 tree clusters, 2 mountain ridge chunks, 1 grassy foreground patch, 1 small sign/plaque UI detail. Cableway physics must be plausible: cabins hang under a hanger grip, towers support a cable line, stations are aligned for a cable entering/exiting the building.
Style: cozy hand-painted pixel art, 16-bit RPG / SNES / GBA era, readable silhouettes, warm natural colors, dark clean outline, no harsh gradients, no modern vector style, no photorealism.
Background: perfectly flat solid #00ff00 chroma-key background for background removal. The background must be one uniform color with no shadows, gradients, texture, reflections, floor plane, or lighting variation. Keep all sprites fully separated from the background with crisp edges and generous padding. Do not use #00ff00 anywhere in the sprites.
Constraints: no text, no watermark, no labels, no impossible cable geometry, no cabins above the cable, no tiny unreadable details.
```

Selected generated source:

```text
/home/alexey/.codex/generated_images/019e7af1-437a-70f1-9164-d2f7b34a9c81/ig_09ab9f55e82853a1016a1ccf56b1dc8191ae872e698ca28b8d.png
```

The image came back at `1254x1254`, so the in-code atlas regions are measured against that actual source size, not the requested nominal size.

Chroma-key removal:

```bash
convert asset_sources/ride/ride_sprite_sheet_source_chroma.png \
  -alpha set \
  -fuzz 12% \
  -transparent 'rgb(22,236,20)' \
  assets/sprites/ride/ride_sprite_sheet.png
```

Validation:

- Corners of `ride_sprite_sheet.png` must be transparent.
- Cabin sprite must include a top grip and must be drawn below the cable point.
- Stations and support towers must expose cable sheaves aligned to the cable line.
- Do not bake route-specific station names or object names into the sprite sheet.

Screenshot review:

```bash
xvfb-run -a godot --path . --script scripts/capture_ride_art_screenshot.gd
```

This writes `tmp/ride-art-issue-92.png` for manual inspection.
