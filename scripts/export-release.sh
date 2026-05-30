#!/usr/bin/env bash
set -euo pipefail

version="${1:-$(cat VERSION)}"
root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
dist_dir="$root_dir/dist/$version"

rm -rf "$dist_dir"
mkdir -p "$dist_dir/web" "$dist_dir/linux"

godot --headless --path "$root_dir" --import --quit
godot --headless --path "$root_dir" --export-release Web "$dist_dir/web/index.html"
godot --headless --path "$root_dir" --export-release Linux "$dist_dir/linux/mir-trossov.x86_64"

(
  cd "$dist_dir"
  python3 -m zipfile -c "mir-trossov-web-$version.zip" web
  python3 -m zipfile -c "mir-trossov-linux-$version.zip" linux
)

find "$dist_dir" -maxdepth 2 -type f -printf '%p %s bytes\n' | sort
