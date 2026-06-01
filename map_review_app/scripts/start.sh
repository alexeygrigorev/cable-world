#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
host="${HOST:-127.0.0.1}"
port="${PORT:-9010}"
runtime_dir="$root_dir/tmp/map-review-app"
pid_file="$runtime_dir/server.pid"
log_file="$runtime_dir/server.log"

mkdir -p "$runtime_dir"

if [[ -f "$pid_file" ]]; then
  pid="$(cat "$pid_file")"
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    echo "Map review app is already running: http://$host:$port/ (PID $pid)"
    exit 0
  fi
  rm -f "$pid_file"
fi

if ss -ltnp "sport = :$port" 2>/dev/null | grep -q ":$port"; then
  echo "Port $port is already in use and is not managed by $pid_file." >&2
  echo "Run map_review_app/scripts/status.sh to inspect it, or stop that process before starting managed review app." >&2
  exit 1
fi

cd "$root_dir"
setsid -f env HOST="$host" PORT="$port" node map_review_app/server.mjs >"$log_file" 2>&1

pid=""
for _ in {1..50}; do
  pid="$(
    ss -ltnp "sport = :$port" 2>/dev/null \
      | sed -n 's/.*pid=\([0-9][0-9]*\).*/\1/p' \
      | head -n 1
  )"
  if [[ -n "$pid" ]]; then
    break
  fi
  sleep 0.1
done

if [[ -z "$pid" ]]; then
  cat "$log_file" >&2 || true
  echo "Map review app did not bind port $port." >&2
  exit 1
fi
printf '%s\n' "$pid" >"$pid_file"

for _ in {1..50}; do
  if curl -fsS "http://$host:$port/api/review-tabs" >/dev/null 2>&1; then
    echo "Map review app: http://$host:$port/"
    echo "PID: $pid"
    echo "Log: $log_file"
    exit 0
  fi
  sleep 0.1
done

cat "$log_file" >&2 || true
echo "Map review app did not become ready on http://$host:$port/" >&2
exit 1
