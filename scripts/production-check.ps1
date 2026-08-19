$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

& (Join-Path $PSScriptRoot "validate-environment.ps1")

Write-Host "Running offline source and integration checks..." -ForegroundColor Cyan
node scripts/frontend_syntax_check.js
python scripts/validate_integration.py
python scripts/validate_endpoint_matrix.py
python scripts/test_api_payload_contracts.py
node scripts/test_frontend_utilities.js
python scripts/validate_lockfiles.py
python -m compileall -q backend/src backend/migrations backend/tests backend/scripts

Write-Host "Removing old project containers..." -ForegroundColor Cyan
docker compose down --remove-orphans

Write-Host "Building frontend from a clean cache..." -ForegroundColor Cyan
docker compose build --no-cache frontend

Write-Host "Building backend services..." -ForegroundColor Cyan
docker compose build api migrate campaign_worker campaign_scheduler

Write-Host "Starting MailTracko..." -ForegroundColor Cyan
docker compose up -d

& (Join-Path $PSScriptRoot "smoke-local.ps1")

docker compose exec -T api alembic current
docker compose exec -T api python -m compileall -q src

$unhealthy = docker compose ps --status unhealthy --quiet
if ($unhealthy) {
    docker compose ps
    throw "One or more services are unhealthy."
}

Write-Host "MailTracko production-base verification passed." -ForegroundColor Green
Write-Host "Complete one manual registration using a different recipient address to confirm Gmail delivery." -ForegroundColor Yellow
