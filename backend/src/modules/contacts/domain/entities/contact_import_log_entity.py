from dataclasses import dataclass, field

from src.modules.contacts.domain.enums.contact_enums import ImportStatusEnum
from src.shared.domain.entity.base_entity import BaseEntity
from src.shared.domain.mixin.audit_mixin import AuditMixin


@dataclass(kw_only=True)
class ContactImportLogEntity(BaseEntity, AuditMixin):
    """
    Tracks an async CSV or Sheets import job.

    Stores totals, errors, and column mapping for auditing.
    """

    organization_id: int = field(metadata={"description": "FK to org_organizations.id"})
    contact_list_id: int | None = field(
        default=None,
        metadata={"description": "Target list FK"},
    )
    filename: str = field(metadata={"description": "Original CSV filename"})
    column_mapping: dict | None = field(
        default=None,
        metadata={"description": "Header -> field mapping"},
    )
    total_rows: int = field(default=0, metadata={"description": "Rows in CSV"})
    success_count: int = field(
        default=0, metadata={"description": "Imported successfully"}
    )
    error_count: int = field(default=0, metadata={"description": "Failed rows"})
    errors: list[dict] | None = field(
        default=None,
        metadata={"description": "Error rows with details"},
    )
    status: str = field(
        default=ImportStatusEnum.PENDING.value,
        metadata={"description": "Import status"},
    )
