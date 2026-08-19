from __future__ import annotations

from datetime import datetime, time
from typing import Any

from pydantic import Field, field_validator, model_validator

from src.modules.campaign.domain.enums import (
    CampaignGoal,
    CampaignPriority,
    CampaignStatus,
    CampaignStep,
    CampaignType,
    DelayUnit,
    RecipientStatus,
    SequenceStepType,
    VariantType,
)
from src.modules.campaign.domain.services import (
    normalize_sending_days,
    validate_sending_window,
    validate_timezone_name,
)
from src.shared.schemas.base_schema import BaseSchema


class _CampaignScheduleFields(BaseSchema):
    timezone: str = Field(default="UTC", min_length=1, max_length=100)
    sending_window_start: time | None = None
    sending_window_end: time | None = None
    sending_days: list[int] = Field(default_factory=lambda: list(range(7)), min_length=1)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        return validate_timezone_name(value)

    @field_validator("sending_days")
    @classmethod
    def validate_days(cls, value: list[int]) -> list[int]:
        return normalize_sending_days(value)

    @model_validator(mode="after")
    def validate_window(self):
        self.sending_days = validate_sending_window(
            self.sending_window_start,
            self.sending_window_end,
            self.sending_days,
        )
        return self


class CreateCampaignRequestSchema(_CampaignScheduleFields):
    name: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=1000)
    campaign_type: CampaignType = CampaignType.REGULAR
    goal: CampaignGoal = CampaignGoal.OUTREACH
    priority: CampaignPriority = CampaignPriority.NORMAL
    email_account_uuid: str | None = None
    template_uuid: str | None = None
    contact_list_uuid: str | None = None
    daily_limit: int | None = Field(default=None, gt=0)
    batch_size: int = Field(default=25, gt=0, le=500)

    @field_validator("name")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("description")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class UpdateCampaignRequestSchema(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=1000)
    goal: CampaignGoal | None = None
    priority: CampaignPriority | None = None
    current_step: CampaignStep | None = None
    timezone: str | None = Field(default=None, min_length=1, max_length=100)
    sending_window_start: time | None = None
    sending_window_end: time | None = None
    sending_days: list[int] | None = Field(default=None, min_length=1)
    email_account_uuid: str | None = None
    template_uuid: str | None = None
    contact_list_uuid: str | None = None
    daily_limit: int | None = Field(default=None, gt=0)
    batch_size: int | None = Field(default=None, gt=0, le=500)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        return validate_timezone_name(value) if value is not None else None

    @field_validator("sending_days")
    @classmethod
    def validate_days(cls, value: list[int] | None) -> list[int] | None:
        return normalize_sending_days(value) if value is not None else None


class ScheduleCampaignRequestSchema(BaseSchema):
    scheduled_at: datetime
    timezone: str = Field(default="UTC", min_length=1, max_length=100)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        return validate_timezone_name(value)


class ProcessCampaignRequestSchema(BaseSchema):
    dry_run: bool = True
    limit: int | None = Field(default=None, gt=0, le=500)


class SequenceStepRequestSchema(BaseSchema):
    step_order: int = Field(gt=0)
    step_type: SequenceStepType
    template_uuid: str | None = None
    subject_override: str | None = Field(default=None, max_length=255)
    body_html_override: str | None = None
    delay_value: int | None = Field(default=None, gt=0)
    delay_unit: DelayUnit | None = None
    is_enabled: bool = True

    @model_validator(mode="after")
    def validate_step(self) -> "SequenceStepRequestSchema":
        if self.step_type == SequenceStepType.EMAIL:
            has_template = bool(self.template_uuid)
            has_override = bool(self.subject_override and self.body_html_override)
            if not has_template and not has_override:
                raise ValueError(
                    "An email step requires template_uuid or subject/body overrides"
                )
            if self.delay_value is not None or self.delay_unit is not None:
                raise ValueError("Email steps cannot contain delay fields")
        elif self.step_type == SequenceStepType.DELAY:
            if self.delay_value is None or self.delay_unit is None:
                raise ValueError("A delay step requires delay_value and delay_unit")
            if self.template_uuid or self.subject_override or self.body_html_override:
                raise ValueError("Delay steps cannot contain email content")
        else:
            raise ValueError("Condition steps are not supported in the selected scope")
        return self


