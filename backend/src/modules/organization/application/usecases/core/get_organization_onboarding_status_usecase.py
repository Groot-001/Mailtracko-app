from src.modules.organization.domain.services.organization_domain_service import (
    OrganizationDomainService,
)
from src.modules.organization.domain.services.organization_invitation_domain_service import (
    OrganizationInvitationDomainService,
)
from src.modules.organization.domain.services.organization_member_domain_service import (
    OrganizationMemberDomainService,
)
from src.shared.exceptions.base_exceptions import DomainError, ServerError


class GetOrganizationOnboardingStatusUseCase:
    """
    Use case for checking whether the current user has completed
    organization onboarding.
    """

    def __init__(
        self,
        organization_domain_service: OrganizationDomainService,
        organization_member_domain_service: OrganizationMemberDomainService,
        organization_invitation_domain_service: OrganizationInvitationDomainService,
    ):
        self.organization_domain_service = organization_domain_service
        self.organization_member_domain_service = organization_member_domain_service
        self.organization_invitation_domain_service = (
            organization_invitation_domain_service
        )

    async def execute(
        self,
        user_id: int,
        actor_email: str,
    ) -> dict:
        """
        Returns organization onboarding status for current user.
        """
        try:
            membership = (
                await self.organization_member_domain_service.get_active_member_by_user_id(
                    user_id=user_id,
                )
            )

            if membership:
                organization = await self.organization_domain_service.get_organization_by_id(
                    organization_id=membership.organization_id,
                )
                return {
                    "has_completed_onboarding": True,
                    "needs_onboarding": False,
                    "has_pending_invitation": False,
                    "invitation_uuid": None,
                    "organization_uuid": organization.uuid if organization else None,
                    "role_code": membership.role_code,
                    "message": "Organization onboarding has already been completed.",
                }

            pending_invitations = await self.organization_invitation_domain_service.get_pending_invitation_by_email_global(
                email=actor_email,
            )

            if pending_invitations:
                invitation = pending_invitations[0]
                return {
                    "has_completed_onboarding": False,
                    "needs_onboarding": False,
                    "has_pending_invitation": True,
                    "invitation_uuid": invitation.uuid,
                    "organization_uuid": None,
                    "role_code": None,
                    "message": "You have a pending organization invitation.",
                }

            return {
                "has_completed_onboarding": False,
                "needs_onboarding": True,
                "has_pending_invitation": False,
                "invitation_uuid": None,
                "organization_uuid": None,
                "role_code": None,
                "message": "Organization onboarding has not been completed.",
            }

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to get organization onboarding status",
                internal_details=str(e),
            ) from e