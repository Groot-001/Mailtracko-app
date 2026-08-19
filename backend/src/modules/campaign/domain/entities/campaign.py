from dataclasses import dataclass
from datetime import UTC, datetime, time

from src.modules.campaign.domain.enums import (
    CampaignGoal,
    CampaignPriority,
    CampaignStatus,
    CampaignStep,
    CampaignType,
    ScheduleType,
)
from src.modules.campaign.domain.services.campaign_rules import (
    validate_sending_window,
    validate_timezone_name,
)
from src.shared.domain.entity.base_entity import BaseEntity
from src.shared.domain.mixin.audit_mixin import AuditMixin
from src.shared.domain.mixin.soft_delete_mixin import SoftDeleteMixin


_ALLOWED_STATUS_TRANSITIONS: dict[CampaignStatus, set[CampaignStatus]] = {
    CampaignStatus.DRAFT: {
        CampaignStatus.READY,
        CampaignStatus.SCHEDULED,
        CampaignStatus.LAUNCHING,
        CampaignStatus.CANCELLED,
        CampaignStatus.ARCHIVED,
    },
    CampaignStatus.READY: {
        CampaignStatus.DRAFT,
        CampaignStatus.SCHEDULED,
        CampaignStatus.LAUNCHING,
        CampaignStatus.CANCELLED,
        CampaignStatus.ARCHIVED,
    },
    CampaignStatus.SCHEDULED: {
        CampaignStatus.DRAFT,
        CampaignStatus.LAUNCHING,
        CampaignStatus.CANCELLED,
    },
    CampaignStatus.LAUNCHING: {
        CampaignStatus.RUNNING,
        CampaignStatus.FAILED,
        CampaignStatus.CANCELLED,
    },
    CampaignStatus.RUNNING: {
        CampaignStatus.PAUSED,
        CampaignStatus.COMPLETED,
        CampaignStatus.FAILED,
        CampaignStatus.CANCELLED,
    },
    CampaignStatus.PAUSED: {
        CampaignStatus.RUNNING,
        CampaignStatus.CANCELLED,
    },
    CampaignStatus.COMPLETED: {CampaignStatus.ARCHIVED},
    CampaignStatus.CANCELLED: {CampaignStatus.ARCHIVED},
    CampaignStatus.FAILED: {
        CampaignStatus.DRAFT,
        CampaignStatus.LAUNCHING,
        CampaignStatus.ARCHIVED,
    },
    CampaignStatus.ARCHIVED: set(),
}


@dataclass(kw_only=True)
class Campaign(BaseEntity, AuditMixin, SoftDeleteMixin):
    """Campaign aggregate using MailTracko's integer-id/string-uuid convention."""

    organization_id: int
    name: str
    created_by_id: int | None = None
    updated_by_id: int | None = None

    description: str | None = None
    campaign_type: str = CampaignType.REGULAR.value
    goal: str = CampaignGoal.OUTREACH.value
    priority: str = CampaignPriority.NORMAL.value
    status: str = CampaignStatus.DRAFT.value
    current_step: str = CampaignStep.SETUP.value

    email_account_id: int | None = None
    template_id: int | None = None
    contact_list_id: int | None = None

    schedule_type: str = ScheduleType.IMMEDIATE.value
    timezone: str = "UTC"
    scheduled_at: datetime | None = None
    sending_window_start: time | None = None
    sending_window_end: time | None = None
    sending_days: list[int] | None = None
    daily_limit: int | None = None
    batch_size: int = 25

    total_recipients: int = 0
    sent_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0

    launched_at: datetime | None = None
    paused_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    archived_at: datetime | None = None

    def __post_init__(self) -> None:
        self.name = self._validate_name(self.name)
        self.description = self._validate_description(self.description)
        self.timezone = self._validate_timezone(self.timezone)
        self.sending_days = validate_sending_window(
            self.sending_window_start,
            self.sending_window_end,
            self.sending_days,
        )
        if self.batch_size <= 0:
            raise ValueError("Campaign batch size must be greater than zero.")
        if self.daily_limit is not None and self.daily_limit <= 0:
            raise ValueError("Campaign daily limit must be greater than zero.")

    @staticmethod
    def _validate_name(name: str) -> str:
        normalized = name.strip()
        if not normalized:
            raise ValueError("Campaign name is required.")
        if len(normalized) > 150:
            raise ValueError("Campaign name cannot exceed 150 characters.")
        return normalized

    @staticmethod
    def _validate_description(description: str | None) -> str | None:
        if description is None:
            return None
        normalized = description.strip()
        if not normalized:
            return None
        if len(normalized) > 1000:
            raise ValueError("Campaign description cannot exceed 1000 characters.")
        return normalized

    @staticmethod
    def _validate_timezone(timezone: str) -> str:
        normalized = validate_timezone_name(timezone)
        if len(normalized) > 100:
            raise ValueError("Campaign timezone cannot exceed 100 characters.")
        return normalized

    def transition_to(self, new_status: CampaignStatus) -> None:
        current_status = CampaignStatus(self.status)
        if new_status == current_status:
            return
        if new_status not in _ALLOWED_STATUS_TRANSITIONS[current_status]:
            raise ValueError(
                f"Campaign cannot transition from '{current_status.value}' "
                f"to '{new_status.value}'."
            )
        self.status = new_status.value
        now = datetime.now(UTC)
        if new_status == CampaignStatus.RUNNING and self.launched_at is None:
            self.launched_at = now
        elif new_status == CampaignStatus.PAUSED:
            self.paused_at = now
        elif new_status == CampaignStatus.COMPLETED:
            self.completed_at = now
        elif new_status == CampaignStatus.CANCELLED:
            self.cancelled_at = now
        elif new_status == CampaignStatus.ARCHIVED:
            self.archived_at = now
            self.deleted_at = now
        self.mark_updated()
