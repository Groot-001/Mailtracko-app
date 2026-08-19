import os
from enum import Enum, StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Final

from cryptography.fernet import Fernet
from dotenv import load_dotenv
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

load_dotenv(BASE_DIR / "env" / ".env")


class Environment(StrEnum, Enum):
    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


environment = os.getenv("ENVIRONMENT", "local").lower()
env_file_path = {
    "local": "env/.env.local",
    "development": "env/.env.development",
    "staging": "env/.env.staging",
    "production": "env/.env.production",
    "testing": "env/.env.test",
}

env_file = env_file_path.get(environment, "env/.env")
env_path = BASE_DIR / env_file


class Settings(BaseSettings):
    # General
    APP_URL: str = "http://localhost:8000"
    ENVIRONMENT: Environment = Environment.LOCAL
    PROJECT_NAME: str = "MailTracko"
    SECRET_KEY: str = "change-me-in-production"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/mailtracko_db"
    )

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Frontend / CORS
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:8000"]

    # Auth
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1
    VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    ACCOUNT_DELETION_GRACE_DAYS: int = 3
    ORGANIZATION_DELETION_GRACE_DAYS: int = 3
    OTP_DIGIT: int = 6

    # OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8080/api/v1/auth/oauth/callback/google"

    # Email Account - OAuth
    GOOGLE_MAIL_CLIENT_ID: str = ""
    GOOGLE_MAIL_CLIENT_SECRET: str = ""
    GOOGLE_MAIL_REDIRECT_URI: str = (
        "http://localhost:8080/api/v1/email-accounts/oauth/callback/google"
    )

    # Google Sheets - OAuth
    GOOGLE_SHEETS_CLIENT_ID: str = ""
    GOOGLE_SHEETS_CLIENT_SECRET: str = ""
    GOOGLE_SHEETS_REDIRECT_URI: str = (
        "http://localhost:8080/api/v1/contact-lists/sheets/oauth/callback"
    )

    # Encryption
    SECRET_ENCRYPTION_KEY: str = ""

    # Email Account limits
    MAX_EMAIL_ACCOUNTS_PER_ORG: int = 1
    PROVIDER_DEFAULT_SENDING_LIMITS: dict[str, int] = {
        "gmail": 500,
        "smtp": 100,
    }
    EMAIL_HEALTH_CHECK_INTERVAL: int = 21600
    EMAIL_STALE_RECONNECT_INTERVAL: int = 3600
    EMAIL_EXPIRED_CLEANUP_INTERVAL: int = 3600

    # SMTP / Transactional Email
    SMTP_HOST: str = "smtp.sendgrid.net"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "apikey"
    SMTP_PASSWORD: str = ""
    SMTP_SECURITY: str = "starttls"  # starttls (587) or ssl (465)
    SMTP_REQUIRE_AUTH: bool = True
    EMAIL_FROM: str = "noreply@mailtracko.com"
    EMAIL_FROM_NAME: str = "MailTracko"
    SMTP_TIMEOUT_SECONDS: int = 30
    SMTP_MAX_RETRIES: int = 3
    SMTP_RETRY_DELAY_SECONDS: float = 1.0

    # SendGrid (alternative to SMTP)
    SENDGRID_API_KEY: str = ""
    # Email Verification (Bouncer)
    EMAIL_VERIFICATION_PROVIDER: str = "bouncer"
    BOUNCER_API_KEY: str = ""
    BOUNCER_API_BASE_URL: str = "https://api.usebouncer.com/v1.1"
    # Dramatiq / Workers
    DRAMATIQ_BROKER_URL: str = "redis://localhost:6379/0"
    OUTBOX_POLLER_INTERVAL_SECONDS: int = 5

    # Warmup
    WARMUP_MAX_DAILY_PER_INBOX: int = 50
    WARMUP_DEFAULT_RAMP_DAYS: int = 21

    # File Storage
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET: str = ""
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    CLOUDINARY_FOLDER: str = "mailtracko"

    # Monitoring
    SENTRY_DSN: str = ""
    PROMETHEUS_ENABLED: bool = True
    LOG_LEVEL: str = "INFO"

    # SaaS administration
    SUPERADMIN_EMAILS: list[str] = []
    PUBLIC_SUPPORT_EMAIL: str = "support@mailtracko.com"
    CHATBOQ_WIDGET_URL: str = ""

    # Billing (Stripe-compatible provider)
    BILLING_ENABLED: bool = False
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_API_VERSION: str = ""
    STRIPE_AUTOMATIC_TAX: bool = False
    STRIPE_COLLECT_BILLING_ADDRESS: bool = True
    STRIPE_PRORATION_BEHAVIOR: str = "create_prorations"
    STRIPE_SUCCESS_URL: str = (
        "http://localhost:5173/organization/account-settings/billing?checkout=success"
    )
    STRIPE_CANCEL_URL: str = (
        "http://localhost:5173/organization/account-settings/billing?checkout=cancelled"
    )
    STRIPE_PORTAL_RETURN_URL: str = (
        "http://localhost:5173/organization/account-settings/billing"
    )

    model_config = SettingsConfigDict(
        env_file=str(env_path), env_file_encoding="utf-8", frozen=True, extra="ignore"
    )

    @staticmethod
    def _looks_like_placeholder(value: str) -> bool:
        normalized = value.strip().lower()
        return (
            not normalized
            or normalized.startswith("your_")
            or normalized.startswith("change_me")
            or normalized.startswith("change-me")
            or (normalized.startswith("<") and normalized.endswith(">"))
            or normalized in {"changeme", "placeholder", "example", "todo"}
        )

    @model_validator(mode="after")
    def _reject_insecure_defaults_in_production(self) -> "Settings":
        if self.ENVIRONMENT != Environment.PRODUCTION:
            return self

        problems: list[str] = []
        if self.DEBUG:
            problems.append("DEBUG must be false")
        if len(self.SECRET_KEY) < 32 or self.SECRET_KEY == "change-me-in-production":
            problems.append("SECRET_KEY must be a long random value")
        try:
            Fernet(self.SECRET_ENCRYPTION_KEY.encode("utf-8"))
        except (TypeError, ValueError):
            problems.append("SECRET_ENCRYPTION_KEY must be a valid Fernet key")
        if "postgres:postgres@localhost" in self.DATABASE_URL:
            problems.append("DATABASE_URL must not use the insecure default")
        if not self.APP_URL.startswith("https://"):
            problems.append("APP_URL must use HTTPS")
        if not self.FRONTEND_URL.startswith("https://"):
            problems.append("FRONTEND_URL must use HTTPS")
        if (
            self._looks_like_placeholder(self.SMTP_HOST)
            or self._looks_like_placeholder(self.SMTP_USERNAME)
            or self._looks_like_placeholder(self.SMTP_PASSWORD)
        ):
            problems.append("SMTP credentials must be configured with real values")
        if self.SMTP_HOST.strip().lower() in {"mailpit", "localhost", "127.0.0.1"}:
            problems.append("Production SMTP_HOST must point to a real mail provider, not a local SMTP catcher")
        if self.SMTP_SECURITY.strip().lower() not in {"starttls", "ssl"}:
            problems.append("SMTP_SECURITY must be 'starttls' or 'ssl'")
        if self.SMTP_HOST.strip().lower() == "smtp.gmail.com":
            expected_port = 587 if self.SMTP_SECURITY.strip().lower() == "starttls" else 465
            if self.SMTP_PORT != expected_port:
                problems.append(
                    f"Gmail SMTP with {self.SMTP_SECURITY} must use port {expected_port}"
                )
        if self.SMTP_REQUIRE_AUTH and (
            self._looks_like_placeholder(self.SMTP_USERNAME)
            or self._looks_like_placeholder(self.SMTP_PASSWORD)
        ):
            problems.append("Authenticated SMTP requires SMTP_USERNAME and SMTP_PASSWORD")
        if self._looks_like_placeholder(self.EMAIL_FROM):
            problems.append("EMAIL_FROM must be configured with a real verified address")
        if not (
            self.CLOUDINARY_CLOUD_NAME
            and self.CLOUDINARY_API_KEY
            and self.CLOUDINARY_API_SECRET
        ):
            problems.append("Cloudinary credentials must be configured for production image uploads")
        if (
            self._looks_like_placeholder(self.GOOGLE_CLIENT_ID)
            or self._looks_like_placeholder(self.GOOGLE_CLIENT_SECRET)
        ):
            problems.append("Google OAuth client ID and secret must be configured")
        if self.BILLING_ENABLED and (
            not self.STRIPE_SECRET_KEY or not self.STRIPE_WEBHOOK_SECRET
        ):
            problems.append(
                "Stripe credentials must be configured when BILLING_ENABLED is true"
            )
        if self.BILLING_ENABLED and not self.STRIPE_SECRET_KEY.startswith("sk_"):
            problems.append("STRIPE_SECRET_KEY must be a Stripe secret key")
        if self.BILLING_ENABLED and not self.STRIPE_WEBHOOK_SECRET.startswith("whsec_"):
            problems.append("STRIPE_WEBHOOK_SECRET must be a Stripe signing secret")
        if self.STRIPE_PUBLISHABLE_KEY and not self.STRIPE_PUBLISHABLE_KEY.startswith(
            "pk_"
        ):
            problems.append("STRIPE_PUBLISHABLE_KEY must be a Stripe publishable key")
        if self.STRIPE_PRORATION_BEHAVIOR not in {
            "always_invoice",
            "create_prorations",
            "none",
        }:
            problems.append("STRIPE_PRORATION_BEHAVIOR is invalid")

        if problems:
            raise ValueError(
                "Production configuration is incomplete: " + "; ".join(problems)
            )
        return self

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == Environment.DEVELOPMENT

    @property
    def is_staging(self) -> bool:
        return self.ENVIRONMENT == Environment.STAGING

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == Environment.TESTING

    @property
    def is_local(self) -> bool:
        return self.ENVIRONMENT == Environment.LOCAL

    def __str__(self) -> str:
        # Never serialize credentials or encryption material into logs.
        return (
            "Settings("
            f"environment={self.ENVIRONMENT.value}, "
            f"project_name={self.PROJECT_NAME!r}, "
            f"app_url={self.APP_URL!r}, "
            f"smtp_host={self.SMTP_HOST!r}, "
            f"smtp_port={self.SMTP_PORT}"
            ")"
        )

    def __repr__(self) -> str:
        return str(self)


@lru_cache
def get_settings() -> Settings:
    return Settings()


config: Final[Settings] = get_settings()

