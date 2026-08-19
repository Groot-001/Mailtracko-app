from datetime import UTC, datetime

from src.modules.organization.domain.entities.organization_member_entity import (
    OrganizationMemberEntity,
)
from src.modules.organization.domain.enums.organization_enums import (
    OrganizationMemberStatusEnum,
)
from src.modules.organization.domain.events.organization_domain_events import (
    OrganizationInvitationAcceptedEvent,
    OrganizationMemberAddedEvent,
)
from src.modules.organization.domain.services.organization_invitation_domain_service import (
    OrganizationInvitationDomainService,
)
from src.modules.organization.domain.services.organization_member_domain_service import (
    OrganizationMemberDomainService,
)
from src.modules.organization.presentation.schemas.organization_schemas import (
    AcceptOrganizationInvitationRequestSchema,
)
from src.shared.exceptions.base_exceptions import CreateError, DomainError, ServerError
from src.shared.mediator.mediator import mediator


class AcceptOrganizationInvitationUseCase:
    """
    Use case for accepting organization invitation.
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
        payload: AcceptOrganizationInvitationRequestSchema,
        actor_id: int,
        actor_email: str,
    ) -> dict:
        """
        Accepts an invitation and creates organization membership.
        """
        try:
            token_hash = (
                self.organization_invitation_domain_service.hash_invitation_token(
                    payload.token
                )
            )

            invitation = (
                await self.organization_invitation_domain_service.get_invitation_by_token_hash(
                    token_hash
                )
            )

            if not invitation or invitation.id is None:
                raise CreateError(
                    error="Failed to accept organization invitation",
                    internal_details="Invitation not found",
                )

            if invitation.email.lower() != actor_email.lower():
                raise CreateError(
                    error="Failed to accept organization invitation",
                    internal_details="Invitation email does not match current user email",
                )

            await self._ensure_user_can_accept_invitation(user_id=actor_id)

            accepted_invitation = (
                await self.organization_invitation_domain_service.accept_invitation(
                    invitation
                )
            )

            if accepted_invitation.id is None:
                raise CreateError(
                    error="Failed to accept organization invitation",
                    internal_details="Accepted invitation id is missing",
                )

            accepted_invitation_id = accepted_invitation.id

            member = OrganizationMemberEntity(
                organization_id=accepted_invitation.organization_id,
                user_id=actor_id,
                role_code=accepted_invitation.role_code,
                status=OrganizationMemberStatusEnum.ACTIVE.value,
                invited_by_id=accepted_invitation.invited_by_id,
                joined_at=datetime.now(UTC),
                created_by_id=actor_id,
            )

            created_member = await self.organization_member_domain_service.add_member(
                member
            )

            if created_member.id is None:
                raise CreateError(
                    error="Failed to accept organization invitation",
                    internal_details="Failed to create organization member",
                )

            created_member_id = created_member.id

            created_member.add_event(
                OrganizationInvitationAcceptedEvent(
                    invitation_id=accepted_invitation_id,
                    organization_id=accepted_invitation.organization_id,
                    user_id=actor_id,
                    invitee_email=accepted_invitation.email,
                )
            )

            created_member.add_event(
                OrganizationMemberAddedEvent(
                    member_id=created_member_id,
                    user_id=actor_id,
                    organization_id=accepted_invitation.organization_id,
                    role_code=accepted_invitation.role_code,
                )
            )

            for event in created_member.pull_events():
                await mediator.publish(event)

            return {
                "uuid": accepted_invitation.uuid,
                "email": accepted_invitation.email,
                "status": accepted_invitation.status,
                "organization_id": accepted_invitation.organization_id,
                "role_code": created_member.role_code,
                "member_uuid": created_member.uuid,
            }

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="An error occurred while accepting organization invitation",
                internal_details=str(e),
            ) from e

    async def _ensure_user_can_accept_invitation(
        self,
        user_id: int,
    ) -> None:
        """
        Ensures user does not already belong to an organization.
        """
        existing_membership = (
            await self.organization_member_domain_service.get_member_by_user_id(
                user_id=user_id
            )
        )

        if existing_membership:
            raise CreateError(
                error="Failed to accept organization invitation",
                internal_details="User already belongs to an organization",
            )