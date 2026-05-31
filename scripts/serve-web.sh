#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
build_dir="${BUILD_DIR_OVERRIDE:-$root_dir/build/web}"
host="${HOST:-127.0.0.1}"
start_port="${PORT:-9000}"
skip_export=0
check_headers=0

for arg in "$@"; do
  case "$arg" in
    --no-export)
      skip_export=1
      ;;
    --check-headers)
      check_headers=1
      skip_export=1
      ;;
    -h|--help)
      cat <<'USAGE'
Usage: scripts/serve-web.sh [--no-export] [--check-headers]

Build and serve the Godot Web export locally.

Environment:
  HOST=127.0.0.1  Bind host.
  PORT=9000       First port to try. The script searches up to 9999.

Options:
  --no-export     Serve the existing build/web directory without rebuilding.
  --check-headers Validate no-store and gzip headers, then exit.
USAGE
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

if [[ "$check_headers" -eq 1 ]]; then
  build_dir="$(mktemp -d "${TMPDIR:-/tmp}/cable-world-web-check.XXXXXX")"
fi

if [[ "$skip_export" -eq 0 ]]; then
  rm -rf "$build_dir"
  mkdir -p "$build_dir"
  godot --headless --path "$root_dir" --import --quit
  godot --headless --path "$root_dir" --export-release Web "$build_dir/index.html"
fi

if [[ ! -f "$build_dir/index.html" ]]; then
  if [[ "$check_headers" -eq 1 ]]; then
    mkdir -p "$build_dir"
    printf '<!doctype html><html><head></head><body><script src="index.js"></script><img src="map.png"></body></html>\n' > "$build_dir/index.html"
    printf 'console.log("header check");\n' > "$build_dir/index.js"
    printf 'wasm-check\n' > "$build_dir/index.wasm"
    printf 'pck-check\n' > "$build_dir/index.pck"
    printf 'png-check\n' > "$build_dir/map.png"
  else
    echo "Missing $build_dir/index.html. Run without --no-export first." >&2
    exit 1
  fi
fi

build_time="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
git_commit="$(git -C "$root_dir" rev-parse --short=12 HEAD 2>/dev/null || printf 'unknown')"
build_id="${WEB_BUILD_ID:-${git_commit}-$(date -u +%Y%m%dT%H%M%SZ)}"

python3 - "$build_dir/index.html" "$build_id" <<'PY'
from pathlib import Path
import re
import sys

index_path = Path(sys.argv[1])
build_id = sys.argv[2]
text = index_path.read_text(encoding="utf-8")

text = re.sub(
    r'\s*<meta name="cable-world-web-build" content="[^"]*">\n?',
    "\n",
    text,
)
meta = f'<meta name="cable-world-web-build" content="{build_id}">'
if "<head>" in text:
    text = text.replace("<head>", f"<head>\n\t\t{meta}", 1)
else:
    text = f"{meta}\n{text}"

def cache_bust(match: re.Match[str]) -> str:
    attr = match.group(1)
    quote = match.group(2)
    url = match.group(3)
    if "://" in url or url.startswith(("data:", "blob:", "#")):
        return match.group(0)
    url = re.sub(r"([?&])v=[^&#\"]*", "", url)
    separator = "&" if "?" in url else "?"
    return f'{attr}={quote}{url}{separator}v={build_id}{quote}'

text = re.sub(
    r'\b(src|href)=(["\'])([^"\']+\.(?:html|js|wasm|pck|png)(?:\?[^"\']*)?)\2',
    cache_bust,
    text,
)
index_path.write_text(text, encoding="utf-8")
PY

cat > "$build_dir/.web-build.json" <<JSON
{"build_id":"$build_id","created_at_utc":"$build_time","git_commit":"$git_commit"}
JSON

find "$build_dir" -maxdepth 1 -type f \( -name '*.wasm' -o -name '*.pck' -o -name '*.js' -o -name '*.html' -o -name '*.png' \) -print0 \
  | while IFS= read -r -d '' file; do
      gzip -9 -kf "$file"
    done

