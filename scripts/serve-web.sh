#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
build_dir="$root_dir/build/web"
host="${HOST:-127.0.0.1}"
start_port="${PORT:-9000}"
skip_export=0

for arg in "$@"; do
  case "$arg" in
    --no-export)
      skip_export=1
      ;;
    -h|--help)
      cat <<'USAGE'
Usage: scripts/serve-web.sh [--no-export]

Build and serve the Godot Web export locally.

Environment:
  HOST=127.0.0.1  Bind host.
  PORT=9000       First port to try. The script searches up to 9999.

Options:
  --no-export     Serve the existing build/web directory without rebuilding.
USAGE
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

if [[ "$skip_export" -eq 0 ]]; then
  rm -rf "$build_dir"
  mkdir -p "$build_dir"
  godot --headless --path "$root_dir" --import --quit
  godot --headless --path "$root_dir" --export-release Web "$build_dir/index.html"
fi

if [[ ! -f "$build_dir/index.html" ]]; then
  echo "Missing $build_dir/index.html. Run without --no-export first." >&2
  exit 1
fi

find "$build_dir" -maxdepth 1 -type f \( -name '*.wasm' -o -name '*.pck' -o -name '*.js' -o -name '*.html' \) -print0 \
  | while IFS= read -r -d '' file; do
      gzip -9 -kf "$file"
    done

python3 - "$build_dir" "$host" "$start_port" <<'PY'
import functools
import http.server
import os
import socket
import sys

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
        ".wasm": "application/wasm",
        ".pck": "application/octet-stream",
        ".js": "text/javascript",
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
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


os.chdir(build_dir)
port = find_port(start_port)
server = http.server.ThreadingHTTPServer((host, port), GodotWebHandler)
print(f"Serving Godot Web build from {build_dir}", flush=True)
print(f"URL: http://{host}:{port}/", flush=True)
server.serve_forever()
PY
