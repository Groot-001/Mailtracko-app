#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
[ -f .env.integration ] || { echo ".env.integration is missing. Run ./scripts/configure-local.sh." >&2; exit 1; }
python3 scripts/validate_real_smtp_env.py
docker compose config >/dev/null
echo "Environment and Docker Compose validation passed."
