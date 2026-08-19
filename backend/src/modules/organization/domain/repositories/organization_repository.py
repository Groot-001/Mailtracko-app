from abc import abstractmethod

from src.modules.organization.domain.entities.organization_entity import (
    OrganizationEntity,
)
from src.shared.domain.repository.base_repository_interface import IBaseRepository


class IOrganizationRepository(IBaseRepository[OrganizationEntity]):
    """
    Interface for the organization repository.
    """

    @abstractmethod
    async def get_active_by_owner_id(
        self,
        owner_id: int,
    ) -> OrganizationEntity | None:
        """
        Retrieves active organization owned by the given user.
        """
        pass