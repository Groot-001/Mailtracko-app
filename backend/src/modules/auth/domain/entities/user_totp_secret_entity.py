from dataclasses import dataclass, field

from src.shared.domain.entity.base_entity import BaseEntity


@dataclass(kw_only=True)
class UserTotpSecretEntity(BaseEntity):
    user_id: int = field(metadata={"description": "FK to sys_auth_users.id", "unique": True})
    secret: str = field(metadata={"description": "Encrypted TOTP secret"})
    enabled: bool = field(default=False, metadata={"description": "Whether 2FA is enabled"})
