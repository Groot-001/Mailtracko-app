from abc import abstractmethod

from src.modules.email_template.domain.entities.template_category_entity import (
    TemplateCategoryEntity,
)
from src.shared.domain.repository.base_repository_interface import IBaseRepository


class ITemplateCategoryRepository(IBaseRepository[TemplateCategoryEntity]):
    """Persistence contract for global and organization template categories."""

    @abstractmethod
    async def list_active(self) -> list[TemplateCategoryEntity]:
        """List active global categories."""
        pass

    @abstractmethod
    async def list_active_for_organization(
        self,
        organization_id: int,
    ) -> list[TemplateCategoryEntity]:
        """List global categories plus active categories owned by an organization."""
        pass

    @abstractmethod
    async def find_active_by_name(
        self,
        name: str,
        organization_id: int | None,
    ) -> TemplateCategoryEntity | None:
        """Find one active category by normalized name in the requested scope."""
        pass

    @abstractmethod
    async def count_active(self, organization_id: int | None = None) -> int:
        """Count active categories, optionally including organization-owned categories."""
        pass
