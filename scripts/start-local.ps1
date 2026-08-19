$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
& (Join-Path $PSScriptRoot "validate-environment.ps1")
docker compose up -d --build
docker compose ps
Write-Host "MailTracko is starting at http://127.0.0.1:3000" -ForegroundColor Green
