#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
host="${HOST:-127.0.0.1}"
port="${PORT:-9010}"
runtime_dir="$root_dir/tmp/map-review-app"
pid_file="$runtime_dir/server.pid"
log_file="$runtime_dir/server.log"

if [[ -f "$pid_file" ]]; then
  pid="$(cat "$pid_file")"
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    echo "Managed map review app PID: $pid"
  else
    echo "Managed map review app PID file is stale: $pid_file"
  fi
else
  echo "No managed map review app PID file: $pid_file"
fi

if ss -ltnp "sport = :$port" 2>/dev/null | grep -q ":$port"; then
  echo "Listener on port $port:"
  ss -ltnp "sport = :$port" 2>/dev/null
else
  echo "No listener on port $port"
fi

if curl -fsS "http://$host:$port/api/review-tabs" >/dev/null 2>&1; then
  echo "Review app is reachable: http://$host:$port/"
else
  echo "Review app is not reachable at http://$host:$port/"
fi

if [[ -f "$log_file" ]]; then
  echo "Log: $log_file"
fi
