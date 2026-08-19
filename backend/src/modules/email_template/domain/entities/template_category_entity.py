from dataclasses import dataclass, field

from src.shared.domain.entity.base_entity import BaseEntity
from src.shared.domain.mixin.audit_mixin import AuditMixin
from src.shared.domain.mixin.soft_delete_mixin import SoftDeleteMixin


@dataclass(kw_only=True)
class TemplateCategoryEntity(BaseEntity, AuditMixin, SoftDeleteMixin):
    """
    Entity representing a system template category.
    """

    name: str = field(
        metadata={
            "description": "Template category name",
        }
    )

    organization_id: int | None = field(
        default=None,
        metadata={
            "description": "Owning organization id; null denotes a global category",
        },
    )

    description: str | None = field(
        default=None,
        metadata={
            "description": "Short description of the template category",
        },
    )

    display_order: int = field(
        default=0,
        metadata={
            "description": "Display order of the category in the template gallery",
            "index": True,
        },
    )

    is_active: bool = field(
        default=True,
        metadata={
            "description": "Whether the template category is active and visible",
            "index": True,
        },
    )