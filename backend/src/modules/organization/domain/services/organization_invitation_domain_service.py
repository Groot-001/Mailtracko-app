import hashlib
import secrets

from src.modules.organization.domain.entities.organization_invitation_entity import (
    OrganizationInvitationEntity,
)
from src.modules.organization.domain.enums.organization_enums import (
    OrganizationInvitationStatusEnum,
    OrganizationRoleCodeEnum,
)
from src.modules.organization.domain.repositories.organization_invitation_repository import (
    IOrganizationInvitationRepository,
)
from src.shared.exceptions.base_exceptions import (
    ConflictError,
    CreateError,
    DomainError,
    InvalidError,
    ServerError,
)


class OrganizationInvitationDomainService:
    """
    Service class for organization invitation domain logic.
    """

    INVITABLE_ROLES = {
        OrganizationRoleCodeEnum.ADMIN.value,
        OrganizationRoleCodeEnum.MEMBER.value,
    }

    def __init__(self, repository: IOrganizationInvitationRepository):
        self.repository = repository

    async def create_invitation(
        self,
        invitation_entity: OrganizationInvitationEntity,
    ) -> OrganizationInvitationEntity:
        """
        Creates organization invitation.

        Invitation is created for an email and role_code.
        The invited user becomes a member only after accepting the invitation.
        """
        try:
            self._ensure_valid_invitation_role(invitation_entity.role_code)

            invitation_entity.email = invitation_entity.email.lower()
            invitation_entity.status = OrganizationInvitationStatusEnum.PENDING.value

            existing_invitation = await self.repository.get_pending_by_email(
                organization_id=invitation_entity.organization_id,
                email=invitation_entity.email,
            )

            if existing_invitation:
                raise ConflictError(
                    error="Pending invitation already exists for this email"
                )

            return await self.repository.add(invitation_entity)

        except DomainError:
            raise
        except Exception as e:
            raise CreateError(
                error="Failed to create organization invitation",
                internal_details=str(e),
            ) from e

    async def get_invitation_by_uuid(
        self,
        invitation_uuid: str,
    ) -> OrganizationInvitationEntity | None:
        """
        Retrieves organization invitation by UUID.
        """
        try:
            return await self.repository.get_by(uuid=invitation_uuid)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to retrieve invitation",
                internal_details=str(e),
            ) from e

    async def get_invitation_by_token_hash(
        self,
        token_hash: str,
    ) -> OrganizationInvitationEntity | None:
        """
        Retrieves organization invitation by token hash.
        """
        try:
            return await self.repository.get_by_token_hash(token_hash=token_hash)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to retrieve invitation",
                internal_details=str(e),
            ) from e

    async def get_pending_invitation_by_email(
        self,
        *,
        organization_id: int,
        email: str,
    ) -> OrganizationInvitationEntity | None:
        """
        Retrieves pending invitation by organization and email.
        """
        try:
            return await self.repository.get_pending_by_email(
                organization_id=organization_id,
                email=email.lower(),
            )
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to retrieve pending invitation",
                internal_details=str(e),
            ) from e

    async def get_pending_invitation_by_email_global(
        self,
        email: str,
    ) -> list[OrganizationInvitationEntity]:
        """
        Retrieves all pending invitations by email across all organizations.
        """
        try:
            return await self.repository.get_pending_by_email_global(
                email=email.lower(),
            )
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to retrieve pending invitations",
                internal_details=str(e),
            ) from e

    async def list_paginated(
        self,
        *,
        organization_id: int,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[OrganizationInvitationEntity], int]:
        """
        Lists organization invitations.

        UI uses this to show invited users who have not accepted yet.
        """
        try:
            return await self.repository.list_paginated(
                organization_id=organization_id,
                status=status,
                limit=limit,
                offset=offset,
            )
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to list organization invitations",
                internal_details=str(e),
            ) from e

    async def accept_invitation(
        self,
        invitation_entity: OrganizationInvitationEntity,
    ) -> OrganizationInvitationEntity:
        """
        Accepts organization invitation.

        This only updates invitation status.
        The usecase creates organization_members row after this.
        """
        try:
            self._ensure_invitation_can_be_accepted(invitation_entity)

            invitation_entity.mark_accepted()

            return await self.repository.update(invitation_entity)

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to accept organization invitation",
                internal_details=str(e),
            ) from e

    async def decline_invitation(
        self,
        invitation_entity: OrganizationInvitationEntity,
    ) -> OrganizationInvitationEntity:
        """
        Declines organization invitation.
        """
        try:
            if not invitation_entity.can_be_declined():
                raise InvalidError(error="Only pending invitation can be declined")

            invitation_entity.mark_declined()

            return await self.repository.update(invitation_entity)

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to decline organization invitation",
                internal_details=str(e),
            ) from e

    async def revoke_invitation(
        self,
        invitation_entity: OrganizationInvitationEntity,
    ) -> OrganizationInvitationEntity:
        """
        Revokes organization invitation.

        This is used when owner/admin cancels a pending invitation.
        """
        try:
            if not invitation_entity.is_pending():
                raise InvalidError(error="Only pending invitation can be revoked")

            invitation_entity.mark_revoked()

            return await self.repository.update(invitation_entity)

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to revoke organization invitation",
                internal_details=str(e),
            ) from e

    async def resend_invitation(
        self,
        invitation_entity: OrganizationInvitationEntity,
        *,
        token_hash: str,
        expires_at,
    ) -> OrganizationInvitationEntity:
        """Refreshes a pending invitation so a new link can be delivered."""
        try:
            if not invitation_entity.is_pending():
                raise InvalidError(error="Only pending invitation can be resent")

            invitation_entity.refresh_for_resend(
                token_hash=token_hash,
                expires_at=expires_at,
            )
            return await self.repository.update(invitation_entity)
        except DomainError:
            raise
        except ValueError as e:
            raise InvalidError(error=str(e)) from e
        except Exception as e:
            raise ServerError(
                error="Failed to resend organization invitation",
                internal_details=str(e),
            ) from e

    def generate_invitation_token(self) -> str:
        """
        Generates raw invitation token.

        Raw token is sent through email link.
        Only hashed token is stored in database.
        """
        return secrets.token_urlsafe(32)

    def hash_invitation_token(self, token: str) -> str:
        """
        Hashes invitation token before storing/checking it.
        """
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _ensure_invitation_can_be_accepted(
        self,
        invitation_entity: OrganizationInvitationEntity,
    ) -> None:
        """
        Ensures invitation is valid for acceptance.
        """
        if not invitation_entity.is_pending():
            raise InvalidError(error="Invitation is not pending")

        if invitation_entity.is_expired():
            raise InvalidError(error="Invitation has expired")

    def _ensure_valid_invitation_role(
        self,
        role_code: str,
    ) -> None:
        """
        Ensures only admin/member roles can be invited.

        Owner is created only when organization is created.
        """
        if role_code not in self.INVITABLE_ROLES:
            raise InvalidError(error="Invalid invitation role")
