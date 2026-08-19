from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.shared.domain.entity.base_entity import BaseEntity


@dataclass(kw_only=True)
class UserTokenEntity(BaseEntity):
    """Entity representing a one-time security token for a user.

    Used for password reset, email verification, and other token-gated flows.
    Tokens are stored as hashes and expire after a configured duration.
    """

    user_id: int = field(metadata={"index": True, "description": "Foreign key to the owning user"})
    type: str = field(metadata={"index": True, "description": "Token purpose: password_reset, email_verify, etc."})
    token_hash: str = field(metadata={"index": True, "description": "SHA-256 hash of the raw token value"})
    expires_at: datetime = field(metadata={"description": "Timestamp when the token expires"})
    used_at: datetime | None = field(default=None, metadata={"description": "Timestamp when the token was consumed"})

    def is_expired(self) -> bool:
        """Check if the token has expired based on the current time."""
        return datetime.now(UTC) > self.expires_at

    def is_used(self) -> bool:
        """Check if the token has already been consumed."""
        return self.used_at is not None

    def mark_used(self):
        """Mark the token as consumed with the current timestamp."""
        self.used_at = datetime.now(UTC)
        self.mark_updated()
