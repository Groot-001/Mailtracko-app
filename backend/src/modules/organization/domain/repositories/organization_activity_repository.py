from abc import abstractmethod

from src.modules.organization.domain.entities.organization_activity_entity import (
    OrganizationActivityEntity,
)
from src.shared.domain.repository.base_repository_interface import IBaseRepository


class IOrganizationActivityRepository(IBaseRepository[OrganizationActivityEntity]):
    """
    Interface for organization activity repository.
    """

    @abstractmethod
    async def list_by_organization_id(
        self,
        organization_id: int,
        limit: int = 10,
        offset: int = 0,
    ) -> list[OrganizationActivityEntity]:
        """
        Lists recent activities for an organization.
        """

    @abstractmethod
    async def count_by_organization_id(
        self,
        organization_id: int,
    ) -> int:
        """
        Counts activities for an organization.
        """