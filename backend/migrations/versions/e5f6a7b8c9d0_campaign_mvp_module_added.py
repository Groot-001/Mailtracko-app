"""campaign MVP module added

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from migrations.base import BaseMigration

revision: str = "e5f6a7b8c9d0"
down_revision: str | Sequence[str] | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _base_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("uuid", sa.String(length=255), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    ]


class CampaignsMigration(BaseMigration):
    """Create/drop the `campaigns` table using the project migration convention."""

    table_name = "campaigns"

    def __init__(self) -> None:
        super().__init__(revision=revision, down_revision="d4e5f6a7b8c9")
        self.create_whole_table = True
        self.fields.extend(
            [
                *_base_columns(),
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
                sa.Column(
                    "updated_by_id",
                    sa.Integer(),
                    sa.ForeignKey("sys_auth_users.id", ondelete="SET NULL"),
                    nullable=True,
                ),
                sa.Column("name", sa.String(length=150), nullable=False),
                sa.Column("description", sa.Text(), nullable=True),
                sa.Column("campaign_type", sa.String(length=30), nullable=False, server_default="regular"),
                sa.Column("goal", sa.String(length=50), nullable=False, server_default="outreach"),
                sa.Column("priority", sa.String(length=20), nullable=False, server_default="normal"),
                sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
                sa.Column("current_step", sa.String(length=30), nullable=False, server_default="setup"),
                sa.Column(
                    "email_account_id",
                    sa.Integer(),
                    sa.ForeignKey("email_accounts.id", ondelete="SET NULL"),
                    nullable=True,
                ),
                sa.Column(
                    "template_id",
                    sa.Integer(),
                    sa.ForeignKey("templates.id", ondelete="SET NULL"),
                    nullable=True,
                ),
                sa.Column(
                    "contact_list_id",
                    sa.Integer(),
                    sa.ForeignKey("contact_lists.id", ondelete="RESTRICT"),
                    nullable=True,
                ),
                sa.Column("schedule_type", sa.String(length=30), nullable=False, server_default="immediate"),
                sa.Column("timezone", sa.String(length=100), nullable=False, server_default="UTC"),
                sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
                sa.Column("daily_limit", sa.Integer(), nullable=True),
                sa.Column("batch_size", sa.Integer(), nullable=False, server_default="25"),
                sa.Column("total_recipients", sa.Integer(), nullable=False, server_default="0"),
                sa.Column("sent_count", sa.Integer(), nullable=False, server_default="0"),
                sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
                sa.Column("skipped_count", sa.Integer(), nullable=False, server_default="0"),
                sa.Column("launched_at", sa.DateTime(timezone=True), nullable=True),
                sa.Column("paused_at", sa.DateTime(timezone=True), nullable=True),
                sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
                sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
                sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
                sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
                sa.CheckConstraint("batch_size > 0", name="ck_campaigns_batch_size_positive"),
                sa.CheckConstraint(
                    "daily_limit IS NULL OR daily_limit > 0",
                    name="ck_campaigns_daily_limit_positive",
                ),
            ]
        )


class CampaignSequencesMigration(BaseMigration):
    """Create/drop the `campaign_sequences` table using the project migration convention."""

    table_name = "campaign_sequences"

    def __init__(self) -> None:
        super().__init__(revision=revision, down_revision="d4e5f6a7b8c9")
        self.create_whole_table = True
        self.fields.extend(
            [
                *_base_columns(),
                sa.Column(
                    "campaign_id",
                    sa.Integer(),
                    sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
                    nullable=False,
                    unique=True,
                ),
                sa.Column(
                    "organization_id",
                    sa.Integer(),
                    sa.ForeignKey("org_organizations.id", ondelete="CASCADE"),
                    nullable=False,
                ),
                sa.Column("status", sa.String(length=30), nullable=False, server_default="not_started"),
                sa.Column("stop_on_reply", sa.Boolean(), nullable=False, server_default=sa.true()),
                sa.Column("stop_on_unsubscribe", sa.Boolean(), nullable=False, server_default=sa.true()),
                sa.Column("total_steps", sa.Integer(), nullable=False, server_default="0"),
            ]
        )


class CampaignAbTestsMigration(BaseMigration):
    """Create/drop the `campaign_ab_tests` table using the project migration convention."""

    table_name = "campaign_ab_tests"

    def __init__(self) -> None:
        super().__init__(revision=revision, down_revision="d4e5f6a7b8c9")
        self.create_whole_table = True
        self.fields.extend(
            [
                *_base_columns(),
                sa.Column(
                    "campaign_id",
                    sa.Integer(),
                    sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
                    nullable=False,
                    unique=True,
                ),
                sa.Column(
                    "organization_id",
                    sa.Integer(),
                    sa.ForeignKey("org_organizations.id", ondelete="CASCADE"),
                    nullable=False,
                ),
                sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
                sa.Column("test_percentage", sa.Integer(), nullable=False, server_default="100"),
                sa.Column("winner_metric", sa.String(length=30), nullable=False, server_default="reply_rate"),
                sa.Column("auto_select_winner", sa.Boolean(), nullable=False, server_default=sa.false()),
                sa.Column("winner_variant_id", sa.Integer(), nullable=True),
            ]
        )


class CampaignSequenceStepsMigration(BaseMigration):
    """Create/drop the `campaign_sequence_steps` table using the project migration convention."""

    table_name = "campaign_sequence_steps"

    def __init__(self) -> None:
        super().__init__(revision=revision, down_revision="d4e5f6a7b8c9")
        self.create_whole_table = True
        self.fields.extend(
            [
                *_base_columns(),
                sa.Column(
                    "organization_id",
                    sa.Integer(),
                    sa.ForeignKey("org_organizations.id", ondelete="CASCADE"),
                    nullable=False,
                ),
                sa.Column(
                    "campaign_id",
                    sa.Integer(),
                    sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
                    nullable=False,
                ),
                sa.Column(
                    "sequence_id",
                    sa.Integer(),
                    sa.ForeignKey("campaign_sequences.id", ondelete="CASCADE"),
                    nullable=False,
                ),
                sa.Column("step_order", sa.Integer(), nullable=False),
                sa.Column("step_type", sa.String(length=30), nullable=False),
                sa.Column(
                    "template_id",
                    sa.Integer(),
                    sa.ForeignKey("templates.id", ondelete="SET NULL"),
                    nullable=True,
                ),
                sa.Column("subject_override", sa.String(length=255), nullable=True),
                sa.Column("body_html_override", sa.Text(), nullable=True),
                sa.Column("delay_value", sa.Integer(), nullable=True),
                sa.Column("delay_unit", sa.String(length=20), nullable=True),
                sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
                sa.UniqueConstraint("sequence_id", "step_order", name="uq_sequence_step_order"),
                sa.CheckConstraint("step_order > 0", name="ck_sequence_step_order_positive"),
            ]
        )


class CampaignAbVariantsMigration(BaseMigration):
    """Create/drop the `campaign_ab_variants` table using the project migration convention."""

    table_name = "campaign_ab_variants"

    def __init__(self) -> None:
        super().__init__(revision=revision, down_revision="d4e5f6a7b8c9")
        self.create_whole_table = True
        self.fields.extend(
            [
                *_base_columns(),
                sa.Column(
                    "organization_id",
                    sa.Integer(),
                    sa.ForeignKey("org_organizations.id", ondelete="CASCADE"),
                    nullable=False,
                ),
                sa.Column(
                    "campaign_id",
                    sa.Integer(),
                    sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
                    nullable=False,
                ),
                sa.Column(
                    "ab_test_id",
                    sa.Integer(),
                    sa.ForeignKey("campaign_ab_tests.id", ondelete="CASCADE"),
                    nullable=False,
                ),
                sa.Column("variant_type", sa.String(length=10), nullable=False),
                sa.Column("name", sa.String(length=100), nullable=False),
                sa.Column(
                    "template_id",
                    sa.Integer(),
                    sa.ForeignKey("templates.id", ondelete="SET NULL"),
                    nullable=True,
                ),
                sa.Column("subject_override", sa.String(length=255), nullable=True),
                sa.Column("body_html_override", sa.Text(), nullable=True),
                sa.Column("allocation_percentage", sa.Integer(), nullable=False, server_default="50"),
                sa.Column("sent_count", sa.Integer(), nullable=False, server_default="0"),
                sa.Column("delivered_count", sa.Integer(), nullable=False, server_default="0"),
                sa.Column("opened_count", sa.Integer(), nullable=False, server_default="0"),
                sa.Column("clicked_count", sa.Integer(), nullable=False, server_default="0"),
                sa.Column("replied_count", sa.Integer(), nullable=False, server_default="0"),
                sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
                sa.UniqueConstraint("ab_test_id", "variant_type", name="uq_ab_test_variant_type"),
                sa.CheckConstraint(
                    "allocation_percentage > 0 AND allocation_percentage < 100",
                    name="ck_ab_variant_allocation",
                ),
            ]
        )


class CampaignRecipientsMigration(BaseMigration):
    """Create/drop the `campaign_recipients` table using the project migration convention."""

    table_name = "campaign_recipients"

    def __init__(self) -> None:
        super().__init__(revision=revision, down_revision="d4e5f6a7b8c9")
        self.create_whole_table = True
        self.fields.extend(
            [
                *_base_columns(),
                sa.Column(
                    "organization_id",
                    sa.Integer(),
                    sa.ForeignKey("org_organizations.id", ondelete="CASCADE"),
                    nullable=False,
                ),
                sa.Column(
                    "campaign_id",
                    sa.Integer(),
                    sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
                    nullable=False,
                ),
                sa.Column(
                    "contact_id",
                    sa.Integer(),
                    sa.ForeignKey("contact_contacts.id", ondelete="SET NULL"),
                    nullable=True,
                ),
                sa.Column(
                    "sequence_step_id",
                    sa.Integer(),
                    sa.ForeignKey("campaign_sequence_steps.id", ondelete="SET NULL"),
                    nullable=True,
                ),
                sa.Column(
                    "ab_variant_id",
                    sa.Integer(),
                    sa.ForeignKey("campaign_ab_variants.id", ondelete="SET NULL"),
                    nullable=True,
                ),
                sa.Column("email", sa.String(length=320), nullable=False),
                sa.Column("normalized_email", sa.String(length=320), nullable=False),
                sa.Column("personalization_data", sa.JSON(), nullable=True),
                sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
                sa.Column("current_step_order", sa.Integer(), nullable=False, server_default="1"),
                sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
                sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
                sa.Column("provider_message_id", sa.String(length=255), nullable=True),
                sa.Column("provider_thread_id", sa.String(length=255), nullable=True),
                sa.Column("last_error_code", sa.String(length=100), nullable=True),
                sa.Column("last_error_message", sa.Text(), nullable=True),
                sa.Column("queued_at", sa.DateTime(timezone=True), nullable=True),
                sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
                sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
                sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
                sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
                sa.Column("clicked_at", sa.DateTime(timezone=True), nullable=True),
                sa.Column("replied_at", sa.DateTime(timezone=True), nullable=True),
                sa.Column("unsubscribed_at", sa.DateTime(timezone=True), nullable=True),
                sa.UniqueConstraint("campaign_id", "normalized_email", name="uq_campaign_recipient_email"),
            ]
        )


def upgrade() -> None:
    CampaignsMigration().upgrade()
    op.create_index("ix_campaigns_uuid", "campaigns", ["uuid"], unique=True)
    op.create_index("ix_campaigns_organization_id", "campaigns", ["organization_id"])
    op.create_index("ix_campaigns_created_by_id", "campaigns", ["created_by_id"])
    op.create_index("ix_campaigns_status", "campaigns", ["status"])
    op.create_index("ix_campaigns_campaign_type", "campaigns", ["campaign_type"])
    op.create_index("ix_campaigns_priority", "campaigns", ["priority"])
    op.create_index("ix_campaigns_email_account_id", "campaigns", ["email_account_id"])
    op.create_index("ix_campaigns_template_id", "campaigns", ["template_id"])
    op.create_index("ix_campaigns_contact_list_id", "campaigns", ["contact_list_id"])
    op.create_index("ix_campaigns_scheduled_at", "campaigns", ["scheduled_at"])
    op.create_index("ix_campaigns_org_status", "campaigns", ["organization_id", "status"])
    op.create_index("ix_campaigns_status_scheduled", "campaigns", ["status", "scheduled_at"])

    CampaignSequencesMigration().upgrade()
    op.create_index("ix_campaign_sequences_uuid", "campaign_sequences", ["uuid"], unique=True)
    op.create_index("ix_campaign_sequences_campaign_id", "campaign_sequences", ["campaign_id"])
    op.create_index("ix_campaign_sequences_organization_id", "campaign_sequences", ["organization_id"])
    op.create_index("ix_campaign_sequences_status", "campaign_sequences", ["status"])

    CampaignAbTestsMigration().upgrade()
    op.create_index("ix_campaign_ab_tests_uuid", "campaign_ab_tests", ["uuid"], unique=True)
    op.create_index("ix_campaign_ab_tests_campaign_id", "campaign_ab_tests", ["campaign_id"])
    op.create_index("ix_campaign_ab_tests_organization_id", "campaign_ab_tests", ["organization_id"])
    op.create_index("ix_campaign_ab_tests_status", "campaign_ab_tests", ["status"])

    CampaignSequenceStepsMigration().upgrade()
    op.create_index("ix_campaign_sequence_steps_uuid", "campaign_sequence_steps", ["uuid"], unique=True)
    op.create_index("ix_campaign_sequence_steps_organization_id", "campaign_sequence_steps", ["organization_id"])
    op.create_index("ix_campaign_sequence_steps_campaign_id", "campaign_sequence_steps", ["campaign_id"])
    op.create_index("ix_campaign_sequence_steps_sequence_id", "campaign_sequence_steps", ["sequence_id"])
    op.create_index("ix_campaign_sequence_steps_step_type", "campaign_sequence_steps", ["step_type"])
    op.create_index("ix_campaign_sequence_steps_template_id", "campaign_sequence_steps", ["template_id"])

    CampaignAbVariantsMigration().upgrade()
    op.create_index("ix_campaign_ab_variants_uuid", "campaign_ab_variants", ["uuid"], unique=True)
    op.create_index("ix_campaign_ab_variants_organization_id", "campaign_ab_variants", ["organization_id"])
    op.create_index("ix_campaign_ab_variants_campaign_id", "campaign_ab_variants", ["campaign_id"])
    op.create_index("ix_campaign_ab_variants_ab_test_id", "campaign_ab_variants", ["ab_test_id"])
    op.create_index("ix_campaign_ab_variants_template_id", "campaign_ab_variants", ["template_id"])

    CampaignRecipientsMigration().upgrade()
    op.create_index("ix_campaign_recipients_uuid", "campaign_recipients", ["uuid"], unique=True)
    op.create_index("ix_campaign_recipients_organization_id", "campaign_recipients", ["organization_id"])
    op.create_index("ix_campaign_recipients_campaign_id", "campaign_recipients", ["campaign_id"])
    op.create_index("ix_campaign_recipients_contact_id", "campaign_recipients", ["contact_id"])
    op.create_index("ix_campaign_recipients_sequence_step_id", "campaign_recipients", ["sequence_step_id"])
    op.create_index("ix_campaign_recipients_ab_variant_id", "campaign_recipients", ["ab_variant_id"])
    op.create_index("ix_campaign_recipients_status", "campaign_recipients", ["status"])
    op.create_index("ix_campaign_recipients_next_attempt_at", "campaign_recipients", ["next_attempt_at"])
    op.create_index("ix_campaign_recipients_provider_message_id", "campaign_recipients", ["provider_message_id"])
    op.create_index("ix_campaign_recipients_campaign_status", "campaign_recipients", ["campaign_id", "status"])
    op.create_index(
        "ix_campaign_recipients_campaign_due",
        "campaign_recipients",
        ["campaign_id", "status", "next_attempt_at"],
    )


def downgrade() -> None:
    CampaignRecipientsMigration().downgrade()
    CampaignAbVariantsMigration().downgrade()
    CampaignSequenceStepsMigration().downgrade()
    CampaignAbTestsMigration().downgrade()
    CampaignSequencesMigration().downgrade()
    CampaignsMigration().downgrade()
