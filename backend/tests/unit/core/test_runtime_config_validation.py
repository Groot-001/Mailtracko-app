from types import SimpleNamespace

from cryptography.fernet import Fernet

from scripts import validate_runtime_config as runtime


def _settings(**overrides):
    base = {
        "SECRET_KEY": "s" * 64,
        "SECRET_ENCRYPTION_KEY": Fernet.generate_key().decode(),
        "DATABASE_URL": "postgresql+asyncpg://mailtracko:Postgres%40123@postgres:5432/mailtracko",
        "SMTP_HOST": "smtp.gmail.com",
        "SMTP_PORT": 587,
        "SMTP_USERNAME": "sender@example.com",
        "SMTP_PASSWORD": "abcdefghijklmnop",
        "SMTP_SECURITY": "starttls",
        "SMTP_REQUIRE_AUTH": True,
        "EMAIL_FROM": "sender@example.com",
        "ENVIRONMENT": SimpleNamespace(value="development"),
        "CLOUDINARY_CLOUD_NAME": "",
        "CLOUDINARY_API_KEY": "",
        "CLOUDINARY_API_SECRET": "",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_core_runtime_accepts_encoded_database_password_and_fernet(monkeypatch) -> None:
    monkeypatch.setattr(runtime, "config", _settings())
    assert runtime.validate_core_runtime() == []


def test_core_runtime_rejects_invalid_fernet_and_malformed_database_host(monkeypatch) -> None:
    monkeypatch.setattr(
        runtime,
        "config",
        _settings(
            SECRET_ENCRYPTION_KEY="not-a-fernet-key",
            DATABASE_URL="postgresql+asyncpg://mailtracko:Postgres@123@postgres:5432/mailtracko",
        ),
    )
    problems = runtime.validate_core_runtime()
    assert "SECRET_ENCRYPTION_KEY must be a valid Fernet key" in problems
    assert any("URL-encode special characters" in problem for problem in problems)


def test_production_storage_requires_cloudinary(monkeypatch) -> None:
    monkeypatch.setattr(
        runtime,
        "config",
        _settings(ENVIRONMENT=SimpleNamespace(value="production")),
    )
    assert runtime.validate_storage_runtime()


def test_development_storage_allows_local_fallback(monkeypatch) -> None:
    monkeypatch.setattr(runtime, "config", _settings())
    assert runtime.validate_storage_runtime() == []
