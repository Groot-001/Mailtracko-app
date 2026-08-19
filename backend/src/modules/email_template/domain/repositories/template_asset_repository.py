from abc import abstractmethod

from src.modules.email_template.domain.entities.template_asset_entity import (
    TemplateAssetEntity,
)
from src.shared.domain.repository.base_repository_interface import IBaseRepository


class ITemplateAssetRepository(IBaseRepository[TemplateAssetEntity]):
    """
    Interface for the template asset repository.
    """

    @abstractmethod
    async def get_by_uuid_and_template_id(
        self,
        *,
        asset_uuid: str,
        template_id: int,
        organization_id: int | None,
    ) -> TemplateAssetEntity | None:
        """
        Retrieves an active template asset by UUID and template ownership.
        """
        pass

    @abstractmethod
    async def list_paginated(
        self,
        *,
        template_id: int,
        organization_id: int | None,
        usage: str | None = None,
        asset_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[TemplateAssetEntity], int]:
        """
        Lists active assets belonging to a template.

        Returns the paginated asset records and total count.
        """
        pass