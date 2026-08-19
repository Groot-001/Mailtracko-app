from dataclasses import dataclass, field

from src.shared.domain.entity.base_entity import BaseEntity
from src.shared.domain.mixin.audit_mixin import AuditMixin
from src.shared.domain.mixin.soft_delete_mixin import SoftDeleteMixin


@dataclass(kw_only=True)
class OrganizationActivityEntity(BaseEntity, AuditMixin, SoftDeleteMixin):
    """
    Entity representing a recent organization activity item.
    """

    organization_id: int = field(
        metadata={
            "description": "Organization id where the activity happened",
            "index": True,
            "on_delete": "cascade",
        }
    )

    activity_type: str = field(
        metadata={
            "description": "Type of organization activity",
            "index": True,
        }
    )

    title: str = field(
        metadata={
            "description": "Activity title shown in recent activity UI",
        }
    )

    actor_user_id: int | None = field(
        default=None,
        metadata={
            "description": "User id who performed the activity",
            "index": True,
            "on_delete": "set_null",
        },
    )

    target_user_id: int | None = field(
        default=None,
        metadata={
            "description": "User id affected by the activity",
            "index": True,
            "on_delete": "set_null",
        },
    )

    target_email: str | None = field(
        default=None,
        metadata={
            "description": "Target email affected by invitation activity",
            "index": True,
        },
    )