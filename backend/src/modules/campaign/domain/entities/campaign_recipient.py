from dataclasses import dataclass, field
from datetime import datetime

from src.modules.campaign.domain.enums import RecipientStatus
from src.shared.domain.entity.base_entity import BaseEntity


@dataclass(kw_only=True)
class CampaignRecipient(BaseEntity):
    organization_id: int
    campaign_id: int
    email: str
    normalized_email: str
    contact_id: int | None = None
    sequence_step_id: int | None = None
    ab_variant_id: int | None = None
    personalization_data: dict = field(default_factory=dict)
    status: str = RecipientStatus.PENDING.value
    current_step_order: int = 1
    attempt_count: int = 0
    next_attempt_at: datetime | None = None
    provider_message_id: str | None = None
    last_error_code: str | None = None
    last_error_message: str | None = None
    queued_at: datetime | None = None
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    failed_at: datetime | None = None
    opened_at: datetime | None = None
    clicked_at: datetime | None = None
    replied_at: datetime | None = None
