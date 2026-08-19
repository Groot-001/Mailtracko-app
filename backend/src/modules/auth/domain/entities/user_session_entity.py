from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.shared.domain.entity.base_entity import BaseEntity
from src.shared.domain.mixin.audit_mixin import AuditMixin


@dataclass(kw_only=True)
class UserSessionEntity(BaseEntity, AuditMixin):
    """Entity representing an active user session.

    Tracks login sessions with device metadata and expiration.
    Sessions can be revoked for security purposes (e.g., logout from other devices).
    """

    user_id: int = field(metadata={"index": True, "description": "Foreign key to the owning user"})
    expires_at: datetime = field(metadata={"description": "Timestamp when the session expires"})
    ip_address: str | None = field(default=None, metadata={"description": "IP address from which the session was created"})
    user_agent: str | None = field(default=None, metadata={"description": "User agent string of the client browser/device"})
    revoked_at: datetime | None = field(default=None, metadata={"description": "Timestamp when the session was revoked"})

    def is_expired(self) -> bool:
        """Check if the session has expired based on the current time."""
        return datetime.now(UTC) > self.expires_at

    def is_revoked(self) -> bool:
        """Check if the session has been manually revoked."""
        return self.revoked_at is not None

    def revoke(self):
        """Revoke the session with the current timestamp."""
        self.revoked_at = datetime.now(UTC)
        self.mark_updated()
