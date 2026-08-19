from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.shared.domain.entity.base_entity import BaseEntity


@dataclass(kw_only=True)
class UserAccountEntity(BaseEntity):
    """Entity representing an authentication method linked to a user.

    Each user can have multiple accounts (password, Google OAuth).
    The `type` field distinguishes the authentication method, and `hashed_password`
    is only populated for password-type accounts.
    """

    user_id: int = field(metadata={"index": True, "description": "Foreign key to the owning user"})
    type: str = field(default="password", metadata={"description": "Authentication type: password or google"})
    hashed_password: str | None = field(default=None, metadata={"description": "Argon2-hashed password (only for type=password)"})
    provider: str | None = field(default=None, metadata={"description": "OAuth provider name (only for OAuth accounts)"})
    provider_account_id: str | None = field(default=None, metadata={"description": "External user ID from the OAuth provider"})
    last_password_updated_at: datetime | None = field(default=None, metadata={"description": "Timestamp of the last password change"})

    def is_password_account(self) -> bool:
        """Check if this is a password-based authentication account."""
        return self.type == "password"

    def is_oauth_account(self) -> bool:
        """Check if this is an OAuth-based authentication account."""
        return self.type == "google"

    def update_password(self, new_hash: str):
        """Update the hashed password and record the change timestamp."""
        self.hashed_password = new_hash
        self.last_password_updated_at = datetime.now(UTC)
        self.mark_updated()
