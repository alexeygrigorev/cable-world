#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
build_dir="${BUILD_DIR_OVERRIDE:-$root_dir/build/web}"
host="${HOST:-127.0.0.1}"
port="${PORT:-9000}"
pid_file="$build_dir/.serve-web.pid"

if [[ -f "$pid_file" ]]; then
  pid="$(cat "$pid_file")"
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    echo "Managed server PID: $pid"
  else
    echo "Managed server PID file is stale: $pid_file"
  fi
else
  echo "No managed server PID file: $pid_file"
fi

listeners="$(ss -ltnp "sport = :$port" 2>/dev/null || true)"
if [[ -n "$listeners" ]]; then
  echo "Listener on port $port:"
  echo "$listeners"
else
  echo "No listener on port $port"
fi

url="http://$host:$port/.web-build.json"
if curl -fsS "$url" >/tmp/cable-world-web-status.json 2>/dev/null; then
  echo "Build stamp at http://$host:$port/:"
  cat /tmp/cable-world-web-status.json
  echo
else
  echo "No readable build stamp at $url"
fi
