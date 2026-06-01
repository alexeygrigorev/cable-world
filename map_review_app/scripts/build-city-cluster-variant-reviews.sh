#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

shopt -s nullglob
for variant_dir in "$root_dir"/tmp/city-cluster-hi-res-v*/outlined; do
  variant_name="$(basename "$(dirname "$variant_dir")")"
  variant_suffix="${variant_name#city-cluster-hi-res-}"
  if [[ "$variant_suffix" != "$variant_name" ]]; then
    variant_id="city_cluster_glyphs_hi_res_${variant_suffix//-/_}"
    variant_title="Hi-res City Cluster Glyphs ${variant_suffix^^}"
  else
    variant_id="${variant_name//-/_}"
    variant_title="$(printf '%s' "$variant_name" | sed 's/-/ /g; s/\b\([a-z]\)/\u\1/g')"
  fi
  out_dir="$root_dir/assets/map/review/$variant_id"
  uv run python -m map_pipeline.build_city_cluster_hi_res_review \
    --source-dir "$variant_dir" \
    --out-dir "$out_dir" \
    --id "$variant_id" \
    --title "$variant_title" \
    --status existing_cluster \
    --description "Temporary city cluster variant generated from $variant_name." \
    --feedback-target "Compare this temporary variant against city_cluster_glyphs_hi_res before replacing tracked runtime assets."
done
