#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
build_dir="${BUILD_DIR_OVERRIDE:-$root_dir/build/web}"
pid_file="$build_dir/.serve-web.pid"

if [[ ! -f "$pid_file" ]]; then
  echo "No managed Web server PID file: $pid_file"
  exit 0
fi

pid="$(cat "$pid_file")"
if [[ -z "$pid" ]]; then
  rm -f "$pid_file"
  echo "Removed empty Web server PID file: $pid_file"
  exit 0
fi

if ! kill -0 "$pid" 2>/dev/null; then
  rm -f "$pid_file"
  echo "Removed stale Web server PID file for PID $pid"
  exit 0
fi

kill "$pid"
for _ in {1..50}; do
  if ! kill -0 "$pid" 2>/dev/null; then
    rm -f "$pid_file"
    echo "Stopped Web server PID $pid"
    exit 0
  fi
  sleep 0.1
done

echo "Web server PID $pid did not stop after TERM" >&2
exit 1
