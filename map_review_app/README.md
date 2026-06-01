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
2. rebuilds temporary variant tabs from `tmp/city-cluster-hi-res-v*/outlined`;
3. captures current Godot runtime map scenes at `50%`, `100%`, `150%`, and `200%`;
4. starts the review app if `9010` is not reachable.

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

- one or more `*_preview_*.png` files;
- `review.yml`

`review.yml` is intentionally written as JSON-compatible YAML, so the app can read it without extra dependencies. Keep it beside the images. If the images are removed, the feedback target disappears with them and stale context cannot pollute the next review.

Use zoom series (`050`, `100`, `150`, `200`) only for runtime map captures where the camera actually changes. Static glyph contact sheets should normally expose only `200`, because downscaled copies do not answer a different review question.

The tracked hi-res city glyph source sheet is not shown as a default review tab anymore. City glyph scale and label attachment must be reviewed through the Godot runtime tabs, because those are the only previews where zoom, map texture scaling, labels, and coastal placement are all active together.

Temporary comparison variants should live under:

```text
tmp/city-cluster-hi-res-vN/outlined/
```

`map_review_app/scripts/capture-godot.sh` will turn each matching folder into its own review tab. These variant tabs are for feedback only; they do not replace tracked runtime assets.

The app also reads `assets/map/review/manifest.json` when present for tab ordering and names.

## Feedback

Saved feedback goes to:

```text
tmp/map-review-feedback/
```

The saved JSON and Markdown include the tab metadata from `review.yml`, so feedback can be traced back to the exact review set and image group.

## Compatibility Wrappers

The old commands under `scripts/map-review-*.sh` remain as thin wrappers. New work should put review-app logic inside `map_review_app/`.
