from abc import abstractmethod

from src.modules.email_template.domain.entities.template_entity import (
    TemplateEntity,
)
from src.shared.domain.repository.base_repository_interface import (
    IBaseRepository,
)


class ITemplateRepository(IBaseRepository[TemplateEntity]):
    """
    Interface for the template repository.
    """

    @abstractmethod
    async def get_custom_by_uuid(
        self,
        *,
        template_uuid: str,
        organization_id: int,
    ) -> TemplateEntity | None:
        """
        Retrieves a custom template by UUID and organization ID.
        """
        pass

    @abstractmethod
    async def get_system_by_uuid(
        self,
        template_uuid: str,
    ) -> TemplateEntity | None:
        """
        Retrieves an active published system template by UUID.
        """
        pass

    @abstractmethod
    async def list_custom_paginated(
        self,
        *,
        organization_id: int,
        status: str | None = None,
        include_archived: bool = False,
        category_id: int | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[TemplateEntity], int]:
        """
        Lists custom templates belonging to an organization.
        """
        pass

    @abstractmethod
    async def list_system_paginated(
        self,
        *,
        category_id: int | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[TemplateEntity], int]:
        """
        Lists active published system templates.
        """
        pass

    @abstractmethod
    async def unset_default_for_organization(
        self,
        *,
        organization_id: int,
        updated_by_id: int,
        exclude_template_id: int | None = None,
    ) -> None:
        """
        Removes the default flag from other custom templates belonging
        to an organization.
        """
        pass

    @abstractmethod
    async def get_dashboard_counts(
        self,
        *,
        organization_id: int,
    ) -> dict[str, int]:
        """
        Returns organization template counts grouped by lifecycle status.
        """
        pass

    @abstractmethod
    async def count_campaign_usages(
        self,
        *,
        template_id: int,
        organization_id: int,
    ) -> int:
        """
        Returns how many non-deleted campaigns currently reference the template.
        """
        pass