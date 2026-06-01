#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$root_dir"

"$root_dir/map_review_app/scripts/clean.sh"
"$root_dir/map_review_app/scripts/build-city-cluster-variant-reviews.sh"

if command -v xvfb-run >/dev/null 2>&1; then
  xvfb-run -a godot --no-header --audio-driver Dummy --path "$root_dir" --script map_review_app/capture_map_review_scenes.gd
else
  godot --no-header --audio-driver Dummy --path "$root_dir" --script map_review_app/capture_map_review_scenes.gd
fi

if ! curl -fsS "http://127.0.0.1:9010/api/review-tabs" >/dev/null 2>&1; then
  "$root_dir/map_review_app/scripts/start.sh"
fi

echo "Godot map review scenes updated: http://127.0.0.1:9010/"
