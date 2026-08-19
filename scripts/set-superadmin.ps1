$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

function Write-Utf8NoBom([string]$Path, [string]$Value) {
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Value, $utf8NoBom)
}
$envPath = Join-Path (Get-Location) ".env.integration"
if (-not (Test-Path $envPath)) { throw ".env.integration is missing. Run .\\scripts\\configure-local.ps1 first." }
$email = Read-Host "Enter the VERIFIED MailTracko account email to grant Platform Admin access"
if ($email -notmatch '^[^@\s]+@[^@\s]+\.[^@\s]+$') { throw "Email format is invalid." }
$email = $email.Trim().ToLowerInvariant().Replace('"','')
$content = Get-Content $envPath -Raw
$line = "SUPERADMIN_EMAILS=[`"$email`"]"
if ($content -match '(?m)^SUPERADMIN_EMAILS=.*$') { $content = [regex]::Replace($content, '(?m)^SUPERADMIN_EMAILS=.*$', $line) }
else { $content = $content.TrimEnd() + "`r`n$line`r`n" }
Write-Utf8NoBom -Path $envPath -Value $content
Write-Host "Platform Admin configured for $email." -ForegroundColor Green
Write-Host "Restart API and sign in again: docker compose up -d --force-recreate api" -ForegroundColor Cyan