class ConfigureSequenceRequestSchema(BaseSchema):
    stop_on_reply: bool = True
    stop_on_unsubscribe: bool = True
    stop_on_click: bool = False
    stop_on_meeting: bool = False
    custom_stop_events: list[str] = Field(default_factory=list, max_length=20)
    steps: list[SequenceStepRequestSchema] = Field(min_length=1, max_length=30)

    @field_validator("custom_stop_events")
    @classmethod
    def normalize_custom_events(cls, values: list[str]) -> list[str]:
        normalized = sorted({value.strip().casefold() for value in values if value.strip()})
        if any(len(value) > 100 for value in normalized):
            raise ValueError("Custom stop event names cannot exceed 100 characters")
        return normalized

    @model_validator(mode="after")
    def validate_orders(self) -> "ConfigureSequenceRequestSchema":
        if not self.stop_on_unsubscribe:
            raise ValueError("Sequences must always stop after unsubscribe")
        orders = sorted(step.step_order for step in self.steps)
        if orders != list(range(1, len(orders) + 1)):
            raise ValueError("Sequence step_order values must start at 1 and be consecutive")
        if not any(step.step_type == SequenceStepType.EMAIL for step in self.steps):
            raise ValueError("A sequence requires at least one email step")
        return self


class SequencePreviewRequestSchema(BaseSchema):
    starts_at: datetime | None = None


class ABVariantRequestSchema(BaseSchema):
    variant_type: VariantType
    name: str = Field(min_length=1, max_length=50)
    template_uuid: str | None = None
    subject_override: str | None = Field(default=None, max_length=255)
    body_html_override: str | None = None
    allocation_percentage: int = Field(gt=0, lt=100)

    @model_validator(mode="after")
    def validate_content(self) -> "ABVariantRequestSchema":
        if not self.template_uuid and not (
            self.subject_override and self.body_html_override
        ):
            raise ValueError(
                "Each A/B variant requires template_uuid or subject/body overrides"
            )
        return self


class ConfigureABTestRequestSchema(BaseSchema):
    test_percentage: int = Field(default=100, gt=0, le=100)
    winner_metric: str = Field(
        default="reply_rate",
        pattern="^(delivery_rate|open_rate|click_rate|reply_rate)$",
    )
    auto_select_winner: bool = False
    minimum_sample_size: int = Field(default=0, ge=0)
    test_duration_hours: int | None = Field(default=None, gt=0, le=24 * 30)
    variants: list[ABVariantRequestSchema] = Field(min_length=2, max_length=2)

    @model_validator(mode="after")
    def validate_variants(self) -> "ConfigureABTestRequestSchema":
        variant_types = {variant.variant_type for variant in self.variants}
        if variant_types != {VariantType.A, VariantType.B}:
            raise ValueError("A/B testing requires exactly variants A and B")
        if sum(v.allocation_percentage for v in self.variants) != 100:
            raise ValueError("A/B variant allocation must total 100 percent")
        return self


class SelectABWinnerRequestSchema(BaseSchema):
    variant_type: VariantType | None = None


class RecipientEventRequestSchema(BaseSchema):
    event_type: str = Field(
        pattern="^(delivered|opened|clicked|replied|bounced|unsubscribed|meeting|custom)$"
    )
    provider_event_id: str | None = Field(default=None, max_length=255)
    provider_message_id: str | None = Field(default=None, max_length=255)
    custom_event_name: str | None = Field(default=None, max_length=100)
    occurred_at: datetime | None = None
    metadata: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_custom_event(self) -> "RecipientEventRequestSchema":
        if self.event_type == "custom" and not self.custom_event_name:
            raise ValueError("custom_event_name is required for a custom event")
        if self.event_type != "custom" and self.custom_event_name:
            raise ValueError("custom_event_name is only valid for a custom event")
        if self.custom_event_name:
            self.custom_event_name = self.custom_event_name.strip().casefold()
        return self


class ReconcileSendOutcomeRequestSchema(BaseSchema):
    outcome: str = Field(pattern="^(sent|failed|retry)$")
    provider_message_id: str | None = Field(default=None, max_length=255)
    provider_thread_id: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def validate_provider_reference(self) -> "ReconcileSendOutcomeRequestSchema":
        if self.outcome == "sent" and not self.provider_message_id:
            raise ValueError(
                "provider_message_id is required when reconciling an outcome as sent"
            )
        return self


