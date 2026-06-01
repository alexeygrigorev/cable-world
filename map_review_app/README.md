# Map Review App

Local web app for fast visual feedback on map/glyph iterations. It serves only local files and runs on `127.0.0.1:9010`.

## Commands

Start, stop, and inspect the app:

```bash
map_review_app/scripts/start.sh
map_review_app/scripts/status.sh
map_review_app/scripts/stop.sh
```

Build the current Godot-native city-cluster review packet:

```bash
map_review_app/scripts/capture-godot.sh
```

That command:

1. clears old review images from `assets/map/review/`;
2. rebuilds `city_cluster_glyphs_hi_res` when tracked hi-res assets exist;
3. rebuilds temporary variant tabs from `tmp/city-cluster-hi-res-v*/outlined`;
4. captures current Godot runtime map scenes at `50%`, `100%`, `150%`, and `200%`;
5. starts the review app if `9010` is not reachable.

Open:

```text
http://127.0.0.1:9010/
```

## Review Sets

Every active review tab is a directory under:

```text
assets/map/review/
```

Each directory contains:

- `*_preview_050.png`
- `*_preview_100.png`
- `*_preview_150.png`
- `*_preview_200.png`
- `review.yml`

`review.yml` is intentionally written as JSON-compatible YAML, so the app can read it without extra dependencies. Keep it beside the images. If the images are removed, the feedback target disappears with them and stale context cannot pollute the next review.

Temporary comparison variants should live under:

```text
tmp/city-cluster-hi-res-vN/outlined/
```

`map_review_app/scripts/capture-godot.sh` will turn each matching folder into its own review tab. These variant tabs are for feedback only; they do not replace tracked runtime assets.

The legacy low-resolution city cluster sheet can still be rebuilt manually with:

```bash
map_review_app/scripts/build-city-cluster-review.sh
```

Do not include it in the default review packet unless it is the thing being reviewed; old tabs make it harder to judge the current high-resolution candidates.

The app also reads `assets/map/review/manifest.json` when present for tab ordering and names.

## Feedback

Saved feedback goes to:

```text
tmp/map-review-feedback/
```

The saved JSON and Markdown include the tab metadata from `review.yml`, so feedback can be traced back to the exact review set and image group.

## Compatibility Wrappers

The old commands under `scripts/map-review-*.sh` remain as thin wrappers. New work should put review-app logic inside `map_review_app/`.
