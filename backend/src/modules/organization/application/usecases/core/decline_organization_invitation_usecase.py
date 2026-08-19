from src.modules.organization.domain.events.organization_domain_events import (
    OrganizationInvitationDeclinedEvent,
)
from src.modules.organization.domain.services.organization_invitation_domain_service import (
    OrganizationInvitationDomainService,
)
from src.modules.organization.presentation.schemas.organization_schemas import (
    DeclineOrganizationInvitationRequestSchema,
)
from src.shared.exceptions.base_exceptions import CreateError, DomainError, ServerError
from src.shared.mediator.mediator import mediator


class DeclineOrganizationInvitationUseCase:
    """
    Use case for declining organization invitation.
    """

    def __init__(
        self,
        organization_invitation_domain_service: OrganizationInvitationDomainService,
    ):
        self.organization_invitation_domain_service = (
            organization_invitation_domain_service
        )

    async def execute(
        self,
        payload: DeclineOrganizationInvitationRequestSchema,
        actor_email: str,
        actor_id: int | None,
    ) -> dict:
        """
        Declines an invitation using token and logged-in email.
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
                    error="Failed to decline organization invitation",
                    internal_details="Invitation not found",
                )

            if invitation.email.lower() != actor_email.lower():
                raise CreateError(
                    error="Failed to decline organization invitation",
                    internal_details="Invitation email does not match current user email",
                )

            declined_invitation = (
                await self.organization_invitation_domain_service.decline_invitation(
                    invitation
                )
            )
            if declined_invitation.id is None:
                raise ServerError(
                    error="Failed to decline organization invitation",
                    internal_details="Declined invitation id is missing",
         )

            declined_invitation_id = declined_invitation.id

            declined_invitation.add_event(
                OrganizationInvitationDeclinedEvent(
                    invitation_id=declined_invitation_id,
                    organization_id=declined_invitation.organization_id,
                    invitee_email=declined_invitation.email,
                    actor_user_id=actor_id,
                )
            )
            for event in declined_invitation.pull_events():
                await mediator.publish(event)

            return {
                "uuid": declined_invitation.uuid,
                "email": declined_invitation.email,
                "status": declined_invitation.status,
            }

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="An error occurred while declining organization invitation",
                internal_details=str(e),
            ) from e
