$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

function Write-Utf8NoBom([string]$Path, [string]$Value) {
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Value, $utf8NoBom)
}
$envPath = Join-Path (Get-Location) ".env.integration"
if (-not (Test-Path $envPath)) { throw ".env.integration is missing. Run .\\scripts\\configure-local.ps1 first." }

function Set-EnvValue([string]$Key, [string]$Value, [string]$Content) {
    $pattern = "(?m)^$([regex]::Escape($Key))=.*$"
    if ([regex]::IsMatch($Content, $pattern)) { return [regex]::Replace($Content, $pattern, "$Key=$Value") }
    return $Content.TrimEnd() + "`r`n$Key=$Value`r`n"
}
function Read-OptionalSecret([string]$Prompt) {
    $secure = Read-Host "$Prompt (hidden; press Enter to keep current/blank)" -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}

$content = Get-Content $envPath -Raw
Write-Host "Configure optional MailTracko integrations. Secret values are never printed." -ForegroundColor Cyan

$googleClientId = Read-Host "Google Web OAuth Client ID (press Enter to leave unchanged)"
$googleClientSecret = Read-OptionalSecret "Google Web OAuth Client Secret"
if ($googleClientId.Trim()) {
    $content = Set-EnvValue "GOOGLE_CLIENT_ID" $googleClientId.Trim() $content
    $content = Set-EnvValue "GOOGLE_MAIL_CLIENT_ID" $googleClientId.Trim() $content
    $content = Set-EnvValue "GOOGLE_SHEETS_CLIENT_ID" $googleClientId.Trim() $content
}
if ($googleClientSecret.Trim()) {
    $content = Set-EnvValue "GOOGLE_CLIENT_SECRET" $googleClientSecret.Trim() $content
    $content = Set-EnvValue "GOOGLE_MAIL_CLIENT_SECRET" $googleClientSecret.Trim() $content
    $content = Set-EnvValue "GOOGLE_SHEETS_CLIENT_SECRET" $googleClientSecret.Trim() $content
}

$content = Set-EnvValue "GOOGLE_REDIRECT_URI" "http://127.0.0.1:3000/api/v1/auth/oauth/callback/google" $content
$content = Set-EnvValue "GOOGLE_MAIL_REDIRECT_URI" "http://127.0.0.1:3000/api/v1/email-accounts/oauth/callback/google" $content
$content = Set-EnvValue "GOOGLE_SHEETS_REDIRECT_URI" "http://127.0.0.1:3000/api/v1/contact-lists/sheets/oauth/callback" $content

$bouncer = Read-OptionalSecret "Bouncer API key"
if ($bouncer.Trim()) { $content = Set-EnvValue "BOUNCER_API_KEY" $bouncer.Trim() $content }

$cloudinaryCloud = Read-Host "Cloudinary cloud name (press Enter to use local development storage)"
$cloudinaryKey = Read-Host "Cloudinary API key (press Enter to leave unchanged)"
$cloudinarySecret = Read-OptionalSecret "Cloudinary API secret"
if ($cloudinaryCloud.Trim()) { $content = Set-EnvValue "CLOUDINARY_CLOUD_NAME" $cloudinaryCloud.Trim() $content }
if ($cloudinaryKey.Trim()) { $content = Set-EnvValue "CLOUDINARY_API_KEY" $cloudinaryKey.Trim() $content }
if ($cloudinarySecret.Trim()) { $content = Set-EnvValue "CLOUDINARY_API_SECRET" $cloudinarySecret.Trim() $content }

$adminEmail = Read-Host "Verified MailTracko account email to grant Platform Admin (press Enter to leave unchanged)"
if ($adminEmail.Trim()) {
    if ($adminEmail -notmatch '^[^@\s]+@[^@\s]+\.[^@\s]+$') { throw "Platform Admin email format is invalid." }
    $normalized = $adminEmail.Trim().ToLowerInvariant().Replace('"','')
    $content = Set-EnvValue "SUPERADMIN_EMAILS" "[`"$normalized`"]" $content
}

Write-Utf8NoBom -Path $envPath -Value $content

docker compose config | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Docker Compose configuration validation failed." }

Write-Host "Optional integration configuration saved." -ForegroundColor Green
Write-Host "Register these exact Google OAuth redirect URIs in Google Cloud:" -ForegroundColor Yellow
Write-Host "  http://127.0.0.1:3000/api/v1/auth/oauth/callback/google"
Write-Host "  http://127.0.0.1:3000/api/v1/email-accounts/oauth/callback/google"
Write-Host "  http://127.0.0.1:3000/api/v1/contact-lists/sheets/oauth/callback"
Write-Host "Local logo/profile uploads fall back to persistent Docker storage when Cloudinary is blank; production requires Cloudinary." -ForegroundColor Yellow
Write-Host "Recreate the API after changing integration settings: docker compose up -d --force-recreate api" -ForegroundColor Cyan
