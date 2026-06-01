#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
review_dir="$root_dir/assets/map/review/city_cluster_glyphs"
source_dir="$root_dir/assets/sprites/city_landmark_clusters/outlined"
work_dir="$root_dir/tmp/city-cluster-source"

mkdir -p "$review_dir" "$work_dir"

montage \
  "$source_dir/city_berlin.png" \
  "$source_dir/city_hamburg.png" \
  "$source_dir/city_rostock.png" \
  "$source_dir/city_munich.png" \
  "$source_dir/city_cologne.png" \
  "$source_dir/city_frankfurt.png" \
  "$source_dir/city_stuttgart.png" \
  "$source_dir/city_dresden.png" \
  -background '#d9c99b' \
  -geometry 300x300+24+24 \
  -tile 4x2 \
  "$work_dir/city_cluster_contact_200.png"

convert "$work_dir/city_cluster_contact_200.png" -resize 25% "$review_dir/city_cluster_glyphs_preview_050.png"
convert "$work_dir/city_cluster_contact_200.png" -resize 50% "$review_dir/city_cluster_glyphs_preview_100.png"
convert "$work_dir/city_cluster_contact_200.png" -resize 75% "$review_dir/city_cluster_glyphs_preview_150.png"
cp "$work_dir/city_cluster_contact_200.png" "$review_dir/city_cluster_glyphs_preview_200.png"

cat >"$review_dir/review.yml" <<'JSON'
{
  "schema": "cable-world.map-review-set.v1",
  "id": "city_cluster_glyphs",
  "title": "City Cluster Glyphs",
  "description": "Current multi-symbol city cluster glyph sheet for the first 8 German cities. Review this for visual weight, recognizability, and 200% source quality.",
  "feedbackTarget": "Approve or reject the cluster glyph source assets before broader replacement.",
  "order": ["050", "100", "150", "200"],
  "cities": ["Berlin", "Hamburg", "Rostock", "München", "Köln", "Frankfurt", "Stuttgart", "Dresden"]
}
JSON

echo "Updated city cluster glyph review set in assets/map/review/city_cluster_glyphs/"
