from datetime import datetime, time

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.model.audit_mixin_model import AuditMixinModel
from src.shared.infrastructure.model.base_model import BaseModel
from src.shared.infrastructure.model.soft_delete_mixin_model import SoftDeleteMixinModel


class CampaignModel(BaseModel, AuditMixinModel, SoftDeleteMixinModel):
    __tablename__ = "campaigns"

    __table_args__ = (
        Index("ix_campaigns_org_status", "organization_id", "status"),
        Index("ix_campaigns_status_scheduled", "status", "scheduled_at"),
        CheckConstraint("batch_size > 0", name="ck_campaigns_batch_size_positive"),
        CheckConstraint(
            "daily_limit IS NULL OR daily_limit > 0",
            name="ck_campaigns_daily_limit_positive",
        ),
        CheckConstraint(
            "sending_window_start IS NULL OR sending_window_end IS NULL "
            "OR sending_window_start < sending_window_end",
            name="ck_campaigns_sending_window_order",
        ),
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("org_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    campaign_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="regular", index=True
    )
    goal: Mapped[str] = mapped_column(String(50), nullable=False, default="outreach")
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default="normal", index=True
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="draft", index=True
    )
    current_step: Mapped[str] = mapped_column(
        String(30), nullable=False, default="setup"
    )

    email_account_id: Mapped[int | None] = mapped_column(
        ForeignKey("email_accounts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    template_id: Mapped[int | None] = mapped_column(
        ForeignKey("templates.id", ondelete="SET NULL"), nullable=True, index=True
    )
    contact_list_id: Mapped[int | None] = mapped_column(
        ForeignKey("contact_lists.id", ondelete="RESTRICT"), nullable=True, index=True
    )

    schedule_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="immediate"
    )
    timezone: Mapped[str] = mapped_column(String(100), nullable=False, default="UTC")
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    sending_window_start: Mapped[time | None] = mapped_column(Time(), nullable=True)
    sending_window_end: Mapped[time | None] = mapped_column(Time(), nullable=True)
    sending_days: Mapped[list[int]] = mapped_column(
        JSON, nullable=False, default=lambda: list(range(7))
    )
    daily_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    batch_size: Mapped[int] = mapped_column(Integer, nullable=False, default=25)

    total_recipients: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    launched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    paused_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class CampaignRecipientModel(BaseModel):
    __tablename__ = "campaign_recipients"

    __table_args__ = (
        UniqueConstraint(
            "campaign_id", "normalized_email", name="uq_campaign_recipient_email"
        ),
        Index("ix_campaign_recipients_campaign_status", "campaign_id", "status"),
        Index(
            "ix_campaign_recipients_campaign_ab_sample",
            "campaign_id",
            "ab_test_sampled",
            "status",
        ),
        Index(
            "ix_campaign_recipients_campaign_due",
            "campaign_id",
            "status",
            "next_attempt_at",
        ),
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("org_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("contact_contacts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    sequence_step_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaign_sequence_steps.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    ab_variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaign_ab_variants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    email: Mapped[str] = mapped_column(String(320), nullable=False)
    normalized_email: Mapped[str] = mapped_column(String(320), nullable=False)
    personalization_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ab_test_sampled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending", index=True
    )
    current_step_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    provider_message_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    provider_thread_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    stop_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    stopped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    queued_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    failed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    bounced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    opened_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    clicked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    replied_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    unsubscribed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class CampaignSequenceModel(BaseModel):
    __tablename__ = "campaign_sequences"

    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("org_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="not_started", index=True
    )
    stop_on_reply: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    stop_on_unsubscribe: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    stop_on_click: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    stop_on_meeting: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    custom_stop_events: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )
    total_steps: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class CampaignSequenceStepModel(BaseModel):
    __tablename__ = "campaign_sequence_steps"

    __table_args__ = (
        UniqueConstraint("sequence_id", "step_order", name="uq_sequence_step_order"),
        CheckConstraint("step_order > 0", name="ck_sequence_step_order_positive"),
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("org_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sequence_id: Mapped[int] = mapped_column(
        ForeignKey("campaign_sequences.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    step_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    template_id: Mapped[int | None] = mapped_column(
        ForeignKey("templates.id", ondelete="SET NULL"), nullable=True, index=True
    )
    subject_override: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body_html_override: Mapped[str | None] = mapped_column(Text, nullable=True)
    delay_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    delay_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class CampaignABTestModel(BaseModel):
    __tablename__ = "campaign_ab_tests"

    __table_args__ = (
        CheckConstraint(
            "test_percentage > 0 AND test_percentage <= 100",
            name="ck_campaign_ab_tests_percentage",
        ),
        CheckConstraint(
            "minimum_sample_size >= 0",
            name="ck_campaign_ab_tests_minimum_sample_size",
        ),
        CheckConstraint(
            "test_duration_hours IS NULL OR test_duration_hours > 0",
            name="ck_campaign_ab_tests_duration_positive",
        ),
    )

    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("org_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="draft", index=True
    )
    test_percentage: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    winner_metric: Mapped[str] = mapped_column(
        String(30), nullable=False, default="reply_rate"
    )
    auto_select_winner: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    minimum_sample_size: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    test_duration_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    winner_variant_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "campaign_ab_variants.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_campaign_ab_tests_winner_variant_id",
        ),
        nullable=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    winner_selected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class CampaignABVariantModel(BaseModel):
    __tablename__ = "campaign_ab_variants"

    __table_args__ = (
        UniqueConstraint("ab_test_id", "variant_type", name="uq_ab_test_variant_type"),
        CheckConstraint(
            "allocation_percentage > 0 AND allocation_percentage < 100",
            name="ck_ab_variant_allocation",
        ),
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("org_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ab_test_id: Mapped[int] = mapped_column(
        ForeignKey("campaign_ab_tests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    variant_type: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    template_id: Mapped[int | None] = mapped_column(
        ForeignKey("templates.id", ondelete="SET NULL"), nullable=True, index=True
    )
    subject_override: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body_html_override: Mapped[str | None] = mapped_column(Text, nullable=True)
    allocation_percentage: Mapped[int] = mapped_column(
        Integer, nullable=False, default=50
    )
    sent_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    delivered_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    opened_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clicked_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    replied_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class CampaignMessageModel(BaseModel):
    """One durable logical send per campaign recipient, sequence step and variant."""

    __tablename__ = "campaign_messages"

    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_campaign_message_idempotency_key"),
        Index("ix_campaign_messages_campaign_status", "campaign_id", "status"),
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("org_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("campaign_recipients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sequence_step_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaign_sequence_steps.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    ab_variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaign_ab_variants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending", index=True
    )
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    provider_message_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    provider_thread_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subject_snapshot: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preheader_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_html_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    from_name_snapshot: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sending_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    failed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reconciled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class CampaignMessageEventModel(BaseModel):
    """Append-only normalized event ledger for campaign analytics and deduplication."""

    __tablename__ = "campaign_message_events"

    __table_args__ = (
        UniqueConstraint("dedupe_key", name="uq_campaign_message_event_dedupe_key"),
        Index("ix_campaign_message_events_campaign_type", "campaign_id", "event_type"),
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("org_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("campaign_recipients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    message_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaign_messages.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    custom_event_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provider_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dedupe_key: Mapped[str] = mapped_column(String(64), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    event_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)


class CampaignSuppressionModel(BaseModel):
    """Campaign-owned organization suppression record without changing Contacts logic."""

    __tablename__ = "campaign_suppressions"

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "normalized_email", name="uq_campaign_suppression_email"
        ),
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("org_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    normalized_email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String(50), nullable=False)
    source_campaign_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source_recipient_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaign_recipients.id", ondelete="SET NULL"), nullable=True
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    suppressed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class CampaignStateHistoryModel(BaseModel):
    __tablename__ = "campaign_state_history"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("org_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_auth_users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    from_status: Mapped[str] = mapped_column(String(30), nullable=False)
    to_status: Mapped[str] = mapped_column(String(30), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    transitioned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
