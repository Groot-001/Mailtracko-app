$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
if (-not (Test-Path ".env.integration")) {
    throw ".env.integration is missing. Run .\scripts\configure-local.ps1 first."
}

python scripts/validate_real_smtp_env.py
if ($LASTEXITCODE -ne 0) {
    throw "Real Gmail SMTP environment validation failed."
}

docker compose config | Out-Null
Write-Host "Environment and Docker Compose validation passed." -ForegroundColor Green
