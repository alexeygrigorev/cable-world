#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
runtime_dir="$root_dir/tmp/map-review-app"
pid_file="$runtime_dir/server.pid"

if [[ ! -f "$pid_file" ]]; then
  echo "No managed map review app PID file."
  exit 0
fi

pid="$(cat "$pid_file")"
if [[ -z "$pid" ]] || ! kill -0 "$pid" 2>/dev/null; then
  rm -f "$pid_file"
  echo "Removed stale map review app PID file."
  exit 0
fi

kill "$pid"
for _ in {1..50}; do
  if ! kill -0 "$pid" 2>/dev/null; then
    rm -f "$pid_file"
    echo "Stopped map review app PID $pid."
    exit 0
  fi
  sleep 0.1
done

kill -9 "$pid" 2>/dev/null || true
rm -f "$pid_file"
echo "Force-stopped map review app PID $pid."
