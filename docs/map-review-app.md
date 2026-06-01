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

This writes the full-map `50%`, `100%`, `150%` and `200%` previews plus one tab per massif entry from `assets/map/massifs/*.json`. The massif tabs use each entry's `map_bbox_px`, so they stay aligned with the same generated texture that the app uses.
The generator also writes `assets/map/review/manifest.json`; the app uses it for readable tab names and descriptions.

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
