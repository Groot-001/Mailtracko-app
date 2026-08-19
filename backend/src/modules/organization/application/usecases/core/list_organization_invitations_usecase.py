from src.modules.organization.domain.entities.organization_invitation_entity import (
    OrganizationInvitationEntity,
)
from src.modules.organization.domain.services.organization_invitation_domain_service import (
    OrganizationInvitationDomainService,
)
from src.shared.exceptions.base_exceptions import DomainError, ServerError


class ListOrganizationInvitationsUseCase:
    """
    Use case for listing organization invitations.
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
        *,
        organization_id: int,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[OrganizationInvitationEntity], int]:
        """
        Executes the use case to list organization invitations.
        """
        try:
            invitations, total = (
                await self.organization_invitation_domain_service.list_paginated(
                    organization_id=organization_id,
                    status=status,
                    limit=limit,
                    offset=offset,
                )
            )

            return invitations, total

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to list organization invitations",
                internal_details=str(e),
            ) from e