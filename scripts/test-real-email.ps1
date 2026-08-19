$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

& (Join-Path $PSScriptRoot "validate-environment.ps1")
if ($LASTEXITCODE -ne 0) { throw "Environment validation failed." }

$recipient = Read-Host "Enter the REAL email inbox that should receive the MailTracko test email"
if ($recipient -notmatch '^[^@\s]+@[^@\s]+\.[^@\s]+$') {
    throw "Recipient email format is invalid."
}

Write-Host "Ensuring the MailTracko API is running..." -ForegroundColor Cyan
docker compose up -d --build api
if ($LASTEXITCODE -ne 0) {
    throw "MailTracko API startup failed. Run 'docker compose logs migrate configcheck api --tail=200'. No email was sent."
}

$apiStatus = docker compose ps --status running --services
if ($LASTEXITCODE -ne 0 -or $apiStatus -notcontains "api") {
    throw "MailTracko API is not running. No email was sent."
}

Write-Host "Sending one real transactional email through the same adapter used by verification/reset emails..." -ForegroundColor Cyan
docker compose exec -T api python -m scripts.test_transactional_email --recipient $recipient
if ($LASTEXITCODE -ne 0) {
    throw "Transactional email test failed. Check the API logs."
}

Write-Host "SMTP test submitted successfully to $recipient." -ForegroundColor Green
Write-Host "Check the real inbox (and Spam/Promotions if needed). Mailpit is not used by this stack." -ForegroundColor Green
