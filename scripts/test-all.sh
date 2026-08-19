#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
node scripts/frontend_syntax_check.js
node scripts/check-unused-typescript.js
python3 scripts/validate_integration.py
python3 scripts/validate_endpoint_matrix.py
python3 scripts/test_api_payload_contracts.py
node scripts/test_frontend_utilities.js
python3 scripts/validate_lockfiles.py
(
  cd backend
  python3 -m compileall -q src migrations tests scripts
  python3 -m pytest -q
  alembic heads
)
if command -v docker >/dev/null 2>&1; then
  docker compose config >/dev/null
  echo "Docker Compose configuration passed."
fi
printf '%s\n' 'All integration tests passed.'
