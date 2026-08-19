from dataclasses import dataclass, field

from src.shared.domain.entity.base_entity import BaseEntity
from src.shared.domain.mixin.audit_mixin import AuditMixin
from src.shared.domain.mixin.soft_delete_mixin import SoftDeleteMixin


@dataclass(kw_only=True)
class ContactListEntity(BaseEntity, AuditMixin, SoftDeleteMixin):
    """
    Represents an independent contact list.

    Each list is self-contained with its own contacts and field definitions.
    """

    organization_id: int = field(metadata={"description": "FK to org_organizations.id"})
    name: str = field(metadata={"description": "List name"})
    description: str | None = field(
        default=None, metadata={"description": "Optional description"}
    )
    field_definitions: list[str] | None = field(
        default=None,
        metadata={"description": "Extra column names from CSV/Sheet imports"},
    )
