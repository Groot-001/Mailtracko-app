from dataclasses import dataclass, field
from datetime import datetime

from src.shared.domain.entity.base_entity import BaseEntity


@dataclass(kw_only=True)
class UserTotpRecoveryCodeEntity(BaseEntity):
    user_id: int = field(metadata={"description": "FK to sys_auth_users.id"})
    code_hash: str = field(metadata={"description": "SHA256 hash of recovery code"})
    used_at: datetime | None = field(default=None, metadata={"description": "When the code was used"})
