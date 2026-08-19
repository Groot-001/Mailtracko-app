"""campaign Phase 1, sequence and A/B hardening

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-07-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from migrations.base import BaseMigration

revision: str = "f6a7b8c9d0e1"
down_revision: str | Sequence[str] | None = "e5f6a7b8c9d0"
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


class CampaignMessagesMigration(BaseMigration):
    """Create/drop the `campaign_messages` table using the project migration convention."""

    table_name = "campaign_messages"

    def __init__(self) -> None:
        super().__init__(revision=revision, down_revision="e5f6a7b8c9d0")
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
                    "recipient_id",
                    sa.Integer(),
                    sa.ForeignKey("campaign_recipients.id", ondelete="CASCADE"),
                    nullable=False,
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
                sa.Column("step_order", sa.Integer(), nullable=False, server_default="1"),
                sa.Column("idempotency_key", sa.String(length=64), nullable=False),
                sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
                sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
                sa.Column("provider_message_id", sa.String(length=255), nullable=True),
                sa.Column("provider_thread_id", sa.String(length=255), nullable=True),
                sa.Column("subject_snapshot", sa.String(length=255), nullable=True),
                sa.Column("preheader_snapshot", sa.Text(), nullable=True),
                sa.Column("body_html_snapshot", sa.Text(), nullable=True),
                sa.Column("from_name_snapshot", sa.String(length=255), nullable=True),
                sa.Column("content_checksum", sa.String(length=64), nullable=True),
                sa.Column("last_error_code", sa.String(length=100), nullable=True),
                sa.Column("last_error_message", sa.Text(), nullable=True),
                sa.Column("sending_started_at", sa.DateTime(timezone=True), nullable=True),
                sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
                sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
                sa.Column("reconciled_at", sa.DateTime(timezone=True), nullable=True),
                sa.UniqueConstraint("idempotency_key", name="uq_campaign_message_idempotency_key"),
            ]
        )


class CampaignMessageEventsMigration(BaseMigration):
    """Create/drop the `campaign_message_events` table using the project migration convention."""

    table_name = "campaign_message_events"

    def __init__(self) -> None:
        super().__init__(revision=revision, down_revision="e5f6a7b8c9d0")
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
                    "recipient_id",
                    sa.Integer(),
                    sa.ForeignKey("campaign_recipients.id", ondelete="CASCADE"),
                    nullable=False,
                ),
                sa.Column(
                    "message_id",
                    sa.Integer(),
                    sa.ForeignKey("campaign_messages.id", ondelete="SET NULL"),
                    nullable=True,
                ),
                sa.Column("event_type", sa.String(length=50), nullable=False),
                sa.Column("custom_event_name", sa.String(length=100), nullable=True),
                sa.Column("provider_event_id", sa.String(length=255), nullable=True),
                sa.Column("provider_message_id", sa.String(length=255), nullable=True),
                sa.Column("dedupe_key", sa.String(length=64), nullable=False),
                sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
                sa.Column("metadata", sa.JSON(), nullable=True),
                sa.UniqueConstraint("dedupe_key", name="uq_campaign_message_event_dedupe_key"),
            ]
        )


class CampaignSuppressionsMigration(BaseMigration):
    """Create/drop the `campaign_suppressions` table using the project migration convention."""

    table_name = "campaign_suppressions"

    def __init__(self) -> None:
        super().__init__(revision=revision, down_revision="e5f6a7b8c9d0")
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
                sa.Column("normalized_email", sa.String(length=320), nullable=False),
                sa.Column("reason", sa.String(length=50), nullable=False),
                sa.Column(
                    "source_campaign_id",
                    sa.Integer(),
                    sa.ForeignKey("campaigns.id", ondelete="SET NULL"),
                    nullable=True,
                ),
                sa.Column(
                    "source_recipient_id",
                    sa.Integer(),
                    sa.ForeignKey("campaign_recipients.id", ondelete="SET NULL"),
                    nullable=True,
                ),
                sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
                sa.Column("suppressed_at", sa.DateTime(timezone=True), nullable=False),
                sa.UniqueConstraint(
                    "organization_id", "normalized_email", name="uq_campaign_suppression_email"
                ),
            ]
        )


class CampaignStateHistoryMigration(BaseMigration):
    """Create/drop the `campaign_state_history` table using the project migration convention."""

    table_name = "campaign_state_history"

    def __init__(self) -> None:
        super().__init__(revision=revision, down_revision="e5f6a7b8c9d0")
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
                    "actor_id",
                    sa.Integer(),
                    sa.ForeignKey("sys_auth_users.id", ondelete="SET NULL"),
                    nullable=True,
                ),
                sa.Column("from_status", sa.String(length=30), nullable=False),
                sa.Column("to_status", sa.String(length=30), nullable=False),
                sa.Column("reason", sa.String(length=255), nullable=True),
                sa.Column("transitioned_at", sa.DateTime(timezone=True), nullable=False),
            ]
        )


class CampaignsSendingWindowStartMigration(BaseMigration):
    """Add/drop `campaigns.sending_window_start` through BaseMigration."""

    table_name = "campaigns"

    def __init__(self) -> None:
        super().__init__(revision=revision, down_revision="e5f6a7b8c9d0")
        self.create_whole_table = False
        self.add_column(sa.Column("sending_window_start", sa.Time(), nullable=True))


class CampaignsSendingWindowEndMigration(BaseMigration):
    """Add/drop `campaigns.sending_window_end` through BaseMigration."""

    table_name = "campaigns"

    def __init__(self) -> None:
        super().__init__(revision=revision, down_revision="e5f6a7b8c9d0")
        self.create_whole_table = False
        self.add_column(sa.Column("sending_window_end", sa.Time(), nullable=True))


class CampaignsSendingDaysMigration(BaseMigration):
    """Add/drop `campaigns.sending_days` through BaseMigration."""

    table_name = "campaigns"

    def __init__(self) -> None:
        super().__init__(revision=revision, down_revision="e5f6a7b8c9d0")
        self.create_whole_table = False
        self.add_column(
            sa.Column(
                "sending_days",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'[0,1,2,3,4,5,6]'"),
            )
        )


class CampaignSequencesStopOnClickMigration(BaseMigration):
    """Add/drop `campaign_sequences.stop_on_click` through BaseMigration."""

    table_name = "campaign_sequences"

    def __init__(self) -> None:
        super().__init__(revision=revision, down_revision="e5f6a7b8c9d0")
        self.create_whole_table = False
        self.add_column(
            sa.Column(
                "stop_on_click",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )


class CampaignSequencesStopOnMeetingMigration(BaseMigration):
    """Add/drop `campaign_sequences.stop_on_meeting` through BaseMigration."""

    table_name = "campaign_sequences"

    def __init__(self) -> None:
        super().__init__(revision=revision, down_revision="e5f6a7b8c9d0")
        self.create_whole_table = False
        self.add_column(
            sa.Column(
                "stop_on_meeting",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )


class CampaignSequencesCustomStopEventsMigration(BaseMigration):
    """Add/drop `campaign_sequences.custom_stop_events` through BaseMigration."""

    table_name = "campaign_sequences"

    def __init__(self) -> None:
        super().__init__(revision=revision, down_revision="e5f6a7b8c9d0")
        self.create_whole_table = False
        self.add_column(
            sa.Column(
                "custom_stop_events",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'[]'"),
            )
        )


class CampaignAbTestsMinimumSampleSizeMigration(BaseMigration):
    """Add/drop `campaign_ab_tests.minimum_sample_size` through BaseMigration."""

    table_name = "campaign_ab_tests"

    def __init__(self) -> None:
        super().__init__(revision=revision, down_revision="e5f6a7b8c9d0")
        self.create_whole_table = False
        self.add_column(
            sa.Column(
                "minimum_sample_size",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )


class CampaignAbTestsTestDurationHoursMigration(BaseMigration):
    """Add/drop `campaign_ab_tests.test_duration_hours` through BaseMigration."""

    table_name = "campaign_ab_tests"

    def __init__(self) -> None:
        super().__init__(revision=revision, down_revision="e5f6a7b8c9d0")
        self.create_whole_table = False
        self.add_column(
            sa.Column("test_duration_hours", sa.Integer(), nullable=True)
        )


class CampaignAbTestsStartedAtMigration(BaseMigration):
    """Add/drop `campaign_ab_tests.started_at` through BaseMigration."""

    table_name = "campaign_ab_tests"

    def __init__(self) -> None:
        super().__init__(revision=revision, down_revision="e5f6a7b8c9d0")
        self.create_whole_table = False
        self.add_column(
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True)
        )


class CampaignAbTestsWinnerSelectedAtMigration(BaseMigration):
    """Add/drop `campaign_ab_tests.winner_selected_at` through BaseMigration."""

    table_name = "campaign_ab_tests"

    def __init__(self) -> None:
        super().__init__(revision=revision, down_revision="e5f6a7b8c9d0")
        self.create_whole_table = False
        self.add_column(
            sa.Column(
                "winner_selected_at",
                sa.DateTime(timezone=True),
                nullable=True,
            )
        )


class CampaignRecipientsStopReasonMigration(BaseMigration):
    """Add/drop `campaign_recipients.stop_reason` through BaseMigration."""

    table_name = "campaign_recipients"

    def __init__(self) -> None:
        super().__init__(revision=revision, down_revision="e5f6a7b8c9d0")
        self.create_whole_table = False
        self.add_column(
            sa.Column("stop_reason", sa.String(length=100), nullable=True)
        )


class CampaignRecipientsStoppedAtMigration(BaseMigration):
    """Add/drop `campaign_recipients.stopped_at` through BaseMigration."""

    table_name = "campaign_recipients"

    def __init__(self) -> None:
        super().__init__(revision=revision, down_revision="e5f6a7b8c9d0")
        self.create_whole_table = False
        self.add_column(
            sa.Column("stopped_at", sa.DateTime(timezone=True), nullable=True)
        )


class CampaignRecipientsBouncedAtMigration(BaseMigration):
    """Add/drop `campaign_recipients.bounced_at` through BaseMigration."""

    table_name = "campaign_recipients"

    def __init__(self) -> None:
        super().__init__(revision=revision, down_revision="e5f6a7b8c9d0")
        self.create_whole_table = False
        self.add_column(
            sa.Column("bounced_at", sa.DateTime(timezone=True), nullable=True)
        )


def upgrade() -> None:
    CampaignsSendingWindowStartMigration().upgrade()
    CampaignsSendingWindowEndMigration().upgrade()
    CampaignsSendingDaysMigration().upgrade()
    op.create_check_constraint(
        "ck_campaigns_sending_window_order",
        "campaigns",
        "sending_window_start IS NULL OR sending_window_end IS NULL "
        "OR sending_window_start < sending_window_end",
    )

    CampaignSequencesStopOnClickMigration().upgrade()
    CampaignSequencesStopOnMeetingMigration().upgrade()
    CampaignSequencesCustomStopEventsMigration().upgrade()

    CampaignAbTestsMinimumSampleSizeMigration().upgrade()
    CampaignAbTestsTestDurationHoursMigration().upgrade()
    CampaignAbTestsStartedAtMigration().upgrade()
    CampaignAbTestsWinnerSelectedAtMigration().upgrade()
    op.create_check_constraint(
        "ck_campaign_ab_tests_minimum_sample_size",
        "campaign_ab_tests",
        "minimum_sample_size >= 0",
    )
    op.create_check_constraint(
        "ck_campaign_ab_tests_duration_positive",
        "campaign_ab_tests",
        "test_duration_hours IS NULL OR test_duration_hours > 0",
    )
    op.create_check_constraint(
        "ck_campaign_ab_tests_percentage",
        "campaign_ab_tests",
        "test_percentage > 0 AND test_percentage <= 100",
    )
    op.create_foreign_key(
        "fk_campaign_ab_tests_winner_variant_id",
        "campaign_ab_tests",
        "campaign_ab_variants",
        ["winner_variant_id"],
        ["id"],
        ondelete="SET NULL",
    )

    CampaignRecipientsStopReasonMigration().upgrade()
    CampaignRecipientsStoppedAtMigration().upgrade()
    CampaignRecipientsBouncedAtMigration().upgrade()

    CampaignMessagesMigration().upgrade()
    op.create_index("ix_campaign_messages_uuid", "campaign_messages", ["uuid"], unique=True)
    op.create_index("ix_campaign_messages_organization_id", "campaign_messages", ["organization_id"])
    op.create_index("ix_campaign_messages_campaign_id", "campaign_messages", ["campaign_id"])
    op.create_index("ix_campaign_messages_recipient_id", "campaign_messages", ["recipient_id"])
    op.create_index("ix_campaign_messages_sequence_step_id", "campaign_messages", ["sequence_step_id"])
    op.create_index("ix_campaign_messages_ab_variant_id", "campaign_messages", ["ab_variant_id"])
    op.create_index("ix_campaign_messages_status", "campaign_messages", ["status"])
    op.create_index("ix_campaign_messages_provider_message_id", "campaign_messages", ["provider_message_id"])
    op.create_index("ix_campaign_messages_campaign_status", "campaign_messages", ["campaign_id", "status"])

    CampaignMessageEventsMigration().upgrade()
    op.create_index("ix_campaign_message_events_uuid", "campaign_message_events", ["uuid"], unique=True)
    op.create_index("ix_campaign_message_events_organization_id", "campaign_message_events", ["organization_id"])
    op.create_index("ix_campaign_message_events_campaign_id", "campaign_message_events", ["campaign_id"])
    op.create_index("ix_campaign_message_events_recipient_id", "campaign_message_events", ["recipient_id"])
    op.create_index("ix_campaign_message_events_message_id", "campaign_message_events", ["message_id"])
    op.create_index("ix_campaign_message_events_event_type", "campaign_message_events", ["event_type"])
    op.create_index(
        "ix_campaign_message_events_campaign_type",
        "campaign_message_events",
        ["campaign_id", "event_type"],
    )

    CampaignSuppressionsMigration().upgrade()
    op.create_index("ix_campaign_suppressions_uuid", "campaign_suppressions", ["uuid"], unique=True)
    op.create_index("ix_campaign_suppressions_organization_id", "campaign_suppressions", ["organization_id"])
    op.create_index("ix_campaign_suppressions_normalized_email", "campaign_suppressions", ["normalized_email"])
    op.create_index("ix_campaign_suppressions_source_campaign_id", "campaign_suppressions", ["source_campaign_id"])
    op.create_index("ix_campaign_suppressions_active", "campaign_suppressions", ["active"])

    CampaignStateHistoryMigration().upgrade()
    op.create_index("ix_campaign_state_history_uuid", "campaign_state_history", ["uuid"], unique=True)
    op.create_index("ix_campaign_state_history_organization_id", "campaign_state_history", ["organization_id"])
    op.create_index("ix_campaign_state_history_campaign_id", "campaign_state_history", ["campaign_id"])
    op.create_index("ix_campaign_state_history_actor_id", "campaign_state_history", ["actor_id"])


def downgrade() -> None:
    CampaignStateHistoryMigration().downgrade()
    CampaignSuppressionsMigration().downgrade()
    CampaignMessageEventsMigration().downgrade()
    CampaignMessagesMigration().downgrade()

    CampaignRecipientsBouncedAtMigration().downgrade()
    CampaignRecipientsStoppedAtMigration().downgrade()
    CampaignRecipientsStopReasonMigration().downgrade()

    op.drop_constraint(
        "fk_campaign_ab_tests_winner_variant_id", "campaign_ab_tests", type_="foreignkey"
    )
    op.drop_constraint(
        "ck_campaign_ab_tests_duration_positive", "campaign_ab_tests", type_="check"
    )
    op.drop_constraint(
        "ck_campaign_ab_tests_percentage", "campaign_ab_tests", type_="check"
    )
    op.drop_constraint(
        "ck_campaign_ab_tests_minimum_sample_size", "campaign_ab_tests", type_="check"
    )
    CampaignAbTestsWinnerSelectedAtMigration().downgrade()
    CampaignAbTestsStartedAtMigration().downgrade()
    CampaignAbTestsTestDurationHoursMigration().downgrade()
    CampaignAbTestsMinimumSampleSizeMigration().downgrade()

    CampaignSequencesCustomStopEventsMigration().downgrade()
    CampaignSequencesStopOnMeetingMigration().downgrade()
    CampaignSequencesStopOnClickMigration().downgrade()

    op.drop_constraint("ck_campaigns_sending_window_order", "campaigns", type_="check")
    CampaignsSendingDaysMigration().downgrade()
    CampaignsSendingWindowEndMigration().downgrade()
    CampaignsSendingWindowStartMigration().downgrade()
