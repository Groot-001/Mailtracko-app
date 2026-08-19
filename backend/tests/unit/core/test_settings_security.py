import pytest
from cryptography.fernet import Fernet
from pydantic import ValidationError

from src.core.config.settings import Environment, Settings

TEST_FERNET_KEY = Fernet.generate_key().decode()
PRODUCTION_STORAGE = {
    "CLOUDINARY_CLOUD_NAME": "mailtracko-test",
    "CLOUDINARY_API_KEY": "cloudinary-test-key",
    "CLOUDINARY_API_SECRET": "cloudinary-test-secret",
}


def test_settings_repr_never_contains_credentials():
    settings = Settings(
        ENVIRONMENT=Environment.DEVELOPMENT,
        SECRET_KEY="s" * 64,
        SECRET_ENCRYPTION_KEY=TEST_FERNET_KEY,
        SMTP_USERNAME="sender@example.com",
        SMTP_PASSWORD="super-secret-app-password",
        EMAIL_FROM="sender@example.com",
    )

    rendered = repr(settings)

    assert "super-secret-app-password" not in rendered
    assert "sender@example.com" not in rendered
    assert "SECRET_ENCRYPTION_KEY" not in rendered
    assert "environment=development" in rendered


def test_production_settings_reject_placeholders_and_http_urls():
    with pytest.raises(ValidationError, match="Production configuration is incomplete"):
        Settings(
            ENVIRONMENT=Environment.PRODUCTION,
            DEBUG=False,
            SECRET_KEY="s" * 64,
            SECRET_ENCRYPTION_KEY="CHANGE_ME_WITH_A_FERNET_KEY",
            DATABASE_URL="postgresql+asyncpg://mailtracko:secret@postgres:5432/mailtracko",
            APP_URL="http://app.example.com",
            FRONTEND_URL="http://app.example.com",
            SMTP_HOST="smtp.gmail.com",
            SMTP_PORT=587,
            SMTP_USERNAME="YOUR_GMAIL_ADDRESS@gmail.com",
            SMTP_PASSWORD="YOUR_16_CHARACTER_GOOGLE_APP_PASSWORD",
            EMAIL_FROM="YOUR_GMAIL_ADDRESS@gmail.com",
        )


def test_production_settings_accept_secure_gmail_configuration():
    settings = Settings(
        ENVIRONMENT=Environment.PRODUCTION,
        DEBUG=False,
        SECRET_KEY="s" * 64,
        SECRET_ENCRYPTION_KEY=TEST_FERNET_KEY,
        DATABASE_URL="postgresql+asyncpg://mailtracko:secret@postgres:5432/mailtracko",
        APP_URL="https://app.example.com",
        FRONTEND_URL="https://app.example.com",
        CORS_ALLOWED_ORIGINS=["https://app.example.com"],
        SMTP_HOST="smtp.gmail.com",
        SMTP_PORT=587,
        SMTP_USERNAME="sender@example.com",
        SMTP_PASSWORD="valid-google-app-password",
        EMAIL_FROM="sender@example.com",
        GOOGLE_CLIENT_ID="google-client-id.apps.googleusercontent.com",
        GOOGLE_CLIENT_SECRET="google-client-secret",
        **PRODUCTION_STORAGE,
    )

    assert settings.is_production is True
    assert settings.SMTP_PORT == 587


def test_billing_configuration_rejects_invalid_stripe_credentials_in_production():
    with pytest.raises(ValidationError, match="STRIPE_SECRET_KEY"):
        Settings(
            ENVIRONMENT=Environment.PRODUCTION,
            DEBUG=False,
            SECRET_KEY="s" * 64,
            SECRET_ENCRYPTION_KEY=TEST_FERNET_KEY,
            DATABASE_URL="postgresql+asyncpg://mailtracko:secret@postgres:5432/mailtracko",
            APP_URL="https://app.example.com",
            FRONTEND_URL="https://app.example.com",
            CORS_ALLOWED_ORIGINS=["https://app.example.com"],
            SMTP_HOST="smtp.gmail.com",
            SMTP_PORT=587,
            SMTP_USERNAME="sender@example.com",
            SMTP_PASSWORD="valid-google-app-password",
            EMAIL_FROM="sender@example.com",
            GOOGLE_CLIENT_ID="google-client-id.apps.googleusercontent.com",
            GOOGLE_CLIENT_SECRET="google-client-secret",
            **PRODUCTION_STORAGE,
            BILLING_ENABLED=True,
            STRIPE_SECRET_KEY="invalid",
            STRIPE_WEBHOOK_SECRET="also-invalid",
        )


def test_billing_configuration_rejects_unknown_proration_behavior():
    with pytest.raises(ValidationError, match="STRIPE_PRORATION_BEHAVIOR"):
        Settings(
            ENVIRONMENT=Environment.PRODUCTION,
            DEBUG=False,
            SECRET_KEY="s" * 64,
            SECRET_ENCRYPTION_KEY=TEST_FERNET_KEY,
            DATABASE_URL="postgresql+asyncpg://mailtracko:secret@postgres:5432/mailtracko",
            APP_URL="https://app.example.com",
            FRONTEND_URL="https://app.example.com",
            CORS_ALLOWED_ORIGINS=["https://app.example.com"],
            SMTP_HOST="smtp.gmail.com",
            SMTP_PORT=587,
            SMTP_USERNAME="sender@example.com",
            SMTP_PASSWORD="valid-google-app-password",
            EMAIL_FROM="sender@example.com",
            GOOGLE_CLIENT_ID="google-client-id.apps.googleusercontent.com",
            GOOGLE_CLIENT_SECRET="google-client-secret",
            **PRODUCTION_STORAGE,
            STRIPE_PRORATION_BEHAVIOR="unexpected",
        )


def test_production_settings_reject_angle_bracket_example_placeholders():
    with pytest.raises(ValidationError, match="SMTP credentials"):
        Settings(
            ENVIRONMENT=Environment.PRODUCTION,
            DEBUG=False,
            SECRET_KEY="s" * 64,
            SECRET_ENCRYPTION_KEY=TEST_FERNET_KEY,
            DATABASE_URL="postgresql+asyncpg://mailtracko:secret@postgres:5432/mailtracko",
            APP_URL="https://app.example.com",
            FRONTEND_URL="https://app.example.com",
            CORS_ALLOWED_ORIGINS=["https://app.example.com"],
            SMTP_HOST="smtp.gmail.com",
            SMTP_PORT=587,
            SMTP_USERNAME="<gmail-or-google-workspace-address>",
            SMTP_PASSWORD="<google-app-password>",
            EMAIL_FROM="<same-verified-address>",
            GOOGLE_CLIENT_ID="<google-auth-client-id>",
            GOOGLE_CLIENT_SECRET="<google-auth-client-secret>",
        )
