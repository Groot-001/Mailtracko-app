$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "Running MailTracko source-integrity checks..." -ForegroundColor Cyan
python scripts/qa_static_checks.py
if ($LASTEXITCODE -ne 0) { throw "Source integrity validation failed." }

python -c "import configparser, pathlib; p=pathlib.Path('backend/alembic.ini'); c=configparser.ConfigParser(); c.read(p, encoding='utf-8'); assert c.has_section('alembic'), 'backend/alembic.ini is missing [alembic]'; print('PASS: alembic.ini structure')"
if ($LASTEXITCODE -ne 0) { throw "Alembic INI validation failed." }

docker compose config | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Docker Compose configuration is invalid." }

Write-Host "Source integrity passed: no NUL/UTF-8 corruption; Python/import checks and Compose config are valid." -ForegroundColor Green
