from abc import abstractmethod

from src.modules.organization.domain.entities.organization_member_entity import (
    OrganizationMemberEntity,
)
from src.shared.domain.repository.base_repository_interface import IBaseRepository


class IOrganizationMemberRepository(IBaseRepository[OrganizationMemberEntity]):
    """
    Interface for the organization member repository.
    """

    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: int,
    ) -> OrganizationMemberEntity | None:
        """
        Retrieves organization membership of a user.

        Since one user can belong to only one organization, this method returns
        the user's single membership if it exists.
        """
        pass

    @abstractmethod
    async def get_active_by_user_id(
        self,
        user_id: int,
    ) -> OrganizationMemberEntity | None:
        """
        Retrieves active organization membership of a user.
        """
        pass

    @abstractmethod
    async def get_by_user_and_organization(
        self,
        *,
        user_id: int,
        organization_id: int,
    ) -> OrganizationMemberEntity | None:
        """
        Retrieves organization member by user ID and organization ID.
        """
        pass

    @abstractmethod
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
        Returns the slice plus the total count for pagination metadata.
        """
        pass

    @abstractmethod
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
        """List member projections with the associated safe user profile fields."""
        pass