if [[ "$check_headers" -eq 1 ]]; then
  BUILD_DIR_OVERRIDE="$build_dir" PORT="$start_port" HOST="$host" "$0" --no-export >"$build_dir/.serve-web-check.log" 2>&1 &
  server_pid="$!"
  trap 'kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true; rm -rf "$build_dir"' EXIT

  url=""
  for _ in {1..100}; do
    if [[ -s "$build_dir/.serve-web-check.log" ]]; then
      url="$(sed -n 's/^URL: //p' "$build_dir/.serve-web-check.log" | tail -n 1)"
      if [[ -n "$url" ]]; then
        break
      fi
    fi
    sleep 0.1
  done

  if [[ -z "$url" ]]; then
    cat "$build_dir/.serve-web-check.log" >&2 || true
    echo "serve-web header check failed to start server" >&2
    exit 1
  fi

  for asset in index.html index.js index.wasm index.pck map.png; do
    test -f "$build_dir/${asset}.gz"
    headers="$(curl -fsSI -H "Accept-Encoding: gzip" "${url%/}/${asset}" | tr -d '\r')"
    printf '%s\n' "$headers" | grep -Eq '^Cache-Control: no-store, no-cache, must-revalidate, max-age=0$'
    printf '%s\n' "$headers" | grep -Eq '^Pragma: no-cache$'
    printf '%s\n' "$headers" | grep -Eq '^Expires: 0$'
    printf '%s\n' "$headers" | grep -Eq '^Content-Encoding: gzip$'
  done

  index_body="$(curl -fsS "${url%/}/index.html")"
  printf '%s\n' "$index_body" | grep -Fq 'name="cable-world-web-build"'
  printf '%s\n' "$index_body" | grep -Eq 'index\.js\?v=[^"]+'
  curl -fsS "${url%/}/.web-build.json" | grep -Fq '"build_id"'
  echo "serve-web header check passed at $url"
  exit 0
fi

python3 - "$build_dir" "$host" "$start_port" <<'PY'
import functools
import http.server
import os
import socket
import sys
import urllib.parse

build_dir, host, start_port_text = sys.argv[1:4]
start_port = int(start_port_text)

if start_port < 9000 or start_port > 9999:
    raise SystemExit("PORT must be in the 9000..9999 range")


def find_port(start: int) -> int:
    for port in range(start, 10000):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
            except OSError:
                continue
            return port
    raise SystemExit("No free port in the 9000..9999 range")


class GodotWebHandler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".html": "text/html",
        ".wasm": "application/wasm",
        ".pck": "application/octet-stream",
        ".js": "text/javascript",
        ".json": "application/json",
        ".png": "image/png",
    }

    def send_head(self):
        if self.command in ("GET", "HEAD") and "gzip" in self.headers.get("Accept-Encoding", ""):
            path = self.translate_path(self.path)
            if os.path.isfile(path) and os.path.isfile(path + ".gz"):
                return self._send_gzip_head(path)
        return super().send_head()

    def _send_gzip_head(self, path):
        gz_path = path + ".gz"
        content_type = self.guess_type(path)
        try:
            file = open(gz_path, "rb")
        except OSError:
            self.send_error(404, "File not found")
            return None

        stat = os.fstat(file.fileno())
        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.send_header("Content-Encoding", "gzip")
        self.send_header("Vary", "Accept-Encoding")
        self.send_header("Content-Length", str(stat.st_size))
        self.send_header("Last-Modified", self.date_time_string(stat.st_mtime))
        self.end_headers()
        return file

    def end_headers(self) -> None:
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, format, *args):
        parsed_path = urllib.parse.urlsplit(self.path).path
        super().log_message("%s " + format, parsed_path, *args)


os.chdir(build_dir)
port = find_port(start_port)
if port != start_port:
    print(f"Requested port {start_port} is busy; leaving it untouched and using {port}.", flush=True)
server = http.server.ThreadingHTTPServer((host, port), GodotWebHandler)
print(f"Serving Godot Web build from {build_dir}", flush=True)
print(f"Build stamp: {os.path.join(build_dir, '.web-build.json')}", flush=True)
print(f"URL: http://{host}:{port}/", flush=True)
server.serve_forever()
PY
