#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
review_dir="$root_dir/assets/map/review"

mkdir -p "$review_dir"
find "$review_dir" -mindepth 1 ! -name .gdignore -exec rm -rf {} +
touch "$review_dir/.gdignore"

echo "Cleaned map review previews in assets/map/review/"
