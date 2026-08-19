$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

function Write-Utf8NoBom([string]$Path, [string]$Value) {
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Value, $utf8NoBom)
}

$envPath = Join-Path (Get-Location) ".env.integration"
$examplePath = Join-Path (Get-Location) ".env.integration.example"
if (-not (Test-Path $examplePath)) {
    throw ".env.integration.example is missing from this package."
}
if (-not (Test-Path $envPath)) {
    Copy-Item $examplePath $envPath
}

function Get-EnvValue([string]$Key, [string]$Content) {
    $match = [regex]::Match($Content, "(?m)^$([regex]::Escape($Key))=(.*)$")
    if ($match.Success) { return $match.Groups[1].Value.Trim() }
    return ""
}

function Set-EnvValue([string]$Key, [string]$Value, [string]$Content) {
    $pattern = "(?m)^$([regex]::Escape($Key))=.*$"
    if ([regex]::IsMatch($Content, $pattern)) {
        return [regex]::Replace($Content, $pattern, "$Key=$Value")
    }
    return $Content.TrimEnd() + "`r`n$Key=$Value`r`n"
}

function New-UrlSafeSecret([int]$byteCount) {
    $bytes = New-Object byte[] $byteCount
    [Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    return [Convert]::ToBase64String($bytes).Replace('+', '-').Replace('/', '_').TrimEnd('=')
}

function New-FernetKey {
    $bytes = New-Object byte[] 32
    [Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    return [Convert]::ToBase64String($bytes).Replace('+', '-').Replace('/', '_')
}

$email = Read-Host "Enter the Gmail address used for MailTracko transactional email"
if ($email -notmatch '^[^@\s]+@[^@\s]+\.[^@\s]+$') {
    throw "The Gmail address format is invalid."
}

$securePassword = Read-Host "Enter the 16-character Google App Password (input is hidden)" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
try {
    $appPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
}
finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}
$appPassword = ($appPassword -replace '\s', '')
if ($appPassword.Length -ne 16) {
    throw "The Google App Password must be exactly 16 characters after spaces are removed."
}

$content = Get-Content $envPath -Raw

# Keep stable local secrets once generated. Re-running this script must not break
# an existing Postgres volume or make already-encrypted provider credentials unreadable.
$databasePassword = Get-EnvValue "POSTGRES_PASSWORD" $content
if (-not $databasePassword -or $databasePassword.StartsWith("CHANGE_ME")) {
    $databasePassword = New-UrlSafeSecret 24
}
$databasePasswordForUrl = [System.Uri]::EscapeDataString($databasePassword)

$secretKey = Get-EnvValue "SECRET_KEY" $content
if (-not $secretKey -or $secretKey.StartsWith("CHANGE_ME") -or $secretKey.Length -lt 32) {
    $secretKey = New-UrlSafeSecret 48
}

$fernetKey = Get-EnvValue "SECRET_ENCRYPTION_KEY" $content
if (-not ($fernetKey -match '^[A-Za-z0-9_-]{43}=$')) {
    $fernetKey = New-FernetKey
}

$updates = [ordered]@{
    ENVIRONMENT = "development"
    APP_URL = "http://127.0.0.1:3000"
    FRONTEND_URL = "http://127.0.0.1:3000"
    CORS_ALLOWED_ORIGINS = '["http://127.0.0.1:3000","http://localhost:3000"]'
    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = "587"
    SMTP_SECURITY = "starttls"
    SMTP_REQUIRE_AUTH = "true"
    SMTP_USERNAME = $email
    SMTP_PASSWORD = $appPassword
    EMAIL_FROM = $email
    EMAIL_FROM_NAME = "MailTracko"
    SECRET_KEY = $secretKey
    SECRET_ENCRYPTION_KEY = $fernetKey
    POSTGRES_USER = "mailtracko"
    POSTGRES_PASSWORD = $databasePassword
    POSTGRES_DB = "mailtracko"
    DATABASE_URL = "postgresql+asyncpg://mailtracko:$databasePasswordForUrl@postgres:5432/mailtracko"
    REDIS_URL = "redis://redis:6379/0"
    DRAMATIQ_BROKER_URL = "redis://redis:6379/0"
    GOOGLE_REDIRECT_URI = "http://127.0.0.1:3000/api/v1/auth/oauth/callback/google"
    GOOGLE_MAIL_REDIRECT_URI = "http://127.0.0.1:3000/api/v1/email-accounts/oauth/callback/google"
    GOOGLE_SHEETS_REDIRECT_URI = "http://127.0.0.1:3000/api/v1/contact-lists/sheets/oauth/callback"
}
foreach ($entry in $updates.GetEnumerator()) {
    $content = Set-EnvValue $entry.Key ([string]$entry.Value) $content
}
Write-Utf8NoBom -Path $envPath -Value $content

Write-Host "MailTracko local configuration now uses real Gmail SMTP." -ForegroundColor Green
Write-Host "Stable database/encryption secrets were preserved when already valid." -ForegroundColor Green
Write-Host "Secrets are stored only in .env.integration. Do not commit or share that file." -ForegroundColor Yellow

docker compose config | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Docker Compose configuration validation failed." }
Write-Host "Docker Compose configuration is valid." -ForegroundColor Green
