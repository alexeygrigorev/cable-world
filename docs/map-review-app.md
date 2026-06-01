# Map Review App

The map review app is a small local web UI for fast visual feedback on generated map previews.

Start it on port `9010`:

```bash
scripts/map-review-start.sh
```

Open:

```text
http://127.0.0.1:9010/
```

Update the preview images without rebuilding Godot or starting the main web export:

```bash
scripts/map-review-update-previews.sh
```

This writes the full-map `50%`, `100%`, `150%` and `200%` previews plus one tab per massif entry from `assets/map/massifs/*.json`. Each preview is a fixed-size viewport crop, so changing from `50%` to `200%` changes the apparent map scale instead of only changing the PNG dimensions. The massif tabs use each entry's `map_bbox_px`, so they stay aligned with the same generated texture that the app uses.
The generator also writes `assets/map/review/manifest.json`; the app uses it for readable tab names and descriptions.

For fast runtime-like iteration, use Godot-native capture instead:

```bash
scripts/map-review-capture-godot.sh
```

This runs `scripts/capture_map_review_scenes.gd` in headless Godot and writes fixed viewport PNGs directly into `assets/map/review/godot_*`. It does not export Web, does not start port `9000`, and is the preferred loop for UI/map placement tweaks such as moving city labels or checking marker jitter.

## Adding Fast Godot Review Scenes

For a new country, city, massif, or UI state, add an entry to `REVIEW_SCENES` in `scripts/capture_map_review_scenes.gd`:

```gdscript
{
    "id": "godot_berlin",
    "title": "Godot Berlin",
    "focus": Vector2(13.4050, 52.5200),
}
```

Use real longitude/latitude in `focus`. The script captures the same scene at `50%`, `100%`, `150%`, and `200%` zoom into a fixed `1280x900` viewport. For new countries or object sets, extend `_sample_objects()` or add a new sample factory so the runtime layer has representative markers and labels.

Preferred fast iteration loop:

1. Change GDScript, map placement, glyph assets, or label offsets.
2. Run `scripts/map-review-capture-godot.sh`.
3. Refresh `http://127.0.0.1:9010/`.
4. Review the `godot_*` tabs and save feedback.

Use `scripts/map-review-update-previews.sh` only when the underlying generated map texture changed and compositor previews are useful. Use Godot capture for runtime placement, labels, marker jitter, zoom behavior, and scene layout.

Check or stop the local review server:

```bash
scripts/map-review-status.sh
scripts/map-review-stop.sh
```

The app reads review images from `assets/map/review/`. PNGs in that directory become the default `Full map` tab. PNGs in subdirectories become extra tabs, which lets one review packet cover several countries, massifs, or generated variants.

Saved feedback is written to:

```text
tmp/map-review-feedback/
```

Only tabs with non-empty feedback are saved. Tabs with draft feedback are marked with a small green dot in the tab bar.
