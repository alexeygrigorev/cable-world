#!/usr/bin/env bash
set -euo pipefail

version="${GODOT_VERSION:-4.6.3-stable}"
install_dir="${GODOT_INSTALL_DIR:-$HOME/.local/bin}"
template_dir="${GODOT_TEMPLATE_DIR:-$HOME/.local/share/godot/export_templates}"
bin_name="Godot_v${version}_linux.x86_64"
templates_zip="Godot_v${version}_export_templates.tpz"
version_dir="${version/-stable/.stable}"
install_export_templates="${INSTALL_EXPORT_TEMPLATES:-true}"
configure_android_export="${CONFIGURE_GODOT_ANDROID_EXPORT:-false}"

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

if [ "$configure_android_export" = "true" ]; then
  android_sdk_path="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}"
  java_sdk_path="${JAVA_HOME:-}"
  if [ -z "$android_sdk_path" ]; then
    echo "CONFIGURE_GODOT_ANDROID_EXPORT=true requires ANDROID_HOME or ANDROID_SDK_ROOT" >&2
    exit 1
  fi
  if [ -z "$java_sdk_path" ]; then
    echo "CONFIGURE_GODOT_ANDROID_EXPORT=true requires JAVA_HOME" >&2
    exit 1
  fi

  settings_version="$(printf '%s' "$version" | sed -E 's/^([0-9]+[.][0-9]+).*/\1/')"
  settings_dir="${XDG_CONFIG_HOME:-$HOME/.config}/godot"
  settings_file="$settings_dir/editor_settings-$settings_version.tres"
  mkdir -p "$settings_dir"
  if [ ! -f "$settings_file" ]; then
    printf '[gd_resource type="EditorSettings" format=3]\n\n[resource]\n' > "$settings_file"
  fi

  set_editor_setting() {
    local key="$1"
    local value="$2"
    local escaped_value
    escaped_value="$(printf '%s' "$value" | sed 's/[\\&|]/\\&/g')"
    if grep -q -F "$key = " "$settings_file"; then
      sed -i "s|^$key = .*|$key = \"$escaped_value\"|" "$settings_file"
    else
      printf '%s = "%s"\n' "$key" "$value" >> "$settings_file"
    fi
  }

  set_editor_setting "export/android/android_sdk_path" "$android_sdk_path"
  set_editor_setting "export/android/java_sdk_path" "$java_sdk_path"
fi

godot --version
