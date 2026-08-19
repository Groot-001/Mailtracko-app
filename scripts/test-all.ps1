$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
node scripts/frontend_syntax_check.js
node scripts/check-unused-typescript.js
python scripts/validate_integration.py
python scripts/validate_endpoint_matrix.py
python scripts/test_api_payload_contracts.py
node scripts/test_frontend_utilities.js
python scripts/validate_lockfiles.py
Push-Location backend
try {
    python -m compileall -q src migrations tests scripts
    python -m pytest -q
    alembic heads
}
finally {
    Pop-Location
}
if (Get-Command docker -ErrorAction SilentlyContinue) {
    docker compose config | Out-Null
    Write-Host "Docker Compose configuration passed."
}
Write-Host "All integration tests passed." -ForegroundColor Green
