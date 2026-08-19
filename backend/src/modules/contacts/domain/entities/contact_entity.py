from dataclasses import dataclass, field
from datetime import datetime

from src.shared.domain.entity.base_entity import BaseEntity


@dataclass(kw_only=True)
class ContactEntity(BaseEntity):
    """
    Represents a single contact record within a list.

    Contacts are created via CSV or Sheets import only.
    The subscribed flag is managed by the campaign module.
    """

    organization_id: int = field(metadata={"description": "FK to org_organizations.id"})
    contact_list_id: int = field(metadata={"description": "FK to contact_lists.id"})
    email: str = field(
        metadata={
            "description": "Email address (unique per list, stored lowercase)",
        },
    )
    metadata: dict | None = field(
        default=None,
        metadata={"description": "Extra CSV/Sheet columns as JSONB"},
    )
    subscribed: bool = field(
        default=True,
        metadata={"description": "True = subscribed, False = unsubscribed by campaign"},
    )
    unsubscribed_at: datetime | None = field(
        default=None,
        metadata={"description": "When campaign set subscribed=false"},
    )
    last_contacted_at: datetime | None = field(
        default=None,
        metadata={"description": "When last emailed"},
    )
    status: str = "active"
    verification_status: str = "unverified"
    verification_sub_status: str | None = None
    verification_score: int | None = None
    verification_details: dict | None = None
    verified_at: datetime | None = None
    bounce_risk: str | None = None
    last_bounced_at: datetime | None = None
    archived_at: datetime | None = None
