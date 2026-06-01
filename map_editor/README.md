# Hex Map Editor

Web editor for the Cable World map. Edits a global hex grid and saves to
`src/data/hex_map.json` — the same file format Godot will read.

## Run

```bash
cd map_editor
npm install
npm run dev   # http://localhost:9050  (also on the LAN for phones)
```

Fixed on port **9050**. Open from a phone on the same network via
`http://<computer-ip>:9050/`.

## How it works

- **Global Web Mercator hex grid.** Hex IDs `(q,r)` are world-global, so
  expanding Germany → Europe → Asia → world later only adds cells; existing IDs
  never shift. Each hex stores its real-world `center: [lon, lat]` so the map can
  be transferred onto a real slippy map.
- **100% = the game.** The editor frames the exact Germany `geo_bounds`
  (`lon [4.5, 16.8] · lat [43.2, 55.8]`) from `scripts/map_panel.gd` with COVER
  fit, so 100% matches Godot's default Germany view. Opens at 100% on Germany;
  zoom 50–200% (step 25%) via the `+/−` buttons. Wheel/trackpad pans.
- **Live reload.** Editing `hex_map.json` (by hand, by the editor's drag-save, or
  from an agent) hot-reloads the browser via Vite HMR + the `/__save` endpoint.

## Regenerate the base data

`src/data/hex_map.json` is baked from existing project data (Natural Earth
coastline, massif region polygons, `ATLAS_FOREST_MASSES`, `CITY_LABELS`):

```bash
cd map_pipeline && uv run python ../map_editor/tools/gen_hex_map.py
```
