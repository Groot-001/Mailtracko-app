param(
    [switch]$ResetData
)

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

& (Join-Path $PSScriptRoot "verify-source-integrity.ps1")
if ($LASTEXITCODE -ne 0) { throw "Source integrity validation failed." }

if ($ResetData) {
    $answer = Read-Host "ResetData will DELETE the local MailTracko PostgreSQL/Redis/upload volumes. Type RESET to continue"
    if ($answer -ne "RESET") { throw "Local data reset cancelled." }
    docker compose down -v --remove-orphans
} else {
    docker compose down --remove-orphans
}
if ($LASTEXITCODE -ne 0) { throw "Could not stop the existing Compose stack." }

docker compose build --no-cache
if ($LASTEXITCODE -ne 0) { throw "Docker image build failed." }

docker compose up -d
if ($LASTEXITCODE -ne 0) { throw "Docker Compose startup failed. Run docker compose logs --tail=200 configcheck migrate api frontend campaign_worker campaign_scheduler." }

docker compose ps -a
Write-Host "Clean rebuild submitted. Wait for API/frontend health checks, then run .\scripts\smoke-local.ps1." -ForegroundColor Green
