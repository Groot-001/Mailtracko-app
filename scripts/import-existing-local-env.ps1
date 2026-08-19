param(
    [Parameter(Mandatory = $true)]
    [string]$FromProject
)

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$source = Join-Path (Resolve-Path $FromProject) ".env.integration"
$target = Join-Path (Get-Location) ".env.integration"
if (-not (Test-Path $source)) { throw "No .env.integration was found in the supplied project folder." }

$content = Get-Content $source -Raw
if ($content -notmatch '(?m)^POSTGRES_PASSWORD=.+$' -or $content -notmatch '(?m)^SECRET_ENCRYPTION_KEY=.+$') {
    throw "The existing environment is missing database/encryption settings."
}
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($target, $content, $utf8NoBom)
Write-Host "Existing local environment imported without printing any secret values." -ForegroundColor Green
Write-Host "Run .\scripts\configure-local.ps1 next; it preserves valid database/encryption secrets." -ForegroundColor Cyan
