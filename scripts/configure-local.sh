#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."

[ -f .env.integration.example ] || { echo ".env.integration.example is missing." >&2; exit 1; }
[ -f .env.integration ] || cp .env.integration.example .env.integration

printf 'Enter the Gmail address used for MailTracko transactional email: '
read -r email
case "$email" in *@*.*) ;; *) echo "Invalid email address." >&2; exit 1 ;; esac
printf 'Enter the 16-character Google App Password (input hidden): '
if [ -t 0 ]; then stty -echo; read -r app_password; stty echo; else read -r app_password; fi
printf '
'
app_password=$(printf '%s' "$app_password" | tr -d '[:space:]')
[ "${#app_password}" -eq 16 ] || { echo "Google App Password must be exactly 16 characters." >&2; exit 1; }

python3 - "$email" "$app_password" <<'PY2'
from pathlib import Path
from urllib.parse import quote
import base64, re, secrets, sys
email, password = sys.argv[1:]
p = Path('.env.integration')
t = p.read_text(encoding='utf-8-sig')

def get(key):
    m=re.search(rf'(?m)^{re.escape(key)}=(.*)$', t)
    return m.group(1).strip() if m else ''

def put(text,key,value):
    pattern=rf'(?m)^{re.escape(key)}=.*$'
    if re.search(pattern,text): return re.sub(pattern, f'{key}={value}', text)
    return text.rstrip()+f'\n{key}={value}\n'

db=get('POSTGRES_PASSWORD')
if not db or db.startswith('CHANGE_ME'): db=secrets.token_urlsafe(24)
secret=get('SECRET_KEY')
if not secret or secret.startswith('CHANGE_ME') or len(secret)<32: secret=secrets.token_urlsafe(48)
fernet=get('SECRET_ENCRYPTION_KEY')
if not re.fullmatch(r'[A-Za-z0-9_-]{43}=', fernet or ''):
    fernet=base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
updates={
 'ENVIRONMENT':'development', 'APP_URL':'http://127.0.0.1:3000',
 'FRONTEND_URL':'http://127.0.0.1:3000',
 'CORS_ALLOWED_ORIGINS':'["http://127.0.0.1:3000","http://localhost:3000"]',
 'SMTP_HOST':'smtp.gmail.com','SMTP_PORT':'587','SMTP_SECURITY':'starttls','SMTP_REQUIRE_AUTH':'true',
 'SMTP_USERNAME':email,'SMTP_PASSWORD':password,'EMAIL_FROM':email,'EMAIL_FROM_NAME':'MailTracko',
 'SECRET_KEY':secret,'SECRET_ENCRYPTION_KEY':fernet,
 'POSTGRES_USER':'mailtracko','POSTGRES_PASSWORD':db,'POSTGRES_DB':'mailtracko',
 'DATABASE_URL':f'postgresql+asyncpg://mailtracko:{quote(db, safe="")}@postgres:5432/mailtracko',
 'REDIS_URL':'redis://redis:6379/0','DRAMATIQ_BROKER_URL':'redis://redis:6379/0',
 'GOOGLE_REDIRECT_URI':'http://127.0.0.1:3000/api/v1/auth/oauth/callback/google',
 'GOOGLE_MAIL_REDIRECT_URI':'http://127.0.0.1:3000/api/v1/email-accounts/oauth/callback/google',
 'GOOGLE_SHEETS_REDIRECT_URI':'http://127.0.0.1:3000/api/v1/contact-lists/sheets/oauth/callback',
}
for k,v in updates.items(): t=put(t,k,v)
p.write_text(t, encoding='utf-8')
PY2

docker compose config >/dev/null
echo "MailTracko local configuration is valid and uses real Gmail SMTP."
