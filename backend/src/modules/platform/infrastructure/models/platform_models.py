from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.model.base_model import BaseModel


class BillingPlanModel(BaseModel):
    __tablename__ = "billing_plans"

    code: Mapped[str] = mapped_column(
        String(80), nullable=False, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    monthly_price_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    annual_price_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stripe_monthly_price_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    stripe_annual_price_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    trial_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    limits: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    features: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class SubscriptionModel(BaseModel):
    __tablename__ = "billing_subscriptions"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("org_organizations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("billing_plans.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    promotion_id: Mapped[int | None] = mapped_column(
        ForeignKey("billing_promotions.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(40), nullable=False, default="trialing", index=True
    )
    billing_cycle: Mapped[str] = mapped_column(
        String(20), nullable=False, default="monthly"
    )
    seats: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    provider_customer_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True
    )
    provider_subscription_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True
    )
    trial_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    current_period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    canceled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class BillingProfileModel(BaseModel):
    __tablename__ = "billing_profiles"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("org_organizations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    billing_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tax_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    card_brand: Mapped[str | None] = mapped_column(String(50), nullable=True)
    card_last4: Mapped[str | None] = mapped_column(String(4), nullable=True)
    card_exp_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    card_exp_year: Mapped[int | None] = mapped_column(Integer, nullable=True)


class InvoiceModel(BaseModel):
    __tablename__ = "billing_invoices"
    __table_args__ = (
        Index("ix_billing_invoices_org_status", "organization_id", "status"),
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("org_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subscription_id: Mapped[int | None] = mapped_column(
        ForeignKey("billing_subscriptions.id", ondelete="SET NULL"), nullable=True
    )
    provider_invoice_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )
    number: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount_due_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    amount_paid_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    hosted_invoice_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    invoice_pdf_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class PaymentModel(BaseModel):
    __tablename__ = "billing_payments"
    __table_args__ = (
        Index("ix_billing_payments_org_status", "organization_id", "status"),
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("org_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invoice_id: Mapped[int | None] = mapped_column(
        ForeignKey("billing_invoices.id", ondelete="SET NULL"), nullable=True
    )
    provider_payment_intent_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    refunded_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    failure_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class RefundModel(BaseModel):
    __tablename__ = "billing_refunds"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("org_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    payment_id: Mapped[int] = mapped_column(
        ForeignKey("billing_payments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    provider_refund_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    requested_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_auth_users.id", ondelete="SET NULL"), nullable=True
    )


class PromotionModel(BaseModel):
    __tablename__ = "billing_promotions"

    code: Mapped[str] = mapped_column(
        String(80), nullable=False, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    percent_off: Mapped[int | None] = mapped_column(Integer, nullable=True)
    amount_off_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    provider_coupon_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    max_redemptions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    redemption_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    starts_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )


class StripeWebhookEventModel(BaseModel):
    """Durable record used to make Stripe webhook processing idempotent."""

    __tablename__ = "stripe_webhook_events"

    provider_event_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    livemode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    api_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class SupportArticleModel(BaseModel):
    __tablename__ = "support_articles"

    slug: Mapped[str] = mapped_column(
        String(180), nullable=False, unique=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    is_published: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class SupportTicketModel(BaseModel):
    __tablename__ = "support_tickets"
    __table_args__ = (
        Index("ix_support_tickets_org_status", "organization_id", "status"),
        Index("ix_support_tickets_assignee_status", "assignee_user_id", "status"),
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("org_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("sys_auth_users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    assignee_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_auth_users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(100), nullable=False, default="general"
    )
    priority: Mapped[str] = mapped_column(
        String(30), nullable=False, default="normal", index=True
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="open", index=True
    )
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class SupportTicketMessageModel(BaseModel):
    __tablename__ = "support_ticket_messages"

    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_auth_users.id", ondelete="SET NULL"), nullable=True
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    attachments: Mapped[list] = mapped_column(JSON, nullable=False, default=list)


class NotificationPreferenceModel(BaseModel):
    __tablename__ = "notification_preferences"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "user_id", name="uq_notification_preference_org_user"
        ),
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("org_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("sys_auth_users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    categories: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class AppNotificationModel(BaseModel):
    __tablename__ = "app_notifications"
    __table_args__ = (Index("ix_app_notifications_user_read", "user_id", "read_at"),)

    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("org_organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("sys_auth_users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    notification_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    action_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class ApiKeyModel(BaseModel):
    __tablename__ = "workspace_api_keys"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("org_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_auth_users.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    scopes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class WebhookEndpointModel(BaseModel):
    __tablename__ = "workspace_webhook_endpoints"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("org_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    events: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    secret_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )
    last_delivery_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class AuditLogModel(BaseModel):
    __tablename__ = "workspace_audit_logs"
    __table_args__ = (
        Index("ix_workspace_audit_logs_org_action", "organization_id", "action"),
    )

    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("org_organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_auth_users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_uuid: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)


class ProviderConfigModel(BaseModel):
    __tablename__ = "platform_provider_configs"
    __table_args__ = (
        UniqueConstraint("provider", "config_key", name="uq_provider_config_key"),
    )

    provider: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    config_key: Mapped[str] = mapped_column(String(160), nullable=False)
    value_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    is_secret: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )


class FeatureFlagModel(BaseModel):
    __tablename__ = "platform_feature_flags"

    key: Mapped[str] = mapped_column(
        String(160), nullable=False, unique=True, index=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    rollout_percentage: Mapped[int] = mapped_column(
        Integer, nullable=False, default=100
    )
    organization_overrides: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict
    )


class PlatformSettingModel(BaseModel):
    __tablename__ = "platform_settings"

    key: Mapped[str] = mapped_column(
        String(160), nullable=False, unique=True, index=True
    )
    value: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class DomainHealthCheckModel(BaseModel):
    __tablename__ = "platform_domain_health_checks"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "domain", name="uq_domain_health_org_domain"
        ),
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("org_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    spf_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="unknown"
    )
    dkim_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="unknown"
    )
    dmarc_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="unknown"
    )
    dns_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="unknown"
    )
    blacklist_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="unknown"
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class AbuseEventModel(BaseModel):
    __tablename__ = "platform_abuse_events"
    __table_args__ = (
        Index("ix_platform_abuse_org_status", "organization_id", "status"),
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("org_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    campaign_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True, index=True
    )
    severity: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="open", index=True
    )
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    resolved_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_auth_users.id", ondelete="SET NULL"), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
