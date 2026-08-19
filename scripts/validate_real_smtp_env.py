"""Validate the local Gmail SMTP environment without revealing credentials."""
from __future__ import annotations

from pathlib import Path

ENV_PATH = Path('.env.integration')


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding='utf-8-sig').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        values[key.strip()] = value.strip()
    return values


def is_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    return (
        not normalized
        or normalized.startswith('your_')
        or normalized.startswith('change_me')
        or normalized.startswith('change-me')
        or (normalized.startswith('<') and normalized.endswith('>'))
        or normalized in {'changeme', 'placeholder', 'example', 'todo'}
    )


def main() -> int:
    if not ENV_PATH.exists():
        print('ERROR: .env.integration is missing. Run scripts/configure-local.ps1 first.')
        return 1

    env = load_env(ENV_PATH)
    problems: list[str] = []
    host = env.get('SMTP_HOST', '').lower()
    port = env.get('SMTP_PORT', '')
    security = env.get('SMTP_SECURITY', '').lower()
    require_auth = env.get('SMTP_REQUIRE_AUTH', '').lower()
    username = env.get('SMTP_USERNAME', '')
    password = env.get('SMTP_PASSWORD', '').replace(' ', '')
    sender = env.get('EMAIL_FROM', '')

    if host != 'smtp.gmail.com':
        problems.append('SMTP_HOST must be smtp.gmail.com for this real-Gmail package')
    if port != '587':
        problems.append('SMTP_PORT must be 587')
    if security != 'starttls':
        problems.append('SMTP_SECURITY must be starttls')
    if require_auth not in {'true', '1', 'yes'}:
        problems.append('SMTP_REQUIRE_AUTH must be true')
    if is_placeholder(username) or '@' not in username:
        problems.append('SMTP_USERNAME must be your real Gmail/Google Workspace address')
    if is_placeholder(password) or len(password) != 16:
        problems.append('SMTP_PASSWORD must be a 16-character Google App Password')
    if is_placeholder(sender) or '@' not in sender:
        problems.append('EMAIL_FROM must be a real sender address')
    if username and sender and username.lower() != sender.lower():
        problems.append('For the local Gmail test, EMAIL_FROM must match SMTP_USERNAME')

    for key in ('SECRET_KEY', 'SECRET_ENCRYPTION_KEY', 'POSTGRES_PASSWORD', 'DATABASE_URL'):
        if is_placeholder(env.get(key, '')):
            problems.append(f'{key} still contains a placeholder')

    if problems:
        print('Real Gmail SMTP configuration FAILED:')
        for problem in problems:
            print(f' - {problem}')
        print('Run scripts/configure-local.ps1 (Windows) or scripts/configure-local.sh (Linux/macOS).')
        return 1

    print('Real Gmail SMTP configuration passed (credentials present; secret values were not printed).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
