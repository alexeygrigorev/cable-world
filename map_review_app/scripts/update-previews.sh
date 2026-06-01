#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "$root_dir"
uv run python -m map_pipeline.compose_map
uv run python -m map_pipeline.render_map_previews
echo "Updated map review previews in assets/map/review/"
