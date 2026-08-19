"""platform billing, support, compliance and administration control plane

Revision ID: a8b9c0d1e2f3
Revises: f7a8b9c0d1e2
Create Date: 2026-08-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a8b9c0d1e2f3"
down_revision: str | Sequence[str] | None = "f7a8b9c0d1e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _base_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("uuid", sa.String(), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    ]


def _create(name: str, *columns: sa.Column, constraints: tuple = ()) -> None:
    op.create_table(name, *_base_columns(), *columns, *constraints)
    op.create_index(f"ix_{name}_uuid", name, ["uuid"], unique=True)


def upgrade() -> None:
    _create(
        "billing_promotions",
        sa.Column("code", sa.String(80), nullable=False, unique=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("percent_off", sa.Integer(), nullable=True),
        sa.Column("amount_off_cents", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("provider_coupon_id", sa.String(255), nullable=True),
        sa.Column("max_redemptions", sa.Integer(), nullable=True),
        sa.Column("redemption_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index(
        "ix_billing_promotions_code", "billing_promotions", ["code"], unique=True
    )
    op.create_index(
        "ix_billing_promotions_is_active", "billing_promotions", ["is_active"]
    )

    _create(
        "billing_plans",
        sa.Column("code", sa.String(80), nullable=False, unique=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column(
            "monthly_price_cents", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "annual_price_cents", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("stripe_monthly_price_id", sa.String(255), nullable=True),
        sa.Column("stripe_annual_price_id", sa.String(255), nullable=True),
        sa.Column("trial_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "limits", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")
        ),
        sa.Column(
            "features", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "is_default", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_billing_plans_code", "billing_plans", ["code"], unique=True)
    op.create_index("ix_billing_plans_is_active", "billing_plans", ["is_active"])
    op.create_index("ix_billing_plans_is_default", "billing_plans", ["is_default"])
    op.get_bind().exec_driver_sql(
        "INSERT INTO billing_plans "
        "(uuid, created_at, code, name, description, currency, monthly_price_cents, "
        "annual_price_cents, trial_days, limits, features, is_active, is_default, display_order) "
        "VALUES ('00000000-0000-4000-8000-000000000001', now(), 'starter', 'Starter', "
        "'Core email outreach for a new workspace.', 'USD', 0, 0, 0, "
        "'{\"contacts\":1000,\"monthly_sends\":5000,\"sender_accounts\":1,\"team_members\":1}'::json, "
        "'[\"Campaigns\",\"Email tracking\",\"Contact management\",\"Community support\"]'::json, "
        "true, true, 0)"
    )

    _create(
        "billing_subscriptions",
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("org_organizations.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "plan_id",
            sa.Integer(),
            sa.ForeignKey("billing_plans.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "promotion_id",
            sa.Integer(),
            sa.ForeignKey("billing_promotions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(40), nullable=False, server_default="trialing"),
        sa.Column(
            "billing_cycle", sa.String(20), nullable=False, server_default="monthly"
        ),
        sa.Column("seats", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("provider_customer_id", sa.String(255), nullable=True, unique=True),
        sa.Column(
            "provider_subscription_id", sa.String(255), nullable=True, unique=True
        ),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "cancel_at_period_end",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_billing_subscriptions_organization_id",
        "billing_subscriptions",
        ["organization_id"],
        unique=True,
    )
    op.create_index(
        "ix_billing_subscriptions_plan_id", "billing_subscriptions", ["plan_id"]
    )
    op.create_index(
        "ix_billing_subscriptions_status", "billing_subscriptions", ["status"]
    )

    _create(
        "billing_profiles",
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("org_organizations.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("billing_email", sa.String(320), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("tax_id", sa.String(100), nullable=True),
        sa.Column("address", sa.JSON(), nullable=True),
        sa.Column("card_brand", sa.String(50), nullable=True),
        sa.Column("card_last4", sa.String(4), nullable=True),
        sa.Column("card_exp_month", sa.Integer(), nullable=True),
        sa.Column("card_exp_year", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_billing_profiles_organization_id",
        "billing_profiles",
        ["organization_id"],
        unique=True,
    )

    _create(
        "billing_invoices",
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("org_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "subscription_id",
            sa.Integer(),
            sa.ForeignKey("billing_subscriptions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("provider_invoice_id", sa.String(255), nullable=False, unique=True),
        sa.Column("number", sa.String(120), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("amount_due_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "amount_paid_cents", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("hosted_invoice_url", sa.String(1000), nullable=True),
        sa.Column("invoice_pdf_url", sa.String(1000), nullable=True),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_billing_invoices_organization_id", "billing_invoices", ["organization_id"]
    )
    op.create_index(
        "ix_billing_invoices_org_status",
        "billing_invoices",
        ["organization_id", "status"],
    )
    op.create_index("ix_billing_invoices_number", "billing_invoices", ["number"])

    _create(
        "billing_payments",
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("org_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "invoice_id",
            sa.Integer(),
            sa.ForeignKey("billing_invoices.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "provider_payment_intent_id", sa.String(255), nullable=False, unique=True
        ),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("refunded_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("failure_message", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_billing_payments_organization_id", "billing_payments", ["organization_id"]
    )
    op.create_index(
        "ix_billing_payments_org_status",
        "billing_payments",
        ["organization_id", "status"],
    )

    _create(
        "billing_refunds",
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("org_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "payment_id",
            sa.Integer(),
            sa.ForeignKey("billing_payments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("provider_refund_id", sa.String(255), nullable=False, unique=True),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("reason", sa.String(100), nullable=True),
        sa.Column(
            "requested_by_id",
            sa.Integer(),
            sa.ForeignKey("sys_auth_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_billing_refunds_organization_id", "billing_refunds", ["organization_id"]
    )
    op.create_index("ix_billing_refunds_payment_id", "billing_refunds", ["payment_id"])
    op.create_index("ix_billing_refunds_status", "billing_refunds", ["status"])

    _create(
        "support_articles",
        sa.Column("slug", sa.String(180), nullable=False, unique=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "tags", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")
        ),
        sa.Column(
            "is_published", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index(
        "ix_support_articles_slug", "support_articles", ["slug"], unique=True
    )
    op.create_index("ix_support_articles_category", "support_articles", ["category"])
    op.create_index(
        "ix_support_articles_is_published", "support_articles", ["is_published"]
    )

    _create(
        "support_tickets",
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("org_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_by_id",
            sa.Integer(),
            sa.ForeignKey("sys_auth_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "assignee_user_id",
            sa.Integer(),
            sa.ForeignKey("sys_auth_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(100), nullable=False, server_default="general"),
        sa.Column("priority", sa.String(30), nullable=False, server_default="normal"),
        sa.Column("status", sa.String(30), nullable=False, server_default="open"),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_support_tickets_organization_id", "support_tickets", ["organization_id"]
    )
    op.create_index(
        "ix_support_tickets_created_by_id", "support_tickets", ["created_by_id"]
    )
    op.create_index(
        "ix_support_tickets_org_status",
        "support_tickets",
        ["organization_id", "status"],
    )
    op.create_index(
        "ix_support_tickets_assignee_status",
        "support_tickets",
        ["assignee_user_id", "status"],
    )

    _create(
        "support_ticket_messages",
        sa.Column(
            "ticket_id",
            sa.Integer(),
            sa.ForeignKey("support_tickets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "author_user_id",
            sa.Integer(),
            sa.ForeignKey("sys_auth_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "is_internal", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "attachments",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
    )
    op.create_index(
        "ix_support_ticket_messages_ticket_id", "support_ticket_messages", ["ticket_id"]
    )

    _create(
        "notification_preferences",
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("org_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("sys_auth_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "email_enabled", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column(
            "in_app_enabled", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column(
            "categories",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
        constraints=(
            sa.UniqueConstraint(
                "organization_id", "user_id", name="uq_notification_preference_org_user"
            ),
        ),
    )
    op.create_index(
        "ix_notification_preferences_organization_id",
        "notification_preferences",
        ["organization_id"],
    )
    op.create_index(
        "ix_notification_preferences_user_id", "notification_preferences", ["user_id"]
    )

    _create(
        "app_notifications",
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("org_organizations.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("sys_auth_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("notification_type", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("action_url", sa.String(1000), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_app_notifications_organization_id", "app_notifications", ["organization_id"]
    )
    op.create_index("ix_app_notifications_user_id", "app_notifications", ["user_id"])
    op.create_index(
        "ix_app_notifications_notification_type",
        "app_notifications",
        ["notification_type"],
    )
    op.create_index(
        "ix_app_notifications_user_read", "app_notifications", ["user_id", "read_at"]
    )

    _create(
        "workspace_api_keys",
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("org_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_by_id",
            sa.Integer(),
            sa.ForeignKey("sys_auth_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("key_prefix", sa.String(20), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False, unique=True),
        sa.Column(
            "scopes", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_workspace_api_keys_organization_id",
        "workspace_api_keys",
        ["organization_id"],
    )
    op.create_index(
        "ix_workspace_api_keys_key_prefix", "workspace_api_keys", ["key_prefix"]
    )

    _create(
        "workspace_webhook_endpoints",
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("org_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column(
            "events", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")
        ),
        sa.Column("secret_encrypted", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_delivery_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status_code", sa.Integer(), nullable=True),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index(
        "ix_workspace_webhook_endpoints_organization_id",
        "workspace_webhook_endpoints",
        ["organization_id"],
    )
    op.create_index(
        "ix_workspace_webhook_endpoints_is_active",
        "workspace_webhook_endpoints",
        ["is_active"],
    )

    _create(
        "workspace_audit_logs",
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("org_organizations.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "actor_user_id",
            sa.Integer(),
            sa.ForeignKey("sys_auth_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(120), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_uuid", sa.String(255), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
    )
    op.create_index(
        "ix_workspace_audit_logs_organization_id",
        "workspace_audit_logs",
        ["organization_id"],
    )
    op.create_index(
        "ix_workspace_audit_logs_actor_user_id",
        "workspace_audit_logs",
        ["actor_user_id"],
    )
    op.create_index(
        "ix_workspace_audit_logs_org_action",
        "workspace_audit_logs",
        ["organization_id", "action"],
    )
    op.create_index(
        "ix_workspace_audit_logs_resource_uuid",
        "workspace_audit_logs",
        ["resource_uuid"],
    )

    _create(
        "platform_provider_configs",
        sa.Column("provider", sa.String(100), nullable=False),
        sa.Column("config_key", sa.String(160), nullable=False),
        sa.Column("value_encrypted", sa.Text(), nullable=False),
        sa.Column("is_secret", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        constraints=(
            sa.UniqueConstraint(
                "provider", "config_key", name="uq_provider_config_key"
            ),
        ),
    )
    op.create_index(
        "ix_platform_provider_configs_provider",
        "platform_provider_configs",
        ["provider"],
    )
    op.create_index(
        "ix_platform_provider_configs_is_active",
        "platform_provider_configs",
        ["is_active"],
    )

    _create(
        "platform_feature_flags",
        sa.Column("key", sa.String(160), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "is_enabled", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "rollout_percentage", sa.Integer(), nullable=False, server_default="100"
        ),
        sa.Column(
            "organization_overrides",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
    )
    op.create_index(
        "ix_platform_feature_flags_key", "platform_feature_flags", ["key"], unique=True
    )
    op.create_index(
        "ix_platform_feature_flags_is_enabled", "platform_feature_flags", ["is_enabled"]
    )

    _create(
        "platform_settings",
        sa.Column("key", sa.String(160), nullable=False, unique=True),
        sa.Column(
            "value", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")
        ),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(
        "ix_platform_settings_key", "platform_settings", ["key"], unique=True
    )

    _create(
        "platform_domain_health_checks",
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("org_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column(
            "spf_status", sa.String(30), nullable=False, server_default="unknown"
        ),
        sa.Column(
            "dkim_status", sa.String(30), nullable=False, server_default="unknown"
        ),
        sa.Column(
            "dmarc_status", sa.String(30), nullable=False, server_default="unknown"
        ),
        sa.Column(
            "dns_status", sa.String(30), nullable=False, server_default="unknown"
        ),
        sa.Column(
            "blacklist_status", sa.String(30), nullable=False, server_default="unknown"
        ),
        sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "details", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")
        ),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        constraints=(
            sa.UniqueConstraint(
                "organization_id", "domain", name="uq_domain_health_org_domain"
            ),
        ),
    )
    op.create_index(
        "ix_platform_domain_health_checks_organization_id",
        "platform_domain_health_checks",
        ["organization_id"],
    )
    op.create_index(
        "ix_platform_domain_health_checks_domain",
        "platform_domain_health_checks",
        ["domain"],
    )

    _create(
        "platform_abuse_events",
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("org_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "campaign_id",
            sa.Integer(),
            sa.ForeignKey("campaigns.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("severity", sa.String(30), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="open"),
        sa.Column(
            "metrics", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")
        ),
        sa.Column(
            "resolved_by_id",
            sa.Integer(),
            sa.ForeignKey("sys_auth_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_platform_abuse_events_organization_id",
        "platform_abuse_events",
        ["organization_id"],
    )
    op.create_index(
        "ix_platform_abuse_events_campaign_id", "platform_abuse_events", ["campaign_id"]
    )
    op.create_index(
        "ix_platform_abuse_org_status",
        "platform_abuse_events",
        ["organization_id", "status"],
    )
    op.create_index(
        "ix_platform_abuse_events_severity", "platform_abuse_events", ["severity"]
    )


def downgrade() -> None:
    for table_name in (
        "platform_abuse_events",
        "platform_domain_health_checks",
        "platform_settings",
        "platform_feature_flags",
        "platform_provider_configs",
        "workspace_audit_logs",
        "workspace_webhook_endpoints",
        "workspace_api_keys",
        "app_notifications",
        "notification_preferences",
        "support_ticket_messages",
        "support_tickets",
        "support_articles",
        "billing_refunds",
        "billing_payments",
        "billing_invoices",
        "billing_profiles",
        "billing_subscriptions",
        "billing_plans",
        "billing_promotions",
    ):
        op.drop_table(table_name)
