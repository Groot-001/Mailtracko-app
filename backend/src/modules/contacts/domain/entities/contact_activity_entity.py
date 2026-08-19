from dataclasses import dataclass, field

from src.shared.domain.entity.base_entity import BaseEntity


@dataclass(kw_only=True)
class ContactActivityEntity(BaseEntity):
    """
    Activity log entry for a contact's timeline.

    Records events like import, merge, and unsubscribe.
    """

    contact_id: int = field(metadata={"description": "FK to contact_contacts.id"})
    organization_id: int = field(metadata={"description": "FK to org_organizations.id"})
    activity_type: str = field(
        metadata={"description": "Type from ContactActivityTypeEnum"},
    )
    description: str | None = field(
        default=None,
        metadata={"description": "Human-readable summary"},
    )
    metadata: dict | None = field(
        default=None,
        metadata={"description": "Additional event data"},
    )
