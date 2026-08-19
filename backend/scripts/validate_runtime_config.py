"""Fail-fast validation for settings required by a running MailTracko stack.

This validates configuration only. It never prints secret values and never makes a
network connection. The goal is to fail in ``configcheck`` with an actionable
message instead of letting migrations/API workers crash later.
"""
from __future__ import annotations

from cryptography.fernet import Fernet
from sqlalchemy.engine import make_url

from src.core.config.settings import config


def _placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    return (
        not normalized
        or normalized.startswith("your_")
        or normalized.startswith("change_me")
        or normalized.startswith("change-me")
        or (normalized.startswith("<") and normalized.endswith(">"))
        or normalized in {"changeme", "placeholder", "example", "todo"}
    )


def validate_core_runtime() -> list[str]:
    problems: list[str] = []

    if _placeholder(config.SECRET_KEY) or len(config.SECRET_KEY) < 32:
        problems.append("SECRET_KEY must be a long random value")

    try:
        Fernet(config.SECRET_ENCRYPTION_KEY.encode("utf-8"))
    except (TypeError, ValueError):
        problems.append("SECRET_ENCRYPTION_KEY must be a valid Fernet key")

    try:
        database_url = make_url(config.DATABASE_URL)
        if database_url.drivername != "postgresql+asyncpg":
            problems.append("DATABASE_URL must use postgresql+asyncpg")
        if not database_url.username or not database_url.host or not database_url.database:
            problems.append("DATABASE_URL must include database user, host, and database name")
        if database_url.host and "@" in database_url.host:
            problems.append(
                "DATABASE_URL host is malformed; URL-encode special characters in the database password"
            )
    except Exception:
        problems.append("DATABASE_URL is not a valid SQLAlchemy database URL")

    return problems


def validate_real_transactional_email() -> list[str]:
    problems: list[str] = []
    host = config.SMTP_HOST.strip().lower()
    username = config.SMTP_USERNAME.strip()
    password = config.SMTP_PASSWORD.replace(" ", "").strip()
    sender = config.EMAIL_FROM.strip()
    security = config.SMTP_SECURITY.strip().lower()

    if _placeholder(host) or host in {"mailpit", "localhost", "127.0.0.1"}:
        problems.append("SMTP_HOST must point to a real SMTP provider")
    if security not in {"starttls", "ssl"}:
        problems.append("SMTP_SECURITY must be 'starttls' or 'ssl'")
    if config.SMTP_REQUIRE_AUTH and (_placeholder(username) or _placeholder(password)):
        problems.append("SMTP_USERNAME and SMTP_PASSWORD must contain real SMTP credentials")
    if _placeholder(sender) or "@" not in sender:
        problems.append("EMAIL_FROM must be a real sender email address")

    if host == "smtp.gmail.com":
        expected_port = 587 if security == "starttls" else 465
        if config.SMTP_PORT != expected_port:
            problems.append(f"Gmail SMTP with {security} requires port {expected_port}")
        # Gmail App Passwords are 16 characters after spaces are removed.
        if config.SMTP_REQUIRE_AUTH and len(password) != 16:
            problems.append(
                "For smtp.gmail.com, SMTP_PASSWORD must be a 16-character Google App Password"
            )

    return problems


def validate_storage_runtime() -> list[str]:
    if config.ENVIRONMENT.value != "production":
        return []
    if not (
        config.CLOUDINARY_CLOUD_NAME
        and config.CLOUDINARY_API_KEY
        and config.CLOUDINARY_API_SECRET
    ):
        return [
            "Production image uploads require CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET"
        ]
    return []


def main() -> int:
    problems = [
        *validate_core_runtime(),
        *validate_real_transactional_email(),
        *validate_storage_runtime(),
    ]
    if problems:
        print("MailTracko runtime configuration FAILED:")
        for problem in problems:
            print(f" - {problem}")
        print(
            "Run scripts/configure-local.ps1 (Windows) or scripts/configure-local.sh "
            "(Linux/macOS), then configure optional integrations separately."
        )
        return 1

    storage_mode = "cloudinary" if config.CLOUDINARY_CLOUD_NAME else "local-development"
    print(
        "MailTracko runtime configuration OK: "
        f"real SMTP host={config.SMTP_HOST}, port={config.SMTP_PORT}, "
        f"security={config.SMTP_SECURITY}, storage={storage_mode}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
