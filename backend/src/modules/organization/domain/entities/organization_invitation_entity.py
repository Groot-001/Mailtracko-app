from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.modules.organization.domain.enums.organization_enums import (
    OrganizationInvitationStatusEnum,
)
from src.shared.domain.entity.base_entity import BaseEntity
from src.shared.domain.mixin.audit_mixin import AuditMixin


@dataclass(kw_only=True)
class OrganizationInvitationEntity(BaseEntity, AuditMixin):
    """
    Entity representing an invitation to join an organization.
    """

    organization_id: int = field(
        metadata={
            "description": "Organization id",
            "index": True,
            "on_delete": "cascade",
        }
    )

    email: str = field(
        metadata={
            "description": "Invited user's email address",
            "index": True,
        }
    )

    role_code: str = field(
        metadata={
            "description": "Role code assigned after invitation acceptance",
            "index": True,
        }
    )

    token_hash: str = field(
        metadata={
            "description": "Hashed invitation token",
            "unique": True,
            "index": True,
        }
    )

    invited_by_id: int = field(
        metadata={
            "description": "User id who sent the invitation",
            "index": True,
            "on_delete": "restrict",
        }
    )

    status: str = field(
        default="pending",
        metadata={
            "description": "Invitation status such as pending, accepted, declined, revoked, or expired",
            "index": True,
        },
    )

    expires_at: datetime = field(
        metadata={
            "description": "Date and time when this invitation expires",
            "index": True,
        }
    )

    accepted_at: datetime | None = field(default=None)
    declined_at: datetime | None = field(default=None)
    revoked_at: datetime | None = field(default=None)

    def is_pending(self) -> bool:
        """
        Returns True if invitation status is pending.
        """
        return self.status == OrganizationInvitationStatusEnum.PENDING.value

    def is_expired(self) -> bool:
        """
        Returns True if the invitation has passed its expiry date.
        """
        return datetime.now(UTC) > self.expires_at

    def is_accepted(self) -> bool:
        """
        Returns True if invitation status is accepted.
        """
        return self.status == OrganizationInvitationStatusEnum.ACCEPTED.value

    def is_declined(self) -> bool:
        """
        Returns True if invitation status is declined.
        """
        return self.status == OrganizationInvitationStatusEnum.DECLINED.value

    def is_revoked(self) -> bool:
        """
        Returns True if invitation status is revoked.
        """
        return self.status == OrganizationInvitationStatusEnum.REVOKED.value

    def can_be_accepted(self) -> bool:
        """
        Returns True if the invitation is still pending and not expired.
        """
        return self.is_pending() and not self.is_expired()

    def can_be_declined(self) -> bool:
        """
        Returns True if the invitation can still be declined.
        """
        return self.is_pending() and not self.is_expired()

    def mark_accepted(self) -> None:
        """
        Marks invitation as accepted.
        """
        self.status = OrganizationInvitationStatusEnum.ACCEPTED.value
        self.accepted_at = datetime.now(UTC)
        self.mark_updated()

    def mark_declined(self) -> None:
        """
        Marks invitation as declined.
        """
        self.status = OrganizationInvitationStatusEnum.DECLINED.value
        self.declined_at = datetime.now(UTC)
        self.mark_updated()

    def mark_revoked(self) -> None:
        """
        Marks invitation as revoked.
        """
        self.status = OrganizationInvitationStatusEnum.REVOKED.value
        self.revoked_at = datetime.now(UTC)
        self.mark_updated()

    def refresh_for_resend(self, *, token_hash: str, expires_at: datetime) -> None:
        """Refreshes a pending invitation with a new token and expiry."""
        if not self.is_pending():
            raise ValueError("Only pending invitations can be resent")
        self.token_hash = token_hash
        self.expires_at = expires_at
        self.mark_updated()
