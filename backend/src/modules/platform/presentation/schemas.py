from datetime import datetime
from typing import Any, Literal

from pydantic import Field, HttpUrl, model_validator

from src.shared.schemas.base_schema import BaseSchema, DomainEmail, field_validator


class CheckoutRequest(BaseSchema):
    plan_code: str = Field(min_length=1, max_length=80)
    billing_cycle: Literal["monthly", "annual"] = "monthly"
    promotion_code: str | None = Field(default=None, max_length=80)


class BillingProfileRequest(BaseSchema):
    billing_email: DomainEmail | None = None
    company_name: str | None = Field(default=None, max_length=255)
    tax_id: str | None = Field(default=None, max_length=100)
    address: dict[str, str] | None = None


class SupportTicketCreateRequest(BaseSchema):
    subject: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=10, max_length=20000)
    category: str = Field(default="general", min_length=1, max_length=100)
    priority: Literal["low", "normal", "high", "urgent"] = "normal"


class SupportTicketMessageRequest(BaseSchema):
    body: str = Field(min_length=1, max_length=20000)
    attachments: list[str] = Field(default_factory=list, max_length=10)
    is_internal: bool = False


class SupportTicketUpdateRequest(BaseSchema):
    status: (
        Literal["open", "in_progress", "waiting_customer", "resolved", "closed"] | None
    ) = None
    priority: Literal["low", "normal", "high", "urgent"] | None = None
    assignee_user_uuid: str | None = None
    resolution: str | None = Field(default=None, max_length=20000)


class SupportArticleRequest(BaseSchema):
    slug: str = Field(
        min_length=2, max_length=180, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    title: str = Field(min_length=2, max_length=255)
    category: str = Field(min_length=1, max_length=100)
    summary: str | None = Field(default=None, max_length=1000)
    content: str = Field(min_length=1, max_length=100000)
    tags: list[str] = Field(default_factory=list, max_length=30)
    is_published: bool = False
    display_order: int = Field(default=0, ge=0)


class NotificationPreferenceRequest(BaseSchema):
    email_enabled: bool
    in_app_enabled: bool
    categories: dict[str, bool] = Field(default_factory=dict)


class ApiKeyCreateRequest(BaseSchema):
    name: str = Field(min_length=2, max_length=50)
    scopes: list[str] = Field(default_factory=list, max_length=30)
    expires_at: datetime | None = None


class WebhookCreateRequest(BaseSchema):
    name: str = Field(min_length=2, max_length=50)
    url: HttpUrl
    events: list[str] = Field(min_length=1, max_length=30)


class WebhookUpdateRequest(BaseSchema):
    name: str | None = Field(default=None, min_length=2, max_length=50)
    url: HttpUrl | None = None
    events: list[str] | None = Field(default=None, min_length=1, max_length=30)
    is_active: bool | None = None


class SuppressionCreateRequest(BaseSchema):
    email: DomainEmail
    reason: str = Field(min_length=2, max_length=100)


class MemberRoleUpdateRequest(BaseSchema):
    role_code: Literal["admin", "member"]


class MemberPermissionsUpdateRequest(BaseSchema):
    permissions: dict[str, bool] = Field(default_factory=dict)


class PlanRequest(BaseSchema):
    code: str = Field(
        min_length=2, max_length=80, pattern=r"^[a-z0-9]+(?:_[a-z0-9]+)*$"
    )
    name: str = Field(min_length=2, max_length=160)
    description: str | None = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    monthly_price_cents: int = Field(default=0, ge=0)
    annual_price_cents: int = Field(default=0, ge=0)
    stripe_monthly_price_id: str | None = Field(default=None, max_length=255)
    stripe_annual_price_id: str | None = Field(default=None, max_length=255)
    trial_days: int = Field(default=0, ge=0, le=365)
    limits: dict[str, int] = Field(default_factory=dict)
    features: list[str] = Field(default_factory=list)
    is_active: bool = True
    is_default: bool = False
    display_order: int = Field(default=0, ge=0)

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: Any) -> str:
        return str(value).strip().upper()

    @field_validator("stripe_monthly_price_id", "stripe_annual_price_id")
    @classmethod
    def validate_stripe_price_id(cls, value: str | None) -> str | None:
        normalized = value.strip() if value else None
        if normalized and not normalized.startswith("price_"):
            raise ValueError("Stripe recurring Price IDs must start with price_")
        return normalized


class PromotionRequest(BaseSchema):
    code: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=160)
    percent_off: int | None = Field(default=None, ge=1, le=100)
    amount_off_cents: int | None = Field(default=None, ge=1)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    provider_coupon_id: str | None = Field(default=None, max_length=255)
    max_redemptions: int | None = Field(default=None, ge=1)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    is_active: bool = True

    @model_validator(mode="after")
    def validate_discount(self) -> "PromotionRequest":
        if bool(self.percent_off) == bool(self.amount_off_cents):
            raise ValueError("Set exactly one of percent_off or amount_off_cents")
        if self.amount_off_cents and not self.currency:
            raise ValueError("currency is required for an amount discount")
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be later than starts_at")
        return self


class RefundRequest(BaseSchema):
    amount_cents: int | None = Field(default=None, ge=1)
    reason: Literal["duplicate", "fraudulent", "requested_by_customer"] | None = None


class ProviderConfigRequest(BaseSchema):
    provider: str = Field(min_length=2, max_length=100)
    config_key: str = Field(min_length=2, max_length=160)
    value: str = Field(min_length=1, max_length=20000)
    is_secret: bool = True
    is_active: bool = True


class FeatureFlagRequest(BaseSchema):
    key: str = Field(
        min_length=2, max_length=160, pattern=r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$"
    )
    description: str | None = None
    is_enabled: bool = False
    rollout_percentage: int = Field(default=100, ge=0, le=100)
    organization_overrides: dict[str, bool] = Field(default_factory=dict)


class MaintenanceRequest(BaseSchema):
    enabled: bool
    message: str = Field(
        default="MailTracko is undergoing scheduled maintenance.", max_length=500
    )
    ends_at: datetime | None = None


class DomainHealthRequest(BaseSchema):
    domain: str = Field(min_length=3, max_length=255)
    dkim_selectors: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("domain", mode="before")
    @classmethod
    def normalize_domain(cls, value: Any) -> str:
        text = str(value).strip().lower()
        for prefix in ("https://", "http://"):
            text = text.removeprefix(prefix)
        return text.split("/", 1)[0].rstrip(".")


class AbuseEventRequest(BaseSchema):
    organization_uuid: str
    campaign_uuid: str | None = None
    severity: Literal["low", "medium", "high", "critical"]
    reason: str = Field(min_length=5, max_length=20000)
    metrics: dict[str, Any] = Field(default_factory=dict)


class AdminStatusRequest(BaseSchema):
    status: Literal["active", "suspended"]


class AdminUserStatusRequest(BaseSchema):
    is_active: bool
