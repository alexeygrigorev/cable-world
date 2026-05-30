#!/usr/bin/env bash
set -euo pipefail

version="${GODOT_VERSION:-4.6.3-stable}"
install_dir="${GODOT_INSTALL_DIR:-$HOME/.local/bin}"
template_dir="${GODOT_TEMPLATE_DIR:-$HOME/.local/share/godot/export_templates}"
bin_name="Godot_v${version}_linux.x86_64"
templates_zip="Godot_v${version}_export_templates.tpz"
version_dir="${version/-stable/.stable}"
install_export_templates="${INSTALL_EXPORT_TEMPLATES:-true}"

mkdir -p "$install_dir" "$template_dir/$version_dir"

if ! command -v godot >/dev/null 2>&1; then
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "$tmp_dir"' EXIT
  curl -L --fail --retry 3 \
    "https://github.com/godotengine/godot/releases/download/${version}/${bin_name}.zip" \
    -o "$tmp_dir/godot.zip"
  unzip -q "$tmp_dir/godot.zip" -d "$tmp_dir"
  install -m 0755 "$tmp_dir/$bin_name" "$install_dir/godot"
fi

if [ "$install_export_templates" = "true" ] && [ ! -f "$template_dir/$version_dir/web_release.zip" ]; then
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "$tmp_dir"' EXIT
  curl -L --fail --retry 3 \
    "https://github.com/godotengine/godot/releases/download/${version}/${templates_zip}" \
    -o "$tmp_dir/templates.tpz"
  unzip -q "$tmp_dir/templates.tpz" -d "$tmp_dir"
  cp -R "$tmp_dir/templates/." "$template_dir/$version_dir/"
fi

godot --version
