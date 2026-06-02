#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
issue="${ISSUE:-issue-81}"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
bundle_dir="${BUNDLE_DIR:-$root_dir/tmp/map-review/${issue}-${stamp}}"
screenshots_dir="$bundle_dir/screenshots"
logs_dir="$bundle_dir/logs"
server_log="$logs_dir/serve-web.log"
header_log="$logs_dir/header-check.log"
server_pid=""

usage() {
  cat <<'USAGE'
Usage: scripts/create-map-review-bundle.sh

Create a strict map reviewer bundle from the current worktree:
  - rebuild/export the Godot Web build through scripts/serve-web.sh
  - serve the exact build on 127.0.0.1:9000 or the next free port
  - collect required mobile/desktop Playwright screenshots
  - verify gzip/no-cache/build metadata headers
  - write build metadata and a forced ACCEPT/REJECT review report template

Environment:
  ISSUE=issue-81                         Bundle label.
  BUNDLE_DIR=tmp/map-review/issue-81     Output directory override.
  PORT=9000                              First port for scripts/serve-web.sh.
  HOST=127.0.0.1                         Bind host.
  PLAYWRIGHT_PACKAGE=playwright          Node package name/path used by verify-web-map.mjs.
USAGE
}

for arg in "$@"; do
  case "$arg" in
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

cleanup() {
  if [[ -n "$server_pid" ]]; then
    kill "$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
  fi
}
trap cleanup EXIT

mkdir -p "$screenshots_dir" "$logs_dir"

cd "$root_dir"

scripts/serve-web.sh >"$server_log" 2>&1 &
server_pid="$!"

review_url=""
for _ in {1..300}; do
  if ! kill -0 "$server_pid" 2>/dev/null; then
    cat "$server_log" >&2 || true
    echo "serve-web exited before printing URL" >&2
    exit 1
  fi
  review_url="$(sed -n 's/^URL: //p' "$server_log" | tail -n 1)"
  if [[ -n "$review_url" ]]; then
    break
  fi
  sleep 0.2
done

if [[ -z "$review_url" ]]; then
  cat "$server_log" >&2 || true
  echo "Timed out waiting for serve-web URL" >&2
  exit 1
fi

URL="$review_url" OUT_DIR="$screenshots_dir" node scripts/verify-web-map.mjs | tee "$logs_dir/playwright-screenshots.log"

{
  echo "URL: $review_url"
  echo
  for asset in index.html index.wasm index.pck index.js; do
    test -f "build/web/${asset}.gz"
    echo "## $asset"
    curl -fsSI -H "Accept-Encoding: gzip" "${review_url%/}/${asset}" | tr -d '\r'
    echo
  done
  for png in build/web/*.png; do
    test -e "$png" || continue
    asset="$(basename "$png")"
    test -f "${png}.gz"
    echo "## $asset"
    curl -fsSI -H "Accept-Encoding: gzip" "${review_url%/}/${asset}" | tr -d '\r'
    echo
  done
} | tee "$header_log" >/dev/null

grep -Eq '^Content-Encoding: gzip$' "$header_log"
grep -Eq '^Cache-Control: no-store, no-cache, must-revalidate, max-age=0$' "$header_log"
grep -Eq '^Pragma: no-cache$' "$header_log"
grep -Eq '^Expires: 0$' "$header_log"

curl -fsS "${review_url%/}/.web-build.json" >"$bundle_dir/web-build.json"
grep -Fq '"build_id"' "$bundle_dir/web-build.json"
curl -fsS "${review_url%/}/index.html" >"$bundle_dir/index.reviewed.html"
grep -Fq 'name="cable-world-web-build"' "$bundle_dir/index.reviewed.html"

git rev-parse HEAD >"$bundle_dir/reviewed-commit.txt"
git status --short >"$bundle_dir/git-status.txt"
find "$screenshots_dir" -maxdepth 1 -type f -name '*.png' -printf '%f\n' | sort >"$bundle_dir/screenshots.txt"

for required in \
  mobile-390x844-initial.png \
  mobile-390x844-zoom-150.png \
  mobile-390x844-zoom-200.png \
  mobile-390x844-after-marker-click.png \
  mobile-390x844-after-drag.png \
  desktop-1280x800-initial.png \
  desktop-1280x800-after-marker-click.png \
  desktop-1280x800-after-drag.png; do
  test -f "$screenshots_dir/$required"
done

cat >"$bundle_dir/review-report.md" <<REPORT
# Map Visual Review Report

Issue: $issue
Worktree: $root_dir
Branch: $(git branch --show-current)
Reviewed commit: $(git rev-parse HEAD)
Live URL: $review_url
Bundle: $bundle_dir
Screenshot directory: $screenshots_dir
Build metadata: web-build.json

## Command Results

- scripts/create-map-review-bundle.sh: PASS
- Web rebuild/export via scripts/serve-web.sh: PASS
- Playwright screenshots via scripts/verify-web-map.mjs: PASS
- gzip/no-cache/header check: PASS
- build metadata check: PASS

## Screenshots Checked

Reviewer must replace each PENDING with CHECKED or REJECT. Every screenshot below must be inspected visually:

- PENDING mobile-390x844-initial.png
- PENDING mobile-390x844-zoom-150.png
- PENDING mobile-390x844-zoom-200.png
- PENDING mobile-390x844-after-marker-click.png
- PENDING mobile-390x844-after-drag.png
- PENDING desktop-1280x800-initial.png
- PENDING desktop-1280x800-after-marker-click.png
- PENDING desktop-1280x800-after-drag.png

## Strict Visual Rubric

Rubric source: docs/map-reviewer-gate.md
Reference direction: warm RPG / atlas map, reusable glyphs/layers, not a monolithic generated map.

Reviewer must explicitly check:

- PENDING no visual regression in map readability.
- PENDING glyphs and tiny objects are readable at screenshot scale; no dust/noise houses/trees/details.
- PENDING labels stay near pictograms and do not drift away from landmarks.
- PENDING cities are not covered by transport icons.
- PENDING terrain, Alps, Harz, lakes and islands look plausible rather than random.
- PENDING list/map switch affordance remains clear where visible.
- PENDING pan/zoom/click screenshots show no marker jitter or detached overlays.
- PENDING live map and screenshots match the reference direction closely enough for the touched scope.

## Score

Score: __/10

Score cap reasons:

- None / list exact caps from docs/map-reviewer-gate.md.

Known accepted limitations:

- None / list only limitations that do not lower this touched scope below 10/10.

## Decision

Decision: REJECT

Only valid final decisions are ACCEPT or REJECT.
ACCEPT is allowed only when Score is 10/10 for the touched scope and every screenshot above is named as CHECKED.
Any visual regression in readability, glyph scale, icon/label alignment, terrain plausibility, or list/map switch affordance is REJECT.
If rejected, Next action must be: send back to implementer/fix-worker before integration.

Blockers if REJECT:

- List exact screenshot names and required fixes.

Next action:

- send back to implementer/fix-worker before integration
REPORT

echo "Map review bundle: $bundle_dir"
echo "Review report: $bundle_dir/review-report.md"
