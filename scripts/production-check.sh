#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
./scripts/validate-environment.sh
node scripts/frontend_syntax_check.js
python3 scripts/validate_integration.py
python3 scripts/validate_endpoint_matrix.py
python3 scripts/test_api_payload_contracts.py
node scripts/test_frontend_utilities.js
python3 scripts/validate_lockfiles.py
python3 -m compileall -q backend/src backend/migrations backend/tests backend/scripts
docker compose down --remove-orphans
docker compose build --no-cache frontend
docker compose build api migrate campaign_worker campaign_scheduler
docker compose up -d
./scripts/smoke-local.sh
docker compose exec -T api alembic current
docker compose exec -T api python -m compileall -q src
[ -z "$(docker compose ps --status unhealthy --quiet)" ] || { docker compose ps; exit 1; }
echo "MailTracko production-base verification passed."
echo "Complete one manual registration using another recipient address to confirm Gmail delivery."
