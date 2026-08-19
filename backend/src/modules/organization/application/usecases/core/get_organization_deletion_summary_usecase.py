from src.core.config.settings import config
from src.modules.organization.domain.enums.organization_enums import (
    OrganizationInvitationStatusEnum,
    OrganizationMemberStatusEnum,
    OrganizationRoleCodeEnum,
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
from src.shared.exceptions.base_exceptions import (
    DomainError,
    ForbiddenError,
    ServerError,
)


class GetOrganizationDeletionSummaryUseCase:
    """
    Usecase for getting organization deletion summary before delete request.
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
        organization_id: int,
        actor_role_code: str,
    ) -> dict:
        try:
            if actor_role_code != OrganizationRoleCodeEnum.OWNER.value:
                raise ForbiddenError(
                    error="Only organization owner can view deletion summary",
                    errors={
                        "code": "ONLY_OWNER_CAN_VIEW_DELETION_SUMMARY",
                        "message": "Only organization owner can view deletion summary.",
                    },
                )

            organization = await self.organization_domain_service.get_organization_by_id(
                organization_id=organization_id,
            )

            if not organization:
                raise ServerError(error="Organization not found")

            _, total_members = (
                await self.organization_member_domain_service.list_paginated(
                    organization_id=organization_id,
                    status=None,
                    limit=1,
                    offset=0,
                )
            )

            _, active_members = (
                await self.organization_member_domain_service.list_paginated(
                    organization_id=organization_id,
                    status=OrganizationMemberStatusEnum.ACTIVE.value,
                    limit=1,
                    offset=0,
                )
            )

            _, pending_invitations = (
                await self.organization_invitation_domain_service.list_paginated(
                    organization_id=organization_id,
                    status=OrganizationInvitationStatusEnum.PENDING.value,
                    limit=1,
                    offset=0,
                )
            )

            return {
                "organization_uuid": organization.uuid,
                "organization_name": organization.name,
                "grace_period_days": config.ORGANIZATION_DELETION_GRACE_DAYS,
                "data_summary": {
                    "team_members": total_members,
                    "active_members": active_members,
                    "pending_invitations": pending_invitations,
                    "campaigns": 0,
                    "stored_contacts": 0,
                    "files_and_attachments": 0,
                },
            }

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to get organization deletion summary",
                internal_details=str(e),
            ) from e