from src.modules.organization.domain.services.organization_member_domain_service import (
    OrganizationMemberDomainService,
)
from src.shared.exceptions.base_exceptions import DomainError, ServerError


class ListOrganizationMembersUseCase:
    """
    Use case for listing organization members.
    """

    def __init__(
        self,
        organization_member_domain_service: OrganizationMemberDomainService,
    ):
        self.organization_member_domain_service = organization_member_domain_service

    async def execute(
        self,
        *,
        organization_id: int,
        status: str | None = None,
        role: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """
        Lists accepted organization members.
        """
        try:
            members, total = (
                await self.organization_member_domain_service.list_paginated_with_users(
                    organization_id=organization_id,
                    status=status,
                    role=role,
                    search=search,
                    limit=limit,
                    offset=offset,
                )
            )

            # Account status (active/inactive) is authorization state; presence
            # (online/offline) is derived independently from recent valid sessions.
            for member in members:
                member.setdefault("presence", "offline")
                member.setdefault("last_active_at", None)

            return members, total

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to list organization members",
                internal_details=str(e),
            ) from e