class CampaignResponseSchema(BaseSchema):
    uuid: str
    organization_id: int
    name: str
    description: str | None = None
    campaign_type: str
    goal: str
    priority: str
    status: str
    current_step: str
    email_account_uuid: str | None = None
    email_account_email: str | None = None
    template_uuid: str | None = None
    template_name: str | None = None
    contact_list_uuid: str | None = None
    contact_list_name: str | None = None
    schedule_type: str
    timezone: str
    scheduled_at: datetime | None = None
    sending_window_start: time | None = None
    sending_window_end: time | None = None
    sending_days: list[int]
    daily_limit: int | None = None
    batch_size: int
    total_recipients: int
    sent_count: int
    failed_count: int
    skipped_count: int
    progress_percentage: float
    launched_at: datetime | None = None
    paused_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    archived_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CampaignListResponseSchema(BaseSchema):
    items: list[CampaignResponseSchema]
    total: int
    limit: int
    offset: int


class CampaignDashboardSummarySchema(BaseSchema):
    total_campaigns: int
    active: int
    scheduled: int
    paused: int
    drafts: int
    completed: int
    failed: int


class CampaignRecipientResponseSchema(BaseSchema):
    uuid: str
    contact_id: int | None = None
    email: str
    ab_test_sampled: bool = True
    status: str
    current_step_order: int
    attempt_count: int
    next_attempt_at: datetime | None = None
    provider_message_id: str | None = None
    last_error_code: str | None = None
    last_error_message: str | None = None
    stop_reason: str | None = None
    stopped_at: datetime | None = None
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    failed_at: datetime | None = None
    bounced_at: datetime | None = None
    opened_at: datetime | None = None
    clicked_at: datetime | None = None
    replied_at: datetime | None = None
    unsubscribed_at: datetime | None = None
    created_at: datetime | None = None


class CampaignRecipientListResponseSchema(BaseSchema):
    items: list[CampaignRecipientResponseSchema]
    total: int
    limit: int
    offset: int


class SequenceStepResponseSchema(BaseSchema):
    uuid: str
    step_order: int
    step_type: str
    template_uuid: str | None = None
    template_name: str | None = None
    subject_override: str | None = None
    body_html_override: str | None = None
    delay_value: int | None = None
    delay_unit: str | None = None
    is_enabled: bool


class SequenceResponseSchema(BaseSchema):
    uuid: str
    status: str
    stop_on_reply: bool
    stop_on_unsubscribe: bool
    stop_on_click: bool
    stop_on_meeting: bool
    custom_stop_events: list[str]
    total_steps: int
    steps: list[SequenceStepResponseSchema]


class SequencePreviewStepSchema(BaseSchema):
    step_order: int
    step_type: str
    due_at: datetime
    template_uuid: str | None = None
    delay_value: int | None = None
    delay_unit: str | None = None


class SequencePreviewResponseSchema(BaseSchema):
    starts_at: datetime
    completes_at: datetime
    steps: list[SequencePreviewStepSchema]


class ABVariantResponseSchema(BaseSchema):
    uuid: str
    variant_type: str
    name: str
    template_uuid: str | None = None
    template_name: str | None = None
    subject_override: str | None = None
    body_html_override: str | None = None
    allocation_percentage: int
    sent_count: int
    delivered_count: int
    opened_count: int
    clicked_count: int
    replied_count: int
    failed_count: int


class ABTestResponseSchema(BaseSchema):
    uuid: str
    status: str
    test_percentage: int
    winner_metric: str
    auto_select_winner: bool
    minimum_sample_size: int
    test_duration_hours: int | None = None
    started_at: datetime | None = None
    winner_selected_at: datetime | None = None
    winner_variant_uuid: str | None = None
    sampled_recipient_count: int = 0
    holdout_recipient_count: int = 0
    released_recipient_count: int = 0
    variants: list[ABVariantResponseSchema]


class CampaignReviewResponseSchema(BaseSchema):
    ready: bool
    errors: list[str]
    warnings: list[str]
    audience: dict[str, int]


class CampaignProcessResponseSchema(BaseSchema):
    dry_run: bool
    processed: int
    sent: int
    failed: int
    deferred: int
    skipped: int = 0
    completed: bool
    details: list[dict[str, Any]]


class CampaignAnalyticsResponseSchema(BaseSchema):
    campaign_uuid: str
    total_recipients: int
    pending: int
    sent: int
    delivered: int
    opened: int
    clicked: int
    replied: int
    bounced: int
    failed: int
    unsubscribed: int
    skipped: int
    delivery_rate: float
    open_rate: float
    click_rate: float
    reply_rate: float
    data_fresh_as_of: datetime
