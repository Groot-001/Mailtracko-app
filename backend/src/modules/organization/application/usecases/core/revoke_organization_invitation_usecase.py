from src.modules.organization.domain.events.organization_domain_events import (
    OrganizationInvitationRevokedEvent,
)
from src.modules.organization.domain.services.organization_invitation_domain_service import (
    OrganizationInvitationDomainService,
)
from src.modules.organization.domain.services.organization_member_domain_service import (
    OrganizationMemberDomainService,
)
from src.shared.exceptions.base_exceptions import (
    DomainError,
    ForbiddenError,
    ServerError,
)
from src.shared.mediator.mediator import mediator


class RevokeOrganizationInvitationUseCase:
    """
    Use case for revoking organization invitation.
    """

    def __init__(
        self,
        organization_invitation_domain_service: OrganizationInvitationDomainService,
        organization_member_domain_service: OrganizationMemberDomainService,
    ):
        self.organization_invitation_domain_service = (
            organization_invitation_domain_service
        )
        self.organization_member_domain_service = organization_member_domain_service

    async def execute(
        self,
        organization_id: int,
        invitation_uuid: str,
        actor_id: int,
    ) -> dict:
        """
        Revokes a pending organization invitation.
        """
        try:
            await self._ensure_actor_can_revoke(
                organization_id=organization_id,
                actor_id=actor_id,
            )

            invitation = (
                await self.organization_invitation_domain_service.get_invitation_by_uuid(
                    invitation_uuid
                )
            )

            if not invitation or invitation.id is None:
                raise ServerError(
                    error="Failed to revoke organization invitation",
                    internal_details="Invitation not found",
                )

            if invitation.organization_id != organization_id:
                raise ServerError(
                    error="Failed to revoke organization invitation",
                    internal_details="Invitation does not belong to current organization",
                )

            revoked_invitation = (
                await self.organization_invitation_domain_service.revoke_invitation(
                    invitation
                )
            )

            if revoked_invitation.id is None:
                raise ServerError(
                    error="Failed to revoke organization invitation",
                    internal_details="Revoked invitation id is missing",
                )

            revoked_invitation_id = revoked_invitation.id

            revoked_invitation.add_event(
                OrganizationInvitationRevokedEvent(
                    invitation_id=revoked_invitation_id,
                    organization_id=revoked_invitation.organization_id,
                    revoked_by_id=actor_id,
                    invitee_email=revoked_invitation.email,
                )
            )

            for event in revoked_invitation.pull_events():
                await mediator.publish(event)

            return {
                "uuid": revoked_invitation.uuid,
                "email": revoked_invitation.email,
                "role_code": revoked_invitation.role_code,
                "status": revoked_invitation.status,
            }

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="An error occurred while revoking organization invitation",
                internal_details=str(e),
            ) from e

    async def _ensure_actor_can_revoke(
        self,
        *,
        organization_id: int,
        actor_id: int,
    ) -> None:
        """
        Ensures only organization owner or admin can revoke invitations.
        """
        member = (
            await self.organization_member_domain_service.get_member_by_user_and_organization(
                organization_id=organization_id,
                user_id=actor_id,
            )
        )

        if not member or not member.can_manage_members():
            raise ForbiddenError(
                error="Only organization owner or admin can revoke invitations",
                errors={
                    "code": "ONLY_MANAGER_CAN_REVOKE",
                    "message": "Only organization owner or admin can revoke invitations.",
                },
            )