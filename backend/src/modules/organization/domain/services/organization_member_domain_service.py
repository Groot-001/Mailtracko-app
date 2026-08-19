from src.modules.organization.domain.entities.organization_member_entity import (
    OrganizationMemberEntity,
)
from src.modules.organization.domain.enums.organization_enums import (
    OrganizationMemberStatusEnum,
    OrganizationRoleCodeEnum,
)
from src.modules.organization.domain.repositories.organization_member_repository import (
    IOrganizationMemberRepository,
)
from src.shared.exceptions.base_exceptions import (
    ConflictError,
    CreateError,
    DomainError,
    ForbiddenError,
    InvalidError,
    ServerError,
)


class OrganizationMemberDomainService:
    """
    Service class for organization member domain logic.
    """

    def __init__(self, repository: IOrganizationMemberRepository):
        self.repository = repository

    async def add_member(
        self,
        member_entity: OrganizationMemberEntity,
    ) -> OrganizationMemberEntity:
        """
        Adds user as organization member.

        A user can belong to only one organization.
        """
        try:
            existing_member = await self.repository.get_by_user_id(
                user_id=member_entity.user_id,
            )

            if existing_member:
                if existing_member.organization_id == member_entity.organization_id:
                    raise ConflictError(
                        error="User is already a member of this organization"
                    )

                raise ConflictError(
                    error="User already belongs to another organization"
                )

            member_entity.status = OrganizationMemberStatusEnum.ACTIVE.value

            return await self.repository.add(member_entity)

        except DomainError:
            raise
        except Exception as e:
            raise CreateError(
                error="Failed to add organization member",
                internal_details=str(e),
            ) from e

    async def get_member_by_user_id(
        self,
        user_id: int,
    ) -> OrganizationMemberEntity | None:
        """
        Retrieves user's organization membership.

        Used after login to decide whether user should enter dashboard or continue onboarding.
        """
        try:
            return await self.repository.get_by_user_id(user_id=user_id)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to retrieve member",
                internal_details=str(e),
            ) from e

    async def get_active_member_by_user_id(
        self,
        user_id: int,
    ) -> OrganizationMemberEntity | None:
        """
        Retrieves active organization membership of user.
        """
        try:
            return await self.repository.get_active_by_user_id(user_id=user_id)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to retrieve active member",
                internal_details=str(e),
            ) from e

    async def get_member_by_user_and_organization(
        self,
        *,
        user_id: int,
        organization_id: int,
    ) -> OrganizationMemberEntity | None:
        """
        Retrieves organization member by user ID and organization ID.
        """
        try:
            return await self.repository.get_by_user_and_organization(
                user_id=user_id,
                organization_id=organization_id,
            )
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to retrieve member",
                internal_details=str(e),
            ) from e

    async def list_paginated(
        self,
        *,
        organization_id: int,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[OrganizationMemberEntity], int]:
        """
        Lists accepted organization members, optionally filtered by status.
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
                error="Failed to list organization members",
                internal_details=str(e),
            ) from e

    async def list_paginated_with_users(
        self,
        *,
        organization_id: int,
        status: str | None = None,
        role: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """List member projections with safe user display information."""
        try:
            return await self.repository.list_paginated_with_users(
                organization_id=organization_id,
                status=status,
                role=role,
                search=search,
                limit=limit,
                offset=offset,
            )
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to list organization member details",
                internal_details=str(e),
            ) from e

    async def remove_member(
        self,
        member_id: int,
        organization_id: int,
        actor_id: int,
        actor_role_code: str,
    ) -> OrganizationMemberEntity:
        """
        Removes (soft-deletes) a member from the organization.

        Only owner/admin can remove members.
        Only owner can remove an admin.
        Owner cannot be removed.
        Actor cannot remove themselves.
        """
        try:
            member = await self.repository.get_by(
                id=member_id,
                organization_id=organization_id,
                deleted_at=None,
            )

            if not member or not member.id:
                raise InvalidError(error="Member not found in this organization")

            if member.user_id == actor_id:
                raise InvalidError(error="Cannot remove yourself")

            if member.is_owner():
                raise InvalidError(error="Cannot remove the organization owner")

            if member.is_admin() and not self._is_owner_role(actor_role_code):
                raise ForbiddenError(
                    error="Only the organization owner can remove an admin",
                )

            member.soft_delete()
            member.mark_updated()

            return await self.repository.update(member)

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to remove organization member",
                internal_details=str(e),
            ) from e

    async def is_organization_member(
        self,
        *,
        organization_id: int,
        user_id: int,
    ) -> bool:
        """
        Checks if a user is an active member of the organization.
        """
        try:
            member = await self.repository.get_by_user_and_organization(
                organization_id=organization_id,
                user_id=user_id,
            )

            return bool(member and member.is_active())
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to check organization membership",
                internal_details=str(e),
            ) from e

    def _is_owner_role(self, role_code: str) -> bool:
        """
        Checks if the given role code is owner.
        """
        return role_code == OrganizationRoleCodeEnum.OWNER.value