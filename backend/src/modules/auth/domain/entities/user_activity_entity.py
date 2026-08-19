from dataclasses import dataclass, field

from src.shared.domain.entity.base_entity import BaseEntity


@dataclass(kw_only=True)
class UserActivityEntity(BaseEntity):
    user_id: int = field(metadata={"description": "FK to sys_auth_users.id"})
    activity_type: str = field(
        metadata={"description": "Type from UserActivityTypeEnum"},
    )
    description: str | None = field(
        default=None,
        metadata={"description": "Human-readable summary"},
    )
    metadata: dict | None = field(
        default=None,
        metadata={"description": "Additional event data"},
    )
