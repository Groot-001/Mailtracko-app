from dataclasses import dataclass, field

from src.shared.domain.entity.base_entity import BaseEntity


@dataclass(kw_only=True)
class OauthConfigEntity(BaseEntity):
    encrypted_refresh_token: str = field(metadata={"description": "Fernet-encrypted OAuth refresh token"})
    organization_id: int | None = field(default=None, metadata={"description": "Workspace owning a non-sender OAuth connection"})
    purpose: str | None = field(default=None, metadata={"description": "Purpose of a shared OAuth connection, e.g. google_sheets"})