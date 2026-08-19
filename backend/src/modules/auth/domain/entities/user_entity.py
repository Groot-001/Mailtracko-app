from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


from src.shared.domain.entity.base_entity import BaseEntity
from src.shared.domain.mixin.audit_mixin import AuditMixin
from src.shared.domain.mixin.soft_delete_mixin import SoftDeleteMixin


@dataclass(kw_only=True)
class UserEntity(BaseEntity, AuditMixin, SoftDeleteMixin):
    """Entity representing a registered user in the system.

    A user can have multiple auth accounts (password or Google),
    belongs to organizations, and is the central identity for all platform activity.
    """

    full_name: str = field(metadata={"description": "Display name of the user"})
    email: str = field(metadata={"unique": True, "index": True, "description": "Primary email address used for login and notifications"})
    profile_image: str | None = field(default=None, metadata={"description": "URL or path to profile image"})
    timezone: str | None = field(default=None, metadata={"description": "User timezone (e.g. America/New_York)"})
    phone: str | None = field(default=None, metadata={"description": "Phone number"})
    country_code: str | None = field(default=None, metadata={"description": "Country code for phone (e.g. +1)"})
    location: str | None = field(default=None, metadata={"description": "User location"})
    theme: str = field(default="light", metadata={"description": "UI theme preference: light or dark"})
    is_active: bool = field(default=True, metadata={"description": "Whether the user account is active or disabled"})
    last_login_at: datetime | None = field(default=None, metadata={"description": "Timestamp of the user's most recent login"})
    email_verified_at: datetime | None = field(default=None, metadata={"description": "Timestamp when the user verified their email address"})
    scheduled_deletion_at: datetime | None = field(default=None, metadata={"description": "If set, the account will be soft-deleted at this timestamp unless the user logs in before then"})

    def is_email_verified(self) -> bool:
        """Check if the user's email has been verified."""
        return self.email_verified_at is not None

    def mark_email_verified(self):
        """Mark the user's email as verified with the current timestamp."""
        self.email_verified_at = datetime.now(UTC)

    def mark_last_login(self):
        """Update the last login timestamp to now."""
        self.last_login_at = datetime.now(UTC)

    def is_deleted(self) -> bool:
        """Check if the user has been soft-deleted."""
        return self.deleted_at is not None

    def has_active_deletion_schedule(self) -> bool:
        """Check if the account is scheduled for deletion and the grace period hasn't expired."""
        if not self.scheduled_deletion_at:
            return False
        return datetime.now(UTC) < self.scheduled_deletion_at

    def is_deletion_schedule_expired(self) -> bool:
        """Check if the scheduled deletion time has passed."""
        if not self.scheduled_deletion_at:
            return False
        return datetime.now(UTC) >= self.scheduled_deletion_at

    def schedule_deletion(self, grace_days: int = 3):
        """Schedule account deletion after a grace period."""
        self.scheduled_deletion_at = datetime.now(UTC) + timedelta(days=grace_days)
        self.mark_updated()

    def cancel_scheduled_deletion(self):
        """Cancel a pending scheduled deletion."""
        self.scheduled_deletion_at = None
        self.mark_updated()

    @staticmethod
    def generate_random_avatar_bg() -> str:
        """Generate a random hex background color for the user's avatar."""
        import random
        return f"#{random.randint(0, 0xFFFFFF):06x}"
