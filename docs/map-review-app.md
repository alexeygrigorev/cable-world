# Map Review App

The review app lives in `map_review_app/`. Keep app code, local control scripts, metadata handling, and the Godot capture script in that folder.

Primary docs:

```text
map_review_app/README.md
```

Current fast loop:

```bash
map_review_app/scripts/capture-godot.sh
```

This command clears stale review tabs, rebuilds the current city-cluster glyph review set, captures Godot runtime map scenes at `50%`, `100%`, `150%`, and `200%`, and starts `http://127.0.0.1:9010/` if needed.

Compatibility wrappers still exist under `scripts/map-review-*.sh`, but new app-specific logic belongs in `map_review_app/`.

## Feedback Hygiene

Before asking for feedback, the review app should contain only the current review packet. Old tabs are noise: they make it unclear what the user is supposed to inspect and can cause feedback to be attached to the wrong iteration.

Each review tab directory under `assets/map/review/` must include a `review.yml` file beside the PNGs. The file stores the review target, description, and image order. When the images are deleted, the metadata is deleted with them.
