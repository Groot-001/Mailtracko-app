from datetime import UTC, datetime, timedelta

from src.modules.organization.domain.events.organization_domain_events import (
    OrganizationInvitationCreatedEvent,
)
from src.modules.organization.domain.services.organization_domain_service import (
    OrganizationDomainService,
)
from src.modules.organization.domain.services.organization_invitation_domain_service import (
    OrganizationInvitationDomainService,
)
from src.modules.organization.domain.services.organization_member_domain_service import (
    OrganizationMemberDomainService,
)
from src.shared.exceptions.base_exceptions import DomainError, ForbiddenError, InvalidError, ServerError
from src.shared.mediator.mediator import mediator


class ResendOrganizationInvitationUseCase:
    """Regenerates a pending invitation token and sends a fresh invite email."""

    def __init__(
        self,
        organization_domain_service: OrganizationDomainService,
        organization_invitation_domain_service: OrganizationInvitationDomainService,
        organization_member_domain_service: OrganizationMemberDomainService,
    ):
        self.organization_domain_service = organization_domain_service
        self.organization_invitation_domain_service = organization_invitation_domain_service
        self.organization_member_domain_service = organization_member_domain_service

    async def execute(self, *, organization_id: int, invitation_uuid: str, actor_id: int) -> dict:
        try:
            member = await self.organization_member_domain_service.get_member_by_user_and_organization(
                organization_id=organization_id,
                user_id=actor_id,
            )
            if not member or not member.can_manage_members():
                raise ForbiddenError(error="Only organization owner or admin can resend invitations")

            invitation = await self.organization_invitation_domain_service.get_invitation_by_uuid(invitation_uuid)
            if not invitation or invitation.id is None or invitation.organization_id != organization_id:
                raise InvalidError(error="Invitation was not found in this organization")
            if not invitation.is_pending():
                raise InvalidError(error="Only pending invitation can be resent")

            organization = await self.organization_domain_service.get_organization_by_id(organization_id)
            if not organization:
                raise InvalidError(error="Organization was not found")

            token = self.organization_invitation_domain_service.generate_invitation_token()
            refreshed = await self.organization_invitation_domain_service.resend_invitation(
                invitation,
                token_hash=self.organization_invitation_domain_service.hash_invitation_token(token),
                expires_at=datetime.now(UTC) + timedelta(days=7),
            )
            if refreshed.id is None:
                raise ServerError(error="Failed to resend organization invitation")

            # Reuse the transactional invitation-delivery event. The DB update and
            # email delivery remain in one UOW, so a delivery failure is not reported
            # as a successful resend.
            refreshed.add_event(
                OrganizationInvitationCreatedEvent(
                    invitation_id=refreshed.id,
                    organization_id=organization_id,
                    organization_name=organization.name,
                    inviter_id=actor_id,
                    invitee_email=refreshed.email,
                    token=token,
                )
            )
            for event in refreshed.pull_events():
                await mediator.publish(event, raise_on_error=True)

            return {
                "uuid": refreshed.uuid,
                "email": refreshed.email,
                "role_code": refreshed.role_code,
                "status": refreshed.status,
                "expires_at": refreshed.expires_at,
                "created_at": refreshed.created_at,
                "updated_at": refreshed.updated_at,
            }
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="An error occurred while resending organization invitation",
                internal_details=str(e),
            ) from e
