#!/usr/bin/env sh
set -eu
check() {
  name="$1"
  url="$2"
  attempts=0
  until curl --fail --silent --show-error --max-time 5 "$url" >/dev/null; do
    attempts=$((attempts + 1))
    [ "$attempts" -lt 40 ] || { echo "$name failed at $url" >&2; exit 1; }
    sleep 3
  done
  echo "$name OK"
}
check "Frontend" "http://127.0.0.1:3000/"
check "Backend OpenAPI" "http://127.0.0.1:8000/openapi.json"
docker compose ps
