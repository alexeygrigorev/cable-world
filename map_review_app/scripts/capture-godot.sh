#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$root_dir"

"$root_dir/map_review_app/scripts/clean.sh"
"$root_dir/map_review_app/scripts/build-city-cluster-review.sh"
if [[ -d "$root_dir/assets/sprites/city_landmark_clusters_hi_res/outlined" ]]; then
  uv run python -m map_pipeline.build_city_cluster_hi_res_review \
    --source-dir "$root_dir/assets/sprites/city_landmark_clusters_hi_res/outlined" \
    --out-dir "$root_dir/assets/map/review/city_cluster_glyphs_hi_res"
fi

if command -v xvfb-run >/dev/null 2>&1; then
  xvfb-run -a godot --no-header --audio-driver Dummy --path "$root_dir" --script map_review_app/capture_map_review_scenes.gd
else
  godot --no-header --audio-driver Dummy --path "$root_dir" --script map_review_app/capture_map_review_scenes.gd
fi

if ! curl -fsS "http://127.0.0.1:9010/api/review-tabs" >/dev/null 2>&1; then
  "$root_dir/map_review_app/scripts/start.sh"
fi

echo "Godot map review scenes updated: http://127.0.0.1:9010/"
